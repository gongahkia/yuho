"""Tests for the Yuho LSP bootstrap."""

from __future__ import annotations

from yuho.library.reference_graph import ReferenceEdge, ReferenceGraph
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


def test_definition_resolves_same_file_cross_section_ref():
    source = """
statute 299 "Base" {
  elements { all_of { actus_reus conduct := "does the act"; } }
}

fn run() : bool { return is_infringed(s299); }
"""
    server = YuhoLanguageServer()
    uri = "file:///tmp/same.yh"
    server.parse_source(uri, source)
    line, character = position_of(source, "s299")
    locations = server.definition_at(uri, line, character)
    assert locations is not None
    assert locations[0].uri == uri
    assert locations[0].range.start.line == 1


def test_definition_resolves_imported_cross_section_ref(tmp_path):
    base = tmp_path / "base.yh"
    base.write_text(
        """
statute 299 "Base" {
  elements { all_of { actus_reus conduct := "does the act"; } }
}
""",
        encoding="utf-8",
    )
    main = tmp_path / "main.yh"
    source = """
import "base.yh"

fn run() : bool { return apply_scope(s299); }
"""
    main.write_text(source, encoding="utf-8")
    server = YuhoLanguageServer()
    uri = main.as_uri()
    server.parse_source(uri, source)
    line, character = position_of(source, "s299")
    locations = server.definition_at(uri, line, character)
    assert locations is not None
    assert locations[0].uri == base.as_uri()
    assert locations[0].range.start.line == 1


def test_definition_uses_reference_graph_library_fallback(tmp_path, monkeypatch):
    library_dir = tmp_path / "library" / "penal_code"
    target = library_dir / "s299_base" / "statute.yh"
    target.parent.mkdir(parents=True)
    target.write_text(
        """
statute 299 "Base" {
  elements { all_of { actus_reus conduct := "does the act"; } }
}
""",
        encoding="utf-8",
    )
    graph = ReferenceGraph()
    graph.add(
        ReferenceEdge(
            src="300",
            dst="299",
            kind="subsumes",
            source_path="penal_code/s300_wrapper/statute.yh",
        )
    )
    monkeypatch.setattr("yuho.lsp.server.DEFAULT_LIBRARY_DIR", library_dir)
    server = YuhoLanguageServer()
    server.reference_graphs[str(library_dir.resolve())] = graph
    source = "fn run() : bool { return is_infringed(s299); }"
    uri = "file:///tmp/library-fallback.yh"
    server.parse_source(uri, source)
    line, character = position_of(source, "s299")
    locations = server.definition_at(uri, line, character)
    assert locations is not None
    assert locations[0].uri == target.as_uri()
    assert locations[0].range.start.line == 1


def test_diagnostics_include_lint_warnings():
    server = YuhoLanguageServer()
    uri = "file:///tmp/lint.yh"
    server.parse_source(uri, VALID_SOURCE)
    diagnostics = server.diagnostics_for_uri(uri)
    messages = [diagnostic.message for diagnostic in diagnostics]
    assert any("no mens_rea" in message for message in messages)
    assert any("no penalty" in message for message in messages)


def test_diagnostics_include_type_check_errors():
    server = YuhoLanguageServer()
    uri = "file:///tmp/type.yh"
    server.parse_source(uri, 'fn f() : int { return "x"; }')
    diagnostics = server.diagnostics_for_uri(uri)
    assert any(
        diagnostic.message == "Return type string does not match expected int"
        for diagnostic in diagnostics
    )


def test_publish_diagnostics_for_uri_sends_publish_params(monkeypatch):
    server = YuhoLanguageServer()
    uri = "file:///tmp/lint.yh"
    server.parse_source(uri, VALID_SOURCE)
    published = []

    def fake_publish(params):
        published.append(params)

    monkeypatch.setattr(server, "text_document_publish_diagnostics", fake_publish)
    server.publish_diagnostics_for_uri(uri)
    assert published
    assert published[0].uri == uri
    assert published[0].diagnostics


def position_of(source: str, needle: str) -> tuple[int, int]:
    offset = source.index(needle)
    line = source[:offset].count("\n")
    character = offset - source.rfind("\n", 0, offset) - 1
    return line, character
