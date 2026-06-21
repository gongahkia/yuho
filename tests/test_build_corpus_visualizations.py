"""Tests for corpus visualization file materialization."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_corpus", REPO / "scripts" / "build_corpus.py")
assert SPEC and SPEC.loader
build_corpus = importlib.util.module_from_spec(SPEC)
sys.modules["build_corpus"] = build_corpus
SPEC.loader.exec_module(build_corpus)


def test_write_visualization_svgs_writes_element_graph(tmp_path: Path) -> None:
    records = [{
        "section_number": "415",
        "transpiled": {"mermaid_svg": '<svg class="yuho-mermaid-svg"></svg>'},
    }]

    written = build_corpus.write_visualization_svgs(records, output_dir=tmp_path)

    assert written == [tmp_path / "s415" / "element-graph.svg"]
    assert written[0].read_text(encoding="utf-8") == '<svg class="yuho-mermaid-svg"></svg>'


def test_write_visualization_svgs_skips_missing_svg(tmp_path: Path) -> None:
    records = [{"section_number": "300", "transpiled": {"mermaid_svg": None}}]

    written = build_corpus.write_visualization_svgs(records, output_dir=tmp_path)

    assert written == []
    assert not (tmp_path / "s300").exists()
