"""Tests for the case-law differential-testing harness.

Three orthogonal scorers run against the curated fixtures under
``evals/case_law/fixtures/``:

* ``score_recommend.py``      — top-k accuracy + MRR
* ``score_contrast.py``        — Z3 contrast vs court reasoning F1
* ``score_contrast_constrained.py`` — encoded-model expressivity

These tests pin the harness behaviour with the bundled fixtures.
The numbers themselves are research data and may shift as fixtures
are added/refined; the asserts below are structural — they check
shape and invariants, not specific accuracy values.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CASE_LAW = REPO / "evals" / "case_law"
FIXTURES = CASE_LAW / "fixtures"

sys.path.insert(0, str(CASE_LAW))


def _have_fixtures() -> bool:
    return any(FIXTURES.glob("*.yaml"))


@pytest.fixture(scope="module")
def fixtures():
    import score_recommend
    return score_recommend._load_fixtures(FIXTURES)


@pytest.mark.skipif(not _have_fixtures(), reason="no case-law fixtures present")
def test_fixtures_load_with_required_fields(fixtures):
    assert len(fixtures) >= 5
    for fx in fixtures:
        assert "id" in fx, f"missing id in {fx.get('__path__')}"
        assert "case_citation" in fx, f"missing citation in {fx.get('id')}"
        assert "actual_charge" in fx, f"missing actual_charge in {fx.get('id')}"
        assert "fact_facts" in fx, f"missing fact_facts in {fx.get('id')}"


@pytest.mark.skipif(not _have_fixtures(), reason="no case-law fixtures present")
def test_recommend_scorer_produces_well_formed_report(fixtures):
    import score_recommend
    report = score_recommend.score(fixtures, top_k=5, max_candidates=60)
    assert report.n == len(fixtures)
    assert 0.0 <= report.top1_accuracy <= 1.0
    assert 0.0 <= report.top5_accuracy <= 1.0
    assert report.top1_accuracy <= report.top5_accuracy
    assert 0.0 <= report.mean_reciprocal_rank <= 1.0
    payload = report.to_dict()
    assert payload["not_legal_advice"] is True
    assert "per_chapter" in payload
    assert "confusion" in payload


@pytest.mark.skipif(not _have_fixtures(), reason="no case-law fixtures present")
def test_recommend_per_chapter_aggregation(fixtures):
    """Tags use inline-list YAML; the chapter parser must coerce strings."""
    import score_recommend
    report = score_recommend.score(fixtures, top_k=5, max_candidates=60)
    # At least one chapter slice must have populated stats — every fixture
    # we ship carries a `chapter:*` tag.
    assert report.per_chapter, "no per-chapter slices populated"
    for chap, stats in report.per_chapter.items():
        assert stats["n"] >= 1
        assert 0.0 <= stats["top1_accuracy"] <= 1.0


@pytest.mark.skipif(not _have_fixtures(), reason="no case-law fixtures present")
def test_contrast_scorer_runs_only_for_alternative_fixtures(fixtures):
    import score_contrast
    report = score_contrast.score(fixtures)
    n_alt = sum(1 for fx in fixtures if fx.get("alternative_charge"))
    assert report.n_with_alternative == n_alt
    # F1 / Jaccard always in [0, 1].
    for fr in report.fixtures:
        assert 0.0 <= fr.f1 <= 1.0
        assert 0.0 <= fr.jaccard <= 1.0
    payload = report.to_dict()
    assert payload["not_legal_advice"] is True


@pytest.mark.skipif(not _have_fixtures(), reason="no case-law fixtures present")
def test_constrained_contrast_classifies_every_fixture(fixtures):
    """Every fixture with court_distinguished_on must land in one
    of: consistent / unsat / no-element-in-encoding / error."""
    import score_contrast_constrained
    report = score_contrast_constrained.score(fixtures)
    valid_statuses = {"consistent", "unsat", "no-element-in-encoding"}
    for rr in report.results:
        assert (rr.status in valid_statuses
                or rr.status.startswith("error:")), \
            f"unexpected status {rr.status!r} for {rr.fixture_id}"
    # Counts must sum to total.
    total = (report.n_consistent + report.n_unsat
             + report.n_no_encoding + report.n_error)
    assert total == report.n


@pytest.mark.skipif(not _have_fixtures(), reason="no case-law fixtures present")
def test_canonical_section_strips_limb_suffix():
    import score_recommend
    assert score_recommend._canonical_section("300(c)") == "300"
    assert score_recommend._canonical_section("s302") == "302"
    assert score_recommend._canonical_section("S.376AA") == "376AA"
    assert score_recommend._canonical_section("Section 415.") == "415"
    assert score_recommend._canonical_section(None) == ""


def test_chapter_tag_handles_inline_list_string():
    """The mini-YAML fallback parses inline-list tags as a string;
    the parser must coerce to a list."""
    import score_recommend
    assert score_recommend._chapter_tag(
        "[source:case-law, chapter:xvi, category:homicide]"
    ) == "xvi"
    assert score_recommend._chapter_tag(
        ["source:case-law", "chapter:xvii"]
    ) == "xvii"
    assert score_recommend._chapter_tag(None) is None
    assert score_recommend._chapter_tag("category:property") is None
