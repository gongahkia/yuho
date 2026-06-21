"""Fact event AST coverage."""

from __future__ import annotations

import json

from yuho.ast import (
    DateNode,
    FactEventNode,
    FactParticipantNode,
    ModuleNode,
    NamedType,
)
from yuho.ast.transformer import Transformer
from yuho.transpile import JSONTranspiler


def test_fact_event_children_include_timestamp_and_participants():
    participant = FactParticipantNode(
        role="agent",
        name="seller",
        type_annotation=NamedType(name="Person"),
    )
    timestamp = DateNode.from_iso8601("2026-01-02")
    event = FactEventNode(
        name="delivery",
        action="deliver_goods",
        timestamp=timestamp,
        participants=(participant,),
    )

    assert event.children() == [timestamp, participant]
    assert participant.children() == [participant.type_annotation]


def test_fact_events_serialize_from_module_json():
    event = FactEventNode(
        name="delivery",
        action="deliver_goods",
        timestamp=DateNode.from_iso8601("2026-01-02"),
        participants=(
            FactParticipantNode("agent", "seller", NamedType(name="Person")),
            FactParticipantNode("patient", "buyer", NamedType(name="Person")),
        ),
        meta={"source": "hypo"},
    )
    module = ModuleNode(
        imports=(),
        type_defs=(),
        function_defs=(),
        statutes=(),
        variables=(),
        fact_events=(event,),
    )

    assert module.children() == [event]
    payload = json.loads(JSONTranspiler(include_locations=False).transpile(module))
    serialized = payload["fact_events"][0]
    assert serialized["action"] == "deliver_goods"
    assert serialized["timestamp"]["value"] == "2026-01-02"
    assert serialized["participants"][0]["role"] == "agent"
    assert serialized["participants"][0]["type"]["name"] == "Person"
    assert serialized["meta"] == {"source": "hypo"}


def test_transformer_visits_fact_event_timestamp():
    class ReplaceDate(Transformer):
        def transform_date(self, node):
            return DateNode.from_iso8601("2026-01-03")

    event = FactEventNode(
        name="delivery",
        action="deliver_goods",
        timestamp=DateNode.from_iso8601("2026-01-02"),
    )

    transformed = ReplaceDate().transform(event)

    assert transformed.timestamp.value.isoformat() == "2026-01-03"
