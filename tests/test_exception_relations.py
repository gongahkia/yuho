"""Tests for explicit exception defeat relation nodes."""

from __future__ import annotations

from yuho.ast.nodes import RebutsRelation, UndercutsRelation
from yuho.services.analysis import analyze_source


def test_builder_maps_rebuts_and_undercuts_relations():
    source = """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  exception a { "a" when TRUE rebuts b }
  exception b { "b" when TRUE undercuts a }
}
"""
    result = analyze_source(source, file="<relations>", run_semantic=False)
    assert not result.parse_errors
    statute = result.ast.statutes[0]
    rebuts, undercuts = statute.exceptions
    assert rebuts.defeats == "b"
    assert isinstance(rebuts.defeat_relation, RebutsRelation)
    assert rebuts.defeat_relation.target == "b"
    assert undercuts.defeats == "a"
    assert isinstance(undercuts.defeat_relation, UndercutsRelation)
    assert undercuts.defeat_relation.target == "a"
