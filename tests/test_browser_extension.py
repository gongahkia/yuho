"""Tests for the Yuho browser extension.

Two tiers:

1. **Structural** (always runs): manifest validity, JS syntax check via
   ``node -c``, presence of expected feature regions in content.js.
2. **Integration** (runs only if Playwright + Chromium are installed):
   loads the unpacked extension into a real Chromium tab, navigates to
   a synthetic SSO-shaped fixture page, asserts that badges appear and
   the panel opens.

The integration tier is skipped on CI runners that don't have a
browser to drive. Run it locally with::

    .venv-lsp/bin/playwright install chromium
    .venv-lsp/bin/pytest tests/test_browser_extension.py -v
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
EXT = REPO / "editors" / "browser-yuho"


# ---------------------------------------------------------------------------
# Tier 1: structural checks (always runs)
# ---------------------------------------------------------------------------


class TestManifests:
    def test_chrome_manifest_validates_as_json(self):
        with (EXT / "manifest.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["manifest_version"] == 3
        assert data["name"]
        assert data["version"]
        for key in ("permissions", "host_permissions", "content_scripts",
                    "background", "web_accessible_resources"):
            assert key in data, f"missing key in manifest.json: {key}"

    def test_chrome_manifest_exposes_svg_dir(self):
        with (EXT / "manifest.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        war = data["web_accessible_resources"]
        flat = [r for entry in war for r in entry.get("resources", [])]
        assert "data/svg/*.svg" in flat, \
            "SVGs must be web-accessible for content-script fetch()"

    def test_chrome_manifest_exposes_explore_dir(self):
        # Tier 3 #7: pre-rendered explorer reports must be fetchable.
        with (EXT / "manifest.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        flat = [r for entry in data["web_accessible_resources"]
                for r in entry.get("resources", [])]
        assert "data/explore/*.json" in flat

    def test_chrome_manifest_uses_service_worker(self):
        with (EXT / "manifest.json").open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert "service_worker" in data["background"]

    def test_firefox_manifest_uses_scripts(self):
        # Generate it on the fly so the test is hermetic.
        subprocess.run(["python3", str(EXT / "build_firefox_manifest.py")],
                       check=True, cwd=REPO)
        ff = EXT / "manifest.firefox.json"
        assert ff.exists()
        with ff.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert "scripts" in data["background"]
        assert "service_worker" not in data["background"]
        assert data["browser_specific_settings"]["gecko"]["strict_min_version"]


class TestJSSyntax:
    @pytest.fixture(autouse=True)
    def _check_node(self):
        if not shutil.which("node"):
            pytest.skip("node not installed")

    def test_content_script_parses(self):
        result = subprocess.run(
            ["node", "-c", str(EXT / "src" / "content" / "content.js")],
            capture_output=True, text=True, cwd=REPO,
        )
        assert result.returncode == 0, f"node -c failed: {result.stderr}"

    def test_service_worker_parses(self):
        result = subprocess.run(
            ["node", "-c", str(EXT / "src" / "background" / "service_worker.js")],
            capture_output=True, text=True, cwd=REPO,
        )
        assert result.returncode == 0, f"node -c failed: {result.stderr}"


class TestContentScriptFeatures:
    """Verify each major UX feature has a recognizable region in content.js."""

    @pytest.fixture(scope="class")
    def content(self):
        return (EXT / "src" / "content" / "content.js").read_text(encoding="utf-8")

    def test_has_badge_injection(self, content):
        assert "function injectBadges" in content

    def test_has_inline_citation_walker(self, content):
        assert "function injectCitationsIn" in content
        assert "yuho-citation" in content

    def test_has_tooltip_render(self, content):
        assert "function renderTooltip" in content
        assert "yuho-tooltip-card" in content

    def test_has_panel_search(self, content):
        assert "function renderSearchResults" in content
        assert "yuho-search-input" in content

    def test_has_prefs_persistence(self, content):
        assert "chrome.storage.sync" in content
        assert "function loadPrefs" in content
        assert "function savePrefs" in content

    def test_has_observer_throttle(self, content):
        assert "function debounce" in content
        assert "OBSERVER_DEBOUNCE_MS" in content

    def test_has_service_worker_message(self, content):
        assert "yuho_section_active" in content

    def test_has_diagram_tab(self, content):
        assert 'data-tab="diagram"' in content
        assert "function renderDiagram" in content
        assert "mermaid_svg_url" in content
        assert "function loadDiagram" in content
        assert "SVG_CACHE" in content

    def test_has_explore_tab(self, content):
        # Tier 3 #7: counter-example explorer button on the panel.
        assert 'data-tab="explore"' in content
        assert "function renderExplore" in content
        assert "function loadExplore" in content
        assert "EXPLORE_CACHE" in content
        # Pre-rendered SVGs and explorer reports both ship under data/.
        assert "data/explore/s" in content


class TestServiceWorkerFeatures:
    @pytest.fixture(scope="class")
    def sw(self):
        return (EXT / "src" / "background" / "service_worker.js").read_text(encoding="utf-8")

    def test_has_action_click(self, sw):
        assert "chrome.action.onClicked" in sw

    def test_has_badge_handler(self, sw):
        assert "yuho_section_active" in sw
        assert "setBadgeText" in sw

    def test_has_navigation_clearing(self, sw):
        assert "chrome.tabs.onUpdated" in sw


class TestCSSRegions:
    @pytest.fixture(scope="class")
    def css(self):
        return (EXT / "src" / "content" / "panel.css").read_text(encoding="utf-8")

    def test_has_tooltip_styles(self, css):
        assert "#yuho-tooltip" in css
        assert ".yuho-tooltip-card" in css

    def test_has_search_styles(self, css):
        assert ".yuho-search-input" in css
        assert ".yuho-search-results" in css

    def test_dark_mode_supported(self, css):
        # Dark mode media query should appear at least once.
        assert "@media (prefers-color-scheme: dark)" in css

    def test_has_diagram_styles(self, css):
        assert ".yuho-diagram" in css


class TestDataBundle:
    def test_data_bundle_exists(self):
        data = EXT / "data" / "sections.json"
        if not data.exists():
            pytest.skip("data/sections.json not built; run build_data.py")
        with data.open("r", encoding="utf-8") as f:
            sections = json.load(f)
        assert isinstance(sections, dict)
        assert "415" in sections, "expected s415 in slim corpus"

    def test_slim_emits_svg_files_and_url(self):
        """Canonical SVG must surface as a per-section file + slim URL pointer."""
        canonical = REPO / "library" / "penal_code" / "_corpus" / "sections"
        slim = EXT / "data" / "sections.json"
        if not canonical.exists() or not slim.exists():
            pytest.skip("corpus or slim bundle not built")
        with slim.open("r", encoding="utf-8") as f:
            sections = json.load(f)
        for path in sorted(canonical.glob("s*.json")):
            with path.open("r", encoding="utf-8") as f:
                rec = json.load(f)
            if not rec.get("transpiled", {}).get("mermaid_svg"):
                continue
            num = rec["section_number"]
            url = sections[num]["transpiled"]["mermaid_svg_url"]
            assert url == f"data/svg/s{num}.svg", f"unexpected url: {url}"
            svg_path = EXT / url
            assert svg_path.exists(), f"slim references {url} but file missing"
            assert svg_path.read_text(encoding="utf-8").lstrip().startswith("<svg")
            return
        pytest.skip("no section in canonical corpus has mermaid_svg "
                    "(install mmdc and rebuild with build_corpus.py)")

    def test_index_bundle_exists(self):
        idx = EXT / "data" / "index.json"
        if not idx.exists():
            pytest.skip("data/index.json not built")
        with idx.open("r", encoding="utf-8") as f:
            index = json.load(f)
        assert "sections" in index
        assert index["totals"]["L1"] == 524


# ---------------------------------------------------------------------------
# Tier 2: integration via Playwright (skipped if browser unavailable)
# ---------------------------------------------------------------------------


_pw = pytest.importorskip(
    "playwright", reason="playwright not installed (.venv-lsp/bin/pip install playwright)"
)


def _has_chromium() -> bool:
    """Check if the Playwright Chromium binary is available."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return False
    try:
        with sync_playwright() as pw:
            # Probe by trying to launch persistent context with --version.
            # If chromium hasn't been downloaded, this fails fast.
            return Path(pw.chromium.executable_path).exists()
    except Exception:
        return False


_FIXTURE_HTML = """<!DOCTYPE html>
<html>
<head><title>Yuho fixture</title></head>
<body>
  <h2 id="pr415-">Section 415 — Cheating</h2>
  <p>Whoever, by deceiving any person, fraudulently or dishonestly induces ...
     References s420 and section 24.</p>
  <h2 id="pr420-">Section 420 — Cheating inducing delivery</h2>
  <p>Whoever cheats and thereby dishonestly induces delivery of property ...</p>
</body>
</html>
"""


@pytest.fixture(scope="module")
def fixture_server(tmp_path_factory):
    """Serve the fixture via a local HTTP server.

    MV3 content scripts don't run on file:// URLs (Chrome blocks them
    unless the per-extension "allow file URLs" toggle is on), so a real
    integration test needs an HTTP origin.
    """
    import http.server
    import socketserver
    import threading
    import os

    site_dir = tmp_path_factory.mktemp("yuho_site")
    (site_dir / "index.html").write_text(_FIXTURE_HTML, encoding="utf-8")

    cwd = os.getcwd()
    os.chdir(site_dir)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), http.server.SimpleHTTPRequestHandler)
    port = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()

    yield f"http://127.0.0.1:{port}/"

    httpd.shutdown()
    os.chdir(cwd)


# Build a tmp copy of the extension with relaxed matchers so the content
# script injects on the test fixture page. The original manifest scopes
# to sso.agc.gov.sg/Act/PC1871*, which the local fixture URL would never
# match.
def _build_test_extension(dst: Path, ext_src: Path) -> None:
    import shutil
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(ext_src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    manifest = dst / "manifest.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    # Match every URL so the content script attaches to the fixture file.
    for cs in data.get("content_scripts", []):
        cs["matches"] = ["<all_urls>"]
    data["host_permissions"] = ["<all_urls>"]
    for entry in data.get("web_accessible_resources", []):
        entry["matches"] = ["<all_urls>"]
    manifest.write_text(json.dumps(data, indent=2), encoding="utf-8")


@pytest.fixture(scope="module")
def chromium_with_ext(tmp_path_factory):
    if not _has_chromium():
        pytest.skip("Chromium not installed for Playwright")
    from playwright.sync_api import sync_playwright

    work_root = tmp_path_factory.mktemp("yuho_pw")
    test_ext = work_root / "ext"
    _build_test_extension(test_ext, EXT)
    user_data = work_root / "user_data"

    pw = sync_playwright().start()
    # Note: extensions only load under the *new* headless mode. The legacy
    # "old headless" silently drops content_scripts.
    ctx = pw.chromium.launch_persistent_context(
        user_data_dir=str(user_data),
        headless=False,
        args=[
            f"--disable-extensions-except={test_ext}",
            f"--load-extension={test_ext}",
            "--no-sandbox",
            "--headless=new",
        ],
    )
    yield ctx
    try:
        ctx.close()
    finally:
        pw.stop()


@pytest.mark.skipif(not _has_chromium(), reason="Chromium not installed for Playwright")
class TestPlaywrightIntegration:
    def test_fixture_page_loads(self, fixture_server, chromium_with_ext):
        page = chromium_with_ext.new_page()
        try:
            page.goto(fixture_server)
            assert "Yuho fixture" in page.title()
        finally:
            page.close()

    def test_content_script_injects_section_badges(self, fixture_server, chromium_with_ext):
        """Open the fixture in headless Chromium with the extension
        loaded, wait for the content script's document_idle init, and
        assert the L1/L2/L3 badges appear next to the section h2s."""
        page = chromium_with_ext.new_page()
        try:
            page.goto(fixture_server)
            badge = page.wait_for_selector(".yuho-badge", timeout=15_000)
            assert badge is not None
            count = page.evaluate("() => document.querySelectorAll('.yuho-badge').length")
            assert count >= 2, f"expected ≥2 badges (s415 + s420), got {count}"
        finally:
            page.close()

    def test_clicking_badge_opens_panel_with_explore_tab(
        self, fixture_server, chromium_with_ext,
    ):
        page = chromium_with_ext.new_page()
        try:
            page.goto(fixture_server)
            page.wait_for_selector(".yuho-badge", timeout=15_000)
            page.evaluate(
                "() => document.querySelector('.yuho-badge[data-section=\"415\"]')?.click()"
            )
            page.wait_for_selector("#yuho-panel", timeout=10_000)
            # Tab bar must include the Explore tab (Tier 3 #7).
            tabs = page.evaluate(
                "() => Array.from(document.querySelectorAll('#yuho-panel .yuho-tab'))"
                ".map(b => b.dataset.tab)"
            )
            assert "explore" in tabs, f"explore tab missing from {tabs}"
            page.evaluate(
                "() => document.querySelector('#yuho-panel .yuho-tab[data-tab=\"explore\"]')?.click()"
            )
            # Either a real report renders or the placeholder fires when
            # the slim explore JSON isn't bundled. Both prove loadExplore ran.
            page.wait_for_selector(
                "#yuho-explore-host h3, #yuho-explore-host .yuho-empty",
                timeout=15_000,
            )
        finally:
            page.close()

    def test_inline_citations_get_wrapped(self, fixture_server, chromium_with_ext):
        """The content script walks the body and wraps `s420` / `section 24`
        in `<span class="yuho-citation">`. Verify at least one is wrapped
        in the fixture prose."""
        page = chromium_with_ext.new_page()
        try:
            page.goto(fixture_server)
            page.wait_for_selector(".yuho-badge", timeout=15_000)
            page.wait_for_function(
                "() => document.querySelectorAll('.yuho-citation').length > 0",
                timeout=10_000,
            )
            count = page.evaluate(
                "() => document.querySelectorAll('.yuho-citation').length"
            )
            assert count >= 1, f"expected ≥1 wrapped citation, got {count}"
        finally:
            page.close()
