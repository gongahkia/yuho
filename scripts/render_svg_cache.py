#!/usr/bin/env python3
"""Parallel Mermaid SVG renderer for the corpus.

`scripts/build_corpus.py` renders SVGs inline (one mmdc subprocess per
section, blocking). At ~5-10 seconds per render and 1048 renders for
the full library (524 flowcharts + 524 mindmaps), the full rebuild
takes ~2 hours single-threaded.

This script does the same work in parallel. It reads the per-section
JSON files under ``library/penal_code/_corpus/sections/``, renders the
``transpiled.mermaid`` and ``transpiled.mindmap`` strings into SVGs
via ``mmdc`` with a configurable worker pool, and writes the results
back into the same JSON files. End-to-end: ~5-10 minutes on a modern
laptop with --workers 8.

Usage::

    # Render every section (default).
    python scripts/render_svg_cache.py

    # Render specific sections.
    python scripts/render_svg_cache.py --sections 415 300 304

    # Tune worker count (default 4; mmdc Chrome instances are heavy).
    python scripts/render_svg_cache.py --workers 8

    # Skip already-rendered SVGs (default: skip).
    python scripts/render_svg_cache.py --force        # rerender everything

The script honours ``YUHO_PUPPETEER_CONFIG`` if set; otherwise it
auto-detects a Chrome install under ``~/.cache/puppeteer/chrome``.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil as _shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
SECTIONS_DIR = REPO / "library" / "penal_code" / "_corpus" / "sections"


def _resolve_mmdc() -> Optional[str]:
    return _shutil.which("mmdc")


def _autodetect_puppeteer_config() -> Optional[str]:
    """Pick the first installed Chrome and write a one-shot config."""
    cache = Path.home() / ".cache" / "puppeteer" / "chrome"
    if not cache.is_dir():
        return None
    for candidate in sorted(cache.iterdir(), reverse=True):
        macos = candidate / "chrome-mac-arm64" / "Google Chrome for Testing.app" / \
            "Contents" / "MacOS" / "Google Chrome for Testing"
        linux = candidate / "chrome-linux64" / "chrome"
        for exe in (macos, linux):
            if exe.exists():
                cfg_path = Path(tempfile.gettempdir()) / "yuho-puppeteer-config.json"
                cfg_path.write_text(json.dumps({"executablePath": str(exe)}))
                return str(cfg_path)
    return None


def _render_one(mmdc: str, mermaid_src: str, pup_cfg: Optional[str]) -> Optional[str]:
    """Render one Mermaid string to inline SVG. Returns None on failure."""
    if not mermaid_src or not mermaid_src.strip():
        return None
    with tempfile.TemporaryDirectory(prefix="yuho-mmdc-") as tdir:
        in_path = Path(tdir) / "in.mmd"
        out_path = Path(tdir) / "out.svg"
        in_path.write_text(mermaid_src, encoding="utf-8")
        cmd = [mmdc, "-i", str(in_path), "-o", str(out_path), "-b", "transparent"]
        if pup_cfg:
            cmd.extend(["-p", pup_cfg])
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except Exception:
            return None
        if r.returncode != 0 or not out_path.exists():
            return None
        svg = out_path.read_text(encoding="utf-8")
    if svg.startswith("<?xml"):
        end = svg.find("?>")
        if end >= 0:
            svg = svg[end + 2:].lstrip()
    svg = svg.replace("<svg ", '<svg class="yuho-mermaid-svg" ', 1)
    return svg


def _process_section(
    path: Path,
    mmdc: str,
    pup_cfg: Optional[str],
    force: bool,
) -> Tuple[str, bool, bool]:
    """Render both mermaid + mindmap SVGs for one section file. Returns
    (section, rendered_mermaid, rendered_mindmap)."""
    rec = json.loads(path.read_text(encoding="utf-8"))
    section = rec["section_number"]
    transpiled = rec.setdefault("transpiled", {})
    rendered_m = False
    rendered_mm = False
    if force or not transpiled.get("mermaid_svg"):
        svg = _render_one(mmdc, transpiled.get("mermaid") or "", pup_cfg)
        if svg:
            transpiled["mermaid_svg"] = svg
            rendered_m = True
    if force or not transpiled.get("mindmap_svg"):
        svg = _render_one(mmdc, transpiled.get("mindmap") or "", pup_cfg)
        if svg:
            transpiled["mindmap_svg"] = svg
            rendered_mm = True
    if rendered_m or rendered_mm:
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return section, rendered_m, rendered_mm


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--sections", nargs="*", help="Section numbers to render (default: all)")
    p.add_argument("--workers", type=int, default=4,
                   help="Parallel mmdc workers (default: 4)")
    p.add_argument("--force", action="store_true",
                   help="Re-render even when an SVG is already present")
    args = p.parse_args()

    mmdc = _resolve_mmdc()
    if not mmdc:
        print("error: mmdc not found on PATH; install with `npm i -g @mermaid-js/mermaid-cli`",
              file=sys.stderr)
        return 1
    pup_cfg = os.environ.get("YUHO_PUPPETEER_CONFIG") or _autodetect_puppeteer_config()
    if pup_cfg:
        print(f"Using puppeteer config: {pup_cfg}")

    if not SECTIONS_DIR.exists():
        print(f"error: corpus not built; run `python scripts/build_corpus.py --no-mermaid-svg` first.",
              file=sys.stderr)
        return 1

    targets: List[Path]
    if args.sections:
        targets = [SECTIONS_DIR / f"s{s}.json" for s in args.sections]
        targets = [t for t in targets if t.exists()]
    else:
        targets = sorted(SECTIONS_DIR.glob("s*.json"))

    print(f"rendering {len(targets)} sections with {args.workers} workers...")
    n_m = n_mm = n_skipped = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(_process_section, t, mmdc, pup_cfg, args.force): t for t in targets
        }
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                section, rm, rmm = fut.result()
            except Exception as exc:
                print(f"  ! {futs[fut].name}: {exc}", file=sys.stderr)
                continue
            if rm: n_m += 1
            if rmm: n_mm += 1
            if not (rm or rmm): n_skipped += 1
            if i % 20 == 0 or i == len(targets):
                print(f"  [{i}/{len(targets)}] s{section} "
                      f"flowchart={n_m} mindmap={n_mm} skipped={n_skipped}",
                      file=sys.stderr)
    print(f"done: {n_m} flowchart SVGs, {n_mm} mindmap SVGs, {n_skipped} skipped (cache hit)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
