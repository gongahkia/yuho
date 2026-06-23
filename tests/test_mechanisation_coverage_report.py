"""Mechanisation coverage report contract."""

from __future__ import annotations

from scripts.verify_mechanisation_coverage import build_report


def test_mechanisation_coverage_report_lists_boundaries() -> None:
    report = build_report()

    assert "=== mechanisation feature coverage ===" in report
    assert "nested_all_of_any_of: covered" in report
    assert "cross_section_apply_scope: covered" in report
    assert "case_law_doctrine: out-of-scope" in report
    assert "Mechanisation coverage:" in report
