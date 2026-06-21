from __future__ import annotations

from pathlib import Path

from yuho.services import analysis


SOURCE = """
statute 1 "Demo" {
    elements {
        actus_reus taking := "takes";
        mens_rea intent := "intends";
    }
}
"""


def test_analyze_file_reuses_disk_cache_without_reparsing(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("YUHO_CACHE_DIR", str(tmp_path / "cache"))
    statute = tmp_path / "statute.yh"
    statute.write_text(SOURCE, encoding="utf-8")

    first = analysis.analyze_file(statute, run_semantic=False)
    assert first.is_valid
    assert first.cache_hit is False

    parser = analysis.get_parser()

    def fail_parse(*_args, **_kwargs):
        raise AssertionError("cache miss reparsed source")

    monkeypatch.setattr(parser, "parse", fail_parse)
    second = analysis.analyze_file(statute, run_semantic=False)

    assert second.cache_hit is True
    assert second.tree is None
    assert second.ast is not None
    assert second.ast_summary == first.ast_summary


def test_analysis_cache_is_keyed_by_stage_options(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("YUHO_CACHE_DIR", str(tmp_path / "cache"))
    statute = tmp_path / "statute.yh"
    statute.write_text(SOURCE, encoding="utf-8")

    syntax = analysis.analyze_file(statute, run_semantic=False)
    semantic = analysis.analyze_file(statute, run_semantic=True)
    semantic_again = analysis.analyze_file(statute, run_semantic=True)

    assert syntax.cache_hit is False
    assert semantic.cache_hit is False
    assert semantic_again.cache_hit is True
    assert semantic_again.semantic_checked is True
