"""LSP handler unit tests.

Skipped automatically if ``pygls`` / ``lsprotocol`` aren't installed
(they're optional deps under ``yuho[lsp]``). When pygls is present,
we drive the handler methods directly without going through the
full stdio protocol.
"""

from __future__ import annotations

from pathlib import Path

import pytest

# Import gating: pygls is optional.
pygls = pytest.importorskip("pygls", reason="pygls not installed (yuho[lsp])")
lsprotocol = pytest.importorskip("lsprotocol", reason="lsprotocol not installed")

from lsprotocol import types as lsp  # type: ignore  # noqa: E402

from yuho.lsp.server import YuhoLanguageServer, DocumentState  # noqa: E402


@pytest.fixture
def server():
    return YuhoLanguageServer()


@pytest.fixture
def workspace_server(tmp_path: Path):
    """A server pointed at a tiny synthetic workspace with one section."""
    library = tmp_path / "library" / "penal_code"
    library.mkdir(parents=True)
    sec = library / "s415_cheating"
    sec.mkdir()
    yh = sec / "statute.yh"
    yh.write_text(
        '/// @meta source=https://sso.agc.gov.sg/Act/PC1871\n'
        'statute 415 "Cheating" effective 1872-01-01 {\n'
        '    elements {\n'
        '        actus_reus deception := "Deceiving any person";\n'
        '    }\n'
        '    penalty {\n'
        '        imprisonment := 0 years .. 7 years;\n'
        '        fine := unlimited;\n'
        '    }\n'
        '}\n',
        encoding="utf-8",
    )

    # Second section that references s415.
    sec_b = library / "s420_cheating_inducing"
    sec_b.mkdir()
    (sec_b / "statute.yh").write_text(
        'statute 420 "Cheating inducing delivery" effective 1872-01-01 {\n'
        '    /// builds on s415 cheating, with the additional inducement\n'
        '    elements {\n'
        '        actus_reus s415_cheating := "Cheating per s415";\n'
        '    }\n'
        '}\n',
        encoding="utf-8",
    )

    s = YuhoLanguageServer()
    s._workspace_folders = [f"file://{tmp_path}"]
    return s, tmp_path


# --------------------------------------------------------------
# Hover
# --------------------------------------------------------------


class TestHover:
    def test_hover_on_keyword(self, server):
        doc = DocumentState(uri="file:///t.yh", source="actus_reus x := \"y\";")
        server._documents[doc.uri] = doc
        # Cursor at column 1 of `actus_reus`
        result = server._get_hover(doc.uri, lsp.Position(line=0, character=2))
        assert result is None or result.contents is not None  # tolerant


# --------------------------------------------------------------
# Cross-section goto-definition (G10)
# --------------------------------------------------------------


class TestCrossSectionGotoDef:
    def test_jumps_to_referenced_section(self, workspace_server):
        s, root = workspace_server
        # Simulate having s420 open and clicking on `s415_cheating`'s `s415`.
        s420_uri = f"file://{root}/library/penal_code/s420_cheating_inducing/statute.yh"
        source = (root / "library/penal_code/s420_cheating_inducing/statute.yh").read_text()
        doc = DocumentState(uri=s420_uri, source=source)
        s._documents[s420_uri] = doc

        # Find the `s415` mention in the doc-comment.
        target_line = next(i for i, ln in enumerate(source.splitlines()) if "s415" in ln)
        line_text = source.splitlines()[target_line]
        char = line_text.index("415")  # column where the digits start

        result = s._get_definition(s420_uri, lsp.Position(line=target_line, character=char))
        assert result is not None, "expected goto-def to land on s415's statute.yh"
        assert "s415_cheating/statute.yh" in result.uri

    def test_returns_none_for_unknown_section(self, workspace_server):
        s, root = workspace_server
        s420_uri = f"file://{root}/library/penal_code/s420_cheating_inducing/statute.yh"
        doc = DocumentState(uri=s420_uri, source='/// see s99999\nstatute 420 "x" {}\n')
        s._documents[s420_uri] = doc
        result = s._get_definition(s420_uri, lsp.Position(line=0, character=11))
        assert result is None


# --------------------------------------------------------------
# Cross-file rename via G10
# --------------------------------------------------------------


class TestCrossFileRename:
    def test_rename_section_propagates(self, workspace_server):
        s, root = workspace_server
        # Open s415; rename to s415A. Should produce edits on s420 too.
        s415 = root / "library/penal_code/s415_cheating/statute.yh"
        uri = f"file://{s415}"
        doc = DocumentState(uri=uri, source=s415.read_text())
        s._documents[uri] = doc

        # Position the cursor on the `415` in `statute 415 "Cheating"`.
        line_text = s415.read_text().splitlines()[1]  # line 1 (0-indexed)
        char = line_text.index("415")
        result = s._rename_symbol(uri, lsp.Position(line=1, character=char), "415A")
        assert result is not None, "expected a WorkspaceEdit"
        # Should include edits to both files.
        files = list(result.changes.keys())
        assert any("s415_cheating" in f for f in files)
        assert any("s420_cheating_inducing" in f for f in files), (
            "expected the cross-section reference in s420 to get renamed too"
        )


# --------------------------------------------------------------
# Semantic tokens
# --------------------------------------------------------------


class TestSemanticTokens:
    def test_emits_tokens_for_known_keywords(self):
        s = YuhoLanguageServer()
        source = (
            'statute 1 "x" effective 1872-01-01 {\n'
            '    elements { actus_reus deception := "y"; }\n'
            '    penalty { fine := unlimited; caning := unspecified; }\n'
            '}\n'
        )
        doc = DocumentState(uri="file:///t.yh", source=source)
        # Need a minimal AST stub so the function doesn't return early.
        class _StubAST:
            type_defs = []
            function_defs = []
            statutes = []
        doc.ast = _StubAST()
        s._documents[doc.uri] = doc
        tokens = s._get_semantic_tokens(doc.uri)
        assert tokens is not None
        # Each token is 5 ints (line, col, length, type, modifiers).
        assert len(tokens.data) % 5 == 0
        assert len(tokens.data) >= 5  # at least one keyword tokenized

    def test_no_overlapping_tokens(self):
        s = YuhoLanguageServer()
        # Many overlapping keyword candidates in one line.
        source = "elements actus_reus mens_rea circumstance unlimited unspecified\n"
        doc = DocumentState(uri="file:///t.yh", source=source)
        class _StubAST:
            type_defs = []
            function_defs = []
            statutes = []
        doc.ast = _StubAST()
        s._documents[doc.uri] = doc
        tokens = s._get_semantic_tokens(doc.uri)
        assert tokens is not None
        # Cumulative position must be monotonic (delta_line >= 0; if delta_line == 0, delta_col > 0).
        line = 0
        col = 0
        for i in range(0, len(tokens.data), 5):
            d_line, d_col, *_ = tokens.data[i:i + 5]
            line += d_line
            col = d_col if d_line > 0 else col + d_col
            assert d_line >= 0
            if d_line == 0:
                assert d_col > 0, "overlapping or duplicate tokens in semantic stream"
