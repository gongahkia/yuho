"""Statute evaluation against fact patterns."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Mapping, Optional, Tuple, Union
from yuho.ast import nodes
from yuho.caselaw import is_inactive_treatment
from yuho.eval.interpreter import Environment, Interpreter, InterpreterError, StructInstance, Value

_DEFAULT_SCOPE_MAX_DEPTH = 32
_SCOPE_MAX_DEPTH_BINDING = "__yuho_scope_max_depth"
_SCOPE_TRACE_BINDING = "__yuho_scope_trace"
_COURT_LEVEL_RANKS = {
    "apex": 50,
    "supreme": 50,
    "court_of_appeal": 50,
    "appellate": 40,
    "high": 30,
    "district": 20,
    "trial": 10,
    "lower": 10,
}
_DOCTRINE_ROLE_RANKS = {"ratio": 20, "holding": 20, "obiter": 10}


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
    reasoning: List[str] = field(default_factory=list)


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
        case_effects = self._active_case_law_effects(
            statute.case_law,
            statute_jurisdiction=statute.jurisdiction,
        )

        for member in statute.elements:
            if isinstance(member, nodes.ElementNode):
                er = self._evaluate_element(
                    member,
                    facts,
                    env,
                    statute.definitions,
                    case_effects,
                )
                all_element_results.append(er)
                reasoning.extend(er.reasoning)
                if not er.satisfied:
                    overall = False
                    reasoning.append(
                        f"Element '{er.element_name}' ({er.element_type}) not satisfied"
                    )
            elif isinstance(member, nodes.ElementGroupNode):
                group_results, group_ok = self._evaluate_group(
                    member,
                    facts,
                    env,
                    statute.definitions,
                    case_effects,
                )
                all_element_results.extend(group_results)
                for er in group_results:
                    reasoning.extend(er.reasoning)
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
        case_effects: Optional[Mapping[str, Tuple[nodes.CaseLawNode, ...]]] = None,
    ) -> ElementResult:
        """Check if a single element is satisfied by the facts."""
        name = element.name
        etype = element.element_type
        case_effects = case_effects or {}

        # derive description
        desc = ""
        if isinstance(element.description, nodes.StringLit):
            desc = element.description.value
        else:
            satisfied = self._evaluate_predicate_description(
                element.description, facts, env, definitions
            )
            return self._apply_case_law_effects(
                ElementResult(
                    element_name=name,
                    element_type=etype,
                    satisfied=satisfied,
                    description=type(element.description).__name__,
                ),
                facts,
                case_effects.get(name, ()),
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

        return self._apply_case_law_effects(
            ElementResult(
                element_name=name,
                element_type=etype,
                satisfied=satisfied,
                description=desc,
            ),
            facts,
            case_effects.get(name, ()),
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
        case_effects: Optional[Mapping[str, Tuple[nodes.CaseLawNode, ...]]] = None,
    ) -> Tuple[List[ElementResult], bool]:
        """Evaluate element group with combinator logic.

        all_of: every child must be satisfied
        any_of: at least one child must be satisfied
        """
        case_effects = case_effects or {}
        results: List[ElementResult] = []
        member_statuses: List[bool] = []
        for member in group.members:
            if isinstance(member, nodes.ElementNode):
                er = self._evaluate_element(member, facts, env, definitions, case_effects)
                results.append(er)
                member_statuses.append(er.satisfied)
            elif isinstance(member, nodes.ElementGroupNode):
                sub_results, sub_ok = self._evaluate_group(
                    member,
                    facts,
                    env,
                    definitions,
                    case_effects,
                )
                results.extend(sub_results)
                member_statuses.append(sub_ok)

        if group.combinator == "all_of":
            ok = all(member_statuses)
        elif group.combinator == "any_of":
            ok = any(member_statuses)
        else:
            ok = all(member_statuses)  # default to all_of

        return results, ok

    def _apply_case_law_effects(
        self,
        result: ElementResult,
        facts: StructInstance,
        cases: Tuple[nodes.CaseLawNode, ...],
    ) -> ElementResult:
        satisfied = result.satisfied
        reasoning = list(result.reasoning)
        for case in cases:
            effect = (case.interpretive_effect or "").lower()
            fact_name = case.effect_fact
            if not effect or not fact_name:
                continue
            fact_value = self._fact_truthy(facts, fact_name)
            before = satisfied
            if effect in {"require", "requires", "narrow", "narrows"}:
                satisfied = satisfied and fact_value
            elif effect in {"satisfy", "satisfies", "expand", "expands"}:
                satisfied = satisfied or fact_value
            elif effect in {"exclude", "excludes"}:
                satisfied = satisfied and not fact_value
            else:
                continue
            if satisfied != before:
                reasoning.append(
                    f"Case law '{case.case_name.value}' {effect} {fact_name} "
                    f"for element '{result.element_name}'"
                )
        if satisfied == result.satisfied and not reasoning:
            return result
        return ElementResult(
            element_name=result.element_name,
            element_type=result.element_type,
            satisfied=satisfied,
            description=result.description,
            reasoning=reasoning,
        )

    def _fact_truthy(self, facts: StructInstance, fact_name: str) -> bool:
        if fact_name in facts.fields:
            return facts.fields[fact_name].is_truthy()
        norm = self._normalise(fact_name)
        for key, value in facts.fields.items():
            if self._normalise(key) == norm:
                return value.is_truthy()
        return False

    def _active_case_law_effects(
        self,
        case_law: Tuple[nodes.CaseLawNode, ...],
        *,
        statute_jurisdiction: Optional[str] = None,
    ) -> Dict[str, Tuple[nodes.CaseLawNode, ...]]:
        inactive = self._inactive_case_targets(case_law)
        result: Dict[str, List[nodes.CaseLawNode]] = {}
        for case in case_law:
            if not case.element_ref:
                continue
            if self._case_key(case.case_name.value) in inactive:
                continue
            if not case.interpretive_effect or not case.effect_fact:
                continue
            result.setdefault(case.element_ref, []).append(case)
        return {
            key: self._resolve_case_effect_conflicts(
                value,
                statute_jurisdiction=statute_jurisdiction,
            )
            for key, value in result.items()
        }

    @staticmethod
    def _resolve_case_effect_conflicts(
        cases: List[nodes.CaseLawNode],
        *,
        statute_jurisdiction: Optional[str],
    ) -> Tuple[nodes.CaseLawNode, ...]:
        buckets: Dict[str, List[tuple[int, nodes.CaseLawNode]]] = {}
        for index, case in enumerate(cases):
            fact_key = StatuteEvaluator._normalise(case.effect_fact or "")
            buckets.setdefault(fact_key, []).append((index, case))

        selected: List[tuple[int, nodes.CaseLawNode]] = []
        for bucket in buckets.values():
            effects = {
                StatuteEvaluator._normalise_effect(case.interpretive_effect)
                for _, case in bucket
            }
            if len(effects) <= 1:
                selected.extend(bucket)
                continue
            selected.append(
                max(
                    bucket,
                    key=lambda item: StatuteEvaluator._case_precedence_key(
                        item[1],
                        statute_jurisdiction=statute_jurisdiction,
                        declaration_index=item[0],
                    ),
                )
            )
        return tuple(case for _, case in sorted(selected, key=lambda item: item[0]))

    @staticmethod
    def _case_precedence_key(
        case: nodes.CaseLawNode,
        *,
        statute_jurisdiction: Optional[str],
        declaration_index: int,
    ) -> tuple[int, int, int, date, int]:
        return (
            StatuteEvaluator._jurisdiction_rank(case.jurisdiction, statute_jurisdiction),
            StatuteEvaluator._court_rank(case.court_level),
            StatuteEvaluator._doctrine_role_rank(case.doctrine_role),
            StatuteEvaluator._decision_date(case.decision_date),
            declaration_index,
        )

    @staticmethod
    def _jurisdiction_rank(
        case_jurisdiction: Optional[str],
        statute_jurisdiction: Optional[str],
    ) -> int:
        if not statute_jurisdiction:
            return 1 if not case_jurisdiction else 0
        if case_jurisdiction and StatuteEvaluator._case_key(
            case_jurisdiction
        ) == StatuteEvaluator._case_key(statute_jurisdiction):
            return 2
        if case_jurisdiction is None:
            return 1
        return 0

    @staticmethod
    def _court_rank(court_level: Optional[str]) -> int:
        if not court_level:
            return 0
        key = StatuteEvaluator._normalise(court_level)
        return _COURT_LEVEL_RANKS.get(key, 0)

    @staticmethod
    def _doctrine_role_rank(doctrine_role: Optional[str]) -> int:
        if not doctrine_role:
            return 0
        key = StatuteEvaluator._normalise(doctrine_role)
        return _DOCTRINE_ROLE_RANKS.get(key, 0)

    @staticmethod
    def _decision_date(value: Optional[str]) -> date:
        if not value:
            return date.min
        try:
            return date.fromisoformat(value)
        except ValueError:
            return date.min

    @staticmethod
    def _normalise_effect(effect: Optional[str]) -> str:
        value = (effect or "").casefold()
        if value in {"require", "requires", "narrow", "narrows"}:
            return "requires"
        if value in {"satisfy", "satisfies", "expand", "expands"}:
            return "satisfies"
        if value in {"exclude", "excludes"}:
            return "excludes"
        return value

    @staticmethod
    def _inactive_case_targets(
        case_law: Tuple[nodes.CaseLawNode, ...],
    ) -> set[str]:
        known = {StatuteEvaluator._case_key(case.case_name.value) for case in case_law}
        inactive: set[str] = set()
        for case in case_law:
            for treatment in case.treatments:
                if not is_inactive_treatment(treatment.kind):
                    continue
                target_key = StatuteEvaluator._case_key(treatment.target.value)
                if target_key in known:
                    inactive.add(target_key)
        return inactive

    @staticmethod
    def _case_key(value: str) -> str:
        return " ".join(value.casefold().split())

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
