#!/usr/bin/env python3
"""Generate Lean fixtures for the full Singapore Penal Code corpus.

Walks `library/penal_code/*/statute.yh`, parses each via the Yuho
parser, and emits a single `mechanisation/scripts/Fixtures.lean`
file containing one `def s<N> : Statute` per encoded section plus
a `fixtures : List (String × Statute)` aggregate the export
script consumes.

Used by `scripts/verify_structural_diff.py` (full-corpus mode) to
extend the four-fixture PoC harness across all 524 sections of the
encoded library.

Notes
-----
* Element kind mapping: ``actus_reus``/``mens_rea``/``circumstance``
  map to the matching Lean :class:`ElementKind` constructor; any
  other kind (``deontic``, ``definitional``, etc.) is treated as
  ``circumstance`` for emit purposes since the structural diff only
  cares about the bicond skeleton and the three Lean-known kinds.
* Exception guards are placeholder ``fun F => F "<atom>"`` lambdas
  with a unique per-section atom name; the structural harness skips
  inner-shape comparison on ``_fires`` biconds, so guard semantics
  don't influence the diff.
* Sections whose elements are declared only inside subsections
  (general defences in ss76–s106) are flattened by the Z3 generator
  on the Python side; this generator hoists subsection elements to
  the top level for parity.
* Section numbers carrying a dot (``390A``-style) are not currently
  represented in the live corpus, but if they appear we replace ``.``
  with ``_`` so the emitted Lean identifier stays valid.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from yuho.ast import ASTBuilder  # noqa: E402
from yuho.ast.nodes import (  # noqa: E402
    ElementGroupNode,
    ElementNode,
    StatuteNode,
)
from yuho.parser import get_parser  # noqa: E402

LIBRARY = REPO / "library" / "penal_code"
OUT = REPO / "mechanisation" / "scripts" / "Fixtures.lean"

KIND_MAP = {
    "actus_reus": ".actusReus",
    "mens_rea": ".mensRea",
    "circumstance": ".circumstance",
}


def _kind(elem_type: str) -> str:
    return KIND_MAP.get(elem_type, ".circumstance")


def _esc(s: str) -> str:
    """Escape a string for Lean source literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _safe_id(name: str) -> str:
    """Lean-safe identifier — strip non-alnum characters."""
    return re.sub(r"[^A-Za-z0-9_]", "_", name)


def _emit_element(elem) -> str:
    """Render an Element / ElementGroup as a Lean ElementGroup expression."""
    if isinstance(elem, ElementNode):
        return (
            f'.leaf {{ kind := {_kind(elem.element_type)}, '
            f'name := "{_esc(elem.name)}", description := "" }}'
        )
    if isinstance(elem, ElementGroupNode):
        ctor = ".allOf" if elem.combinator == "all_of" else ".anyOf"
        members = ", ".join(_emit_element(m) for m in elem.members)
        return f"{ctor} [{members}]"
    raise TypeError(f"unexpected element shape: {type(elem).__name__}")


def _flatten_for_topelems(statute: StatuteNode) -> List:
    """Mirror `_generate_statute_constraints`: when top-level elements
    are absent, recursively hoist subsection elements to the top
    level. The recursive walk matches the Z3 generator's deepening
    landed 2026-04-30, which was needed for s305's
    `subsection (1) (a) { elements { … } }` 2-level nesting."""
    if statute.elements:
        return list(statute.elements)
    out: List = []
    def _walk(subs):
        for sub in subs or ():
            for elem in getattr(sub, "elements", ()) or ():
                out.append(elem)
            _walk(getattr(sub, "subsections", ()))
    _walk(getattr(statute, "subsections", ()) or ())
    return out


def _emit_elements(statute: StatuteNode) -> str:
    """Render the top-level element list as a single ElementGroup
    (implicit all_of, per §4.2)."""
    elems = _flatten_for_topelems(statute)
    if not elems:
        return ".allOf []"
    if len(elems) == 1 and isinstance(elems[0], ElementGroupNode):
        return _emit_element(elems[0])
    members = ", ".join(_emit_element(e) for e in elems)
    return f".allOf [{members}]"


def _emit_exceptions(statute: StatuteNode) -> str:
    """Render the exception list. Guards are placeholder lambdas; the
    structural harness skips inner-shape comparison on `_fires`."""
    parts: List[str] = []
    for i, exc in enumerate(statute.exceptions):
        label = exc.label or f"exception_{i}"
        defeats = exc.defeats
        defeats_lit = (
            f"[{', '.join(chr(34) + _esc(d) + chr(34) for d in [defeats])}]"
            if defeats
            else "[]"
        )
        parts.append(
            f'  {{ label := "{_esc(label)}", '
            f'guard := fun F => F "exc_{_safe_id(label)}", '
            f"defeats := {defeats_lit} }}"
        )
    if not parts:
        return "[]"
    return "[\n" + ",\n".join(parts) + "\n]"


def _emit_statute(name: str, statute: StatuteNode) -> str:
    """Emit a single `def s<safe_id> : Statute := { … }`."""
    return (
        f"def {name} : Statute :=\n"
        f"  {{ section_number := \"{_esc(statute.section_number)}\"\n"
        f'    title := "{_esc(getattr(statute.title, "value", "") if statute.title else "")}"\n'
        f"    elements := {_emit_elements(statute)}\n"
        f"    exceptions := {_emit_exceptions(statute)}\n"
        f"  }}\n"
    )


def _parse_statute(path: Path) -> StatuteNode | None:
    """Parse a statute.yh into a StatuteNode (first statute only)."""
    parser = get_parser()
    try:
        result = parser.parse_file(path)
    except Exception:
        return None
    if result.errors or result.root_node is None:
        return None
    try:
        ast = ASTBuilder(result.source, str(path)).build(result.root_node)
    except Exception:
        return None
    return ast.statutes[0] if ast.statutes else None


def main() -> int:
    if not LIBRARY.is_dir():
        print(f"library not found: {LIBRARY}", file=sys.stderr)
        return 2

    paths = sorted(LIBRARY.glob("*/statute.yh"))
    print(f"→ parsing {len(paths)} statutes…")

    entries: List[tuple[str, StatuteNode]] = []
    skipped: List[str] = []
    for p in paths:
        statute = _parse_statute(p)
        if statute is None:
            skipped.append(p.parent.name)
            continue
        # Guard against duplicate section numbers — the linter
        # flags these elsewhere; emit only the first occurrence.
        ident = "s" + _safe_id(statute.section_number)
        if any(e[0] == ident for e in entries):
            skipped.append(f"{p.parent.name} (duplicate {ident})")
            continue
        entries.append((ident, statute))

    print(f"→ encoded {len(entries)} statutes ({len(skipped)} skipped)")

    body = [
        "-- Auto-generated by `mechanisation/scripts/generate_fixtures.py`.",
        "-- Do not edit by hand; regenerate via",
        "--   python3 mechanisation/scripts/generate_fixtures.py",
        "import Yuho",
        "",
        "open Yuho",
        "",
        "namespace Yuho.Fixtures",
        "",
    ]
    for name, statute in entries:
        body.append(_emit_statute(name, statute))

    body.append("def fixtures : List (String × Statute) :=")
    body.append("  [")
    pairs = ",\n".join(f'    ("{n}", {n})' for n, _ in entries)
    body.append(pairs)
    body.append("  ]")
    body.append("")
    body.append("end Yuho.Fixtures")
    body.append("")

    OUT.write_text("\n".join(body), encoding="utf-8")
    print(f"→ wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size:,} bytes)")
    if skipped:
        print(f"  skipped: {', '.join(skipped[:10])}"
              + (f" … +{len(skipped)-10} more" if len(skipped) > 10 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
