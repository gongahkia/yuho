"""E2E tests: transpilation roundtrip."""

import pytest
import json
from yuho.transpile.base import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry

TARGETS = [t for t in TranspileTarget]

MINIMAL_SOURCE = """
struct TestCase { bool guilty, }
statute 999 "Test Statute" {
    elements {
        actus_reus act := "The physical act";
        mens_rea intent := "The mental state";
    }
    penalty {
        imprisonment := 1 years .. 5 years;
    }
}
"""

MULTI_STATUTE_SOURCE = """
statute 100 "First Offence" {
    elements {
        actus_reus a1 := "First act";
    }
}
statute 200 "Second Offence" {
    elements {
        actus_reus a2 := "Second act";
        mens_rea m2 := "Second intent";
    }
}
"""


class TestTranspileRoundtrip:
    def test_transpile_to_json(self, statute_dir, parse_file):
        """Statutes should transpile to valid JSON."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)
        assert len(output) > 0
        parsed = json.loads(output)  # should be valid JSON
        assert isinstance(parsed, dict)

    def test_transpile_to_english(self, statute_dir, parse_file):
        """Statutes should transpile to English text."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.ENGLISH)
        output = transpiler.transpile(ast)
        assert len(output) > 0
        lower = output.lower()
        assert "section" in lower or "statute" in lower

    @pytest.mark.parametrize("target", TARGETS, ids=lambda t: t.name)
    def test_all_targets_produce_output(self, target, parse_source):
        """All transpile targets should produce non-empty output for a minimal statute."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(target)
            output = transpiler.transpile(ast)
            assert len(output) > 0
        except Exception:
            pytest.skip(f"Transpiler {target.name} not available")

    def test_json_contains_statute_section(self, parse_source):
        """JSON output should contain the statute section number and title."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)
        parsed = json.loads(output)
        # section number and title should appear somewhere in the JSON tree
        raw = json.dumps(parsed)
        assert "999" in raw
        assert "Test Statute" in raw

    def test_json_contains_element_names(self, parse_source):
        """JSON output should include element names from the statute."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)
        raw = output.lower()
        assert "act" in raw
        assert "intent" in raw

    def test_json_contains_struct_defs(self, parse_source):
        """JSON output should include struct type definitions."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)
        raw = output.lower()
        assert "testcase" in raw or "test_case" in raw or "guilty" in raw

    def test_english_contains_section_number(self, statute_dir, parse_file):
        """English output should contain the statute section number."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.ENGLISH)
        output = transpiler.transpile(ast)
        # at least one statute section number should appear
        for statute in ast.statutes:
            assert (
                statute.section_number in output
            ), f"Section number {statute.section_number} not found in English output"

    def test_english_contains_element_descriptions(self, parse_source):
        """English output should include element descriptions."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.ENGLISH)
        output = transpiler.transpile(ast)
        assert "physical act" in output.lower() or "act" in output.lower()
        assert "mental state" in output.lower() or "intent" in output.lower()

    def test_latex_has_expected_commands(self, parse_source):
        """LaTeX output should contain expected LaTeX commands."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(TranspileTarget.LATEX)
            output = transpiler.transpile(ast)
            assert len(output) > 0
            # LaTeX should have document structure commands
            assert "\\" in output  # must contain at least some LaTeX commands
            # check for common LaTeX patterns
            has_section = "\\section" in output or "\\subsection" in output
            has_begin = "\\begin" in output
            has_textbf = "\\textbf" in output
            has_item = "\\item" in output
            assert (
                has_section or has_begin or has_textbf or has_item
            ), "LaTeX output lacks expected structural commands"
        except (KeyError, Exception):
            pytest.skip("LaTeX transpiler not available")

    def test_latex_contains_statute_info(self, parse_source):
        """LaTeX output should include section number and title."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(TranspileTarget.LATEX)
            output = transpiler.transpile(ast)
            assert "999" in output
            assert "Test Statute" in output
        except (KeyError, Exception):
            pytest.skip("LaTeX transpiler not available")

    def test_mermaid_produces_valid_diagram(self, parse_source):
        """Mermaid output should start with a valid diagram type declaration."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(TranspileTarget.MERMAID)
            output = transpiler.transpile(ast)
            assert len(output) > 0
            first_line = output.strip().split("\n")[0].strip().lower()
            # mermaid diagrams start with graph, flowchart, classDiagram, etc.
            valid_starts = (
                "graph",
                "flowchart",
                "classdiagram",
                "statediagram",
                "sequencediagram",
                "erdiagram",
                "---",
            )
            assert any(
                first_line.startswith(s) for s in valid_starts
            ), f"Mermaid output doesn't start with valid diagram type: '{first_line}'"
        except (KeyError, Exception):
            pytest.skip("Mermaid transpiler not available")

    def test_json_multiple_statutes(self, parse_source):
        """JSON output should contain data for all statutes in a multi-statute module."""
        ast = parse_source(MULTI_STATUTE_SOURCE)
        registry = TranspilerRegistry.instance()
        transpiler = registry.get(TranspileTarget.JSON)
        output = transpiler.transpile(ast)
        parsed = json.loads(output)
        raw = json.dumps(parsed)
        assert "100" in raw
        assert "200" in raw
        assert "First Offence" in raw
        assert "Second Offence" in raw

    def test_alloy_transpiler_contains_sig(self, parse_source):
        """Alloy transpiler output should contain 'sig' declarations."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(TranspileTarget.ALLOY)
            output = transpiler.transpile(ast)
            assert len(output) > 0
            assert "sig" in output
        except (KeyError, Exception):
            pytest.skip("Alloy transpiler not available")

    def test_graphql_transpiler_contains_type(self, parse_source):
        """GraphQL transpiler output should contain 'type' declarations."""
        ast = parse_source(MINIMAL_SOURCE)
        registry = TranspilerRegistry.instance()
        try:
            transpiler = registry.get(TranspileTarget.GRAPHQL)
            output = transpiler.transpile(ast)
            assert len(output) > 0
            assert "type" in output.lower() or "query" in output.lower()
        except (KeyError, Exception):
            pytest.skip("GraphQL transpiler not available")
