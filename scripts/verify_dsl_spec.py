#!/usr/bin/env python3
"""Verify the executable Yuho DSL v1 conformance fixture."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from yuho.services.analysis import analyze_source
from yuho.transpile.json_schema import AST_SCHEMA_VERSION
from yuho.transpile.json_transpiler import JSONTranspiler

SPEC_FIXTURE = Path("tests/fixtures/conformance/dsl_spec_v1.json")


def load_fixture(path: Path = SPEC_FIXTURE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_spec(path: Path = SPEC_FIXTURE) -> dict[str, Any]:
    fixture = load_fixture(path)
    spec_path = Path(fixture["spec_document"])
    spec_text = spec_path.read_text(encoding="utf-8")
    failures: list[str] = []
    checked: list[str] = []

    for rule in fixture["rules"]:
        rule_id = rule["id"]
        checked.append(rule_id)
        if rule_id not in spec_text:
            failures.append(f"{rule_id}: missing from {spec_path}")
            continue

        analysis = analyze_source(
            rule["source"],
            file=f"<{rule_id}>",
            run_semantic=True,
        )
        parse_valid = not analysis.parse_errors
        semantic_valid = not any(
            item.get("severity") == "error" and item.get("stage") == "semantic"
            for item in analysis.diagnostics()
        )

        if parse_valid != rule["parse_valid"]:
            failures.append(f"{rule_id}: parse_valid={parse_valid}")
        if parse_valid and semantic_valid != rule["semantic_valid"]:
            failures.append(f"{rule_id}: semantic_valid={semantic_valid}")

        expected = rule.get("expected_diagnostic")
        if expected:
            messages = [item["message"] for item in analysis.diagnostics()]
            if not any(expected in message for message in messages):
                failures.append(f"{rule_id}: missing diagnostic {expected!r}")

        if rule["parse_valid"] and rule["semantic_valid"] and analysis.ast is not None:
            payload = json.loads(JSONTranspiler().transpile(analysis.ast).output)
            if payload.get("_schema_version") != AST_SCHEMA_VERSION:
                failures.append(f"{rule_id}: JSON schema version mismatch")

    return {
        "spec_version": fixture["spec_version"],
        "checked": checked,
        "failures": failures,
        "ok": not failures,
    }


def main() -> None:
    report = verify_spec()
    if report["ok"]:
        print(
            "dsl spec v{spec_version}: {count}/{count} rules pass".format(
                spec_version=report["spec_version"],
                count=len(report["checked"]),
            )
        )
        return
    for failure in report["failures"]:
        print(f"FAIL: {failure}")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
