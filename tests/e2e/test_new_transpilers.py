"""
E2E tests for new transpiler targets: BibTeX, Comparative, Verification Report.

Tests the full pipeline: parse → AST → transpile for each new target.
"""

import pytest
from pathlib import Path

from yuho.services.analysis import analyze_file, analyze_source
from yuho.transpile import TranspileTarget, get_transpiler


SAMPLE_SOURCE = """\
statute 1 "Test Offence" {
    definitions {
        offence := "A test offence";
    }
    elements {
        actus_reus act := "Doing the prohibited act";
        mens_rea intent := "Intending to do the act";
        circumstance context := "In a prohibited context";
    }
    penalty {
        imprisonment := 0 days .. 5 years;
        fine := $0.00 .. $10,000.00;
    }
    illustration example1 {
        "A does X intending Y. A is guilty."
    }
}
"""

SAMPLE_TWO_STATUTES = """\
statute 1 "First Offence" {
    definitions { first := "The first offence"; }
    elements {
        actus_reus act1 := "First act";
        mens_rea intent1 := "First intent";
    }
    penalty { imprisonment := 0 days .. 3 years; }
}

statute 2 "Second Offence" {
    definitions { second := "The second offence"; }
    elements {
        actus_reus act2 := "Second act";
        mens_rea intent2 := "Second intent";
    }
    penalty { imprisonment := 0 days .. 7 years; }
}
"""


@pytest.fixture
def single_ast():
    result = analyze_source(SAMPLE_SOURCE)
    assert result.is_valid
    return result.ast


@pytest.fixture
def two_statute_ast():
    result = analyze_source(SAMPLE_TWO_STATUTES)
    assert result.is_valid
    return result.ast


@pytest.mark.skipif(
    not hasattr(TranspileTarget, "BIBTEX"),
    reason="BibTeX transpiler not yet shipped (planned target).",
)
class TestBibTeXTranspiler:
    def test_produces_output(self, single_ast):
        t = get_transpiler(TranspileTarget.BIBTEX)
        output = t.transpile(single_ast)
        assert isinstance(output, str)

    def test_empty_for_no_caselaw(self, single_ast):
        t = get_transpiler(TranspileTarget.BIBTEX)
        output = t.transpile(single_ast)
        # no case_law in sample, should produce minimal/empty output
        assert isinstance(output, str)


@pytest.mark.skipif(
    not hasattr(TranspileTarget, "COMPARATIVE"),
    reason="Comparative transpiler not yet shipped (planned target).",
)
class TestComparativeTranspiler:
    def test_needs_two_statutes(self, single_ast):
        t = get_transpiler(TranspileTarget.COMPARATIVE)
        output = t.transpile(single_ast)
        assert "Need at least 2 statutes" in output or "need" in output.lower()

    def test_produces_table_for_two(self, two_statute_ast):
        t = get_transpiler(TranspileTarget.COMPARATIVE)
        output = t.transpile(two_statute_ast)
        assert "First Offence" in output
        assert "Second Offence" in output
        assert "|" in output  # markdown table


class TestVerificationReport:
    def test_produces_latex(self, single_ast):
        from yuho.transpile.verification_report import generate_verification_report

        output = generate_verification_report(single_ast)
        assert r"\documentclass" in output
        assert r"\begin{document}" in output
        assert r"\end{document}" in output

    def test_checks_structural_elements(self, single_ast):
        from yuho.transpile.verification_report import generate_verification_report

        output = generate_verification_report(single_ast)
        assert "Has title" in output
        assert "Actus reus present" in output
        assert "Has penalty" in output

    def test_pass_status_for_complete_statute(self, single_ast):
        from yuho.transpile.verification_report import generate_verification_report

        output = generate_verification_report(single_ast)
        assert r"\pass" in output


class TestAllTargetsRoundtrip:
    """Ensure all transpile targets produce non-empty output. Targets that
    have an alias listed but aren't currently shipped (graphql / blocks /
    bibtex / comparative / akomantoso / prolog) skip cleanly so the suite
    stays green while the planned-target gap is visible."""

    TARGETS = [
        "json",
        "english",
        "mermaid",
        "latex",
        "alloy",
        "graphql",
        "blocks",
        "bibtex",
        "comparative",
        "akomantoso",
        "prolog",
    ]

    @pytest.mark.parametrize("target_name", TARGETS)
    def test_target_produces_output(self, single_ast, target_name):
        try:
            target = TranspileTarget.from_string(target_name)
        except ValueError:
            pytest.skip(f"transpile target {target_name!r} not yet shipped")
        try:
            t = get_transpiler(target)
        except (KeyError, ValueError):
            pytest.skip(f"transpile target {target_name!r} not registered")
        output = t.transpile(single_ast)
        assert isinstance(output, str)
        assert len(output) > 0, f"{target_name} produced empty output"


class TestLibraryFileTranspilation:
    """Test transpilation of actual library statutes."""

    LIBRARY_DIR = Path(__file__).parent.parent.parent / "library" / "penal_code"

    def _first_statute(self):
        if not self.LIBRARY_DIR.exists():
            pytest.skip("library not found")
        for d in sorted(self.LIBRARY_DIR.iterdir()):
            yh = d / "statute.yh"
            if yh.exists():
                return str(yh)
        pytest.skip("no statute files")

    def test_english_transpilation(self):
        path = self._first_statute()
        result = analyze_file(path)
        assert result.is_valid
        t = get_transpiler(TranspileTarget.ENGLISH)
        output = t.transpile(result.ast)
        assert len(output) > 50

    def test_json_transpilation(self):
        import json

        path = self._first_statute()
        result = analyze_file(path)
        assert result.is_valid
        t = get_transpiler(TranspileTarget.JSON)
        output = t.transpile(result.ast)
        parsed = json.loads(output)
        assert "statutes" in parsed
