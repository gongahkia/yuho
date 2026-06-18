"""Chronology exporters and semantic diff renderers."""

from __future__ import annotations

import html
import json
from datetime import date
from typing import Any, Optional

from yuho.chronology.model import (
    Appearance,
    ChronologyWorld,
    Diagnostic,
    DurationValue,
    EntityRecord,
    NamedRecord,
    RelationshipRecord,
    SourceRecord,
    TimeRange,
)


def render_world(world: ChronologyWorld, target: str, narrative: Optional[str] = None) -> str:
    if narrative:
        world = filter_world_by_narrative(world, narrative)
    if target == "json":
        return json.dumps(world_to_dict(world), indent=2, sort_keys=True)
    if target == "markdown":
        return render_markdown(world)
    if target == "mermaid":
        return render_mermaid(world)
    if target == "svg":
        return render_svg(world)
    if target == "html":
        svg = render_svg(world)
        return f"<!doctype html><html><body>{svg}<pre>{html.escape(render_markdown(world))}</pre></body></html>\n"
    raise ValueError(f"Unsupported chronology export target: {target}")


def filter_world_by_narrative(world: ChronologyWorld, narrative: str) -> ChronologyWorld:
    entities = {
        name: entity
        for name, entity in world.entities.items()
        if _matches_narrative(entity.fields.get("narrative"), narrative)
        or _matches_narrative(entity.fields.get("narratives"), narrative)
    }
    relationships = [
        rel for rel in world.relationships if rel.source in entities and rel.target in entities
    ]
    timeline_names = {
        appearance.timeline
        for entity in entities.values()
        for appearance in entity.appearances
    }
    return ChronologyWorld(
        sources=dict(world.sources),
        source_bundles=dict(world.source_bundles),
        locators=dict(world.locators),
        rulesets=dict(world.rulesets),
        deadline_rules=dict(world.deadline_rules),
        issues=dict(world.issues),
        issue_elements=dict(world.issue_elements),
        timelines={name: timeline for name, timeline in world.timelines.items() if name in timeline_names},
        entities=entities,
        relationship_types=dict(world.relationship_types),
        relationships=relationships,
        scenarios=dict(world.scenarios),
        views=dict(world.views),
        constraints=dict(world.constraints),
        entity_schemas=dict(world.entity_schemas),
        function_defs=dict(world.function_defs),
        statute_nodes=dict(world.statute_nodes),
        duplicates=list(world.duplicates),
        statute_refs=set(world.statute_refs),
        section_refs=set(world.section_refs),
        element_refs=set(world.element_refs),
        exception_refs=set(world.exception_refs),
        caselaw_refs=set(world.caselaw_refs),
    )


def world_to_dict(world: ChronologyWorld) -> dict[str, Any]:
    return {
        "sources": {name: _source_to_dict(record) for name, record in sorted(world.sources.items())},
        "source_bundles": _record_map(world.source_bundles),
        "locators": _record_map(world.locators),
        "rulesets": _record_map(world.rulesets),
        "deadline_rules": _record_map(world.deadline_rules),
        "issues": _record_map(world.issues),
        "issue_elements": _record_map(world.issue_elements),
        "timelines": {name: _record_to_dict(record) for name, record in sorted(world.timelines.items())},
        "entities": {name: _entity_to_dict(record) for name, record in sorted(world.entities.items())},
        "relationship_types": _record_map(world.relationship_types),
        "relationships": [_relationship_to_dict(rel) for rel in world.relationships],
        "scenarios": {
            name: _scenario_to_dict(record)
            for name, record in sorted(world.scenarios.items())
        },
        "views": _record_map(world.views),
        "constraints": _record_map(world.constraints),
        "entity_schemas": {
            name: {
                "parent": record.parent,
                "fields": record.fields,
                "optional": sorted(record.optional),
            }
            for name, record in sorted(world.entity_schemas.items())
        },
    }


def render_markdown(world: ChronologyWorld) -> str:
    lines = ["# Chronology", ""]
    if world.sources:
        lines.extend(["## Sources", ""])
        for source in sorted(world.sources.values(), key=lambda item: item.name):
            citation = source.fields.get("citation", "")
            lines.append(f"- **{source.name}** ({source.kind}) {citation}".rstrip())
        lines.append("")
    if world.timelines:
        lines.extend(["## Timelines", ""])
        for timeline in sorted(world.timelines.values(), key=lambda item: item.name):
            start = _value(timeline.fields.get("start"))
            end = _value(timeline.fields.get("end"))
            lines.append(f"- **{timeline.name}**: {start}..{end}")
        lines.append("")
    if world.relationship_types:
        lines.extend(["## Relationship Types", ""])
        for reltype in sorted(world.relationship_types.values(), key=lambda item: item.name):
            source = reltype.fields.get("source", reltype.fields.get("sources", "any"))
            target = reltype.fields.get("target", reltype.fields.get("targets", "any"))
            lines.append(f"- **{reltype.name}**: {source} -> {target}")
        lines.append("")
    if world.entities:
        lines.extend(["## Entities", ""])
        for entity in sorted(world.entities.values(), key=lambda item: item.name):
            summary = entity.fields.get("summary") or entity.fields.get("description") or ""
            lines.append(f"- **{entity.name}** [{entity.type_name}] {summary}".rstrip())
        lines.append("")
    if world.relationships:
        lines.extend(["## Relationships", ""])
        for rel in world.relationships:
            label = rel.label or "rel"
            lines.append(f"- {rel.source} -[{label}]-> {rel.target}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_mermaid(world: ChronologyWorld) -> str:
    lines = ["gantt", "  title Yuho Chronology", "  dateFormat YYYY-MM-DD"]
    emitted = False
    for timeline in sorted(world.timelines.values(), key=lambda item: item.name):
        lines.append(f"  section {_mermaid_text(timeline.name)}")
        for entity in sorted(world.entities.values(), key=lambda item: item.name):
            for appearance in _expanded_appearances(entity):
                if appearance.timeline != timeline.name:
                    continue
                start = appearance.range.start
                end = appearance.range.end
                if isinstance(start, date) and isinstance(end, date):
                    lines.append(
                        f"  {_mermaid_text(entity.name)} :{_mermaid_id(entity.name)}, {start.isoformat()}, {end.isoformat()}"
                    )
                    emitted = True
    if not emitted:
        lines.append("  section Entities")
        for entity in sorted(world.entities.values(), key=lambda item: item.name):
            date_value = entity.fields.get("date")
            if isinstance(date_value, date):
                lines.append(
                    f"  {_mermaid_text(entity.name)} :{_mermaid_id(entity.name)}, {date_value.isoformat()}, 1d"
                )
    return "\n".join(lines) + "\n"


def render_svg(world: ChronologyWorld) -> str:
    width = 980
    row_height = 70
    margin = 40
    entities = list(sorted(world.entities.values(), key=lambda item: item.name))
    height = max(180, margin * 2 + len(entities) * row_height)
    positions: dict[str, tuple[int, int]] = {}
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="40" y="30" font-family="system-ui" font-size="20" font-weight="700">Yuho Chronology</text>',
    ]
    for idx, entity in enumerate(entities):
        x = 80
        y = margin + idx * row_height + 35
        positions[entity.name] = (x + 120, y)
        fill = "#f7f7f5" if entity.type_name not in ("claim", "fact") else "#eef6ff"
        lines.append(
            f'<rect x="{x}" y="{y - 22}" width="240" height="44" rx="6" fill="{fill}" stroke="#444"/>'
        )
        lines.append(
            f'<text x="{x + 12}" y="{y + 4}" font-family="system-ui" font-size="13">{html.escape(entity.name)} ({html.escape(entity.type_name)})</text>'
        )
    for rel in world.relationships:
        if rel.source not in positions or rel.target not in positions:
            continue
        x1, y1 = positions[rel.source]
        x2, y2 = positions[rel.target]
        color = "#c1121f" if rel.label == "contradicts" else "#555"
        label = html.escape(rel.label or "rel")
        lines.append(
            f'<line x1="{x1 + 120}" y1="{y1}" x2="{x2 + 120}" y2="{y2}" stroke="{color}" stroke-width="2"/>'
        )
        lines.append(
            f'<text x="{max(x1, x2) + 250}" y="{(y1 + y2) // 2}" font-family="system-ui" font-size="12" fill="{color}">{label}</text>'
        )
    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_diff(left: ChronologyWorld, right: ChronologyWorld, target: str = "text") -> str:
    left_dict = world_to_dict(left)
    right_dict = world_to_dict(right)
    changes = _diff_dicts(left_dict, right_dict)
    if target == "text":
        return "\n".join(changes) + ("\n" if changes else "No semantic chronology changes.\n")
    if target == "html":
        body = "<br/>".join(html.escape(change) for change in changes) or "No semantic chronology changes."
        return f"<!doctype html><html><body><pre>{body}</pre></body></html>\n"
    if target == "svg":
        text = changes or ["No semantic chronology changes."]
        height = 80 + len(text) * 24
        lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="{height}">',
            '<rect width="100%" height="100%" fill="#ffffff"/>',
            '<text x="30" y="35" font-family="system-ui" font-size="20" font-weight="700">Chronology Diff</text>',
        ]
        for idx, change in enumerate(text):
            color = "#0b6bcb" if change.startswith("+") else "#a4161a" if change.startswith("-") else "#333"
            lines.append(
                f'<text x="30" y="{70 + idx * 24}" font-family="ui-monospace, monospace" font-size="14" fill="{color}">{html.escape(change)}</text>'
            )
        lines.append("</svg>")
        return "\n".join(lines) + "\n"
    raise ValueError(f"Unsupported chronology diff target: {target}")


def diagnostics_to_dict(diagnostics: list[Diagnostic]) -> list[dict[str, Any]]:
    return [
        {
            "severity": diagnostic.severity,
            "message": diagnostic.message,
            "line": diagnostic.line,
            "column": diagnostic.column,
        }
        for diagnostic in diagnostics
    ]


def _record_map(store: dict[str, NamedRecord]) -> dict[str, Any]:
    return {name: _record_to_dict(record) for name, record in sorted(store.items())}


def _record_to_dict(record: NamedRecord) -> dict[str, Any]:
    return {"fields": {name: _value(value) for name, value in sorted(record.fields.items())}}


def _source_to_dict(record: SourceRecord) -> dict[str, Any]:
    payload = _record_to_dict(record)
    payload["kind"] = record.kind
    return payload


def _entity_to_dict(record: EntityRecord) -> dict[str, Any]:
    payload = _record_to_dict(record)
    payload["type"] = record.type_name
    return payload


def _relationship_to_dict(rel: RelationshipRecord) -> dict[str, Any]:
    return {
        "source": rel.source,
        "label": rel.label,
        "target": rel.target,
        "temporal_scope": _value(rel.temporal_scope),
    }


def _scenario_to_dict(record: Any) -> dict[str, Any]:
    return {
        "fork_from": record.fork_from,
        "world": world_to_dict(record.world) if record.world else None,
    }


def _value(value: Any) -> Any:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, DurationValue):
        return {
            "years": value.years,
            "months": value.months,
            "days": value.days,
            "hours": value.hours,
            "minutes": value.minutes,
            "seconds": value.seconds,
        }
    if isinstance(value, TimeRange):
        return {"start": _value(value.start), "end": _value(value.end)}
    if isinstance(value, Appearance):
        return {"timeline": value.timeline, "range": _value(value.range)}
    if isinstance(value, list):
        return [_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _value(item) for key, item in sorted(value.items())}
    if value.__class__.__module__.startswith("yuho.ast"):
        return value.__class__.__name__
    return value


def _matches_narrative(value: Any, narrative: str) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value == narrative
    if isinstance(value, list):
        return narrative in value
    return False


def _diff_dicts(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    changes: list[str] = []
    for section in (
        "sources",
        "source_bundles",
        "locators",
        "rulesets",
        "deadline_rules",
        "issues",
        "issue_elements",
        "timelines",
        "entities",
        "relationship_types",
        "views",
        "constraints",
        "entity_schemas",
        "scenarios",
    ):
        left_keys = set(left.get(section, {}))
        right_keys = set(right.get(section, {}))
        for key in sorted(right_keys - left_keys):
            changes.append(f"+ {section}.{key}")
        for key in sorted(left_keys - right_keys):
            changes.append(f"- {section}.{key}")
        for key in sorted(left_keys & right_keys):
            if left[section][key] != right[section][key]:
                changes.append(f"~ {section}.{key}")
    left_rels = {json.dumps(rel, sort_keys=True) for rel in left.get("relationships", [])}
    right_rels = {json.dumps(rel, sort_keys=True) for rel in right.get("relationships", [])}
    for rel in sorted(right_rels - left_rels):
        changes.append(f"+ relationship {rel}")
    for rel in sorted(left_rels - right_rels):
        changes.append(f"- relationship {rel}")
    return changes


def _expanded_appearances(entity: EntityRecord, limit: int = 128) -> list[Appearance]:
    appearances = list(entity.appearances)
    recurrence = entity.fields.get("recurrence")
    if not isinstance(recurrence, DurationValue) or recurrence.days <= 0:
        return appearances
    skips = entity.fields.get("skip")
    skip_dates = {value for value in skips if isinstance(value, date)} if isinstance(skips, list) else set()
    expanded: list[Appearance] = []
    for appearance in appearances:
        start = appearance.range.start
        end = appearance.range.end
        if not isinstance(start, date) or not isinstance(end, date):
            expanded.append(appearance)
            continue
        current = start
        count = 0
        while current <= end and count < limit:
            if current not in skip_dates:
                expanded.append(Appearance(appearance.timeline, TimeRange(current, current)))
            current = date.fromordinal(current.toordinal() + recurrence.days)
            count += 1
    return expanded


def _mermaid_text(value: str) -> str:
    return value.replace(":", "-")


def _mermaid_id(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value)
