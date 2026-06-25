"""SARIF output contract for CI integrations."""

from __future__ import annotations

import json

from yuho.output.sarif import make_sarif_result, to_sarif, validate_sarif_document


def test_sarif_output_declares_rules_artifacts_and_invocations() -> None:
    result = make_sarif_result(
        rule_id="yuho/semantic",
        message="bad return",
        file="demo.yh",
        line=3,
        col=7,
        level="error",
    )
    document = json.loads(to_sarif([result]))
    run = document["runs"][0]

    assert document["version"] == "2.1.0"
    assert document["$schema"].endswith("sarif-schema-2.1.0.json")
    assert run["invocations"][0]["executionSuccessful"] is True
    assert run["artifacts"][0]["location"]["uri"] == "demo.yh"
    assert run["automationDetails"]["id"] == "yuho/check"
    assert run["tool"]["driver"]["rules"][0]["id"] == "yuho/semantic"
    assert validate_sarif_document(document) == []


def test_sarif_validation_rejects_missing_rule_descriptors() -> None:
    document = json.loads(to_sarif([make_sarif_result("yuho/parse", "bad", "demo.yh")]))
    document["runs"][0]["tool"]["driver"]["rules"] = []

    errors = validate_sarif_document(document)

    assert any("has no reportingDescriptor" in error for error in errors)
