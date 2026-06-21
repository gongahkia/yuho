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


class TestTreatmentLint:
    def test_overruled_case_cited_as_section_authority(self):
        g = _g()
        _add(g, "case:New v Case", "case:Old v Case", kind="treatment_overruled")
        _add(g, "415", "case:Old v Case", kind="authority")

        warnings = lint_reference_graph(g)

        assert any(w.code == "overruled_authority_cited" for w in warnings)
        warning = next(w for w in warnings if w.code == "overruled_authority_cited")
        assert warning.sections == ("415", "case:Old v Case", "case:New v Case")
        assert "Old v Case" in warning.message

    def test_overruled_case_followed_by_later_case(self):
        g = _g()
        _add(g, "case:New v Case", "case:Old v Case", kind="treatment_overruled")
        _add(g, "case:Later v Case", "case:Old v Case", kind="treatment_followed")

        warnings = lint_reference_graph(g)

        assert any(w.code == "overruled_authority_cited" for w in warnings)

    def test_contradictory_treatment_pair(self):
        g = _g()
        _add(g, "case:New v Case", "case:Old v Case", kind="treatment_followed")
        _add(g, "case:New v Case", "case:Old v Case", kind="treatment_overruled")

        warnings = lint_reference_graph(g)

        assert any(w.code == "contradictory_treatment" for w in warnings)
        warning = next(w for w in warnings if w.code == "contradictory_treatment")
        assert warning.sections == ("case:New v Case", "case:Old v Case")
        assert "followed" in warning.message and "overruled" in warning.message

    def test_overruled_case_not_cited_has_no_warning(self):
        g = _g()
        _add(g, "case:New v Case", "case:Old v Case", kind="treatment_overruled")

        warnings = lint_reference_graph(g)

        assert all(w.code != "overruled_authority_cited" for w in warnings)
