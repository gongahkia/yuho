#!/usr/bin/env python3
"""Pre-render the counter-example explorer report per section.

Walks every section in ``library/penal_code/<section>/statute.yh``,
runs the explorer (``yuho.explore.counterexamples``), and writes the
``ExplorerReport`` JSON to ``editors/browser-yuho/data/explore/sN.json``.

The browser extension's panel lazy-loads these per-section files when
the user opens the "Counter-examples" tab. Pre-rendering keeps the
extension shippable (no Python or Z3 in the browser).

Run after ``scripts/build_corpus.py``:

    python3 editors/browser-yuho/build_explore.py
    python3 editors/browser-yuho/build_explore.py --section 415  # one section

Skips gracefully if z3 is not installed; in that case existing
explore-data files are preserved (so a partial dataset stays usable).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent.parent
LIBRARY_DIR = REPO / "library" / "penal_code"
DATA_DIR = Path(__file__).resolve().parent / "data" / "explore"


def _section_dirs():
    return sorted(
        d for d in LIBRARY_DIR.iterdir()
        if d.is_dir() and d.name.startswith("s") and not d.name.startswith("_")
    )


def _section_number(section_dir: Path) -> str:
    stem = section_dir.name[1:]
    if "_" in stem:
        stem = stem.split("_", 1)[0]
    return stem


def _explore_one(section_dir: Path) -> Optional[dict]:
    yh = section_dir / "statute.yh"
    if not yh.exists():
        return None
    try:
        from yuho.services.analysis import analyze_file
        from yuho.explore.counterexamples import CounterexampleExplorer
    except Exception as exc:
        print(f"error: cannot import explorer: {exc}", file=sys.stderr)
        return None
    try:
        analysis = analyze_file(str(yh), run_semantic=False)
    except Exception as exc:
        return {"section": _section_number(section_dir),
                "available": False,
                "reason": f"parse failed: {exc}"}
    if analysis.parse_errors or analysis.ast is None:
        return {"section": _section_number(section_dir),
                "available": False,
                "reason": "parse_errors"}
    explorer = CounterexampleExplorer(analysis.ast)
    report = explorer.explore_section(_section_number(section_dir),
                                      max_satisfying=4)
    return report.to_dict()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--section", help="Build only this section number")
    args = ap.parse_args()

    try:
        import z3  # noqa: F401
    except Exception:
        print("z3 not installed; skipping. Install with: pip install z3-solver",
              file=sys.stderr)
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    dirs = _section_dirs()
    if args.section:
        dirs = [d for d in dirs if _section_number(d) == args.section]
        if not dirs:
            print(f"no section dir for {args.section!r}", file=sys.stderr)
            return 1

    n_ok = n_fail = 0
    for sd in dirs:
        num = _section_number(sd)
        try:
            payload = _explore_one(sd)
        except Exception as exc:
            print(f"  s{num}: error {exc}", file=sys.stderr)
            n_fail += 1
            continue
        if payload is None:
            continue
        out = DATA_DIR / f"s{num}.json"
        out.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        n_ok += 1
        if n_ok % 50 == 0:
            print(f"  built {n_ok} explorer reports...", file=sys.stderr)

    print(f"\nDone: {n_ok} explorer reports written to "
          f"{DATA_DIR.relative_to(REPO)}/ ({n_fail} failed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
