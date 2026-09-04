"""Run read-only automated L3 triage for encoded Penal Code sections.

This tool records model-assisted triage in an append-only JSONL file. It never
writes ``metadata.toml``, changes an L3 stamp, or certifies human review.

Usage:
    python scripts/l3_audit.py --list
    python scripts/l3_audit.py 415
    python scripts/l3_audit.py --all --dispatch --parallel 1
    python scripts/l3_audit.py --all --dispatch --resume
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "docs" / "researcher" / "l3-triage-prompt.md"
RAW_PATH = REPO / "library" / "penal_code" / "_raw" / "act.json"
TRIAGE_SCHEMA_VERSION = "yuho.automated-triage/v1"
DECISIONS = {"TRIAGE_PASS", "FLAG", "NEEDS_HUMAN_REVIEW"}


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sortkey(number: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d+)([A-Z]*)", number)
    if match is None:
        return (9999, number)
    return (int(match.group(1)), match.group(2))


def load_raw() -> tuple[dict[str, dict[str, Any]], str]:
    document = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    sections = {
        str(section["number"]): section
        for section in document.get("sections", [])
        if isinstance(section, dict) and section.get("number")
    }
    return sections, str(document.get("act_code", "PC1871"))


def expand_spec(specs: list[str], raw: dict[str, dict[str, Any]]) -> list[str]:
    targets: list[str] = []
    seen: set[str] = set()
    for token in (part.strip() for spec in specs for part in spec.split(",")):
        if not token:
            continue
        match = re.fullmatch(r"(\d+)\s*-\s*(\d+)", token)
        if match is None:
            if token not in seen:
                seen.add(token)
                targets.append(token)
            continue
        start, end = sorted((int(match.group(1)), int(match.group(2))))
        for number in range(start, end + 1):
            for candidate in sorted(
                (section for section in raw if re.fullmatch(rf"{number}[A-Z]*", section)),
                key=_sortkey,
            ):
                if candidate not in seen:
                    seen.add(candidate)
                    targets.append(candidate)
    return targets


def find_dir(number: str) -> Path | None:
    matches = sorted((REPO / "library" / "penal_code").glob(f"s{number}_*"))
    return matches[0] if len(matches) == 1 and matches[0].is_dir() else None


def reviewed_hashes(number: str, raw_section: dict[str, Any]) -> dict[str, str] | None:
    section_dir = find_dir(number)
    if section_dir is None:
        return None
    yh_path = section_dir / "statute.yh"
    if not yh_path.is_file():
        return None
    return {
        "raw_sha256": sha256_bytes(str(raw_section.get("text", "")).encode("utf-8")),
        "yh_sha256": sha256_bytes(yh_path.read_bytes()),
    }


def repository_path(value: str) -> Path:
    path = (REPO / value).resolve()
    try:
        path.relative_to(REPO)
    except ValueError as error:
        raise ValueError(f"path escapes repository: {value}") from error
    return path


def completed_triage(progress_path: Path) -> dict[str, dict[str, str]]:
    completed: dict[str, dict[str, str]] = {}
    if not progress_path.is_file():
        return completed
    for line in progress_path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            record.get("schema_version") == TRIAGE_SCHEMA_VERSION
            and record.get("decision") in DECISIONS
            and isinstance(record.get("section"), str)
            and isinstance(record.get("reviewed_inputs"), dict)
        ):
            hashes = record["reviewed_inputs"]
            if isinstance(hashes.get("raw_sha256"), str) and isinstance(
                hashes.get("yh_sha256"), str
            ):
                completed[record["section"]] = {
                    "raw_sha256": hashes["raw_sha256"],
                    "yh_sha256": hashes["yh_sha256"],
                }
    return completed


def render(number: str, section: dict[str, Any], act_code: str, template: str) -> str:
    marginal = str(section.get("marginal_note") or f"Section {number}")
    anchor = str(section.get("anchor_id") or f"pr{number}-")
    section_dir = find_dir(number)
    directory = str(section_dir.relative_to(REPO)) if section_dir is not None else "(missing)"
    header = "\n".join(
        (
            "## Section context (pre-filled)",
            "",
            f"- Section: **{number}**",
            f"- Marginal note: **{marginal}**",
            f"- SSO anchor: `{anchor}`",
            f"- SSO URL: https://sso.agc.gov.sg/Act/{act_code}?ProvIds={anchor}#{anchor}",
            f"- Directory: `{directory}`",
            f'- Canonical text: `library/penal_code/_raw/act.json` entry where `number == "{number}"`',
            "",
            "---",
            "",
        )
    )
    return header + template.replace("{N}", number)


def dispatch_codex(
    prompt: str,
    timeout: int,
    model: str | None,
    reasoning: str | None,
) -> subprocess.CompletedProcess[str]:
    """Run a reviewer with read-only filesystem access only."""
    command = [
        "codex",
        "exec",
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        str(REPO),
    ]
    if model:
        command.extend(("-m", model))
    if reasoning:
        command.extend(("-c", f"model_reasoning_effort={reasoning}"))
    command.append("-")
    return subprocess.run(command, input=prompt, text=True, capture_output=True, timeout=timeout)


def parse_triage_response(output: str) -> dict[str, Any] | None:
    """Extract the required final JSON record without trusting prose around it."""
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", output):
        try:
            candidate, _ = decoder.raw_decode(output[match.start() :])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict):
            continue
        decision = candidate.get("decision")
        section = candidate.get("section")
        failed_items = candidate.get("failed_items")
        summary = candidate.get("summary")
        if (
            decision not in DECISIONS
            or not isinstance(section, str)
            or not isinstance(failed_items, list)
            or not all(isinstance(item, int) and 1 <= item <= 11 for item in failed_items)
            or len(set(failed_items)) != len(failed_items)
            or not isinstance(summary, str)
            or not summary.strip()
        ):
            continue
        return {
            "section": section,
            "decision": decision,
            "failed_items": sorted(failed_items),
            "summary": summary.strip(),
        }
    return None


def triage_record(
    number: str,
    prompt: str,
    reviewed_inputs: dict[str, str],
    model: str,
    reasoning: str,
    timeout: int,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "schema_version": TRIAGE_SCHEMA_VERSION,
        "kind": "automated_triage",
        "section": number,
        "reviewed_inputs": reviewed_inputs,
        "prompt_sha256": sha256_bytes(prompt.encode("utf-8")),
        "model": model,
        "reasoning": reasoning,
        "completed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    try:
        result = dispatch_codex(prompt, timeout, model, reasoning)
    except subprocess.TimeoutExpired:
        return {**record, "decision": "ERROR", "error": "timeout"}
    except OSError as error:
        return {**record, "decision": "ERROR", "error": error.__class__.__name__}
    if result.returncode != 0:
        return {**record, "decision": "ERROR", "error": f"exit={result.returncode}"}
    response = parse_triage_response(result.stdout)
    if response is None or response["section"] != number:
        return {**record, "decision": "ERROR", "error": "invalid triage response"}
    return {
        **record,
        **response,
        "output_sha256": sha256_bytes(result.stdout.encode("utf-8")),
    }


def main() -> None:
    parser = argparse.ArgumentParser(prog="l3_audit", description=__doc__)
    parser.add_argument("specs", nargs="*", help="section numbers, ranges (1-20), or comma lists")
    parser.add_argument(
        "--list", action="store_true", help="list sections without current automated triage"
    )
    parser.add_argument(
        "--all", action="store_true", help="target every section in the raw snapshot"
    )
    parser.add_argument("--dispatch", action="store_true", help="invoke read-only Codex triage")
    parser.add_argument(
        "--parallel", type=int, default=1, metavar="K", help="maximum concurrent triage runs"
    )
    parser.add_argument(
        "--progress",
        default="library/penal_code/_coverage/automated-triage.jsonl",
        help="append-only JSONL triage evidence path",
    )
    parser.add_argument(
        "--resume", action="store_true", help="skip matching completed automated triage"
    )
    parser.add_argument("--timeout", type=int, default=900, help="per-section timeout in seconds")
    parser.add_argument("--model", default="gpt-5.4", help="Codex model used for triage")
    parser.add_argument("--reasoning", default="high", help="Codex reasoning effort")
    args = parser.parse_args()

    raw, act_code = load_raw()
    try:
        progress_path = repository_path(args.progress)
    except ValueError as error:
        parser.error(str(error))
    completed = completed_triage(progress_path)

    if args.list:
        for number in sorted(raw, key=_sortkey):
            hashes = reviewed_hashes(number, raw[number])
            if hashes is None or completed.get(number) != hashes:
                print(f"{number}\t{raw[number].get('marginal_note', '')[:80]}")
        return

    if args.all:
        targets = sorted(raw, key=_sortkey)
    else:
        targets = expand_spec(args.specs, raw)
    targets = [number for number in targets if number in raw]
    if not targets:
        parser.error("supply section numbers, --all, or --list")

    current_inputs = {number: reviewed_hashes(number, raw[number]) for number in targets}
    missing_inputs = [number for number, inputs in current_inputs.items() if inputs is None]
    if missing_inputs:
        parser.error(f"missing encoded source for: {', '.join(missing_inputs)}")
    if args.resume:
        targets = [number for number in targets if completed.get(number) != current_inputs[number]]
        print(f"[resume] {len(targets)} section(s) require current triage", flush=True)
    if not targets:
        return

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    prompts = {number: render(number, raw[number], act_code, template) for number in targets}
    if not args.dispatch:
        separator = "\n\n<<<---NEXT_SECTION--->>>\n\n" if len(prompts) > 1 else "\n"
        sys.stdout.write(separator.join(prompts.values()) + "\n")
        return

    progress_path.parent.mkdir(parents=True, exist_ok=True)
    print(
        f"[start] {len(targets)} section(s), model={args.model}, reasoning={args.reasoning}, parallel={args.parallel}",
        flush=True,
    )
    with (
        progress_path.open("a", encoding="utf-8") as progress,
        ThreadPoolExecutor(max_workers=max(args.parallel, 1)) as executor,
    ):
        futures = {
            executor.submit(
                triage_record,
                number,
                prompts[number],
                current_inputs[number],
                args.model,
                args.reasoning,
                args.timeout,
            ): number
            for number in targets
        }
        for future in as_completed(futures):
            number = futures[future]
            try:
                record = future.result()
            except Exception as error:  # pragma: no cover - defensive process boundary
                record = {"section": number, "decision": "ERROR", "error": error.__class__.__name__}
            progress.write(json.dumps(record, sort_keys=True) + "\n")
            progress.flush()
            print(f"[{record['decision']}] s{number}", flush=True)


if __name__ == "__main__":
    main()
