#!/usr/bin/env python3
"""Build the browser extension's data bundle from the canonical corpus.

Reads `library/penal_code/_corpus/{index.json,sections/*.json}` and emits a
slim, single-file `data/sections.json` plus a copy of `data/index.json`
inside `editors/browser-yuho/data/`. The slim format drops fields the
panel UI does not consume (e.g. full Mermaid source) to keep the
extension package small.

Run this script after `scripts/build_corpus.py` or whenever the encoded
library changes.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Dict

REPO = Path(__file__).resolve().parent.parent.parent
SOURCE = REPO / "library" / "penal_code" / "_corpus"
DEST = Path(__file__).resolve().parent / "data"


# Fields kept per section in the slim format.
KEEP_RAW = ("marginal_note", "text", "sub_items", "amendments", "hash_sha256")
KEEP_ENCODED_AST = (
    "elements", "illustrations", "subsections", "exceptions",
    "case_law", "definitions", "effective_dates", "repealed_date",
    "subsumes", "amends", "has_penalty",
)


def slim_record(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Return a minimal version of a section record for the panel UI."""
    ast = rec.get("encoded", {}).get("ast_summary", {}) or {}
    return {
        "section_number": rec["section_number"],
        "section_title": rec["section_title"],
        "act": rec.get("act"),
        "act_code": rec.get("act_code"),
        "jurisdiction": rec.get("jurisdiction"),
        "sso_url": rec.get("sso_url"),
        "sso_anchor": rec.get("sso_anchor"),
        "raw": {k: rec.get("raw", {}).get(k) for k in KEEP_RAW},
        "encoded": {
            "yh_source": rec.get("encoded", {}).get("yh_source"),
            "ast_summary": {k: ast.get(k) for k in KEEP_ENCODED_AST},
        },
        "transpiled": {
            "english": rec.get("transpiled", {}).get("english"),
            "mermaid_svg_url": (
                f"data/svg/s{rec['section_number']}.svg"
                if rec.get("transpiled", {}).get("mermaid_svg") else None
            ),
            # raw mermaid source + inline SVG omitted -- panel lazy-loads
            # the per-section SVG file from data/svg/ on tab open.
        },
        "coverage": rec.get("coverage", {}),
        "references": rec.get("references", {}),
        "metadata": {
            "summary": rec.get("metadata", {}).get("summary"),
        },
        "provenance": rec.get("provenance", {}),
    }


def main() -> int:
    if not SOURCE.exists():
        print(f"error: corpus not found at {SOURCE}. Run `python3 scripts/build_corpus.py` first.")
        return 1

    DEST.mkdir(parents=True, exist_ok=True)
    svg_dir = DEST / "svg"
    svg_dir.mkdir(parents=True, exist_ok=True)
    # Wipe stale SVGs so deletions in the canonical corpus propagate.
    for old in svg_dir.glob("s*.svg"):
        old.unlink()

    # Copy the index verbatim — it's already small and panel-friendly.
    shutil.copy2(SOURCE / "index.json", DEST / "index.json")
    print(f"copied {DEST / 'index.json'}")

    # Build the combined slim sections file.
    sections: Dict[str, Dict[str, Any]] = {}
    files = sorted((SOURCE / "sections").glob("s*.json"))
    n_svgs = 0
    for path in files:
        with path.open("r", encoding="utf-8") as f:
            rec = json.load(f)
        sections[rec["section_number"]] = slim_record(rec)
        svg = rec.get("transpiled", {}).get("mermaid_svg")
        if svg:
            (svg_dir / f"s{rec['section_number']}.svg").write_text(svg, encoding="utf-8")
            n_svgs += 1
    print(f"wrote {n_svgs} SVGs to {svg_dir}")

    out_path = DEST / "sections.json"
    out_path.write_text(json.dumps(sections, ensure_ascii=False), encoding="utf-8")
    size_kb = out_path.stat().st_size // 1024
    print(f"wrote {out_path} ({len(sections)} sections, {size_kb} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
