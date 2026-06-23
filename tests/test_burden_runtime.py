from __future__ import annotations

from yuho.ast import nodes
from yuho.eval.facts import struct_from_facts
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.services.analysis import analyze_source


def _statute() -> nodes.StatuteNode:
    result = analyze_source(
        """
        statute 1 "Burdened" {
            elements {
                actus_reus taking := "taking"
                    burden prosecution beyond_reasonable_doubt;
            }
        }
        """,
        run_semantic=False,
    )
    assert not result.parse_errors, [str(error) for error in result.parse_errors]
    assert result.ast is not None
    return result.ast.statutes[0]


def test_burden_metadata_mismatch_defeats_element_truth() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts(
            {
                "facts": {
                    "taking": {
                        "value": True,
                        "burden": "defence",
                        "standard_of_proof": "beyond_reasonable_doubt",
                    }
                }
            }
        ),
    )

    assert result.overall_satisfied is False
    assert result.element_results[0].satisfied is False
    assert any("burden=defence" in item for item in result.reasoning)


def test_burden_standard_metadata_mismatch_defeats_element_truth() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts(
            {
                "facts": {
                    "taking": {
                        "value": True,
                        "burden": "prosecution",
                        "standard_of_proof": "balance_of_probabilities",
                    }
                }
            }
        ),
    )

    assert result.overall_satisfied is False
    assert result.element_results[0].satisfied is False
    assert any("standard=balance_of_probabilities" in item for item in result.reasoning)


def test_legacy_facts_do_not_require_burden_metadata() -> None:
    result = StatuteEvaluator().evaluate(
        _statute(),
        struct_from_facts({"taking": True}),
    )

    assert result.overall_satisfied is True
    assert result.element_results[0].satisfied is True
