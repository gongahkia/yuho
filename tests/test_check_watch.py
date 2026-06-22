from __future__ import annotations

from types import SimpleNamespace

import pytest
from click.testing import CliRunner

import yuho.cli.commands.check as check_cmd
from yuho.cli.main import cli


def test_check_cli_passes_watch(monkeypatch):
    calls = {}

    def fake_run_check(file, **kwargs):
        calls["file"] = file
        calls["watch"] = kwargs["watch"]

    monkeypatch.setattr(check_cmd, "run_check", fake_run_check)

    result = CliRunner().invoke(cli, ["check", "--watch", "sample.yh"])

    assert result.exit_code == 0
    assert calls == {"file": "sample.yh", "watch": True}


def test_watch_rejects_stdin(capsys):
    with pytest.raises(SystemExit) as exc:
        check_cmd.run_check("-", watch=True)

    assert exc.value.code == 2
    assert "--watch requires a file path" in capsys.readouterr().err


def test_watch_reports_missing_watchdog(tmp_path, monkeypatch):
    def missing_watchdog():
        raise ImportError("no watchdog")

    monkeypatch.setattr(check_cmd, "_load_watchdog", missing_watchdog)

    status = check_cmd._run_watch_mode(str(tmp_path / "sample.yh"), lambda: 0)

    assert status == 2


def test_watch_missing_watchdog_message(tmp_path, monkeypatch, capsys):
    def missing_watchdog():
        raise ImportError("no watchdog")

    monkeypatch.setattr(check_cmd, "_load_watchdog", missing_watchdog)

    check_cmd._run_watch_mode(str(tmp_path / "sample.yh"), lambda: 0)

    assert "install yuho[watch] or yuho[dev]" in capsys.readouterr().err


def test_watch_event_matches_target(tmp_path):
    target = (tmp_path / "sample.yh").resolve()
    event = SimpleNamespace(src_path=str(target), dest_path=None)

    assert check_cmd._event_touches_target(event, target)
