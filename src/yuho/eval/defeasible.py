"""
Defeasible reasoning engine for Yuho statutes.

Implements exception-defeat logic: when evaluating facts against a statute,
exceptions with satisfied guards override conviction.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional, Tuple
from yuho.ast import nodes
from yuho.eval.dependencies import (
    DependencyDiagnostic,
    DependencyResult,
    DependencySubresult,
)
from yuho.ir import CanonicalDependency

if TYPE_CHECKING:
    from yuho.eval.interpreter import ScopeCallResult


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
    guard_satisfied: Optional[bool]
    effect: str = ""
    dependency_results: Tuple[DependencyResult, ...] = ()
    dependency_diagnostics: Tuple[DependencyDiagnostic, ...] = ()


@dataclass(frozen=True)
class _GuardEvaluation:
    """The value and observable section calls from one exception guard."""

    satisfied: Optional[bool]
    calls: Tuple["ScopeCallResult", ...] = ()
    diagnostic: Optional[DependencyDiagnostic] = None


@dataclass
class DefeasibleResult:
    """Result of defeasible evaluation of a statute against facts."""

    statute_section: str
    statute_title: str
    base_satisfied: bool  # whether base elements are all satisfied
    exceptions_applied: List[ExceptionApplication]
    final_verdict: str  # "convicted", "exception_applied", "not_satisfied", "unresolved_dependency"
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

        # This legacy facade has no branch result type.  Do not reintroduce
        # the former empty-top-level-elements success for subsection statutes;
        # callers that need their executable result must use StatuteEvaluator.
        if statute.subsections:
            reasoning.append(
                ReasoningStep(
                    description=(
                        "Subsection rule branches require StatuteEvaluator; "
                        "DefeasibleReasoner does not flatten them"
                    ),
                    result=False,
                )
            )
            return DefeasibleResult(
                statute_section=section,
                statute_title=title,
                base_satisfied=False,
                exceptions_applied=[],
                final_verdict="not_satisfied",
                reasoning_chain=reasoning,
            )

        # step 1: evaluate base elements
        base_satisfied, element_steps = self._evaluate_base_elements(statute.elements, facts, env)
        reasoning.extend(element_steps)
        reasoning.append(
            ReasoningStep(
                description=f"Base elements {'satisfied' if base_satisfied else 'not satisfied'}",
                result=base_satisfied,
            )
        )

        # step 2: if base satisfied, check exceptions
        exceptions_applied: List[ExceptionApplication] = []
        if base_satisfied and statute.exceptions:
            from yuho.ir import lower_statute, rule_branches

            branches = rule_branches(lower_statute(statute))
            dependencies = branches[0].dependencies if len(branches) == 1 else ()
            reasoning.append(
                ReasoningStep(
                    description=f"Checking {len(statute.exceptions)} exception(s)",
                    result=True,
                )
            )
            for index, exc in enumerate(statute.exceptions):
                edges = tuple(
                    dependency
                    for dependency in dependencies
                    if dependency.source_kind == "exception"
                    and dependency.citation_path == (statute.section_number,)
                    and dependency.declaration_index == index
                )
                app = self._evaluate_exception(exc, facts, env, edges)
                exceptions_applied.append(app)
                reasoning.append(
                    ReasoningStep(
                        description=f"Exception '{app.label}': guard {'satisfied' if app.guard_satisfied else 'not satisfied'}",
                        result=app.guard_satisfied is True,
                        details=app.effect if app.guard_satisfied else "",
                    )
                )

        # step 3: determine final verdict
        if not base_satisfied:
            final_verdict = "not_satisfied"
        elif any(e.dependency_diagnostics for e in exceptions_applied):
            final_verdict = "unresolved_dependency"
        elif any(e.guard_satisfied for e in exceptions_applied):
            final_verdict = "exception_applied"
        else:
            final_verdict = "convicted"

        reasoning.append(
            ReasoningStep(
                description=f"Final verdict: {final_verdict}",
                result=(final_verdict == "convicted"),
            )
        )

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
                steps.append(
                    ReasoningStep(
                        description=f"{elem.element_type} '{elem.name}'",
                        result=satisfied,
                        details=(
                            elem.description.value
                            if isinstance(elem.description, nodes.StringLit)
                            else str(elem.description)
                        ),
                    )
                )
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
                steps.append(
                    ReasoningStep(
                        description=f"{member.element_type} '{member.name}'",
                        result=satisfied,
                    )
                )
                results.append(satisfied)

        if group.combinator == "all_of":
            overall = all(results) if results else True
        else:  # any_of
            overall = any(results) if results else False

        steps.append(
            ReasoningStep(
                description=f"{group.combinator} group: {'satisfied' if overall else 'not satisfied'}",
                result=overall,
            )
        )
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
            return True  # non-None truthy
        return False

    def _evaluate_exception(
        self,
        exc: nodes.ExceptionNode,
        facts: dict,
        env,
        dependency_edges: Tuple[CanonicalDependency, ...] = (),
    ) -> ExceptionApplication:
        """Evaluate a single exception against facts."""
        label = exc.label or "unnamed"
        condition = exc.condition.value if exc.condition else ""
        effect = exc.effect.value if exc.effect else ""

        guard_satisfied: Optional[bool] = False
        dependency_results: Tuple[DependencyResult, ...] = ()
        dependency_diagnostics: Tuple[DependencyDiagnostic, ...] = ()
        if exc.guard is not None:
            guard_evaluation = self._evaluate_guard(exc.guard, facts, env, dependency_edges)
            guard_satisfied = guard_evaluation.satisfied
            dependency_results = self._dependency_results(
                dependency_edges,
                guard_evaluation,
            )
            if guard_evaluation.diagnostic is not None:
                dependency_diagnostics = (guard_evaluation.diagnostic,)
        else:
            # no guard - check if facts have a matching exception field
            if "exception" in facts:
                guard_satisfied = facts["exception"] == label

        return ExceptionApplication(
            label=label,
            condition=condition,
            guard_satisfied=guard_satisfied,
            effect=effect,
            dependency_results=dependency_results,
            dependency_diagnostics=dependency_diagnostics,
        )

    def _evaluate_guard(
        self,
        guard: nodes.ASTNode,
        facts: dict,
        env,
        dependency_edges: Tuple[CanonicalDependency, ...],
    ) -> _GuardEvaluation:
        """Evaluate a guard with the active registry, facts, and call trace."""
        from yuho.eval.interpreter import (
            Interpreter,
            InterpreterError,
            Environment,
            ScopeCallResult,
            StructInstance,
            Value,
            _SCOPE_DEPENDENCY_TRACE_BINDING,
        )

        # A child preserves the caller's statute registry, scope trace, and
        # other bindings. Facts are deliberately rebound in the child so they
        # are the exact fact pattern supplied to the charging-rule evaluation.
        eval_env = env.child() if env is not None else Environment()
        facts_instance = StructInstance(
            type_name="Facts",
            fields={k: Value(raw=v, type_tag=_infer_tag(v)) for k, v in facts.items()},
        )
        eval_env.set("facts", Value(raw=facts_instance, type_tag="struct"))

        # also bind fact keys directly
        for k, v in facts.items():
            eval_env.set(k, Value(raw=v, type_tag=_infer_tag(v)))

        calls: List[ScopeCallResult] = []
        eval_env.set(
            _SCOPE_DEPENDENCY_TRACE_BINDING,
            Value(raw=calls, type_tag="list"),
        )

        interp = Interpreter(env=eval_env)
        try:
            result = interp.visit(guard)
            if isinstance(result, Value):
                return _GuardEvaluation(result.is_truthy(), tuple(calls))
            if isinstance(result, bool):
                return _GuardEvaluation(result, tuple(calls))
            return _GuardEvaluation(bool(result) if result is not None else False, tuple(calls))
        except RecursionError as exc:
            return _GuardEvaluation(
                None,
                tuple(calls),
                self._guard_diagnostic("YRDG002", str(exc), dependency_edges),
            )
        except InterpreterError as exc:
            message = str(exc)
            code = (
                "YRDG001"
                if "unresolved section reference" in message
                else "YRDG002" if "YRDG002" in message else "YRDG003"
            )
            return _GuardEvaluation(
                None,
                tuple(calls),
                self._guard_diagnostic(code, message, dependency_edges),
            )
        except (KeyError, NotImplementedError, TypeError, ValueError) as exc:
            return _GuardEvaluation(
                None,
                tuple(calls),
                self._guard_diagnostic("YRDG003", str(exc), dependency_edges),
            )

    @staticmethod
    def _guard_diagnostic(
        code: str,
        error: str,
        dependency_edges: Tuple[CanonicalDependency, ...],
    ) -> DependencyDiagnostic:
        edge = dependency_edges[0] if dependency_edges else None
        target = f"s{edge.target_section}" if edge is not None else "the guard expression"
        citation_path = edge.citation_path if edge is not None else ()
        return DependencyDiagnostic(
            code=code,
            message=f"Unable to resolve {target} in exception guard: {error}",
            citation_path=citation_path,
            target_section=edge.target_section if edge is not None else None,
        )

    @staticmethod
    def _dependency_results(
        dependency_edges: Tuple[CanonicalDependency, ...],
        guard_evaluation: _GuardEvaluation,
    ) -> Tuple[DependencyResult, ...]:
        """Match observed calls to their immutable canonical dependency edges."""
        from yuho.eval.interpreter import ScopeCallResult

        results: List[DependencyResult] = []
        unmatched_calls = list(guard_evaluation.calls)
        for edge in dependency_edges:
            call_index = next(
                (
                    index
                    for index, call in enumerate(unmatched_calls)
                    if isinstance(call, ScopeCallResult)
                    and call.predicate == edge.reference_kind
                    and call.target_section == edge.target_section
                ),
                None,
            )
            if call_index is None:
                if guard_evaluation.diagnostic is not None:
                    results.append(
                        DependencyResult(
                            edge=edge,
                            status="unresolved",
                            diagnostic=guard_evaluation.diagnostic,
                        )
                    )
                else:
                    results.append(DependencyResult(edge=edge, status="not_evaluated"))
                continue

            call = unmatched_calls.pop(call_index)
            result = call.result
            subresult = DependencySubresult(
                statute_section=result.statute_section,
                statute_title=result.statute_title,
                overall_satisfied=result.overall_satisfied,
                is_determinate=result.is_determinate,
                branch_paths=tuple(branch.citation_path for branch in result.branch_results),
            )
            if not result.is_determinate:
                results.append(
                    DependencyResult(
                        edge=edge,
                        status="unresolved",
                        subresult=subresult,
                        diagnostic=guard_evaluation.diagnostic,
                    )
                )
            else:
                results.append(
                    DependencyResult(
                        edge=edge,
                        status="satisfied" if result.overall_satisfied else "not_satisfied",
                        subresult=subresult,
                    )
                )
        return tuple(results)


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
