#!/usr/bin/env python3
"""CI-style: round-trip every encoded statute through the AKN transpiler
and assert each emitted XML document validates structurally.

Exits non-zero on the first invalid document. Output JSON to stdout when
``--json`` is set.

Usage:
    python3 scripts/akn_roundtrip.py
    python3 scripts/akn_roundtrip.py --json
    python3 scripts/akn_roundtrip.py --library library/penal_code
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from yuho.services.analysis import analyze_file  # noqa: E402
from yuho.transpile import TranspileTarget, get_transpiler  # noqa: E402
from yuho.transpile.akn_validator import validate_akn  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--library", default=str(REPO / "library" / "penal_code"))
    p.add_argument("--json", dest="json_out", action="store_true")
    p.add_argument("--max-errors", type=int, default=20)
    args = p.parse_args()

    lib = Path(args.library)
    if not lib.exists():
        print(f"error: library not found at {lib}", file=sys.stderr)
        return 2

    transpiler = get_transpiler(TranspileTarget.AKOMANTOSO)
    n_total = 0
    n_pass = 0
    failures: list[dict] = []

    for yh in sorted(lib.glob("*/statute.yh")):
        n_total += 1
        result = analyze_file(yh, run_semantic=False)
        if result.ast is None:
            failures.append({
                "section": yh.parent.name,
                "stage": "parse",
                "errors": [str(e) for e in result.parse_errors][:3],
            })
            continue
        try:
            xml = transpiler.transpile(result.ast)
        except Exception as exc:
            failures.append({
                "section": yh.parent.name,
                "stage": "transpile",
                "errors": [str(exc)],
            })
            continue
        v = validate_akn(xml)
        if v.ok:
            n_pass += 1
        else:
            failures.append({
                "section": yh.parent.name,
                "stage": "validate",
                "errors": list(v.errors)[: args.max_errors],
            })

    summary = {
        "n_total": n_total,
        "n_pass": n_pass,
        "n_fail": len(failures),
        "failures": failures[: args.max_errors],
    }

    if args.json_out:
        print(json.dumps(summary, indent=2))
    else:
        print(f"AKN round-trip: {n_pass}/{n_total} validate clean")
        if failures:
            print(f"\nFirst {min(len(failures), 5)} failures:")
            for f in failures[:5]:
                print(f"  {f['section']:60s}  {f['stage']:10s}  "
                      f"{f['errors'][0] if f['errors'] else ''}"[:160])
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
