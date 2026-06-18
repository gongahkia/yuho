"""Chronology validation rules."""

from __future__ import annotations

import re
from datetime import date
from typing import Any, Iterable, Optional
from urllib.parse import urlparse

from yuho.chronology.model import (
    Appearance,
    BUILTIN_ENTITY_TYPES,
    BUILTIN_RELATIONSHIPS,
    ChronologyWorld,
    Diagnostic,
    DurationValue,
    EntityRecord,
    EntitySchemaRecord,
    NamedRecord,
    RelationshipRecord,
    TimeRange,
)


def validate_world(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = list(world.duplicates)
    diagnostics.extend(_validate_entity_schemas(world))
    diagnostics.extend(_validate_duplicate_ids(world))
    diagnostics.extend(_validate_sources(world))
    diagnostics.extend(_validate_locators(world))
    diagnostics.extend(_validate_timelines(world))
    diagnostics.extend(_validate_rulesets(world))
    diagnostics.extend(_validate_deadlines(world))
    diagnostics.extend(_validate_entities(world))
    diagnostics.extend(_validate_issues(world))
    diagnostics.extend(_validate_relationship_types(world))
    diagnostics.extend(_validate_relationships(world))
    diagnostics.extend(_validate_statute_refs(world))
    diagnostics.extend(_validate_constraints(world))
    for scenario in world.scenarios.values():
        if scenario.fork_from and scenario.fork_from not in world.timelines:
            diagnostics.append(_diag("error", f"Scenario '{scenario.name}' has unknown fork timeline '{scenario.fork_from}'", scenario))
        if scenario.world:
            for item in validate_world(scenario.world):
                diagnostics.append(
                    Diagnostic(
                        severity=item.severity,
                        message=f"Scenario '{scenario.name}': {item.message}",
                        line=item.line or scenario.line,
                        column=item.column or scenario.column,
                    )
                )
    return diagnostics


def _validate_entity_schemas(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for schema in world.entity_schemas.values():
        if schema.parent and schema.parent not in world.entity_schemas and schema.parent not in BUILTIN_ENTITY_TYPES:
            diagnostics.append(_schema_diag("error", f"Unknown parent entity schema '{schema.parent}'", schema))
        seen: set[str] = set()
        current: Optional[str] = schema.name
        while current:
            if current in seen:
                diagnostics.append(_schema_diag("error", f"Entity schema '{schema.name}' has cyclic inheritance", schema))
                break
            seen.add(current)
            parent = world.entity_schemas.get(current)
            current = parent.parent if parent else None
    return diagnostics


def _validate_duplicate_ids(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen_canonical: dict[str, NamedRecord] = {}
    seen_citation: dict[str, NamedRecord] = {}
    for record in _all_named_records(world):
        canonical_id = record.fields.get("canonical_id")
        if isinstance(canonical_id, str):
            key = _norm_identity(canonical_id)
            if key in seen_canonical:
                diagnostics.append(_diag("error", f"Duplicate canonical_id '{canonical_id}'", record))
            seen_canonical[key] = record
        citation = record.fields.get("citation")
        if isinstance(citation, str):
            key = _norm_identity(citation)
            if key in seen_citation:
                diagnostics.append(_diag("warning", f"Duplicate citation '{citation}'", record))
            seen_citation[key] = record
    return diagnostics


def _validate_sources(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for source in world.sources.values():
        if not any(source.fields.get(name) for name in ("citation", "title", "url", "path")):
            diagnostics.append(_diag("warning", f"Source '{source.name}' lacks citation/title/url/path", source))
        url = source.fields.get("url")
        if isinstance(url, str) and not _valid_url(url):
            diagnostics.append(_diag("warning", f"Source '{source.name}' has invalid url '{url}'", source))
    for bundle in world.source_bundles.values():
        seen: set[str] = set()
        for name in _as_list(bundle.fields.get("sources")):
            if not isinstance(name, str):
                continue
            if name in seen:
                diagnostics.append(_diag("warning", f"Duplicate source '{name}' in bundle '{bundle.name}'", bundle))
            seen.add(name)
            if name not in world.sources:
                diagnostics.append(_diag("error", f"Unknown source '{name}' in bundle '{bundle.name}'", bundle))
    return diagnostics


def _validate_locators(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    concrete = {
        "bates",
        "page",
        "paragraph",
        "line",
        "line_start",
        "line_end",
        "transcript_page",
        "transcript_line",
        "docket_entry",
        "url_fragment",
    }
    for locator in world.locators.values():
        source_ref = locator.fields.get("source_ref")
        if source_ref is None:
            diagnostics.append(_diag("error", f"Locator '{locator.name}' missing source_ref", locator))
        else:
            diagnostics.extend(_validate_source_refs(world, locator, source_ref))
        if not any(locator.fields.get(name) is not None for name in concrete):
            diagnostics.append(_diag("warning", f"Locator '{locator.name}' has no concrete locator field", locator))
    return diagnostics


def _validate_timelines(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    valid_kinds = {"linear", "branch", "parallel", "loop"}
    for timeline in world.timelines.values():
        kind = timeline.fields.get("kind")
        if kind and kind not in valid_kinds:
            diagnostics.append(_diag("error", f"Timeline '{timeline.name}' has invalid kind '{kind}'", timeline))
        start = timeline.fields.get("start")
        end = timeline.fields.get("end")
        if _comparable(start, end) and start > end:
            diagnostics.append(_diag("error", f"Timeline '{timeline.name}' start is after end", timeline))
        parent = timeline.fields.get("parent")
        if isinstance(parent, str):
            if parent not in world.timelines:
                diagnostics.append(_diag("error", f"Timeline '{timeline.name}' has unknown parent '{parent}'", timeline))
            else:
                diagnostics.extend(_validate_timeline_context(world, timeline, world.timelines[parent], "parent"))
        elif kind == "branch":
            diagnostics.append(_diag("warning", f"Branch timeline '{timeline.name}' has no parent", timeline))
        for field_name in ("fork_from", "merge_into"):
            ref_name = _timeline_ref_name(timeline.fields.get(field_name))
            if ref_name:
                if ref_name not in world.timelines:
                    diagnostics.append(_diag("error", f"Timeline '{timeline.name}' has unknown {field_name} '{ref_name}'", timeline))
                else:
                    diagnostics.extend(_validate_timeline_context(world, timeline, world.timelines[ref_name], field_name))
        for field_name in ("fork_at", "merge_at"):
            point = timeline.fields.get(field_name)
            if point is not None and not isinstance(point, (int, float, date)):
                diagnostics.append(_diag("error", f"Timeline '{timeline.name}' {field_name} must be a time point", timeline))
        loop_count = timeline.fields.get("loop_count")
        if loop_count is not None and (not isinstance(loop_count, int) or loop_count <= 0):
            diagnostics.append(_diag("error", f"Timeline '{timeline.name}' loop_count must be positive", timeline))
        if kind == "loop" and loop_count is None:
            diagnostics.append(_diag("warning", f"Loop timeline '{timeline.name}' has no loop_count", timeline))
    return diagnostics


def _validate_timeline_context(
    world: ChronologyWorld,
    child: NamedRecord,
    referenced: NamedRecord,
    relation: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for field_name in ("jurisdiction", "procedure", "court"):
        child_value = child.fields.get(field_name)
        ref_value = referenced.fields.get(field_name)
        if child_value and ref_value and child_value != ref_value:
            diagnostics.append(
                _diag(
                    "warning",
                    f"Timeline '{child.name}' {field_name} differs from {relation} timeline '{referenced.name}'",
                    child,
                )
            )
    return diagnostics


def _validate_rulesets(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for ruleset in world.rulesets.values():
        source_ref = ruleset.fields.get("source_ref")
        if source_ref is None:
            diagnostics.append(_diag("error", f"Ruleset '{ruleset.name}' missing source_ref", ruleset))
        else:
            diagnostics.extend(_validate_source_refs(world, ruleset, source_ref))
        for field_name in ("jurisdiction", "procedure"):
            if not ruleset.fields.get(field_name):
                diagnostics.append(_diag("warning", f"Ruleset '{ruleset.name}' missing {field_name}", ruleset))
    return diagnostics


def _validate_deadlines(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for rule in world.deadline_rules.values():
        for field_name in ("ruleset", "rule"):
            if not rule.fields.get(field_name):
                diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' missing {field_name}", rule))
        ruleset = rule.fields.get("ruleset")
        if isinstance(ruleset, str) and ruleset not in world.rulesets:
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' has unknown ruleset '{ruleset}'", rule))
        trigger = rule.fields.get("trigger", rule.fields.get("trigger_event"))
        if trigger is None:
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' missing trigger", rule))
        offset = rule.fields.get("offset", rule.fields.get("duration"))
        if offset is None:
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' missing offset", rule))
        elif not _duration_positive(offset):
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' offset must be positive", rule))
        source_ref = rule.fields.get("source_ref")
        if source_ref is None:
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' missing source_ref", rule))
        else:
            diagnostics.extend(_validate_source_refs(world, rule, source_ref))
        direction = rule.fields.get("direction")
        if direction is not None and direction not in {"after", "before"}:
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' has invalid direction '{direction}'", rule))
        counting = rule.fields.get("counting")
        if counting is not None and counting not in {"calendar", "calendar_days", "court", "court_days", "business", "business_days"}:
            diagnostics.append(_diag("error", f"Deadline rule '{rule.name}' has invalid counting '{counting}'", rule))

    for entity in world.entities.values():
        if entity.type_name != "deadline":
            continue
        rule_ref = entity.fields.get("rule_ref", entity.fields.get("rule"))
        rule_record = None
        if isinstance(rule_ref, str):
            if rule_ref in world.deadline_rules:
                rule_record = world.deadline_rules[rule_ref]
            elif rule_ref in world.rulesets:
                rule_record = world.rulesets[rule_ref]
            else:
                diagnostics.append(_diag("error", f"Unknown rule_ref '{rule_ref}'", entity))
        due = entity.fields.get("due")
        trigger = entity.fields.get("trigger")
        if _comparable(trigger, due) and trigger > due:
            diagnostics.append(_diag("error", f"Deadline '{entity.name}' is due before its trigger", entity))
        if rule_record:
            rule_jurisdiction = rule_record.fields.get("jurisdiction")
            entity_jurisdiction = entity.fields.get("jurisdiction")
            if rule_jurisdiction and entity_jurisdiction and rule_jurisdiction != entity_jurisdiction:
                diagnostics.append(_diag("warning", f"Deadline '{entity.name}' jurisdiction differs from rule_ref '{rule_ref}'", entity))
        for appearance in entity.appearances:
            timeline = world.timelines.get(appearance.timeline)
            if not timeline:
                continue
            timeline_jurisdiction = timeline.fields.get("jurisdiction")
            entity_jurisdiction = entity.fields.get("jurisdiction")
            if timeline_jurisdiction and entity_jurisdiction and timeline_jurisdiction != entity_jurisdiction:
                diagnostics.append(_diag("warning", f"Deadline '{entity.name}' jurisdiction differs from timeline '{timeline.name}'", entity))
    return diagnostics


def _validate_entities(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    cited_targets = {rel.target for rel in world.relationships if rel.label == "cites"}
    for entity in world.entities.values():
        schema = _entity_schema(world, entity.type_name)
        if schema is None:
            diagnostics.append(_diag("warning", f"Unknown entity type '{entity.type_name}'", entity))
        else:
            for field_name in sorted(schema["required"]):
                if entity.fields.get(field_name) is None:
                    diagnostics.append(
                        _diag(
                            "error",
                            f"Entity '{entity.name}' of type '{entity.type_name}' missing {field_name}",
                            entity,
                        )
                    )
            for field_name, expected in schema["types"].items():
                if field_name in entity.fields:
                    diagnostics.extend(_validate_field_type(world, entity, field_name, expected, entity.fields[field_name]))
        if entity.type_name == "evidence" and not entity.fields.get("source") and not entity.fields.get("source_ref"):
            diagnostics.append(_diag("error", f"Evidence '{entity.name}' missing source or source_ref", entity))
        diagnostics.extend(_validate_ref_fields(world, entity))
        diagnostics.extend(_validate_recurrence(entity))
        diagnostics.extend(_validate_state_changes(entity))
        for appearance in entity.appearances:
            diagnostics.extend(_validate_appearance(world, entity, appearance))
        if entity.type_name in {"claim", "fact"} and not entity.fields.get("source_ref") and entity.name not in cited_targets:
            diagnostics.append(_diag("warning", f"{entity.type_name.capitalize()} '{entity.name}' has no source backing", entity))
        if entity.fields.get("continuous") is True:
            diagnostics.extend(_validate_continuous_coverage(entity))
    diagnostics.extend(_validate_witness_depositions(world))
    return diagnostics


def _validate_recurrence(entity: EntityRecord) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    recurrence = entity.fields.get("recurrence")
    if recurrence is not None and not _duration_positive(recurrence):
        diagnostics.append(_diag("error", f"Entity '{entity.name}' recurrence must be a positive duration", entity))
    for skip in _as_list(entity.fields.get("skip")):
        if not isinstance(skip, date):
            diagnostics.append(_diag("error", f"Entity '{entity.name}' skip values must be dates", entity))
    return diagnostics


def _validate_state_changes(entity: EntityRecord) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    state = entity.fields.get("state")
    if state is None:
        return diagnostics
    changes = state if isinstance(state, list) else [state]
    for change in changes:
        if not isinstance(change, dict):
            diagnostics.append(_diag("error", f"Entity '{entity.name}' state entries must be objects", entity))
            continue
        at = change.get("at")
        if at is None:
            diagnostics.append(_diag("error", f"Entity '{entity.name}' state entry missing at", entity))
        elif not isinstance(at, (int, float, date)):
            diagnostics.append(_diag("error", f"Entity '{entity.name}' state at must be a time point", entity))
    return diagnostics


def _validate_continuous_coverage(entity: EntityRecord) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    by_timeline: dict[str, list[TimeRange]] = {}
    for appearance in entity.appearances:
        by_timeline.setdefault(appearance.timeline, []).append(appearance.range)
    for timeline, ranges in by_timeline.items():
        sortable = [rng for rng in ranges if _comparable(rng.start, rng.end)]
        sortable.sort(key=lambda rng: rng.start)
        for previous, current in zip(sortable, sortable[1:]):
            if _comparable(previous.end, current.start) and previous.end < current.start:
                diagnostics.append(_diag("warning", f"Entity '{entity.name}' has continuous coverage gap on timeline '{timeline}'", entity))
                break
    return diagnostics


def _validate_witness_depositions(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    depositions = [entity for entity in world.entities.values() if entity.type_name == "deposition"]
    for witness in (entity for entity in world.entities.values() if entity.type_name == "witness"):
        aliases = {witness.name}
        if isinstance(witness.fields.get("name"), str):
            aliases.add(witness.fields["name"])
        if not any(dep.fields.get("deponent") in aliases for dep in depositions):
            diagnostics.append(_diag("warning", f"Witness '{witness.name}' has no matching deposition", witness))
    return diagnostics


def _validate_issues(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for issue in world.issues.values():
        if not any(issue.fields.get(name) for name in ("title", "question", "summary")):
            diagnostics.append(_diag("warning", f"Issue '{issue.name}' has no title/question/summary", issue))
    for element in world.issue_elements.values():
        issue_ref = element.fields.get("issue_ref")
        if isinstance(issue_ref, str) and issue_ref not in world.issues:
            diagnostics.append(_diag("error", f"Unknown issue_ref '{issue_ref}'", element))
        entity_ref = element.fields.get("entity_ref")
        if isinstance(entity_ref, str) and entity_ref not in world.entities:
            diagnostics.append(_diag("error", f"Unknown entity_ref '{entity_ref}'", element))
        diagnostics.extend(_validate_ref_fields(world, element))
    return diagnostics


def _validate_relationship_types(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for reltype in world.relationship_types.values():
        for field_name in ("source", "sources", "target", "targets"):
            for type_name in _type_set(reltype.fields.get(field_name)):
                if not _known_entity_type(world, type_name):
                    diagnostics.append(_diag("error", f"Relationship type '{reltype.name}' references unknown entity type '{type_name}'", reltype))
        for min_name, max_name in (("min_inbound", "max_inbound"), ("min_outbound", "max_outbound")):
            minimum = reltype.fields.get(min_name)
            maximum = reltype.fields.get(max_name)
            if minimum is not None and (not isinstance(minimum, int) or minimum < 0):
                diagnostics.append(_diag("error", f"Relationship type '{reltype.name}' {min_name} must be non-negative", reltype))
            if maximum is not None and (not isinstance(maximum, int) or maximum < 0):
                diagnostics.append(_diag("error", f"Relationship type '{reltype.name}' {max_name} must be non-negative", reltype))
            if isinstance(minimum, int) and isinstance(maximum, int) and minimum > maximum:
                diagnostics.append(_diag("error", f"Relationship type '{reltype.name}' {min_name} exceeds {max_name}", reltype))
        temporal = reltype.fields.get("temporal")
        if temporal is not None and temporal not in {"source_before_target", "before", "source_after_target", "after", "none"}:
            diagnostics.append(_diag("error", f"Relationship type '{reltype.name}' has invalid temporal '{temporal}'", reltype))
    return diagnostics


def _validate_relationships(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    seen: set[tuple[str, Optional[str], str]] = set()
    for rel in world.relationships:
        if rel.temporal_scope and _comparable(rel.temporal_scope.start, rel.temporal_scope.end) and rel.temporal_scope.start > rel.temporal_scope.end:
            diagnostics.append(_rel_diag("error", f"Relationship '{rel.label or 'rel'}' temporal scope starts after it ends", rel))
        if rel.source not in world.entities:
            diagnostics.append(_rel_diag("error", f"Unknown relationship source '{rel.source}'", rel))
            continue
        if rel.target not in world.entities:
            diagnostics.append(_rel_diag("error", f"Unknown relationship target '{rel.target}'", rel))
            continue
        key = (rel.source, rel.label, rel.target)
        if key in seen:
            diagnostics.append(_rel_diag("warning", "Duplicate relationship", rel))
        seen.add(key)
        if rel.label == "contradicts" and _shared_timeline(world.entities[rel.source], world.entities[rel.target]):
            diagnostics.append(_rel_diag("warning", f"Contradiction: {rel.source} contradicts {rel.target}", rel))
        if rel.label:
            diagnostics.extend(_validate_relationship_instance(world, rel))
    diagnostics.extend(_validate_relationship_cardinality(world))
    return diagnostics


def _validate_relationship_instance(world: ChronologyWorld, rel: RelationshipRecord) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    source = world.entities[rel.source]
    target = world.entities[rel.target]
    spec = _relationship_spec(world, rel.label)
    if spec is None:
        diagnostics.append(_rel_diag("warning", f"Unknown relationship type '{rel.label}'", rel))
        return diagnostics
    source_types = _relationship_types_from_spec(spec, "source")
    target_types = _relationship_types_from_spec(spec, "target")
    if source_types and not any(_entity_is_type(world, source, type_name) for type_name in source_types):
        diagnostics.append(_rel_diag("warning", f"Relationship '{rel.label}' source should be {sorted(source_types)}, got {source.type_name}", rel))
    if target_types and not any(_entity_is_type(world, target, type_name) for type_name in target_types):
        diagnostics.append(_rel_diag("warning", f"Relationship '{rel.label}' target should be {sorted(target_types)}, got {target.type_name}", rel))
    temporal = spec.get("temporal")
    if temporal in {"before", "source_before_target"}:
        diagnostics.extend(_validate_temporal_relationship(rel, source, target, "source_before_target"))
    elif temporal in {"after", "source_after_target"}:
        diagnostics.extend(_validate_temporal_relationship(rel, source, target, "source_after_target"))
    return diagnostics


def _validate_relationship_cardinality(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for label, reltype in world.relationship_types.items():
        spec = reltype.fields
        source_types = _relationship_types_from_spec(spec, "source")
        target_types = _relationship_types_from_spec(spec, "target")
        min_inbound = _cardinality_min(spec, "min_inbound", default=1 if spec.get("required") is True else None)
        max_inbound = spec.get("max_inbound")
        min_outbound = _cardinality_min(spec, "min_outbound")
        max_outbound = spec.get("max_outbound")
        if min_inbound is not None or max_inbound is not None:
            for entity in world.entities.values():
                if target_types and not any(_entity_is_type(world, entity, type_name) for type_name in target_types):
                    continue
                count = sum(1 for rel in world.relationships if rel.label == label and rel.target == entity.name)
                diagnostics.extend(_cardinality_diagnostics(reltype, entity, label, count, min_inbound, max_inbound, "inbound"))
        if min_outbound is not None or max_outbound is not None:
            for entity in world.entities.values():
                if source_types and not any(_entity_is_type(world, entity, type_name) for type_name in source_types):
                    continue
                count = sum(1 for rel in world.relationships if rel.label == label and rel.source == entity.name)
                diagnostics.extend(_cardinality_diagnostics(reltype, entity, label, count, min_outbound, max_outbound, "outbound"))
    return diagnostics


def _cardinality_diagnostics(
    reltype: NamedRecord,
    entity: EntityRecord,
    label: str,
    count: int,
    minimum: Any,
    maximum: Any,
    direction: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if isinstance(minimum, int) and count < minimum:
        diagnostics.append(_diag("warning", f"Entity '{entity.name}' has {count} {direction} '{label}' relationships; expected at least {minimum}", reltype))
    if isinstance(maximum, int) and count > maximum:
        diagnostics.append(_diag("warning", f"Entity '{entity.name}' has {count} {direction} '{label}' relationships; expected at most {maximum}", reltype))
    return diagnostics


def _validate_temporal_relationship(
    rel: RelationshipRecord,
    source: EntityRecord,
    target: EntityRecord,
    temporal: str,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    source_range = _primary_range(source)
    target_range = _primary_range(target)
    if source_range is None or target_range is None:
        return diagnostics
    if temporal == "source_before_target" and _comparable(source_range.end, target_range.start) and source_range.end > target_range.start:
        diagnostics.append(_rel_diag("warning", f"Relationship '{rel.label}' violates temporal order", rel))
    if temporal == "source_after_target" and _comparable(source_range.start, target_range.end) and source_range.start < target_range.end:
        diagnostics.append(_rel_diag("warning", f"Relationship '{rel.label}' violates temporal order", rel))
    return diagnostics


def _validate_statute_refs(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    checks = {
        "statute_ref": world.statute_refs,
        "section_ref": world.section_refs,
        "element_ref": world.element_refs,
        "exception_ref": world.exception_refs,
        "caselaw_ref": world.caselaw_refs,
    }
    for record in _all_named_records(world):
        for field_name, valid_refs in checks.items():
            if field_name not in record.fields:
                continue
            for ref in _as_list(record.fields[field_name]):
                if isinstance(ref, str) and ref not in valid_refs:
                    diagnostics.append(_diag("error", f"Unknown {field_name} '{ref}'", record))
    return diagnostics


def _validate_constraints(world: ChronologyWorld) -> list[Diagnostic]:
    if not world.constraints:
        return []
    from yuho.chronology.constraints import validate_constraints

    return validate_constraints(world)


def _validate_ref_fields(world: ChronologyWorld, record: NamedRecord) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    diagnostics.extend(_validate_source_refs(world, record, record.fields.get("source_ref")))
    for ref in _as_list(record.fields.get("locator_ref")):
        if isinstance(ref, str) and ref not in world.locators:
            diagnostics.append(_diag("error", f"Unknown locator_ref '{ref}'", record))
    return diagnostics


def _validate_source_refs(world: ChronologyWorld, record: NamedRecord, value: Any) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for ref in _as_list(value):
        if isinstance(ref, str) and ref not in world.sources and ref not in world.source_bundles:
            diagnostics.append(_diag("error", f"Unknown source_ref '{ref}'", record))
    return diagnostics


def _validate_appearance(
    world: ChronologyWorld,
    entity: EntityRecord,
    appearance: Appearance,
) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    if appearance.timeline not in world.timelines:
        diagnostics.append(_diag("error", f"Unknown timeline '{appearance.timeline}'", entity))
        return diagnostics
    timeline = world.timelines[appearance.timeline]
    start = timeline.fields.get("start")
    end = timeline.fields.get("end")
    app_start = appearance.range.start
    app_end = appearance.range.end
    if _comparable(app_start, app_end) and app_start > app_end:
        diagnostics.append(_diag("error", f"Entity '{entity.name}' appearance starts after it ends", entity))
    if _comparable(start, app_start) and app_start < start:
        diagnostics.append(_diag("error", f"Entity '{entity.name}' appears before timeline start", entity))
    if _comparable(end, app_end) and app_end > end:
        diagnostics.append(_diag("error", f"Entity '{entity.name}' appears after timeline end", entity))
    return diagnostics


def _entity_schema(world: ChronologyWorld, type_name: str) -> Optional[dict[str, Any]]:
    required: set[str] = set()
    optional: set[str] = set()
    types: dict[str, Any] = {}
    found = False
    builtin = BUILTIN_ENTITY_TYPES.get(type_name)
    if builtin:
        required.update(builtin["required"])
        optional.update(builtin["optional"])
        found = True
    chain = _schema_chain(world, type_name)
    if chain:
        found = True
    for schema in chain:
        for name, expected in schema.fields.items():
            types[name] = expected
            if name in schema.optional:
                optional.add(name)
                required.discard(name)
            elif name not in optional:
                required.add(name)
    return {"required": required, "optional": optional, "types": types} if found else None


def _schema_chain(world: ChronologyWorld, type_name: str) -> list[EntitySchemaRecord]:
    chain: list[EntitySchemaRecord] = []
    seen: set[str] = set()
    current = type_name
    while current in world.entity_schemas and current not in seen:
        seen.add(current)
        schema = world.entity_schemas[current]
        chain.insert(0, schema)
        current = schema.parent or ""
    return chain


def _validate_field_type(
    world: ChronologyWorld,
    entity: EntityRecord,
    field_name: str,
    expected: str,
    value: Any,
) -> list[Diagnostic]:
    if _value_matches_type(world, value, expected):
        return []
    return [_diag("warning", f"Entity '{entity.name}' field '{field_name}' expected {expected}", entity)]


def _value_matches_type(world: ChronologyWorld, value: Any, expected: str) -> bool:
    if expected in ("string", "str"):
        return isinstance(value, str)
    if expected == "int":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "float":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "bool":
        return isinstance(value, bool)
    if expected == "date":
        return isinstance(value, date)
    if expected == "duration":
        return isinstance(value, DurationValue)
    if expected == "source":
        return isinstance(value, str) and (value in world.sources or value in world.source_bundles)
    if expected == "timeline":
        return isinstance(value, str) and value in world.timelines
    if expected == "entity":
        return isinstance(value, str) and value in world.entities
    if expected.startswith("[") and expected.endswith("]"):
        inner = expected[1:-1]
        return isinstance(value, list) and all(_value_matches_type(world, item, inner) for item in value)
    if expected in world.entity_schemas or expected in BUILTIN_ENTITY_TYPES:
        return isinstance(value, str) and value in world.entities and _entity_is_type(world, world.entities[value], expected)
    return True


def _relationship_spec(world: ChronologyWorld, label: str) -> Optional[dict[str, Any]]:
    if label in BUILTIN_RELATIONSHIPS:
        return BUILTIN_RELATIONSHIPS[label]
    custom = world.relationship_types.get(label)
    if custom:
        return custom.fields
    return None


def _relationship_types_from_spec(spec: dict[str, Any], side: str) -> set[str]:
    values = _type_set(spec.get(side))
    values.update(_type_set(spec.get(f"{side}s")))
    return values


def _type_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {item.strip() for item in value.split("|") if item.strip()}
    if isinstance(value, set):
        return {item for item in value if isinstance(item, str)}
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_type_set(item))
        return result
    if isinstance(value, tuple):
        result: set[str] = set()
        for item in value:
            result.update(_type_set(item))
        return result
    return set()


def _known_entity_type(world: ChronologyWorld, type_name: str) -> bool:
    return type_name in BUILTIN_ENTITY_TYPES or type_name in world.entity_schemas


def _entity_is_type(world: ChronologyWorld, entity: EntityRecord, expected: str) -> bool:
    if expected == "entity":
        return True
    if entity.type_name == expected:
        return True
    current = entity.type_name
    seen: set[str] = set()
    while current in world.entity_schemas and current not in seen:
        seen.add(current)
        parent = world.entity_schemas[current].parent
        if parent == expected:
            return True
        current = parent or ""
    return False


def _primary_range(entity: EntityRecord) -> Optional[TimeRange]:
    if entity.appearances:
        return entity.appearances[0].range
    value = entity.fields.get("date", entity.fields.get("time"))
    if value is not None:
        return TimeRange(value, value)
    return None


def _shared_timeline(left: EntityRecord, right: EntityRecord) -> bool:
    left_timelines = {appearance.timeline for appearance in left.appearances}
    right_timelines = {appearance.timeline for appearance in right.appearances}
    return bool(left_timelines & right_timelines)


def _timeline_ref_name(value: Any) -> Optional[str]:
    if isinstance(value, Appearance):
        return value.timeline
    if isinstance(value, str):
        return value
    return None


def _duration_positive(value: Any) -> bool:
    return isinstance(value, DurationValue) and any(
        part > 0
        for part in (value.years, value.months, value.days, value.hours, value.minutes, value.seconds)
    )


def _cardinality_min(spec: dict[str, Any], key: str, default: Any = None) -> Any:
    return spec.get(key) if spec.get(key) is not None else default


def _all_named_records(world: ChronologyWorld) -> Iterable[NamedRecord]:
    stores = (
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
    )
    for store in stores:
        yield from store.values()


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _comparable(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    return isinstance(left, type(right)) and isinstance(left, (int, float, date))


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _norm_identity(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def _diag(severity: str, message: str, record: NamedRecord) -> Diagnostic:
    return Diagnostic(
        severity=severity,
        message=message,
        line=record.line,
        column=record.column,
    )


def _schema_diag(severity: str, message: str, schema: EntitySchemaRecord) -> Diagnostic:
    return Diagnostic(
        severity=severity,
        message=message,
        line=schema.line,
        column=schema.column,
    )


def _rel_diag(severity: str, message: str, rel: RelationshipRecord) -> Diagnostic:
    return Diagnostic(
        severity=severity,
        message=message,
        line=rel.line,
        column=rel.column,
    )
