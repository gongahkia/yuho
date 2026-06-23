"""Typed fact helpers for runtime explanation/debug commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


FACTS_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://yuho.local/schema/facts.schema.json",
    "title": "Yuho facts",
    "type": "object",
    "oneOf": [
        {"required": ["facts"]},
        {"not": {"required": ["facts"]}},
    ],
    "properties": {
        "facts": {
            "type": "object",
            "additionalProperties": {"$ref": "#/$defs/fact"},
        }
    },
    "additionalProperties": {"$ref": "#/$defs/factOrValue"},
    "$defs": {
        "factOrValue": {
            "oneOf": [
                {"$ref": "#/$defs/fact"},
                {"type": ["boolean", "number", "integer", "string", "null"]},
            ]
        },
        "fact": {
            "type": "object",
            "required": ["value"],
            "properties": {
                "value": {"type": ["boolean", "number", "integer", "string", "null"]},
                "type": {"enum": ["bool", "int", "float", "string", "money", "date", "duration"]},
                "source": {"type": "string"},
                "date": {"type": "string", "format": "date"},
                "jurisdiction": {"type": "string"},
                "evidential_status": {"type": "string"},
                "burden": {"type": "string"},
                "standard_of_proof": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
            },
            "additionalProperties": True,
        },
    },
}


@dataclass(frozen=True)
class TypedFact:
    """A normalized fact value plus optional evidential metadata."""

    value: Any
    type_name: str | None = None
    source: str | None = None
    date: str | None = None
    jurisdiction: str | None = None
    evidential_status: str | None = None
    burden: str | None = None
    standard_of_proof: str | None = None
    confidence: float | None = None

    def is_truthy(self) -> bool:
        return bool(self.value)

    def reason_suffix(self) -> str:
        parts: list[str] = []
        if self.evidential_status:
            parts.append(f"status={self.evidential_status}")
        if self.standard_of_proof:
            parts.append(f"standard={self.standard_of_proof}")
        if self.burden:
            parts.append(f"burden={self.burden}")
        if self.source:
            parts.append(f"source={self.source}")
        if self.date:
            parts.append(f"date={self.date}")
        if self.jurisdiction:
            parts.append(f"jurisdiction={self.jurisdiction}")
        if self.confidence is not None:
            parts.append(f"confidence={self.confidence:g}")
        return "; ".join(parts)


def normalize_facts(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return legacy or typed facts as a flat fact mapping."""
    raw_facts = payload.get("facts")
    if isinstance(raw_facts, Mapping):
        return {str(key): normalize_fact(value) for key, value in raw_facts.items()}
    return {str(key): normalize_fact(value) for key, value in payload.items()}


def normalize_fact(value: Any) -> Any:
    """Normalize one fact entry, preserving legacy primitive values."""
    if isinstance(value, TypedFact):
        return value
    if isinstance(value, Mapping) and "value" in value:
        confidence = value.get("confidence")
        return TypedFact(
            value=value.get("value"),
            type_name=_optional_str(value.get("type")),
            source=_optional_str(value.get("source")),
            date=_optional_str(value.get("date")),
            jurisdiction=_optional_str(value.get("jurisdiction")),
            evidential_status=_optional_str(value.get("evidential_status")),
            burden=_optional_str(value.get("burden")),
            standard_of_proof=_optional_str(value.get("standard_of_proof")),
            confidence=float(confidence) if isinstance(confidence, (int, float)) else None,
        )
    return value


def fact_value(value: Any) -> Any:
    """Return the primitive value used by legacy evaluators."""
    if isinstance(value, TypedFact):
        return value.value
    return value


def runtime_value_from_fact(value: Any):
    """Convert a JSON/typed fact value into a Yuho runtime Value."""
    from yuho.eval.interpreter import StructInstance, Value

    metadata = value if isinstance(value, TypedFact) else None
    raw = fact_value(value)
    if isinstance(raw, Mapping):
        fields = {
            str(key): runtime_value_from_fact(child) for key, child in normalize_facts(raw).items()
        }
        return Value(
            raw=StructInstance(type_name="Facts", fields=fields),
            type_tag="struct",
            metadata=metadata,
        )
    if isinstance(raw, list):
        return Value(
            raw=[runtime_value_from_fact(child) for child in raw],
            type_tag="list",
            metadata=metadata,
        )
    return Value(raw=raw, metadata=metadata)


def struct_from_facts(facts: Mapping[str, Any], type_name: str = "Facts"):
    """Build a StructInstance from a fact mapping."""
    from yuho.eval.interpreter import StructInstance

    normalized = normalize_facts(facts)
    return StructInstance(
        type_name=type_name,
        fields={str(key): runtime_value_from_fact(value) for key, value in normalized.items()},
    )


def fact_truthy(value: Any) -> bool:
    """Return Yuho truthiness for a fact or typed fact."""
    if value is None:
        return False
    if isinstance(value, TypedFact):
        return value.is_truthy()
    is_truthy = getattr(value, "is_truthy", None)
    if callable(is_truthy):
        return bool(is_truthy())
    raw = getattr(value, "raw", value)
    return bool(raw)


def fact_reason(name: str, value: Any, satisfied: bool) -> str:
    """Return an explanation phrase for one fact lookup."""
    state = "truthy" if satisfied else "missing or false"
    suffix = value.reason_suffix() if isinstance(value, TypedFact) else ""
    if suffix:
        return f"fact '{name}' is {state} ({suffix})"
    return f"fact '{name}' is {state}"


def _optional_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None
