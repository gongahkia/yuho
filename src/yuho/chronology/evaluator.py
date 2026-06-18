"""Build chronology worlds from Yuho AST nodes."""

from __future__ import annotations

from typing import Any

from yuho.ast import nodes
from yuho.chronology.model import (
    Appearance,
    ChronologyWorld,
    Diagnostic,
    DurationValue,
    EntitySchemaRecord,
    EntityRecord,
    NamedRecord,
    RelationshipRecord,
    RelationshipTypeRecord,
    ScenarioRecord,
    SourceRecord,
    TimeRange,
    TimelineRecord,
    source_location,
)


def build_world(module: nodes.ModuleNode) -> ChronologyWorld:
    world = ChronologyWorld()
    world.function_defs = {fn.name: fn for fn in module.function_defs}
    world.statute_nodes = {statute.section_number: statute for statute in module.statutes}
    _collect_statute_refs(world, module)
    _collect_entity_schemas(world, module)

    for decl in _top_level_decls(module, include_scenarios=False):
        _apply_decl(world, decl)

    for scenario in module.scenarios:
        scenario_world = _clone_world(world)
        for decl in scenario.body:
            _apply_decl(scenario_world, decl)
        line, column = source_location(scenario)
        _insert(
            world.scenarios,
            ScenarioRecord(
                name=scenario.name,
                fork_from=scenario.fork_from,
                world=scenario_world,
                line=line,
                column=column,
            ),
            world,
            "scenario",
        )
    return world


def _top_level_decls(module: nodes.ModuleNode, include_scenarios: bool) -> list[nodes.ASTNode]:
    decls: list[nodes.ASTNode] = []
    decls.extend(module.sources)
    decls.extend(module.source_bundles)
    decls.extend(module.locators)
    decls.extend(module.rulesets)
    decls.extend(module.deadline_rules)
    decls.extend(module.issues)
    decls.extend(module.issue_elements)
    decls.extend(module.timelines)
    decls.extend(module.entities)
    decls.extend(module.relationship_types)
    decls.extend(module.relationships)
    if include_scenarios:
        decls.extend(module.scenarios)
    decls.extend(module.views)
    decls.extend(module.constraints)
    return decls


def _collect_statute_refs(world: ChronologyWorld, module: nodes.ModuleNode) -> None:
    for statute in module.statutes:
        world.section_refs.add(statute.section_number)
        if statute.title:
            world.statute_refs.add(statute.title.value)
        world.statute_refs.add(statute.section_number)
        for element in statute.elements:
            _collect_element_refs(world, statute.section_number, element)
        for exception in statute.exceptions:
            if exception.label:
                world.exception_refs.add(exception.label)
                world.exception_refs.add(f"{statute.section_number}.{exception.label}")
        for case in statute.case_law:
            world.caselaw_refs.add(case.case_name.value)
            if case.citation:
                world.caselaw_refs.add(case.citation.value)


def _collect_element_refs(world: ChronologyWorld, section: str, element: nodes.ASTNode) -> None:
    if isinstance(element, nodes.ElementNode):
        world.element_refs.add(element.name)
        world.element_refs.add(f"{section}.{element.name}")
    elif isinstance(element, nodes.ElementGroupNode):
        for member in element.members:
            _collect_element_refs(world, section, member)


def _collect_entity_schemas(world: ChronologyWorld, module: nodes.ModuleNode) -> None:
    for struct in module.type_defs:
        line, column = source_location(struct)
        fields: dict[str, Any] = {}
        optional: set[str] = set()
        for field in struct.fields:
            type_name, is_optional = _type_annotation(field.type_annotation)
            fields[field.name] = type_name
            if is_optional:
                optional.add(field.name)
        world.entity_schemas[struct.name] = EntitySchemaRecord(
            name=struct.name,
            parent=getattr(struct, "parent", None),
            fields=fields,
            optional=optional,
            line=line,
            column=column,
        )


def _clone_world(world: ChronologyWorld) -> ChronologyWorld:
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


def _apply_decl(world: ChronologyWorld, decl: nodes.ASTNode) -> None:
    if isinstance(decl, nodes.SourceDeclNode):
        line, column = source_location(decl)
        _insert(
            world.sources,
            SourceRecord(
                name=decl.name,
                fields=_fields(decl.fields),
                kind=decl.kind or "source",
                line=line,
                column=column,
            ),
            world,
            "source",
        )
    elif isinstance(decl, nodes.SourceBundleDeclNode):
        _insert(world.source_bundles, _record(decl), world, "source_bundle")
    elif isinstance(decl, nodes.LocatorDeclNode):
        _insert(world.locators, _record(decl), world, "locator")
    elif isinstance(decl, nodes.RulesetDeclNode):
        _insert(world.rulesets, _record(decl), world, "ruleset")
    elif isinstance(decl, nodes.DeadlineRuleDeclNode):
        _insert(world.deadline_rules, _record(decl), world, "deadline_rule")
    elif isinstance(decl, nodes.IssueDeclNode):
        _insert(world.issues, _record(decl), world, "issue")
    elif isinstance(decl, nodes.IssueElementDeclNode):
        _insert(world.issue_elements, _record(decl), world, "issue_element")
    elif isinstance(decl, nodes.TimelineDeclNode):
        line, column = source_location(decl)
        _insert(
            world.timelines,
            TimelineRecord(name=decl.name, fields=_fields(decl.fields), line=line, column=column),
            world,
            "timeline",
        )
    elif isinstance(decl, nodes.EntityDeclNode):
        line, column = source_location(decl)
        _insert(
            world.entities,
            EntityRecord(
                name=decl.name,
                fields=_fields(decl.fields),
                type_name=decl.type_name or "entity",
                line=line,
                column=column,
            ),
            world,
            "entity",
        )
    elif isinstance(decl, nodes.RelationshipTypeDeclNode):
        line, column = source_location(decl)
        _insert(
            world.relationship_types,
            RelationshipTypeRecord(
                name=decl.name,
                fields=_fields(decl.fields),
                line=line,
                column=column,
            ),
            world,
            "reltype",
        )
    elif isinstance(decl, nodes.RelationshipDeclNode):
        line, column = source_location(decl)
        world.relationships.append(
            RelationshipRecord(
                source=decl.source,
                target=decl.target,
                label=decl.label,
                temporal_scope=_eval_expr(decl.temporal_scope) if decl.temporal_scope else None,
                line=line,
                column=column,
            )
        )
    elif isinstance(decl, nodes.ViewDeclNode):
        _insert(world.views, _record(decl), world, "view")
    elif isinstance(decl, nodes.ConstraintDeclNode):
        line, column = source_location(decl)
        _insert(
            world.constraints,
            NamedRecord(
                name=decl.name,
                fields={"body": list(decl.body)},
                line=line,
                column=column,
            ),
            world,
            "constraint",
        )


def _insert(store: dict[str, Any], record: Any, world: ChronologyWorld, label: str) -> None:
    if record.name in store:
        world.duplicates.append(
            Diagnostic(
                severity="error",
                message=f"Duplicate {label} '{record.name}'",
                line=getattr(record, "line", 0),
                column=getattr(record, "column", 0),
            )
        )
    store[record.name] = record


def _record(decl: nodes.ChronologyDeclNode) -> NamedRecord:
    line, column = source_location(decl)
    return NamedRecord(
        name=decl.name,
        fields=_fields(decl.fields),
        line=line,
        column=column,
    )


def _fields(fields: tuple[nodes.ChronologyField, ...]) -> dict[str, Any]:
    return {field.name: _eval_expr(field.value) for field in fields}


def _eval_expr(expr: nodes.ASTNode | None) -> Any:
    if expr is None:
        return None
    if isinstance(expr, nodes.StringLit):
        return expr.value
    if isinstance(expr, nodes.IntLit):
        return expr.value
    if isinstance(expr, nodes.FloatLit):
        return expr.value
    if isinstance(expr, nodes.BoolLit):
        return expr.value
    if isinstance(expr, nodes.DateNode):
        return expr.value
    if isinstance(expr, nodes.DurationNode):
        return DurationValue(
            years=expr.years,
            months=expr.months,
            days=expr.days,
            hours=expr.hours,
            minutes=expr.minutes,
            seconds=expr.seconds,
        )
    if isinstance(expr, nodes.MoneyNode):
        return {"currency": expr.currency.name, "amount": str(expr.amount)}
    if isinstance(expr, nodes.PercentNode):
        return {"percent": str(expr.value)}
    if isinstance(expr, nodes.IdentifierNode):
        return expr.name
    if isinstance(expr, nodes.FieldAccessNode):
        base = _eval_expr(expr.base)
        return f"{base}.{expr.field_name}" if base else expr.field_name
    if isinstance(expr, nodes.ListExprNode):
        return [_eval_expr(item) for item in expr.items]
    if isinstance(expr, nodes.RangeExprNode):
        return TimeRange(start=_eval_expr(expr.start), end=_eval_expr(expr.end))
    if isinstance(expr, nodes.TimelineAppearanceNode):
        return Appearance(timeline=expr.timeline, range=_eval_expr(expr.range))
    if isinstance(expr, nodes.StructLiteralNode):
        values = {field.name: _eval_expr(field.value) for field in expr.field_values}
        if expr.struct_name:
            values["_type"] = expr.struct_name
        return values
    if isinstance(expr, nodes.FunctionCallNode):
        return _eval_function_call(expr)
    if isinstance(expr, nodes.UnaryExprNode):
        value = _eval_expr(expr.operand)
        if expr.operator == "-" and isinstance(value, (int, float)):
            return -value
        return {"op": expr.operator, "value": value}
    if isinstance(expr, nodes.BinaryExprNode):
        return {"left": _eval_expr(expr.left), "op": expr.operator, "right": _eval_expr(expr.right)}
    return str(expr)


def _eval_function_call(expr: nodes.FunctionCallNode) -> Any:
    if isinstance(expr.callee, nodes.IdentifierNode):
        name = expr.callee.name
    elif isinstance(expr.callee, nodes.FieldAccessNode):
        name = expr.callee.field_name
    else:
        name = ""
    values = [_eval_expr(arg) for arg in expr.args]
    if len(values) == 1 and isinstance(values[0], int):
        if name in ("days", "day"):
            return DurationValue(days=values[0])
        if name in ("months", "month"):
            return DurationValue(months=values[0])
        if name in ("years", "year"):
            return DurationValue(years=values[0])
    return {"call": name, "args": values}


def _type_annotation(type_node: nodes.TypeNode) -> tuple[str, bool]:
    if isinstance(type_node, nodes.OptionalType):
        name, _ = _type_annotation(type_node.inner)
        return name, True
    if isinstance(type_node, nodes.BuiltinType):
        return type_node.name, False
    if isinstance(type_node, nodes.NamedType):
        return type_node.name, False
    if isinstance(type_node, nodes.ArrayType):
        inner, _ = _type_annotation(type_node.element_type)
        return f"[{inner}]", False
    if isinstance(type_node, nodes.GenericType):
        args = ", ".join(_type_annotation(arg)[0] for arg in type_node.type_args)
        return f"{type_node.base}<{args}>", False
    return type_node.__class__.__name__, False
