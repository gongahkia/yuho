"""CLI tests for ``yuho irac``."""

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


def test_irac_cli_outputs_irac_sections(tmp_path: Path):
    statute = tmp_path / "statute.yh"
    statute.write_text(STATUTE, encoding="utf-8")
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True, "intent": False}), encoding="utf-8")

    result = CliRunner().invoke(cli, ["irac", "--facts", str(facts), str(statute)])

    assert result.exit_code == 0
    assert "ISSUE" in result.output
    assert "RULE" in result.output
    assert "APPLICATION" in result.output
    assert "CONCLUSION" in result.output
    assert "Section 1 is not satisfied." in result.output
