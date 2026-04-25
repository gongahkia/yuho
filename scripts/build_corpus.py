#!/usr/bin/env python3
"""Build the enriched JSON corpus for the Singapore Penal Code library.

Output layout under ``library/penal_code/_corpus/``:

    index.json                 -- top-level manifest
    sections/s{N}.json         -- per-section enriched record

Each per-section record stitches together:

* canonical SSO raw text (from ``_raw/act.json``)
* encoded ``.yh`` source + AST summary
* controlled-English and Mermaid transpilations
* L1 / L2 / L3 coverage state and any flags
* outgoing / incoming reference edges (via G10 reference graph)
* provenance: Yuho version, scrape date, encoding commit, raw SSO hash

This is the data layer for the browser extension (Task 2b) and the static
explorer site (Task 2c). Both UIs read the same JSON; the corpus is the
single source of truth.

Run:
    python3 scripts/build_corpus.py
    python3 scripts/build_corpus.py --section 415         # one section
    python3 scripts/build_corpus.py --validate-only       # don't write
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


REPO = Path(__file__).resolve().parent.parent
LIBRARY_DIR = REPO / "library" / "penal_code"
RAW_PATH = LIBRARY_DIR / "_raw" / "act.json"
COVERAGE_PATH = LIBRARY_DIR / "_coverage" / "coverage.json"
CORPUS_DIR = LIBRARY_DIR / "_corpus"
SECTIONS_DIR = CORPUS_DIR / "sections"


# ---------------------------------------------------------------------------
# AST summary builder
# ---------------------------------------------------------------------------


def _ast_summary(module) -> Dict[str, Any]:
    """Compact summary of one parsed module's structural counts."""
    if not module.statutes:
        return {"statutes": 0}
    s = module.statutes[0]
    n_elements = sum(_count_elements(e) for e in s.elements)
    for sub in s.subsections:
        n_elements += sum(_count_elements(e) for e in sub.elements)
    return {
        "statutes": len(module.statutes),
        "elements": n_elements,
        "illustrations": len(s.illustrations) + sum(len(sub.illustrations) for sub in s.subsections),
        "subsections": len(s.subsections),
        "exceptions": len(s.exceptions),
        "case_law": len(s.case_law),
        "definitions": len(s.definitions),
        "effective_dates": list(s.effective_dates) if s.effective_dates else (
            [s.effective_date] if s.effective_date else []
        ),
        "repealed_date": s.repealed_date,
        "subsumes": s.subsumes,
        "amends": s.amends,
        "has_penalty": s.penalty is not None,
        "jurisdiction": s.jurisdiction,
    }


def _count_elements(node) -> int:
    """Count individual ElementNodes inside an element / element-group."""
    from yuho.ast import nodes as ast_nodes
    if isinstance(node, ast_nodes.ElementNode):
        return 1
    if isinstance(node, ast_nodes.ElementGroupNode):
        return sum(_count_elements(m) for m in node.members)
    return 0


# ---------------------------------------------------------------------------
# Section directory discovery
# ---------------------------------------------------------------------------


def _section_dirs() -> List[Path]:
    """Sorted list of per-section directories under library/penal_code/."""
    return sorted(
        d for d in LIBRARY_DIR.iterdir()
        if d.is_dir() and d.name.startswith("s") and not d.name.startswith("_")
    )


def _section_number_from_dir(d: Path) -> str:
    """Extract the section number from a directory name like ``s415_cheating``."""
    stem = d.name[1:]  # drop leading 's'
    if "_" in stem:
        stem = stem.split("_", 1)[0]
    return stem


# ---------------------------------------------------------------------------
# Raw SSO lookup
# ---------------------------------------------------------------------------


def _load_raw_index(raw_path: Path) -> Dict[str, Dict[str, Any]]:
    """Build a section-number → raw-section dict from _raw/act.json."""
    with raw_path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return {sec["number"]: sec for sec in raw.get("sections", [])}


def _hash_raw_text(text: str) -> str:
    """SHA-256 of the canonical raw text (provenance anchor)."""
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Coverage lookup
# ---------------------------------------------------------------------------


def _load_coverage(path: Path) -> Dict[str, Dict[str, Any]]:
    """Load coverage.json, return section-number-keyed dict."""
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        cov = json.load(f)
    sections = cov.get("sections", cov.get("per_section", []))
    if isinstance(sections, dict):
        return sections
    out: Dict[str, Dict[str, Any]] = {}
    for entry in sections:
        n = entry.get("number") or entry.get("section")
        if n:
            out[str(n)] = entry
    return out


# ---------------------------------------------------------------------------
# Metadata.toml lookup
# ---------------------------------------------------------------------------


def _load_metadata(section_dir: Path) -> Dict[str, Any]:
    """Parse metadata.toml if present."""
    meta_path = section_dir / "metadata.toml"
    if not meta_path.exists():
        return {}
    try:
        return tomllib.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _l3_status(meta: Dict[str, Any], section_dir: Path) -> str:
    """Derive L3 status label.

    Order of precedence:
    1. metadata.toml [verification].last_verified ⇒ "stamped"
    2. _L3_FLAG.md present ⇒ "flagged"
    3. otherwise "unstamped"
    """
    verification = meta.get("verification", {})
    if verification.get("last_verified"):
        return "stamped"
    if (section_dir / "_L3_FLAG.md").exists():
        return "flagged"
    if verification.get("flag") or meta.get("flag"):
        return "flagged"
    return "unstamped"


def _l3_flag_details(section_dir: Path) -> Optional[Dict[str, Any]]:
    """Parse the per-section _L3_FLAG.md if present."""
    flag_path = section_dir / "_L3_FLAG.md"
    if not flag_path.exists():
        return None
    text = flag_path.read_text(encoding="utf-8")
    out: Dict[str, Any] = {"raw": text}
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


# ---------------------------------------------------------------------------
# Transpilations
# ---------------------------------------------------------------------------


def _transpile(yh_path: Path, target: str) -> Optional[str]:
    """Transpile in-process via the registry (orders of magnitude faster than subprocess)."""
    try:
        from yuho.services.analysis import analyze_file
        from yuho.transpile import get_transpiler, TranspileTarget

        analysis = analyze_file(yh_path, run_semantic=False)
        if analysis.parse_errors or analysis.ast is None:
            return None
        tgt = TranspileTarget.from_string(target)
        return get_transpiler(tgt).transpile(analysis.ast)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Reference-graph integration
# ---------------------------------------------------------------------------


def _build_reference_graph():
    """Lazy import + build reference graph once."""
    from yuho.library.reference_graph import build_reference_graph
    return build_reference_graph(LIBRARY_DIR)


def _refs_for_section(graph, section: str) -> Dict[str, Any]:
    return {
        "outgoing": [
            {
                "dst": e.dst,
                "kind": e.kind,
                "snippet": e.snippet,
            }
            for e in graph.outgoing(section)
        ],
        "incoming": [
            {
                "src": e.src,
                "kind": e.kind,
                "snippet": e.snippet,
            }
            for e in graph.incoming(section)
        ],
    }


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


def _git_head_sha(repo: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=repo, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return None


def _yuho_version() -> str:
    try:
        from yuho import __version__
        return __version__
    except Exception:
        return "unknown"


# ---------------------------------------------------------------------------
# Per-section build
# ---------------------------------------------------------------------------


@dataclass
class CorpusBuildContext:
    raw_index: Dict[str, Dict[str, Any]]
    coverage: Dict[str, Dict[str, Any]]
    reference_graph: Any
    yuho_version: str
    git_sha: Optional[str]
    scrape_date: Optional[str]


def build_section_record(section_dir: Path, ctx: CorpusBuildContext) -> Dict[str, Any]:
    """Build the enriched JSON record for one section."""
    from yuho.services.analysis import analyze_file

    section_num = _section_number_from_dir(section_dir)
    yh_path = section_dir / "statute.yh"

    # --- Encoded source + AST summary ---
    yh_source = ""
    ast_summary: Dict[str, Any] = {}
    parse_ok = False
    if yh_path.exists():
        yh_source = yh_path.read_text(encoding="utf-8")
        try:
            analysis = analyze_file(yh_path, run_semantic=False)
            if analysis.ast and not analysis.parse_errors:
                ast_summary = _ast_summary(analysis.ast)
                parse_ok = True
        except Exception:
            pass

    # --- Raw SSO text ---
    raw_entry = ctx.raw_index.get(section_num, {})
    raw_text = raw_entry.get("text", "")

    # --- Coverage ---
    cov = ctx.coverage.get(section_num, {})
    meta = _load_metadata(section_dir)

    # --- Transpilations ---
    english = _transpile(yh_path, "english") if yh_path.exists() else None
    mermaid = _transpile(yh_path, "mermaid") if yh_path.exists() else None

    # --- References (G10) ---
    refs = _refs_for_section(ctx.reference_graph, section_num)

    # --- Title ---
    title = (
        meta.get("statute", {}).get("title")
        or raw_entry.get("marginal_note", "")
        or ""
    )

    # --- SSO anchor / URL ---
    sso_url = (
        meta.get("verification", {}).get("sso_url")
        or f"https://sso.agc.gov.sg/Act/PC1871?ProvIds={raw_entry.get('anchor_id', f'pr{section_num}-')}"
    )

    # --- Build record ---
    record: Dict[str, Any] = {
        "section_number": section_num,
        "section_title": title,
        "act": "Penal Code 1871",
        "act_code": "PC1871",
        "jurisdiction": "SG",
        "sso_anchor": raw_entry.get("anchor_id"),
        "sso_url": sso_url,
        "raw": {
            "marginal_note": raw_entry.get("marginal_note"),
            "text": raw_text,
            "sub_items": raw_entry.get("sub_items", []),
            "amendments": raw_entry.get("amendments", []),
            "hash_sha256": _hash_raw_text(raw_text),
        },
        "encoded": {
            "yh_source": yh_source,
            "yh_path": str(yh_path.relative_to(REPO)) if yh_path.exists() else None,
            "ast_summary": ast_summary,
            "parse_ok": parse_ok,
        },
        "transpiled": {
            "english": english,
            "mermaid": mermaid,
        },
        "coverage": {
            "L1": cov.get("L1_pass", parse_ok),
            "L2": cov.get("L2_pass", parse_ok),
            "L3": _l3_status(meta, section_dir),
            "L3_stamp_date": meta.get("verification", {}).get("last_verified"),
            "L3_verified_by": meta.get("verification", {}).get("verified_by"),
            "L3_flag": _l3_flag_details(section_dir),
            "flags": cov.get("flags", []),
        },
        "references": refs,
        "metadata": {
            "summary": meta.get("description", {}).get("summary"),
            "notes": meta.get("description", {}).get("notes"),
            "contributor": meta.get("contributor", {}),
            "version": meta.get("statute", {}).get("version"),
        },
        "provenance": {
            "yuho_version": ctx.yuho_version,
            "scrape_date": ctx.scrape_date,
            "encoding_commit": ctx.git_sha,
            "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        },
    }
    return record


# ---------------------------------------------------------------------------
# Index builder
# ---------------------------------------------------------------------------


def build_index(records: List[Dict[str, Any]], ctx: CorpusBuildContext) -> Dict[str, Any]:
    """Top-level manifest. One row per section with summary fields."""
    rows = []
    n_l1 = n_l2 = n_l3_stamped = n_flagged = 0
    for r in records:
        cov = r["coverage"]
        if cov["L1"]:
            n_l1 += 1
        if cov["L2"]:
            n_l2 += 1
        if cov["L3"] == "stamped":
            n_l3_stamped += 1
        if cov["L3"] == "flagged":
            n_flagged += 1
        rows.append({
            "number": r["section_number"],
            "title": r["section_title"],
            "L1": cov["L1"],
            "L2": cov["L2"],
            "L3": cov["L3"],
            "elements": r["encoded"]["ast_summary"].get("elements", 0),
            "illustrations": r["encoded"]["ast_summary"].get("illustrations", 0),
            "subsections": r["encoded"]["ast_summary"].get("subsections", 0),
            "exceptions": r["encoded"]["ast_summary"].get("exceptions", 0),
            "outgoing_refs": len(r["references"]["outgoing"]),
            "incoming_refs": len(r["references"]["incoming"]),
            "sso_url": r["sso_url"],
        })
    return {
        "act": "Penal Code 1871",
        "act_code": "PC1871",
        "jurisdiction": "SG",
        "n_sections": len(records),
        "totals": {
            "L1": n_l1,
            "L2": n_l2,
            "L3_stamped": n_l3_stamped,
            "L3_flagged": n_flagged,
            "L3_unstamped": len(records) - n_l3_stamped - n_flagged,
        },
        "generated_at": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "yuho_version": ctx.yuho_version,
        "encoding_commit": ctx.git_sha,
        "scrape_date": ctx.scrape_date,
        "sections": rows,
    }


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--section", help="Build only this section number (e.g. 415)")
    parser.add_argument("--validate-only", action="store_true",
                        help="Build records in memory, don't write to disk")
    parser.add_argument("--no-transpile", action="store_true",
                        help="Skip controlled-English + Mermaid transpilations (fast mode)")
    args = parser.parse_args()

    if not LIBRARY_DIR.exists():
        print(f"error: library dir not found: {LIBRARY_DIR}", file=sys.stderr)
        return 1

    print(f"Loading raw index from {RAW_PATH.relative_to(REPO)}...", file=sys.stderr)
    raw_index = _load_raw_index(RAW_PATH)
    print(f"  {len(raw_index)} sections in raw act.json", file=sys.stderr)

    print("Loading coverage...", file=sys.stderr)
    coverage = _load_coverage(COVERAGE_PATH)
    print(f"  {len(coverage)} entries in coverage.json", file=sys.stderr)

    print("Building reference graph (G10)...", file=sys.stderr)
    graph = _build_reference_graph()
    print(f"  {len(graph.nodes)} nodes, {graph.edge_count()} edges", file=sys.stderr)

    # Read scrape_date from raw act.json header
    with RAW_PATH.open("r", encoding="utf-8") as f:
        raw_full = json.load(f)
    scrape_date = raw_full.get("scraped_at")

    ctx = CorpusBuildContext(
        raw_index=raw_index,
        coverage=coverage,
        reference_graph=graph,
        yuho_version=_yuho_version(),
        git_sha=_git_head_sha(REPO),
        scrape_date=scrape_date,
    )

    section_dirs = _section_dirs()
    if args.section:
        section_dirs = [d for d in section_dirs if _section_number_from_dir(d) == args.section]
        if not section_dirs:
            print(f"error: no section dir matches {args.section!r}", file=sys.stderr)
            return 1

    print(f"Building corpus over {len(section_dirs)} section(s)...", file=sys.stderr)

    # Monkey-patch out transpilation if --no-transpile
    if args.no_transpile:
        global _transpile
        _transpile = lambda yh_path, target: None  # type: ignore

    records: List[Dict[str, Any]] = []
    for i, sd in enumerate(section_dirs, 1):
        try:
            rec = build_section_record(sd, ctx)
        except Exception as e:
            print(f"  [{i}/{len(section_dirs)}] {sd.name}: ERROR {type(e).__name__}: {e}", file=sys.stderr)
            continue
        records.append(rec)
        if i % 25 == 0 or i == len(section_dirs):
            print(f"  [{i}/{len(section_dirs)}] {sd.name}", file=sys.stderr)

    if args.validate_only:
        print(f"\nValidate-only mode. Built {len(records)} records in memory; not writing.", file=sys.stderr)
        return 0

    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nWriting per-section JSON to {SECTIONS_DIR.relative_to(REPO)}/...", file=sys.stderr)
    for rec in records:
        out_path = SECTIONS_DIR / f"s{rec['section_number']}.json"
        out_path.write_text(json.dumps(rec, indent=2, sort_keys=True, ensure_ascii=False))

    index = build_index(records, ctx)
    index_path = CORPUS_DIR / "index.json"
    index_path.write_text(json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False))
    print(f"Wrote index to {index_path.relative_to(REPO)}", file=sys.stderr)

    print(f"\nDone. Corpus: {len(records)} sections, "
          f"L1={index['totals']['L1']}, L2={index['totals']['L2']}, "
          f"L3_stamped={index['totals']['L3_stamped']}, "
          f"L3_flagged={index['totals']['L3_flagged']}.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
