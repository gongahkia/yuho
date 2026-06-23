from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


def test_doctor_json_reports_parser_and_sample(tmp_path: Path) -> None:
    sample = tmp_path / "sample.yh"
    sample.write_text(
        """
        statute 1 "Sample" {
            elements {
                actus_reus act := "does an act";
            }
        }
        """,
        encoding="utf-8",
    )

    result = CliRunner().invoke(cli, ["doctor", "--json", "--sample", str(sample)])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    checks = {check["name"]: check for check in payload["checks"]}
    assert payload["ok"] is True
    assert checks["parser"]["status"] == "ok"
    assert checks["sample"]["status"] == "ok"


def test_doctor_strict_fails_on_missing_sample(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yh"

    result = CliRunner().invoke(cli, ["doctor", "--strict", "--sample", str(missing)])

    assert result.exit_code == 1
    assert "[WARN] sample:" in result.output
