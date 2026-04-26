#!/usr/bin/env python3
"""Cross-validate the synthesised contrast scenarios against the
curated case-law corpus.

Phase 2c Direction B follow-up. The Z3-driven bulk-contrast driver
(``scripts/bulk_contrast.py``) emits ~115 satisfying-assignment
fact patterns per doctrinally-related section pair under
``library/penal_code/_corpus/contrast/<a>_vs_<b>.json``. The
case-law harness (``evals/case_law/``) curates ~23 real Singapore
criminal cases each with an ``actual_charge`` + ``alternative_charge``.

This driver asks: **for how many of the 115 synthesised pairs do
we have a real case-law fixture covering the same (actual,
alternative) section pair?** A high match rate is evidence the
synthesis tool is producing scenarios that doctrinally matter
(courts have addressed the same boundary); a low rate means the
synthesis covers paper-relevant pairs the case-law sample does
not yet exercise.

The match is purely structural — the synthesised fact pattern
and the case-law fact pattern can differ wildly while sharing the
same section-pair. We do not (in this v0) attempt fact-level
similarity; that is left to a v2 with embedding similarity over
the scenarios.

Usage::

    python scripts/contrast_caselaw_validation.py
    python scripts/contrast_caselaw_validation.py --json --out evals/case_law/results-contrast-validation.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
CONTRAST_DIR = REPO / "library" / "penal_code" / "_corpus" / "contrast"
CASE_LAW_DIR = REPO / "evals" / "case_law" / "fixtures"

sys.path.insert(0, str(REPO / "evals" / "case_law"))


def _canonical(s: Optional[str]) -> str:
    if not s:
        return ""
    raw = str(s).strip().strip(".").strip()
    raw = re.sub(r"^(?:section|sec\.?|s\.?)\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\(.*", "", raw)
    return raw.strip()


def _load_contrast_pairs(directory: Path) -> List[Tuple[str, str, str]]:
    """Return [(actual, alternative, source_file), …] from each per-pair
    contrast JSON file under `directory`."""
    pairs: List[Tuple[str, str, str]] = []
    for fp in sorted(directory.glob("s*_vs_s*.json")):
        try:
            payload = json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        a = _canonical(payload.get("section_a"))
        b = _canonical(payload.get("section_b"))
        if a and b:
            pairs.append((a, b, fp.name))
    return pairs


def _load_case_law_pairs(directory: Path) -> List[Tuple[str, str, str]]:
    """Return [(actual, alternative, fixture_id), …] from each case-law
    fixture YAML that carries both fields."""
    try:
        import yaml  # type: ignore
        loader = lambda txt: yaml.safe_load(txt)
    except ImportError:
        sim_dir = REPO / "simulator"
        if str(sim_dir) not in sys.path:
            sys.path.insert(0, str(sim_dir))
        from simulator import _mini_yaml  # type: ignore
        loader = _mini_yaml

    pairs: List[Tuple[str, str, str]] = []
    for fp in sorted(directory.glob("*.yaml")):
        try:
            raw = loader(fp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(raw, dict):
            continue
        a = _canonical(raw.get("actual_charge"))
        b = _canonical(raw.get("alternative_charge"))
        fid = str(raw.get("id", fp.stem))
        if a and b:
            pairs.append((a, b, fid))
    return pairs


def cross_validate(
    contrast_pairs: List[Tuple[str, str, str]],
    case_law_pairs: List[Tuple[str, str, str]],
) -> Dict[str, Any]:
    """For each contrast pair, check whether any case-law fixture covers
    the same (actual, alternative) ordered pair. Also reports the
    *unordered* match (case-law has the inverse pair). -- bidirectional
    match is structurally meaningful: if a court chose A over B, the
    contrast tool's distinguisher between A and B is doctrinally
    relevant regardless of which side our synthesis put first."""
    case_law_ordered: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    case_law_unordered: Dict[frozenset, List[str]] = defaultdict(list)
    for a, b, fid in case_law_pairs:
        case_law_ordered[(a, b)].append(fid)
        case_law_unordered[frozenset([a, b])].append(fid)

    matched_ordered: List[Dict[str, Any]] = []
    matched_unordered: List[Dict[str, Any]] = []
    unmatched: List[Dict[str, Any]] = []

    for a, b, src in contrast_pairs:
        ordered_hits = case_law_ordered.get((a, b), [])
        unordered_hits = case_law_unordered.get(frozenset([a, b]), [])
        if ordered_hits:
            matched_ordered.append({
                "contrast_pair": [a, b],
                "case_law_fixtures": ordered_hits,
                "source_file": src,
            })
        elif unordered_hits:
            matched_unordered.append({
                "contrast_pair": [a, b],
                "case_law_fixtures": unordered_hits,
                "source_file": src,
                "note": "unordered match — case-law fixture has the inverse pair",
            })
        else:
            unmatched.append({
                "contrast_pair": [a, b],
                "source_file": src,
            })

    return {
        "n_contrast_pairs": len(contrast_pairs),
        "n_case_law_pairs": len(case_law_pairs),
        "n_matched_ordered": len(matched_ordered),
        "n_matched_unordered": len(matched_unordered),
        "n_unmatched": len(unmatched),
        "match_rate_ordered":
            len(matched_ordered) / len(contrast_pairs) if contrast_pairs else 0.0,
        "match_rate_any":
            (len(matched_ordered) + len(matched_unordered)) / len(contrast_pairs)
            if contrast_pairs else 0.0,
        "matched_ordered": matched_ordered[:20],
        "matched_unordered": matched_unordered[:20],
        "unmatched_sample": unmatched[:20],
        "case_law_pair_summary": [
            {"pair": list(k), "fixtures": v}
            for k, v in sorted(case_law_unordered.items(), key=lambda x: -len(x[1]))
        ],
        "not_legal_advice": True,
        "disclaimer": (
            "Match-rate measures structural overlap between the "
            "Z3-synthesised contrast pairs and the curated case-law "
            "corpus. A low rate means the synthesis exercises section "
            "boundaries the case-law sample does not yet cover (or "
            "vice versa), not that either is wrong."
        ),
    }


def render(report: Dict[str, Any]) -> str:
    lines = [
        "Phase 2c Direction B — contrast vs case-law cross-validation",
        "",
        f"  contrast pairs            : {report['n_contrast_pairs']}",
        f"  case-law pairs            : {report['n_case_law_pairs']}",
        f"  matched (ordered)         : {report['n_matched_ordered']}",
        f"  matched (unordered)       : {report['n_matched_unordered']}",
        f"  unmatched                 : {report['n_unmatched']}",
        "",
        f"  ordered match rate        : {report['match_rate_ordered']:.1%}",
        f"  any-direction match rate  : {report['match_rate_any']:.1%}",
        "",
        "Case-law-covered section pairs (most-fixtured first):",
    ]
    for entry in report["case_law_pair_summary"][:10]:
        a, b = entry["pair"]
        lines.append(f"  s{a:6s} ↔ s{b:6s}  fixtures={len(entry['fixtures'])}")
    if report["matched_ordered"]:
        lines.append("")
        lines.append("Ordered-direction matches (sample):")
        for m in report["matched_ordered"][:10]:
            a, b = m["contrast_pair"]
            lines.append(
                f"  s{a:6s} ↔ s{b:6s}  ← {m['case_law_fixtures'][0]}"
            )
    lines.append("")
    lines.append("Not legal advice — structural-overlap measure only.")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--contrast-dir", type=Path, default=CONTRAST_DIR)
    p.add_argument("--case-law-dir", type=Path, default=CASE_LAW_DIR)
    p.add_argument("--json", dest="json_out", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    if not args.contrast_dir.exists():
        print(f"error: contrast corpus missing at {args.contrast_dir} "
              f"(run scripts/bulk_contrast.py first)", file=sys.stderr)
        return 2
    if not args.case_law_dir.exists():
        print(f"error: case-law fixtures missing at {args.case_law_dir}",
              file=sys.stderr)
        return 2

    contrast_pairs = _load_contrast_pairs(args.contrast_dir)
    case_law_pairs = _load_case_law_pairs(args.case_law_dir)
    report = cross_validate(contrast_pairs, case_law_pairs)

    output = (
        json.dumps(report, indent=2, ensure_ascii=False)
        if args.json_out else render(report)
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"wrote: {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
