"""Tests for Catala-style apply_scope() composition."""

from __future__ import annotations

from yuho.ast import nodes
from yuho.library.graph_lint import (
    check_apply_scope_resolution,
    lint_reference_graph,
)
from yuho.library.reference_graph import (
    ReferenceEdge,
    ReferenceGraph,
    can_apply_scope,
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


def _find_apply_scope(module):
    return [n for n in _walk(module) if isinstance(n, nodes.ApplyScopeNode)]


class TestASTLifting:
    def test_basic_one_arg(self):
        src = '''
        fn check() : bool {
            return apply_scope(s299);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        nodes_found = _find_apply_scope(result.ast)
        assert len(nodes_found) == 1
        assert nodes_found[0].section_ref == "299"
        assert nodes_found[0].args == ()

    def test_with_extra_args(self):
        src = '''
        fn check(string facts) : bool {
            return apply_scope(s299, facts);
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        nodes_found = _find_apply_scope(result.ast)
        assert len(nodes_found) == 1
        assert nodes_found[0].section_ref == "299"
        assert len(nodes_found[0].args) == 1

    def test_apply_scope_with_alpha_suffix_section(self):
        src = '''
        fn f() : bool { return apply_scope("376AA"); }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        nodes_found = _find_apply_scope(result.ast)
        assert nodes_found[0].section_ref == "376AA"

    def test_unrecognised_first_arg_stays_function_call(self):
        src = '''
        fn f(string facts) : bool { return apply_scope(facts); }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        assert _find_apply_scope(result.ast) == []

    def test_apply_scope_does_not_collide_with_is_infringed(self):
        src = '''
        fn f() : bool {
            let x := is_infringed(s299);
            let y := apply_scope(s299);
            return x;
        }
        '''
        result = analyze_source(src, run_semantic=False)
        assert not result.parse_errors
        is_inf = [n for n in _walk(result.ast) if isinstance(n, nodes.IsInfringedNode)]
        scopes = _find_apply_scope(result.ast)
        assert len(is_inf) == 1
        assert len(scopes) == 1


class TestResolverPredicate:
    def test_can_apply_scope_existing(self):
        g = ReferenceGraph()
        g.add(ReferenceEdge(src="299", dst="300", kind="subsumes", source_path="x"))
        assert can_apply_scope(g, "299") is True

    def test_can_apply_scope_missing(self):
        g = ReferenceGraph()
        assert can_apply_scope(g, "9999") is False


class TestLintResolution:
    def test_unresolved_flagged(self):
        src = 'fn f() : bool { return apply_scope(s9999); }'
        result = analyze_source(src, run_semantic=False)
        warnings = check_apply_scope_resolution(result.ast, known_sections=["299"])
        assert len(warnings) == 1
        assert warnings[0].code == "apply_scope_unresolved"
        assert warnings[0].sections == ("9999",)

    def test_resolved_not_flagged(self):
        src = 'fn f() : bool { return apply_scope(s299); }'
        result = analyze_source(src, run_semantic=False)
        warnings = check_apply_scope_resolution(result.ast, known_sections=["299"])
        assert warnings == []

    def test_lint_module_kwarg_routing(self):
        g = ReferenceGraph()
        g.add(ReferenceEdge(src="100", dst="200", kind="implicit", source_path="x"))
        src = 'fn f() : bool { return apply_scope(s99999); }'
        result = analyze_source(src, run_semantic=False)
        warnings = lint_reference_graph(g, module=result.ast)
        assert any(w.code == "apply_scope_unresolved" for w in warnings)
