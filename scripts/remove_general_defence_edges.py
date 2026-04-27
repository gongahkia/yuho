#!/usr/bin/env python3
"""Idempotent remover for general-defence `defeats` edges, the
inverse of ``scripts/add_general_defence_edges.py``.

Scans the encoded library and removes any
``exception general_defence_s<N> { … }`` block whose defence number
matches the supplied ``--defences`` list. Used by the doctrinal-
fidelity audit that strips structurally-misclassified edges (s98
proportionality limits, s101 / s104 timing sections — these are
prerequisites for the s96/s97/s100/s103/s106 family, not standalone
defeating predicates).

Usage::

    # Strip a single defence's edges across the entire library:
    python scripts/remove_general_defence_edges.py --defences 98

    # Strip multiple defences in one pass:
    python scripts/remove_general_defence_edges.py --defences 98,101,104

    # Restrict to a specific section:
    python scripts/remove_general_defence_edges.py \\
        --section s302 --defences 98

    # Dry-run; report what would change without writing:
    python scripts/remove_general_defence_edges.py --defences 98 --dry-run

Block-detection rule: the canonical block emitted by
``add_general_defence_edges.py`` matches the regex
``exception general_defence_s<N> \\{ ... \\}`` (single nested level,
balanced braces). The remover handles the canonical form plus any
trailing blank line; it is conservative — if a block doesn't match
the expected shape (e.g. has been hand-edited), it is left alone
and reported.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "library" / "penal_code"


def _find_block(text: str, defence: int) -> Optional[Tuple[int, int]]:
    """Locate a single ``exception general_defence_s<N> { … }`` block in
    ``text``. Returns ``(start, end)`` indices on the source string,
    where ``end`` is one past the closing ``}`` (and any trailing
    blank line). Returns ``None`` if no matching block is present."""
    marker = f"exception general_defence_s{defence}"
    idx = text.find(marker)
    if idx < 0:
        return None
    # Walk forward to the opening `{`.
    open_brace = text.find("{", idx)
    if open_brace < 0:
        return None
    # Count braces forward to find the matching close.
    depth = 1
    i = open_brace + 1
    in_string = False
    while i < len(text) and depth > 0:
        c = text[i]
        if in_string:
            if c == "\\" and i + 1 < len(text):
                i += 2
                continue
            if c == '"':
                in_string = False
        else:
            if c == "/" and i + 1 < len(text) and text[i + 1] == "/":
                # skip to end of line
                nl = text.find("\n", i)
                i = nl + 1 if nl >= 0 else len(text)
                continue
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
        i += 1
    if depth != 0:
        return None
    end = i
    # Walk backward from `marker` start to drop a single preceding
    # newline (and any indentation) so the removal doesn't leave a
    # spurious blank line.
    start = idx
    # Drop a preceding indentation run on the same line.
    while start > 0 and text[start - 1] in " \t":
        start -= 1
    # Drop one preceding newline if present (so the block-leading
    # blank line collapses).
    if start > 0 and text[start - 1] == "\n":
        start -= 1
    # If there's a trailing newline + blank line, consume one newline
    # for symmetry.
    if end < len(text) and text[end] == "\n":
        end += 1
    return (start, end)


def remove_edges(
    path: Path, defences: List[int]
) -> Tuple[int, List[int]]:
    """Remove all matching defence-edge blocks from ``path``.

    Returns ``(removed_count, defences_actually_removed)``.
    """
    text = path.read_text(encoding="utf-8")
    removed = 0
    actually_removed: List[int] = []
    for defence in defences:
        # Repeat in case of (extremely unlikely) duplicates.
        while True:
            span = _find_block(text, defence)
            if span is None:
                break
            text = text[: span[0]] + text[span[1] :]
            removed += 1
            actually_removed.append(defence)
    if removed:
        path.write_text(text, encoding="utf-8")
    return (removed, actually_removed)


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawTextHelpFormatter
    )
    p.add_argument(
        "--defences",
        required=True,
        help="Comma-separated defence numbers, e.g. 98,101,104",
    )
    p.add_argument(
        "--section",
        default=None,
        help="Restrict removal to a single section directory "
        "(e.g. s302). Default: sweep entire library.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without writing",
    )
    args = p.parse_args()

    defences = [int(d.strip()) for d in args.defences.split(",") if d.strip()]
    if args.section:
        section = args.section if args.section.startswith("s") else f"s{args.section}"
        candidates = sorted(LIB.glob(f"{section}_*"))
        if not candidates:
            print(f"error: no library directory matches {section}", file=sys.stderr)
            return 2
        sections = candidates
    else:
        sections = sorted(d for d in LIB.iterdir() if d.is_dir() and not d.name.startswith("_"))

    total_removed = 0
    affected = 0
    for section_dir in sections:
        yh = section_dir / "statute.yh"
        if not yh.exists():
            continue
        if args.dry_run:
            text = yh.read_text(encoding="utf-8")
            present = [d for d in defences if f"general_defence_s{d}" in text]
            if present:
                affected += 1
                total_removed += len(present)
                print(f"  {section_dir.name}: would remove {present}")
        else:
            removed, _ = remove_edges(yh, defences)
            if removed:
                affected += 1
                total_removed += removed
                print(f"  {section_dir.name}: removed {removed}")
    verb = "would remove" if args.dry_run else "removed"
    print(f"{verb} {total_removed} edge(s) across {affected} section(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
