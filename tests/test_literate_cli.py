"""CLI tests for literate statute reports."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


def _make_literate_workspace(tmp_path: Path) -> Path:
    root = tmp_path / "literate"
    result = CliRunner().invoke(cli, ["init", "--template", "statute-literate", str(root)])
    assert result.exit_code == 0, result.output
    return root


def test_literate_writes_markdown_report_with_trace(tmp_path: Path) -> None:
    root = _make_literate_workspace(tmp_path)
    output = root / "out" / "literate.md"

    result = CliRunner().invoke(
        cli,
        [
            "literate",
            str(root / "statute.yh"),
            "--legal-text",
            str(root / "legal-text.md"),
            "--facts",
            str(root / "facts.json"),
            "-o",
            str(output),
        ],
    )

    assert result.exit_code == 0
    report = output.read_text(encoding="utf-8")
    assert "## Legal Text" in report
    assert "## Yuho Source" in report
    assert "`legal-text.md#p1`" in report
    assert "## Executable Element Spans" in report
    assert "`representation`: lines" in report
    assert "## Result Trace" in report
    assert "Section 1 is satisfied." in report


def test_literate_renders_html_to_stdout(tmp_path: Path) -> None:
    root = _make_literate_workspace(tmp_path)

    result = CliRunner().invoke(
        cli,
        [
            "literate",
            str(root / "statute.yh"),
            "--legal-text",
            str(root / "legal-text.md"),
            "--format",
            "html",
        ],
    )

    assert result.exit_code == 0
    assert "<title>Yuho Literate Report</title>" in result.output
    assert "legal-text.md#p1" in result.output
    assert "<h2>Executable Element Spans</h2>" in result.output
    assert "<code>representation</code>" in result.output


def test_literate_aligns_paragraphs_when_no_source_anchors(tmp_path: Path) -> None:
    statute = tmp_path / "statute.yh"
    statute.write_text(
        """
statute 1 "No Anchors" {
  elements {
    actus_reus deception := "Deceives another person";
    circumstance harm := "Causes financial harm";
  }
}
""",
        encoding="utf-8",
    )
    legal_text = tmp_path / "legal.md"
    legal_text.write_text(
        "A person deceives another person.\n\nThe conduct causes financial harm.",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        [
            "literate",
            str(statute),
            "--legal-text",
            str(legal_text),
        ],
    )

    assert result.exit_code == 0
    assert "## Paragraph Alignment" in result.output
    assert "`deception`: paragraph 1 (confidence" in result.output
    assert "`harm`: paragraph 2 (confidence" in result.output
    assert "matched terms:" in result.output
