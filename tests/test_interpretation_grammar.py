"""Parser coverage for element interpretation blocks."""

from __future__ import annotations

from yuho.parser import get_parser


def test_element_interpretation_blocks_parse():
    source = """
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
    result = get_parser().parse(source, "<interpretation>")
    assert not result.errors, [str(error) for error in result.errors]
    assert has_node_type(result.root_node, "interpretation_block")


def has_node_type(node, node_type: str) -> bool:
    if node.type == node_type:
        return True
    return any(has_node_type(child, node_type) for child in node.children)
