"""Tests for jurisdiction-aware scope analysis."""

from __future__ import annotations

from yuho.ast.scope_analysis import ScopeAnalysisVisitor, SymbolKind
from yuho.services.analysis import analyze_source


def _scope_result(source: str):
    analysis = analyze_source(source, file="<jurisdiction-scope>", run_semantic=False)
    assert not analysis.parse_errors
    visitor = ScopeAnalysisVisitor()
    return analysis.ast.accept(visitor), analysis.ast


def test_scope_indexes_definitions_by_jurisdiction():
    result, _ = _scope_result(
        """
statute 1 "SG demo" jurisdiction singapore {
  definitions { property := "sg property"; }
}
statute 1 "IN demo" jurisdiction india {
  definitions { property := "in property"; }
}
"""
    )

    sg_defs = result.jurisdiction_definitions["singapore"]
    in_defs = result.jurisdiction_definitions["india"]
    assert sg_defs["property"][0].jurisdiction == "singapore"
    assert in_defs["property"][0].jurisdiction == "india"
    assert sg_defs["property"][0].declaration_node.definition.value == "sg property"
    assert in_defs["property"][0].declaration_node.definition.value == "in property"


def test_scope_registers_jurisdiction_symbols_once():
    result, _ = _scope_result(
        """
statute 1 "One" jurisdiction singapore { }
statute 2 "Two" jurisdiction singapore { }
"""
    )

    symbol = result.root_scope.lookup("jurisdiction:singapore")
    assert symbol is not None
    assert symbol.kind is SymbolKind.JURISDICTION
    assert not result.errors


def test_doc_comment_jurisdiction_populates_node_and_scope():
    result, ast = _scope_result(
        """
/// @jurisdiction singapore
statute 1 "Demo" {
  definitions { act := "x"; }
}
"""
    )

    statute = ast.statutes[0]
    assert statute.jurisdiction_node
    assert statute.jurisdiction_node.name == "singapore"
    assert "act" in result.jurisdiction_definitions["singapore"]
