"""Regression coverage for branch-scoped runtime penalty selection (#49)."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.ast import ASTBuilder
from yuho.eval import Environment, StatuteEvaluator, StructInstance, Value
from yuho.ir import lower_statute, rule_branches
from yuho.parser import get_parser
from yuho.verify.z3_solver import Z3_AVAILABLE, Z3Generator, Z3UnsupportedFeature


def _module(source: str):
    parsed = get_parser().parse(source)
    assert not parsed.errors, parsed.errors
    return ASTBuilder(source).build(parsed.root_node)


def _facts(**values: bool) -> StructInstance:
    return StructInstance(
        "Facts",
        {name: Value(raw=value, type_tag="bool") for name, value in values.items()},
    )


def _dependency_environment(statute):
    """Register each explicit exception target as its checked-in provision."""
    env = Environment()
    targets = {
        dependency.target_section
        for dependency in rule_branches(lower_statute(statute))[0].dependencies
    }
    for target in targets:
        matches = sorted(Path("library/penal_code").glob(f"s{target}_*/statute.yh"))
        assert len(matches) == 1, target
        target_statute = _module(matches[0].read_text(encoding="utf-8")).statutes[0]
        env.statutes[target] = target_statute
    return env


def _s304a_result(*, rash_act: bool, negligent_act: bool):
    source = Path("library/penal_code/s304A_causing_death_rash_negligent_act/statute.yh").read_text(
        encoding="utf-8"
    )
    statute = _module(source).statutes[0]
    return StatuteEvaluator().evaluate(
        statute,
        _facts(
            doing_act=True,
            causing_death=True,
            rash_act=rash_act,
            negligent_act=negligent_act,
            not_culpable_homicide=True,
        ),
        _dependency_environment(statute),
    )


def test_s304a_selects_only_the_rash_penalty_for_a_rash_fact_pattern() -> None:
    result = _s304a_result(rash_act=True, negligent_act=False)

    assert result.overall_satisfied
    assert [penalty.guard for penalty in result.applicable_penalties] == ["rash_act"]
    assert result.applicable_penalties[0].citation == "s304A"
    assert result.applicable_penalties[0].penalty.imprisonment_max is not None
    assert result.applicable_penalties[0].penalty.imprisonment_max.years == 5
    assert result.penalty_diagnostics == ()


def test_s304a_selects_only_the_negligent_penalty_for_a_negligent_fact_pattern() -> None:
    result = _s304a_result(rash_act=False, negligent_act=True)

    assert result.overall_satisfied
    assert [penalty.guard for penalty in result.applicable_penalties] == ["negligent_act"]
    assert result.applicable_penalties[0].citation == "s304A"
    assert result.applicable_penalties[0].penalty.imprisonment_max is not None
    assert result.applicable_penalties[0].penalty.imprisonment_max.years == 2
    assert result.penalty_diagnostics == ()


def test_multi_subsection_penalty_is_selected_from_the_satisfied_branch() -> None:
    source = Path(
        "library/penal_code/s174_failure_attend_obedience_order_public_servant/statute.yh"
    ).read_text(encoding="utf-8")
    statute = _module(source).statutes[0]

    result = StatuteEvaluator().evaluate(
        statute,
        _facts(
            legal_attendance_duty=True,
            competent_process=True,
            omits_to_attend=True,
            premature_departure=False,
            individual_case=True,
            other_case=False,
            subsection_1_offence=False,
            court_attendance_process=False,
        ),
    )

    assert result.overall_satisfied
    assert [penalty.citation for penalty in result.applicable_penalties] == ["s174(1)"]
    assert result.applicable_penalties[0].guard == "individual_case"
    assert result.applicable_penalties[0].branch_paths == (("174", "(1)"),)


def test_unguarded_sibling_penalty_blocks_are_cumulative_consequences() -> None:
    statute = _module("""
        statute 1 "Cumulative sources" {
            elements { actus_reus act := "act"; }
            penalty cumulative { imprisonment := 1 days; }
            penalty { fine := unlimited; }
        }
        """).statutes[0]

    result = StatuteEvaluator().evaluate(statute, _facts(act=True))

    assert result.overall_satisfied
    assert len(result.applicable_penalties) == 2
    assert all(penalty.guard is None for penalty in result.applicable_penalties)
    assert result.penalty_diagnostics == ()


def test_selected_penalty_retains_its_unflattened_disposition_structure() -> None:
    statute = _module("""
        statute 4 "Disposition surface" {
            elements { actus_reus act := "act"; }
            penalty cumulative {
                imprisonment := 1 days;
                fine := unlimited;
                caning := unspecified;
                death := TRUE;
                supplementary := "life imprisonment or a non-custodial disposition remains source text";
            }
        }
        """).statutes[0]

    result = StatuteEvaluator().evaluate(statute, _facts(act=True))

    selected = result.applicable_penalties[0].penalty
    assert selected.imprisonment_max is not None
    assert selected.fine_unlimited
    assert selected.caning_unspecified
    assert selected.death_penalty is True
    assert selected.supplementary is not None
    assert "life imprisonment" in selected.supplementary.value
    assert "non-custodial" in selected.supplementary.value


def test_overlapping_guarded_sibling_penalties_emit_a_deterministic_diagnostic() -> None:
    statute = _module("""
        statute 2 "Overlapping alternatives" {
            elements { any_of {
                circumstance left := "left";
                circumstance right := "right";
            } }
            penalty when left { fine := unlimited; }
            penalty when right { imprisonment := 1 days; }
        }
        """).statutes[0]

    result = StatuteEvaluator().evaluate(statute, _facts(left=True, right=True))

    assert [penalty.guard for penalty in result.applicable_penalties] == ["left", "right"]
    assert len(result.penalty_diagnostics) == 1
    diagnostic = result.penalty_diagnostics[0]
    assert diagnostic.code == "YRTP001"
    assert diagnostic.citation_paths == (("2",),)
    assert "penalty #1 when left, penalty #2 when right" in diagnostic.message


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_explicitly_rejects_conditional_and_sibling_penalty_selection() -> None:
    module = _module("""
        statute 3 "Conditional penalties" {
            elements { actus_reus act := "act"; }
            penalty when rash { fine := unlimited; }
            penalty when negligent { imprisonment := 1 days; }
        }
        """)

    with pytest.raises(Z3UnsupportedFeature) as excinfo:
        Z3Generator().generate(module)

    assert "s3: multiple penalty blocks" in excinfo.value.features
    assert "s3: conditional penalty guard 'rash'" in excinfo.value.features
    assert "s3: conditional penalty guard 'negligent'" in excinfo.value.features
