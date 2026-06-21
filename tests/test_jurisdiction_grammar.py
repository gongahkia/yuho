"""Parser coverage for first-class statute jurisdiction parameter."""

from __future__ import annotations

from yuho.parser import get_parser
from yuho.services.analysis import analyze_source


def test_statute_jurisdiction_identifier_parses_and_builds():
    source = """
statute 1 "Demo" jurisdiction singapore effective 2020-01-01 {
  elements { actus_reus act := "x"; }
}
"""
    result = get_parser().parse(source, "<jurisdiction>")
    assert not result.errors, [str(error) for error in result.errors]

    analysis = analyze_source(source, file="<jurisdiction>", run_semantic=False)
    assert not analysis.parse_errors
    statute = analysis.ast.statutes[0]
    assert statute.jurisdiction == "singapore"
    assert statute.jurisdiction_node
    assert statute.jurisdiction_node.name == "singapore"


def test_statute_jurisdiction_string_overrides_doc_comment():
    source = """
/// @jurisdiction singapore
statute 1 "Demo" jurisdiction "india" {
  elements { actus_reus act := "x"; }
}
"""
    analysis = analyze_source(source, file="<jurisdiction>", run_semantic=False)

    assert not analysis.parse_errors
    statute = analysis.ast.statutes[0]
    assert statute.jurisdiction == "india"
    assert statute.jurisdiction_node
    assert statute.jurisdiction_node.name == "india"
