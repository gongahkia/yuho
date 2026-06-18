"""Chronology report helpers."""

from __future__ import annotations

import csv
import io
import json
from typing import Any, Optional

from yuho.chronology.model import ChronologyWorld, Diagnostic, EntityRecord, NamedRecord
from yuho.chronology.renderers import diagnostics_to_dict, render_diff, world_to_dict
from yuho.chronology.validation import validate_world


def render_sources_report(world: ChronologyWorld) -> str:
    lines = ["Sources"]
    references = _source_references(world)
    for source in sorted(world.sources.values(), key=lambda item: item.name):
        detail = _compact_fields(source, ("citation", "title", "url", "path", "canonical_id"))
        lines.append(f"- {source.name} [{source.kind}] {detail}".rstrip())
        if references.get(source.name):
            lines.append(f"  referenced_by: {', '.join(sorted(references[source.name]))}")
    for bundle in sorted(world.source_bundles.values(), key=lambda item: item.name):
        members = ", ".join(str(item) for item in _as_list(bundle.fields.get("sources")))
        lines.append(f"- bundle {bundle.name}: {members}")
        if references.get(bundle.name):
            lines.append(f"  referenced_by: {', '.join(sorted(references[bundle.name]))}")
    for locator in sorted(world.locators.values(), key=lambda item: item.name):
        detail = _compact_fields(locator, ("source_ref", "bates", "page", "paragraph", "line", "line_start", "line_end", "docket_entry"))
        lines.append(f"- locator {locator.name}: {detail}".rstrip())
    return "\n".join(lines) + "\n"


def render_deadlines_report(world: ChronologyWorld) -> str:
    lines = ["Deadlines"]
    for ruleset in sorted(world.rulesets.values(), key=lambda item: item.name):
        detail = _compact_fields(ruleset, ("jurisdiction", "procedure", "source_ref", "effective_start", "effective_end"))
        lines.append(f"- ruleset {ruleset.name}: {detail}".rstrip())
    for rule in sorted(world.deadline_rules.values(), key=lambda item: item.name):
        detail = _compact_fields(rule, ("ruleset", "rule", "trigger", "offset", "direction", "counting", "source_ref", "jurisdiction"))
        lines.append(f"- rule {rule.name}: {detail}".rstrip())
    for entity in sorted(world.entities.values(), key=lambda item: item.name):
        if entity.type_name == "deadline":
            detail = _compact_fields(entity, ("rule", "rule_ref", "trigger", "due", "jurisdiction", "source_ref"))
            lines.append(f"- deadline {entity.name}: {detail}".rstrip())
    return "\n".join(lines) + "\n"


def render_issues_report(world: ChronologyWorld) -> str:
    lines = ["Issues"]
    for issue in sorted(world.issues.values(), key=lambda item: item.name):
        detail = _compact_fields(issue, ("title", "question", "summary", "status"))
        lines.append(f"- {issue.name}: {detail}".rstrip())
        linked = [
            element
            for element in world.issue_elements.values()
            if element.fields.get("issue_ref") == issue.name
        ]
        for element in sorted(linked, key=lambda item: item.name):
            lines.append(f"  - element {element.name}: entity={element.fields.get('entity_ref')}")
    return "\n".join(lines) + "\n"


def render_contradictions_report(world: ChronologyWorld) -> str:
    lines = ["Contradictions"]
    for rel in world.relationships:
        if rel.label != "contradicts":
            continue
        source = world.entities.get(rel.source)
        target = world.entities.get(rel.target)
        shared = sorted(_timeline_names(source) & _timeline_names(target)) if source and target else []
        lines.append(f"- {rel.source} contradicts {rel.target}" + (f" on {', '.join(shared)}" if shared else ""))
        for side, entity_name in (("source", rel.source), ("target", rel.target)):
            evidence = _supporting_evidence(world, entity_name)
            if evidence:
                lines.append(f"  {side}_evidence: {', '.join(evidence)}")
    if len(lines) == 1:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def render_exhibits_report(world: ChronologyWorld, output_format: str = "text") -> str:
    exhibits = [
        entity
        for entity in sorted(world.entities.values(), key=lambda item: str(item.fields.get("number", item.name)))
        if entity.type_name == "exhibit"
    ]
    rows = [_exhibit_row(entity, appearance_idx, appearance) for entity in exhibits for appearance_idx, appearance in _entity_appearances(entity)]
    if output_format == "json":
        return json.dumps(rows, indent=2, sort_keys=True) + "\n"
    if output_format == "csv":
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["number", "entity", "description", "timeline", "start", "end", "source_ref", "locator_ref"])
        writer.writeheader()
        writer.writerows(rows)
        return buf.getvalue()
    lines = ["Exhibits"]
    if not rows:
        lines.append("- none")
    for row in rows:
        suffix = f" timeline={row['timeline']} start={row['start']} end={row['end']}" if row["timeline"] else ""
        lines.append(f"- {row['number']}: {row['description']} ({row['entity']}){suffix}".rstrip())
    return "\n".join(lines) + "\n"


def render_review_report(world: ChronologyWorld, diagnostics: list[Diagnostic]) -> str:
    payload: dict[str, Any] = {
        "summary": {
            "sources": len(world.sources),
            "source_bundles": len(world.source_bundles),
            "locators": len(world.locators),
            "rulesets": len(world.rulesets),
            "deadline_rules": len(world.deadline_rules),
            "timelines": len(world.timelines),
            "entities": len(world.entities),
            "relationships": len(world.relationships),
            "issues": len(world.issues),
            "scenarios": len(world.scenarios),
        },
        "diagnostics": diagnostics_to_dict(diagnostics),
        "diagnostics_by_severity": {
            "error": sum(1 for item in diagnostics if item.severity == "error"),
            "warning": sum(1 for item in diagnostics if item.severity == "warning"),
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def render_scenario_report(world: ChronologyWorld, scenario_name: Optional[str] = None) -> str:
    scenarios = [world.scenarios[scenario_name]] if scenario_name else [world.scenarios[name] for name in sorted(world.scenarios)]
    lines = ["Scenarios"]
    if not scenarios:
        lines.append("- none")
    for scenario in scenarios:
        if not scenario.world:
            lines.append(f"- {scenario.name}: unavailable")
            continue
        diagnostics = validate_world(scenario.world)
        errors = sum(1 for item in diagnostics if item.severity == "error")
        warnings = sum(1 for item in diagnostics if item.severity == "warning")
        lines.append(f"- {scenario.name}: fork_from={scenario.fork_from or ''} errors={errors} warnings={warnings}".rstrip())
        diff = render_diff(_base_world(world), scenario.world, target="text").strip()
        for line in diff.splitlines():
            lines.append(f"  {line}")
    return "\n".join(lines) + "\n"


def render_scenario_diff(world: ChronologyWorld, scenario_name: str, target: str) -> str:
    scenario = world.scenarios.get(scenario_name)
    if not scenario or not scenario.world:
        raise ValueError(f"Unknown scenario: {scenario_name}")
    return render_diff(_base_world(world), scenario.world, target=target)


def _base_world(world: ChronologyWorld) -> ChronologyWorld:
    return ChronologyWorld(
        sources=dict(world.sources),
        source_bundles=dict(world.source_bundles),
        locators=dict(world.locators),
        rulesets=dict(world.rulesets),
        deadline_rules=dict(world.deadline_rules),
        issues=dict(world.issues),
        issue_elements=dict(world.issue_elements),
        timelines=dict(world.timelines),
        entities=dict(world.entities),
        relationship_types=dict(world.relationship_types),
        relationships=list(world.relationships),
        scenarios={},
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


def _source_references(world: ChronologyWorld) -> dict[str, set[str]]:
    references: dict[str, set[str]] = {}
    for record in _all_records(world):
        for source_ref in _as_list(record.fields.get("source_ref")):
            if isinstance(source_ref, str):
                references.setdefault(source_ref, set()).add(record.name)
    return references


def _supporting_evidence(world: ChronologyWorld, entity_name: str) -> list[str]:
    values = []
    for rel in world.relationships:
        if rel.label == "cites" and rel.target == entity_name:
            evidence = world.entities.get(rel.source)
            if evidence:
                citation = evidence.fields.get("citation")
                values.append(f"{evidence.name}" + (f" ({citation})" if citation else ""))
    return sorted(values)


def _compact_fields(record: NamedRecord, names: tuple[str, ...]) -> str:
    parts = [f"{name}={record.fields[name]}" for name in names if record.fields.get(name) is not None]
    return " ".join(parts)


def _entity_appearances(entity: EntityRecord):
    if not entity.appearances:
        yield 0, None
        return
    for idx, appearance in enumerate(entity.appearances):
        yield idx, appearance


def _exhibit_row(entity: EntityRecord, appearance_idx: int, appearance: Any) -> dict[str, Any]:
    return {
        "number": str(entity.fields.get("number", entity.name)),
        "entity": entity.name,
        "description": str(entity.fields.get("description", "")),
        "timeline": appearance.timeline if appearance else "",
        "start": str(appearance.range.start) if appearance else "",
        "end": str(appearance.range.end) if appearance else "",
        "source_ref": str(entity.fields.get("source_ref", "")),
        "locator_ref": str(entity.fields.get("locator_ref", "")),
    }


def _timeline_names(entity: Optional[EntityRecord]) -> set[str]:
    if not entity:
        return set()
    return {appearance.timeline for appearance in entity.appearances}


def _all_records(world: ChronologyWorld):
    for store in (
        world.sources,
        world.source_bundles,
        world.locators,
        world.rulesets,
        world.deadline_rules,
        world.issues,
        world.issue_elements,
        world.timelines,
        world.entities,
        world.relationship_types,
        world.views,
        world.constraints,
    ):
        yield from store.values()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
