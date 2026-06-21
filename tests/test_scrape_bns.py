"""Tests for the BNS India Code scraper."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _has_bs4() -> bool:
    try:
        import bs4  # noqa: F401
    except ImportError:
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _has_bs4(), reason="beautifulsoup4 not installed"
)


def test_parse_index_extracts_bns_section_links():
    import scrape_bns as scraper

    html = """
    <a href="/show-data?abv=CEN&actid=A&orderno=1&orgactid=A&sectionId=90366&sectionno=1&statehandle=123456789%2F1362">
      Section 1. Short title, commencement and application.
    </a>
    <a href="/show-data?abv=CEN&actid=A&orderno=100&orgactid=A&sectionId=90465&sectionno=100&statehandle=123456789%2F1362">
      Section 100. Culpable homicide.
    </a>
    """

    items = scraper.parse_index(html)

    assert [item["section_number"] for item in items] == ["1", "100"]
    assert items[0]["title"] == "Short title, commencement and application."
    assert items[1]["section_id"] == "90465"


def test_parse_section_payload_classifies_content():
    import scrape_bns as scraper

    payload = {
        "content": """
        <span></span>(1) This Act may be called the Bharatiya Nyaya Sanhita, 2023.</br><hr/>
        <span></span>(a) any citizen of India;</br><hr/>
        <i>Explanation.</i>--In this section, offence includes an act outside India.</br><hr/>
        Illustration.</br><hr/>
        A commits murder outside India.</br><hr/>
        """,
        "footnote": "</br><hr/>1. 1st July, 2024, vide notification.</br><hr/>",
    }

    section = scraper.parse_section_payload(
        section_number="1",
        marginal_note="Short title, commencement and application.",
        section_id="90366",
        payload=payload,
    )

    assert section.number == "1"
    assert section.anchor_id == "90366"
    assert any(item.kind == "subsection" and item.label == "1" for item in section.sub_items)
    assert any(item.kind == "item" and item.label == "a" for item in section.sub_items)
    assert any(item.kind == "explanation" for item in section.sub_items)
    assert any(item.kind == "illustration" for item in section.sub_items)
    assert section.text == "A commits murder outside India."
    assert section.amendments[0].marker.startswith("1. 1st July")


def test_act_dataclass_shape_matches_raw_schema():
    from dataclasses import asdict
    import scrape_bns as scraper

    act = scraper.Act(
        act_code="BNS2023",
        title="The Bharatiya Nyaya Sanhita, 2023",
        url=scraper.INDEX_URL,
        scraped_at="2026-06-21T00:00:00Z",
        source="indiacode",
        act_id=scraper.ACT_ID,
        sections=[scraper.Section(number="1", marginal_note="Title", text="Body")],
    )

    payload = asdict(act)

    assert payload["act_code"] == "BNS2023"
    assert payload["source"] == "indiacode"
    assert payload["sections"][0]["number"] == "1"
