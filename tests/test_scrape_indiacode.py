"""Tests for the IPC scraper (`scripts/scrape_indiacode.py`).

Network-free: every test runs the parsers against committed HTML
fixtures under ``tests/fixtures/indiacode_*.html``. The fixtures
were drafted against AdvocateKhoj's typical IPC-section page shape;
if the upstream HTML changes, the fixtures (not the parser) should
be updated to match, then the parser adjusted from there.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load_fixture(name: str) -> str:
    return (Path(__file__).resolve().parent / "fixtures" / name).read_text(
        encoding="utf-8",
    )


def _has_bs4() -> bool:
    try:
        import bs4  # noqa: F401
    except ImportError:
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _has_bs4(), reason="beautifulsoup4 not installed"
)


def test_advocatekhoj_section_parses_simple_section():
    import scrape_indiacode as scraper
    html = _load_fixture("indiacode_advocatekhoj_s302.html")
    sec = scraper.parse_advocatekhoj_section(html, "302")
    assert sec is not None
    assert sec.number == "302"
    assert "Punishment for murder" in sec.marginal_note
    assert "death" in sec.text or "imprisonment for life" in sec.text
    # The Act-of-1870 amendment marker should land in the amendments list.
    assert any("Act 27 of 1870" in a.marker for a in sec.amendments)


def test_advocatekhoj_section_classifies_subitems():
    """s378 ships with 2 explanations + 2 illustrations. The classifier
    must surface them with the right `kind` rather than dump them into
    the body text."""
    import scrape_indiacode as scraper
    html = _load_fixture("indiacode_advocatekhoj_s378.html")
    sec = scraper.parse_advocatekhoj_section(html, "378")
    assert sec is not None
    explanations = [s for s in sec.sub_items if s.kind == "explanation"]
    illustrations = [s for s in sec.sub_items if s.kind == "illustration"]
    assert len(explanations) >= 2, sec.sub_items
    assert len(illustrations) >= 2, sec.sub_items


def test_advocatekhoj_index_extracts_section_links_and_dedupes():
    import scrape_indiacode as scraper
    html = _load_fixture("indiacode_advocatekhoj_index.html")
    items = scraper.parse_advocatekhoj_index(html)
    nums = [it["section_number"] for it in items]
    # Exactly the unique sections in the fixture, in source order.
    assert nums == ["1", "299", "300", "302", "304", "304A", "378", "415"], nums
    # Each entry has a non-empty title and a back-resolvable href.
    for it in items:
        assert it["title"]
        assert "indianpenalcode/" in it["href"]


def test_section_dataclass_round_trips_via_dict():
    """The output JSON shape must mirror scrape_sso.py so the same
    downstream encoder pipeline works on both libraries."""
    from dataclasses import asdict
    import scrape_indiacode as scraper
    sec = scraper.Section(
        number="378",
        marginal_note="Theft",
        text="Whoever takes…",
        sub_items=[scraper.SubItem(kind="illustration", label="a", text="…")],
        amendments=[scraper.Amendment(marker="[Act 1 of 1870]")],
        anchor_id=None,
    )
    payload = asdict(sec)
    assert payload["number"] == "378"
    assert payload["sub_items"][0]["kind"] == "illustration"
    assert payload["amendments"][0]["marker"] == "[Act 1 of 1870]"


def test_backend_dispatch_rejects_unknown_source():
    import scrape_indiacode as scraper
    with pytest.raises(SystemExit):
        scraper._backend("unknown-backend")


def test_backend_dispatch_returns_callables():
    import scrape_indiacode as scraper
    for name in ("advocatekhoj", "indiacode"):
        backend = scraper._backend(name)
        assert callable(backend["parse_index"])
        assert callable(backend["parse_section"])
        assert callable(backend["section_url"])
        assert backend["base_url"].startswith("https://")


def test_http_client_throttles_requests(monkeypatch):
    """Two consecutive fetches must respect the configured delay."""
    import scrape_indiacode as scraper

    timeline: list[float] = []

    def fake_urlopen(req, timeout=30.0):
        import io

        class _Resp:
            headers = type("H", (), {"get_content_charset": lambda self: "utf-8"})()

            def __enter__(self_): return self_

            def __exit__(self_, *a): pass

            def read(self_): return b"<html></html>"

        timeline.append(0.0)
        return _Resp()

    sleeps: list[float] = []
    monkeypatch.setattr(scraper.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(scraper.time, "sleep", lambda s: sleeps.append(s))

    client = scraper.HttpClient(delay=2.0)
    client.fetch("http://example.test/a")
    client.fetch("http://example.test/b")
    # Second fetch should have triggered a sleep close to delay (the
    # first fetch leaves _last set, and the second's _throttle waits
    # for the gap to elapse).
    assert any(s > 1.0 for s in sleeps), sleeps


def test_section_classifier_handles_subsection_labels():
    import scrape_indiacode as scraper
    html = """
    <h2>Section 511. Punishment for attempting to commit offences</h2>
    <div class="content">
      <p>Whoever attempts to commit an offence punishable by this Code...</p>
      <p>(1) Subsection one body text.</p>
      <p>(2A) Subsection two-A body text.</p>
    </div>
    """
    sec = scraper.parse_advocatekhoj_section(html, "511")
    assert sec is not None
    subs = [s for s in sec.sub_items if s.kind == "subsection"]
    labels = sorted(s.label for s in subs)
    assert labels == ["1", "2A"], subs
