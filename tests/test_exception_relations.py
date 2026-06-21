"""Tests for explicit exception defeat relation nodes."""

from __future__ import annotations

from yuho.ast.nodes import RebutsRelation, UndercutsRelation
from yuho.ast.statute_lint import lint_module
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


def test_lint_detects_rebuts_cycles_separately():
    messages = relation_lint_messages(
        """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  exception a { "a" when TRUE rebuts b }
  exception b { "b" when TRUE rebuts a }
}
"""
    )
    assert any("rebuts chain forms a cycle" in message for message in messages)
    assert not any("undercuts chain forms a cycle" in message for message in messages)


def test_lint_detects_undercuts_cycles_separately():
    messages = relation_lint_messages(
        """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  exception a { "a" when TRUE undercuts b }
  exception b { "b" when TRUE undercuts a }
}
"""
    )
    assert any("undercuts chain forms a cycle" in message for message in messages)
    assert not any("rebuts chain forms a cycle" in message for message in messages)


def test_lint_does_not_mix_rebuts_and_undercuts_cycles():
    messages = relation_lint_messages(
        """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  exception a { "a" when TRUE rebuts b }
  exception b { "b" when TRUE undercuts a }
}
"""
    )
    assert not any("chain forms a cycle" in message for message in messages)


def relation_lint_messages(source: str) -> list[str]:
    result = analyze_source(source, file="<relations>", run_semantic=False)
    assert not result.parse_errors
    return [warning.message for warning in lint_module(result.ast)]
