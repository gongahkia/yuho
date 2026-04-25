"""Tests for the counter-example explorer.

The explorer relies on Z3 being installed; tests skip cleanly when it
is not. Where possible we run on a real encoded section (s415 cheating)
to exercise the full Z3Generator -> CounterexampleExplorer pipeline.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
S415_PATH = REPO / "library" / "penal_code" / "s415_cheating" / "statute.yh"


# Z3 may be installed in the .venv-scrape env but not in the test
# runner's env. Skip in that case rather than fail.
z3 = pytest.importorskip("z3", reason="z3 not installed")


def _analyze(file_path: Path):
    from yuho.services.analysis import analyze_file
    return analyze_file(str(file_path), run_semantic=False)


@pytest.fixture(scope="module")
def s415_module():
    if not S415_PATH.exists():
        pytest.skip("s415 fixture not present")
    analysis = _analyze(S415_PATH)
    if analysis.parse_errors or analysis.ast is None:
        pytest.skip(f"s415 failed to parse: {analysis.parse_errors!r}")
    return analysis.ast


class TestExplorerCore:
    def test_explore_section_returns_report(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_section("415")
        assert report.available is True
        assert report.section == "415"
        assert report.summary["n_leaf_elements"] >= 1

    def test_explore_section_finds_satisfying(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_section("415", max_satisfying=3)
        assert report.summary["conviction_reachable"] is True
        assert len(report.satisfying) >= 1
        first = report.satisfying[0]
        # Every reported scenario must include at least one element variable.
        assert first.elements

    def test_explore_section_load_bearing(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_section("415")
        # Every leaf element should be load-bearing (s415 has no any_of
        # group at the top level besides the mens-rea sub-group, so most
        # elements are individually load-bearing).
        assert report.summary["n_load_bearing"] >= 1

    def test_unknown_section_yields_unavailable(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_section("9999")
        assert report.available is False
        assert "not found" in (report.reason or "")

    def test_report_serialises_to_json(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_section("415")
        # Must round-trip through json without exceptions.
        s = json.dumps(report.to_dict())
        roundtrip = json.loads(s)
        assert roundtrip["section"] == "415"
        assert roundtrip["available"] is True


class TestExploreFileHelper:
    def test_explore_file_top_level(self):
        if not S415_PATH.exists():
            pytest.skip("s415 fixture not present")
        from yuho.explore.counterexamples import explore_file
        result = explore_file(str(S415_PATH), "415", max_satisfying=2)
        assert result["ok"] is True
        rep = result["report"]
        assert rep["section"] == "415"
        assert rep["available"] is True

    def test_explore_file_unknown_section(self):
        if not S415_PATH.exists():
            pytest.skip("s415 fixture not present")
        from yuho.explore.counterexamples import explore_file
        result = explore_file(str(S415_PATH), "9999")
        assert result["ok"] is True            # parse OK
        assert result["report"]["available"] is False


class TestCLI:
    def test_cli_smoke(self):
        if not S415_PATH.exists():
            pytest.skip("s415 fixture not present")
        venv_yuho = REPO / ".venv-scrape" / "bin" / "yuho"
        if not venv_yuho.exists():
            pytest.skip("scrape venv not available")
        out = subprocess.run(
            [str(venv_yuho), "explore", str(S415_PATH), "415", "--json"],
            capture_output=True, text=True, timeout=30,
        )
        assert out.returncode == 0, f"CLI exited {out.returncode}: {out.stderr}"
        payload = json.loads(out.stdout)
        assert payload["ok"] is True
        assert payload["report"]["section"] == "415"


class TestRendering:
    def test_text_report_contains_summary(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer, render_report_text
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_section("415")
        text = render_report_text(report)
        assert "elements:" in text
        assert "Satisfying scenarios" in text


class TestSubsumption:
    """Tier 2 #4: subsumption query — does section A convict on the same
    facts as section B?"""

    def test_self_subsumption_is_equal(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_subsumption("415", "415")
        assert report.available is True
        assert report.relation == "equal"
        # By definition, when comparing a section to itself, no a-only or
        # b-only witness should exist (modulo the renamed variables).
        assert report.a_only_witness is None
        assert report.b_only_witness is None

    def test_unknown_section_yields_unavailable(self, s415_module):
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(s415_module)
        report = explorer.explore_subsumption("415", "9999")
        assert report.available is False
        assert "not found" in (report.reason or "").lower()

    def test_synthetic_two_section_overlap(self, tmp_path):
        """Synthesise a tiny two-statute module to exercise the cross-section
        path. s100 has elements (a, b); s101 has elements (a, c). They share
        ``a`` symbolically but the Z3 generator names per-statute, so any
        binding satisfying both convictions is the overlap case."""
        src = (
            'statute 100 "alpha" effective 1872-01-01 {\n'
            '  elements {\n'
            '    actus_reus a := "act a";\n'
            '    mens_rea  b := "mens b";\n'
            '  }\n'
            '  penalty cumulative { fine := unlimited; }\n'
            '}\n'
            'statute 101 "beta" effective 1872-01-01 {\n'
            '  elements {\n'
            '    actus_reus a := "act a";\n'
            '    mens_rea  c := "mens c";\n'
            '  }\n'
            '  penalty cumulative { fine := unlimited; }\n'
            '}\n'
        )
        from yuho.services.analysis import analyze_source
        analysis = analyze_source(src, file="<synth>", run_semantic=False)
        if analysis.parse_errors or analysis.ast is None:
            pytest.skip(f"synthetic source did not parse: {analysis.parse_errors!r}")
        from yuho.explore.counterexamples import CounterexampleExplorer
        explorer = CounterexampleExplorer(analysis.ast)
        report = explorer.explore_subsumption("100", "101")
        assert report.available is True
        # Independent statutes with no defeats / temporal links should
        # admit overlap (both convict simultaneously) and a/b-only witnesses.
        assert report.relation == "overlap", \
            f"expected overlap for independent sections, got {report.relation}"
        assert report.overlap_witness is not None
        assert report.a_only_witness is not None
        assert report.b_only_witness is not None
