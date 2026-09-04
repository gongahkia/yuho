"""Regression coverage for canonical runtime subsection branches (#48)."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.ast import ASTBuilder, nodes
from yuho.eval import StatuteEvaluator, StructInstance, Value
from yuho.eval.defeasible import DefeasibleReasoner
from yuho.ir import lower_module, rule_branches
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


def _element_names(provision: nodes.StatuteNode | nodes.SubsectionNode) -> set[str]:
    """Return every named element declared at or below a provision."""

    def visit_members(
        members: tuple[nodes.ElementNode | nodes.CivilPrimitiveNode | nodes.ElementGroupNode, ...],
    ) -> set[str]:
        names: set[str] = set()
        for member in members:
            if isinstance(member, nodes.ElementNode):
                names.add(member.name)
            elif isinstance(member, nodes.ElementGroupNode):
                names.update(visit_members(member.members))
        return names

    names = visit_members(provision.elements)
    for subsection in provision.subsections:
        names.update(_element_names(subsection))
    return names


@pytest.mark.parametrize(
    ("directory", "expected_element_count"),
    [
        ("s511_attempt_commit_offence", 3),
        ("s84_act_person_unsound_mind", 7),
        ("s107_abetment_doing_thing", 5),
        ("s120A_definition_criminal_conspiracy", 3),
        ("s304B_causing_death_child_below_14_years_age", 4),
        ("s304C_causing_allowing_death_child_below_14_years", 9),
        ("s375_rape", 13),
        ("s377D_mistake_age_sexual_offences", 5),
    ],
)
def test_nested_corpus_statutes_do_not_satisfy_with_empty_facts(
    directory: str,
    expected_element_count: int,
) -> None:
    path = Path("library/penal_code") / directory / "statute.yh"
    source = path.read_text(encoding="utf-8")
    statute = _module(source).statutes[0]

    result = StatuteEvaluator().evaluate(statute, _facts())

    assert result.provision_kind == "executable"
    assert result.branch_results
    assert not result.overall_satisfied
    assert all(len(branch.citation_path) > 1 for branch in result.branch_results)
    assert (
        sum(len(branch.element_results) for branch in result.branch_results)
        == expected_element_count
    )


@pytest.mark.parametrize(
    "directory",
    [
        "s511_attempt_commit_offence",
        "s84_act_person_unsound_mind",
        "s107_abetment_doing_thing",
        "s120A_definition_criminal_conspiracy",
        "s304B_causing_death_child_below_14_years_age",
        "s304C_causing_allowing_death_child_below_14_years",
        "s375_rape",
        "s377D_mistake_age_sexual_offences",
    ],
)
def test_nested_corpus_statutes_evaluate_every_element_with_matching_fact_fields(
    directory: str,
) -> None:
    """Boolean fact shims exercise every parsed element, not legal conclusions."""
    path = Path("library/penal_code") / directory / "statute.yh"
    statute = _module(path.read_text(encoding="utf-8")).statutes[0]

    result = StatuteEvaluator().evaluate(
        statute,
        _facts(**{name: True for name in _element_names(statute)}),
    )

    # This fixture intentionally evaluates one corpus statute in isolation.
    # A cross-section exception guard therefore cannot resolve its registered
    # target and must leave the statutory verdict unresolved rather than
    # silently treating that defence as false. The test still proves every
    # directly encoded element was visited with its matching fact shim.
    assert all(element.satisfied for element in result.element_results)
    if result.is_determinate:
        assert result.overall_satisfied is True
    else:
        assert result.overall_satisfied is None
        assert result.dependency_diagnostics


def test_sibling_subsection_leaves_are_alternative_branches() -> None:
    source = """
        statute 1 "Alternatives" {
            subsection (a) { elements { actus_reus first := "first"; } }
            subsection (b) { elements { actus_reus second := "second"; } }
        }
    """
    statute = _module(source).statutes[0]

    result = StatuteEvaluator().evaluate(statute, _facts(first=True, second=False))

    assert result.overall_satisfied
    assert [(branch.citation, branch.satisfied) for branch in result.branch_results] == [
        ("s1(a)", True),
        ("s1(b)", False),
    ]
    assert result.branch_results[0].element_results[0].citation_path == ("1", "(a)")


def test_nested_branch_inherits_ancestor_requirements_conjunctively() -> None:
    source = """
        statute 2 "Nested" {
            elements { actus_reus common := "common"; }
            subsection (1) { elements { any_of {
                circumstance first := "first";
                circumstance second := "second";
            } } }
        }
    """
    statute = _module(source).statutes[0]
    branches = rule_branches(lower_module(_module(source)).module.statutes[0])

    missing_ancestor = StatuteEvaluator().evaluate(
        statute,
        _facts(common=False, first=True, second=False),
    )
    satisfied = StatuteEvaluator().evaluate(
        statute,
        _facts(common=True, first=False, second=True),
    )

    assert len(branches) == 1
    assert branches[0].citation == "s2(1)"
    assert len(branches[0].requirements) == 2
    assert not missing_ancestor.overall_satisfied
    assert satisfied.overall_satisfied
    assert [result.citation_path for result in satisfied.element_results] == [
        ("2",),
        ("2", "(1)"),
        ("2", "(1)"),
    ]


def test_definition_only_provision_is_not_an_empty_satisfied_offence() -> None:
    source = """
        statute 3 "Definition only" {
            subsection (1) { definitions { meaning := "definition"; } }
        }
    """

    result = StatuteEvaluator().evaluate(_module(source).statutes[0], _facts())

    assert not result.overall_satisfied
    assert result.provision_kind == "definition_only"
    assert result.branch_results == []


def test_subsection_exceptions_apply_only_to_the_selected_branch() -> None:
    source = """
        statute 5 "Branch exception" {
            subsection (1) {
                elements { actus_reus act := "act"; }
                exception defence {
                    "defence applies"
                    "no conviction"
                    when defence
                }
            }
        }
    """
    statute = _module(source).statutes[0]

    defeated = StatuteEvaluator().evaluate(statute, _facts(act=True, defence=True))
    available = StatuteEvaluator().evaluate(statute, _facts(act=True, defence=False))

    assert not defeated.overall_satisfied
    assert defeated.branch_results[0].exception_paths == (("5", "(1)"),)
    assert available.overall_satisfied


def test_branch_traces_inherit_and_select_penalty_sources() -> None:
    source = """
        statute 6 "Penalty sources" {
            penalty { fine := unlimited; }
            subsection (1) {
                elements { actus_reus act := "act"; }
                penalty { imprisonment := 1 days; }
            }
        }
    """

    result = StatuteEvaluator().evaluate(_module(source).statutes[0], _facts(act=True))

    assert result.overall_satisfied
    assert result.branch_results[0].penalty_paths == (("6",), ("6", "(1)"))
    assert [penalty.citation for penalty in result.applicable_penalties] == ["s6", "s6(1)"]
    assert result.penalty_diagnostics == ()


def test_legacy_defeasible_facade_fails_closed_for_subsection_statutes() -> None:
    source = """
        statute 7 "Nested" {
            subsection (1) { elements { actus_reus act := "act"; } }
        }
    """

    result = DefeasibleReasoner().evaluate_with_exceptions(
        _module(source).statutes[0],
        {"act": True},
    )

    assert not result.base_satisfied
    assert result.final_verdict == "not_satisfied"
    assert "StatuteEvaluator" in result.reasoning_chain[0].description


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_z3_explicitly_rejects_unmigrated_subsection_branch_semantics() -> None:
    source = """
        statute 4 "Nested" {
            subsection (1) { elements { actus_reus act := "act"; } }
        }
    """
    module = _module(source)

    with pytest.raises(Z3UnsupportedFeature, match="canonical-IR subsection"):
        Z3Generator().generate(module)
