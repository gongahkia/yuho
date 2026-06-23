"""Typed fact model tests."""

from __future__ import annotations

import json
from pathlib import Path

from yuho.eval.facts import (
    FACTS_SCHEMA,
    TypedFact,
    fact_reason,
    fact_truthy,
    fact_value,
    normalize_facts,
    struct_from_facts,
)


def test_legacy_facts_remain_primitives() -> None:
    facts = normalize_facts({"taking": True, "intent": False})

    assert facts == {"taking": True, "intent": False}
    assert fact_truthy(facts["taking"]) is True
    assert fact_truthy(facts["intent"]) is False


def test_typed_facts_normalize_value_and_metadata() -> None:
    facts = normalize_facts(
        {
            "facts": {
                "taking": {
                    "value": True,
                    "type": "bool",
                    "source": "witness A",
                    "date": "2026-06-23",
                    "jurisdiction": "SG",
                    "evidential_status": "admitted",
                    "burden": "prosecution",
                    "standard_of_proof": "beyond_reasonable_doubt",
                    "confidence": 0.75,
                }
            }
        }
    )

    fact = facts["taking"]
    assert isinstance(fact, TypedFact)
    assert fact_value(fact) is True
    assert fact_truthy(fact) is True
    reason = fact_reason("taking", fact, True)
    assert "source=witness A" in reason
    assert "standard=beyond_reasonable_doubt" in reason
    assert "confidence=0.75" in reason


def test_documented_facts_schema_matches_runtime_constant() -> None:
    documented = json.loads(Path("docs/user/facts-schema.json").read_text(encoding="utf-8"))

    assert documented == FACTS_SCHEMA


def test_struct_from_facts_preserves_nested_records() -> None:
    facts = struct_from_facts({"outer": {"inner": True}})

    outer = facts.get_field("outer")
    assert outer.type_tag == "struct"
    assert outer.raw.get_field("inner").raw is True
