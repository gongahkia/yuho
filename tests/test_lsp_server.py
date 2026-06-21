"""Tests for the Yuho LSP bootstrap."""

from __future__ import annotations

from yuho.lsp.server import YuhoLanguageServer, create_server, uri_to_file


VALID_SOURCE = """
statute 1 "Demo" {
  elements { all_of {
    actus_reus conduct := "does the act";
  } }
}
"""


def test_uri_to_file_decodes_file_uri():
    assert uri_to_file("file:///tmp/demo%20file.yh") == "/tmp/demo file.yh"
    assert uri_to_file("untitled:demo.yh") == "untitled:demo.yh"


def test_server_parse_source_uses_tree_sitter_parser():
    server = YuhoLanguageServer()
    parsed = server.parse_source("file:///tmp/demo.yh", VALID_SOURCE)
    assert parsed.result.is_valid
    assert parsed.result.root_node is not None
    assert parsed.ast is not None
    assert server.cached_parse("file:///tmp/demo.yh") is parsed


def test_server_parse_source_caches_parse_errors():
    server = YuhoLanguageServer()
    parsed = server.parse_source("file:///tmp/bad.yh", 'statute 1 "Bad" {')
    assert not parsed.result.is_valid
    assert parsed.result.errors


def test_create_server_registers_document_features():
    server = create_server()
    assert server.protocol.fm.features


def test_hover_surfaces_ast_node_kind_and_source_location():
    server = YuhoLanguageServer()
    uri = "file:///tmp/demo.yh"
    server.parse_source(uri, VALID_SOURCE)
    offset = VALID_SOURCE.index("conduct")
    line = VALID_SOURCE[:offset].count("\n")
    character = offset - VALID_SOURCE.rfind("\n", 0, offset) - 1
    hover = server.hover_at(uri, line, character)
    assert hover is not None
    assert "ElementNode" in hover.contents.value
    assert "/tmp/demo.yh" in hover.contents.value
    assert hover.range is not None
