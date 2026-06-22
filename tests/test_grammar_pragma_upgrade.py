from __future__ import annotations

from click.testing import CliRunner

from yuho.ast import ASTBuilder
from yuho.cli.commands.upgrade import upgrade_source
from yuho.cli.main import cli
from yuho.parser import get_parser


SOURCE = """
statute 1 "Demo" {
    elements {
        actus_reus act := "act";
    }
}
"""


def test_parser_accepts_top_level_grammar_pragma():
    source = "#yuho v5.1\n" + SOURCE
    result = get_parser().parse(source, "<test>")

    assert result.is_valid, [str(error) for error in result.errors]
    assert result.grammar_version == "5.1"
    ast = ASTBuilder(result.source, "<test>").build(result.root_node)
    assert ast.statutes[0].section_number == "1"


def test_parser_rejects_unsupported_grammar_pragma():
    result = get_parser().parse("#yuho v4.0\n" + SOURCE, "<test>")

    assert result.errors
    assert result.errors[0].node_type == "GRAMMAR_PRAGMA"
    assert "unsupported grammar version" in result.errors[0].message


def test_upgrade_source_inserts_current_pragma():
    result = upgrade_source(SOURCE)

    assert result.changed
    assert result.from_version is None
    assert result.to_version == "5.1"
    assert result.source.startswith("#yuho v5.1\n")


def test_upgrade_source_without_pragma_records_default_migration():
    result = upgrade_source(SOURCE, to_version="v5.1")

    assert result.changed
    assert result.from_version is None
    assert result.to_version == "5.1"
    assert result.source.startswith("#yuho v5.1\n")


def test_upgrade_source_replaces_existing_pragma():
    result = upgrade_source("#yuho v4.0\n" + SOURCE)

    assert result.changed
    assert result.from_version == "4.0"
    assert result.source.startswith("#yuho v5.1\n")


def test_upgrade_source_obsolete_version_can_jump_to_current():
    result = upgrade_source("#yuho v4.0\n" + SOURCE, from_version="v4.0", to_version="v5.1")

    assert result.changed
    assert result.from_version == "4.0"
    assert result.to_version == "5.1"
    assert result.source.startswith("#yuho v5.1\n")
    assert "#yuho v4.0" not in result.source


def test_upgrade_cli_check_and_in_place(tmp_path):
    path = tmp_path / "sample.yh"
    path.write_text(SOURCE, encoding="utf-8")
    runner = CliRunner()

    check_result = runner.invoke(cli, ["upgrade", "--check", str(path)])
    assert check_result.exit_code == 1
    assert "upgrade required" in check_result.stderr

    upgrade_result = runner.invoke(cli, ["upgrade", "--in-place", str(path)])
    assert upgrade_result.exit_code == 0
    assert path.read_text(encoding="utf-8").startswith("#yuho v5.1\n")

    clean_result = runner.invoke(cli, ["upgrade", "--check", str(path)])
    assert clean_result.exit_code == 0
