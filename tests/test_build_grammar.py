"""Grammar generation must use the repository's locked Node CLI."""

from __future__ import annotations

from pathlib import Path

from scripts.build_grammar import build_grammar, find_tree_sitter_cli


def test_build_grammar_requires_a_local_cli(tmp_path: Path, capsys) -> None:
    grammar_dir = tmp_path / "grammar"
    grammar_dir.mkdir()

    assert find_tree_sitter_cli(grammar_dir) is None
    assert build_grammar(grammar_dir) is False
    assert "npm ci" in capsys.readouterr().out
