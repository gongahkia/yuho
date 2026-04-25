#!/usr/bin/env python3
"""Build the provenance & fidelity ledger.

The ledger is the citable, auditable companion to the encoded library.
For every section it records:

* canonical SSO anchor + URL
* SHA-256 of the canonical scraped text
* scrape date
* Yuho version that encoded the section
* git commit at encoding time
* L1 / L2 / L3 state (from coverage)
* current flags (with reason + suggested fix, if present)
* known caveats and grammar-gap dependencies
* per-section reviewer attribution where available

Output:
    library/penal_code/_ledger/ledger.json    -- machine-readable
    library/penal_code/_ledger/LEDGER.md      -- human-readable

Both regenerate from the existing corpus + git metadata; no new sources
of truth are introduced. The ledger surfaces what's already known across
metadata.toml, coverage.json, _L3_FLAG.md, and provenance hashes — in
one place a reader can cite.
"""

from __future__ import annotations

import datetime as _dt
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"
LEDGER_DIR = REPO / "library" / "penal_code" / "_ledger"


# ---------------------------------------------------------------------------
# Data load
# ---------------------------------------------------------------------------


def _load_corpus_records() -> List[Dict[str, Any]]:
    sect_dir = CORPUS / "sections"
    if not sect_dir.exists():
        sys.exit("error: corpus not built. Run scripts/build_corpus.py first.")
    out: List[Dict[str, Any]] = []
    for path in sorted(sect_dir.glob("s*.json")):
        with path.open("r", encoding="utf-8") as f:
            out.append(json.load(f))
    return out


# ---------------------------------------------------------------------------
# Git provenance per section
# ---------------------------------------------------------------------------


def _git_log_for(path: Path) -> Dict[str, Any]:
    """First-commit and last-commit metadata for a tracked path."""
    if not path.exists():
        return {}
    rel = path.relative_to(REPO)
    try:
        first = subprocess.run(
            ["git", "log", "--diff-filter=A", "--format=%H|%aI|%an", "--", str(rel)],
            capture_output=True, text=True, cwd=REPO, timeout=10,
        )
        last = subprocess.run(
            ["git", "log", "-1", "--format=%H|%aI|%an", "--", str(rel)],
            capture_output=True, text=True, cwd=REPO, timeout=10,
        )
        first_line = (first.stdout.strip().splitlines() or [""])[-1]
        last_line = last.stdout.strip().splitlines()[0] if last.stdout.strip() else ""
        out: Dict[str, Any] = {}
        if first_line:
            sha, date, author = (first_line.split("|") + ["", "", ""])[:3]
            out["first_commit"] = {"sha": sha, "date": date, "author": author}
        if last_line:
            sha, date, author = (last_line.split("|") + ["", "", ""])[:3]
            out["last_commit"] = {"sha": sha, "date": date, "author": author}
        return out
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Ledger entry shape
# ---------------------------------------------------------------------------


def build_entry(rec: Dict[str, Any]) -> Dict[str, Any]:
    """Build one ledger row from a corpus record."""
    cov = rec.get("coverage", {})
    enc = rec.get("encoded", {})
    prov = rec.get("provenance", {})
    raw = rec.get("raw", {})
    yh_path = enc.get("yh_path")
    git_meta = _git_log_for(REPO / yh_path) if yh_path else {}

    return {
        "section_number": rec["section_number"],
        "section_title": rec.get("section_title"),
        "act_code": rec.get("act_code"),
        "sso_anchor": rec.get("sso_anchor"),
        "sso_url": rec.get("sso_url"),
        "raw": {
            "sha256": raw.get("hash_sha256"),
        },
        "encoding": {
            "yh_path": yh_path,
            "first_commit": git_meta.get("first_commit"),
            "last_commit": git_meta.get("last_commit"),
        },
        "coverage": {
            "L1": cov.get("L1"),
            "L2": cov.get("L2"),
            "L3": cov.get("L3"),
            "L3_stamp_date": cov.get("L3_stamp_date"),
            "L3_verified_by": cov.get("L3_verified_by"),
            "L3_flag": cov.get("L3_flag"),
            "flags": cov.get("flags") or [],
        },
        "provenance": {
            "yuho_version": prov.get("yuho_version"),
            "scrape_date": prov.get("scrape_date"),
            "encoding_commit": prov.get("encoding_commit"),
            "corpus_generated_at": prov.get("generated_at"),
        },
        "metadata": rec.get("metadata", {}),
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------


def render_markdown(entries: List[Dict[str, Any]]) -> str:
    n_total = len(entries)
    n_l3 = sum(1 for e in entries if e["coverage"]["L3"] == "stamped")
    n_flagged = sum(1 for e in entries if e["coverage"]["L3"] == "flagged")
    n_unstamped = sum(1 for e in entries if e["coverage"]["L3"] == "unstamped")
    today = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    lines: List[str] = [
        "# Yuho — Singapore Penal Code provenance & fidelity ledger",
        "",
        f"_Generated {today}._",
        "",
        "Per-section audit trail. For every encoded section the ledger records",
        "the canonical SSO anchor, a SHA-256 hash of the scraped text, the",
        "Yuho version and git commit at encoding time, the current L1 / L2 / L3",
        "coverage state, and any review flags. Use this file to cite a specific",
        "version of the encoded library; cross-reference with the canonical",
        "SSO source for any decision that matters.",
        "",
        f"**Coverage**: {n_total} sections · L3 stamped: {n_l3} · L3 flagged: {n_flagged} · unstamped: {n_unstamped}.",
        "",
        "---",
        "",
        "| Section | Title | L1 | L2 | L3 | Stamp date | Raw SHA-256 (first 16) |",
        "|---|---|:-:|:-:|:-:|---|---|",
    ]
    for e in entries:
        cov = e["coverage"]
        sha = (e["raw"].get("sha256") or "")[:16]
        l1 = "✓" if cov.get("L1") else "—"
        l2 = "✓" if cov.get("L2") else "—"
        l3 = cov.get("L3") or "—"
        stamp = cov.get("L3_stamp_date") or ""
        title = (e.get("section_title") or "").replace("|", "\\|")[:80]
        anchor = e.get("sso_anchor") or ""
        section_link = f"[s{e['section_number']}](https://sso.agc.gov.sg/Act/PC1871?ProvIds={anchor}#{anchor})"
        lines.append(f"| {section_link} | {title} | {l1} | {l2} | {l3} | {stamp} | `{sha}` |")

    # Flag detail.
    flagged = [e for e in entries if e["coverage"]["L3"] == "flagged"]
    if flagged:
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"## L3 flags ({len(flagged)})")
        lines.append("")
        for e in flagged:
            f = e["coverage"]["L3_flag"] or {}
            lines.append(f"### s{e['section_number']} — {e.get('section_title','')}")
            if f.get("failed_check") is not None:
                lines.append(f"- failed check: {f['failed_check']}")
            if f.get("reason"):
                lines.append(f"- reason: {f['reason']}")
            if f.get("suggested_fix"):
                lines.append(f"- suggested fix: {f['suggested_fix']}")
            lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    print("Loading corpus...", file=sys.stderr)
    records = _load_corpus_records()
    print(f"  {len(records)} sections", file=sys.stderr)

    print("Building ledger entries (this walks git per file)...", file=sys.stderr)
    entries = []
    for i, rec in enumerate(records, 1):
        entries.append(build_entry(rec))
        if i % 50 == 0:
            print(f"  [{i}/{len(records)}]", file=sys.stderr)

    LEDGER_DIR.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = LEDGER_DIR / "ledger.json"
    payload = {
        "act_code": "PC1871",
        "act": "Penal Code 1871",
        "jurisdiction": "SG",
        "n_sections": len(entries),
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "entries": entries,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"wrote {json_path.relative_to(REPO)}", file=sys.stderr)

    # Markdown
    md_path = LEDGER_DIR / "LEDGER.md"
    md_path.write_text(render_markdown(entries))
    print(f"wrote {md_path.relative_to(REPO)}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
