#!/usr/bin/env python3
"""Author a universal-shape behavioural test companion for a section.

For a section that lacks a `test_statute.yh`, this helper:

  1. Adds an `fn is_<short_name>(bool elements_satisfied, bool
     defence_applies) : bool` helper to the section's `statute.yh`,
     inserted just before the `statute N "..." { … }` block.
  2. Writes a `test_statute.yh` next to it that exercises the
     three universal-shape cases (guilty, defended, no-elements).

The shape mirrors TODO L26-29's universal-test pattern; sections
already carrying a section-specific helper-fn are excluded by
design (their tests are bespoke).

Usage::

    python scripts/add_behavioural_test.py \\
        --section s394 --short-name robbery_with_hurt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LIB = REPO / "library" / "penal_code"

HELPER_FN_TEMPLATE = """fn is_{short_name}(bool elements_satisfied, bool defence_applies) : bool {{
    match {{
        case TRUE if defence_applies := consequence FALSE;
        case TRUE if elements_satisfied := consequence TRUE;
        case _ := consequence FALSE;
    }}
}}

"""

TEST_FILE_TEMPLATE = """// Test file for {section_dir}
// Yuho v5 Syntax — behavioural fixture.
// Universal offence shape: made out iff elements ∧ ¬defence.

referencing penal_code/{section_dir}

struct {struct_name}TestCase {{
    bool elements_satisfied,
    bool defence_applies,
}}

// elements satisfied, no defence -> offence made out
{struct_name}TestCase guilty := {struct_name}TestCase {{
    elements_satisfied := TRUE,
    defence_applies := FALSE,
}}
assert is_{short_name}(guilty.elements_satisfied, guilty.defence_applies) == TRUE

// elements satisfied, defence applies -> not made out
{struct_name}TestCase defended := {struct_name}TestCase {{
    elements_satisfied := TRUE,
    defence_applies := TRUE,
}}
assert is_{short_name}(defended.elements_satisfied, defended.defence_applies) == FALSE

// no elements -> not made out
{struct_name}TestCase notMadeOut := {struct_name}TestCase {{
    elements_satisfied := FALSE,
    defence_applies := FALSE,
}}
assert is_{short_name}(notMadeOut.elements_satisfied, notMadeOut.defence_applies) == FALSE
"""


def find_section_dir(section: str) -> Path:
    if not section.startswith("s"):
        section = "s" + section
    candidates = sorted(LIB.glob(f"{section}_*"))
    if not candidates:
        raise FileNotFoundError(f"no library directory matches {section}")
    exact = [c for c in candidates if c.name.split("_", 1)[0] == section]
    if not exact and len(candidates) == 1:
        return candidates[0]
    if exact:
        return exact[0]
    raise FileNotFoundError(f"ambiguous: {[c.name for c in candidates]}")


def to_camel(snake: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in snake.split("_"))


def add_helper_fn_and_test(section: str, short_name: str) -> None:
    section_dir = find_section_dir(section)
    yh = section_dir / "statute.yh"
    test_yh = section_dir / "test_statute.yh"

    src = yh.read_text(encoding="utf-8")
    if f"fn is_{short_name}(" in src:
        print(f"  {section_dir.name}: helper-fn already present, skipping")
    else:
        # Insert helper fn just before the `statute` block.
        m = re.search(r"^statute\s+\S+\s+\".*?\".*?\{", src, re.MULTILINE)
        if m is None:
            raise ValueError(f"{yh}: no statute block found")
        insert_at = m.start()
        helper = HELPER_FN_TEMPLATE.format(short_name=short_name)
        new_src = src[:insert_at] + helper + src[insert_at:]
        yh.write_text(new_src, encoding="utf-8")
        print(f"  {section_dir.name}: added helper-fn is_{short_name}")

    if test_yh.exists():
        print(f"  {section_dir.name}: test_statute.yh already exists, skipping test")
        return
    struct_name = to_camel(short_name)
    test_src = TEST_FILE_TEMPLATE.format(
        section_dir=section_dir.name,
        struct_name=struct_name,
        short_name=short_name,
    )
    test_yh.write_text(test_src, encoding="utf-8")
    print(f"  {section_dir.name}: wrote test_statute.yh")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--section", required=True)
    p.add_argument("--short-name", required=True,
                   help="snake_case short name, e.g. robbery_with_hurt")
    args = p.parse_args()
    try:
        add_helper_fn_and_test(args.section, args.short_name)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
