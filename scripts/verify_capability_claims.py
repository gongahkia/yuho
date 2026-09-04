#!/usr/bin/env python3
"""Verify machine-readable public-claim and corpus-review boundaries."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
REGISTRY = ROOT / "docs" / "release" / "capability-claims.json"
COVERAGE = ROOT / "library" / "penal_code" / "_coverage" / "coverage.json"
EVIDENCE = ROOT / "docs" / "release" / "evidence.md"
STATUS_MATRIX = ROOT / "docs" / "positioning" / "status-matrix.md"
RETROSPECTIVE = ROOT / "docs" / "retrospective.md"
REQUIRED_SOURCES = {
    "docs/positioning/status-matrix.md",
    "library/penal_code/_coverage/coverage.json",
    "tests/fixtures/backend_parity/claims.json",
}
# README is intentionally excluded because it is subject to the separate
# no-edit constraint. Every other checked-in Markdown document is in scope:
# an archived or contributor-facing page can still be quoted as an assurance
# claim outside its original context.
PUBLIC_BOUNDARY_DOCUMENTS = (ROOT / "docs",)


def review_kind(value: object) -> str:
    """Classify existing reviewer labels without upgrading ambiguous evidence."""
    reviewer = str(value or "").casefold()
    if "human-verified" in reviewer or "manual" in reviewer:
        return "human_reviewed"
    if "automated" in reviewer or "gpt-" in reviewer or "opus" in reviewer:
        return "automated_triage"
    return "unattributed_team_review"


def validate_capability_claims(
    registry_path: Path = REGISTRY,
    coverage_path: Path = COVERAGE,
    evidence_path: Path = EVIDENCE,
) -> list[str]:
    failures: list[str] = []
    try:
        registry: dict[str, Any] = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"cannot read capability registry: {error}"]

    if registry.get("schema_version") != "yuho.capability-claims/v1":
        failures.append("unsupported capability-claim schema version")
    generated_from = registry.get("generated_from")
    if not isinstance(generated_from, list) or not REQUIRED_SOURCES.issubset(generated_from):
        failures.append("registry must identify all required evidence sources")

    claims = registry.get("claims")
    if not isinstance(claims, list) or not claims:
        failures.append("registry has no claims")
    else:
        identifiers = [claim.get("id") for claim in claims if isinstance(claim, dict)]
        if len(identifiers) != len(set(identifiers)) or any(
            not identifier for identifier in identifiers
        ):
            failures.append("claim identifiers must be non-empty and unique")
        for claim in claims:
            if not isinstance(claim, dict):
                failures.append("claim is not an object")
                continue
            if claim.get("status") not in {"stable", "partial", "experimental", "unsupported"}:
                failures.append(f"{claim.get('id', '<unknown>')}: invalid status")
            if (
                not isinstance(claim.get("public_wording"), str)
                or not claim["public_wording"].strip()
            ):
                failures.append(f"{claim.get('id', '<unknown>')}: missing public wording")
            if not claim.get("evidence") or not claim.get("limits"):
                failures.append(f"{claim.get('id', '<unknown>')}: evidence and limits are required")

    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        sections = coverage["sections"]
    except (OSError, KeyError, json.JSONDecodeError) as error:
        failures.append(f"cannot read review coverage: {error}")
        sections = []

    counts = Counter(review_kind(section.get("L3_verified_by")) for section in sections)
    expected = registry.get("corpus_review", {})
    if expected.get("total_sections") != len(sections):
        failures.append(
            f"corpus_review.total_sections={expected.get('total_sections')} but coverage has {len(sections)}"
        )
    for key in ("automated_triage", "human_reviewed", "unattributed_team_review"):
        if expected.get(key) != counts[key]:
            failures.append(
                f"corpus_review.{key}={expected.get(key)} but coverage has {counts[key]}"
            )
    if sum(counts.values()) != len(sections):
        failures.append("review classes do not cover all sections")

    try:
        evidence = evidence_path.read_text(encoding="utf-8")
    except OSError as error:
        failures.append(f"cannot read release evidence: {error}")
    else:
        if "capability-claims.json" not in evidence:
            failures.append("release evidence does not link the capability registry")
        if "human-verified" in evidence.casefold():
            failures.append("release evidence uses an unsupported blanket human-review claim")

    for label, path in (("status matrix", STATUS_MATRIX), ("retrospective", RETROSPECTIVE)):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read {label}: {error}")
            continue
        if "capability-claims.json" not in text:
            failures.append(f"{label} does not link the capability registry")

    documents: list[Path] = []
    for path in PUBLIC_BOUNDARY_DOCUMENTS:
        documents.extend(path.rglob("*.md") if path.is_dir() else [path])
    for path in documents:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as error:
            failures.append(f"cannot read public boundary document {path}: {error}")
            continue
        if "formally verified" in text.casefold():
            failures.append(f"{path.relative_to(ROOT)} uses a blanket formal-verification claim")
        if re.search(r"(?:all\s+)?524(?:/524)?[^\n]{0,80}human[- ]verif", text, re.IGNORECASE):
            failures.append(f"{path.relative_to(ROOT)} uses a blanket human-review claim")

    return failures


def main() -> None:
    failures = validate_capability_claims()
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        raise SystemExit(1)
    print("capability claims: schema, evidence boundary, and review classes verified")


if __name__ == "__main__":
    main()
