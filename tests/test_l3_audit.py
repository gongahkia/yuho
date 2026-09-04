"""Automated L3 triage must remain read-only and non-certifying."""

from __future__ import annotations

import subprocess

from scripts import l3_audit


def test_triage_response_requires_a_non_certifying_decision() -> None:
    assert l3_audit.parse_triage_response(
        '{"section":"415","decision":"FLAG","failed_items":[7,9],"summary":"penalty mismatch"}'
    ) == {
        "section": "415",
        "decision": "FLAG",
        "failed_items": [7, 9],
        "summary": "penalty mismatch",
    }
    assert (
        l3_audit.parse_triage_response(
            '{"section":"415","decision":"STAMP","failed_items":[],"summary":"approved"}'
        )
        is None
    )


def test_triage_dispatch_uses_read_only_codex(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["kwargs"] = kwargs
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    monkeypatch.setattr(l3_audit.subprocess, "run", fake_run)

    l3_audit.dispatch_codex("triage", timeout=1, model="gpt-5.4", reasoning="high")

    command = captured["command"]
    assert command[:5] == ["codex", "exec", "--sandbox", "read-only", "--ephemeral"]
    assert "--full-auto" not in command
    assert captured["kwargs"] == {
        "input": "triage",
        "text": True,
        "capture_output": True,
        "timeout": 1,
    }
