"""Statute evaluation against fact patterns."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
from yuho.ast import nodes
from yuho.eval.interpreter import Interpreter, Environment, Value, StructInstance


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------

@dataclass
class ElementResult:
    """Result of evaluating a single element."""
    element_name: str
    element_type: str # actus_reus, mens_rea, circumstance
    satisfied: bool
    description: str = ""


@dataclass
class EvaluationResult:
    """Result of evaluating a statute against facts."""
    statute_section: str
    statute_title: str
    element_results: List[ElementResult]
    overall_satisfied: bool
    applicable_penalties: Optional[nodes.PenaltyNode] = None
    reasoning: List[str] = field(default_factory=list)

    def summary(self) -> str:
        """Human-readable summary of the evaluation."""
        lines: List[str] = []
        status = "SATISFIED" if self.overall_satisfied else "NOT SATISFIED"
        lines.append(f"Section {self.statute_section} ({self.statute_title}): {status}")
        for er in self.element_results:
            mark = "[x]" if er.satisfied else "[ ]"
            lines.append(f"  {mark} {er.element_type}: {er.element_name}")
            if er.description:
                lines.append(f"      {er.description}")
        if self.reasoning:
            lines.append("  Reasoning:")
            for r in self.reasoning:
                lines.append(f"    - {r}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------

class StatuteEvaluator:
    """Evaluates statutes against fact patterns (StructInstance)."""

    def __init__(self, interpreter: Optional[Interpreter] = None):
        self.interpreter = interpreter or Interpreter()

    def evaluate(
        self,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Optional[Environment] = None,
    ) -> EvaluationResult:
        """Evaluate a statute against given facts.

        Each top-level element/group in the statute is checked against
        matching fields in *facts*.  A field is considered to satisfy an
        element when it exists and its value is truthy.

        For ElementGroupNode:
          - all_of -> every member must be satisfied
          - any_of -> at least one member must be satisfied
        """
        env = env or self.interpreter.env
        title = statute.title.value if statute.title else "(untitled)"
        all_element_results: List[ElementResult] = []
        reasoning: List[str] = []
        overall = True

        for member in statute.elements:
            if isinstance(member, nodes.ElementNode):
                er = self._evaluate_element(member, facts, env)
                all_element_results.append(er)
                if not er.satisfied:
                    overall = False
                    reasoning.append(f"Element '{er.element_name}' ({er.element_type}) not satisfied")
            elif isinstance(member, nodes.ElementGroupNode):
                group_results, group_ok = self._evaluate_group(member, facts, env)
                all_element_results.extend(group_results)
                if not group_ok:
                    overall = False
                    reasoning.append(f"Element group ({member.combinator}) not satisfied")

        penalty = statute.penalty if overall else None

        # check exceptions -- if any exception's matching field is truthy, it negates the result
        if overall and statute.exceptions:
            for exc in statute.exceptions:
                exc_key = self._exception_key(exc)
                if exc_key and exc_key in facts.fields:
                    exc_val = facts.fields[exc_key]
                    if exc_val.is_truthy():
                        overall = False
                        reasoning.append(f"Exception '{exc_key}' applies")
                        break

        return EvaluationResult(
            statute_section=statute.section_number,
            statute_title=title,
            element_results=all_element_results,
            overall_satisfied=overall,
            applicable_penalties=penalty,
            reasoning=reasoning,
        )

    # -- internal helpers ---------------------------------------------------

    def _evaluate_element(
        self,
        element: nodes.ElementNode,
        facts: StructInstance,
        env: Environment,
    ) -> ElementResult:
        """Check if a single element is satisfied by the facts."""
        name = element.name
        etype = element.element_type

        # derive description
        desc = ""
        if isinstance(element.description, nodes.StringLit):
            desc = element.description.value

        # look for a matching field in facts
        if name in facts.fields:
            val = facts.fields[name]
            satisfied = val.is_truthy()
        else:
            # try normalised key: lowercase, underscored
            norm = self._normalise(name)
            found = False
            for k, v in facts.fields.items():
                if self._normalise(k) == norm:
                    satisfied = v.is_truthy()
                    found = True
                    break
            if not found:
                satisfied = False

        return ElementResult(
            element_name=name,
            element_type=etype,
            satisfied=satisfied,
            description=desc,
        )

    def _evaluate_group(
        self,
        group: nodes.ElementGroupNode,
        facts: StructInstance,
        env: Environment,
    ) -> Tuple[List[ElementResult], bool]:
        """Evaluate element group with combinator logic.

        all_of: every child must be satisfied
        any_of: at least one child must be satisfied
        """
        results: List[ElementResult] = []
        for member in group.members:
            if isinstance(member, nodes.ElementNode):
                er = self._evaluate_element(member, facts, env)
                results.append(er)
            elif isinstance(member, nodes.ElementGroupNode):
                sub_results, _ = self._evaluate_group(member, facts, env)
                results.extend(sub_results)

        if group.combinator == "all_of":
            ok = all(r.satisfied for r in results)
        elif group.combinator == "any_of":
            ok = any(r.satisfied for r in results)
        else:
            ok = all(r.satisfied for r in results) # default to all_of

        return results, ok

    @staticmethod
    def _normalise(s: str) -> str:
        """Normalise a name for fuzzy matching."""
        return s.lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _exception_key(exc: nodes.ExceptionNode) -> Optional[str]:
        """Derive a fact-field key from an exception node."""
        if exc.label:
            return exc.label
        return None

    def evaluate_all(
        self,
        statutes: Dict[str, nodes.StatuteNode],
        facts: StructInstance,
        env: Optional[Environment] = None,
    ) -> List[EvaluationResult]:
        """Evaluate multiple statutes against the same facts."""
        return [self.evaluate(st, facts, env) for st in statutes.values()]
