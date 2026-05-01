"""Tests for ``yuho refs --compare-libraries`` (§8 cross-jurisdiction
comparative-encoding skeleton)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from yuho.cli.commands.refs import (
    _enumerate_library_sections,
    _section_sort_key,
    run_compare_libraries,
)


def _mk_encoded_lib(root: Path, sections: list[str]) -> None:
    """Materialise a minimal `<root>/sN_*/statute.yh` library."""
    for n in sections:
        d = root / f"s{n}_test"
        d.mkdir(parents=True, exist_ok=True)
        (d / "statute.yh").write_text(
            f"statute {n} \"test\" effective 1872-01-01 {{ }}\n",
            encoding="utf-8",
        )


def _mk_raw_act(root: Path, sections: list[str]) -> None:
    raw_dir = root / "_raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "act_code": "TEST",
        "title": "Test Act",
        "scraped_at": "2026-04-30T00:00:00Z",
        "source": "test",
        "sections": [{"number": n, "marginal_note": f"s{n}", "text": "",
                       "sub_items": [], "amendments": []} for n in sections],
    }
    (raw_dir / "act.json").write_text(json.dumps(payload), encoding="utf-8")


def test_section_sort_key_handles_alpha_suffix():
    assert _section_sort_key("123") < _section_sort_key("123A")
    assert _section_sort_key("123A") < _section_sort_key("123B")
    assert _section_sort_key("123B") < _section_sort_key("124")
    assert _section_sort_key("9") < _section_sort_key("10")


def test_enumerate_encoded_library(tmp_path: Path):
    _mk_encoded_lib(tmp_path, ["1", "100", "300", "377BB"])
    sections, kind = _enumerate_library_sections(tmp_path)
    assert kind == "encoded"
    assert sections == ["1", "100", "300", "377BB"]


def test_enumerate_raw_act_library(tmp_path: Path):
    _mk_raw_act(tmp_path, ["1", "300", "509"])
    sections, kind = _enumerate_library_sections(tmp_path)
    assert kind == "raw_act"
    assert sections == ["1", "300", "509"]


def test_enumerate_missing_library(tmp_path: Path):
    sections, kind = _enumerate_library_sections(tmp_path / "does-not-exist")
    assert kind == "missing"
    assert sections == []


def test_enumerate_empty_library(tmp_path: Path):
    (tmp_path / "_misc").mkdir()
    sections, kind = _enumerate_library_sections(tmp_path)
    assert kind == "empty"
    assert sections == []


def test_enumerate_skips_underscore_dirs(tmp_path: Path):
    _mk_encoded_lib(tmp_path, ["1", "2"])
    (tmp_path / "_corpus").mkdir()
    (tmp_path / "_coverage").mkdir()
    sections, kind = _enumerate_library_sections(tmp_path)
    assert kind == "encoded"
    assert sections == ["1", "2"]


def test_compare_libraries_two_overlapping(tmp_path: Path, capsys):
    a = tmp_path / "lib_a"
    b = tmp_path / "lib_b"
    _mk_encoded_lib(a, ["1", "100", "300", "377BB"])
    _mk_raw_act(b, ["1", "300", "509"])
    rc = run_compare_libraries((a, b), json_output=True)
    assert rc == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["full_intersection"] == ["1", "300"]
    assert payload["full_intersection_count"] == 2
    pair = payload["pairs"][0]
    assert pair["shared"] == ["1", "300"]
    assert pair["only_a"] == ["100", "377BB"]
    assert pair["only_b"] == ["509"]


def test_compare_libraries_no_usable_returns_1(tmp_path: Path, capsys):
    rc = run_compare_libraries(
        (tmp_path / "missing_a", tmp_path / "missing_b"),
        json_output=False,
    )
    assert rc == 1


def test_compare_libraries_human_output_lists_kinds(tmp_path: Path, capsys):
    a = tmp_path / "lib_a"
    b = tmp_path / "lib_b"
    _mk_encoded_lib(a, ["1"])
    _mk_raw_act(b, ["1"])
    rc = run_compare_libraries((a, b), json_output=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[encoded]" in out
    assert "[raw_act]" in out
    assert "shared:  1" in out
    assert "Phase 2" in out
