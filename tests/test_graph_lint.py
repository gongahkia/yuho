"""Tests for library-level reference-graph diagnostics."""

from yuho.library.reference_graph import ReferenceEdge, ReferenceGraph
from yuho.library.graph_lint import lint_reference_graph


def _g():
    return ReferenceGraph()


def _add(g, src, dst, kind="implicit"):
    g.add(ReferenceEdge(src=src, dst=dst, kind=kind, source_path="x"))


class TestCrossSectionCycle:
    def test_acyclic_no_warnings(self):
        g = _g()
        _add(g, "A", "B")
        _add(g, "B", "C")
        assert lint_reference_graph(g) == []

    def test_two_cycle_flagged(self):
        g = _g()
        _add(g, "A", "B")
        _add(g, "B", "A")
        warnings = lint_reference_graph(g)
        assert len(warnings) == 1
        w = warnings[0]
        assert w.code == "cross_section_cycle"
        assert w.severity == "warning"
        assert tuple(w.sections) == ("A", "B")

    def test_amend_chains_ignored_by_default(self):
        # legit amendment history is chainy/cyclic in some encodings; default
        # filter (implicit, subsumes) should not flag it.
        g = _g()
        _add(g, "A", "B", kind="amends")
        _add(g, "B", "A", kind="amends")
        assert lint_reference_graph(g) == []

    def test_explicit_kinds_can_include_amends(self):
        g = _g()
        _add(g, "A", "B", kind="amends")
        _add(g, "B", "A", kind="amends")
        warnings = lint_reference_graph(g, kinds=["amends"])
        assert len(warnings) == 1

    def test_self_reference(self):
        g = _g()
        _add(g, "A", "A", kind="implicit")
        warnings = lint_reference_graph(g)
        assert len(warnings) == 1
        assert warnings[0].sections == ("A",)
        assert "self-referential" in warnings[0].message

    def test_message_lists_sections(self):
        g = _g()
        _add(g, "A", "B")
        _add(g, "B", "C")
        _add(g, "C", "A")
        warnings = lint_reference_graph(g)
        assert len(warnings) == 1
        msg = warnings[0].message
        assert "sA" in msg and "sB" in msg and "sC" in msg
