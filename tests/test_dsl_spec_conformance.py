"""Versioned Yuho DSL spec conformance contract."""

from __future__ import annotations

from pathlib import Path

from scripts.verify_dsl_spec import load_fixture, verify_spec


def test_dsl_spec_fixture_schema_and_doc_links() -> None:
    fixture = load_fixture()

    assert fixture["schema_version"] == 1
    assert fixture["spec_version"] == "1.0.0"
    assert Path(fixture["spec_document"]).exists()
    assert Path(fixture["json_schema"]).exists()
    assert fixture["rules"]
    for rule in fixture["rules"]:
        assert rule["id"].startswith("YH-")
        assert isinstance(rule["source"], str) and rule["source"]
        assert isinstance(rule["parse_valid"], bool)
        assert isinstance(rule["semantic_valid"], bool)
        if not rule["semantic_valid"]:
            assert rule["expected_diagnostic"]


def test_dsl_spec_v1_rules_execute() -> None:
    report = verify_spec()

    assert report["ok"], report["failures"]
    assert len(report["checked"]) == len(load_fixture()["rules"])
