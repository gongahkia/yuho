"""Datalog-style explanation backend for statute element satisfaction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from yuho.ast import nodes
from yuho.eval.facts import fact_reason, fact_truthy, normalize_facts, struct_from_facts
from yuho.eval.interpreter import Environment, Interpreter, InterpreterError, Value


@dataclass(frozen=True)
class ElementTrace:
    """Justification for one element or element group."""

    name: str
    element_type: str
    satisfied: bool
    rule: str
    reason: str
    children: tuple["ElementTrace", ...] = ()


@dataclass(frozen=True)
class JustificationTrace:
    """Trace returned by the Datalog-style explainer."""

    statute_section: str
    overall_satisfied: bool
    elements: tuple[ElementTrace, ...]
    rules: tuple[str, ...]


class DatalogExplainer:
    """Explain statute satisfaction by deriving element/group predicates."""

    def explain(
        self,
        statute: nodes.StatuteNode,
        facts: Mapping[str, object],
    ) -> JustificationTrace:
        normalized_facts = normalize_facts(facts)
        runtime_facts = struct_from_facts(normalized_facts)
        traces: list[ElementTrace] = []
        rules: list[str] = []
        overall = True
        for index, member in enumerate(statute.elements):
            trace = self._trace_member(
                member,
                normalized_facts,
                runtime_facts,
                statute.definitions,
                f"top_{index}",
                rules,
            )
            traces.append(trace)
            if not trace.satisfied:
                overall = False
        return JustificationTrace(
            statute_section=statute.section_number,
            overall_satisfied=overall,
            elements=tuple(traces),
            rules=tuple(rules),
        )

    def _trace_member(
        self,
        member: nodes.ASTNode,
        facts: Mapping[str, object],
        runtime_facts,
        definitions: tuple[nodes.DefinitionEntry, ...],
        fallback_name: str,
        rules: list[str],
    ) -> ElementTrace:
        if isinstance(member, nodes.ElementGroupNode):
            child_traces = tuple(
                self._trace_member(
                    child, facts, runtime_facts, definitions, f"{fallback_name}_{i}", rules
                )
                for i, child in enumerate(member.members)
            )
            if member.combinator == "any_of":
                satisfied = any(child.satisfied for child in child_traces)
                rule = self._rule_any(fallback_name, child_traces)
                reason = "at least one child element is satisfied"
            else:
                satisfied = all(child.satisfied for child in child_traces)
                rule = self._rule_all(fallback_name, child_traces)
                reason = "all child elements are satisfied"
            rules.append(rule)
            if not satisfied:
                reason = self._group_failure_reason(member.combinator, child_traces)
            return ElementTrace(
                name=fallback_name,
                element_type=member.combinator,
                satisfied=satisfied,
                rule=rule,
                reason=reason,
                children=child_traces,
            )

        if isinstance(member, nodes.CivilPrimitiveNode):
            name = member.name
            element_type = member.primitive_type
        elif isinstance(member, nodes.ElementNode):
            name = member.name
            element_type = member.element_type
        else:
            name = fallback_name
            element_type = type(member).__name__
        if isinstance(member, (nodes.ElementNode, nodes.CivilPrimitiveNode)) and not isinstance(
            member.description, nodes.StringLit
        ):
            satisfied = self._predicate_truthy(member.description, runtime_facts, definitions)
            rule = f"satisfied({name}) :- predicate({name})."
            reason = (
                "predicate expression is truthy" if satisfied else "predicate expression is false"
            )
        else:
            fact = facts.get(name)
            satisfied = fact_truthy(fact)
            rule = f"satisfied({name}) :- fact({name}, true)."
            reason = fact_reason(name, fact, satisfied)
        rules.append(rule)
        return ElementTrace(
            name=name,
            element_type=element_type,
            satisfied=satisfied,
            rule=rule,
            reason=reason,
        )

    @staticmethod
    def _rule_all(group_name: str, children: Sequence[ElementTrace]) -> str:
        body = ", ".join(f"satisfied({child.name})" for child in children)
        return f"satisfied({group_name}) :- {body}."

    @staticmethod
    def _rule_any(group_name: str, children: Sequence[ElementTrace]) -> str:
        body = "; ".join(f"satisfied({child.name})" for child in children)
        return f"satisfied({group_name}) :- {body}."

    @staticmethod
    def _group_failure_reason(
        combinator: str,
        children: Sequence[ElementTrace],
    ) -> str:
        failed = [child.name for child in children if not child.satisfied]
        if combinator == "any_of":
            return "no child element is satisfied"
        return f"unsatisfied child elements: {', '.join(failed)}"

    @staticmethod
    def _predicate_truthy(
        predicate: nodes.ASTNode,
        runtime_facts,
        definitions: tuple[nodes.DefinitionEntry, ...] = (),
    ) -> bool:
        env = Environment()
        env.set("facts", Value(raw=runtime_facts, type_tag="struct"))
        for key, value in runtime_facts.fields.items():
            env.set(key, value)
        interp = Interpreter(env)
        for definition in definitions:
            if isinstance(definition.definition, nodes.StringLit):
                continue
            try:
                env.set(definition.term, interp.visit(definition.definition))
            except InterpreterError:
                continue
        try:
            return interp.visit(predicate).is_truthy()
        except InterpreterError:
            return False
