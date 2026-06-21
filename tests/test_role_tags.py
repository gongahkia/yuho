"""Agent/patient role tag coverage."""

from __future__ import annotations

import json

from yuho.ast import nodes
from yuho.services.analysis import analyze_source
from yuho.transpile import JSONTranspiler


ROLE_SOURCE = """
struct TransferFact {
    string action agent seller patient buyer,
}

statute 1 "Role tags" {
    elements {
        actus_reus transfer := "transfer goods" agent seller patient buyer;
        mens_rea intent := TRUE actor seller patient buyer;
    }
}
"""


def test_agent_patient_tags_lower_to_ast():
    result = analyze_source(ROLE_SOURCE, run_semantic=False)

    assert not result.parse_errors
    assert result.ast is not None
    field = result.ast.type_defs[0].fields[0]
    assert field.agent == "seller"
    assert field.patient == "buyer"
    elements = result.ast.statutes[0].elements
    transfer = elements[0]
    intent = elements[1]
    assert isinstance(transfer, nodes.ElementNode)
    assert transfer.agent == "seller"
    assert transfer.actor is None
    assert transfer.patient == "buyer"
    assert isinstance(intent, nodes.ElementNode)
    assert intent.actor == "seller"
    assert intent.agent is None
    assert intent.patient == "buyer"


def test_agent_patient_tags_serialize_to_json():
    result = analyze_source(ROLE_SOURCE, run_semantic=False)
    assert result.ast is not None

    payload = json.loads(JSONTranspiler(include_locations=False).transpile(result.ast))
    field = payload["type_defs"][0]["fields"][0]
    transfer = payload["statutes"][0]["elements"][0]
    assert field["agent"] == "seller"
    assert field["patient"] == "buyer"
    assert transfer["agent"] == "seller"
    assert transfer["patient"] == "buyer"


def test_civil_primitives_keep_agent_patient_tags():
    source = """
    statute 2 "Civil role tags" {
        elements {
            obligation_to deliver_goods := "deliver goods" agent seller patient buyer;
        }
    }
    """

    result = analyze_source(source, run_semantic=True, features={"civil"})

    assert not result.parse_errors
    assert result.semantic_summary is not None
    assert not result.semantic_summary.has_errors
    element = result.ast.statutes[0].elements[0]
    assert isinstance(element, nodes.CivilPrimitiveNode)
    assert element.agent == "seller"
    assert element.patient == "buyer"
