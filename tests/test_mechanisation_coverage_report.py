"""Mechanisation coverage report contract."""

from __future__ import annotations

from scripts.verify_mechanisation_coverage import (
    CORPUS_STRATA,
    REPO,
    build_report,
    corpus_strata_representatives,
)


def test_mechanisation_coverage_report_lists_boundaries() -> None:
    report = build_report()

    assert "=== mechanisation feature coverage ===" in report
    assert "nested_all_of_any_of: covered" in report
    assert "cross_section_apply_scope: covered" in report
    assert "case_law_doctrine: partial" in report
    assert "Corpus strata representatives:" in report
    assert "Mechanisation corpus strata:" in report
    for stratum in CORPUS_STRATA:
        assert f"{stratum}=covered" in report
    assert "Mechanisation coverage:" in report


def test_mechanisation_corpus_strata_have_representatives() -> None:
    representatives = corpus_strata_representatives(REPO / "library" / "penal_code")

    assert set(CORPUS_STRATA).issubset(representatives)
    for section, path in representatives.values():
        assert section
        assert path.endswith("/statute.yh")
