from __future__ import annotations

import pytest

from yuho.ast import BuiltinType
from yuho.services.analysis import analyze_source
from yuho.verify.alloy import AlloyGenerator, AlloyUnsupportedFeature


def _ast(source: str):
    result = analyze_source(source, file="<alloy>", run_semantic=False)
    assert not result.errors
    assert result.ast is not None
    return result.ast


def test_alloy_generates_plain_element_model() -> None:
    model = AlloyGenerator().generate(
        _ast(
            """
            statute 10 "Plain" {
                elements {
                    all_of {
                        actus_reus act := "Act";
                        mens_rea intent := "Intent";
                    }
                }
            }
            """
        )
    )

    assert "Statute_10" in model
    assert "conviction_iff_elements" in model


def test_alloy_rejects_penalty_semantics() -> None:
    with pytest.raises(AlloyUnsupportedFeature) as excinfo:
        AlloyGenerator().generate(
            _ast(
                """
                statute 11 "Penalty" {
                    elements { actus_reus act := "Act"; }
                    penalty { imprisonment := 1 years; }
                }
                """
            )
        )

    assert "s11: penalty semantics" in excinfo.value.features


def test_alloy_rejects_duration_struct_fields() -> None:
    with pytest.raises(AlloyUnsupportedFeature) as excinfo:
        AlloyGenerator().generate(
            _ast(
                """
                struct Sentence { duration term, }
                statute 11 "Duration field" {
                    elements { actus_reus act := "Act"; }
                }
                """
            )
        )

    assert "struct Sentence.term: duration type" in excinfo.value.features


def test_alloy_rejects_duration_literals() -> None:
    with pytest.raises(AlloyUnsupportedFeature) as excinfo:
        AlloyGenerator().generate(
            _ast(
                """
                duration term := 1 years;
                statute 11 "Duration literal" {
                    elements { actus_reus act := "Act"; }
                }
                """
            )
        )

    assert "variable term: duration type" in excinfo.value.features
    assert "variable term: duration literal" in excinfo.value.features


def test_alloy_duration_type_mapping_is_not_raw_days() -> None:
    generator = AlloyGenerator()

    assert generator._type_to_alloy(BuiltinType(name="duration")) == "Duration"
    assert generator._type_to_alloy("duration") == "Duration"


def test_alloy_rejects_case_law_semantics() -> None:
    with pytest.raises(AlloyUnsupportedFeature) as excinfo:
        AlloyGenerator().generate(
            _ast(
                """
                statute 12 "Case" {
                    elements { actus_reus act := "Act"; }
                    caselaw "A v B" "2026 SGCA 1" {
                        "Narrow reading"
                        element act
                    }
                }
                """
            )
        )

    assert "s12: case-law semantics" in excinfo.value.features


def test_alloy_rejects_exception_priority() -> None:
    with pytest.raises(AlloyUnsupportedFeature) as excinfo:
        AlloyGenerator().generate(
            _ast(
                """
                statute 13 "Priority" {
                    elements { actus_reus act := "Act"; }
                    exception defence {
                        "Defence"
                        "No conviction"
                        priority 10
                    }
                }
                """
            )
        )

    assert "s13: exception priority" in excinfo.value.features


def test_alloy_rejects_cross_section_predicate_descriptions() -> None:
    with pytest.raises(AlloyUnsupportedFeature) as excinfo:
        AlloyGenerator().generate(
            _ast(
                """
                statute 14 "Cross" {
                    elements {
                        actus_reus base := is_infringed(s299);
                    }
                }
                """
            )
        )

    assert any("cross-section expression IsInfringedNode" in f for f in excinfo.value.features)
