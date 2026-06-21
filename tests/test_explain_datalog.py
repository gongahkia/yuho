"""Datalog-style explanation backend tests."""

from __future__ import annotations

from yuho.ast import nodes
from yuho.eval.interpreter import Value
from yuho.explain import DatalogExplainer


def test_datalog_explainer_traces_elements_and_all_of_group():
    statute = nodes.StatuteNode(
        section_number="1",
        title=nodes.StringLit("Demo"),
        definitions=(),
        elements=(
            nodes.ElementGroupNode(
                combinator="all_of",
                members=(
                    nodes.ElementNode("actus_reus", "taking", nodes.StringLit("takes")),
                    nodes.ElementNode("mens_rea", "intent", nodes.StringLit("intends")),
                ),
            ),
        ),
        penalty=None,
        illustrations=(),
    )

    trace = DatalogExplainer().explain(statute, {"taking": True, "intent": False})

    assert trace.overall_satisfied is False
    group = trace.elements[0]
    assert group.element_type == "all_of"
    assert group.satisfied is False
    assert [child.name for child in group.children] == ["taking", "intent"]
    assert group.children[0].satisfied is True
    assert group.children[1].reason == "fact 'intent' is missing or false"
    assert "satisfied(taking) :- fact(taking, true)." in trace.rules
    assert "satisfied(top_0) :- satisfied(taking), satisfied(intent)." in trace.rules


def test_datalog_explainer_any_of_group_is_satisfied_by_one_child():
    statute = nodes.StatuteNode(
        section_number="2",
        title=nodes.StringLit("Demo"),
        definitions=(),
        elements=(
            nodes.ElementGroupNode(
                combinator="any_of",
                members=(
                    nodes.ElementNode("circumstance", "minor", nodes.StringLit("minor")),
                    nodes.ElementNode("circumstance", "weapon", nodes.StringLit("weapon")),
                ),
            ),
        ),
        penalty=None,
        illustrations=(),
    )

    trace = DatalogExplainer().explain(statute, {"weapon": Value(True, "bool")})

    assert trace.overall_satisfied is True
    assert trace.elements[0].reason == "at least one child element is satisfied"
    assert "satisfied(top_0) :- satisfied(minor); satisfied(weapon)." in trace.rules


def test_datalog_explainer_traces_civil_primitives():
    statute = nodes.StatuteNode(
        section_number="3",
        title=nodes.StringLit("Civil"),
        definitions=(),
        elements=(
            nodes.CivilPrimitiveNode(
                primitive_type="obligation_to",
                name="deliver_goods",
                description=nodes.StringLit("deliver"),
            ),
        ),
        penalty=None,
        illustrations=(),
    )

    trace = DatalogExplainer().explain(statute, {"deliver_goods": True})

    assert trace.overall_satisfied is True
    assert trace.elements[0].element_type == "obligation_to"
    assert trace.elements[0].reason == "fact 'deliver_goods' is truthy"
