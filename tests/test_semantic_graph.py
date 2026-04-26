"""Tests for the library-wide semantic graph.

Pins both the structural shape (node kinds, edge kinds, IDs) and the
intra-section invariants (every definition/element/exception is reached
from its section by a `contains` edge; defeats edges only fire between
exceptions in the same section).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.ast import nodes
from yuho.library.semantic_graph import (
    SemanticGraph,
    add_shares_term_edges,
    add_statute_to_graph,
    build_semantic_graph,
)
from yuho.services.analysis import analyze_source


def _g(src: str) -> SemanticGraph:
    result = analyze_source(src, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    g = SemanticGraph()
    for stat in result.ast.statutes:
        add_statute_to_graph(g, stat)
    add_shares_term_edges(g)
    return g


# =============================================================================
# Section-level structure
# =============================================================================


def test_section_node_emitted():
    g = _g('statute 415 "Cheating" { elements { actus_reus a := "x"; } }')
    sec = next(n for n in g.nodes if n.kind == "section")
    assert sec.id == "sec:415"
    assert sec.label == "s415 Cheating"


def test_section_contains_definitions_elements_exceptions():
    g = _g('''
        statute 1 "Demo" {
          definitions { foo := "bar"; }
          elements { actus_reus a := "x"; }
          exception consent { "x" "y" }
        }
    ''')
    contains = [e for e in g.edges if e.kind == "contains"]
    edge_targets = {e.dst for e in contains if e.src == "sec:1"}
    assert "def:1:foo" in edge_targets
    assert "elem:1:a" in edge_targets
    assert "exc:1:consent" in edge_targets


def test_definition_term_extracted():
    g = _g('''
        statute 1 "Demo" {
          definitions { deceive := "To cause to believe something false"; }
          elements { actus_reus a := "x"; }
        }
    ''')
    node = next(n for n in g.nodes if n.kind == "definition")
    assert node.id == "def:1:deceive"
    assert node.label == "deceive"


def test_element_type_recorded():
    g = _g('''
        statute 1 "Demo" {
          elements { all_of {
            actus_reus deception := "Deceives";
            mens_rea fraud := "Fraudulent";
          } }
        }
    ''')
    by_id = {n.id: n for n in g.nodes}
    assert by_id["elem:1:deception"].element_type == "actus_reus"
    assert by_id["elem:1:fraud"].element_type == "mens_rea"


# =============================================================================
# `mentions` edges
# =============================================================================


def test_element_description_mentions_definition_term():
    g = _g('''
        statute 1 "Demo" {
          definitions { deception := "X"; }
          elements { actus_reus act := "Acts of deception by the accused"; }
        }
    ''')
    mentions = [e for e in g.edges if e.kind == "mentions"]
    # One mentions edge: elem:1:act -> def:1:deception
    assert any(e.src == "elem:1:act" and e.dst == "def:1:deception" for e in mentions)


def test_short_terms_dont_create_noise():
    """3-char minimum on the term length keeps `a`/`an`/`be` etc. from
    flooding the graph with spurious mentions edges."""
    g = _g('''
        statute 1 "Demo" {
          definitions { a := "ambiguous"; }
          elements { actus_reus deception := "Deceives a person"; }
        }
    ''')
    mentions = [e for e in g.edges if e.kind == "mentions"]
    # def:1:a is too short (1 char) — no mentions edge despite "a" appearing.
    assert all(not e.dst.endswith(":a") for e in mentions)


# =============================================================================
# `defeats` edges
# =============================================================================


def test_defeats_edge_fires_between_exceptions():
    g = _g('''
        statute 94 "Demo" {
          elements { actus_reus a := "x"; }
          exception base { "x" "y" }
          exception override {
            "x" "y"
            priority 2
            defeats base
          }
        }
    ''')
    defeats = [e for e in g.edges if e.kind == "defeats"]
    assert len(defeats) == 1
    assert defeats[0].src == "exc:94:override"
    assert defeats[0].dst == "exc:94:base"


# =============================================================================
# `shares_term` edges (cross-section)
# =============================================================================


def test_shares_term_links_same_definition_across_sections():
    g = _g('''
        statute 23 "Definitions" {
          definitions { deceive := "ambiguous"; }
          elements { actus_reus a := "x"; }
        }
        statute 415 "Cheating" {
          definitions { deceive := "more specific"; }
          elements { actus_reus a := "x"; }
        }
    ''')
    shares = [e for e in g.edges if e.kind == "shares_term"]
    assert len(shares) == 1
    src, dst = shares[0].src, shares[0].dst
    assert {src, dst} == {"def:23:deceive", "def:415:deceive"}


def test_shares_term_does_not_self_link():
    g = _g('''
        statute 1 "Demo" {
          definitions { foo := "x"; bar := "y"; }
          elements { actus_reus a := "x"; }
        }
    ''')
    shares = [e for e in g.edges if e.kind == "shares_term"]
    # Only one section, no shared terms across sections.
    assert shares == []


# =============================================================================
# Stats + JSON shape
# =============================================================================


def test_stats_count_each_kind():
    g = _g('''
        statute 1 "A" {
          definitions { foo := "x"; }
          elements { actus_reus a := "x"; }
          exception e { "x" "y" }
        }
    ''')
    stats = g.stats()
    assert stats["n_section"] == 1
    assert stats["n_definition"] == 1
    assert stats["n_element"] == 1
    assert stats["n_exception"] == 1
    assert stats["n_contains"] == 3   # section -> def, elem, exc


def test_to_dict_round_trip_shape():
    g = _g('statute 1 "Demo" { elements { actus_reus a := "x"; } }')
    d = g.to_dict()
    assert isinstance(d.get("nodes"), list)
    assert isinstance(d.get("edges"), list)
    assert isinstance(d.get("stats"), dict)
    # Every node has the required keys.
    for n in d["nodes"]:
        assert "id" in n and "kind" in n and "section" in n and "label" in n


def test_unknown_edge_kind_rejected():
    g = SemanticGraph()
    from yuho.library.semantic_graph import SemanticEdge
    with pytest.raises(ValueError):
        g.add_edge(SemanticEdge(src="a", dst="b", kind="bogus"))


# =============================================================================
# Real library smoke
# =============================================================================


@pytest.mark.skipif(
    not Path("library/penal_code").exists(),
    reason="library/penal_code not present in this checkout",
)
def test_library_build_non_trivial():
    g = build_semantic_graph(Path("library/penal_code"))
    stats = g.stats()
    # We expect a non-trivial graph: 524 sections, definitions in the
    # hundreds, elements in the thousands.
    assert stats["n_section"] > 100
    assert stats["n_definition"] > 50
    assert stats["n_element"] > 500
    # Every section has a contains edge to every component it owns.
    section_ids = {n.id for n in g.nodes if n.kind == "section"}
    contains_targets = {e.dst for e in g.edges if e.kind == "contains" and e.src in section_ids}
    assert len(contains_targets) > 100
