#!/usr/bin/env python3
"""Idempotently insert general-defence `defeats` edges into Penal Code
section files.

Usage:
    python scripts/add_general_defence_edges.py \\
        --section s299 --defences 79,80,84,96

Or, batch via a YAML / inline cluster definition (see __main__ at bottom
for the canonical clusters used by the Direction B expansion).

Each call inserts an `exception general_defence_sN { … when is_infringed(sN) }`
block before the final `}` of the top-level `statute` block, but only if
that exact `general_defence_sN` block is not already present in the file.

Convention matches the v0 sample at s302/s323/s325/s378:

    exception general_defence_sN {
        "<short doctrinal description>"
        "no s<X> conviction per s<N> general exception"
        when is_infringed(sN)
    }

The descriptions are looked up from a small built-in dictionary keyed
by defence number; the per-section conviction predicate (s<X>) is taken
from the section number passed in.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "library" / "penal_code"

# Doctrinal one-liners for each Chapter IV defence we expand.
DEFENCE_TITLES = {
    79: "act done by reason of mistake of fact",
    80: "accident in the doing of a lawful act",
    81: "act likely to cause harm but done to prevent other harm",
    82: "act of a child under ten years of age",
    83: "act of a child above ten and under twelve of immature understanding",
    84: "act done by a person of unsound mind",
    85: "intoxication when a defence",
    86: "effect of defence of intoxication when established",
    87: "act not intended and not known to be likely to cause death or grievous hurt",
    88: "act not intended to cause death done by consent",
    89: "act done in good faith for the benefit of a child or person of unsound mind",
    92: "act done in good faith for the benefit of a person without consent",
    94: "act to which a person is compelled by threats",
    95: "act causing slight harm",
    96: "act done in private defence",
    97: "right of private defence of body and property",
    98: "right of private defence against the act of a person of unsound mind",
    100: "right of private defence against deadly assault on body",
    101: "right of private defence against assault not extending to causing death",
    103: "right of private defence of property against deadly attack",
    104: "right of private defence of property against attack not extending to causing death",
    106: "right of private defence against deadly assault when there is risk of harm to innocent person",
}


def find_section_dir(section: str) -> Path:
    """Map a section identifier (e.g. 's299', '299', 's376AA') to its
    library directory."""
    if not section.startswith("s"):
        section = "s" + section
    candidates = sorted(LIB.glob(f"{section}_*"))
    if not candidates:
        raise FileNotFoundError(f"no library directory matches {section}")
    if len(candidates) > 1:
        # Disambiguate by exact prefix match on the section identifier.
        exact = [c for c in candidates if c.name.split("_", 1)[0] == section]
        if not exact:
            raise FileNotFoundError(
                f"ambiguous match for {section}: {[c.name for c in candidates]}"
            )
        return exact[0]
    return candidates[0]


def build_edge_block(section_num: str, defence_num: int) -> str:
    """Render the exception block string."""
    title = DEFENCE_TITLES.get(defence_num, f"general defence under s{defence_num}")
    return (
        f"    exception general_defence_s{defence_num} {{\n"
        f"        \"{title}\"\n"
        f"        \"no s{section_num} conviction per s{defence_num} general exception\"\n"
        f"        when is_infringed(s{defence_num})\n"
        f"    }}\n"
    )


def insert_edges(path: Path, section_num: str, defences: List[int]) -> Tuple[int, int]:
    """Insert any missing defence edges into ``path``.

    Returns ``(added_count, already_present_count)``.
    """
    src = path.read_text(encoding="utf-8")

    # Skip insertion if the section .yh has no top-level `statute N {…}`
    # block we recognise.
    statute_match = re.search(r"^statute\s+\S+\s+\".*?\"", src, re.MULTILINE)
    if statute_match is None:
        raise ValueError(f"{path} has no top-level statute block")

    # Find the closing `}` of the top-level statute block. We do this by
    # scanning brace depth from the start of the `statute` line. Yuho
    # uses `"..."` for string literals (no `'...'`), so the brace tracker
    # only treats `"` as a string delimiter — ASCII `'` shows up in
    # English possessives inside `///` doc comments and would otherwise
    # confuse the tracker. `///` and `//` line comments also skipped.
    start = statute_match.start()
    depth = 0
    end = -1
    in_string = False
    i = start
    while i < len(src):
        c = src[i]
        if in_string:
            if c == "\\" and i + 1 < len(src):
                i += 2
                continue
            if c == '"':
                in_string = False
        else:
            # Skip line comments outright.
            if c == "/" and i + 1 < len(src) and src[i + 1] == "/":
                nl = src.find("\n", i)
                if nl < 0:
                    break
                i = nl + 1
                continue
            if c == '"':
                in_string = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i
                    break
        i += 1
    if end < 0:
        raise ValueError(f"{path} statute block has no balanced closing brace")

    added = 0
    skipped = 0
    inserts = []
    for defence in defences:
        marker = f"general_defence_s{defence}"
        if marker in src:
            skipped += 1
            continue
        inserts.append(build_edge_block(section_num, defence))
        added += 1

    if not inserts:
        return (0, skipped)

    insertion = "".join(inserts)
    # Ensure exactly one blank line precedes the inserted block(s).
    prefix = src[:end]
    if not prefix.endswith("\n"):
        prefix += "\n"
    if not prefix.endswith("\n\n"):
        prefix += "\n"
    new_src = prefix + insertion + src[end:]
    path.write_text(new_src, encoding="utf-8")
    return (added, skipped)


def parse_section_id(name: str) -> str:
    """'s299_culpable_homicide' -> '299'; 's376AA_…' -> '376AA'."""
    if name.startswith("s"):
        name = name[1:]
    return name.split("_", 1)[0]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--section", required=True,
                   help="Section identifier, e.g. s299 or 299 or s376AA")
    p.add_argument("--defences", required=True,
                   help="Comma-separated defence numbers, e.g. 79,80,84,96")
    p.add_argument("--dry-run", action="store_true",
                   help="Report what would be inserted without writing")
    args = p.parse_args()

    section_dir = find_section_dir(args.section)
    yh_file = section_dir / "statute.yh"
    if not yh_file.exists():
        print(f"error: {yh_file} not found", file=sys.stderr)
        return 2

    section_num = parse_section_id(section_dir.name)
    defences = [int(d.strip()) for d in args.defences.split(",") if d.strip()]
    if args.dry_run:
        existing = yh_file.read_text(encoding="utf-8")
        for defence in defences:
            present = f"general_defence_s{defence}" in existing
            print(f"  s{defence}: {'present' if present else 'WOULD ADD'}")
        return 0

    added, skipped = insert_edges(yh_file, section_num, defences)
    print(f"{section_dir.name}: added={added} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
