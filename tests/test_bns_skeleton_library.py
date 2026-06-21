"""BNS skeleton library coverage."""

from __future__ import annotations

from pathlib import Path

from yuho.services.analysis import analyze_file


ROOT = Path(__file__).resolve().parents[1]
BNS_DIR = ROOT / "library" / "bharatiya_nyaya_sanhita"


def _statute_paths() -> list[Path]:
    return sorted(
        path for path in BNS_DIR.glob("s*/statute.yh")
        if path.parent.is_dir() and not path.parent.name.startswith("_")
    )


def test_bns_skeleton_contains_358_sections():
    assert len(_statute_paths()) == 358


def test_bns_skeleton_l1_l2_pass():
    for path in _statute_paths():
        result = analyze_file(path)

        assert result.is_valid, (path, result.errors)
        assert result.ast is not None, path
