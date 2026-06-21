"""Parser coverage for element interpretation blocks."""

from __future__ import annotations

from yuho.ast.statute_lint import lint_module
from yuho.ast.nodes import ElementNode
from yuho.parser import get_parser
from yuho.services.analysis import analyze_source


SOURCE = """
statute 1 "Demo" {
  elements {
    actus_reus deception := "deception" interpretations {
      interpretation narrow {
        "express representation only"
        citation "Foo v Bar"
        court "CA"
        endorsement binding
      }
      interpretation broad {
        "conduct can imply representation"
        endorsement persuasive
      }
    }
  }
}
"""


def test_element_interpretation_blocks_parse():
    result = get_parser().parse(SOURCE, "<interpretation>")
    assert not result.errors, [str(error) for error in result.errors]
    assert has_node_type(result.root_node, "interpretation_block")


def test_builder_attaches_element_interpretations():
    result = analyze_source(SOURCE, file="<interpretation>", run_semantic=False)
    assert not result.parse_errors
    element = result.ast.statutes[0].elements[0]
    assert isinstance(element, ElementNode)
    assert len(element.interpretations) == 2

    narrow, broad = element.interpretations
    assert narrow.name == "narrow"
    assert narrow.reading.value == "express representation only"
    assert narrow.citation and narrow.citation.value == "Foo v Bar"
    assert narrow.court and narrow.court.value == "CA"
    assert narrow.endorsement == "binding"
    assert broad.name == "broad"
    assert broad.endorsement == "persuasive"


def test_lint_warns_on_unendorsed_competing_interpretations():
    source = """
statute 1 "Demo" {
  elements {
    actus_reus deception := "deception" interpretations {
      interpretation narrow { "express representation only" }
      interpretation broad { "conduct can imply representation" }
    }
  }
}
"""
    messages = lint_messages(source)
    assert any("competing interpretations" in message for message in messages)


def test_lint_accepts_endorsed_competing_interpretations():
    messages = lint_messages(SOURCE)
    assert not any("competing interpretations" in message for message in messages)


def has_node_type(node, node_type: str) -> bool:
    if node.type == node_type:
        return True
    return any(has_node_type(child, node_type) for child in node.children)


def lint_messages(source: str) -> list[str]:
    result = analyze_source(source, file="<interpretation>", run_semantic=False)
    assert not result.parse_errors
    return [warning.message for warning in lint_module(result.ast)]
