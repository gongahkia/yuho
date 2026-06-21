"""Tests for explicit exception defeat relation nodes."""

from __future__ import annotations

import pytest

from yuho.ast.nodes import RebutsRelation, UndercutsRelation
from yuho.ast.statute_lint import lint_module
from yuho.services.analysis import analyze_source
from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE


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


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_rebut_negates_conviction():
    import z3

    gen, solver = z3_for_relations(
        """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  exception base { "base" when FALSE }
  exception rebutter { "rebut" when TRUE rebuts base }
}
"""
    )
    solver.add(gen._consts["1_leaf_act"])
    solver.add(gen._consts["1_conviction"])
    assert solver.check() == z3.unsat


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_undercut_suppresses_target_without_negating_conviction():
    import z3

    gen, solver = z3_for_relations(
        """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  exception base { "base" when TRUE }
  exception blocker { "block" when TRUE undercuts base }
}
"""
    )
    solver.add(gen._consts["1_leaf_act"])
    solver.add(z3.Not(gen._consts["1_exc_base_fires"]))
    solver.add(gen._consts["1_exc_blocker_fires"])
    solver.add(gen._consts["1_conviction"])
    assert solver.check() == z3.sat


def relation_lint_messages(source: str) -> list[str]:
    result = analyze_source(source, file="<relations>", run_semantic=False)
    assert not result.parse_errors
    return [warning.message for warning in lint_module(result.ast)]


def z3_for_relations(source: str):
    result = analyze_source(source, file="<relations>", run_semantic=False)
    assert not result.parse_errors
    gen = Z3Generator()
    solver, _ = gen.generate(result.ast)
    return gen, solver
