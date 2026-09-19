#!/usr/bin/env python3
"""Fail closed on unsupported public product and assurance claims."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md"))]
FORBIDDEN = (
    "rewrite/haskell", "rewrite/frontend", "old python implementation",
    "legacy yuho", "migration guide", "entirely formally verified",
    "complete executable encoding of singapore criminal law",
)


def main() -> None:
    failures: list[str] = []
    for path in PUBLIC:
        text = path.read_text(encoding="utf-8")
        folded = text.casefold()
        for phrase in FORBIDDEN:
            if phrase in folded:
                failures.append(f"{path.relative_to(ROOT)} contains {phrase!r}")
        if re.search(r"(?:all\s+)?524[^\n]{0,80}(?:executable|legally reviewed)", text, re.I):
            failures.append(f"{path.relative_to(ROOT)} overstates 524-row coverage")
        if "yuho is formally verified" in folded:
            failures.append(f"{path.relative_to(ROOT)} makes an unqualified proof claim")

    coverage = json.loads((ROOT / "research/singapore/SINGAPORE-CRIMINAL-LAW-COVERAGE-v0.3.json").read_text())
    summary = coverage["summary"]
    expected = {"provisions": 524, "total_offence_families": 26,
                "total_general_exceptions": 13, "total_candidate_penalties": 22,
                "total_singapore_scenarios": 306, "total_cases": 16}
    for key, value in expected.items():
        if summary.get(key) != value:
            failures.append(f"coverage summary {key}={summary.get(key)!r}, expected {value}")
    executable = summary["by_classification"].get("executable_research", 0) + summary["by_classification"].get("executable_partial", 0)
    if executable != 55:
        failures.append(f"executable coverage rows={executable}, expected 55")

    if failures:
        raise SystemExit("\n".join(f"FAIL: {item}" for item in failures))
    print("capability claims: current product, proof and corpus boundaries verified")


if __name__ == "__main__":
    main()
