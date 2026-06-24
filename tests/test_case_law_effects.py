from __future__ import annotations

import json

from yuho.ast import nodes
from yuho.eval.facts import struct_from_facts
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
            /// @burden_shift prosecution beyond_reasonable_doubt
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
    assert case.burden_shift == "prosecution"
    assert case.burden_shift_standard == "beyond_reasonable_doubt"

    payload = json.loads(JSONTranspiler(include_locations=False).transpile(module).output)
    encoded = payload["statutes"][0]["case_law"][0]
    assert encoded["doctrine_role"] == "ratio"
    assert encoded["interpretive_effect"] == "requires"
    assert encoded["effect_fact"] == "control_plus_deprivation"
    assert encoded["burden_shift"] == "prosecution"
    assert encoded["burden_shift_standard"] == "beyond_reasonable_doubt"


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


def test_negative_treatment_does_not_adopt_target_effect() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            caselaw "Distinguishing Case" "[2026] SGCA 1" {
                "Distinguishes source without adopting its effect"
                element deception
                treatment distinguished "Restrictive Source" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    assert effects == {}


def test_negative_treatment_is_skipped_before_positive_adoption() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            /// @effect satisfies rescue_fact
            caselaw "Expansive Source" "[2021] SGCA 1" {
                "Expansive source"
                element deception
            }

            caselaw "Fallback Adopter" "[2026] SGCA 1" {
                "Skips negative treatment and adopts positive target"
                element deception
                treatment disapproved "Restrictive Source" "[2020] SGCA 1"
                treatment approved "Expansive Source" "[2021] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    adopted = [
        case for case in effects["deception"]
        if case.case_name.value == "Fallback Adopter"
    ]
    assert len(adopted) == 1
    assert adopted[0].interpretive_effect == "satisfies"


def test_inactive_adopting_case_does_not_materialize_adopted_effect() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            caselaw "Inactive Adopter" "[2025] SGCA 1" {
                "Would adopt source if active"
                element deception
                treatment approved "Restrictive Source" "[2020] SGCA 1"
            }

            caselaw "Overruling Case" "[2026] SGCA 1" {
                "Overrules adopter"
                element deception
                treatment overruled "Inactive Adopter" "[2025] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    assert not any(
        case.case_name.value == "Inactive Adopter"
        for case in effects["deception"]
    )


def test_cumulative_case_law_effects_apply_in_declaration_order() -> None:
    expansive_then_restrictive = _module(
        """
        statute 1 "Cheating" {
            elements { actus_reus deception := "deception"; }

            /// @effect satisfies rescue_fact
            caselaw "Expansive First" "[2026] SGCA 1" {
                "Can satisfy first"
                element deception
            }

            /// @effect requires active_misleading
            caselaw "Restrictive Second" "[2026] SGCA 2" {
                "Can require second"
                element deception
            }
        }
        """
    )
    restrictive_then_expansive = _module(
        """
        statute 1 "Cheating" {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive First" "[2026] SGCA 1" {
                "Can require first"
                element deception
            }

            /// @effect satisfies rescue_fact
            caselaw "Expansive Second" "[2026] SGCA 2" {
                "Can satisfy second"
                element deception
            }
        }
        """
    )
    facts = _facts(deception=False, rescue_fact=True, active_misleading=False)
    evaluator = StatuteEvaluator()

    first = evaluator.evaluate(expansive_then_restrictive.statutes[0], facts)
    second = evaluator.evaluate(restrictive_then_expansive.statutes[0], facts)

    assert first.overall_satisfied is False
    assert second.overall_satisfied is True


def test_case_law_conflict_prefers_statute_jurisdiction() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @jurisdiction england
            /// @court_level apex
            /// @date 2026-01-01
            /// @effect satisfies active_misleading
            caselaw "Foreign v PP" "[2026] UKSC 1" {
                "Foreign expansive view"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level high
            /// @date 2020-01-01
            /// @effect requires active_misleading
            caselaw "Local v PP" "[2020] SGHC 1" {
                "Local restrictive view"
                element deception
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(deception=True, active_misleading=False),
    )

    assert result.overall_satisfied is False
    assert any("Local v PP" in item for item in result.reasoning)
    assert not any("Foreign v PP" in item for item in result.reasoning)


def test_case_law_conflict_buckets_normalise_effect_fact_key() -> None:
    low = nodes.CaseLawNode(
        case_name=nodes.StringLit("Low v PP"),
        element_ref="deception",
        interpretive_effect="requires",
        effect_fact="active_misleading",
        jurisdiction="singapore",
        court_level="high",
        decision_date="2020-01-01",
    )
    apex = nodes.CaseLawNode(
        case_name=nodes.StringLit("Apex v PP"),
        element_ref="deception",
        interpretive_effect="satisfies",
        effect_fact="active-misleading",
        jurisdiction="singapore",
        court_level="apex",
        decision_date="2020-01-01",
    )

    selected = StatuteEvaluator._resolve_case_effect_conflicts(
        [low, apex],
        statute_jurisdiction="singapore",
    )

    assert [case.case_name.value for case in selected] == ["Apex v PP"]


def test_case_law_same_effect_fact_and_kind_are_not_precedence_collapsed() -> None:
    first = nodes.CaseLawNode(
        case_name=nodes.StringLit("First v PP"),
        element_ref="deception",
        interpretive_effect="requires",
        effect_fact="active_misleading",
        jurisdiction="singapore",
        court_level="high",
        decision_date="2020-01-01",
    )
    second = nodes.CaseLawNode(
        case_name=nodes.StringLit("Second v PP"),
        element_ref="deception",
        interpretive_effect="requires",
        effect_fact="active-misleading",
        jurisdiction="singapore",
        court_level="apex",
        decision_date="2020-01-01",
    )

    selected = StatuteEvaluator._resolve_case_effect_conflicts(
        [first, second],
        statute_jurisdiction="singapore",
    )

    assert [case.case_name.value for case in selected] == [
        "First v PP",
        "Second v PP",
    ]


def test_case_law_conflict_prefers_higher_court_over_newer_date() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @jurisdiction singapore
            /// @court_level high
            /// @date 2026-01-01
            /// @effect satisfies active_misleading
            caselaw "High Court v PP" "[2026] SGHC 1" {
                "High Court expansive view"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2020-01-01
            /// @effect requires active_misleading
            caselaw "Apex v PP" "[2020] SGCA 1" {
                "Apex restrictive view"
                element deception
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(deception=True, active_misleading=False),
    )

    assert result.overall_satisfied is False
    assert any("Apex v PP" in item for item in result.reasoning)
    assert not any("High Court v PP" in item for item in result.reasoning)


def test_case_law_conflict_prefers_newer_same_court_decision() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2020-01-01
            /// @effect requires active_misleading
            caselaw "Old Apex v PP" "[2020] SGCA 1" {
                "Old restrictive view"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            /// @effect satisfies active_misleading
            caselaw "New Apex v PP" "[2026] SGCA 1" {
                "New expansive view"
                element deception
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(deception=False, active_misleading=True),
    )

    assert result.overall_satisfied is True
    assert any("New Apex v PP" in item for item in result.reasoning)
    assert not any("Old Apex v PP" in item for item in result.reasoning)


def test_case_law_burden_shift_constrains_effect_fact_metadata() -> None:
    module = _module(
        """
        statute 1 "Excuse" jurisdiction singapore {
            elements { circumstance excuse := "excuse"; }

            /// @jurisdiction singapore
            /// @effect satisfies lawful_excuse
            /// @burden_shift defence balance_of_probabilities
            caselaw "Excuse Case" "[2026] SGCA 3" {
                "Lawful excuse shifts to the defence"
                element excuse
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        struct_from_facts(
            {
                "facts": {
                    "excuse": False,
                    "lawful_excuse": {
                        "value": True,
                        "burden": "prosecution",
                        "standard_of_proof": "balance_of_probabilities",
                    },
                }
            }
        ),
    )

    assert result.overall_satisfied is False
    assert result.element_results[0].satisfied is False
    assert any("expects burden=defence" in item for item in result.reasoning)


def test_case_law_burden_shift_accepts_matching_effect_fact_metadata() -> None:
    module = _module(
        """
        statute 1 "Excuse" jurisdiction singapore {
            elements { circumstance excuse := "excuse"; }

            /// @jurisdiction singapore
            /// @effect satisfies lawful_excuse
            /// @burden_shift defence balance_of_probabilities
            caselaw "Excuse Case" "[2026] SGCA 3" {
                "Lawful excuse shifts to the defence"
                element excuse
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        struct_from_facts(
            {
                "facts": {
                    "excuse": False,
                    "lawful_excuse": {
                        "value": True,
                        "burden": "defence",
                        "standard_of_proof": "balance_of_probabilities",
                    },
                }
            }
        ),
    )

    assert result.overall_satisfied is True
    assert result.element_results[0].satisfied is True
    assert any("Excuse Case" in item for item in result.reasoning)


def test_case_law_burden_shift_is_ignored_for_foreign_jurisdiction() -> None:
    module = _module(
        """
        statute 1 "Excuse" jurisdiction singapore {
            elements { circumstance excuse := "excuse"; }

            /// @jurisdiction england
            /// @effect satisfies lawful_excuse
            /// @burden_shift defence balance_of_probabilities
            caselaw "Foreign Excuse Case" "[2026] UKSC 3" {
                "Foreign shift is not jurisdiction-compatible"
                element excuse
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        struct_from_facts(
            {
                "facts": {
                    "excuse": False,
                    "lawful_excuse": {
                        "value": True,
                        "burden": "prosecution",
                        "standard_of_proof": "balance_of_probabilities",
                    },
                }
            }
        ),
    )

    assert result.overall_satisfied is True
    assert not any("expects burden=defence" in item for item in result.reasoning)


def test_positive_treatment_adopts_target_effect_with_treating_case_precedence() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @jurisdiction england
            /// @court_level apex
            /// @date 2020-01-01
            /// @effect requires active_misleading
            caselaw "Foreign Restrictive" "[2020] UKSC 1" {
                "Foreign restrictive view"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level high
            /// @date 2021-01-01
            /// @effect satisfies active_misleading
            caselaw "Local Expansive" "[2021] SGHC 1" {
                "Local expansive view"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Adopting Apex" "[2026] SGCA 1" {
                "Adopts the restrictive view"
                element deception
                treatment follows "Foreign Restrictive" "[2020] UKSC 1"
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(deception=True, active_misleading=False),
    )

    assert result.overall_satisfied is False
    assert any("Adopting Apex" in item for item in result.reasoning)
    assert not any("Local Expansive" in item for item in result.reasoning)


def test_positive_treatment_adoption_preserves_declaration_order_tiebreak() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Earlier Adopter" "[2026] SGCA 2" {
                "Adopts restrictive source"
                element deception
                treatment approved "Restrictive Source" "[2020] SGCA 1"
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            /// @effect satisfies active_misleading
            caselaw "Later Expansive" "[2026] SGCA 3" {
                "Later equal-precedence expansive view"
                element deception
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(deception=True, active_misleading=False),
    )

    assert result.overall_satisfied is True
    assert not any("Earlier Adopter" in item for item in result.reasoning)


def test_case_with_own_effect_does_not_adopt_treatment_target_effect() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            /// @effect satisfies active_misleading
            caselaw "Own Effect" "[2026] SGCA 1" {
                "Own effect wins over adopted source"
                element deception
                treatment follows "Restrictive Source" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    selected = effects["deception"][0]
    assert selected.case_name.value == "Own Effect"
    assert selected.interpretive_effect == "satisfies"


def test_positive_treatment_to_unknown_case_does_not_materialize_effect() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            caselaw "Unknown Adopter" "[2026] SGCA 1" {
                "Unknown target cannot supply an effect"
                element deception
                treatment follows "Missing Case" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    assert effects == {}


def test_positive_treatment_adoption_skips_unknown_target_before_known_target() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Fallback Adopter" "[2026] SGCA 1" {
                "Skips unknown target and adopts known source"
                element deception
                treatment follows "Missing Case" "[2020] SGCA 1"
                treatment approved "Restrictive Source" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    fallback = [
        case for case in effects["deception"]
        if case.case_name.value == "Fallback Adopter"
    ]
    assert len(fallback) == 1
    assert fallback[0].interpretive_effect == "requires"


def test_positive_treatment_adoption_skips_effectless_target_before_known_target() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            caselaw "Effectless Source" "[2020] SGCA 1" {
                "Explanatory source without a materialized effect"
                element deception
            }

            /// @effect satisfies rescue_fact
            caselaw "Expansive Source" "[2021] SGCA 1" {
                "Expansive source"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Fallback Adopter" "[2026] SGCA 1" {
                "Skips effectless target and adopts known source"
                element deception
                treatment follows "Effectless Source" "[2020] SGCA 1"
                treatment approved "Expansive Source" "[2021] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    fallback = [
        case for case in effects["deception"]
        if case.case_name.value == "Fallback Adopter"
    ]
    assert len(fallback) == 1
    assert fallback[0].interpretive_effect == "satisfies"
    assert fallback[0].effect_fact == "rescue_fact"


def test_positive_treatment_adoption_uses_first_complete_positive_target() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            /// @effect satisfies active_misleading
            caselaw "Expansive Source" "[2021] SGCA 1" {
                "Expansive source"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Ordered Adopter" "[2026] SGCA 1" {
                "Uses first complete positive source"
                element deception
                treatment follows "Restrictive Source" "[2020] SGCA 1"
                treatment approved "Expansive Source" "[2021] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    adopted = [
        case for case in effects["deception"]
        if case.case_name.value == "Ordered Adopter"
    ]
    assert len(adopted) == 1
    assert adopted[0].interpretive_effect == "requires"
    assert adopted[0].effect_fact == "active_misleading"


def test_applies_treatment_adopts_target_effect() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @effect requires active_misleading
            caselaw "Restrictive Source" "[2020] SGCA 1" {
                "Restrictive source"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Applied Adopter" "[2026] SGCA 1" {
                "Applies source"
                element deception
                treatment applies "Restrictive Source" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    adopted = [
        case for case in effects["deception"]
        if case.case_name.value == "Applied Adopter"
    ]
    assert len(adopted) == 1
    assert adopted[0].interpretive_effect == "requires"
    assert adopted[0].effect_fact == "active_misleading"


def test_positive_treatment_adoption_preserves_target_metadata_without_override() -> None:
    module = _module(
        """
        statute 1 "Excuse" jurisdiction singapore {
            elements { circumstance excuse := "excuse"; }

            /// @jurisdiction singapore
            /// @effect satisfies lawful_excuse
            /// @burden_shift defence balance_of_probabilities
            caselaw "Burden Source" "[2020] SGCA 1" {
                "Source supplies metadata"
                element excuse
            }

            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Metadata Fallback Adopter" "[2026] SGCA 1" {
                "Adopts metadata from source"
                element excuse
                treatment follows "Burden Source" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    adopted = [
        case for case in effects["excuse"]
        if case.case_name.value == "Metadata Fallback Adopter"
    ]
    assert len(adopted) == 1
    assert adopted[0].burden_shift == "defence"
    assert adopted[0].burden_shift_standard == "balance_of_probabilities"
    assert adopted[0].jurisdiction == "singapore"


def test_positive_treatment_adoption_prefers_treating_case_metadata_override() -> None:
    module = _module(
        """
        statute 1 "Excuse" jurisdiction singapore {
            elements { circumstance excuse := "excuse"; }

            /// @jurisdiction england
            /// @effect satisfies lawful_excuse
            /// @burden_shift prosecution beyond_reasonable_doubt
            caselaw "Foreign Burden Source" "[2020] UKSC 1" {
                "Source supplies foreign metadata"
                element excuse
            }

            /// @jurisdiction singapore
            /// @burden_shift defence balance_of_probabilities
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Metadata Override Adopter" "[2026] SGCA 1" {
                "Overrides metadata from source"
                element excuse
                treatment follows "Foreign Burden Source" "[2020] UKSC 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    adopted = [
        case for case in effects["excuse"]
        if case.case_name.value == "Metadata Override Adopter"
    ]
    assert len(adopted) == 1
    assert adopted[0].burden_shift == "defence"
    assert adopted[0].burden_shift_standard == "balance_of_probabilities"
    assert adopted[0].jurisdiction == "singapore"


def test_positive_treatment_adoption_remaps_effect_to_treating_case_element() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements {
                actus_reus source_element := "source element";
                actus_reus deception := "deception";
            }

            /// @effect requires active_misleading
            caselaw "Source Element Case" "[2020] SGCA 1" {
                "Source element rule"
                element source_element
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Element Remap Adopter" "[2026] SGCA 1" {
                "Applies source rule to deception"
                element deception
                treatment follows "Source Element Case" "[2020] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    remapped = [
        case for case in effects["deception"]
        if case.case_name.value == "Element Remap Adopter"
    ]
    assert len(remapped) == 1
    assert remapped[0].interpretive_effect == "requires"
    assert remapped[0].effect_fact == "active_misleading"


def test_positive_treatment_adoption_resolves_transitive_chain() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            /// @jurisdiction england
            /// @court_level apex
            /// @date 2020-01-01
            /// @effect requires active_misleading
            caselaw "Foreign Restrictive" "[2020] UKSC 1" {
                "Foreign restrictive view"
                element deception
            }

            caselaw "Intermediate Adopter" "[2024] SGHC 1" {
                "Follows foreign restrictive view"
                element deception
                treatment follows "Foreign Restrictive" "[2020] UKSC 1"
            }

            /// @jurisdiction singapore
            /// @court_level high
            /// @date 2021-01-01
            /// @effect satisfies active_misleading
            caselaw "Local Expansive" "[2021] SGHC 1" {
                "Local expansive view"
                element deception
            }

            /// @jurisdiction singapore
            /// @court_level apex
            /// @date 2026-01-01
            caselaw "Apex Chain Adopter" "[2026] SGCA 1" {
                "Applies the adopted restrictive view"
                element deception
                treatment applies "Intermediate Adopter" "[2024] SGHC 1"
            }
        }
        """
    )

    result = StatuteEvaluator().evaluate(
        module.statutes[0],
        _facts(deception=True, active_misleading=False),
    )

    assert result.overall_satisfied is False
    assert any("Apex Chain Adopter" in item for item in result.reasoning)
    assert not any("Local Expansive" in item for item in result.reasoning)


def test_positive_treatment_adoption_cycle_does_not_materialize_effect() -> None:
    module = _module(
        """
        statute 1 "Cheating" jurisdiction singapore {
            elements { actus_reus deception := "deception"; }

            caselaw "Cycle A" "[2026] SGCA 1" {
                "Adopts Cycle B"
                element deception
                treatment follows "Cycle B" "[2026] SGCA 2"
            }

            caselaw "Cycle B" "[2026] SGCA 2" {
                "Adopts Cycle A"
                element deception
                treatment approved "Cycle A" "[2026] SGCA 1"
            }
        }
        """
    )

    effects = StatuteEvaluator().active_case_law_effects(
        module.statutes[0].case_law,
        statute_jurisdiction=module.statutes[0].jurisdiction,
    )

    assert effects == {}
