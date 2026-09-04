#!/usr/bin/env python3
"""Validate corpus provenance ledger completeness."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "library" / "penal_code" / "_ledger" / "ledger.json"
RAW = ROOT / "library" / "penal_code" / "_raw" / "act.json"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_corpus_provenance(
    ledger_path: Path = LEDGER,
    raw_path: Path = RAW,
    root: Path = ROOT,
    expected_sections: int = 524,
) -> list[str]:
    """Validate that the ledger still identifies the checked-in inputs exactly."""
    failures: list[str] = []
    if not ledger_path.exists():
        return [f"missing {ledger_path}"]
    if not raw_path.exists():
        return [f"missing {raw_path}"]

    try:
        ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
        raw_document = json.loads(raw_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid JSON: {error}"]

    entries = ledger.get("entries", [])
    raw_sections = raw_document.get("sections", [])
    if not isinstance(entries, list):
        return ["ledger entries must be a list"]
    if not isinstance(raw_sections, list):
        return ["raw source sections must be a list"]
    if ledger.get("n_sections") != len(entries):
        failures.append("n_sections does not match entries length")
    if len(entries) != expected_sections:
        failures.append(f"expected {expected_sections} entries, got {len(entries)}")

    raw_by_section: dict[str, dict[object, object]] = {}
    for raw_section in raw_sections:
        if not isinstance(raw_section, dict) or not raw_section.get("number"):
            failures.append("raw source entry missing number")
            continue
        section = str(raw_section["number"])
        if section in raw_by_section:
            failures.append(f"raw source has duplicate section {section}")
            continue
        raw_by_section[section] = raw_section

    sections: set[str] = set()
    root_resolved = root.resolve()
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append("ledger entry is not an object")
            continue
        section = entry.get("section_number")
        if not section:
            failures.append("entry missing section_number")
            continue
        section = str(section)
        if section in sections:
            failures.append(f"duplicate ledger entry for s{section}")
            continue
        sections.add(section)
        prefix = f"s{section}"
        if not entry.get("sso_url"):
            failures.append(f"{prefix}: missing sso_url")
        if not entry.get("sso_anchor"):
            failures.append(f"{prefix}: missing sso_anchor")
        raw_sha = entry.get("raw", {}).get("sha256")
        if not raw_sha or not SHA256_RE.match(raw_sha):
            failures.append(f"{prefix}: invalid raw sha256")
        raw_entry = raw_by_section.get(section)
        if raw_entry is None:
            failures.append(f"{prefix}: missing raw source entry")
        elif raw_sha and raw_sha != sha256_bytes(str(raw_entry.get("text", "")).encode("utf-8")):
            failures.append(f"{prefix}: raw source hash does not match act.json")
        encoding = entry.get("encoding", {})
        yh_path = encoding.get("yh_path")
        if not isinstance(yh_path, str):
            failures.append(f"{prefix}: missing encoded source path")
        else:
            candidate = (root / yh_path).resolve()
            try:
                candidate.relative_to(root_resolved)
            except ValueError:
                failures.append(f"{prefix}: encoded source path escapes repository")
                candidate = None
            if candidate is not None and not candidate.is_file():
                failures.append(f"{prefix}: missing encoded source path")
            expected_yh_sha = encoding.get("sha256")
            if not expected_yh_sha or not isinstance(expected_yh_sha, str) or not SHA256_RE.match(expected_yh_sha):
                failures.append(f"{prefix}: invalid encoded source sha256")
            elif candidate is not None and candidate.is_file() and expected_yh_sha != sha256_bytes(candidate.read_bytes()):
                failures.append(f"{prefix}: encoded source hash does not match {yh_path}")
        if not encoding.get("first_commit"):
            failures.append(f"{prefix}: missing first_commit")
        if not encoding.get("last_commit"):
            failures.append(f"{prefix}: missing last_commit")
        coverage = entry.get("coverage", {})
        if coverage.get("L1") is not True or coverage.get("L2") is not True:
            failures.append(f"{prefix}: missing L1/L2 coverage")
        if coverage.get("L3") != "stamped":
            failures.append(f"{prefix}: L3 not stamped")
        provenance = entry.get("provenance", {})
        for key in ("yuho_version", "scrape_date", "encoding_commit", "corpus_generated_at"):
            if not provenance.get(key):
                failures.append(f"{prefix}: missing provenance.{key}")
    missing_ledger_entries = set(raw_by_section) - sections
    if missing_ledger_entries:
        failures.append(f"raw sections missing from ledger: {', '.join(sorted(missing_ledger_entries))}")
    return failures


def main() -> None:
    failures = validate_corpus_provenance()
    if not failures:
        print("corpus provenance: 524/524 entries complete")
        return
    for failure in failures:
        print(f"FAIL: {failure}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
