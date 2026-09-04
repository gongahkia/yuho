"""Statute evaluation against fact patterns."""

from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Dict, List, Mapping, Optional, Tuple, Union
from yuho.ast import nodes
from yuho.caselaw import is_adopting_treatment, is_inactive_treatment
from yuho.eval.dependencies import DependencyDiagnostic, DependencyResult
from yuho.eval.facts import TypedFact
from yuho.eval.interpreter import Environment, Interpreter, InterpreterError, StructInstance, Value
from yuho.eval.outcomes import (
    CriminalOutcome,
    CriminalOutcomeKind,
    OutcomeDiagnostic,
    OutcomeSource,
    OutcomeTarget,
    SpecialDisposition,
)
from yuho.ir import (
    CANONICAL_IR_VERSION,
    CapabilityDiagnostic,
    CanonicalDependency,
    CanonicalOutcomeTransition,
    CanonicalRuleBranch,
    CanonicalStatute,
    canonical_hash,
    diagnose_statute_capabilities,
    lower_statute,
    rule_branches,
)

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
    citation_path: Tuple[str, ...] = ()


@dataclass
class BranchResult:
    """The result of one canonically scoped executable provision branch."""

    citation_path: Tuple[str, ...]
    element_results: List[ElementResult]
    satisfied: Optional[bool]
    reasoning: List[str] = field(default_factory=list)
    penalty_paths: Tuple[Tuple[str, ...], ...] = ()
    exception_paths: Tuple[Tuple[str, ...], ...] = ()
    outcome_transition: Optional[CanonicalOutcomeTransition] = None
    dependency_results: Tuple[DependencyResult, ...] = ()
    dependency_diagnostics: Tuple[DependencyDiagnostic, ...] = ()

    @property
    def citation(self) -> str:
        section, *subsections = self.citation_path
        return f"s{section}{''.join(subsections)}"

    @property
    def is_determinate(self) -> bool:
        return self.satisfied is not None


@dataclass(frozen=True)
class ApplicablePenalty:
    """A penalty block selected from a satisfied liability branch.

    ``penalty`` preserves the parsed disposition structure rather than
    coercing imprisonment, fines, caning, death, or supplementary terms into
    a numeric range. ``branch_paths`` records every satisfied branch that
    selected this one source block.
    """

    penalty: nodes.PenaltyNode
    citation_path: Tuple[str, ...]
    declaration_index: int
    guard: Optional[str]
    branch_paths: Tuple[Tuple[str, ...], ...]

    @property
    def citation(self) -> str:
        section, *subsections = self.citation_path
        return f"s{section}{''.join(subsections)}"


@dataclass(frozen=True)
class PenaltyDiagnostic:
    """A deterministic warning about selected penalty source blocks."""

    code: str
    message: str
    citation_paths: Tuple[Tuple[str, ...], ...]


@dataclass
class EvaluationResult:
    """Result of evaluating a statute against facts."""

    statute_section: str
    statute_title: str
    element_results: List[ElementResult]
    overall_satisfied: Optional[bool]
    outcome: CriminalOutcome = field(
        default_factory=lambda: CriminalOutcome(
            kind=CriminalOutcomeKind.NOT_PROVED,
            underlying_act_found=False,
        )
    )
    applicable_penalties: Tuple[ApplicablePenalty, ...] = ()
    penalty_diagnostics: Tuple[PenaltyDiagnostic, ...] = ()
    dependency_results: Tuple[DependencyResult, ...] = ()
    dependency_diagnostics: Tuple[DependencyDiagnostic, ...] = ()
    reasoning: List[str] = field(default_factory=list)
    canonical_ir_version: str = CANONICAL_IR_VERSION
    canonical_ir_hash: Optional[str] = None
    diagnostics: Tuple[CapabilityDiagnostic, ...] = ()
    branch_results: List[BranchResult] = field(default_factory=list)
    provision_kind: str = "executable"

    @property
    def is_determinate(self) -> bool:
        """Whether unresolved cross-section dependencies leave no verdict gap."""
        return self.overall_satisfied is not None

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
        status = (
            "SATISFIED"
            if self.overall_satisfied is True
            else "NOT SATISFIED" if self.overall_satisfied is False else "UNRESOLVED"
        )
        lines.append(f"Section {self.statute_section} ({self.statute_title}): {status}")
        outcome = self.outcome
        source = f" from {outcome.source.citation}" if outcome.source is not None else ""
        lines.append(f"  Outcome: {outcome.kind.value}{source}")
        if outcome.target is not None:
            lines.append(
                f"    Target: s{outcome.target.section} ({outcome.target.outcome_kind.value})"
            )
        if outcome.disposition is not None:
            lines.append(f"    Disposition: {outcome.disposition.reference}")
        for outcome_diagnostic in outcome.diagnostics:
            lines.append(f"    - {outcome_diagnostic.code}: {outcome_diagnostic.message}")
        for er in self.element_results:
            mark = "[x]" if er.satisfied else "[ ]"
            path = (
                f" at s{er.citation_path[0]}{''.join(er.citation_path[1:])}"
                if er.citation_path
                else ""
            )
            lines.append(f"  {mark} {er.element_type}: {er.element_name}{path}")
            if er.description:
                lines.append(f"      {er.description}")
        if self.branch_results:
            lines.append("  Branches:")
            for branch in self.branch_results:
                mark = "[x]" if branch.satisfied else "[ ]"
                lines.append(f"    {mark} {branch.citation}")
        if self.applicable_penalties:
            lines.append("  Penalties:")
            for selected in self.applicable_penalties:
                guard = f" when {selected.guard}" if selected.guard else ""
                lines.append(f"    - {selected.citation}{guard}")
        if self.penalty_diagnostics:
            lines.append("  Penalty diagnostics:")
            for penalty_diagnostic in self.penalty_diagnostics:
                lines.append(f"    - {penalty_diagnostic.code}: {penalty_diagnostic.message}")
        if self.dependency_results:
            lines.append("  Dependencies:")
            for dependency in self.dependency_results:
                edge = dependency.edge
                lines.append(
                    f"    - {edge.reference_kind}(s{edge.target_section}) from "
                    f"s{edge.citation_path[0]}{''.join(edge.citation_path[1:])}: "
                    f"{dependency.status}"
                )
        if self.dependency_diagnostics:
            lines.append("  Dependency diagnostics:")
            for dependency_diagnostic in self.dependency_diagnostics:
                lines.append(f"    - {dependency_diagnostic.code}: {dependency_diagnostic.message}")
        if self.reasoning:
            lines.append("  Reasoning:")
            for r in self.reasoning:
                lines.append(f"    - {r}")
        if self.diagnostics:
            lines.append("  Diagnostics:")
            for diagnostic in self.diagnostics:
                lines.append(f"    - {diagnostic.code}: {diagnostic.message}")
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
        """Evaluate a statute against given facts through canonical IR.

        The public AST entry point is transitional.  It immediately lowers to
        a :class:`~yuho.ir.CanonicalStatute`, then invokes the named AST
        adapter for expression execution while that evaluator is migrated.
        ``evaluate_canonical`` is the canonical consumer boundary.
        """
        canonical_statute = lower_statute(statute)
        return self.evaluate_canonical(
            canonical_statute,
            facts,
            ast_adapter=statute,
            env=env,
        )

    def evaluate_canonical(
        self,
        statute: CanonicalStatute,
        facts: StructInstance,
        *,
        ast_adapter: nodes.StatuteNode,
        env: Optional[Environment] = None,
    ) -> EvaluationResult:
        """Evaluate canonical statute IR using the explicit legacy adapter.

        The adapter is deliberately required rather than retained implicitly
        on the IR object.  That keeps persisted canonical IR free of Python
        AST nodes and exposes the remaining migration work in capability
        diagnostics.
        """
        if statute.section_number != ast_adapter.section_number:
            raise ValueError(
                "canonical statute and AST adapter refer to different sections: "
                f"s{statute.section_number} and s{ast_adapter.section_number}"
            )
        diagnostics = diagnose_statute_capabilities(statute, "runtime")
        return self._evaluate_ast(
            ast_adapter,
            facts,
            env,
            canonical_statute=statute,
            canonical_ir_hash=canonical_hash(statute),
            diagnostics=diagnostics,
        )

    def _evaluate_ast(
        self,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Optional[Environment],
        *,
        canonical_statute: CanonicalStatute,
        canonical_ir_hash: str,
        diagnostics: Tuple[CapabilityDiagnostic, ...],
    ) -> EvaluationResult:
        """Evaluate the transition adapter for the canonical runtime boundary.

        For ElementGroupNode:
          - all_of -> every member must be satisfied
          - any_of -> at least one member must be satisfied
        """
        env = env or self.interpreter.env
        title = statute.title.value if statute.title else "(untitled)"
        branches = rule_branches(canonical_statute)
        if not branches:
            return EvaluationResult(
                statute_section=statute.section_number,
                statute_title=title,
                element_results=[],
                overall_satisfied=False,
                reasoning=[
                    f"Section s{statute.section_number} has no executable element-bearing provision"
                ],
                canonical_ir_hash=canonical_ir_hash,
                diagnostics=diagnostics,
                provision_kind="definition_only",
            )

        all_element_results: List[ElementResult] = []
        branch_results: List[BranchResult] = []
        evaluated_branches: List[Tuple[CanonicalRuleBranch, BranchResult]] = []
        dependency_results: List[DependencyResult] = []
        dependency_diagnostics: List[DependencyDiagnostic] = []
        reasoning: List[str] = []
        case_effects = self.active_case_law_effects(
            statute.case_law,
            statute_jurisdiction=statute.jurisdiction,
        )

        for branch in branches:
            branch_result = self._evaluate_branch(
                branch,
                statute,
                facts,
                env,
                case_effects,
            )
            branch_results.append(branch_result)
            evaluated_branches.append((branch, branch_result))
            all_element_results.extend(branch_result.element_results)
            dependency_results.extend(branch_result.dependency_results)
            dependency_diagnostics.extend(branch_result.dependency_diagnostics)
            dependency_diagnostics.extend(
                dependency.diagnostic
                for dependency in branch_result.dependency_results
                if dependency.diagnostic is not None
            )
            reasoning.extend(branch_result.reasoning)

        # Canonical sibling branches are alternatives.  Their individual
        # element groups retain their own all_of/any_of composition.
        overall: Optional[bool]
        if any(branch.satisfied is True for branch in branch_results):
            overall = True
        elif any(branch.satisfied is None for branch in branch_results):
            overall = None
        else:
            overall = False
        applicable_penalties, penalty_diagnostics = self._select_penalties(
            evaluated_branches,
            statute,
            facts,
            env,
        )
        reasoning.extend(diagnostic.message for diagnostic in penalty_diagnostics)
        outcome, outcome_overall, outcome_penalties = self._resolve_criminal_outcome(
            statute,
            facts,
            env,
            evaluated_branches,
            overall,
            applicable_penalties,
        )
        overall = outcome_overall
        applicable_penalties = outcome_penalties
        reasoning.extend(diagnostic.message for diagnostic in outcome.diagnostics)

        return EvaluationResult(
            statute_section=statute.section_number,
            statute_title=title,
            element_results=all_element_results,
            overall_satisfied=overall,
            outcome=outcome,
            applicable_penalties=applicable_penalties,
            penalty_diagnostics=penalty_diagnostics,
            dependency_results=tuple(dependency_results),
            dependency_diagnostics=tuple(dict.fromkeys(dependency_diagnostics)),
            reasoning=reasoning,
            canonical_ir_hash=canonical_ir_hash,
            diagnostics=diagnostics,
            branch_results=branch_results,
        )

    # -- internal helpers ---------------------------------------------------

    def _evaluate_branch(
        self,
        branch: CanonicalRuleBranch,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Environment,
        case_effects: Mapping[str, Tuple[nodes.CaseLawNode, ...]],
    ) -> BranchResult:
        """Evaluate one canonical rule branch with its ancestor context."""
        provisions = self._branch_adapter_provisions(statute, branch.citation_path)
        definitions = tuple(
            definition for provision in provisions for definition in provision.definitions
        )
        element_results: List[ElementResult] = []
        reasoning: List[str] = []
        satisfied: Optional[bool] = True

        for provision, path in zip(provisions, self._citation_prefixes(branch.citation_path)):
            results, provision_satisfied = self._evaluate_requirement_members(
                provision.elements,
                facts,
                env,
                definitions,
                case_effects,
                statute.jurisdiction,
                path,
            )
            element_results.extend(results)
            reasoning.extend(
                result_reason for result in results for result_reason in result.reasoning
            )
            if not provision_satisfied:
                satisfied = False
                reasoning.append(f"Requirements at s{path[0]}{''.join(path[1:])} not satisfied")

        dependency_results: Tuple[DependencyResult, ...] = ()
        dependency_diagnostics: Tuple[DependencyDiagnostic, ...] = ()
        outcome_transition: Optional[CanonicalOutcomeTransition] = None
        if satisfied is True:
            (
                satisfied,
                dependency_results,
                dependency_diagnostics,
                outcome_transition,
            ) = self._apply_branch_exceptions(branch, statute, facts, env, reasoning)

        reasoning.insert(
            0,
            f"Branch {branch.citation} "
            f"{'satisfied' if satisfied is True else 'not satisfied' if satisfied is False else 'unresolved'}",
        )
        return BranchResult(
            citation_path=branch.citation_path,
            element_results=element_results,
            satisfied=satisfied,
            reasoning=reasoning,
            penalty_paths=tuple(source.citation_path for source in branch.penalties),
            exception_paths=tuple(source.citation_path for source in branch.exceptions),
            outcome_transition=outcome_transition,
            dependency_results=dependency_results,
            dependency_diagnostics=dependency_diagnostics,
        )

    def _resolve_criminal_outcome(
        self,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Environment,
        evaluated_branches: List[Tuple[CanonicalRuleBranch, BranchResult]],
        overall: Optional[bool],
        convicted_penalties: Tuple[ApplicablePenalty, ...],
    ) -> Tuple[CriminalOutcome, Optional[bool], Tuple[ApplicablePenalty, ...]]:
        """Turn the structural liability result into a typed legal outcome.

        ``overall_satisfied`` remains a compatibility projection. Consumers
        requiring a legal consequence must use ``EvaluationResult.outcome``.
        An exception's former prose effect is never used for routing.
        """
        if overall is True:
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.CONVICTED,
                    underlying_act_found=True,
                    facts_used=tuple(sorted(facts.fields)),
                ),
                True,
                convicted_penalties,
            )

        exceptional = next(
            (
                (branch, result)
                for branch, result in evaluated_branches
                if result.outcome_transition is not None
            ),
            None,
        )
        if exceptional is None:
            if overall is None:
                return (
                    CriminalOutcome(
                        kind=CriminalOutcomeKind.UNRESOLVED,
                        underlying_act_found=False,
                        facts_used=tuple(sorted(facts.fields)),
                    ),
                    None,
                    (),
                )
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.NOT_PROVED,
                    underlying_act_found=False,
                    facts_used=tuple(sorted(facts.fields)),
                ),
                False,
                (),
            )

        branch, branch_result = exceptional
        transition = branch_result.outcome_transition
        assert transition is not None
        source = self._outcome_source(statute, transition)
        if transition.outcome_kind in {"acquit", "legacy_acquit"}:
            outcome = CriminalOutcome(
                kind=CriminalOutcomeKind.ACQUITTED,
                underlying_act_found=True,
                source=source,
                transition_sources=(source,),
                facts_used=tuple(sorted(facts.fields)),
                acquitted=True,
            )
            return self._apply_special_disposition(
                statute,
                facts,
                env,
                branch,
                outcome,
            )
        if transition.outcome_kind == "reduce_to":
            return self._resolve_reduction(statute, facts, env, transition, source)

        diagnostic = OutcomeDiagnostic(
            code="YROD002",
            message=(
                f"Unsupported exception outcome '{transition.outcome_kind}' at {source.citation}; "
                "the result is unresolved"
            ),
            source=source,
        )
        return (
            CriminalOutcome(
                kind=CriminalOutcomeKind.UNRESOLVED,
                underlying_act_found=True,
                source=source,
                transition_sources=(source,),
                facts_used=tuple(sorted(facts.fields)),
                diagnostics=(diagnostic,),
            ),
            None,
            (),
        )

    def _resolve_reduction(
        self,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Environment,
        transition: CanonicalOutcomeTransition,
        source: OutcomeSource,
    ) -> Tuple[CriminalOutcome, Optional[bool], Tuple[ApplicablePenalty, ...]]:
        """Resolve a lesser-offence transition through the active registry."""
        target = self._outcome_target_section(transition.target)
        if target is None:
            diagnostic = OutcomeDiagnostic(
                code="YROD002",
                message=f"Invalid reduce_to target {transition.target!r} at {source.citation}",
                source=source,
            )
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.UNRESOLVED,
                    underlying_act_found=True,
                    source=source,
                    transition_sources=(source,),
                    facts_used=tuple(sorted(facts.fields)),
                    diagnostics=(diagnostic,),
                ),
                None,
                (),
            )

        stack = self._outcome_resolution_stack(env)
        if target == statute.section_number or target in stack:
            diagnostic = OutcomeDiagnostic(
                code="YROD002",
                message=(
                    f"Cyclic reduce_to target s{target} at {source.citation}: "
                    + " -> ".join(f"s{item}" for item in (*stack, statute.section_number, target))
                ),
                source=source,
            )
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.UNRESOLVED,
                    underlying_act_found=True,
                    source=source,
                    transition_sources=(source,),
                    facts_used=tuple(sorted(facts.fields)),
                    diagnostics=(diagnostic,),
                ),
                None,
                (),
            )

        target_statute = env.get_statute(target)
        if target_statute is None:
            diagnostic = OutcomeDiagnostic(
                code="YROD001",
                message=(
                    f"reduce_to target s{target} at {source.citation} is not registered "
                    "in the active statute environment"
                ),
                source=source,
            )
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.UNRESOLVED,
                    underlying_act_found=True,
                    source=source,
                    transition_sources=(source,),
                    facts_used=tuple(sorted(facts.fields)),
                    diagnostics=(diagnostic,),
                ),
                None,
                (),
            )

        target_env = env.child()
        target_env.set(
            "__yuho_outcome_resolution_stack",
            Value(raw=[*stack, statute.section_number], type_tag="list"),
        )
        target_result = self.evaluate(target_statute, facts, target_env)
        target_summary = OutcomeTarget(
            section=target,
            title=target_result.statute_title,
            outcome_kind=target_result.outcome.kind,
            overall_satisfied=target_result.overall_satisfied,
        )
        if not target_result.outcome.is_determinate:
            diagnostic = OutcomeDiagnostic(
                code="YROD003",
                message=(
                    f"reduce_to target s{target} at {source.citation} has an unresolved outcome"
                ),
                source=source,
            )
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.UNRESOLVED,
                    underlying_act_found=True,
                    source=source,
                    transition_sources=(source,),
                    target=target_summary,
                    facts_used=tuple(sorted(facts.fields)),
                    diagnostics=(diagnostic,),
                ),
                None,
                (),
            )

        return (
            CriminalOutcome(
                kind=CriminalOutcomeKind.REDUCED_TO,
                underlying_act_found=True,
                source=source,
                transition_sources=(source,),
                target=target_summary,
                facts_used=tuple(sorted(facts.fields)),
            ),
            target_result.overall_satisfied,
            target_result.applicable_penalties if target_result.overall_satisfied is True else (),
        )

    def _apply_special_disposition(
        self,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Environment,
        branch: CanonicalRuleBranch,
        outcome: CriminalOutcome,
    ) -> Tuple[CriminalOutcome, Optional[bool], Tuple[ApplicablePenalty, ...]]:
        """Apply a provision's guarded procedural outcome after acquittal."""
        for transition in branch.outcomes:
            if transition.source_kind != "outcome" or transition.outcome_kind != "disposition":
                continue
            source = self._outcome_source(statute, transition)
            outcome_node = self._outcome_adapter_node(statute, transition)
            if outcome_node is None:
                diagnostic = OutcomeDiagnostic(
                    code="YROD003",
                    message=f"Outcome source {source.citation} has no AST adapter node",
                    source=source,
                )
                return (
                    CriminalOutcome(
                        kind=CriminalOutcomeKind.UNRESOLVED,
                        underlying_act_found=True,
                        source=source,
                        transition_sources=(*outcome.transition_sources, source),
                        facts_used=outcome.facts_used,
                        diagnostics=(diagnostic,),
                        acquitted=True,
                    ),
                    None,
                    (),
                )
            if outcome_node.guard is not None:
                from yuho.eval.defeasible import DefeasibleReasoner

                raw_facts = {key: value.raw for key, value in facts.fields.items()}
                guard = DefeasibleReasoner()._evaluate_guard(outcome_node.guard, raw_facts, env, ())
                if guard.diagnostic is not None:
                    diagnostic = OutcomeDiagnostic(
                        code="YROD003",
                        message=(
                            f"Unable to evaluate disposition {transition.target!r} at "
                            f"{source.citation}: {guard.diagnostic.message}"
                        ),
                        source=source,
                    )
                    return (
                        CriminalOutcome(
                            kind=CriminalOutcomeKind.UNRESOLVED,
                            underlying_act_found=True,
                            source=source,
                            transition_sources=(*outcome.transition_sources, source),
                            facts_used=outcome.facts_used,
                            diagnostics=(diagnostic,),
                            acquitted=True,
                        ),
                        None,
                        (),
                    )
                if guard.satisfied is not True:
                    continue
            if not transition.target:
                diagnostic = OutcomeDiagnostic(
                    code="YROD002",
                    message=f"Disposition outcome at {source.citation} has no reference target",
                    source=source,
                )
                return (
                    CriminalOutcome(
                        kind=CriminalOutcomeKind.UNRESOLVED,
                        underlying_act_found=True,
                        source=source,
                        transition_sources=(*outcome.transition_sources, source),
                        facts_used=outcome.facts_used,
                        diagnostics=(diagnostic,),
                        acquitted=True,
                    ),
                    None,
                    (),
                )
            return (
                CriminalOutcome(
                    kind=CriminalOutcomeKind.SPECIAL_DISPOSITION,
                    underlying_act_found=True,
                    source=source,
                    transition_sources=(*outcome.transition_sources, source),
                    disposition=SpecialDisposition(reference=transition.target, source=source),
                    facts_used=outcome.facts_used,
                    acquitted=True,
                ),
                False,
                (),
            )
        return outcome, False, ()

    @staticmethod
    def _outcome_target_section(target: Optional[str]) -> Optional[str]:
        """Normalize a grammar-level ``s304`` reference to a registry key."""
        if target is None or not target.startswith("s") or len(target) == 1:
            return None
        section = target[1:]
        return section if section[0].isdigit() else None

    @staticmethod
    def _outcome_resolution_stack(env: Environment) -> Tuple[str, ...]:
        binding = env.get("__yuho_outcome_resolution_stack")
        if binding is None or not isinstance(binding.raw, list):
            return ()
        return tuple(item for item in binding.raw if isinstance(item, str))

    def _outcome_source(
        self,
        statute: nodes.StatuteNode,
        transition: CanonicalOutcomeTransition,
    ) -> OutcomeSource:
        return OutcomeSource(
            citation_path=transition.citation_path,
            source_kind=transition.source_kind,
            declaration_index=transition.declaration_index,
            outcome_kind=transition.outcome_kind,
            target=transition.target,
            source_version=tuple(statute.effective_dates),
        )

    def _outcome_adapter_node(
        self,
        statute: nodes.StatuteNode,
        transition: CanonicalOutcomeTransition,
    ) -> Optional[nodes.OutcomeNode]:
        provisions = {path: provision for path, provision in self._all_adapter_provisions(statute)}
        provision = provisions.get(transition.citation_path)
        if provision is None:
            return None
        if transition.source_kind == "exception":
            if transition.declaration_index >= len(provision.exceptions):
                return None
            return provision.exceptions[transition.declaration_index].outcome
        if transition.declaration_index >= len(provision.outcomes):
            return None
        return provision.outcomes[transition.declaration_index]

    def _select_penalties(
        self,
        evaluated_branches: List[Tuple[CanonicalRuleBranch, BranchResult]],
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Environment,
    ) -> Tuple[Tuple[ApplicablePenalty, ...], Tuple[PenaltyDiagnostic, ...]]:
        """Select each penalty source governed by a satisfied rule branch.

        Unguarded blocks and multiple blocks with the same guard are
        cumulative source consequences. Distinct guards on sibling blocks in
        one provision are mutually exclusive candidates. If case facts make
        more than one such candidate applicable, preserve every candidate and
        emit ``YRTP001`` rather than choosing declaration order.
        """
        provisions = {path: provision for path, provision in self._all_adapter_provisions(statute)}
        selected: Dict[
            Tuple[Tuple[str, ...], int], Tuple[nodes.PenaltyNode, set[Tuple[str, ...]]]
        ] = {}

        for branch, branch_result in evaluated_branches:
            if branch_result.satisfied is not True:
                continue
            for source in branch.penalties:
                provision = provisions.get(source.citation_path)
                if provision is None:
                    raise ValueError(
                        "canonical penalty source does not match its AST adapter at "
                        f"s{source.citation_path[0]}{''.join(source.citation_path[1:])}"
                    )
                penalties = (provision.penalty, *provision.additional_penalties)
                if source.declaration_index >= len(penalties):
                    raise ValueError(
                        "canonical penalty declaration does not match its AST adapter at "
                        f"s{source.citation_path[0]}{''.join(source.citation_path[1:])}"
                    )
                penalty = penalties[source.declaration_index]
                if penalty is None:
                    raise ValueError("canonical penalty source resolved to no AST penalty")
                if not self._penalty_guard_satisfied(penalty.condition, branch_result, facts, env):
                    continue
                key = (source.citation_path, source.declaration_index)
                if key not in selected:
                    selected[key] = (penalty, set())
                selected[key][1].add(branch_result.citation_path)

        applicable = tuple(
            ApplicablePenalty(
                penalty=penalty,
                citation_path=citation_path,
                declaration_index=declaration_index,
                guard=penalty.condition,
                branch_paths=tuple(sorted(branch_paths)),
            )
            for (citation_path, declaration_index), (penalty, branch_paths) in sorted(
                selected.items(), key=lambda item: (item[0][0], item[0][1])
            )
        )
        return applicable, self._penalty_selection_diagnostics(applicable)

    def _penalty_guard_satisfied(
        self,
        guard: Optional[str],
        branch_result: BranchResult,
        facts: StructInstance,
        env: Environment,
    ) -> bool:
        """Resolve a ``penalty when <identifier>`` guard for one branch."""
        if guard is None:
            return True

        matching_elements = [
            result.satisfied
            for result in branch_result.element_results
            if self._normalise(result.element_name) == self._normalise(guard)
        ]
        if matching_elements:
            return any(matching_elements)

        fact_value = self._matching_fact_value(facts, guard)
        if fact_value is not None:
            return fact_value.is_truthy()
        env_value = env.get(guard)
        return env_value.is_truthy() if env_value is not None else False

    @staticmethod
    def _penalty_selection_diagnostics(
        applicable: Tuple[ApplicablePenalty, ...],
    ) -> Tuple[PenaltyDiagnostic, ...]:
        """Report overlapping guarded siblings without discarding either one."""
        by_provision: Dict[Tuple[str, ...], List[ApplicablePenalty]] = {}
        for selected in applicable:
            if selected.guard is not None:
                by_provision.setdefault(selected.citation_path, []).append(selected)

        diagnostics: List[PenaltyDiagnostic] = []
        for citation_path, candidates in sorted(by_provision.items()):
            guards = {candidate.guard for candidate in candidates}
            if len(guards) < 2:
                continue
            ordered = sorted(candidates, key=lambda candidate: candidate.declaration_index)
            labels = ", ".join(
                f"penalty #{candidate.declaration_index + 1} when {candidate.guard}"
                for candidate in ordered
            )
            citation = f"s{citation_path[0]}{''.join(citation_path[1:])}"
            diagnostics.append(
                PenaltyDiagnostic(
                    code="YRTP001",
                    message=(
                        f"Conflicting guarded sibling penalty candidates at {citation}: {labels}; "
                        "all candidates are retained for review"
                    ),
                    citation_paths=(citation_path,),
                )
            )
        return tuple(diagnostics)

    def _evaluate_requirement_members(
        self,
        members: Tuple[
            Union[nodes.ElementNode, nodes.CivilPrimitiveNode, nodes.ElementGroupNode], ...
        ],
        facts: StructInstance,
        env: Environment,
        definitions: Tuple[nodes.DefinitionEntry, ...],
        case_effects: Mapping[str, Tuple[nodes.CaseLawNode, ...]],
        statute_jurisdiction: Optional[str],
        citation_path: Tuple[str, ...],
    ) -> Tuple[List[ElementResult], bool]:
        """Evaluate direct requirements in one provision conjunctively."""
        results: List[ElementResult] = []
        statuses: List[bool] = []
        for member in members:
            if isinstance(member, nodes.ElementNode):
                result = self._evaluate_element(
                    member,
                    facts,
                    env,
                    definitions,
                    case_effects,
                    statute_jurisdiction,
                    citation_path,
                )
                results.append(result)
                statuses.append(result.satisfied)
            elif isinstance(member, nodes.ElementGroupNode):
                group_results, group_satisfied = self._evaluate_group(
                    member,
                    facts,
                    env,
                    definitions,
                    case_effects,
                    statute_jurisdiction,
                    citation_path,
                )
                results.extend(group_results)
                statuses.append(group_satisfied)
            else:
                results.append(
                    ElementResult(
                        element_name=type(member).__name__,
                        element_type="unsupported",
                        satisfied=False,
                        description="civil primitive element has no runtime lowering",
                        reasoning=[
                            f"Unsupported runtime requirement at "
                            f"s{citation_path[0]}{''.join(citation_path[1:])}"
                        ],
                        citation_path=citation_path,
                    )
                )
                statuses.append(False)
        return results, all(statuses)

    def _apply_branch_exceptions(
        self,
        branch: CanonicalRuleBranch,
        statute: nodes.StatuteNode,
        facts: StructInstance,
        env: Environment,
        reasoning: List[str],
    ) -> Tuple[
        Optional[bool],
        Tuple[DependencyResult, ...],
        Tuple[DependencyDiagnostic, ...],
        Optional[CanonicalOutcomeTransition],
    ]:
        """Apply governing exceptions and retain cross-section dependency trace."""
        from yuho.eval.defeasible import DefeasibleReasoner

        provisions = {path: provision for path, provision in self._all_adapter_provisions(statute)}
        facts_dict = {key: value.raw for key, value in facts.fields.items()}
        reasoner = DefeasibleReasoner()
        dependency_results: List[DependencyResult] = []
        dependency_diagnostics: List[DependencyDiagnostic] = []
        for source in branch.exceptions:
            provision = provisions[source.citation_path]
            exception = provision.exceptions[source.declaration_index]
            edges = tuple(
                dependency
                for dependency in branch.dependencies
                if dependency.source_kind == "exception"
                and dependency.citation_path == source.citation_path
                and dependency.declaration_index == source.declaration_index
            )
            app = reasoner._evaluate_exception(exception, facts_dict, env, edges)
            dependency_results.extend(app.dependency_results)
            dependency_diagnostics.extend(app.dependency_diagnostics)
            if app.dependency_diagnostics:
                reasoning.extend(
                    f"{diagnostic.code}: {diagnostic.message}"
                    for diagnostic in app.dependency_diagnostics
                )
                return None, tuple(dependency_results), tuple(dependency_diagnostics), None
            if app.guard_satisfied is True:
                reasoning.append(
                    f"Exception '{app.label}' at s{source.citation_path[0]}"
                    f"{''.join(source.citation_path[1:])} defeated branch: {app.effect}"
                )
                return (
                    False,
                    tuple(dependency_results),
                    tuple(dependency_diagnostics),
                    self._exception_outcome_transition(branch, source),
                )
            exception_key = self._exception_key(exception)
            if exception_key is not None and exception_key in facts.fields:
                if facts.fields[exception_key].is_truthy():
                    reasoning.append(
                        f"Exception '{exception_key}' at s{source.citation_path[0]}"
                        f"{''.join(source.citation_path[1:])} applies"
                    )
                    return (
                        False,
                        tuple(dependency_results),
                        tuple(dependency_diagnostics),
                        self._exception_outcome_transition(branch, source),
                    )
        return True, tuple(dependency_results), tuple(dependency_diagnostics), None

    @staticmethod
    def _exception_outcome_transition(
        branch: CanonicalRuleBranch,
        source,
    ) -> CanonicalOutcomeTransition:
        """Find a typed exception transition or preserve legacy acquittal semantics.

        Legacy effects remain descriptive only. The pre-outcome evaluator's
        established behaviour was that a fired exception defeated conviction;
        represent that compatibility rule explicitly rather than reading its
        free-text effect as a legal route.
        """
        typed = next(
            (
                outcome
                for outcome in branch.outcomes
                if outcome.source_kind == "exception"
                and outcome.citation_path == source.citation_path
                and outcome.declaration_index == source.declaration_index
            ),
            None,
        )
        if typed is not None:
            return typed
        return CanonicalOutcomeTransition(
            citation_path=source.citation_path,
            source_kind="exception",
            declaration_index=source.declaration_index,
            outcome_kind="legacy_acquit",
        )

    @staticmethod
    def _citation_prefixes(citation_path: Tuple[str, ...]) -> Tuple[Tuple[str, ...], ...]:
        return tuple(citation_path[:index] for index in range(1, len(citation_path) + 1))

    def _branch_adapter_provisions(
        self,
        statute: nodes.StatuteNode,
        citation_path: Tuple[str, ...],
    ) -> Tuple[Union[nodes.StatuteNode, nodes.SubsectionNode], ...]:
        provisions: List[Union[nodes.StatuteNode, nodes.SubsectionNode]] = [statute]
        current: Union[nodes.StatuteNode, nodes.SubsectionNode] = statute
        for subsection_number in citation_path[1:]:
            next_provision = next(
                (
                    subsection
                    for subsection in current.subsections
                    if subsection.number == subsection_number
                ),
                None,
            )
            if next_provision is None:
                raise ValueError(
                    "canonical branch does not match its AST adapter at "
                    f"s{citation_path[0]}{''.join(citation_path[1:])}"
                )
            provisions.append(next_provision)
            current = next_provision
        return tuple(provisions)

    def _all_adapter_provisions(
        self,
        statute: nodes.StatuteNode,
    ) -> Tuple[Tuple[Tuple[str, ...], Union[nodes.StatuteNode, nodes.SubsectionNode]], ...]:
        items: List[Tuple[Tuple[str, ...], Union[nodes.StatuteNode, nodes.SubsectionNode]]] = []

        def walk(
            provision: Union[nodes.StatuteNode, nodes.SubsectionNode],
            path: Tuple[str, ...],
        ) -> None:
            items.append((path, provision))
            for subsection in provision.subsections:
                walk(subsection, path + (subsection.number,))

        walk(statute, (statute.section_number,))
        return tuple(items)

    def _evaluate_element(
        self,
        element: nodes.ElementNode,
        facts: StructInstance,
        env: Environment,
        definitions: Tuple[nodes.DefinitionEntry, ...] = (),
        case_effects: Optional[Mapping[str, Tuple[nodes.CaseLawNode, ...]]] = None,
        statute_jurisdiction: Optional[str] = None,
        citation_path: Tuple[str, ...] = (),
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
            return self._with_citation_path(
                self._apply_case_law_effects(
                    ElementResult(
                        element_name=name,
                        element_type=etype,
                        satisfied=satisfied,
                        description=type(element.description).__name__,
                    ),
                    facts,
                    case_effects.get(name, ()),
                    statute_jurisdiction,
                ),
                citation_path,
            )

        fact_value = self._matching_fact_value(facts, name)
        satisfied = fact_value.is_truthy() if fact_value is not None else False

        result = self._apply_case_law_effects(
            ElementResult(
                element_name=name,
                element_type=etype,
                satisfied=satisfied,
                description=desc,
            ),
            facts,
            case_effects.get(name, ()),
            statute_jurisdiction,
        )
        final_satisfied, burden_reason = self._apply_burden_metadata(
            element,
            fact_value,
            result.satisfied,
        )
        if not burden_reason and final_satisfied == result.satisfied:
            return self._with_citation_path(result, citation_path)
        reasoning = list(result.reasoning)
        if burden_reason:
            reasoning.append(burden_reason)
        return ElementResult(
            element_name=result.element_name,
            element_type=result.element_type,
            satisfied=final_satisfied,
            description=result.description,
            reasoning=reasoning,
            citation_path=citation_path,
        )

    @staticmethod
    def _with_citation_path(
        result: ElementResult,
        citation_path: Tuple[str, ...],
    ) -> ElementResult:
        if result.citation_path == citation_path:
            return result
        return replace(result, citation_path=citation_path)

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
        statute_jurisdiction: Optional[str] = None,
        citation_path: Tuple[str, ...] = (),
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
                er = self._evaluate_element(
                    member,
                    facts,
                    env,
                    definitions,
                    case_effects,
                    statute_jurisdiction,
                    citation_path,
                )
                results.append(er)
                member_statuses.append(er.satisfied)
            elif isinstance(member, nodes.ElementGroupNode):
                sub_results, sub_ok = self._evaluate_group(
                    member,
                    facts,
                    env,
                    definitions,
                    case_effects,
                    statute_jurisdiction,
                    citation_path,
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
        statute_jurisdiction: Optional[str] = None,
    ) -> ElementResult:
        satisfied = result.satisfied
        reasoning = list(result.reasoning)
        for case in cases:
            effect = (case.interpretive_effect or "").lower()
            fact_name = case.effect_fact
            if not effect or not fact_name:
                continue
            raw_fact = self._matching_fact_value(facts, fact_name)
            fact_value = raw_fact.is_truthy() if raw_fact is not None else False
            burden_reason = self._case_burden_reason(
                case,
                fact_name,
                raw_fact,
                statute_jurisdiction,
            )
            if burden_reason:
                fact_value = False
                reasoning.append(burden_reason)
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

    def apply_case_law_effects(
        self,
        result: ElementResult,
        facts: StructInstance,
        cases: Tuple[nodes.CaseLawNode, ...],
        statute_jurisdiction: Optional[str] = None,
    ) -> ElementResult:
        return self._apply_case_law_effects(result, facts, cases, statute_jurisdiction)

    def _case_burden_reason(
        self,
        case: nodes.CaseLawNode,
        fact_name: str,
        fact_value: Optional[Value],
        statute_jurisdiction: Optional[str],
    ) -> Optional[str]:
        if not fact_value or not fact_value.is_truthy() or not case.burden_shift:
            return None
        if not self._case_jurisdiction_permits(case, statute_jurisdiction):
            return None
        metadata = getattr(fact_value, "metadata", None)
        if not isinstance(metadata, TypedFact):
            return None
        if metadata.burden and self._normalise(metadata.burden) != self._normalise(
            case.burden_shift
        ):
            return (
                f"Case law '{case.case_name.value}' shifted burden for fact "
                f"'{fact_name}' expects burden={case.burden_shift}, got burden={metadata.burden}"
            )
        if (
            case.burden_shift_standard
            and metadata.standard_of_proof
            and self._normalise(metadata.standard_of_proof)
            != self._normalise(case.burden_shift_standard)
        ):
            return (
                f"Case law '{case.case_name.value}' shifted burden for fact "
                f"'{fact_name}' expects standard={case.burden_shift_standard}, "
                f"got standard={metadata.standard_of_proof}"
            )
        return None

    @staticmethod
    def _case_jurisdiction_permits(
        case: nodes.CaseLawNode,
        statute_jurisdiction: Optional[str],
    ) -> bool:
        if not statute_jurisdiction or not case.jurisdiction:
            return True
        return StatuteEvaluator._case_key(case.jurisdiction) == StatuteEvaluator._case_key(
            statute_jurisdiction
        )

    def _fact_truthy(self, facts: StructInstance, fact_name: str) -> bool:
        value = self._matching_fact_value(facts, fact_name)
        return value.is_truthy() if value is not None else False

    def _matching_fact_value(self, facts: StructInstance, fact_name: str) -> Optional[Value]:
        if fact_name in facts.fields:
            return facts.fields[fact_name]
        norm = self._normalise(fact_name)
        for key, value in facts.fields.items():
            if self._normalise(key) == norm:
                return value
        return None

    def _apply_burden_metadata(
        self,
        element: nodes.ElementNode,
        fact_value: Optional[Value],
        satisfied: bool,
    ) -> tuple[bool, Optional[str]]:
        if fact_value is None or not satisfied:
            return satisfied, None
        metadata = getattr(fact_value, "metadata", None)
        if not isinstance(metadata, TypedFact):
            return satisfied, None
        if element.burden and metadata.burden:
            if self._normalise(metadata.burden) != self._normalise(element.burden):
                return (
                    False,
                    f"Fact '{element.name}' burden={metadata.burden} does not match declared burden={element.burden}",
                )
        if element.burden_standard and metadata.standard_of_proof:
            if self._normalise(metadata.standard_of_proof) != self._normalise(
                element.burden_standard
            ):
                return (
                    False,
                    "Fact "
                    f"'{element.name}' standard={metadata.standard_of_proof} "
                    f"does not match declared standard={element.burden_standard}",
                )
        return satisfied, None

    def _active_case_law_effects(
        self,
        case_law: Tuple[nodes.CaseLawNode, ...],
        *,
        statute_jurisdiction: Optional[str] = None,
    ) -> Dict[str, Tuple[nodes.CaseLawNode, ...]]:
        inactive = self._inactive_case_targets(case_law)
        active_case_law = self._case_law_with_adopted_effects(case_law, inactive)
        result: Dict[str, List[nodes.CaseLawNode]] = {}
        for case in active_case_law:
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

    def active_case_law_effects(
        self,
        case_law: Tuple[nodes.CaseLawNode, ...],
        *,
        statute_jurisdiction: Optional[str] = None,
    ) -> Dict[str, Tuple[nodes.CaseLawNode, ...]]:
        return self._active_case_law_effects(
            case_law,
            statute_jurisdiction=statute_jurisdiction,
        )

    @staticmethod
    def _case_law_with_adopted_effects(
        case_law: Tuple[nodes.CaseLawNode, ...],
        inactive: set[str],
    ) -> Tuple[nodes.CaseLawNode, ...]:
        by_name = {StatuteEvaluator._case_key(case.case_name.value): case for case in case_law}
        resolved: Dict[str, nodes.CaseLawNode] = {}

        def resolve(case: nodes.CaseLawNode, seen: set[str]) -> nodes.CaseLawNode:
            case_key = StatuteEvaluator._case_key(case.case_name.value)
            if case_key in resolved:
                return resolved[case_key]
            if case.interpretive_effect or case.effect_fact:
                resolved[case_key] = case
                return case
            if case_key in inactive or case_key in seen:
                resolved[case_key] = case
                return case
            for treatment in case.treatments:
                if not is_adopting_treatment(treatment.kind):
                    continue
                target_key = StatuteEvaluator._case_key(treatment.target.value)
                target = by_name.get(target_key)
                if target is None:
                    continue
                if target_key in inactive:
                    continue
                target = resolve(target, seen | {case_key})
                if not target.interpretive_effect or not target.effect_fact:
                    continue
                element_ref = case.element_ref or target.element_ref
                if not element_ref:
                    continue
                adopted_case = replace(
                    case,
                    element_ref=element_ref,
                    interpretive_effect=target.interpretive_effect,
                    effect_fact=target.effect_fact,
                    jurisdiction=case.jurisdiction or target.jurisdiction,
                    burden_shift=case.burden_shift or target.burden_shift,
                    burden_shift_standard=case.burden_shift_standard
                    or target.burden_shift_standard,
                )
                resolved[case_key] = adopted_case
                return adopted_case
            resolved[case_key] = case
            return case

        return tuple(resolve(case, set()) for case in case_law)

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
                StatuteEvaluator._normalise_effect(case.interpretive_effect) for _, case in bucket
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
