from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from yuho.cli.main import cli
from yuho.verify.z3_solver import Z3_AVAILABLE


def test_verify_capabilities_json_reports_backend_status() -> None:
    result = CliRunner().invoke(cli, ["verify", "--capabilities", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    capabilities = payload["capabilities"]

    assert capabilities["z3"]["status"] == "conformance-tested"
    assert capabilities["alloy"]["status"] == "secondary-explicit-unsupported"
    assert capabilities["lean"]["status"] == "spec/proof"
    assert capabilities["combined"]["status"] == "aggregate"

    for backend in ("z3", "alloy", "lean", "combined"):
        assert capabilities[backend]["role"]
        assert capabilities[backend]["unsupported_features"]


def test_verify_capabilities_text_reports_status_labels() -> None:
    result = CliRunner().invoke(cli, ["verify", "--capabilities"])

    assert result.exit_code == 0
    assert "Alloy:" in result.output
    assert "[secondary-explicit-unsupported]" in result.output
    assert "Z3:" in result.output
    assert "[conformance-tested]" in result.output
    assert "Lean:" in result.output
    assert "[spec/proof]" in result.output


def test_verify_reference_date_rejects_bad_iso_date() -> None:
    result = CliRunner().invoke(
        cli,
        ["verify", "--capabilities", "--reference-date", "2024-02-31"],
    )

    assert result.exit_code == 2
    assert "invalid --reference-date" in result.output


def test_verify_z3_reports_unsupported_case_law() -> None:
    if not Z3_AVAILABLE:
        pytest.skip("z3-solver package not installed")
    runner = CliRunner()
    with runner.isolated_filesystem():
        path = Path("case.yh")
        path.write_text(
            """
            statute 1 "Case" {
                elements { actus_reus act := "Act"; }
                caselaw "A v B" "2026 SGCA 1" {
                    "Narrow reading"
                    element act
                }
            }
            """,
            encoding="utf-8",
        )

        result = runner.invoke(cli, ["verify", "--engine", "z3", str(path)])

    assert result.exit_code == 2
    assert "z3 verification unsupported" in result.output
    assert "s1: case-law semantics" in result.output
