"""Tests for the Yuho Word add-in.

Three tiers:

1. **Manifest** — XML wellformedness via ``xmllint``, then string-level
   shape checks (required elements, every URL/icon resid resolves).
2. **JS** — ``node -c`` syntax check on every JS file under ``src/``.
3. **Data** — slim corpus is present and has the shape the taskpane
   expects.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parent.parent
EXT = REPO / "editors" / "word-yuho"
MANIFEST = EXT / "manifest.xml"
SRC = EXT / "src"


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def manifest_text() -> str:
    return MANIFEST.read_text(encoding="utf-8")


class TestManifest:
    def test_xml_wellformed(self):
        if not shutil.which("xmllint"):
            pytest.skip("xmllint not installed")
        result = subprocess.run(
            ["xmllint", "--noout", str(MANIFEST)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"xmllint failed: {result.stderr}"

    def test_required_top_level_elements(self, manifest_text):
        for tag in ("<Id>", "<Version>", "<DisplayName ", "<Permissions>",
                    "<Hosts>", "<DefaultSettings>", "<VersionOverrides "):
            assert tag in manifest_text, f"manifest missing {tag}"

    def test_taskpane_url_declared(self, manifest_text):
        assert 'id="Taskpane.Url"' in manifest_text
        assert "/taskpane/taskpane.html" in manifest_text

    def test_commands_url_declared(self, manifest_text):
        # Required for FunctionFile / ExecuteFunction commands (G1).
        assert 'id="Commands.Url"' in manifest_text
        assert "<FunctionFile " in manifest_text
        assert "/commands/commands.html" in manifest_text

    def test_every_executefunction_has_implementation(self, manifest_text):
        # Pull every <FunctionName>X</FunctionName> and assert commands.js
        # associates each one via Office.actions.associate.
        names = re.findall(r"<FunctionName>([^<]+)</FunctionName>", manifest_text)
        assert names, "no ExecuteFunction commands declared"
        cmd_js = (SRC / "commands" / "commands.js").read_text(encoding="utf-8")
        for n in names:
            pat = rf'Office\.actions\.associate\(\s*"{re.escape(n)}"'
            assert re.search(pat, cmd_js), \
                f"manifest declares {n!r} but commands.js doesn't associate it"

    def test_every_referenced_icon_file_exists(self, manifest_text):
        # The manifest references icon URLs under https://localhost:3000/assets/.
        # The local files must be present so the dev server can serve them.
        urls = re.findall(r'DefaultValue="https://localhost:3000/assets/([^"]+)"',
                          manifest_text)
        assert urls, "no icon URLs declared in manifest"
        for u in urls:
            assert (SRC / "assets" / u).exists(), \
                f"manifest references assets/{u} but file is missing"

    def test_every_referenced_html_file_exists(self, manifest_text):
        urls = re.findall(r'DefaultValue="https://localhost:3000/([^"]+\.html)"',
                          manifest_text)
        for u in urls:
            assert (SRC / u).exists(), \
                f"manifest references {u} but file is missing"


# ---------------------------------------------------------------------------
# JS syntax
# ---------------------------------------------------------------------------


class TestJSSyntax:
    @pytest.fixture(autouse=True)
    def _check_node(self):
        if not shutil.which("node"):
            pytest.skip("node not installed")

    @pytest.mark.parametrize("rel", [
        "taskpane/taskpane.js",
        "commands/commands.js",
    ])
    def test_js_parses(self, rel):
        path = SRC / rel
        assert path.exists(), f"missing {rel}"
        result = subprocess.run(
            ["node", "-c", str(path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"node -c failed for {rel}: {result.stderr}"

    def test_dev_server_parses(self):
        # G8: dev_server.js must parse so `npm start` doesn't blow up.
        path = EXT / "dev_server.js"
        assert path.exists()
        result = subprocess.run(
            ["node", "-c", str(path)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"node -c failed: {result.stderr}"


# ---------------------------------------------------------------------------
# Data bundle
# ---------------------------------------------------------------------------


class TestDataBundle:
    def test_sections_json_present(self):
        path = EXT / "data" / "sections.json"
        if not path.exists():
            pytest.skip("data/sections.json not built; run npm run build:data")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict) and len(data) > 0

    def test_sections_have_expected_shape(self):
        path = EXT / "data" / "sections.json"
        if not path.exists():
            pytest.skip("data/sections.json not built")
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        # Pick any one record and assert required fields the taskpane reads.
        rec = next(iter(data.values()))
        for key in ("section_number", "section_title", "encoded",
                    "transpiled", "coverage"):
            assert key in rec, f"section record missing {key}"

    def test_index_json_present(self):
        path = EXT / "data" / "index.json"
        if not path.exists():
            pytest.skip("data/index.json not built")
        with path.open("r", encoding="utf-8") as f:
            idx = json.load(f)
        assert "sections" in idx and "totals" in idx


# ---------------------------------------------------------------------------
# Taskpane HTML — sanity checks for the static markup
# ---------------------------------------------------------------------------


class TestProdManifestBuilder:
    """G7: build_manifest.py rewrites localhost URLs for production."""

    def test_builder_emits_swapped_manifest(self, tmp_path):
        out = tmp_path / "manifest.prod.xml"
        result = subprocess.run(
            ["python3", str(EXT / "build_manifest.py"),
             "--host", "https://yuho.dev/word",
             "--version", "9.9.9.9",
             "--output", str(out)],
            capture_output=True, text=True, cwd=EXT,
        )
        assert result.returncode == 0, f"build_manifest.py failed: {result.stderr}"
        text = out.read_text(encoding="utf-8")
        assert "https://localhost:3000" not in text
        assert "https://yuho.dev/word" in text
        assert "<Version>9.9.9.9</Version>" in text


class TestTaskpaneHtml:
    @pytest.fixture(scope="class")
    def html(self):
        return (SRC / "taskpane" / "taskpane.html").read_text(encoding="utf-8")

    def test_loads_office_js(self, html):
        assert "appsforoffice.microsoft.com/lib/1/hosted/office.js" in html

    def test_search_input_present(self, html):
        assert 'id="search"' in html

    def test_action_buttons_match_taskpane_js(self, html):
        js = (SRC / "taskpane" / "taskpane.js").read_text(encoding="utf-8")
        for handler_id in re.findall(r'id="(action-[a-z\-]+)"', html):
            assert handler_id in js, \
                f"taskpane.html declares #{handler_id} but taskpane.js never references it"
