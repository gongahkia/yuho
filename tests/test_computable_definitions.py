"""Computable statute definition support."""

from __future__ import annotations

from yuho.ast import nodes
from yuho.eval.facts import struct_from_facts
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.explain import DatalogExplainer


def _fact_path(*parts: str) -> nodes.ASTNode:
    expr: nodes.ASTNode = nodes.IdentifierNode("facts")
    for part in parts:
        expr = nodes.FieldAccessNode(base=expr, field_name=part)
    return expr


def _statute() -> nodes.StatuteNode:
    definition = nodes.DefinitionEntry(
        term="deceptive",
        definition=_fact_path("representation", "falsehood"),
    )
    return nodes.StatuteNode(
        section_number="1",
        title=nodes.StringLit("Computed"),
        definitions=(definition,),
        elements=(
            nodes.ElementNode(
                element_type="actus_reus",
                name="deception",
                description=nodes.IdentifierNode("deceptive"),
            ),
            nodes.ElementNode(
                element_type="circumstance",
                name="harm",
                description=nodes.IdentifierNode("deceptive"),
            ),
        ),
        penalty=None,
        illustrations=(),
    )


def test_runtime_elements_can_reference_computable_definition() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts({"representation": {"falsehood": True}}),
    )

    assert result.overall_satisfied is True
    assert result.bindings() == {"deception": True, "harm": True}


def test_runtime_computable_definition_can_fail() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts({"representation": {"falsehood": False}}),
    )

    assert result.overall_satisfied is False
    assert result.bindings() == {"deception": False, "harm": False}


def test_explainer_uses_computable_definition() -> None:
    trace = DatalogExplainer().explain(
        _statute(),
        {"representation": {"falsehood": True}},
    )

    assert trace.overall_satisfied is True
    assert [element.satisfied for element in trace.elements] == [True, True]
