"""Parser coverage for civil-law primitives behind --feature=civil."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.ast import nodes
from yuho.cli.main import cli
from yuho.parser import get_parser
from yuho.services.analysis import analyze_source


CIVIL_SOURCE = """
statute 1 "Civil demo" {
  elements {
    party buyer := "the buyer";
    obligation_to deliver_goods := "seller must deliver goods";
    condition_precedent payment := "buyer pays first";
    breach non_delivery := "seller does not deliver";
  }
}
"""


def test_civil_primitives_require_feature_flag():
    result = get_parser().parse(CIVIL_SOURCE, "<civil>")

    assert result.errors
    assert any("requires --feature=civil" in str(error) for error in result.errors)


def test_civil_primitives_parse_with_feature_flag():
    result = get_parser().parse(CIVIL_SOURCE, "<civil>", features={"civil"})

    assert not result.errors, [str(error) for error in result.errors]
    assert civil_element_types(result.root_node, CIVIL_SOURCE) == [
        "party",
        "obligation_to",
        "condition_precedent",
        "breach",
    ]


def test_civil_primitives_build_ast_nodes():
    result = analyze_source(
        CIVIL_SOURCE,
        file="<civil>",
        run_semantic=False,
        features={"civil"},
    )

    assert not result.parse_errors
    civil_nodes = [
        element
        for element in result.ast.statutes[0].elements
        if isinstance(element, nodes.CivilPrimitiveNode)
    ]
    assert [node.primitive_type for node in civil_nodes] == [
        "party",
        "obligation_to",
        "condition_precedent",
        "breach",
    ]
    assert civil_nodes[0].name == "buyer"


def test_check_feature_civil_allows_file(tmp_path: Path):
    path = tmp_path / "civil.yh"
    path.write_text(CIVIL_SOURCE, encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["check", str(path), "--syntax-only", "--feature", "civil", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["phases"]["parse"]["valid"] is True


def civil_element_types(node, source: str) -> list[str]:
    out = []
    if node.type == "element_entry":
        element_type = node.child_by_field_name("element_type")
        if element_type is not None:
            source_bytes = source.encode("utf-8")
            text = source_bytes[
                element_type.start_byte:element_type.end_byte
            ].decode("utf-8")
            if text in {"party", "obligation_to", "condition_precedent", "breach"}:
                out.append(text)
    for child in node.children:
        out.extend(civil_element_types(child, source))
    return out
