"""CLI tests for ``yuho explain``."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


STATUTE = """
statute 1 "Demo" {
    elements {
        actus_reus taking := "takes";
        mens_rea intent := "intends";
    }
}
"""


def _write_library(tmp_path: Path) -> Path:
    root = tmp_path / "library"
    section = root / "s1_demo"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(STATUTE, encoding="utf-8")
    return root


def test_explain_cli_outputs_element_trace(tmp_path: Path):
    root = _write_library(tmp_path)
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True, "intent": False}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert "Section 1: NOT SATISFIED" in result.output
    assert "[x] actus_reus: taking" in result.output
    assert "[ ] mens_rea: intent" in result.output


def test_explain_cli_json_output(tmp_path: Path):
    root = _write_library(tmp_path)
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True, "intent": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "--json", "1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["overall_satisfied"] is True
    assert payload["elements"][0]["name"] == "taking"
