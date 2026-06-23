from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


def test_init_creates_runnable_workspace(tmp_path: Path) -> None:
    root = tmp_path / "starter"

    result = CliRunner().invoke(cli, ["init", str(root)])

    assert result.exit_code == 0
    assert "Created Yuho starter workspace" in result.output
    assert (root / "statute.yh").exists()
    assert (root / "facts.json").exists()
    assert (root / "README.md").exists()
    assert (root / "out" / "starter.txt").exists()

    check = CliRunner().invoke(cli, ["check", str(root / "statute.yh")])
    assert check.exit_code == 0
    assert "VALID:" in check.output


def test_init_json_lists_created_files(tmp_path: Path) -> None:
    root = tmp_path / "starter"

    result = CliRunner().invoke(cli, ["init", "--json", str(root)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["created"]["directory"] == str(root)
    assert payload["smoke"]["valid"] is True
    assert payload["smoke"]["explains"] is True
    assert "yuho check statute.yh" in payload["commands"]


def test_init_refuses_nonempty_directory_without_force(tmp_path: Path) -> None:
    root = tmp_path / "starter"
    root.mkdir()
    (root / "keep.txt").write_text("keep", encoding="utf-8")

    result = CliRunner().invoke(cli, ["init", str(root)])

    assert result.exit_code == 2
    assert "already exists and is not empty" in result.output
