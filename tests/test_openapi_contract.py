"""Decision-service OpenAPI contract checks."""

from __future__ import annotations

from pathlib import Path


OPENAPI = Path("docs/researcher/openapi.yaml")


def test_openapi_contract_exposes_decision_paths() -> None:
    text = OPENAPI.read_text(encoding="utf-8")

    assert "openapi: 3.1.0" in text
    assert "title: Yuho Decision Service Contract" in text
    assert "  /healthz:" in text
    assert "  /evaluate:" in text
    assert "  /verify:" in text
    assert "operationId: evaluateStatute" in text
    assert "operationId: verifyStatute" in text


def test_openapi_contract_has_request_response_schemas() -> None:
    text = OPENAPI.read_text(encoding="utf-8")

    for schema in [
        "EvaluateRequest",
        "EvaluateResponse",
        "VerifyRequest",
        "VerifyResponse",
        "TraceStep",
        "Diagnostics",
    ]:
        assert f"    {schema}:" in text
    assert "enum: [combined, z3, alloy]" in text
    assert "enum: [ok, unsupported, counterexample, error]" in text
