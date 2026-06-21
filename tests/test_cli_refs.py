"""Tests for ``yuho refs`` treatment-query CLI."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.commands.refs import run_refs
from yuho.cli.main import cli


def _mk_treatment_library(root: Path) -> Path:
    library = root / "library"
    section_dir = library / "s1_demo"
    section_dir.mkdir(parents=True)
    (section_dir / "statute.yh").write_text(
        """
statute 1 "Demo" {
  elements { actus_reus act := "x"; }
  caselaw "Foo v Bar" "[2020] SGCA 1" {
    "holding"
    treatment overruled "Old v Case" "[1990] 1 SLR 1"
  }
}
""",
        encoding="utf-8",
    )
    return library


def test_refs_overruled_json_flag(tmp_path: Path):
    library = _mk_treatment_library(tmp_path)
    result = CliRunner().invoke(
        cli,
        ["refs", "--library", str(library), "--overruled", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["kinds"] == ["treatment_overruled"]
    assert payload["edges"][0]["src"] == "case:Foo v Bar"
    assert payload["edges"][0]["dst"] == "case:Old v Case"


def test_refs_treatment_case_query_formats_case_nodes(tmp_path: Path, capsys):
    library = _mk_treatment_library(tmp_path)

    run_refs(
        section="Foo v Bar",
        library_dir=str(library),
        direction="out",
        kinds=(),
        treatment=True,
    )

    out = capsys.readouterr().out
    assert "outgoing from Foo v Bar" in out
    assert "Old v Case" in out
    assert "scase:" not in out
