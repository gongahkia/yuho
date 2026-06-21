"""Tests for jurisdiction-aware reference resolution."""

from __future__ import annotations

from pathlib import Path

from yuho.services.analysis import analyze_file


def _write_statute(path: Path, jurisdiction: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'statute 99 "Target" jurisdiction {jurisdiction} {{ }}\n',
        encoding="utf-8",
    )


def _messages(path: Path) -> list[str]:
    result = analyze_file(path, run_semantic=True)
    assert result.semantic_summary is not None
    return [issue.message for issue in result.semantic_summary.issues]


def test_cross_jurisdiction_reference_requires_explicit_opt_in(tmp_path: Path):
    _write_statute(tmp_path / "library" / "india_case" / "statute.yh", "india")
    source = tmp_path / "main.yh"
    source.write_text(
        """
referencing india_case;
statute 1 "Main" jurisdiction singapore { }
""",
        encoding="utf-8",
    )

    messages = _messages(source)

    assert any("cross-jurisdiction reference" in message for message in messages)
    assert any("@cross_jurisdiction" in message for message in messages)


def test_explicit_cross_jurisdiction_reference_allowed(tmp_path: Path):
    _write_statute(tmp_path / "library" / "india_case" / "statute.yh", "india")
    source = tmp_path / "main.yh"
    source.write_text(
        """
/// @cross_jurisdiction
referencing india_case;
statute 1 "Main" jurisdiction singapore { }
""",
        encoding="utf-8",
    )

    messages = _messages(source)

    assert not any("cross-jurisdiction reference" in message for message in messages)


def test_same_jurisdiction_reference_allowed(tmp_path: Path):
    _write_statute(tmp_path / "library" / "sg_case" / "statute.yh", "singapore")
    source = tmp_path / "main.yh"
    source.write_text(
        """
referencing sg_case;
statute 1 "Main" jurisdiction singapore { }
""",
        encoding="utf-8",
    )

    messages = _messages(source)

    assert not any("cross-jurisdiction reference" in message for message in messages)
