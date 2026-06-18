"""Chronology world model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Optional


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    message: str
    line: int = 0
    column: int = 0


@dataclass(frozen=True)
class DurationValue:
    years: int = 0
    months: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0


@dataclass(frozen=True)
class TimeRange:
    start: Any
    end: Any


@dataclass(frozen=True)
class Appearance:
    timeline: str
    range: TimeRange


@dataclass
class NamedRecord:
    name: str
    fields: dict[str, Any] = field(default_factory=dict)
    line: int = 0
    column: int = 0


@dataclass
class SourceRecord(NamedRecord):
    kind: str = "source"


@dataclass
class TimelineRecord(NamedRecord):
    pass


@dataclass
class EntitySchemaRecord:
    name: str
    parent: Optional[str] = None
    fields: dict[str, Any] = field(default_factory=dict)
    optional: set[str] = field(default_factory=set)
    line: int = 0
    column: int = 0


@dataclass
class EntityRecord(NamedRecord):
    type_name: str = "entity"

    @property
    def appearances(self) -> list[Appearance]:
        value = self.fields.get("appears_on")
        if value is None:
            value = self.fields.get("appearance")
        if value is None:
            return []
        if isinstance(value, Appearance):
            return [value]
        if isinstance(value, list):
            return [item for item in value if isinstance(item, Appearance)]
        return []


@dataclass
class RelationshipTypeRecord(NamedRecord):
    pass


@dataclass
class RelationshipRecord:
    source: str
    target: str
    label: Optional[str] = None
    temporal_scope: Optional[TimeRange] = None
    line: int = 0
    column: int = 0


@dataclass
class ScenarioRecord:
    name: str
    fork_from: Optional[str] = None
    world: Optional["ChronologyWorld"] = None
    line: int = 0
    column: int = 0


@dataclass
class ChronologyWorld:
    sources: dict[str, SourceRecord] = field(default_factory=dict)
    source_bundles: dict[str, NamedRecord] = field(default_factory=dict)
    locators: dict[str, NamedRecord] = field(default_factory=dict)
    rulesets: dict[str, NamedRecord] = field(default_factory=dict)
    deadline_rules: dict[str, NamedRecord] = field(default_factory=dict)
    issues: dict[str, NamedRecord] = field(default_factory=dict)
    issue_elements: dict[str, NamedRecord] = field(default_factory=dict)
    timelines: dict[str, TimelineRecord] = field(default_factory=dict)
    entities: dict[str, EntityRecord] = field(default_factory=dict)
    relationship_types: dict[str, RelationshipTypeRecord] = field(default_factory=dict)
    relationships: list[RelationshipRecord] = field(default_factory=list)
    scenarios: dict[str, ScenarioRecord] = field(default_factory=dict)
    views: dict[str, NamedRecord] = field(default_factory=dict)
    constraints: dict[str, NamedRecord] = field(default_factory=dict)
    entity_schemas: dict[str, EntitySchemaRecord] = field(default_factory=dict)
    function_defs: dict[str, Any] = field(default_factory=dict)
    statute_nodes: dict[str, Any] = field(default_factory=dict)
    duplicates: list[Diagnostic] = field(default_factory=list)
    statute_refs: set[str] = field(default_factory=set)
    section_refs: set[str] = field(default_factory=set)
    element_refs: set[str] = field(default_factory=set)
    exception_refs: set[str] = field(default_factory=set)
    caselaw_refs: set[str] = field(default_factory=set)

    def has_content(self) -> bool:
        return any(
            (
                self.sources,
                self.source_bundles,
                self.locators,
                self.rulesets,
                self.deadline_rules,
                self.issues,
                self.issue_elements,
                self.timelines,
                self.entities,
                self.relationship_types,
                self.relationships,
                self.scenarios,
                self.views,
                self.constraints,
            )
        )


BUILTIN_ENTITY_TYPES: dict[str, dict[str, set[str]]] = {
    "entity": {"required": set(), "optional": set()},
    "event": {"required": set(), "optional": set()},
    "person": {"required": set(), "optional": set()},
    "place": {"required": set(), "optional": set()},
    "object": {"required": set(), "optional": set()},
    "group": {"required": set(), "optional": set()},
    "character": {"required": set(), "optional": set()},
    "artifact": {"required": set(), "optional": set()},
    "location": {"required": set(), "optional": set()},
    "faction": {"required": set(), "optional": set()},
    "evidence": {
        "required": {"citation"},
        "optional": {"source", "source_ref", "locator_ref", "bates", "admissibility", "narrative"},
    },
    "witness": {
        "required": set(),
        "optional": {"affiliation", "credibility", "narrative"},
    },
    "claim": {
        "required": set(),
        "optional": {"source_ref", "locator_ref", "statute_ref", "section_ref", "narrative"},
    },
    "fact": {
        "required": set(),
        "optional": {"source_ref", "locator_ref", "statute_ref", "section_ref", "narrative"},
    },
    "expert_opinion": {
        "required": {"opinion"},
        "optional": {"source_ref", "locator_ref", "expert", "narrative"},
    },
    "deadline": {
        "required": {"rule", "jurisdiction", "trigger", "due"},
        "optional": {"source_ref", "rule_ref", "narrative"},
    },
    "exhibit": {
        "required": {"number", "description"},
        "optional": {"source_ref", "locator_ref", "narrative"},
    },
    "deposition": {
        "required": {"deponent", "date"},
        "optional": {"source_ref", "locator_ref", "narrative"},
    },
}


BUILTIN_RELATIONSHIPS: dict[str, dict[str, Any]] = {
    "cites": {"source": {"evidence"}, "target": {"claim", "fact"}},
    "contradicts": {},
    "corroborates": {},
    "supersedes": {"temporal": "source_after_target"},
    "caused": {"temporal": "source_before_target"},
    "causes": {"temporal": "source_before_target"},
    "enabled": {"temporal": "source_before_target"},
    "enables": {"temporal": "source_before_target"},
    "preceded": {"temporal": "source_before_target"},
    "impeaches": {"source": {"evidence"}, "target": {"witness"}},
}


TIME_VALUE = int | float | date


def source_location(node: Any) -> tuple[int, int]:
    loc = getattr(node, "source_location", None)
    if not loc:
        return 0, 0
    return loc.line, loc.col
