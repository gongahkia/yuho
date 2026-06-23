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


def test_init_statute_literate_template_creates_source_anchors(tmp_path: Path) -> None:
    root = tmp_path / "literate"

    result = CliRunner().invoke(cli, ["init", "--template", "statute-literate", str(root)])

    assert result.exit_code == 0
    assert (root / "legal-text.md").exists()
    statute = (root / "statute.yh").read_text(encoding="utf-8")
    assert "source: legal-text.md#p1" in statute
    assert "facts.representation.made" in statute
    assert (root / "out" / "starter.txt").exists()

    explain = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(root / "facts.json"), str(root / "statute.yh")],
    )
    assert explain.exit_code == 0
    assert "Section 1 is satisfied." in explain.output


def test_init_statute_literate_json_lists_legal_text(tmp_path: Path) -> None:
    root = tmp_path / "literate"

    result = CliRunner().invoke(
        cli,
        ["init", "--template", "statute-literate", "--json", str(root)],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["created"]["template"] == "statute-literate"
    assert payload["created"]["legal_text"] == str(root / "legal-text.md")
    assert payload["smoke"]["explains"] is True


def test_init_statute_exceptions_template_creates_defence_workflow(tmp_path: Path) -> None:
    root = tmp_path / "exceptions"

    result = CliRunner().invoke(cli, ["init", "--template", "statute-exceptions", str(root)])

    assert result.exit_code == 0
    statute = (root / "statute.yh").read_text(encoding="utf-8")
    facts = json.loads((root / "facts.json").read_text(encoding="utf-8"))
    assert "exception lawful_authority" in statute
    assert "when facts.defence.lawful_authority" in statute
    assert facts["defence"]["lawful_authority"] is False

    check = CliRunner().invoke(cli, ["check", str(root / "statute.yh")])
    assert check.exit_code == 0


def test_init_statute_cross_reference_template_runs_section_two(tmp_path: Path) -> None:
    root = tmp_path / "crossref"

    result = CliRunner().invoke(
        cli,
        ["init", "--template", "statute-cross-reference", str(root)],
    )

    assert result.exit_code == 0
    statute = (root / "statute.yh").read_text(encoding="utf-8")
    assert "apply_scope(s1, facts)" in statute

    explain = CliRunner().invoke(
        cli,
        [
            "explain",
            str(root / "statute.yh"),
            "--facts",
            str(root / "facts.json"),
        ],
    )
    assert explain.exit_code == 0
    assert "Section 2 is satisfied." in explain.output


def test_init_guided_prompts_for_template_and_title(tmp_path: Path) -> None:
    root = tmp_path / "guided"

    result = CliRunner().invoke(
        cli,
        ["init", "--guided", "--no-run", str(root)],
        input="statute-exceptions\nGuided Defence\n\n\n",
    )

    assert result.exit_code == 0
    assert "Yuho guided init" in result.output
    assert "Executable elements" in result.output
    assert "guided:  template=statute-exceptions" in result.output
    statute = (root / "statute.yh").read_text(encoding="utf-8")
    assert 'statute 1 "Guided Defence"' in statute
    assert "exception lawful_authority" in statute
    assert not (root / "out" / "starter.txt").exists()


def test_init_guided_reprompts_invalid_element_expression(tmp_path: Path) -> None:
    root = tmp_path / "guided-invalid"

    result = CliRunner().invoke(
        cli,
        ["init", "--guided", "--no-run", str(root)],
        input='basic\nGuided Theft\nfacts.\n"Custom taking"\n\n\n',
    )

    assert result.exit_code == 0
    assert "invalid element expression" in result.output
    statute = (root / "statute.yh").read_text(encoding="utf-8")
    assert 'actus_reus taking := "Custom taking";' in statute
    assert "facts." not in statute


def test_init_guided_refuses_json_mode(tmp_path: Path) -> None:
    result = CliRunner().invoke(
        cli,
        ["init", "--guided", "--json", str(tmp_path / "guided")],
    )

    assert result.exit_code == 2
    assert "--guided cannot be combined with --json" in result.output


def test_init_refuses_nonempty_directory_without_force(tmp_path: Path) -> None:
    root = tmp_path / "starter"
    root.mkdir()
    (root / "keep.txt").write_text("keep", encoding="utf-8")

    result = CliRunner().invoke(cli, ["init", str(root)])

    assert result.exit_code == 2
    assert "already exists and is not empty" in result.output
