"""Automated L3 triage must remain read-only and non-certifying."""

from __future__ import annotations

import subprocess
import sys

from scripts import apply_flag_fix, coverage_report, l3_audit, review_flags


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


def test_flag_fix_tool_only_generates_non_certifying_proposals() -> None:
    proposal = apply_flag_fix.render(
        "415",
        {"marginal_note": "Cheating", "anchor_id": "pr415-"},
        "PC1871",
    )

    assert "must not" in proposal
    assert "remove `_L3_FLAG.md` automatically" in proposal
    assert "create an L3 stamp" in proposal

    result = subprocess.run(
        [sys.executable, str(l3_audit.REPO / "scripts" / "apply_flag_fix.py"), "--dispatch"],
        cwd=l3_audit.REPO,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode != 0
    assert "--dispatch" in result.stderr


def test_flag_review_summary_is_an_advisory_not_a_stamp_instruction() -> None:
    summary = review_flags.render_summary({}, {})

    assert "automated triage, not human-review evidence" in summary
    assert "REVIEW_REQUIRED" in summary
    assert "STAMP_OVERRIDE" not in summary
    assert "Do not change `metadata.toml`" in summary


def test_coverage_report_labels_l3_as_legacy_metadata(tmp_path) -> None:
    output = tmp_path / "coverage.md"
    json_output = tmp_path / "coverage.json"
    coverage_report.emit_md(
        output,
        [],
        coverage_report.Totals(raw_sections=1),
        {"title": "Test Act", "act_code": "TEST", "scraped_at": None, "valid_date": None},
    )

    rendered = output.read_text(encoding="utf-8")
    assert "L3** — legacy stamp" in rendered
    assert "not human-review or legal-certification evidence" in rendered

    coverage_report.emit_json(
        json_output,
        [],
        coverage_report.Totals(raw_sections=1),
        {"title": "Test Act", "act_code": "TEST", "scraped_at": None, "valid_date": None},
    )
    generated = json_output.read_text(encoding="utf-8")
    assert "not human-review" in generated
    assert "+00:00" in generated
