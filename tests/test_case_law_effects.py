from __future__ import annotations

import json

from yuho.ast import nodes
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.services.analysis import analyze_source
from yuho.transpile.json_transpiler import JSONTranspiler


def _facts(**fields: bool) -> StructInstance:
    return StructInstance(
        type_name="Facts",
        fields={name: Value(raw=value, type_tag="bool") for name, value in fields.items()},
    )


def _module(source: str) -> nodes.ModuleNode:
    result = analyze_source(source, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    assert result.ast is not None
    return result.ast


def test_case_law_doc_metadata_survives_ast_and_json_export() -> None:
    module = _module(
        """
        statute 1 "Theft" {
            elements { actus_reus taking := "takes"; }

            /// @role ratio
            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            /// @effect requires control_plus_deprivation
            caselaw "New v PP" "[2026] SGCA 1" {
                "Taking requires control plus deprivation"
                element taking
            }
        }
        """
    )

    case = module.statutes[0].case_law[0]

    assert case.doctrine_role == "ratio"
    assert case.jurisdiction == "singapore"
    assert case.court_level == "apex"
    assert case.decision_date == "2026-01-01"
    assert case.interpretive_effect == "requires"
    assert case.effect_fact == "control_plus_deprivation"

    payload = json.loads(JSONTranspiler(include_locations=False).transpile(module).output)
    encoded = payload["statutes"][0]["case_law"][0]
    assert encoded["doctrine_role"] == "ratio"
    assert encoded["interpretive_effect"] == "requires"
    assert encoded["effect_fact"] == "control_plus_deprivation"


def test_active_case_law_can_narrow_target_element() -> None:
    module = _module(
        """
        statute 1 "Theft" {
            elements { actus_reus taking := "takes"; }

            /// @effect requires control_plus_deprivation
            caselaw "New v PP" "[2026] SGCA 1" {
                "Taking requires control plus deprivation"
                element taking
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(taking=True, control_plus_deprivation=False),
    )

    assert result.overall_satisfied is False
    assert result.element_results[0].satisfied is False
    assert any("New v PP" in item for item in result.reasoning)


def test_active_case_law_can_expand_target_element() -> None:
    module = _module(
        """
        statute 1 "Consent" {
            elements { circumstance consent := "consent"; }

            /// @effect satisfies constructive_consent
            caselaw "Constructive Consent" "[2026] SGCA 2" {
                "Constructive consent can satisfy consent"
                element consent
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(consent=False, constructive_consent=True),
    )

    assert result.overall_satisfied is True
    assert result.element_results[0].satisfied is True
    assert any("Constructive Consent" in item for item in result.reasoning)


def test_overruled_case_law_effect_is_inactive() -> None:
    module = _module(
        """
        statute 1 "Theft" {
            elements { actus_reus taking := "takes"; }

            /// @effect requires control_plus_deprivation
            caselaw "Old v PP" "[1990] SGHC 1" {
                "Taking requires control plus deprivation"
                element taking
            }

            caselaw "New v PP" "[2026] SGCA 1" {
                "Old v PP is overruled"
                element taking
                treatment overruled "Old v PP" "[1990] SGHC 1"
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(taking=True, control_plus_deprivation=False),
    )

    assert result.overall_satisfied is True
    assert result.element_results[0].satisfied is True
    assert not any("Old v PP" in item for item in result.reasoning)
