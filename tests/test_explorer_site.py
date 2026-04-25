"""Tests for the explorer-site static generator.

Two tiers, like the browser-extension test:

1. **Generator** (always runs): the build script imports cleanly, and the
   page renderers produce well-formed HTML.
2. **Built-site** (skipped if ``editors/explorer-site/build/`` doesn't
   exist): walk every emitted HTML file, parse it, and verify internal
   links resolve, sitemap covers all pages, etc.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Set

import pytest


REPO = Path(__file__).resolve().parent.parent
SITE = REPO / "editors" / "explorer-site"
BUILD = SITE / "build"


# ---------------------------------------------------------------------------
# Tier 1: generator-side checks
# ---------------------------------------------------------------------------


class TestGenerator:
    def test_module_imports(self):
        sys.path.insert(0, str(SITE))
        try:
            import build  # noqa: F401
        finally:
            sys.path.pop(0)

    def test_renders_section_with_minimal_record(self):
        sys.path.insert(0, str(SITE))
        try:
            import build as b
            rec = {
                "section_number": "415",
                "section_title": "Cheating",
                "raw": {"text": "raw text", "hash_sha256": "abcdef" * 8},
                "encoded": {"yh_source": "statute s415 {}", "ast_summary": {}},
                "transpiled": {"english": "EN", "mermaid_svg": "<svg></svg>"},
                "coverage": {"L1": True, "L2": True, "L3": "stamped"},
                "references": {"outgoing": [], "incoming": []},
                "metadata": {"summary": "Cheating in brief."},
                "provenance": {"yuho_version": "5.1.0",
                               "generated_at": "2026-04-25T00:00:00Z"},
                "sso_url": "https://sso.agc.gov.sg/Act/PC1871",
            }
            html = b.render_section(
                rec,
                prev_rec={"number": "414", "title": "Prev"},
                next_rec={"number": "416", "title": "Next"},
            )
            # Anchors must be on every present h2.
            for aid in ("summary", "canonical", "english", "structural",
                        "refs-out", "refs-in", "diagram", "source"):
                assert f'id="{aid}"' in html, f"missing anchor #{aid}"
            assert 'class="breadcrumb"' in html
            assert 'class="prevnext"' in html
            assert "/s/414.html" in html
            assert "/s/416.html" in html
            assert "<svg></svg>" in html
        finally:
            sys.path.pop(0)


# ---------------------------------------------------------------------------
# Tier 2: built-site walker
# ---------------------------------------------------------------------------


def _ensure_built() -> bool:
    """Skip-safe check that the build dir exists with at least one section page."""
    return BUILD.exists() and (BUILD / "index.html").exists() and \
           any((BUILD / "s").glob("*.html"))


@pytest.fixture(scope="module")
def built_site():
    if not _ensure_built():
        pytest.skip("explorer-site not built; run editors/explorer-site/build.py")
    return BUILD


class _LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = []

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "a" and "href" in d:
            self.hrefs.append(d["href"])
        if "id" in d:
            self.ids.append(d["id"])


def _all_built_pages(build_dir: Path):
    yield from build_dir.glob("*.html")
    yield from (build_dir / "s").glob("*.html")


class TestBuiltSite:
    def test_top_level_pages_present(self, built_site):
        for name in ("index.html", "coverage.html", "flags.html",
                     "about.html", "404.html",
                     "sitemap.xml", "robots.txt"):
            assert (built_site / name).exists(), f"missing {name}"

    def test_static_assets_present(self, built_site):
        for name in ("style.css", "search.js", "index.json", "search-index.json"):
            assert (built_site / "static" / name).exists(), f"missing static/{name}"

    def test_section_count_matches_index(self, built_site):
        with (built_site / "static" / "index.json").open() as f:
            index = json.load(f)
        section_pages = list((built_site / "s").glob("*.html"))
        assert len(section_pages) == index["n_sections"], (
            f"index claims {index['n_sections']} sections, "
            f"build has {len(section_pages)} pages"
        )

    def test_every_section_in_index_has_a_page(self, built_site):
        with (built_site / "static" / "index.json").open() as f:
            index = json.load(f)
        for row in index["sections"]:
            assert (built_site / "s" / f"{row['number']}.html").exists(), \
                f"missing /s/{row['number']}.html"

    def test_every_html_page_parses(self, built_site):
        for path in _all_built_pages(built_site):
            text = path.read_text(encoding="utf-8")
            parser = _LinkExtractor()
            parser.feed(text)
            assert text.lstrip().startswith("<!DOCTYPE html>"), \
                f"{path.relative_to(built_site)} missing doctype"
            # Header + footer must be present.
            assert '<header class="site">' in text, f"{path.name} missing header"
            assert '<footer class="site">' in text, f"{path.name} missing footer"

    def test_internal_section_links_resolve(self, built_site):
        existing: Set[str] = {p.name for p in (built_site / "s").glob("*.html")}
        broken = []
        for path in _all_built_pages(built_site):
            parser = _LinkExtractor()
            parser.feed(path.read_text(encoding="utf-8"))
            for href in parser.hrefs:
                m = re.match(r"/s/([^./#?]+)\.html", href)
                if not m:
                    continue
                target = f"{m.group(1)}.html"
                if target not in existing:
                    broken.append((path.name, href))
        assert not broken, f"broken /s/<n>.html links: {broken[:10]}"

    def test_sitemap_covers_every_section(self, built_site):
        sm = (built_site / "sitemap.xml").read_text(encoding="utf-8")
        with (built_site / "static" / "index.json").open() as f:
            index = json.load(f)
        for row in index["sections"]:
            needle = f"/s/{row['number']}.html"
            assert needle in sm, f"sitemap missing {needle}"

    def test_robots_references_sitemap(self, built_site):
        robots = (built_site / "robots.txt").read_text(encoding="utf-8")
        assert "Sitemap:" in robots
        assert "/sitemap.xml" in robots

    def test_404_present(self, built_site):
        text = (built_site / "404.html").read_text(encoding="utf-8")
        assert "404" in text
        assert "/index.html" in text

    def test_section_pages_have_anchors_and_nav(self, built_site):
        # Pick one well-known section.
        s415 = (built_site / "s" / "415.html")
        if not s415.exists():
            pytest.skip("s415 not built")
        text = s415.read_text(encoding="utf-8")
        for aid in ("canonical", "structural", "refs-out", "refs-in", "source"):
            assert f'id="{aid}"' in text, f"s415 missing anchor #{aid}"
        assert 'class="breadcrumb"' in text
        assert 'class="prevnext"' in text

    def test_provenance_footer_present(self, built_site):
        text = (built_site / "s" / "415.html").read_text(encoding="utf-8")
        assert "raw SHA-256" in text
        assert "yuho " in text  # version stamp
