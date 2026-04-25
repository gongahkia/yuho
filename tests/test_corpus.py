"""Tests for the enriched JSON corpus (Task 2a)."""

import json
from pathlib import Path

import pytest


CORPUS_DIR = Path("library/penal_code/_corpus")
INDEX = CORPUS_DIR / "index.json"
SECTIONS = CORPUS_DIR / "sections"


@pytest.fixture(scope="module")
def index():
    if not INDEX.exists():
        pytest.skip("corpus not built; run scripts/build_corpus.py")
    with INDEX.open("r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def s415():
    path = SECTIONS / "s415.json"
    if not path.exists():
        pytest.skip("s415 record not built")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


class TestIndex:
    def test_has_required_top_level_keys(self, index):
        for key in ("act", "act_code", "jurisdiction", "n_sections",
                    "totals", "generated_at", "yuho_version", "sections"):
            assert key in index, f"missing key: {key}"

    def test_section_count_matches_rows(self, index):
        assert index["n_sections"] == len(index["sections"])

    def test_pc1871(self, index):
        assert index["act_code"] == "PC1871"
        assert index["jurisdiction"] == "SG"

    def test_totals_consistent(self, index):
        totals = index["totals"]
        # L1 / L2 / L3_stamped + L3_flagged + L3_unstamped should equal n_sections
        assert (
            totals["L3_stamped"] + totals["L3_flagged"] + totals["L3_unstamped"]
        ) == index["n_sections"]
        assert totals["L1"] == index["n_sections"]
        assert totals["L2"] == index["n_sections"]


class TestSectionRecord:
    def test_has_required_top_level_keys(self, s415):
        for key in ("section_number", "section_title", "act", "jurisdiction",
                    "sso_url", "raw", "encoded", "transpiled", "coverage",
                    "references", "metadata", "provenance"):
            assert key in s415, f"missing key: {key}"

    def test_section_number(self, s415):
        assert s415["section_number"] == "415"

    def test_raw_text_nonempty(self, s415):
        assert s415["raw"]["text"]
        assert s415["raw"]["hash_sha256"]
        assert len(s415["raw"]["hash_sha256"]) == 64

    def test_encoded_yh_source_nonempty(self, s415):
        assert "statute 415" in s415["encoded"]["yh_source"]

    def test_ast_summary_has_elements(self, s415):
        ast = s415["encoded"]["ast_summary"]
        assert ast["statutes"] == 1
        assert ast["elements"] >= 4  # cheating has 4+ elements
        assert ast["illustrations"] >= 3

    def test_transpiled_english_present(self, s415):
        # English transpilation should produce non-empty output for s415.
        assert s415["transpiled"]["english"]
        assert "Cheating" in s415["transpiled"]["english"]

    def test_coverage_passes_l1_l2(self, s415):
        cov = s415["coverage"]
        assert cov["L1"] is True
        assert cov["L2"] is True

    def test_references_outgoing_includes_s24_or_s25(self, s415):
        # s415's mens-rea elements reference s24/s25 (definitions of dishonestly/fraudulently).
        outs = {e["dst"] for e in s415["references"]["outgoing"]}
        assert outs & {"24", "25"}, f"expected s24 or s25 in outgoing refs, got {outs}"

    def test_provenance_has_yuho_version(self, s415):
        assert s415["provenance"]["yuho_version"]


class TestPerSectionFiles:
    def test_section_files_exist_for_index_rows(self, index):
        # Every row in the index should have a corresponding sections/s{N}.json.
        for row in index["sections"]:
            path = SECTIONS / f"s{row['number']}.json"
            assert path.exists(), f"missing: {path}"

    def test_no_extra_section_files(self, index):
        n_index = index["n_sections"]
        n_files = sum(1 for _ in SECTIONS.glob("s*.json"))
        assert n_files == n_index, f"index says {n_index}, found {n_files} files"
