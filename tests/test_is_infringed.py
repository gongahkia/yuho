"""Tests for the lam4-style IS_INFRINGED predicate."""

from __future__ import annotations

from yuho.ast import nodes
from yuho.library.graph_lint import (
    check_is_infringed_resolution,
    lint_reference_graph,
)
from yuho.library.reference_graph import (
    ReferenceEdge,
    ReferenceGraph,
    is_infringed,
)
from yuho.services.analysis import analyze_source


def _walk(root):
    stack = [root]
    while stack:
        n = stack.pop()
        yield n
        children = n.children() if hasattr(n, "children") else []
        for c in children:
            if isinstance(c, nodes.ASTNode):
                stack.append(c)


def _find_is_infringed(module):
    return [n for n in _walk(module) if isinstance(n, nodes.IsInfringedNode)]


class TestASTLifting:
    def test_identifier_form(self):
        src = '''
        fn check() : bool {
            return is_infringed(s299);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        nodes_found = _find_is_infringed(result.ast)
        assert len(nodes_found) == 1
        assert nodes_found[0].section_ref == "299"

    def test_int_literal_form(self):
        src = '''
        fn check() : bool {
            return is_infringed(300);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        nodes_found = _find_is_infringed(result.ast)
        assert len(nodes_found) == 1
        assert nodes_found[0].section_ref == "300"

    def test_string_literal_with_alpha_suffix(self):
        src = '''
        fn check() : bool {
            return is_infringed("376AA");
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        nodes_found = _find_is_infringed(result.ast)
        assert len(nodes_found) == 1
        assert nodes_found[0].section_ref == "376AA"

    def test_unrecognised_argument_remains_function_call(self):
        # Free variable, not a section ref -> stays a regular function call.
        src = '''
        fn check(string facts) : bool {
            return is_infringed(facts);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        is_inf = _find_is_infringed(result.ast)
        assert is_inf == []

    def test_other_function_calls_unaffected(self):
        src = '''
        fn check() : bool {
            return some_other_fn(s299);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        assert _find_is_infringed(result.ast) == []


class TestResolverPredicate:
    def test_existing_section_returns_true(self):
        g = ReferenceGraph()
        g.add(ReferenceEdge(src="299", dst="300", kind="subsumes", source_path="x"))
        assert is_infringed(g, "299") is True
        assert is_infringed(g, "s299") is True
        assert is_infringed(g, "Section 299") is True

    def test_missing_section_returns_false(self):
        g = ReferenceGraph()
        g.add(ReferenceEdge(src="299", dst="300", kind="subsumes", source_path="x"))
        assert is_infringed(g, "999") is False


class TestLintResolution:
    def test_unresolved_reference_flagged(self):
        src = '''
        fn check() : bool {
            return is_infringed(s9999);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        warnings = check_is_infringed_resolution(result.ast, known_sections=["299", "300"])
        assert len(warnings) == 1
        w = warnings[0]
        assert w.code == "is_infringed_unresolved"
        assert w.sections == ("9999",)

    def test_resolved_reference_not_flagged(self):
        src = '''
        fn check() : bool {
            return is_infringed(s299);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        warnings = check_is_infringed_resolution(result.ast, known_sections=["299"])
        assert warnings == []

    def test_lint_module_kwarg_routing(self):
        # When `module=` is passed to lint_reference_graph, the unresolved
        # is_infringed checker should fire alongside the SCC analysis.
        g = ReferenceGraph()
        g.add(ReferenceEdge(src="299", dst="300", kind="implicit", source_path="x"))
        src = 'fn f() : bool { return is_infringed(s99999); }'
        result = analyze_source(src, run_semantic=False)
        warnings = lint_reference_graph(g, module=result.ast)
        assert any(w.code == "is_infringed_unresolved" for w in warnings)
