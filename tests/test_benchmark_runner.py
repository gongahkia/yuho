"""Tests for the Yuho LLM legal-reasoning benchmark runner.

Pins:
- Fixture loader handles both block and inline list syntax
  (the bundled fixtures use `[a, b, c]` for compactness).
- F1 scoring on the element-set task is correct on edge cases
  (empty sets, partial overlap, total mismatch).
- Section / exception canonicalisation strips prefixes and
  punctuation as documented.
- The FakeClient + run_benchmark loop scores every bundled
  fixture at 100%.
- Per-fixture errors don't kill the run; they're surfaced as
  zero scores with an `<error: …>` predicted token.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
BENCHMARK = REPO / "benchmark"

sys.path.insert(0, str(BENCHMARK))
import run as bench  # type: ignore  # noqa: E402


def _all_fixtures():
    return bench.load_fixtures(BENCHMARK / "fixtures")


def test_fixture_loader_handles_inline_lists():
    fixtures = _all_fixtures()
    assert len(fixtures) >= 20
    s415 = next(fx for fx in fixtures if fx.id == "s415-classic")
    assert s415.truth_section == "415"
    assert "deception" in s415.truth_elements
    assert "fraudulent" in s415.truth_elements
    assert s415.truth_exception is None
    # tags also use inline-list syntax in the bundled fixtures.
    assert any(t.startswith("chapter:") for t in s415.tags)


def test_canonical_section_strips_prefixes_and_punctuation():
    assert bench._canonical_section("s415") == "415"
    assert bench._canonical_section("S.415") == "415"
    assert bench._canonical_section("Section 415") == "415"
    assert bench._canonical_section("415.") == "415"
    assert bench._canonical_section("  376AA  ") == "376AA"


def test_canonical_exception_canonicalises_none():
    assert bench._canonical_exception(None) == "none"
    assert bench._canonical_exception("") == "none"
    assert bench._canonical_exception(" Private Defence ") == "private_defence"


def test_f1_scorer_edge_cases():
    # Empty sets — both empty is a perfect score.
    f1, p, r = bench._f1([], [])
    assert (f1, p, r) == (1.0, 1.0, 1.0)
    # One side empty.
    f1, p, r = bench._f1(["a"], [])
    assert f1 == 0.0
    f1, p, r = bench._f1([], ["a"])
    assert f1 == 0.0
    # Total overlap.
    f1, p, r = bench._f1(["a", "b"], ["b", "a"])
    assert f1 == 1.0
    # Partial overlap: predicted = {a, b}, expected = {a, c} → P=0.5, R=0.5, F1=0.5
    f1, p, r = bench._f1(["a", "b"], ["a", "c"])
    assert p == 0.5 and r == 0.5 and f1 == 0.5


def test_parse_elements_handles_json_and_list_strings():
    assert bench._parse_elements('["a", "b", "c"]') == ["a", "b", "c"]
    assert bench._parse_elements("a, b, c") == ["a", "b", "c"]
    assert bench._parse_elements("[a, b]") == ["a", "b"]
    assert bench._parse_elements("") == []
    # Single-element fallback.
    assert bench._parse_elements("solo_element") == ["solo_element"]


def test_fake_client_end_to_end_scores_all_correct():
    fixtures = _all_fixtures()
    client = bench.FakeClient(fixtures=fixtures)
    result = bench.run_benchmark(fixtures, client)
    assert result.n == len(fixtures)
    assert result.task_accuracy("t1_section") == 1.0
    assert result.task_accuracy("t2_elements") == 1.0
    assert result.task_accuracy("t3_exception") == 1.0
    assert result.mean_f1() == pytest.approx(1.0)


def test_to_dict_carries_required_fields():
    fixtures = _all_fixtures()[:3]
    client = bench.FakeClient(fixtures=fixtures)
    result = bench.run_benchmark(fixtures, client)
    payload = result.to_dict()
    assert payload["n"] == 3
    assert payload["not_legal_advice"] is True
    assert "t1_accuracy" in payload
    assert "t2_mean_f1" in payload
    assert len(payload["fixtures"]) == 3
    for entry in payload["fixtures"]:
        assert "t1" in entry and "t2" in entry and "t3" in entry
        assert "elapsed_seconds" in entry


def test_per_fixture_error_does_not_kill_run():
    """A client raising mid-run yields a zero-scored FixtureResult."""

    class _BoomClient:
        def query(self, *a, **kw):
            raise RuntimeError("model unreachable")

    fixtures = _all_fixtures()[:2]
    result = bench.run_benchmark(fixtures, _BoomClient())
    assert result.n == 2
    for fr in result.fixtures:
        assert fr.t1_section.correct is False
        assert "<error:" in str(fr.t1_section.predicted)
        assert fr.t2_elements.f1 == 0.0


def test_render_report_includes_disclaimer():
    fixtures = _all_fixtures()[:1]
    client = bench.FakeClient(fixtures=fixtures)
    result = bench.run_benchmark(fixtures, client)
    text = bench.render_report(result)
    assert "Yuho LLM legal-reasoning benchmark" in text
    assert "Not legal advice" in text
    assert "T1 (section identification)" in text


def test_stratified_report_groups_by_tag_prefix():
    """The stratified accuracy slice keys on the `key:value` tag form."""
    fixtures = _all_fixtures()
    client = bench.FakeClient(fixtures=fixtures)
    result = bench.run_benchmark(fixtures, client)
    strat = result.stratified()
    # Bundled fixtures use chapter / category / difficulty / synth / polarity tags.
    assert "chapter" in strat
    assert "difficulty" in strat
    # Every slice value carries n + per-task accuracy.
    for prefix, by_value in strat.items():
        for value, row in by_value.items():
            assert row["n"] >= 1
            assert 0.0 <= row["t1_accuracy"] <= 1.0
            assert 0.0 <= row["t2_mean_f1"] <= 1.0
            assert 0.0 <= row["t3_accuracy"] <= 1.0


def test_render_report_includes_stratified_section():
    fixtures = _all_fixtures()
    client = bench.FakeClient(fixtures=fixtures)
    result = bench.run_benchmark(fixtures, client)
    text = bench.render_report(result, show_per_fixture=False)
    assert "Stratified by `chapter`" in text
    assert "Stratified by `difficulty`" in text
    # `--no-per-fixture` mode shouldn't render the per-row table heading.
    assert "Per-fixture:" not in text


def test_to_dict_includes_stratified_in_json():
    fixtures = _all_fixtures()[:5]
    client = bench.FakeClient(fixtures=fixtures)
    result = bench.run_benchmark(fixtures, client)
    payload = result.to_dict()
    assert "stratified" in payload
    assert isinstance(payload["stratified"], dict)
