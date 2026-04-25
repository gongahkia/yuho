#!/usr/bin/env python3
"""Build the Yuho benchmark pack from the canonical JSON corpus.

Generates JSONL task files under ``benchmarks/tasks/``. Each task type is
a separate file; each line is one task with fields documented in the
benchmarks/README.md card.

Task types (v0):

    citation_grounding          -- given a question/claim, identify the supporting section
    penalty_extraction          -- given a section, extract its penalty (range / unlimited / etc.)
    element_classification      -- given an element string, classify as actus_reus / mens_rea / etc.
    cross_reference             -- given a section, list the sections it references (G10)
    illustration_recognition    -- given a fact pattern, identify the illustration it matches

Each task carries a ``provenance`` block: source section, raw SHA, Yuho
version, generated_at. Tasks are deterministic given a fixed corpus +
seed, so re-runs of this script produce stable diffs.

Usage:
    python3 benchmarks/build_benchmarks.py
    python3 benchmarks/build_benchmarks.py --task penalty_extraction
    python3 benchmarks/build_benchmarks.py --max 50    # smoke run, 50 tasks each

The benchmark is research infrastructure. It does not provide legal advice.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"
TASKS = Path(__file__).resolve().parent / "tasks"


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------


def _load_corpus() -> Dict[str, Dict[str, Any]]:
    """Load every section record into memory."""
    sect_dir = CORPUS / "sections"
    if not sect_dir.exists():
        sys.exit("error: corpus not built. Run scripts/build_corpus.py first.")
    out: Dict[str, Dict[str, Any]] = {}
    for path in sorted(sect_dir.glob("s*.json")):
        with path.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        out[rec["section_number"]] = rec
    return out


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def _provenance(rec: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_section": rec["section_number"],
        "raw_sha256": rec.get("raw", {}).get("hash_sha256"),
        "yuho_version": rec.get("provenance", {}).get("yuho_version"),
        "encoding_commit": rec.get("provenance", {}).get("encoding_commit"),
    }


# ---------------------------------------------------------------------------
# Task type 1: citation grounding
# ---------------------------------------------------------------------------


def task_citation_grounding(corpus: Dict[str, Dict[str, Any]], rng: random.Random) -> Iterable[Dict[str, Any]]:
    """Given a fragment of a section's canonical text, identify the section."""
    for num, rec in corpus.items():
        text = rec.get("raw", {}).get("text") or ""
        title = rec.get("section_title") or ""
        if len(text) < 80:
            continue
        # Pick a random middle slice; keep boundaries on word breaks.
        start = rng.randint(0, max(0, len(text) - 60))
        end = min(len(text), start + rng.randint(40, 100))
        # Snap to word boundaries.
        while start > 0 and text[start].isalpha():
            start -= 1
        while end < len(text) and text[end].isalpha():
            end += 1
        fragment = text[start:end].strip()
        if len(fragment) < 30:
            continue
        yield {
            "task": "citation_grounding",
            "id": f"cite_s{num}",
            "input": {
                "fragment": fragment,
                "instruction": "Identify the Singapore Penal Code section number whose canonical text contains this fragment.",
            },
            "answer": {
                "section_number": num,
                "section_title": title,
                "act_code": "PC1871",
            },
            "provenance": _provenance(rec),
        }


# ---------------------------------------------------------------------------
# Task type 2: penalty extraction
# ---------------------------------------------------------------------------


def _extract_penalty_block(yh: str) -> Optional[str]:
    """Pull the body of the first ``penalty { ... }`` block from a .yh source."""
    if not yh:
        return None
    idx = yh.find("penalty")
    if idx < 0:
        return None
    open_idx = yh.find("{", idx)
    if open_idx < 0:
        return None
    depth = 1
    for i in range(open_idx + 1, len(yh)):
        c = yh[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return yh[idx:i + 1].strip()
    return None


def task_penalty_extraction(corpus: Dict[str, Dict[str, Any]], rng: random.Random) -> Iterable[Dict[str, Any]]:
    for num, rec in corpus.items():
        ast = rec.get("encoded", {}).get("ast_summary", {}) or {}
        if not ast.get("has_penalty"):
            continue
        yh = rec.get("encoded", {}).get("yh_source") or ""
        penalty_block = _extract_penalty_block(yh)
        if not penalty_block:
            continue
        raw_text = rec.get("raw", {}).get("text") or ""
        yield {
            "task": "penalty_extraction",
            "id": f"penalty_s{num}",
            "input": {
                "section_number": num,
                "canonical_text": raw_text,
                "instruction": (
                    "Given the canonical text of a Singapore Penal Code section, "
                    "extract the penalty: imprisonment range, fine cap (or 'unlimited'), "
                    "caning (or 'unspecified' / 'none'), and combinator "
                    "(cumulative / alternative / or_both). Match the encoded "
                    "Yuho representation exactly."
                ),
            },
            "answer": {
                "encoded_penalty_block": penalty_block,
            },
            "provenance": _provenance(rec),
        }


# ---------------------------------------------------------------------------
# Task type 3: element classification
# ---------------------------------------------------------------------------


_ELEMENT_KIND_RE = (
    r"(actus_reus|mens_rea|circumstance|obligation|prohibition|permission)"
)


def task_element_classification(corpus: Dict[str, Dict[str, Any]], rng: random.Random) -> Iterable[Dict[str, Any]]:
    """Pull individual element declarations and ask: which kind?"""
    import re
    pattern = re.compile(
        rf"\b{_ELEMENT_KIND_RE}\s+(\w+)\s*:=\s*\"([^\"]+)\"", re.MULTILINE
    )
    for num, rec in corpus.items():
        yh = rec.get("encoded", {}).get("yh_source") or ""
        if not yh:
            continue
        for match in pattern.finditer(yh):
            kind = match.group(1)
            elem_name = match.group(2)
            elem_desc = match.group(3)
            yield {
                "task": "element_classification",
                "id": f"elem_s{num}_{elem_name}",
                "input": {
                    "section_number": num,
                    "section_title": rec.get("section_title"),
                    "element_name": elem_name,
                    "element_description": elem_desc,
                    "instruction": (
                        "Classify this element of a Penal Code offence into one of: "
                        "actus_reus, mens_rea, circumstance, obligation, prohibition, permission."
                    ),
                },
                "answer": {
                    "kind": kind,
                },
                "provenance": _provenance(rec),
            }


# ---------------------------------------------------------------------------
# Task type 4: cross-reference (depends on G10)
# ---------------------------------------------------------------------------


def task_cross_reference(corpus: Dict[str, Dict[str, Any]], rng: random.Random) -> Iterable[Dict[str, Any]]:
    for num, rec in corpus.items():
        refs = rec.get("references", {})
        outgoing = refs.get("outgoing", [])
        if not outgoing:
            continue
        yield {
            "task": "cross_reference",
            "id": f"xref_s{num}",
            "input": {
                "section_number": num,
                "section_title": rec.get("section_title"),
                "canonical_text": rec.get("raw", {}).get("text"),
                "instruction": (
                    "List every other Singapore Penal Code section that this section "
                    "references, subsumes, or amends. Provide section numbers only."
                ),
            },
            "answer": {
                "outgoing_sections": sorted({e["dst"] for e in outgoing}),
                "n_outgoing": len(outgoing),
            },
            "provenance": _provenance(rec),
        }


# ---------------------------------------------------------------------------
# Task type 5: illustration recognition
# ---------------------------------------------------------------------------


def task_illustration_recognition(corpus: Dict[str, Dict[str, Any]], rng: random.Random) -> Iterable[Dict[str, Any]]:
    """Pull illustration strings from .yh files; ask which section they belong to."""
    import re
    pattern = re.compile(r"illustration\s+\w+\s*\{\s*\"([^\"]+)\"\s*\}", re.MULTILINE | re.DOTALL)
    for num, rec in corpus.items():
        yh = rec.get("encoded", {}).get("yh_source") or ""
        if not yh:
            continue
        for i, match in enumerate(pattern.finditer(yh)):
            illustration = match.group(1).strip()
            if len(illustration) < 30:
                continue
            yield {
                "task": "illustration_recognition",
                "id": f"ill_s{num}_{i}",
                "input": {
                    "illustration": illustration,
                    "instruction": (
                        "This is a verbatim illustration from one section of the "
                        "Singapore Penal Code 1871. Identify the section number."
                    ),
                },
                "answer": {
                    "section_number": num,
                    "section_title": rec.get("section_title"),
                },
                "provenance": _provenance(rec),
            }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


_GENERATORS = {
    "citation_grounding": task_citation_grounding,
    "penalty_extraction": task_penalty_extraction,
    "element_classification": task_element_classification,
    "cross_reference": task_cross_reference,
    "illustration_recognition": task_illustration_recognition,
}


def _write_jsonl(rows: List[Dict[str, Any]], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--task", choices=list(_GENERATORS), help="Build only this task type")
    parser.add_argument("--max", type=int, default=None, help="Cap rows per task")
    parser.add_argument("--seed", type=int, default=20260425, help="RNG seed")
    args = parser.parse_args()

    print(f"Loading corpus from {CORPUS.relative_to(REPO)}/...", file=sys.stderr)
    corpus = _load_corpus()
    print(f"  {len(corpus)} sections", file=sys.stderr)

    rng = random.Random(args.seed)

    targets = [args.task] if args.task else list(_GENERATORS.keys())

    print(f"Generating tasks: {', '.join(targets)}", file=sys.stderr)

    summary: Dict[str, int] = {}
    for task_name in targets:
        gen = _GENERATORS[task_name]
        rows = list(gen(corpus, rng))
        if args.max:
            rng.shuffle(rows)
            rows = rows[: args.max]
        out_path = TASKS / f"{task_name}.jsonl"
        n = _write_jsonl(rows, out_path)
        summary[task_name] = n
        print(f"  {task_name:30s} -> {out_path.relative_to(REPO)}  ({n} rows)", file=sys.stderr)

    # Top-level manifest.
    manifest = {
        "name": "Yuho benchmark pack",
        "version": "0.1.0",
        "act_code": "PC1871",
        "act": "Penal Code 1871",
        "jurisdiction": "SG",
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "seed": args.seed,
        "tasks": [
            {
                "name": name,
                "file": f"tasks/{name}.jsonl",
                "n_rows": summary[name],
            }
            for name in targets
        ],
        "disclaimer": (
            "Research / educational artefact. Not legal advice. The benchmark "
            "draws from the publicly-available Singapore Penal Code 1871 as encoded "
            "in the Yuho library; cross-reference with the canonical SSO source for "
            "any decision that matters."
        ),
    }
    manifest_path = TASKS.parent / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nManifest: {manifest_path.relative_to(REPO)}")
    print(f"Total rows: {sum(summary.values())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
