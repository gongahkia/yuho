"""Statute evaluation against fact patterns."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Optional, Tuple, Union
from yuho.ast import nodes
from yuho.eval.interpreter import Environment, Interpreter, InterpreterError, StructInstance, Value

_DEFAULT_SCOPE_MAX_DEPTH = 32
_SCOPE_MAX_DEPTH_BINDING = "__yuho_scope_max_depth"
_SCOPE_TRACE_BINDING = "__yuho_scope_trace"


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------


@dataclass
class ElementResult:
    """Result of evaluating a single element."""

    element_name: str
    element_type: str  # actus_reus, mens_rea, circumstance
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

    def bindings(self) -> Dict[str, bool]:
        """Return ``{element_name: satisfied}`` for every element evaluated.

        Used by Catala-style scope composition: a parent statute that
        invokes ``apply_scope(<base_section>, facts)`` consumes this map
        as the bound element states from the base scope, optionally
        re-using individual bindings in its own predicates.
        """
        return {er.element_name: er.satisfied for er in self.element_results}

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
                er = self._evaluate_element(member, facts, env, statute.definitions)
                all_element_results.append(er)
                if not er.satisfied:
                    overall = False
                    reasoning.append(
                        f"Element '{er.element_name}' ({er.element_type}) not satisfied"
                    )
            elif isinstance(member, nodes.ElementGroupNode):
                group_results, group_ok = self._evaluate_group(
                    member, facts, env, statute.definitions
                )
                all_element_results.extend(group_results)
                if not group_ok:
                    overall = False
                    reasoning.append(f"Element group ({member.combinator}) not satisfied")

        penalty = statute.penalty if overall else None

        # check exceptions via defeasible reasoning
        if overall and statute.exceptions:
            from yuho.eval.defeasible import DefeasibleReasoner

            reasoner = DefeasibleReasoner()
            facts_dict = {k: v.raw for k, v in facts.fields.items()}
            for exc in statute.exceptions:
                app = reasoner._evaluate_exception(exc, facts_dict, env)
                if app.guard_satisfied:
                    overall = False
                    reasoning.append(f"Exception '{app.label}' defeated conviction: {app.effect}")
                    break
                else:
                    exception_key = self._exception_key(exc)
                    if exception_key is None or exception_key not in facts.fields:
                        continue
                    if facts.fields[exception_key].is_truthy():
                        overall = False
                        reasoning.append(f"Exception '{exception_key}' applies")
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
        definitions: Tuple[nodes.DefinitionEntry, ...] = (),
    ) -> ElementResult:
        """Check if a single element is satisfied by the facts."""
        name = element.name
        etype = element.element_type

        # derive description
        desc = ""
        if isinstance(element.description, nodes.StringLit):
            desc = element.description.value
        else:
            satisfied = self._evaluate_predicate_description(
                element.description, facts, env, definitions
            )
            return ElementResult(
                element_name=name,
                element_type=etype,
                satisfied=satisfied,
                description=type(element.description).__name__,
            )

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

    def _evaluate_predicate_description(
        self,
        predicate: nodes.ASTNode,
        facts: StructInstance,
        env: Environment,
        definitions: Tuple[nodes.DefinitionEntry, ...] = (),
    ) -> bool:
        predicate_env = self._predicate_env(facts, env, definitions)
        try:
            return Interpreter(predicate_env).visit(predicate).is_truthy()
        except InterpreterError:
            return False

    def _predicate_env(
        self,
        facts: StructInstance,
        env: Environment,
        definitions: Tuple[nodes.DefinitionEntry, ...] = (),
    ) -> Environment:
        predicate_env = env.child()
        predicate_env.set("facts", Value(raw=facts, type_tag="struct"))
        for key, value in facts.fields.items():
            predicate_env.set(key, value)
        interp = Interpreter(predicate_env)
        for definition in definitions:
            if isinstance(definition.definition, nodes.StringLit):
                continue
            try:
                predicate_env.set(definition.term, interp.visit(definition.definition))
            except InterpreterError:
                continue
        return predicate_env

    def _evaluate_group(
        self,
        group: nodes.ElementGroupNode,
        facts: StructInstance,
        env: Environment,
        definitions: Tuple[nodes.DefinitionEntry, ...] = (),
    ) -> Tuple[List[ElementResult], bool]:
        """Evaluate element group with combinator logic.

        all_of: every child must be satisfied
        any_of: at least one child must be satisfied
        """
        results: List[ElementResult] = []
        member_statuses: List[bool] = []
        for member in group.members:
            if isinstance(member, nodes.ElementNode):
                er = self._evaluate_element(member, facts, env, definitions)
                results.append(er)
                member_statuses.append(er.satisfied)
            elif isinstance(member, nodes.ElementGroupNode):
                sub_results, sub_ok = self._evaluate_group(member, facts, env, definitions)
                results.extend(sub_results)
                member_statuses.append(sub_ok)

        if group.combinator == "all_of":
            ok = all(member_statuses)
        elif group.combinator == "any_of":
            ok = any(member_statuses)
        else:
            ok = all(member_statuses)  # default to all_of

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

    # ------------------------------------------------------------------
    # Catala-style scope composition (apply_scope)
    # ------------------------------------------------------------------

    def apply_scope(
        self,
        section_ref: str,
        facts: StructInstance,
        registry: Mapping[str, nodes.StatuteNode],
        *,
        env: Optional[Environment] = None,
        _trace: Optional[List[str]] = None,
        max_depth: int = _DEFAULT_SCOPE_MAX_DEPTH,
    ) -> EvaluationResult:
        """Evaluate a base section as a callable scope.

        ``section_ref`` is the canonical section number (matches
        ``StatuteNode.section_number``); ``registry`` is the section-to-
        statute lookup the caller maintains for the surrounding library.
        Returns an :class:`EvaluationResult` whose
        :meth:`~EvaluationResult.bindings` map is the lam4-style scope
        output --- the parent scope composes by reading specific
        bindings or by inspecting ``overall_satisfied``.

        Recursion: if the base scope itself contains
        :class:`ApplyScopeNode` references to further sections, this
        method recurses through ``registry``. A ``_trace`` accumulator
        guards against cycles by raising :class:`RecursionError` if the
        same section appears twice on the call chain.

        Raises ``KeyError`` when ``section_ref`` is not in ``registry``.
        """
        canonical = _canonical_section(section_ref)
        target = registry.get(canonical)
        if target is None:
            raise KeyError(
                f"apply_scope: section s{canonical} is not in the supplied "
                f"statute registry (known: {sorted(registry.keys())[:5]}…)"
            )
        trace = list(_trace) if _trace else []
        if max_depth > 0 and len(trace) >= max_depth:
            raise RecursionError(
                f"apply_scope: depth limit {max_depth} exceeded in "
                f"scope-call chain: {' -> '.join(trace + [canonical])}"
            )
        if canonical in trace:
            raise RecursionError(
                f"apply_scope: cycle detected in scope-call chain: "
                f"{' -> '.join(trace + [canonical])}"
            )
        trace.append(canonical)
        call_env = env
        if env is not None:
            call_env = env.child()
            call_env.set(_SCOPE_TRACE_BINDING, Value(raw=list(trace), type_tag="list"))
            call_env.set(
                _SCOPE_MAX_DEPTH_BINDING,
                Value(raw=max_depth, type_tag="int"),
            )
        # Standard evaluation handles elements + exceptions. Embedded
        # apply_scope/is_infringed expressions resolve through the supplied
        # environment's statute registry; the trace guard applies to this
        # direct scope call.
        return self.evaluate(target, facts, call_env)


def _canonical_section(s: str) -> str:
    """Strip an optional leading ``s`` / ``S.`` / ``Section`` prefix."""
    raw = s.strip()
    lower = raw.lower()
    if lower.startswith("section"):
        raw = raw[len("section") :].strip().strip(".").strip()
    elif lower.startswith("s."):
        raw = raw[2:].strip()
    elif lower.startswith("s") and len(raw) > 1 and raw[1].isdigit():
        raw = raw[1:]
    return raw
