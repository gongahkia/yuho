"""Tests for the charge-recommender.

Exercises the recommender against the s415 classic fixture (where the
expected top-1 is s415 itself) and the s378 theft fixture.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"
FIXTURES = REPO / "simulator" / "fixtures"
S415_FIX = FIXTURES / "s415_classic.yaml"
S378_FIX = FIXTURES / "s378_theft.yaml"


def _has_corpus():
    return (CORPUS / "sections").exists() and any((CORPUS / "sections").glob("s*.json"))


def _strip_section(facts):
    """Return facts with the section field removed — the recommender
    is what we want to rediscover it."""
    return {k: v for k, v in facts.items() if k != "section"}


@pytest.fixture(scope="module")
def s415_facts():
    if not S415_FIX.exists():
        pytest.skip("s415 fixture missing")
    import sys
    sim_dir = REPO / "simulator"
    if str(sim_dir) not in sys.path:
        sys.path.insert(0, str(sim_dir))
    import simulator as sim_mod  # type: ignore
    facts = sim_mod._load_yaml_or_json(S415_FIX)
    return _strip_section(facts)


@pytest.fixture(scope="module")
def s378_facts():
    if not S378_FIX.exists():
        pytest.skip("s378 fixture missing")
    import sys
    sim_dir = REPO / "simulator"
    if str(sim_dir) not in sys.path:
        sys.path.insert(0, str(sim_dir))
    import simulator as sim_mod  # type: ignore
    facts = sim_mod._load_yaml_or_json(S378_FIX)
    return _strip_section(facts)


class TestRecommenderCore:
    def test_returns_disclaimer_envelope(self, s415_facts):
        if not _has_corpus():
            pytest.skip("corpus not built")
        from yuho.recommend.charge_recommender import ChargeRecommender, LEGAL_DISCLAIMER
        rec = ChargeRecommender().recommend(s415_facts, top_k=3)
        d = rec.to_dict()
        assert d["not_legal_advice"] is True
        assert d["disclaimer"] == LEGAL_DISCLAIMER
        assert isinstance(d["candidates"], list)

    def test_s415_is_top_candidate(self, s415_facts):
        if not _has_corpus():
            pytest.skip("corpus not built")
        from yuho.recommend.charge_recommender import ChargeRecommender
        rec = ChargeRecommender().recommend(s415_facts, top_k=5)
        assert rec.candidates, "no candidates returned"
        top = rec.candidates[0]
        # The s415 classic fixture should rediscover s415 OR a closely
        # related section (e.g. s420 cheating-and-inducing-delivery).
        assert top.section in ("415", "420", "417"), (
            f"unexpected top recommendation: s{top.section} ({top.title})"
        )
        assert top.coverage > 0.0

    def test_s378_returns_property_offence(self, s378_facts):
        if not _has_corpus():
            pytest.skip("corpus not built")
        from yuho.recommend.charge_recommender import ChargeRecommender
        rec = ChargeRecommender().recommend(s378_facts, top_k=5)
        assert rec.candidates, "no candidates returned"
        top_sections = [c.section for c in rec.candidates]
        # s378 (theft) or one of its kin (s379/s380/s403/s405/s406) should rank.
        property_offences = {"378", "379", "380", "403", "405", "406", "411"}
        assert property_offences.intersection(top_sections), (
            f"expected one of {property_offences} in top {len(top_sections)}, "
            f"got {top_sections}"
        )

    def test_empty_facts_returns_no_candidates(self):
        if not _has_corpus():
            pytest.skip("corpus not built")
        from yuho.recommend.charge_recommender import ChargeRecommender
        rec = ChargeRecommender().recommend({}, top_k=3)
        assert rec.candidates == []
        assert rec.not_legal_advice is True


class TestRecommendHelper:
    def test_recommend_dict_output(self, s415_facts):
        if not _has_corpus():
            pytest.skip("corpus not built")
        from yuho.recommend.charge_recommender import recommend
        out = recommend(s415_facts, top_k=2)
        assert out["not_legal_advice"] is True
        assert "candidates" in out
        assert "disclaimer" in out
        assert len(out["candidates"]) <= 2


class TestRendering:
    def test_text_output_includes_disclaimer(self, s415_facts):
        if not _has_corpus():
            pytest.skip("corpus not built")
        from yuho.recommend.charge_recommender import (
            ChargeRecommender, render_recommendation_text, LEGAL_DISCLAIMER,
        )
        rec = ChargeRecommender().recommend(s415_facts, top_k=2)
        text = render_recommendation_text(rec)
        assert "NOT LEGAL ADVICE" in text
        assert LEGAL_DISCLAIMER in text


class TestCLI:
    def test_cli_smoke(self):
        if not _has_corpus():
            pytest.skip("corpus not built")
        if not S415_FIX.exists():
            pytest.skip("s415 fixture missing")
        venv_yuho = REPO / ".venv-test" / "bin" / "yuho"
        if not venv_yuho.exists():
            venv_yuho = REPO / ".venv-scrape" / "bin" / "yuho"
            if not venv_yuho.exists():
                pytest.skip("yuho CLI venv not available")
        result = subprocess.run(
            [str(venv_yuho), "recommend", str(S415_FIX), "--top-k", "3", "--json"],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, f"CLI failed ({result.returncode}): {result.stderr}"
        payload = json.loads(result.stdout)
        assert payload["not_legal_advice"] is True
        assert "candidates" in payload
