"""Tests for the cross-section reference graph (G10)."""

from pathlib import Path

import pytest

from yuho.library.reference_graph import (
    ReferenceEdge,
    ReferenceGraph,
    _normalise_section,
    _scan_implicit_refs,
    build_reference_graph,
)


class TestNormalise:
    def test_strip_s_prefix(self):
        assert _normalise_section("s415") == "415"
        assert _normalise_section("S.415") == "415"
        assert _normalise_section("s. 415") == "415"

    def test_keep_alpha_suffix(self):
        assert _normalise_section("s376AA") == "376AA"

    def test_section_word(self):
        assert _normalise_section("Section 300") == "300"
        assert _normalise_section("section 300") == "300"

    def test_already_canonical(self):
        assert _normalise_section("415") == "415"


class TestScanImplicit:
    def test_short_form(self):
        assert _scan_implicit_refs("see s415 for details") == ["415"]

    def test_alpha_suffix(self):
        assert _scan_implicit_refs("subject to s376AA") == ["376AA"]

    def test_long_form(self):
        assert _scan_implicit_refs("under Section 300") == ["300"]

    def test_multiple(self):
        text = "compare s415 with section 420 and s. 425"
        assert _scan_implicit_refs(text) == ["415", "420", "425"]

    def test_no_false_positive_on_word_break(self):
        # "ss" alone shouldn't match.
        assert _scan_implicit_refs("the loss") == []

    def test_empty(self):
        assert _scan_implicit_refs("") == []


class TestReferenceGraph:
    def setup_method(self):
        self.g = ReferenceGraph()

    def test_add_and_query_outgoing(self):
        self.g.add(ReferenceEdge(src="300", dst="299", kind="subsumes", source_path="x"))
        outs = self.g.outgoing("300")
        assert len(outs) == 1
        assert outs[0].dst == "299"
        assert outs[0].kind == "subsumes"

    def test_incoming(self):
        self.g.add(ReferenceEdge(src="302", dst="300", kind="implicit", source_path="x"))
        ins = self.g.incoming("300")
        assert len(ins) == 1
        assert ins[0].src == "302"

    def test_kind_filter(self):
        self.g.add(ReferenceEdge(src="A", dst="B", kind="subsumes", source_path="x"))
        self.g.add(ReferenceEdge(src="A", dst="C", kind="implicit", source_path="x"))
        out_subsumes = self.g.outgoing("A", kinds=["subsumes"])
        assert len(out_subsumes) == 1
        assert out_subsumes[0].dst == "B"

    def test_reachable_from_transitive(self):
        # 302 → 300 → 299
        self.g.add(ReferenceEdge(src="302", dst="300", kind="implicit", source_path="x"))
        self.g.add(ReferenceEdge(src="300", dst="299", kind="subsumes", source_path="x"))
        reach = self.g.reachable_from("302")
        assert reach == {"300", "299"}

    def test_reachable_to_transitive(self):
        self.g.add(ReferenceEdge(src="302", dst="300", kind="implicit", source_path="x"))
        self.g.add(ReferenceEdge(src="304", dst="300", kind="implicit", source_path="x"))
        rev = self.g.reachable_to("300")
        assert rev == {"302", "304"}

    def test_reject_unknown_kind(self):
        with pytest.raises(ValueError):
            self.g.add(ReferenceEdge(src="A", dst="B", kind="bogus", source_path="x"))

    def test_to_dict_stats(self):
        self.g.add(ReferenceEdge(src="A", dst="B", kind="subsumes", source_path="x"))
        self.g.add(ReferenceEdge(src="A", dst="C", kind="implicit", source_path="x"))
        d = self.g.to_dict()
        assert d["stats"]["n_nodes"] == 3
        assert d["stats"]["n_edges"] == 2
        assert d["stats"]["n_subsumes"] == 1
        assert d["stats"]["n_implicit"] == 1


class TestSCC:
    """Tarjan SCC + cycle detection over the reference graph."""

    def setup_method(self):
        self.g = ReferenceGraph()

    def _add(self, src, dst, kind="implicit"):
        self.g.add(ReferenceEdge(src=src, dst=dst, kind=kind, source_path="x"))

    def test_empty_graph(self):
        assert self.g.find_sccs() == []
        assert self.g.cycles() == []
        assert not self.g.is_cyclic()

    def test_acyclic_chain(self):
        self._add("A", "B")
        self._add("B", "C")
        sccs = self.g.find_sccs()
        # three singletons, no cycles
        assert sorted([sorted(c) for c in sccs]) == [["A"], ["B"], ["C"]]
        assert self.g.cycles() == []
        assert not self.g.is_cyclic()

    def test_self_loop_is_cycle(self):
        self._add("A", "A")
        assert self.g.is_cyclic()
        cyc = self.g.cycles()
        assert cyc == [["A"]]

    def test_two_cycle(self):
        self._add("A", "B")
        self._add("B", "A")
        cyc = self.g.cycles()
        assert len(cyc) == 1
        assert sorted(cyc[0]) == ["A", "B"]
        assert self.g.is_cyclic()

    def test_three_cycle_with_tail(self):
        # tail D -> A -> B -> C -> A
        self._add("D", "A")
        self._add("A", "B")
        self._add("B", "C")
        self._add("C", "A")
        cyc = self.g.cycles()
        assert len(cyc) == 1
        assert sorted(cyc[0]) == ["A", "B", "C"]
        # D remains a singleton outside the cycle
        all_sccs = self.g.find_sccs()
        singletons = [c for c in all_sccs if len(c) == 1]
        assert ["D"] in singletons

    def test_kind_filter(self):
        # cycle exists in implicit edges only; subsumes is acyclic
        self._add("A", "B", kind="implicit")
        self._add("B", "A", kind="implicit")
        self._add("X", "Y", kind="subsumes")
        assert self.g.is_cyclic(kinds=["implicit"])
        assert not self.g.is_cyclic(kinds=["subsumes"])

    def test_disconnected_components(self):
        # one cyclic, one acyclic
        self._add("A", "B")
        self._add("B", "A")
        self._add("X", "Y")
        cyc = self.g.cycles()
        assert len(cyc) == 1
        assert sorted(cyc[0]) == ["A", "B"]

    def test_condensation_dag_is_acyclic(self):
        # build: cycle {A,B} -> singleton C
        self._add("A", "B")
        self._add("B", "A")
        self._add("A", "C")
        comps, dag = self.g.condensation_dag()
        # locate component indices
        for i, c in enumerate(comps):
            if "A" in c:
                cycle_idx = i
            if c == ["C"]:
                c_idx = i
        assert c_idx in dag[cycle_idx]
        # no self-loops in condensation
        for i, succs in dag.items():
            assert i not in succs

    def test_reverse_topological_order(self):
        # A -> B -> C, expect C emitted before B before A
        self._add("A", "B")
        self._add("B", "C")
        sccs = self.g.find_sccs()
        order = [c[0] for c in sccs]
        assert order.index("C") < order.index("B") < order.index("A")


@pytest.mark.skipif(
    not Path("library/penal_code").exists(),
    reason="library/penal_code not present in this checkout",
)
class TestBuildOnLibrary:
    """Smoke test against the encoded library."""

    def test_graph_builds_without_error(self):
        graph = build_reference_graph(Path("library/penal_code"))
        assert len(graph.nodes) > 0
        assert graph.edge_count() > 0

    def test_s300_subsumes_s299(self):
        graph = build_reference_graph(Path("library/penal_code"))
        out = graph.outgoing("300", kinds=["subsumes"])
        assert any(e.dst == "299" for e in out), \
            "s300 should subsume s299 per metadata"
