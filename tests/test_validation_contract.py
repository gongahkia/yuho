"""Regression tests for phase-aware validation contracts."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from yuho.api.websocket import handle_parse, handle_validate
from yuho.cli.commands.api import YuhoAPIHandler
from yuho.cli.main import cli


SEMANTICALLY_INVALID_SOURCE = """
fn f() : int {
    return unknown_var;
}
"""

VALID_SOURCE = """
statute 415 "Cheating" {
    elements {
        actus_reus deception := "Deceives a person";
    }
}
"""


def _invoke_api(method_name: str, data: dict[str, object]) -> tuple[int, object]:
    """Call an API handler method and capture the response."""
    handler = object.__new__(YuhoAPIHandler)
    captured: dict[str, object] = {}

    def fake_send_json_response(status: int, response: object) -> None:
        captured["status"] = status
        captured["response"] = response

    handler._send_json_response = fake_send_json_response  # type: ignore[attr-defined]
    getattr(handler, method_name)(data)
    return captured["status"], captured["response"]


def test_cli_check_runs_semantic_validation_by_default(tmp_path: Path) -> None:
    """`yuho check` should fail on parse-valid, semantic-invalid input."""
    runner = CliRunner()
    source_path = tmp_path / "broken.yh"
    source_path.write_text(SEMANTICALLY_INVALID_SOURCE, encoding="utf-8")

    result = runner.invoke(cli, ["check", str(source_path)])

    assert result.exit_code == 1
    assert "semantic=FAIL" in result.output
    assert "Undeclared identifier 'unknown_var'" in result.output


def test_cli_check_syntax_only_skips_semantic_validation(tmp_path: Path) -> None:
    """`yuho check --syntax-only` should preserve parse-only behavior."""
    runner = CliRunner()
    source_path = tmp_path / "broken.yh"
    source_path.write_text(SEMANTICALLY_INVALID_SOURCE, encoding="utf-8")

    result = runner.invoke(cli, ["check", "--syntax-only", str(source_path)])

    assert result.exit_code == 0
    assert "semantic=SKIP" in result.output


def test_cli_explain_rejects_semantic_invalid_source(tmp_path: Path) -> None:
    """`yuho explain` should not explain semantically invalid models."""
    runner = CliRunner()
    source_path = tmp_path / "broken.yh"
    source_path.write_text(SEMANTICALLY_INVALID_SOURCE, encoding="utf-8")

    result = runner.invoke(cli, ["explain", str(source_path), "--no-llm"])

    assert result.exit_code == 1
    assert "Undeclared identifier 'unknown_var'" in result.output


def test_websocket_validate_returns_phase_aware_semantic_payload() -> None:
    """WebSocket validate should expose semantic phase status explicitly."""
    payload = handle_validate({"source": SEMANTICALLY_INVALID_SOURCE})

    assert payload["parse_valid"] is True
    assert payload["ast_valid"] is True
    assert payload["semantic_checked"] is True
    assert payload["semantic_valid"] is False
    assert any(item["stage"] == "semantic" for item in payload["errors"])


def test_websocket_parse_returns_parse_and_ast_phase_status() -> None:
    """WebSocket parse should expose parse and AST status without semantics."""
    payload = handle_parse({"source": VALID_SOURCE})

    assert payload["valid"] is True
    assert payload["parse_valid"] is True
    assert payload["ast_valid"] is True
    assert payload["semantic_checked"] is False


def test_api_validate_runs_semantic_validation() -> None:
    """REST validate should fail semantic-invalid input with phase metadata."""
    status, response = _invoke_api(
        "_handle_validate",
        {"source": SEMANTICALLY_INVALID_SOURCE, "filename": "broken.yh"},
    )

    assert status == 422
    assert response.success is False
    assert response.data["parse_valid"] is True
    assert response.data["semantic_checked"] is True
    assert response.data["semantic_valid"] is False


def test_api_parse_reports_phase_status_without_semantic_checks() -> None:
    """REST parse should keep semantic analysis disabled while exposing phases."""
    status, response = _invoke_api(
        "_handle_parse",
        {"source": VALID_SOURCE, "filename": "valid.yh"},
    )

    assert status == 200
    assert response.success is True
    assert response.data["parse_valid"] is True
    assert response.data["ast_valid"] is True
    assert response.data["semantic_checked"] is False
