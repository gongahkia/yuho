from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


VALID_SOURCE = '''
statute 1 "Demo" {
    elements { actus_reus act := "acts"; }
}
'''


def test_ci_report_writes_aggregate_json_and_fails_for_invalid_sources(tmp_path: Path) -> None:
    sources = tmp_path / "sources"
    sources.mkdir()
    (sources / "valid.yh").write_text(VALID_SOURCE, encoding="utf-8")
    (sources / "invalid.yh").write_text("statute", encoding="utf-8")
    output = tmp_path / "report.json"

    result = CliRunner().invoke(cli, ["ci-report", str(sources), "--format", "json", "-o", str(output)])

    assert result.exit_code == 1, result.output
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["version"] == "yuho-ci-report-v1"
    assert report["ok"] is False
    assert report["summary"]["files"] == 2
    assert report["summary"]["errors"] > 0
    assert {item["file"] for item in report["diagnostics"] if item["severity"] == "error"} == {
        "invalid.yh"
    }


def test_ci_report_writes_sarif_for_a_clean_directory(tmp_path: Path) -> None:
    (tmp_path / "valid.yh").write_text(VALID_SOURCE, encoding="utf-8")
    output = tmp_path / "report.sarif"

    result = CliRunner().invoke(cli, ["ci-report", str(tmp_path), "-o", str(output)])

    assert result.exit_code == 0, result.output
    sarif = json.loads(output.read_text(encoding="utf-8"))
    assert sarif["version"] == "2.1.0"
    assert all(result["level"] != "error" for result in sarif["runs"][0]["results"])
