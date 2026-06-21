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
    assert server.cached_parse("file:///tmp/demo.yh") is parsed


def test_server_parse_source_caches_parse_errors():
    server = YuhoLanguageServer()
    parsed = server.parse_source("file:///tmp/bad.yh", 'statute 1 "Bad" {')
    assert not parsed.result.is_valid
    assert parsed.result.errors


def test_create_server_registers_document_features():
    server = create_server()
    assert server.protocol.fm.features
