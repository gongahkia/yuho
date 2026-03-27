"""Regression tests for study-oriented generated test cases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from yuho.cli.main import cli
from yuho.verify.z3_solver import Z3_AVAILABLE


MURDER_STATUTE = (
    Path(__file__).resolve().parents[1]
    / "library"
    / "penal_code"
    / "s300_murder"
    / "statute.yh"
)


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_generate_tests_json_prioritizes_boundary_and_exception_cases() -> None:
    """JSON output should surface study cases before lower-value bulk toggles."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["generate-tests", str(MURDER_STATUTE), "-n", "6", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    case_ids = [case["case_id"] for case in payload]

    assert "s300_conviction_path" in case_ids
    assert "s300_all_of_gap_causedeath" in case_ids
    assert "s300_minimal_any_of_intent1" in case_ids
    assert any(case_id.startswith("s300_exception_") for case_id in case_ids)


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_generate_tests_json_output_is_machine_readable() -> None:
    """JSON mode should not append human summary text after the payload."""
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["generate-tests", str(MURDER_STATUTE), "-n", "3", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert len(payload) == 3
    assert payload[0]["kind"] == "happy_path"
