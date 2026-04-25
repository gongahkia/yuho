"""phase_d_flag_fix.py — dispatch Codex agents to apply minimum-edit fixes
to sections that carry an _L3_FLAG.md file.

renders doc/PHASE_D_FLAG_FIX_PROMPT.md per section and invokes
`codex exec --full-auto -m gpt-5.4 -c model_reasoning_effort=high`.
Each agent reads the section's existing _L3_FLAG.md + canonical text,
patches statute.yh to address the specific flag, and deletes the flag
file on success. Progress tracked in library/penal_code/_coverage/phase_d_flag_fix_progress.jsonl.

usage:
    python scripts/phase_d_flag_fix.py --list
    python scripts/phase_d_flag_fix.py --all-flagged --dispatch --parallel 8
    python scripts/phase_d_flag_fix.py 188 304C --dispatch
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "docs" / "researcher" / "phase-d-flag-fix-prompt.md"
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

def load_template_body() -> str:
    doc = TEMPLATE_PATH.read_text()
    start = doc.find("## PROMPT")
    start = doc.find("\n", start) + 1
    end = doc.rfind("\n```\n") + len("\n```\n")
    return doc[start:end].strip() + "\n"

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

def render(num: str, sec: dict, act_code: str, body: str) -> str:
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
    return header + body.replace("{N}", num)

def dispatch_codex(prompt: str, timeout: int = 900,
                   model: str | None = None, reasoning: str | None = None) -> subprocess.CompletedProcess:
    cmd = ["codex", "exec", "--full-auto", "--skip-git-repo-check", "-C", str(REPO)]
    if model: cmd += ["-m", model]
    if reasoning: cmd += ["-c", f"model_reasoning_effort={reasoning}"]
    cmd.append("-")
    return subprocess.run(cmd, input=prompt, text=True, capture_output=True, timeout=timeout)

def flag_file_gone(n: str) -> bool:
    d = find_dir(n)
    if not d: return False
    return not (d / "_L3_FLAG.md").exists()

def yuho_check_passes(n: str) -> bool:
    d = find_dir(n)
    if not d or not (d / "statute.yh").exists(): return False
    r = subprocess.run(
        [str(REPO / ".venv-scrape" / "bin" / "yuho"), "check", "--format", "json",
         str(d / "statute.yh")],
        capture_output=True, text=True, timeout=60,
    )
    try: return json.loads(r.stdout).get("valid", False)
    except Exception: return False

def main() -> None:
    p = argparse.ArgumentParser(prog="phase_d_flag_fix", description=__doc__)
    p.add_argument("specs", nargs="*", help="section numbers to fix")
    p.add_argument("--list", action="store_true",
                   help="list sections with an _L3_FLAG.md file")
    p.add_argument("--all-flagged", action="store_true",
                   help="target every section whose directory has an _L3_FLAG.md")
    p.add_argument("--dispatch", action="store_true",
                   help="actually invoke `codex exec`")
    p.add_argument("--parallel", type=int, default=1, metavar="K",
                   help="with --dispatch, run up to K codex instances in parallel")
    p.add_argument("--progress", metavar="FILE", default="library/penal_code/_coverage/phase_d_flag_fix_progress.jsonl",
                   help="append-only JSONL file recording per-section outcomes")
    p.add_argument("--timeout", type=int, default=900,
                   help="per-section timeout in seconds")
    p.add_argument("--model", default="gpt-5.4", help="codex model")
    p.add_argument("--reasoning", default="high", help="reasoning effort")
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

    body = load_template_body()
    prompts = {n: render(n, raw[n], act_code, body) for n in targets}

    if not args.dispatch:
        for n, prompt in prompts.items():
            print(f"\n<<< s{n} >>>\n{prompt}")
        return

    def _run(n: str) -> dict:
        prompt = prompts[n]
        try:
            r = dispatch_codex(prompt, args.timeout, args.model, args.reasoning)
            if r.returncode != 0:
                return {"section": n, "outcome": "ERROR", "error": f"exit={r.returncode}"}
            flag_gone = flag_file_gone(n)
            check_ok = yuho_check_passes(n)
            if flag_gone and check_ok: return {"section": n, "outcome": "FIXED"}
            if flag_gone and not check_ok: return {"section": n, "outcome": "BROKEN",
                                                    "error": "flag deleted but yuho check failed"}
            if not flag_gone and check_ok: return {"section": n, "outcome": "PARTIAL",
                                                    "error": "flag still present (agent unsure?)"}
            return {"section": n, "outcome": "UNCHANGED"}
        except subprocess.TimeoutExpired:
            return {"section": n, "outcome": "ERROR", "error": "timeout"}
        except Exception as e:
            return {"section": n, "outcome": "ERROR", "error": e.__class__.__name__}

    progress_path = REPO / args.progress
    fh = open(progress_path, "a")
    def _record(r: dict) -> None:
        fh.write(json.dumps(r) + "\n"); fh.flush()
        tag = r["outcome"]
        extra = f" — {r['error']}" if "error" in r else ""
        print(f"[{tag}] s{r['section']}{extra}", flush=True)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"[start] {len(targets)} flagged sections, model={args.model}, reasoning={args.reasoning}, parallel={args.parallel}", flush=True)
    with ThreadPoolExecutor(max_workers=max(args.parallel, 1)) as pool:
        futs = {pool.submit(_run, n): n for n in targets}
        for f in as_completed(futs):
            n = futs[f]
            try: _record(f.result())
            except Exception as e:
                _record({"section": n, "outcome": "ERROR", "error": e.__class__.__name__})
    fh.close()

    counts: dict[str, int] = {}
    for line in progress_path.read_text().splitlines():
        try:
            rec = json.loads(line)
            k = rec["outcome"]; counts[k] = counts.get(k, 0) + 1
        except Exception: continue
    print(f"[end] " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())), flush=True)

if __name__ == "__main__":
    main()
