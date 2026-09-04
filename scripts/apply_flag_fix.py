"""Render minimum-edit proposals for sections that carry an ``_L3_FLAG.md``.

The previous implementation dispatched an unrestricted coding agent that
could edit ``statute.yh`` and remove its own flag. That process has been
retired: automated triage may propose a repair, but it cannot change source,
clear a flag, or create review evidence. Apply any proposal through the
ordinary reviewed-change process and record the resulting evidence separately.

usage:
    python scripts/apply_flag_fix.py --list
    python scripts/apply_flag_fix.py --all-flagged
    python scripts/apply_flag_fix.py 188 304C
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RAW_PATH = REPO / "library" / "penal_code" / "_raw" / "act.json"

STOPWORDS = {"of","and","the","in","for","to","with","by","on","or",
             "a","an","at","its","from","as","is","be","any"}

def slugify(marginal: str, maxlen: int = 45) -> str:
    words = re.findall(r"[A-Za-z0-9]+", marginal.lower())
    words = [w for w in words if w not in STOPWORDS]
    slug = "_".join(words) or "section"
    if len(slug) <= maxlen: return slug
    cut = slug[:maxlen].rsplit("_", 1)[0]
    return cut or slug[:maxlen]

def _sortkey(n: str) -> tuple:
    m = re.match(r"(\d+)([A-Z]*)", n)
    return (int(m.group(1)), m.group(2)) if m else (9999, n)

def expand_spec(specs: list[str], raw: dict[str, dict]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    tokens = [t.strip() for s in specs for t in s.split(",") if t.strip()]
    for tok in tokens:
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", tok)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo > hi: lo, hi = hi, lo
            for i in range(lo, hi + 1):
                for cand in sorted([k for k in raw if re.fullmatch(rf"{i}[A-Z]*", k)], key=_sortkey):
                    if cand not in seen: seen.add(cand); out.append(cand)
        else:
            if tok in seen: continue
            seen.add(tok); out.append(tok)
    return out

def find_dir(n: str) -> Path | None:
    for p in (REPO / "library" / "penal_code").iterdir():
        if p.is_dir() and re.match(rf"s{n}_", p.name):
            return p
    return None

def load_raw() -> tuple[dict[str, dict], str]:
    d = json.loads(RAW_PATH.read_text())
    return {s["number"]: s for s in d["sections"] if s.get("number")}, d.get("act_code", "PC1871")

def find_flagged_sections() -> list[str]:
    """Sections whose directory contains a _L3_FLAG.md file."""
    out = []
    for p in (REPO / "library" / "penal_code").glob("s*/_L3_FLAG.md"):
        m = re.match(r"s(\d+[A-Z]*)_", p.parent.name)
        if m: out.append(m.group(1))
    return sorted(out, key=_sortkey)

def render(num: str, sec: dict, act_code: str) -> str:
    marginal = sec.get("marginal_note") or f"Section {num}"
    anchor = sec.get("anchor_id") or f"pr{num}-"
    sso = f"https://sso.agc.gov.sg/Act/{act_code}?ProvIds={anchor}#{anchor}"
    existing = find_dir(num)
    slug = existing.name[len(f"s{num}_"):] if existing else slugify(marginal)
    header = (
        f"## Section context (pre-filled)\n\n"
        f"- Section: **{num}**\n"
        f"- Marginal note: **{marginal}**\n"
        f"- SSO URL: {sso}\n"
        f"- Directory: `library/penal_code/s{num}_{slug}/`\n"
        f"- Flag file: `library/penal_code/s{num}_{slug}/_L3_FLAG.md` (read first)\n"
        f"- Canonical text: the entry in `library/penal_code/_raw/act.json` with `number == \"{num}\"`\n\n"
        f"---\n\n"
    )
    return header + """## Non-certifying repair proposal

Compare the flag, the canonical source, and the current encoding. Propose the
smallest source-backed repair in a reviewed change. This proposal must not:

- edit `statute.yh` or remove `_L3_FLAG.md` automatically;
- treat a passing `yuho check` as legal or human-review approval; or
- update `metadata.toml` to create an L3 stamp.

The reviewed change and a separate evidence record under
`docs/release/corpus-evidence-schema.json` are required before the flag can be
resolved.
"""

def main() -> None:
    p = argparse.ArgumentParser(prog="apply_flag_fix", description=__doc__)
    p.add_argument("specs", nargs="*", help="section numbers for repair proposals")
    p.add_argument("--list", action="store_true",
                   help="list sections with an _L3_FLAG.md file")
    p.add_argument("--all-flagged", action="store_true",
                   help="target every section whose directory has an _L3_FLAG.md")
    args = p.parse_args()

    raw, act_code = load_raw()
    flagged = find_flagged_sections()

    if args.list:
        for n in flagged: print(f"{n}\t{raw.get(n, {}).get('marginal_note','')[:80]}")
        return

    if args.all_flagged:
        targets = list(flagged)
    else:
        targets = expand_spec(args.specs, raw) if args.specs else []
    if not targets: p.error("supply section numbers, --all-flagged, or --list")
    targets = [n for n in targets if n in raw and find_dir(n)]

    prompts = {n: render(n, raw[n], act_code) for n in targets}

    for n, prompt in prompts.items():
        print(f"\n<<< s{n} >>>\n{prompt}")

if __name__ == "__main__":
    main()
