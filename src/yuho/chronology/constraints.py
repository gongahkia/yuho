"""Chronology constraint evaluation."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from yuho.ast import nodes
from yuho.chronology.model import (
    Appearance,
    ChronologyWorld,
    Diagnostic,
    DurationValue,
    EntityRecord,
    NamedRecord,
    RelationshipRecord,
    TimeRange,
)
from yuho.eval.interpreter import (
    AssertionError_,
    Environment,
    Interpreter,
    InterpreterError,
    StructInstance,
    Value,
)


def validate_constraints(world: ChronologyWorld) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for constraint in world.constraints.values():
        interpreter = ChronologyInterpreter(world)
        for stmt in constraint.fields.get("body", []):
            try:
                if isinstance(stmt, nodes.RelationshipDeclNode):
                    if not _relationship_exists(world, stmt):
                        diagnostics.append(_node_diag("error", f"Constraint '{constraint.name}' relationship is not satisfied", stmt, constraint))
                    continue
                result = interpreter.visit(stmt)
                if isinstance(stmt, nodes.ExpressionStmt):
                    if result.type_tag != "bool":
                        diagnostics.append(_node_diag("error", f"Constraint '{constraint.name}' expression did not evaluate to bool", stmt, constraint))
                    elif result.raw is not True:
                        diagnostics.append(_node_diag("error", f"Constraint '{constraint.name}' expression evaluated false", stmt, constraint))
            except AssertionError_ as exc:
                diagnostics.append(_node_diag("error", f"Constraint '{constraint.name}' assertion failed: {exc}", getattr(exc, "node", None), constraint))
            except InterpreterError as exc:
                diagnostics.append(_node_diag("error", f"Constraint '{constraint.name}' evaluation failed: {exc}", getattr(exc, "node", None), constraint))
    return diagnostics


class ChronologyInterpreter(Interpreter):
    def __init__(self, world: ChronologyWorld):
        super().__init__(Environment())
        self.world = world
        self.env.function_defs.update(world.function_defs)
        self.env.statutes.update(world.statute_nodes)
        self._seed_world()

    def visit_list_expr(self, node: nodes.ListExprNode) -> Value:
        return Value([self.visit(item) for item in node.items], "list")

    def visit_range_expr(self, node: nodes.RangeExprNode) -> Value:
        return _range_value(self.visit(node.start), self.visit(node.end))

    def visit_timeline_appearance(self, node: nodes.TimelineAppearanceNode) -> Value:
        range_value = self.visit_range_expr(node.range)
        return Value(
            StructInstance(
                type_name="Appearance",
                fields={
                    "timeline": Value(node.timeline, "string"),
                    "range": range_value,
                    "start": range_value.raw.get_field("start"),
                    "end": range_value.raw.get_field("end"),
                },
            ),
            "struct",
        )

    def visit_function_call(self, node: nodes.FunctionCallNode) -> Value:
        name = _callee_name(node)
        if name in CHRONOLOGY_BUILTINS:
            return CHRONOLOGY_BUILTINS[name](self, [self.visit(arg) for arg in node.args], node)
        return super().visit_function_call(node)

    def _seed_world(self) -> None:
        entity_values = []
        source_values = []
        timeline_values = []
        relationship_values = []
        for source in self.world.sources.values():
            value = self._record_value(source, "Source")
            self.env.set(source.name, value)
            source_values.append(value)
        for bundle in self.world.source_bundles.values():
            value = self._record_value(bundle, "SourceBundle")
            self.env.set(bundle.name, value)
            source_values.append(value)
        for timeline in self.world.timelines.values():
            value = self._record_value(timeline, "Timeline")
            self.env.set(timeline.name, value)
            timeline_values.append(value)
        for entity in self.world.entities.values():
            value = self._entity_value(entity)
            self.env.set(entity.name, value)
            entity_values.append(value)
        for rel in self.world.relationships:
            relationship_values.append(self._relationship_value(rel))
        self.env.set("entities", Value(entity_values, "list"))
        self.env.set("sources", Value(source_values, "list"))
        self.env.set("timelines", Value(timeline_values, "list"))
        self.env.set("relationships", Value(relationship_values, "list"))

    def _record_value(self, record: NamedRecord, type_name: str) -> Value:
        fields = {"id": Value(record.name, "string"), "name": Value(record.name, "string")}
        fields.update({name: _to_value(value) for name, value in record.fields.items()})
        return Value(StructInstance(type_name=type_name, fields=fields), "struct")

    def _entity_value(self, entity: EntityRecord) -> Value:
        fields = {
            "id": Value(entity.name, "string"),
            "name": Value(entity.name, "string"),
            "type": Value(entity.type_name, "string"),
        }
        fields.update({name: _to_value(value) for name, value in entity.fields.items()})
        return Value(StructInstance(type_name=entity.type_name, fields=fields), "struct")

    def _relationship_value(self, rel: RelationshipRecord) -> Value:
        fields = {
            "source": Value(rel.source, "string"),
            "target": Value(rel.target, "string"),
            "label": Value(rel.label or "", "string"),
        }
        if rel.temporal_scope:
            fields["temporal_scope"] = _to_value(rel.temporal_scope)
        return Value(StructInstance(type_name="Relationship", fields=fields), "struct")


def _builtin_type_of(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("type_of", args, 1, node)
    entity = _entity_from_value(interpreter.world, args[0])
    if entity:
        return Value(entity.type_name, "string")
    if args[0].type_tag == "struct":
        return Value(args[0].raw.type_name, "string")
    return Value(args[0].type_tag, "string")


def _builtin_entities_where(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    if len(args) not in {1, 2}:
        raise InterpreterError("entities_where expects 1 or 2 arguments", node)
    matches: list[Value] = []
    if len(args) == 1:
        type_name = str(args[0].raw)
        for entity in interpreter.world.entities.values():
            if entity.type_name == type_name:
                matches.append(interpreter._entity_value(entity))
        return Value(matches, "list")
    field_name = str(args[0].raw)
    expected = args[1].raw
    for entity in interpreter.world.entities.values():
        if entity.fields.get(field_name) == expected:
            matches.append(interpreter._entity_value(entity))
    return Value(matches, "list")


def _builtin_inbound(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    return _relationship_endpoint_values(interpreter, args, node, inbound=True, exists=False)


def _builtin_outbound(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    return _relationship_endpoint_values(interpreter, args, node, inbound=False, exists=False)


def _builtin_has_inbound(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    return _relationship_endpoint_values(interpreter, args, node, inbound=True, exists=True)


def _builtin_has_outbound(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    return _relationship_endpoint_values(interpreter, args, node, inbound=False, exists=True)


def _builtin_before(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("before", args, 2, node)
    left = _range_from_value(interpreter.world, args[0])
    right = _range_from_value(interpreter.world, args[1])
    return Value(bool(left and right and _comparable(left.end, right.start) and left.end <= right.start), "bool")


def _builtin_after(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("after", args, 2, node)
    left = _range_from_value(interpreter.world, args[0])
    right = _range_from_value(interpreter.world, args[1])
    return Value(bool(left and right and _comparable(left.start, right.end) and left.start >= right.end), "bool")


def _builtin_overlaps(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("overlaps", args, 2, node)
    left = _range_from_value(interpreter.world, args[0])
    right = _range_from_value(interpreter.world, args[1])
    if not left or not right or not _comparable(left.start, right.end) or not _comparable(right.start, left.end):
        return Value(False, "bool")
    return Value(left.start <= right.end and right.start <= left.end, "bool")


def _builtin_state_at(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("state_at", args, 2, node)
    entity = _require_entity(interpreter.world, args[0], node)
    point = args[1].raw
    fields = _effective_fields(entity, point)
    return Value(
        StructInstance(entity.type_name, {name: _to_value(value) for name, value in fields.items()}),
        "struct",
    )


def _builtin_field_at(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("field_at", args, 3, node)
    entity = _require_entity(interpreter.world, args[0], node)
    field = str(args[1].raw)
    point = args[2].raw
    return _to_value(_effective_fields(entity, point).get(field))


def _builtin_len(interpreter: ChronologyInterpreter, args: list[Value], node: nodes.ASTNode) -> Value:
    _arity("len", args, 1, node)
    if args[0].type_tag not in {"list", "string"}:
        raise InterpreterError("len expects list or string", node)
    return Value(len(args[0].raw), "int")


CHRONOLOGY_BUILTINS = {
    "type_of": _builtin_type_of,
    "entities_where": _builtin_entities_where,
    "inbound": _builtin_inbound,
    "outbound": _builtin_outbound,
    "has_inbound": _builtin_has_inbound,
    "has_outbound": _builtin_has_outbound,
    "before": _builtin_before,
    "after": _builtin_after,
    "overlaps": _builtin_overlaps,
    "state_at": _builtin_state_at,
    "field_at": _builtin_field_at,
    "len": _builtin_len,
}


def _relationship_endpoint_values(
    interpreter: ChronologyInterpreter,
    args: list[Value],
    node: nodes.ASTNode,
    inbound: bool,
    exists: bool,
) -> Value:
    if len(args) not in {1, 2}:
        raise InterpreterError("relationship endpoint query expects 1 or 2 arguments", node)
    entity = _require_entity(interpreter.world, args[0], node)
    label = str(args[1].raw) if len(args) == 2 else None
    rels = [
        rel
        for rel in interpreter.world.relationships
        if (rel.target == entity.name if inbound else rel.source == entity.name)
        and (label is None or rel.label == label)
    ]
    if exists:
        return Value(bool(rels), "bool")
    other_names = [rel.source if inbound else rel.target for rel in rels]
    return Value([interpreter._entity_value(interpreter.world.entities[name]) for name in other_names if name in interpreter.world.entities], "list")


def _effective_fields(entity: EntityRecord, point: Any) -> dict[str, Any]:
    fields = dict(entity.fields)
    state = fields.pop("state", None)
    changes = state if isinstance(state, list) else [state] if state else []
    applicable = [
        change
        for change in changes
        if isinstance(change, dict)
        and _comparable(change.get("at"), point)
        and change.get("at") <= point
    ]
    applicable.sort(key=lambda change: change["at"])
    for change in applicable:
        for name, value in change.items():
            if name != "at":
                fields[name] = value
    return fields


def _relationship_exists(world: ChronologyWorld, node: nodes.RelationshipDeclNode) -> bool:
    return any(
        rel.source == node.source
        and rel.target == node.target
        and (node.label is None or rel.label == node.label)
        for rel in world.relationships
    )


def _entity_from_value(world: ChronologyWorld, value: Value) -> Optional[EntityRecord]:
    if value.type_tag == "string":
        return world.entities.get(str(value.raw))
    if value.type_tag == "struct":
        name_value = value.raw.fields.get("id") or value.raw.fields.get("name")
        if name_value:
            return world.entities.get(str(name_value.raw))
    return None


def _require_entity(world: ChronologyWorld, value: Value, node: nodes.ASTNode) -> EntityRecord:
    entity = _entity_from_value(world, value)
    if not entity:
        raise InterpreterError("expected chronology entity", node)
    return entity


def _range_from_value(world: ChronologyWorld, value: Value) -> Optional[TimeRange]:
    entity = _entity_from_value(world, value)
    if entity:
        if entity.appearances:
            return entity.appearances[0].range
        point = entity.fields.get("date", entity.fields.get("time"))
        if point is not None:
            return TimeRange(point, point)
    if value.type_tag == "struct":
        if value.raw.type_name == "Range":
            return TimeRange(value.raw.get_field("start").raw, value.raw.get_field("end").raw)
        if value.raw.type_name == "Appearance":
            return TimeRange(value.raw.get_field("start").raw, value.raw.get_field("end").raw)
    return None


def _range_value(start: Value, end: Value) -> Value:
    return Value(
        StructInstance("Range", {"start": start, "end": end}),
        "struct",
    )


def _to_value(value: Any) -> Value:
    if isinstance(value, Value):
        return value
    if isinstance(value, TimeRange):
        return _range_value(_to_value(value.start), _to_value(value.end))
    if isinstance(value, Appearance):
        range_value = _to_value(value.range)
        return Value(
            StructInstance(
                "Appearance",
                {
                    "timeline": Value(value.timeline, "string"),
                    "range": range_value,
                    "start": range_value.raw.get_field("start"),
                    "end": range_value.raw.get_field("end"),
                },
            ),
            "struct",
        )
    if isinstance(value, DurationValue):
        return Value(
            nodes.DurationNode(
                years=value.years,
                months=value.months,
                days=value.days,
                hours=value.hours,
                minutes=value.minutes,
                seconds=value.seconds,
            ),
            "duration",
        )
    if isinstance(value, dict):
        return Value(StructInstance("<anonymous>", {str(key): _to_value(item) for key, item in value.items()}), "struct")
    if isinstance(value, list):
        return Value([_to_value(item) for item in value], "list")
    if isinstance(value, bool):
        return Value(value, "bool")
    if isinstance(value, int):
        return Value(value, "int")
    if isinstance(value, float):
        return Value(value, "float")
    if isinstance(value, date):
        return Value(value, "date")
    if value is None:
        return Value(None, "none")
    return Value(str(value), "string")


def _callee_name(node: nodes.FunctionCallNode) -> str:
    if isinstance(node.callee, nodes.IdentifierNode):
        return node.callee.name
    if isinstance(node.callee, nodes.FieldAccessNode):
        return node.callee.field_name
    return ""


def _arity(name: str, args: list[Value], expected: int, node: nodes.ASTNode) -> None:
    if len(args) != expected:
        raise InterpreterError(f"{name} expects {expected} arguments", node)


def _comparable(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    return isinstance(left, type(right)) and isinstance(left, (int, float, date))


def _node_diag(
    severity: str,
    message: str,
    node: Optional[nodes.ASTNode],
    fallback: NamedRecord,
) -> Diagnostic:
    loc = getattr(node, "source_location", None)
    return Diagnostic(
        severity=severity,
        message=message,
        line=loc.line if loc else fallback.line,
        column=loc.col if loc else fallback.column,
    )
