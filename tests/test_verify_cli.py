from __future__ import annotations

import json

from click.testing import CliRunner

from yuho.cli.main import cli


def test_verify_capabilities_json_reports_backend_status() -> None:
    result = CliRunner().invoke(cli, ["verify", "--capabilities", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    capabilities = payload["capabilities"]

    assert capabilities["z3"]["status"] == "conformance-tested"
    assert capabilities["alloy"]["status"] == "experimental"
    assert capabilities["lean"]["status"] == "spec/proof"
    assert capabilities["combined"]["status"] == "aggregate"

    for backend in ("z3", "alloy", "lean", "combined"):
        assert capabilities[backend]["role"]
        assert capabilities[backend]["unsupported_features"]


def test_verify_capabilities_text_reports_status_labels() -> None:
    result = CliRunner().invoke(cli, ["verify", "--capabilities"])

    assert result.exit_code == 0
    assert "Alloy:" in result.output
    assert "[experimental]" in result.output
    assert "Z3:" in result.output
    assert "[conformance-tested]" in result.output
    assert "Lean:" in result.output
    assert "[spec/proof]" in result.output
