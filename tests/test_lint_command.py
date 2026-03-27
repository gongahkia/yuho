"""Regression tests for lint command fixes."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


SOURCE_WITH_FIXABLE_WARNINGS = """statute 12 {
    elements {
        actus_reus act := "Acts";
        mens_rea intent := "Intends";
    }

    penalty {
        imprisonment := 0 days .. 1 years;
    }

    illustration example {
        ""
    }
}
"""


def test_lint_fix_applies_safe_rewrites_and_clears_warnings(tmp_path: Path) -> None:
    """`yuho lint --fix` should repair supported low-risk warnings in place."""
    runner = CliRunner()
    statute_path = tmp_path / "fixable.yh"
    statute_path.write_text(SOURCE_WITH_FIXABLE_WARNINGS, encoding="utf-8")

    lint_result = runner.invoke(cli, ["lint", str(statute_path)])
    assert lint_result.exit_code == 2
    assert "[missing-title]" in lint_result.output
    assert "[empty-illustration]" in lint_result.output

    fix_result = runner.invoke(cli, ["lint", str(statute_path), "--fix"])
    assert fix_result.exit_code == 0
    assert "Fixed 2 issue(s)" in fix_result.output
    assert "missing-title" in fix_result.output
    assert "empty-illustration" in fix_result.output

    updated = statute_path.read_text(encoding="utf-8")
    assert 'statute 12 "Untitled Section 12"' in updated
    assert '"Illustration pending."' in updated

    clean_result = runner.invoke(cli, ["lint", str(statute_path)])
    assert clean_result.exit_code == 0
    assert "No issues found" in clean_result.output
