"""Check runtime/Z3 conviction verdicts on penalty-bearing fixtures."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import sys
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yuho.ast import ASTBuilder, nodes
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.parser import get_parser
from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE, _verifier_duration_days


PENALTY_FIXTURE_SOURCE = """
struct Facts {
    bool act,
    bool intent,
    bool lawful,
}

statute 1 "Penalty offence" {
    elements {
        actus_reus act := "act";
        mens_rea intent := "intent";
    }

    penalty {
        imprisonment := 1 days .. 5 days;
        fine := $10.00 .. $20.00;
        caning := 3 .. 6 strokes;
        death := TRUE;
    }

    exception lawful_authority {
        "lawful authority"
        "no conviction"
        when lawful
    }
}
"""


@dataclass(frozen=True)
class PenaltyVerdictCase:
    name: str
    source: str
    facts: dict[str, bool]
    expected: bool
    section: str = "1"


@dataclass(frozen=True)
class PenaltyMismatch:
    case: str
    message: str


@dataclass(frozen=True)
class PenaltyVerdictSummary:
    checked: int
    conviction_matches: int
    penalty_bound_checks: int
    mismatches: tuple[PenaltyMismatch, ...]
    errors: tuple[PenaltyMismatch, ...]


DEFAULT_CASES = (
    PenaltyVerdictCase(
        name="penalty_applies",
        source=PENALTY_FIXTURE_SOURCE,
        facts={"act": True, "intent": True, "lawful": False},
        expected=True,
    ),
    PenaltyVerdictCase(
        name="penalty_blocked_by_missing_mens_rea",
        source=PENALTY_FIXTURE_SOURCE,
        facts={"act": True, "intent": False, "lawful": False},
        expected=False,
    ),
    PenaltyVerdictCase(
        name="penalty_blocked_by_exception",
        source=PENALTY_FIXTURE_SOURCE,
        facts={"act": True, "intent": True, "lawful": True},
        expected=False,
    ),
)


def _parse_source(source: str) -> nodes.ModuleNode:
    parser = get_parser()
    result = parser.parse(source, "<penalty-verdict-fixture>")
    if result.errors:
        joined = "; ".join(str(error) for error in result.errors)
        raise RuntimeError(joined)
    return ASTBuilder(result.source, "<penalty-verdict-fixture>").build(result.root_node)


def _facts_struct(facts: dict[str, bool]) -> StructInstance:
    return StructInstance(
        type_name="Facts",
        fields={name: Value(raw=value, type_tag="bool") for name, value in facts.items()},
    )


def _walk_ast(node: Any) -> Iterable[Any]:
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        children = current.children() if hasattr(current, "children") else []
        stack.extend(child for child in children if isinstance(child, nodes.ASTNode))


def _element_names(statute: nodes.StatuteNode) -> set[str]:
    return {node.name for node in _walk_ast(statute) if isinstance(node, nodes.ElementNode)}


def _identifier_names(statute: nodes.StatuteNode) -> set[str]:
    return {node.name for node in _walk_ast(statute) if isinstance(node, nodes.IdentifierNode)}


def _safe(name: str) -> str:
    return name.replace(" ", "_").replace("-", "_")


def _add_fact_bindings(solver: Any, gen: Z3Generator, statute: nodes.StatuteNode, facts: dict[str, bool]) -> None:
    import z3

    statute_id = statute.section_number.replace(".", "_")
    for name in _element_names(statute):
        const = gen._consts.get(f"{statute_id}_leaf_{_safe(name)}")
        if const is not None:
            solver.add(const == z3.BoolVal(bool(facts.get(name, False))))
    for name in _identifier_names(statute) | set(facts):
        const = gen._consts.get(f"{statute_id}_{_safe(name)}")
        if const is not None:
            solver.add(const == z3.BoolVal(bool(facts.get(name, False))))


def _clone_with(assertions: Iterable[Any], extra: Any) -> Any:
    import z3

    solver = z3.Solver()
    for assertion in assertions:
        solver.add(assertion)
    solver.add(extra)
    return solver


def _fine_cents(money: nodes.MoneyNode) -> int:
    return int(Decimal(money.amount) * 100)


def _check_penalty_bounds(
    case: PenaltyVerdictCase,
    assertions: tuple[Any, ...],
    gen: Z3Generator,
    statute: nodes.StatuteNode,
) -> tuple[int, list[PenaltyMismatch]]:
    import z3

    penalty = statute.penalty
    if penalty is None:
        return 0, [PenaltyMismatch(case.name, "fixture has no penalty")]

    checks = 0
    mismatches: list[PenaltyMismatch] = []
    statute_id = statute.section_number.replace(".", "_")

    imprisonment = gen._consts.get(f"{statute_id}_imprisonment")
    if imprisonment is not None:
        if penalty.imprisonment_min is not None:
            lo, _ = _verifier_duration_days(penalty.imprisonment_min)
            checks += 1
            if _clone_with(assertions, imprisonment < lo).check() != z3.unsat:
                mismatches.append(PenaltyMismatch(case.name, f"imprisonment lower bound {lo} not enforced"))
        if penalty.imprisonment_max is not None:
            hi, _ = _verifier_duration_days(penalty.imprisonment_max)
            checks += 1
            if _clone_with(assertions, imprisonment > hi).check() != z3.unsat:
                mismatches.append(PenaltyMismatch(case.name, f"imprisonment upper bound {hi} not enforced"))

    fine = gen._consts.get(f"{statute_id}_fine")
    if fine is not None:
        if penalty.fine_min is not None:
            lo = _fine_cents(penalty.fine_min)
            checks += 1
            if _clone_with(assertions, fine < lo).check() != z3.unsat:
                mismatches.append(PenaltyMismatch(case.name, f"fine lower bound {lo} not enforced"))
        if penalty.fine_max is not None:
            hi = _fine_cents(penalty.fine_max)
            checks += 1
            if _clone_with(assertions, fine > hi).check() != z3.unsat:
                mismatches.append(PenaltyMismatch(case.name, f"fine upper bound {hi} not enforced"))

    caning = gen._consts.get(f"{statute_id}_caning")
    if caning is not None:
        if penalty.caning_min is not None:
            checks += 1
            if _clone_with(assertions, caning < penalty.caning_min).check() != z3.unsat:
                mismatches.append(
                    PenaltyMismatch(
                        case.name,
                        f"caning lower bound {penalty.caning_min} not enforced",
                    )
                )
        if penalty.caning_max is not None:
            checks += 1
            if _clone_with(assertions, caning > penalty.caning_max).check() != z3.unsat:
                mismatches.append(
                    PenaltyMismatch(
                        case.name,
                        f"caning upper bound {penalty.caning_max} not enforced",
                    )
                )

    death = gen._consts.get(f"{statute_id}_death_penalty")
    if death is not None and penalty.death_penalty is not None:
        checks += 1
        forbidden = not bool(penalty.death_penalty)
        if _clone_with(assertions, death == z3.BoolVal(forbidden)).check() != z3.unsat:
            mismatches.append(
                PenaltyMismatch(
                    case.name,
                    f"death penalty flag {penalty.death_penalty} not enforced",
                )
            )

    return checks, mismatches


def run_penalty_verdict_checks(
    cases: Iterable[PenaltyVerdictCase] = DEFAULT_CASES,
) -> PenaltyVerdictSummary | None:
    if not Z3_AVAILABLE:
        return None

    import z3

    checked = conviction_matches = penalty_bound_checks = 0
    mismatches: list[PenaltyMismatch] = []
    errors: list[PenaltyMismatch] = []

    for case in cases:
        try:
            ast = _parse_source(case.source)
            statute = next(s for s in ast.statutes if s.section_number == case.section)
            runtime = StatuteEvaluator().evaluate(statute, _facts_struct(case.facts)).overall_satisfied
            if runtime != case.expected:
                mismatches.append(
                    PenaltyMismatch(case.name, f"runtime={runtime} expected={case.expected}")
                )

            gen = Z3Generator()
            solver, _ = gen.generate(ast)
            if solver is None:
                errors.append(PenaltyMismatch(case.name, "Z3 generator returned no solver"))
                continue
            _add_fact_bindings(solver, gen, statute, case.facts)
            if solver.check() != z3.sat:
                errors.append(PenaltyMismatch(case.name, "Z3 model is unsatisfiable after fact bindings"))
                continue

            statute_id = case.section.replace(".", "_")
            conviction = gen._consts.get(f"{statute_id}_conviction")
            if conviction is None:
                errors.append(PenaltyMismatch(case.name, "missing Z3 conviction atom"))
                continue
            model_verdict = z3.is_true(solver.model().eval(conviction, model_completion=True))
            if model_verdict == runtime == case.expected:
                conviction_matches += 1
            else:
                mismatches.append(
                    PenaltyMismatch(
                        case.name,
                        f"runtime={runtime} z3={model_verdict} expected={case.expected}",
                    )
                )

            checks, bound_mismatches = _check_penalty_bounds(
                case, tuple(solver.assertions()), gen, statute
            )
            penalty_bound_checks += checks
            mismatches.extend(bound_mismatches)
            checked += 1
        except Exception as exc:
            errors.append(PenaltyMismatch(case.name, f"{type(exc).__name__}: {exc}"))

    return PenaltyVerdictSummary(
        checked=checked,
        conviction_matches=conviction_matches,
        penalty_bound_checks=penalty_bound_checks,
        mismatches=tuple(mismatches),
        errors=tuple(errors),
    )


def main() -> int:
    summary = run_penalty_verdict_checks()
    if summary is None:
        print("penalty verdicts: SKIP (z3-solver not installed)")
        return 0
    print(
        "penalty verdicts: "
        f"CHECKED={summary.checked} CONVICTION_MATCH={summary.conviction_matches} "
        f"BOUND_CHECKS={summary.penalty_bound_checks} "
        f"MISMATCH={len(summary.mismatches)} ERR={len(summary.errors)}"
    )
    for mismatch in summary.mismatches:
        print(f"  mismatch {mismatch.case}: {mismatch.message}", file=sys.stderr)
    for error in summary.errors:
        print(f"  error {error.case}: {error.message}", file=sys.stderr)
    return 0 if not summary.mismatches and not summary.errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
