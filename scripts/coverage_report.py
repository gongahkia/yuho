"""coverage_report.py — phase B of the Yuho revamp roadmap.

compares the canonical scraped statute corpus (library/<act>/_raw/act.json)
against encoded .yh + metadata.toml pairs to produce a three-layer coverage
dashboard:

    L1 (parse)     : `yuho check --syntax-only` passes
    L2 (typecheck) : `yuho check` passes (parse + ast + semantic + lint)
    L3 (verified)  : metadata.toml has [verification].last_verified set

outputs:
    <act_dir>/_coverage/coverage.json
    <act_dir>/_coverage/COVERAGE.md

usage:
    python scripts/coverage_report.py --act-dir library/penal_code
    python scripts/coverage_report.py --act-dir library/penal_code --yuho ./.venv-scrape/bin/yuho
"""
from __future__ import annotations
import argparse, datetime as _dt, json, re, subprocess, sys, tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

_DIR_NUM_RE = re.compile(r"^s(\d+[A-Z]*)_")
_SSO_TMPL = "https://sso.agc.gov.sg/Act/{code}?ProvIds={pid}#{pid}"

@dataclass
class Row:
    number: str
    marginal_note: str
    encoded_path: Optional[str] = None
    metadata_path: Optional[str] = None
    sso_url: Optional[str] = None
    L1: bool = False                                    # parse ok
    L2: bool = False                                    # full check ok
    L3: bool = False                                    # human-verified
    L3_verified_by: Optional[str] = None
    L3_verified_on: Optional[str] = None
    errors: list[str] = field(default_factory=list)

@dataclass
class Totals:
    raw_sections: int = 0
    encoded: int = 0
    L1_pass: int = 0
    L2_pass: int = 0
    L3_pass: int = 0

    @property
    def L1_pct(self) -> float: return 100 * self.L1_pass / self.raw_sections if self.raw_sections else 0.0
    @property
    def L2_pct(self) -> float: return 100 * self.L2_pass / self.raw_sections if self.raw_sections else 0.0
    @property
    def L3_pct(self) -> float: return 100 * self.L3_pass / self.raw_sections if self.raw_sections else 0.0

def _scan_encoded(act_dir: Path) -> dict[str, tuple[Path, Path | None]]:
    """map section-number → (statute.yh, metadata.toml-or-None)."""
    out: dict[str, tuple[Path, Path | None]] = {}
    for sub in sorted(act_dir.iterdir()):
        if not sub.is_dir() or sub.name.startswith("_"): continue
        m = _DIR_NUM_RE.match(sub.name)
        if not m: continue
        yh = sub / "statute.yh"
        if not yh.is_file(): continue
        meta = sub / "metadata.toml"
        out[m.group(1)] = (yh, meta if meta.is_file() else None)
    return out

def _run_yuho(yuho_bin: str, path: Path, syntax_only: bool) -> dict:
    cmd = [yuho_bin, "check", "--format", "json", str(path)]
    if syntax_only: cmd.insert(2, "--syntax-only")       # must precede positional FILE arg
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return {"valid": False, "parse_valid": False, "errors": [{"message": "timeout"}]}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {"valid": False, "parse_valid": False,
                "errors": [{"message": r.stderr.strip() or "non-json output"}]}

def _check_L3(meta_path: Path | None) -> tuple[bool, Optional[str], Optional[str]]:
    if not meta_path or not meta_path.is_file(): return False, None, None
    try:
        data = tomllib.loads(meta_path.read_text())
    except Exception: return False, None, None
    ver = data.get("verification", {}) or {}
    last = ver.get("last_verified")
    by = ver.get("verified_by")
    return (bool(last), by or None, str(last) if last else None)

def build(act_dir: Path, yuho_bin: str) -> tuple[list[Row], Totals, dict]:
    raw_path = act_dir / "_raw" / "act.json"
    raw = json.loads(raw_path.read_text())
    act_code = raw["act_code"]
    encoded = _scan_encoded(act_dir)

    rows: list[Row] = []
    t = Totals(raw_sections=len(raw["sections"]))
    for s in raw["sections"]:
        num = s["number"]
        if not num: continue
        row = Row(number=num, marginal_note=s.get("marginal_note", ""))
        if s.get("anchor_id"):
            row.sso_url = _SSO_TMPL.format(code=act_code, pid=s["anchor_id"])
        pair = encoded.get(num)
        if pair:
            yh, meta = pair
            row.encoded_path = str(yh.relative_to(act_dir.parent.parent)) if yh.is_absolute() else str(yh)
            row.metadata_path = str(meta.relative_to(act_dir.parent.parent)) if meta and meta.is_absolute() else (str(meta) if meta else None)
            t.encoded += 1
            # L1: syntax-only check
            r1 = _run_yuho(yuho_bin, yh, syntax_only=True)
            row.L1 = bool(r1.get("parse_valid", False) and r1.get("valid", r1.get("parse_valid", False)))
            if not row.L1:
                for e in r1.get("errors", []):
                    row.errors.append(f"L1: {e.get('message', e)}")
            # L2: full check
            r2 = _run_yuho(yuho_bin, yh, syntax_only=False)
            row.L2 = bool(r2.get("valid", False))
            if not row.L2:
                for e in r2.get("errors", []):
                    row.errors.append(f"L2: {e.get('message', e)}")
            # L3
            row.L3, row.L3_verified_by, row.L3_verified_on = _check_L3(meta)
        rows.append(row)
        t.L1_pass += row.L1; t.L2_pass += row.L2; t.L3_pass += row.L3
    return rows, t, {"act_code": act_code, "title": raw.get("title", act_code),
                     "valid_date": raw.get("valid_date"),
                     "scraped_at": raw.get("scraped_at")}

def emit_json(path: Path, rows: list[Row], totals: Totals, meta: dict) -> None:
    payload = {
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        "act": meta,
        "totals": {**asdict(totals),
                   "L1_pct": round(totals.L1_pct, 1),
                   "L2_pct": round(totals.L2_pct, 1),
                   "L3_pct": round(totals.L3_pct, 1)},
        "sections": [asdict(r) for r in rows],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

def emit_md(path: Path, rows: list[Row], totals: Totals, meta: dict) -> None:
    def tick(b: bool) -> str: return "✓" if b else "·"
    lines = [
        f"# Coverage — {meta['title']} ({meta['act_code']})",
        "",
        f"_Generated: {_dt.datetime.now(_dt.UTC).isoformat(timespec='seconds')}_  ",
        f"_Scraped: {meta.get('scraped_at') or 'n/a'}_  ",
        f"_Valid date: {meta.get('valid_date') or 'n/a'}_",
        "",
        "## Totals",
        "",
        "| Metric | Count | % of raw |",
        "|---|---|---|",
        f"| raw sections (canonical) | {totals.raw_sections} | — |",
        f"| encoded (.yh present) | {totals.encoded} | {100*totals.encoded/max(totals.raw_sections,1):.1f}% |",
        f"| **L1** — parses | **{totals.L1_pass}** | **{totals.L1_pct:.1f}%** |",
        f"| **L2** — typechecks | **{totals.L2_pass}** | **{totals.L2_pct:.1f}%** |",
        f"| **L3** — verified | **{totals.L3_pass}** | **{totals.L3_pct:.1f}%** |",
        "",
        "## Encoded sections",
        "",
        "| § | Marginal note | L1 | L2 | L3 | Verified | Path |",
        "|---|---|:-:|:-:|:-:|---|---|",
    ]
    for r in rows:
        if not r.encoded_path: continue
        ver = f"{r.L3_verified_on or ''} {r.L3_verified_by or ''}".strip() or "—"
        lines.append(f"| s{r.number} | {r.marginal_note[:60]} | "
                     f"{tick(r.L1)} | {tick(r.L2)} | {tick(r.L3)} | {ver} | `{r.encoded_path}` |")

    unenc = [r for r in rows if not r.encoded_path]
    lines += ["", f"## Unencoded sections ({len(unenc)})", "",
              "| § | Marginal note | SSO |", "|---|---|---|"]
    for r in unenc:
        sso = f"[↗]({r.sso_url})" if r.sso_url else ""
        lines.append(f"| s{r.number} | {r.marginal_note[:80]} | {sso} |")

    errs = [r for r in rows if r.errors]
    if errs:
        lines += ["", "## Errors", ""]
        for r in errs:
            lines.append(f"- **s{r.number}** ({r.marginal_note[:50]})")
            for e in r.errors:
                lines.append(f"  - {e}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")

def main() -> None:
    p = argparse.ArgumentParser(prog="coverage_report", description=__doc__)
    p.add_argument("--act-dir", type=Path, required=True,
                   help="e.g., library/penal_code (must contain _raw/act.json)")
    p.add_argument("--yuho", default="yuho", help="yuho binary path (default: on PATH)")
    p.add_argument("--out-dir", type=Path, help="override output dir (default: <act-dir>/_coverage)")
    args = p.parse_args()

    out_dir = args.out_dir or (args.act_dir / "_coverage")
    print(f"scanning {args.act_dir}...", file=sys.stderr)
    rows, totals, meta = build(args.act_dir, args.yuho)
    emit_json(out_dir / "coverage.json", rows, totals, meta)
    emit_md(out_dir / "COVERAGE.md", rows, totals, meta)
    print(f"encoded={totals.encoded}/{totals.raw_sections} "
          f"L1={totals.L1_pass} L2={totals.L2_pass} L3={totals.L3_pass} "
          f"→ {out_dir}", file=sys.stderr)

if __name__ == "__main__":
    main()
