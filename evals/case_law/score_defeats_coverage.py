#!/usr/bin/env python3
"""Defeats-edge structural-coverage sweep for ``yuho narrow-defence``.

For every ``(offence, defence)`` pair where the encoded library
carries a ``general_defence_s<N>`` edge on the offence section,
runs ``yuho narrow-defence offence defence`` and records:

* whether Z3 returns a satisfying structural assignment (the
  smallest fact-set where both the offence's elements and the
  defence's elements fire);
* the structural-floor size — number of element flags set true
  in the returned model — per side;
* per-defence and per-cluster aggregation.

Output is the empirical artefact paper §7.6's ``defeats edge
coverage'' paragraph cites: it shows that the bulk-inserted
edges are not just syntactically present but Z3-actionable. The
sweep ran end-to-end after the Direction B v3 expansion (610
edges across 147 sections; 15 distinct Chapter IV defences).

Usage::

    python evals/case_law/score_defeats_coverage.py
    python evals/case_law/score_defeats_coverage.py --json \\
        --out evals/case_law/results-defeats-coverage.json

The structural-floor model is read from
``yuho narrow-defence --json`` so we don't shell out per pair.
The script lifts the same library walker used elsewhere; see
``score_recommend.py`` for the matching pattern.

NOT legal advice. The metric is structural availability of the
defence under Yuho's encoded model — whether the defence is
both present in the corpus *and* satisfiable by the Z3 backend
on a non-degenerate fact-set. It does *not* assess whether the
defence will succeed evidentially on any given case.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
LIB = REPO / "library" / "penal_code"

# Cluster mapping for the per-cluster aggregation. Keyed by
# section-number prefix; matches the cluster names used in
# Direction B's TODO breakdown.
CLUSTERS: List[Tuple[str, List[range]]] = [
    ("homicide", [range(299, 309)]),
    ("hurt", [range(319, 339)]),
    ("sexual", [range(354, 378)]),
    ("kidnapping", [range(359, 375)]),
    ("property_theft", [range(378, 383)]),
    ("property_robbery", [range(390, 395)]),
    ("property_misappropriation", [range(403, 405)]),
    ("property_breach_of_trust", [range(405, 410)]),
    ("property_cheating", [range(415, 421)]),
    ("forgery", [range(463, 478)]),
    ("intimidation", [range(503, 507)]),
    ("mischief", [range(425, 441)]),
    ("trespass", [range(441, 463)]),
    ("abetment", [range(107, 121)]),
    ("defamation", [range(499, 503)]),
    ("attempt", [range(511, 512)]),
]


def _section_num(section_dir_name: str) -> Optional[Tuple[int, str]]:
    """``s299_culpable_homicide`` -> (299, '299'); ``s376AA_…`` -> (376, '376AA')."""
    m = re.match(r"^s(\d+)([A-Z]*)_", section_dir_name)
    if not m:
        return None
    return (int(m.group(1)), m.group(1) + m.group(2))


def _cluster_for(section_id: int) -> str:
    """Map a numeric section to its cluster name (or 'other')."""
    for name, ranges in CLUSTERS:
        for r in ranges:
            if section_id in r:
                return name
    return "other"


def collect_edges() -> List[Tuple[str, int]]:
    """Walk every encoded section and extract ``(offence, defence)``
    pairs from each ``general_defence_s<N>`` block."""
    pattern = re.compile(r"general_defence_s(\d+)")
    out: List[Tuple[str, int]] = []
    for section_dir in sorted(LIB.iterdir()):
        if not section_dir.is_dir() or section_dir.name.startswith("_"):
            continue
        sid = _section_num(section_dir.name)
        if sid is None:
            continue
        offence = sid[1]
        yh = section_dir / "statute.yh"
        if not yh.exists():
            continue
        text = yh.read_text(encoding="utf-8")
        for m in pattern.finditer(text):
            out.append((offence, int(m.group(1))))
    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for pair in out:
        if pair not in seen:
            seen.add(pair)
            deduped.append(pair)
    return deduped


def run_narrow_defence(offence: str, defence: int,
                       timeout: int = 30000) -> Dict[str, Any]:
    """Shell out to ``yuho narrow-defence --json`` and parse the
    response."""
    cmd = [
        "yuho", "narrow-defence",
        f"s{offence}", f"s{defence}",
        "--json",
        "--timeout", str(timeout),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=int(timeout / 1000) + 30,
        )
    except subprocess.TimeoutExpired:
        return {"sat": False, "error": "timeout"}
    if proc.returncode != 0:
        return {"sat": False, "error": proc.stderr.strip()[:200] or "non-zero exit"}
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {"sat": False, "error": f"json decode: {exc}"}


def score_one(offence: str, defence: int) -> Dict[str, Any]:
    """Run narrow-defence on a single pair, normalise the result."""
    raw = run_narrow_defence(offence, defence)
    out: Dict[str, Any] = {
        "offence": offence,
        "defence": defence,
        "sat": False,
        "offence_floor": 0,
        "defence_floor": 0,
    }
    if raw.get("error"):
        out["error"] = raw["error"]
        return out
    # `narrow-defence --json` returns:
    #   {overlap: bool, offence: "s300", defence: "s84",
    #    fact_pattern: {s<N>_elements: {<element>: bool, …}, …},
    #    shared_satisfied_names: [...]}
    out["sat"] = bool(raw.get("overlap"))
    fp = raw.get("fact_pattern") or {}
    off_key = f"s{offence}_elements"
    def_key = f"s{defence}_elements"
    if isinstance(fp.get(off_key), dict):
        out["offence_floor"] = sum(1 for v in fp[off_key].values() if v)
    if isinstance(fp.get(def_key), dict):
        out["defence_floor"] = sum(1 for v in fp[def_key].values() if v)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--json", dest="json_out", action="store_true",
                   help="Emit JSON instead of human-readable text")
    p.add_argument("--out", type=Path, default=None,
                   help="Write report to this path (default: stdout)")
    p.add_argument("--timeout", type=int, default=30000,
                   help="Z3 solver timeout per pair (ms)")
    p.add_argument("--limit", type=int, default=0,
                   help="Cap number of pairs (0 = no cap; useful for smoke)")
    args = p.parse_args()

    pairs = collect_edges()
    if args.limit:
        pairs = pairs[: args.limit]
    print(f"sweeping {len(pairs)} (offence, defence) pairs…", file=sys.stderr)

    results: List[Dict[str, Any]] = []
    for i, (offence, defence) in enumerate(pairs, 1):
        r = score_one(offence, defence)
        results.append(r)
        if i % 50 == 0:
            sat_so_far = sum(1 for x in results if x["sat"])
            print(f"  [{i}/{len(pairs)}] sat={sat_so_far}", file=sys.stderr)

    # Aggregate
    by_defence: Dict[int, Dict[str, int]] = defaultdict(lambda: {"n": 0, "sat": 0})
    by_cluster: Dict[str, Dict[str, int]] = defaultdict(lambda: {"n": 0, "sat": 0})
    for r in results:
        sid = re.match(r"^(\d+)", r["offence"])
        cluster = _cluster_for(int(sid.group(1))) if sid else "other"
        by_defence[r["defence"]]["n"] += 1
        by_cluster[cluster]["n"] += 1
        if r["sat"]:
            by_defence[r["defence"]]["sat"] += 1
            by_cluster[cluster]["sat"] += 1

    n = len(results)
    sat_total = sum(1 for r in results if r["sat"])
    summary: Dict[str, Any] = {
        "n_pairs": n,
        "n_sat": sat_total,
        "sat_rate": (sat_total / n) if n else 0.0,
        "by_defence": {str(k): v for k, v in sorted(by_defence.items())},
        "by_cluster": dict(sorted(by_cluster.items())),
        "pairs": results,
        "not_legal_advice": True,
        "disclaimer": (
            "Sat-rate measures structural availability of each "
            "(offence, defence) pair under Yuho's encoded model — "
            "whether Z3 returns a satisfying assignment for both sides' "
            "elements simultaneously. Does not measure whether any "
            "given defence will succeed evidentially on any given case."
        ),
    }

    if args.json_out:
        output = json.dumps(summary, indent=2)
    else:
        lines = [
            f"defeats-edge structural-coverage sweep (n={n} pairs)",
            "",
            f"  SAT pairs: {sat_total}/{n}  ({summary['sat_rate']:.1%})",
            "",
            "Per-defence:",
        ]
        for d in sorted(by_defence):
            row = by_defence[d]
            rate = row["sat"] / row["n"] if row["n"] else 0
            lines.append(f"  s{d:>4}: {row['sat']:>3d} / {row['n']:>3d}  ({rate:.0%})")
        lines.append("")
        lines.append("Per-cluster:")
        for c in sorted(by_cluster):
            row = by_cluster[c]
            rate = row["sat"] / row["n"] if row["n"] else 0
            lines.append(f"  {c:>26s}: {row['sat']:>3d} / {row['n']:>3d}  ({rate:.0%})")
        lines.append("")
        lines.append("Not legal advice — structural availability only.")
        output = "\n".join(lines)

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"wrote: {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
