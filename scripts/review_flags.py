#!/usr/bin/env python3
"""Manual L3 flag review helper.

For every flagged section under ``library/penal_code/s*/_L3_FLAG.md``,
produces a structured review record with:

* the flag's failed-check number, reason, and suggested fix
* the canonical SSO text (truncated)
* the encoded .yh source (truncated)
* a heuristic VERDICT recommendation:
    - STAMP_OVERRIDE   = flag is likely spurious; encoding looks faithful
    - FIX_NEEDED       = flag is likely correct; an automated fix is plausible
    - INVESTIGATE      = flag needs a human read

Output is written to ``library/penal_code/_L3_review/`` as Markdown grouped
by failed-check number, plus a top-level summary.

Usage:
    python3 scripts/review_flags.py
    python3 scripts/review_flags.py --section 415        # one section
    python3 scripts/review_flags.py --check 9            # one check group
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
LIBRARY = REPO / "library" / "penal_code"
RAW = LIBRARY / "_raw" / "act.json"
OUT_DIR = LIBRARY / "_L3_review"


# ---------------------------------------------------------------------------
# Heuristic verdicts
# ---------------------------------------------------------------------------


def verdict_for(check: int, reason: str, fix: str, raw_text: str, yh: str) -> Tuple[str, str]:
    """Return (label, rationale) for a flag.

    Conservative: only call STAMP_OVERRIDE when the encoded content
    visibly addresses the flag's concern. Otherwise FIX_NEEDED if there's
    a clear mechanical fix; INVESTIGATE if not.
    """
    rl = (reason or "").lower()
    fl = (fix or "").lower()
    rt = (raw_text or "").lower()
    yhl = (yh or "").lower()

    # check 9: effective-date sanity
    if check == 9:
        # look for amendment markers like [N/YYYY] in the canonical text
        amend_match = re.findall(r"\[\d+/\d{4}\]", raw_text or "")
        # look for `effective <DATE>` lines in the encoding
        eff = re.findall(r"effective\s+(\d{4}-\d{2}-\d{2})", yh)
        if amend_match and len(eff) <= 1:
            return ("FIX_NEEDED",
                    f"raw text mentions amendments {amend_match}; encoding has only {eff}. "
                    f"Add amendment effective dates.")
        if amend_match and len(eff) > 1:
            return ("STAMP_OVERRIDE",
                    f"encoding already carries multiple effective dates {eff}; flag may be spurious.")
        return ("INVESTIGATE", "no amendment markers detected; flag reasoning unclear")

    # check 7: fabricated penalty facts
    if check == 7:
        # check for unlimited fine in raw text vs numeric range in encoding
        canonical_unlimited = bool(re.search(r"\bwith fine\b(?!.*\b(?:not exceeding|of \$|may extend))",
                                             raw_text or "", re.IGNORECASE))
        encoded_numeric = bool(re.search(r"fine\s*:=\s*\$[0-9]", yh))
        if canonical_unlimited and encoded_numeric:
            return ("FIX_NEEDED", "canonical 'with fine' suggests unlimited; encoding uses numeric range. "
                                  "Switch to `fine := unlimited`.")
        canonical_caning_unspec = bool(re.search(r"liable to caning(?!\s*\b(?:not exceeding|with))",
                                                  raw_text or "", re.IGNORECASE))
        encoded_caning_numeric = bool(re.search(r"caning\s*:=\s*\d+", yh))
        if canonical_caning_unspec and encoded_caning_numeric:
            return ("FIX_NEEDED", "canonical 'liable to caning' is unspecified; encoding uses numeric strokes. "
                                  "Switch to `caning := unspecified`.")
        return ("INVESTIGATE", "penalty discrepancy needs side-by-side comparison")

    # check 8: all_of vs any_of
    if check == 8:
        has_or = bool(re.search(r"\b(?:,\s*or\b|\bany\s+of\b|\beither\b)", raw_text or "", re.IGNORECASE))
        has_and = bool(re.search(r"\b(?:,\s*and\b|\ball\s+of\b|\bevery\b)", raw_text or "", re.IGNORECASE))
        encoded_all = "all_of" in yh
        encoded_any = "any_of" in yh
        if has_or and encoded_all and not encoded_any:
            return ("FIX_NEEDED", "raw uses 'or' but encoding uses all_of without any_of — "
                                  "switch element grouping to any_of.")
        if has_and and encoded_any and not encoded_all:
            return ("FIX_NEEDED", "raw uses 'and' but encoding uses any_of — "
                                  "switch to all_of.")
        return ("INVESTIGATE", "connective mismatch unclear without close read")

    # check 6: subsections
    if check == 6:
        canonical_subsections = bool(re.search(r"\(\d+[A-Z]?\)", raw_text or ""))
        encoded_subsections = bool(re.search(r"\bsubsection\s*\(", yh))
        if canonical_subsections and not encoded_subsections:
            return ("FIX_NEEDED", "raw has numbered subsections; encoding has none. "
                                  "Add `subsection (N) {}` blocks.")
        if not canonical_subsections and encoded_subsections:
            return ("STAMP_OVERRIDE",
                    "encoding has subsections that the raw text doesn't structurally have, "
                    "but the encoding is more granular — likely defensible.")
        return ("INVESTIGATE", "subsection structure needs comparison")

    # check 5: exceptions
    if check == 5:
        return ("INVESTIGATE", "exception preservation needs canonical-vs-encoded comparison")

    # check 4: explanations preserved
    if check == 4:
        return ("INVESTIGATE", "check whether canonical explanations are present "
                               "as `///` comments or structured refinements")

    # check 3: illustration completeness
    if check == 3:
        canonical_illustrations = bool(re.search(r"^\s*\([a-z]\)", raw_text or "", re.MULTILINE))
        encoded_illustration_count = len(re.findall(r"^\s*illustration\s+\w+\s*\{", yh, re.MULTILINE))
        if canonical_illustrations and encoded_illustration_count == 0:
            return ("FIX_NEEDED", "raw has lettered illustrations; encoding has none.")
        return ("INVESTIGATE", "illustration count needs recounting")

    # check -1: no parsed failed-check field — typically structural or
    # sensitivity flags from the agent
    return ("INVESTIGATE", "no machine-readable check code; needs human read")


# ---------------------------------------------------------------------------
# Data load
# ---------------------------------------------------------------------------


def load_raw_index() -> Dict[str, Dict[str, Any]]:
    with RAW.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {sec["number"]: sec for sec in raw.get("sections", [])}


def parse_flag(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    out = {"raw_text": text, "failed_check": -1, "reason": "", "suggested_fix": ""}
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("- failed:"):
            try:
                out["failed_check"] = int(s.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif s.startswith("- reason:"):
            out["reason"] = s.split(":", 1)[1].strip()
        elif s.startswith("- suggested fix:"):
            out["suggested_fix"] = s.split(":", 1)[1].strip()
    return out


def section_number_from_dir(d: Path) -> str:
    stem = d.name[1:]  # drop leading 's'
    if "_" in stem:
        stem = stem.split("_", 1)[0]
    return stem


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------


def render_section_block(rec: Dict[str, Any]) -> str:
    """One section's review block as Markdown."""
    n = rec["section_number"]
    title = rec["title"]
    verdict = rec["verdict"]
    rationale = rec["rationale"]
    flag = rec["flag"]
    raw_excerpt = (rec["raw_text"] or "")[:500].replace("\n", " ")
    if len(rec["raw_text"]) > 500:
        raw_excerpt += "…"
    yh_excerpt = rec["yh"][:1200]

    return f"""### s{n} — {title}

**Verdict:** `{verdict}` — {rationale}

**Flag** (check {flag['failed_check']}):
- reason: {flag.get('reason') or '(none)'}
- suggested fix: {flag.get('suggested_fix') or '(none)'}

**Canonical text (first 500 chars):**

> {raw_excerpt}

**Encoded `.yh` (first 1200 chars):**

```yh
{yh_excerpt}
```

---

"""


def render_summary(by_check: Dict[int, List[Dict[str, Any]]],
                   by_verdict: Dict[str, List[Dict[str, Any]]]) -> str:
    total = sum(len(v) for v in by_check.values())
    lines = [
        "# L3 flag manual review",
        "",
        f"Generated review of all {total} flagged sections.",
        "",
        "## Summary by verdict",
        "",
        "| Verdict | Count | Meaning |",
        "|---|--:|---|",
    ]
    meanings = {
        "STAMP_OVERRIDE": "Flag is likely spurious. Encoding addresses the concern; safe to override and stamp.",
        "FIX_NEEDED": "Flag is correct; mechanical fix is plausible.",
        "INVESTIGATE": "Needs a human read — the heuristic can't decide.",
    }
    for v in ("STAMP_OVERRIDE", "FIX_NEEDED", "INVESTIGATE"):
        lines.append(f"| `{v}` | {len(by_verdict.get(v, []))} | {meanings[v]} |")

    lines.append("")
    lines.append("## Summary by failed check")
    lines.append("")
    lines.append("| Check | Description | Count |")
    lines.append("|--:|---|--:|")
    descriptions = {
        3: "Illustrations complete",
        4: "Explanations preserved",
        5: "Exceptions preserved",
        6: "Subsections preserved",
        7: "No fabricated penalty facts",
        8: "all_of vs any_of matches English",
        9: "Effective date sane",
        -1: "(no machine-readable failed-check code)",
    }
    for k in sorted(by_check):
        desc = descriptions.get(k, "(unknown)")
        lines.append(f"| {k} | {desc} | {len(by_check[k])} |")

    lines.append("")
    lines.append("## Per-check files")
    lines.append("")
    for k in sorted(by_check):
        desc = descriptions.get(k, "(unknown)")
        lines.append(f"- [check{k}.md](./check{k}.md) — {desc} ({len(by_check[k])} sections)")

    lines.append("")
    lines.append("## How to use this review")
    lines.append("")
    lines.append("1. For each `check<N>.md` file, scan the verdicts at the top of each block.")
    lines.append("2. Group by verdict and act:")
    lines.append("   - `STAMP_OVERRIDE` — manually stamp via metadata.toml (`last_verified = \"YYYY-MM-DD\"`).")
    lines.append("   - `FIX_NEEDED` — apply the suggested fix to `statute.yh`, re-run `yuho check`, then stamp.")
    lines.append("   - `INVESTIGATE` — open the section dir, read `_L3_FLAG.md` and the canonical SSO text together.")
    lines.append("3. After resolving a flag, delete `_L3_FLAG.md` and add a `last_verified` line to `metadata.toml`.")
    lines.append("4. Rebuild the corpus + ledger to reflect changes.")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--section", help="Build review for one section number")
    parser.add_argument("--check", type=int, help="Build review for one failed-check group")
    args = parser.parse_args()

    raw_index = load_raw_index()
    flag_files = sorted(LIBRARY.glob("s*/_L3_FLAG.md"))

    records: List[Dict[str, Any]] = []
    for fp in flag_files:
        section_dir = fp.parent
        section_num = section_number_from_dir(section_dir)
        if args.section and section_num != args.section:
            continue

        flag = parse_flag(fp)
        if args.check is not None and flag["failed_check"] != args.check:
            continue

        raw_entry = raw_index.get(section_num, {})
        raw_text = raw_entry.get("text", "")
        title = raw_entry.get("marginal_note", "")

        yh_path = section_dir / "statute.yh"
        yh = yh_path.read_text(encoding="utf-8") if yh_path.exists() else ""

        verdict, rationale = verdict_for(flag["failed_check"], flag["reason"],
                                          flag["suggested_fix"], raw_text, yh)
        records.append({
            "section_number": section_num,
            "title": title,
            "section_dir": str(section_dir.relative_to(REPO)),
            "raw_text": raw_text,
            "yh": yh,
            "flag": flag,
            "verdict": verdict,
            "rationale": rationale,
        })

    by_check: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    by_verdict: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for rec in records:
        by_check[rec["flag"]["failed_check"]].append(rec)
        by_verdict[rec["verdict"]].append(rec)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Per-check files
    for check_num, recs in by_check.items():
        recs_sorted = sorted(recs, key=lambda r: (r["verdict"], int(re.match(r"\d+", r["section_number"]).group()) if re.match(r"\d+", r["section_number"]) else 999))
        out_path = OUT_DIR / f"check{check_num}.md"
        body = [f"# L3 flags — failed check {check_num}", "",
                f"{len(recs_sorted)} sections in this group.", "", "---", ""]
        for rec in recs_sorted:
            body.append(render_section_block(rec))
        out_path.write_text("".join(body), encoding="utf-8")

    # Top-level summary
    summary = render_summary(by_check, by_verdict)
    (OUT_DIR / "REVIEW.md").write_text(summary, encoding="utf-8")

    print(f"Wrote {len(records)} section reviews", file=sys.stderr)
    print(f"  Summary: {OUT_DIR.relative_to(REPO)}/REVIEW.md", file=sys.stderr)
    print(f"  Verdicts: {dict((k, len(v)) for k, v in by_verdict.items())}", file=sys.stderr)

    # Also emit a JSON manifest for machine consumers.
    manifest = {
        "n_total": len(records),
        "by_verdict": {k: len(v) for k, v in by_verdict.items()},
        "by_check": {k: len(v) for k, v in by_check.items()},
        "sections": [
            {
                "number": r["section_number"],
                "title": r["title"],
                "verdict": r["verdict"],
                "rationale": r["rationale"],
                "failed_check": r["flag"]["failed_check"],
                "reason": r["flag"].get("reason"),
                "suggested_fix": r["flag"].get("suggested_fix"),
                "section_dir": r["section_dir"],
            }
            for r in records
        ],
    }
    (OUT_DIR / "review.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
