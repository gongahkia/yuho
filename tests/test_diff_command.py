"""Regression tests for statute diff study workflows."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


REPO_ROOT = Path(__file__).resolve().parents[1]
S299_STATUTE = REPO_ROOT / "library" / "penal_code" / "s299_culpable_homicide" / "statute.yh"
S300_STATUTE = REPO_ROOT / "library" / "penal_code" / "s300_murder" / "statute.yh"


def test_diff_compares_single_statute_siblings_semantically() -> None:
    """Sibling offence comparisons should expose doctrinal differences directly."""
    runner = CliRunner()

    result = runner.invoke(cli, ["diff", str(S299_STATUTE), str(S300_STATUTE)])

    assert result.exit_code == 1
    assert "Sibling offence comparison" in result.output
    assert "Added exception: provocation" in result.output
    assert "Modified death-penalty exposure" in result.output


def test_diff_score_json_includes_penalty_and_related_section_coverage() -> None:
    """Score mode should report broader study-oriented comparison categories."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["diff", str(S300_STATUTE), str(S300_STATUTE), "--score", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    categories = payload["statutes"][0]["categories"]

    assert categories["penalty_detail"]["matched"] == 1
    assert categories["case_law"]["matched"] == 1
    assert categories["related_sections"]["matched"] == 1


def test_diff_jurisdictions_compares_section_across_corpora() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["diff", "--jurisdictions", "sg,my,pk", "300"])

    assert result.exit_code == 1
    assert "Jurisdiction diff: Section 300" in result.output
    assert "sg -> my" in result.output
    assert "sg -> pk" in result.output
    assert "Modified" in result.output


def test_diff_jurisdictions_json_reports_files_and_summaries() -> None:
    runner = CliRunner()

    result = runner.invoke(cli, ["diff", "--jurisdictions", "sg,my", "300", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.output)

    assert payload["section"] == "300"
    assert payload["jurisdictions"] == ["sg", "my"]
    assert "library/penal_code" in payload["files"]["sg"]
    assert "library/malaysia_penal_code" in payload["files"]["my"]
    assert payload["comparisons"][0]["summary"]["modified"] > 0
