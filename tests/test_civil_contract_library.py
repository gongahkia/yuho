"""Civil library proof-of-concept coverage."""

from __future__ import annotations

from pathlib import Path

from yuho.ast import nodes
from yuho.services.analysis import analyze_file


CONTRACT_POC = Path(
    "library/contracts_rights_third_parties/s2_right_third_party_enforce/statute.yh"
)


def _flatten(elements):
    out = []
    for element in elements:
        if isinstance(element, nodes.ElementGroupNode):
            out.extend(_flatten(element.members))
        else:
            out.append(element)
    return out


def test_contract_poc_section_uses_civil_feature_primitives():
    result = analyze_file(CONTRACT_POC, run_semantic=True, features={"civil"})

    assert not result.parse_errors
    assert result.ast is not None
    assert result.semantic_summary is not None
    assert not result.semantic_summary.has_errors
    statute = result.ast.statutes[0]
    assert statute.jurisdiction == "singapore"
    civil_nodes = [
        element
        for element in _flatten(statute.elements)
        if isinstance(element, nodes.CivilPrimitiveNode)
    ]
    assert [node.primitive_type for node in civil_nodes] == [
        "party",
        "party",
        "obligation_to",
        "obligation_to",
        "condition_precedent",
        "condition_precedent",
    ]


def test_contract_poc_section_requires_civil_feature():
    result = analyze_file(CONTRACT_POC, run_semantic=False)

    assert result.parse_errors
    assert any("requires --feature=civil" in str(error) for error in result.parse_errors)
