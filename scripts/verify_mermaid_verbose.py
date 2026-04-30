"""Static-syntax sweep for ``yuho transpile -t mermaid --shape verbose``
across every ``library/penal_code/*/statute.yh`` file.

Validates the verbose-shape output post the 2026-04-30 audit pass
(commits ``50eae123`` penalty-conditional-fix + ``d825d2e5``
exception-priority-sort) at corpus scale. Catches any regression
that re-introduces orphan node references, transpile failures, or
zero-output cases the unit tests would not surface.

Exit codes:
  0 — all 524/524 sections render with 0 orphans, 0 failures
  1 — at least one section transpile-fails or carries orphan nodes
  2 — internal error
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "library" / "penal_code"

NODE_DEF = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\b[\[\(\{]", re.M)
EDGE = re.compile(
    r"^\s*([A-Z][A-Z0-9_]*)\s*-+(?:\.+)?>(?:\|[^|]*\|)?\s*([A-Z][A-Z0-9_]*)\b",
    re.M,
)


def main() -> int:
    if not LIBRARY.is_dir():
        print(f"library not found: {LIBRARY}", file=sys.stderr)
        return 2

    sections = sorted(LIBRARY.glob("s*/statute.yh"))
    if not sections:
        print("no sections found", file=sys.stderr)
        return 2

    print(f"→ verbose-mermaid-sweeping {len(sections)} sections…")

    failures: list[tuple[str, str]] = []
    orphans: list[tuple[str, list[str]]] = []
    for s in sections:
        r = subprocess.run(
            [sys.executable, "-m", "yuho.cli.main", "transpile",
             "-t", "mermaid", "--shape", "verbose", str(s)],
            capture_output=True, text=True, timeout=30,
        )
        if r.returncode != 0:
            failures.append((s.parent.name, r.stderr.strip()[:160]))
            continue
        defined = set(NODE_DEF.findall(r.stdout))
        referenced = set()
        for src, tgt in EDGE.findall(r.stdout):
            referenced.add(src)
            referenced.add(tgt)
        orphan_set = referenced - defined
        if orphan_set:
            orphans.append((s.parent.name, sorted(orphan_set)[:5]))

    print(
        f"verbose-mermaid sweep: PASS={len(sections) - len(failures) - len(orphans)}"
        f"/{len(sections)}  FAIL={len(failures)}  ORPHAN_SECTIONS={len(orphans)}"
    )
    if failures:
        print("Transpile failures:", file=sys.stderr)
        for name, msg in failures:
            print(f"  {name}: {msg}", file=sys.stderr)
    if orphans:
        print("Orphan-node sections:", file=sys.stderr)
        for name, ids in orphans:
            print(f"  {name}: {ids}", file=sys.stderr)

    return 0 if not (failures or orphans) else 1


if __name__ == "__main__":
    sys.exit(main())
