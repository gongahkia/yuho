"""Parser coverage for caselaw treatment clauses."""

from __future__ import annotations

from yuho.parser import get_parser
from yuho.services.analysis import analyze_source


SOURCE = """
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


def test_caselaw_treatment_clauses_parse():
    result = get_parser().parse(SOURCE, "<treatment>")
    assert not result.errors, [str(error) for error in result.errors]
    assert count_nodes(result.root_node, "treatment_clause") == 3


def test_builder_attaches_caselaw_treatments():
    result = analyze_source(SOURCE, file="<treatment>", run_semantic=False)
    assert not result.parse_errors
    case = result.ast.statutes[0].case_law[0]
    assert len(case.treatments) == 3

    followed, distinguished, overruled = case.treatments
    assert followed.kind == "followed"
    assert followed.target.value == "Earlier v Case"
    assert followed.citation and followed.citation.value == "[1990] 1 SLR 1"
    assert distinguished.kind == "distinguished"
    assert distinguished.target.value == "Different v Case"
    assert distinguished.citation is None
    assert overruled.kind == "overruled"
    assert overruled.target.value == "Old v Case"


def count_nodes(node, node_type: str) -> int:
    return int(node.type == node_type) + sum(
        count_nodes(child, node_type) for child in node.children
    )
