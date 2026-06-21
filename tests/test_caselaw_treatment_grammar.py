"""Parser coverage for caselaw treatment clauses."""

from __future__ import annotations

from yuho.parser import get_parser


def test_caselaw_treatment_clauses_parse():
    source = """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  caselaw "Foo v Bar" "[2020] SGCA 1" {
    "A later case treats earlier authorities."
    element act
    treatment followed "Earlier v Case" "[1990] 1 SLR 1"
    treatment distinguished "Different v Case"
    treatment overruled "Old v Case";
  }
}
"""
    result = get_parser().parse(source, "<treatment>")
    assert not result.errors, [str(error) for error in result.errors]
    assert count_nodes(result.root_node, "treatment_clause") == 3


def count_nodes(node, node_type: str) -> int:
    return int(node.type == node_type) + sum(
        count_nodes(child, node_type) for child in node.children
    )
