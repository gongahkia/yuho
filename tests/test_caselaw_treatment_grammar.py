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
    treatment followed "Followed v Case" "[1990] 1 SLR 1"
    treatment follows "Follows v Case"
    treatment distinguished "Distinguished v Case"
    treatment distinguishes "Distinguishes v Case"
    treatment overruled "Overruled v Case";
    treatment overrules "Overrules v Case"
    treatment reversed "Reversed v Case"
    treatment reverses "Reverses v Case"
    treatment approved "Approved v Case"
    treatment approves "Approves v Case"
    treatment disapproved "Disapproved v Case"
    treatment disapproves "Disapproves v Case"
    treatment applied "Applied v Case"
    treatment applies "Applies v Case"
  }
}
"""


def test_caselaw_treatment_clauses_parse():
    result = get_parser().parse(SOURCE, "<treatment>")
    assert not result.errors, [str(error) for error in result.errors]
    assert count_nodes(result.root_node, "treatment_clause") == 14


def test_builder_attaches_caselaw_treatments():
    result = analyze_source(SOURCE, file="<treatment>", run_semantic=False)
    assert not result.parse_errors
    case = result.ast.statutes[0].case_law[0]
    assert len(case.treatments) == 14

    followed, follows, distinguished, distinguishes, overruled, overrules, *rest = (
        case.treatments
    )
    assert followed.kind == "followed"
    assert followed.target.value == "Followed v Case"
    assert followed.citation and followed.citation.value == "[1990] 1 SLR 1"
    assert follows.kind == "followed"
    assert distinguished.kind == "distinguished"
    assert distinguished.target.value == "Distinguished v Case"
    assert distinguished.citation is None
    assert distinguishes.kind == "distinguished"
    assert overruled.kind == "overruled"
    assert overruled.target.value == "Overruled v Case"
    assert overrules.kind == "overruled"
    assert [t.kind for t in rest] == [
        "reversed",
        "reversed",
        "approved",
        "approved",
        "disapproved",
        "disapproved",
        "applied",
        "applied",
    ]


def count_nodes(node, node_type: str) -> int:
    return int(node.type == node_type) + sum(
        count_nodes(child, node_type) for child in node.children
    )
