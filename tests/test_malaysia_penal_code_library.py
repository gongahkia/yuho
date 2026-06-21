"""Malaysia Penal Code proof-of-concept library coverage."""

from __future__ import annotations

import json
from pathlib import Path

from yuho.services.analysis import analyze_file


ROOT = Path(__file__).resolve().parents[1]
MY_DIR = ROOT / "library" / "malaysia_penal_code"
RAW_PATH = MY_DIR / "_raw" / "act.json"
POC_SECTIONS = {
    "1", "2", "6", "24", "25", "299", "300", "302", "304", "307",
    "319", "320", "322", "339", "378", "379", "383", "390", "415", "420",
}


def _statute_paths() -> list[Path]:
    return sorted(
        path for path in MY_DIR.glob("s*/statute.yh")
        if path.parent.is_dir() and not path.parent.name.startswith("_")
    )


def test_malaysia_raw_contains_scraped_sections_and_sources():
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    sections = {section["number"]: section for section in raw["sections"]}

    assert raw["source"] == "agc_lom_pdf_2023"
    assert raw["official_page"] == "https://lom.agc.gov.my/act-detail.php?act=574&lang=BI"
    assert raw["as_at"] == "2023-07-04"
    assert len(sections) >= 500
    assert POC_SECTIONS <= sections.keys()


def test_malaysia_poc_contains_twenty_sections():
    paths = _statute_paths()
    numbers = {path.parent.name.split("_", 1)[0].removeprefix("s") for path in paths}

    assert len(paths) == 20
    assert numbers == POC_SECTIONS


def test_malaysia_poc_l1_l2_pass():
    for path in _statute_paths():
        result = analyze_file(path)

        assert result.is_valid, (path, result.errors)
        assert result.ast is not None, path
