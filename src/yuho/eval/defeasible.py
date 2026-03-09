"""
Defeasible reasoning engine for Yuho statutes.

Implements exception-defeat logic: when evaluating facts against a statute,
exceptions with satisfied guards override conviction.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
from yuho.ast import nodes


@dataclass
class ReasoningStep:
    """Single step in defeasible reasoning chain."""
    description: str
    result: bool
    details: str = ""


@dataclass
class ExceptionApplication:
    """Result of evaluating a single exception."""
    label: str
    condition: str
    guard_satisfied: bool
    effect: str = ""


@dataclass
class DefeasibleResult:
    """Result of defeasible evaluation of a statute against facts."""
    statute_section: str
    statute_title: str
    base_satisfied: bool # whether base elements are all satisfied
    exceptions_applied: List[ExceptionApplication]
    final_verdict: str # "convicted", "exception_applied", "not_satisfied"
    reasoning_chain: List[ReasoningStep]

    @property
    def defeated(self) -> bool:
        return any(e.guard_satisfied for e in self.exceptions_applied)


class DefeasibleReasoner:
    """Evaluates statutes with defeasible exception logic."""

    def __init__(self):
        from yuho.eval.interpreter import Interpreter, Environment
        self.interpreter = Interpreter()

    def evaluate_with_exceptions(
        self,
        statute: nodes.StatuteNode,
        facts: dict,
        env=None,
    ) -> DefeasibleResult:
        """
        Evaluate a statute against facts with exception defeat.

        Args:
            statute: statute AST node
            facts: dict mapping field names to values
            env: optional evaluation environment

        Returns:
            DefeasibleResult with base satisfaction, exception applications, and final verdict
        """
        from yuho.eval.interpreter import Environment, Value, StructInstance
        if env is None:
            env = Environment()

        section = statute.section_number
        title = statute.title.value if statute.title else ""
        reasoning: List[ReasoningStep] = []

        # step 1: evaluate base elements
        base_satisfied, element_steps = self._evaluate_base_elements(
            statute.elements, facts, env
        )
        reasoning.extend(element_steps)
        reasoning.append(ReasoningStep(
            description=f"Base elements {'satisfied' if base_satisfied else 'not satisfied'}",
            result=base_satisfied,
        ))

        # step 2: if base satisfied, check exceptions
        exceptions_applied: List[ExceptionApplication] = []
        if base_satisfied and statute.exceptions:
            reasoning.append(ReasoningStep(
                description=f"Checking {len(statute.exceptions)} exception(s)",
                result=True,
            ))
            for exc in statute.exceptions:
                app = self._evaluate_exception(exc, facts, env)
                exceptions_applied.append(app)
                reasoning.append(ReasoningStep(
                    description=f"Exception '{app.label}': guard {'satisfied' if app.guard_satisfied else 'not satisfied'}",
                    result=app.guard_satisfied,
                    details=app.effect if app.guard_satisfied else "",
                ))

        # step 3: determine final verdict
        if not base_satisfied:
            final_verdict = "not_satisfied"
        elif any(e.guard_satisfied for e in exceptions_applied):
            final_verdict = "exception_applied"
        else:
            final_verdict = "convicted"

        reasoning.append(ReasoningStep(
            description=f"Final verdict: {final_verdict}",
            result=(final_verdict == "convicted"),
        ))

        return DefeasibleResult(
            statute_section=section,
            statute_title=title,
            base_satisfied=base_satisfied,
            exceptions_applied=exceptions_applied,
            final_verdict=final_verdict,
            reasoning_chain=reasoning,
        )

    def _evaluate_base_elements(
        self,
        elements: tuple,
        facts: dict,
        env,
    ) -> Tuple[bool, List[ReasoningStep]]:
        """Evaluate base elements against facts."""
        steps: List[ReasoningStep] = []
        if not elements:
            return True, steps

        all_satisfied = True
        for elem in elements:
            if isinstance(elem, nodes.ElementGroupNode):
                satisfied, group_steps = self._evaluate_element_group(elem, facts, env)
                steps.extend(group_steps)
                if not satisfied:
                    all_satisfied = False
            elif isinstance(elem, nodes.ElementNode):
                satisfied = self._check_element(elem, facts)
                steps.append(ReasoningStep(
                    description=f"{elem.element_type} '{elem.name}'",
                    result=satisfied,
                    details=elem.description.value if isinstance(elem.description, nodes.StringLit) else str(elem.description),
                ))
                if not satisfied:
                    all_satisfied = False

        return all_satisfied, steps

    def _evaluate_element_group(
        self,
        group: nodes.ElementGroupNode,
        facts: dict,
        env,
    ) -> Tuple[bool, List[ReasoningStep]]:
        """Evaluate element group with combinator logic."""
        steps: List[ReasoningStep] = []
        results: List[bool] = []

        for member in group.members:
            if isinstance(member, nodes.ElementGroupNode):
                satisfied, sub_steps = self._evaluate_element_group(member, facts, env)
                steps.extend(sub_steps)
                results.append(satisfied)
            elif isinstance(member, nodes.ElementNode):
                satisfied = self._check_element(member, facts)
                steps.append(ReasoningStep(
                    description=f"{member.element_type} '{member.name}'",
                    result=satisfied,
                ))
                results.append(satisfied)

        if group.combinator == "all_of":
            overall = all(results) if results else True
        else: # any_of
            overall = any(results) if results else False

        steps.append(ReasoningStep(
            description=f"{group.combinator} group: {'satisfied' if overall else 'not satisfied'}",
            result=overall,
        ))
        return overall, steps

    def _check_element(self, element: nodes.ElementNode, facts: dict) -> bool:
        """Check if a single element is satisfied by facts."""
        # look for matching field in facts dict
        name = element.name
        if name in facts:
            val = facts[name]
            if isinstance(val, bool):
                return val
            if val is None:
                return False
            return True # non-None truthy
        return False

    def _evaluate_exception(
        self,
        exc: nodes.ExceptionNode,
        facts: dict,
        env,
    ) -> ExceptionApplication:
        """Evaluate a single exception against facts."""
        label = exc.label or "unnamed"
        condition = exc.condition.value if exc.condition else ""
        effect = exc.effect.value if exc.effect else ""

        guard_satisfied = False
        if exc.guard is not None:
            # evaluate the guard expression against facts
            guard_satisfied = self._evaluate_guard(exc.guard, facts, env)
        else:
            # no guard - check if facts have a matching exception field
            if "exception" in facts:
                guard_satisfied = (facts["exception"] == label)

        return ExceptionApplication(
            label=label,
            condition=condition,
            guard_satisfied=guard_satisfied,
            effect=effect,
        )

    def _evaluate_guard(self, guard: nodes.ASTNode, facts: dict, env) -> bool:
        """Evaluate a guard expression against facts."""
        from yuho.eval.interpreter import Interpreter, Environment, Value, StructInstance

        # create an environment with facts bound
        eval_env = Environment()
        facts_instance = StructInstance(
            type_name="Facts",
            fields={k: Value(raw=v, type_tag=_infer_tag(v)) for k, v in facts.items()},
        )
        eval_env.set("facts", Value(raw=facts_instance, type_tag="struct"))

        # also bind fact keys directly
        for k, v in facts.items():
            eval_env.set(k, Value(raw=v, type_tag=_infer_tag(v)))

        interp = Interpreter(env=eval_env)
        try:
            result = interp.visit(guard)
            if isinstance(result, Value):
                return result.is_truthy()
            if isinstance(result, bool):
                return result
            return bool(result) if result is not None else False
        except Exception:
            return False


def _infer_tag(val) -> str:
    """Infer type tag from Python value."""
    if isinstance(val, bool):
        return "bool"
    if isinstance(val, int):
        return "int"
    if isinstance(val, float):
        return "float"
    if isinstance(val, str):
        return "string"
    if val is None:
        return "none"
    return "string"
