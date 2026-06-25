#!/usr/bin/env python3
"""Validate corpus provenance ledger completeness."""

from __future__ import annotations

import json
import re
from pathlib import Path

LEDGER = Path("library/penal_code/_ledger/ledger.json")
RAW = Path("library/penal_code/_raw/act.json")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def validate_corpus_provenance() -> list[str]:
    failures: list[str] = []
    if not LEDGER.exists():
        return [f"missing {LEDGER}"]
    if not RAW.exists():
        failures.append(f"missing {RAW}")

    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = ledger.get("entries", [])
    if ledger.get("n_sections") != len(entries):
        failures.append("n_sections does not match entries length")
    if len(entries) != 524:
        failures.append(f"expected 524 entries, got {len(entries)}")

    sections = set()
    for entry in entries:
        section = entry.get("section_number")
        if not section:
            failures.append("entry missing section_number")
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
        encoding = entry.get("encoding", {})
        yh_path = encoding.get("yh_path")
        if not yh_path or not Path(yh_path).exists():
            failures.append(f"{prefix}: missing encoded source path")
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
