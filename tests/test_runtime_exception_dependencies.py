"""Regression coverage for traceable cross-section exception guards."""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.eval import DefeasibleReasoner, Interpreter, StatuteEvaluator, StructInstance, Value
from yuho.ir import diagnose_capabilities, lower_module, rule_branches
from yuho.services.analysis import analyze_source

_COMPOSED_SOURCE = """
statute 84 "Unsoundness defence" {
  elements { circumstance unsoundness_defence := "unsoundness applies"; }
}

statute 85 "Intoxication defence" {
  elements { circumstance intoxication_defence := "intoxication applies"; }
}

statute 96 "Private-defence gateway" {
  elements { circumstance private_defence := "private defence applies"; }
}

statute 299 "Charge" {
  elements { actus_reus charged_act := "charged act"; }
  exception s84_defence {
    "unsoundness"
    "s84 defeats the charge"
    when is_infringed(s84)
  }
  exception s85_defence {
    "intoxication"
    "s85 defeats the charge"
    when is_infringed(s85)
  }
  exception s96_defence {
    "private defence"
    "s96 defeats the charge"
    when is_infringed(s96)
  }
}
"""


def _module(source: str):
    analysis = analyze_source(source, run_semantic=False)
    assert analysis.ast is not None, [str(error) for error in analysis.parse_errors]
    return analysis.ast


def _evaluate(source: str, **facts: bool):
    module = _module(source)
    interpreter = Interpreter()
    interpreter.interpret(module)
    result = StatuteEvaluator().evaluate(
        next(statute for statute in module.statutes if statute.section_number == "299"),
        StructInstance(
            type_name="Facts",
            fields={name: Value(raw=value, type_tag="bool") for name, value in facts.items()},
        ),
        interpreter.env,
    )
    return module, interpreter, result


@pytest.mark.parametrize(
    ("target_section", "fact_name"),
    [
        ("84", "unsoundness_defence"),
        ("85", "intoxication_defence"),
        ("96", "private_defence"),
    ],
)
def test_registered_defence_guard_uses_the_charge_fact_context(
    target_section: str,
    fact_name: str,
) -> None:
    module = _module(_COMPOSED_SOURCE)
    interpreter = Interpreter()
    interpreter.interpret(module)
    # The fact supplied to the charge must shadow an older environment binding.
    interpreter.env.set(fact_name, Value(raw=False, type_tag="bool"))
    facts = {
        "charged_act": True,
        "unsoundness_defence": False,
        "intoxication_defence": False,
        "private_defence": False,
    }
    facts[fact_name] = True

    result = StatuteEvaluator().evaluate(
        module.statutes[-1],
        StructInstance(
            type_name="Facts",
            fields={name: Value(raw=value, type_tag="bool") for name, value in facts.items()},
        ),
        interpreter.env,
    )

    assert result.overall_satisfied is False
    assert result.is_determinate is True
    dependency = next(
        dependency
        for dependency in result.dependency_results
        if dependency.edge.target_section == target_section
    )
    assert dependency.edge.reference_kind == "is_infringed"
    assert dependency.status == "satisfied"
    assert dependency.subresult is not None
    assert dependency.subresult.overall_satisfied is True
    assert dependency.subresult.statute_section == target_section


def test_canonical_ir_records_exception_dependency_edges() -> None:
    module = _module(_COMPOSED_SOURCE)
    charge = lower_module(module).module.statutes[-1]
    branch = rule_branches(charge)[0]

    assert [dependency.target_section for dependency in branch.dependencies] == ["84", "85", "96"]
    assert all(dependency.source_kind == "exception" for dependency in branch.dependencies)
    assert branch.to_dict()["dependencies"][2]["reference_kind"] == "is_infringed"


def test_checked_in_s299_corpus_records_its_general_exception_edges() -> None:
    source = Path("library/penal_code/s299_culpable_homicide/statute.yh").read_text(
        encoding="utf-8"
    )
    charge = lower_module(_module(source)).module.statutes[0]
    targets = {
        dependency.target_section
        for branch in rule_branches(charge)
        for dependency in branch.dependencies
    }

    assert {"84", "85", "96"}.issubset(targets)


def test_non_runtime_canonical_consumers_reject_exception_dependency_edges() -> None:
    ir = lower_module(_module(_COMPOSED_SOURCE))

    for consumer in ("alloy", "lean"):
        diagnostics = diagnose_capabilities(ir, consumer)
        assert any(diagnostic.feature == "cross_section_dependency" for diagnostic in diagnostics)


def test_missing_exception_dependency_is_unresolved_not_false() -> None:
    _, _, result = _evaluate(
        """
        statute 299 "Charge" {
          elements { actus_reus charged_act := "charged act"; }
          exception unavailable {
            "unavailable defence"
            "defeat"
            when is_infringed(s999)
          }
        }
        """,
        charged_act=True,
    )

    assert result.overall_satisfied is None
    assert result.is_determinate is False
    assert result.dependency_results[0].status == "unresolved"
    assert result.dependency_diagnostics[0].code == "YRDG001"
    assert result.dependency_diagnostics[0].target_section == "999"


def test_legacy_defeasible_facade_exposes_unresolved_dependency() -> None:
    module = _module("""
        statute 299 "Charge" {
          elements { actus_reus charged_act := "charged act"; }
          exception unavailable {
            "unavailable defence"
            "defeat"
            when is_infringed(s999)
          }
        }
        """)

    result = DefeasibleReasoner().evaluate_with_exceptions(
        module.statutes[0],
        {"charged_act": True},
        Interpreter().env,
    )

    assert result.final_verdict == "unresolved_dependency"
    assert result.exceptions_applied[0].dependency_diagnostics[0].code == "YRDG001"


def test_cyclic_exception_dependencies_are_diagnosed() -> None:
    _, _, result = _evaluate(
        """
        statute 299 "Charge" {
          elements { actus_reus charged_act := "charged act"; }
          exception loop { "loop" "defeat" when is_infringed(s84) }
        }
        statute 84 "Defence" {
          elements { circumstance defence_applies := "defence applies"; }
          exception loop { "loop" "defeat" when is_infringed(s299) }
        }
        """,
        charged_act=True,
        defence_applies=True,
    )

    assert result.overall_satisfied is None
    assert result.dependency_results[0].status == "unresolved"
    assert result.dependency_diagnostics[0].code == "YRDG002"
    assert "cycle detected" in result.dependency_diagnostics[0].message


def test_unsupported_guard_expression_is_diagnosed() -> None:
    _, _, result = _evaluate(
        """
        statute 299 "Charge" {
          elements { actus_reus charged_act := "charged act"; }
          exception unknown { "unknown" "defeat" when unknown_guard() }
        }
        """,
        charged_act=True,
    )

    assert result.overall_satisfied is None
    assert result.dependency_diagnostics[0].code == "YRDG003"
    assert "Undefined function 'unknown_guard'" in result.dependency_diagnostics[0].message
