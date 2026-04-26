#!/usr/bin/env python3
"""Bulk Z3-driven contrast across the encoded library.

For every doctrinally-related pair `(A, B)` in the encoded library
(default: pairs sharing a non-trivial SCC + every explicit
``subsumes`` edge), run ``yuho contrast`` and persist the satisfying
fact pattern. Output:

    library/penal_code/_corpus/contrast/
    ├── index.json                   -- {pair: relpath, n_pairs, ...}
    ├── s299_vs_s300.json
    ├── s302_vs_s299.json
    └── …

Each per-pair file is the same JSON shape ``yuho contrast --json``
emits, plus a ``pair_kind`` field annotating why the pair was
selected (``subsumes`` / ``scc`` / ``referenced``).

Usage::

    python scripts/bulk_contrast.py
    python scripts/bulk_contrast.py --minimal      # use z3.Optimize
    python scripts/bulk_contrast.py --max-pairs 50 # cap the run
    python scripts/bulk_contrast.py --library library/penal_code

Skips per-pair failures (Z3 timeouts, sections without elements)
without aborting the run; failures are logged in the index.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))


def _collect_pairs(library_dir: Path) -> List[Tuple[str, str, str]]:
    """Return [(a, b, kind), …] for every contrast-worthy pair.

    Three sources:

    - SCC pairs: every (a, b) with a != b inside a non-trivial SCC of
      the implicit + subsumes reference graph.
    - Subsumes pairs: every (a, b) with an explicit `subsumes` edge.
    - Referenced pairs: every (a, b) with an implicit cross-reference
      edge (typically textual mentions in element / illustration
      bodies).

    Deduped — `(a, b)` and `(b, a)` are stored as separate entries
    (the contrast Z3 query is asymmetric: A satisfied, B not).
    """
    from yuho.library.reference_graph import build_reference_graph

    graph = build_reference_graph(library_dir)
    pairs: List[Tuple[str, str, str]] = []
    seen: Set[Tuple[str, str]] = set()

    def _push(a: str, b: str, kind: str) -> None:
        if a == b:
            return
        key = (a, b)
        if key in seen:
            return
        seen.add(key)
        pairs.append((a, b, kind))

    # Walk every outgoing edge once; the ReferenceGraph exposes
    # adjacency by source/kind via `out_edges` (no flat .edges accessor).
    for src, edges in graph.out_edges.items():
        for edge in edges:
            if edge.kind == "subsumes":
                _push(edge.src, edge.dst, "subsumes")
                _push(edge.dst, edge.src, "subsumes")
            elif edge.kind in ("referenced", "implicit"):
                _push(edge.src, edge.dst, "referenced")

    # SCC pairs (implicit + subsumes).
    for component in graph.cycles(("implicit", "subsumes")):
        component = sorted(component)
        for i in range(len(component)):
            for j in range(len(component)):
                if i == j:
                    continue
                _push(component[i], component[j], "scc")

    return pairs


def _run_one(
    a: str, b: str, library_dir: Path, *, minimal: bool, timeout_ms: int,
) -> Tuple[bool, Dict]:
    """Run contrast for one pair. Returns (ok, payload-or-error)."""
    # Direct call into the command implementation rather than a
    # subprocess — the CLI calls sys.exit, which would kill us.
    from yuho.cli.commands.contrast import (
        _build_combined_module, _read_model_facts, _statute_yh_for,
    )

    a_path = _statute_yh_for(library_dir, a)
    b_path = _statute_yh_for(library_dir, b)
    if a_path is None or b_path is None:
        return False, {"error": "section path not found", "pair": [a, b]}

    try:
        import z3
        module = _build_combined_module([a_path, b_path])
        from yuho.verify.z3_solver import Z3Generator
        gen = Z3Generator()
        gen.generate(module)

        a_id = a.lstrip("sS").replace(".", "_")
        b_id = b.lstrip("sS").replace(".", "_")
        a_conv = gen._consts.get(f"{a_id}_conviction")
        b_conv = gen._consts.get(f"{b_id}_conviction")
        if a_conv is None or b_conv is None:
            return False, {
                "error": "no elements declared for one of the sections",
                "pair": [a, b],
                "missing": [
                    s for s, c in [(a, a_conv), (b, b_conv)] if c is None
                ],
            }

        if minimal:
            solver = z3.Optimize()
            solver.set("timeout", timeout_ms)
            for assertion in gen._assertions:
                solver.add(assertion)
            solver.add(a_conv)
            solver.add(z3.Not(b_conv))
            weight_terms = [
                z3.If(var, 1, 0)
                for name, var in gen._consts.items()
                if name.endswith("_satisfied")
                and name not in (f"{a_id}_elements_satisfied",
                                 f"{b_id}_elements_satisfied")
            ]
            if weight_terms:
                solver.minimize(z3.Sum(*weight_terms))
        else:
            solver = z3.Solver()
            solver.set("timeout", timeout_ms)
            for assertion in gen._assertions:
                solver.add(assertion)
            solver.add(a_conv)
            solver.add(z3.Not(b_conv))

        result = solver.check()
        if result != z3.sat:
            return False, {
                "error": "no contrast model",
                "z3_status": str(result),
                "pair": [a, b],
            }

        model = solver.model()
        a_facts = _read_model_facts(model, gen._consts, a_id)
        b_facts = _read_model_facts(model, gen._consts, b_id)
        return True, {
            "contrast": True,
            "section_a": a,
            "section_b": b,
            "fact_pattern": {
                f"{a}_elements": a_facts,
                f"{b}_elements": b_facts,
            },
            "a_conviction": True,
            "b_conviction": False,
            "minimal": minimal,
            "not_legal_advice": True,
        }
    except Exception as exc:  # noqa: BLE001 — keep run resilient
        return False, {"error": f"{type(exc).__name__}: {exc}", "pair": [a, b]}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--library", default=str(REPO / "library" / "penal_code"))
    p.add_argument("--out-dir",
                   help="Override output directory (default: "
                        "<library>/_corpus/contrast/)")
    p.add_argument("--minimal", action="store_true",
                   help="Use z3.Optimize for smallest fact-sets")
    p.add_argument("--timeout-ms", type=int, default=15000,
                   help="Per-pair Z3 timeout (default 15000)")
    p.add_argument("--max-pairs", type=int, default=0,
                   help="Cap number of pairs (0 = no cap)")
    p.add_argument("--kinds", nargs="*",
                   choices=["subsumes", "scc", "referenced"],
                   help="Only run pairs of the given kinds")
    args = p.parse_args()

    lib = Path(args.library)
    if not lib.exists():
        print(f"error: library not found at {lib}", file=sys.stderr)
        return 2

    out_dir = Path(args.out_dir) if args.out_dir else lib / "_corpus" / "contrast"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Collecting contrast-worthy pairs from {lib}…", file=sys.stderr)
    pairs = _collect_pairs(lib)
    if args.kinds:
        pairs = [p for p in pairs if p[2] in set(args.kinds)]
    if args.max_pairs:
        pairs = pairs[: args.max_pairs]

    print(f"  {len(pairs)} pairs to run "
          f"(minimal={args.minimal}, timeout={args.timeout_ms}ms)",
          file=sys.stderr)

    index: Dict[str, Dict] = {}
    n_ok = n_fail = 0
    t0 = time.monotonic()
    for i, (a, b, kind) in enumerate(pairs, 1):
        ok, payload = _run_one(
            a, b, lib, minimal=args.minimal, timeout_ms=args.timeout_ms
        )
        slug = f"s{a}_vs_s{b}.json"
        if ok:
            payload["pair_kind"] = kind
            (out_dir / slug).write_text(
                json.dumps(payload, indent=2, ensure_ascii=False)
            )
            n_ok += 1
            index[slug] = {"pair": [a, b], "kind": kind, "ok": True}
        else:
            n_fail += 1
            index[slug] = {"pair": [a, b], "kind": kind, "ok": False,
                           "error": payload.get("error", "unknown")}
        if i % 25 == 0 or i == len(pairs):
            elapsed = time.monotonic() - t0
            rate = i / elapsed if elapsed else 0
            print(f"  [{i}/{len(pairs)}]  ok={n_ok}  fail={n_fail}  "
                  f"({rate:.1f}/s)", file=sys.stderr)

    summary = {
        "n_pairs": len(pairs),
        "n_ok": n_ok,
        "n_fail": n_fail,
        "minimal": args.minimal,
        "timeout_ms": args.timeout_ms,
        "kinds": sorted({p[2] for p in pairs}),
        "pairs": index,
        "elapsed_seconds": round(time.monotonic() - t0, 2),
        "not_legal_advice": True,
    }
    (out_dir / "index.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False)
    )
    print(f"done: {n_ok}/{len(pairs)} pairs landed → {out_dir}", file=sys.stderr)
    return 0 if n_ok > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
