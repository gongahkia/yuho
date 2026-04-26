"""phase_d_reencode.py — render the strict Phase D re-encoding prompt for one
or more PC sections and optionally dispatch them via `codex exec`.

renders doc/PHASE_D_REENCODING_PROMPT.md with {N} substituted and per-section
context prefilled (marginal note, SSO anchor, existing dir path).

usage:
    # print one prompt to stdout
    python paper/reproducibility/phase_d_reencode.py 415

    # print prompts for a range as sentinel-separated stream
    python paper/reproducibility/phase_d_reencode.py 1-20

    # list the sections that still need re-encoding (non-L3, non-clean-simple)
    python paper/reproducibility/phase_d_reencode.py --list

    # dispatch ONE section to `codex exec --full-auto` in the foreground
    python paper/reproducibility/phase_d_reencode.py 415 --dispatch

    # dispatch a batch to codex in parallel (background processes)
    python paper/reproducibility/phase_d_reencode.py 1-10 --dispatch --parallel 5

    # write prompts to files in /tmp/phase_d/ for manual paste-to-Codex-Cloud
    python paper/reproducibility/phase_d_reencode.py 1-50 --to-files /tmp/phase_d/
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "docs" / "researcher" / "phase-d-reencoding-prompt.md"
RAW_PATH = REPO / "library" / "penal_code" / "_raw" / "act.json"
COVERAGE_PATH = REPO / "library" / "penal_code" / "_coverage" / "coverage.json"
SEPARATOR = "\n\n<<<---NEXT_SECTION--->>>\n\n"

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
    end = doc.rfind("\n```\n") + len("\n```\n")                # include final report block
    return doc[start:end].strip() + "\n"

def load_raw() -> tuple[dict[str, dict], str]:
    d = json.loads(RAW_PATH.read_text())
    return {s["number"]: s for s in d["sections"] if s.get("number")}, d.get("act_code", "PC1871")

def load_l3_set() -> set[str]:
    if not COVERAGE_PATH.is_file(): return set()
    d = json.loads(COVERAGE_PATH.read_text())
    return {s["number"] for s in d.get("sections", []) if s.get("L3")}

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
        f"- SSO anchor: `{anchor}`\n"
        f"- SSO URL: {sso}\n"
        f"- Directory: `library/penal_code/s{num}_{slug}/`"
        f"{' (existing — treat as low-fidelity draft)' if existing else ' (new)'}\n"
        f"- Canonical text: `{{s['number'] == \"{num}\"}}` in `library/penal_code/_raw/act.json`\n\n"
        f"---\n\n"
    )
    return header + body.replace("{N}", num)

def dispatch_codex(prompt: str, num: str, timeout: int = 900,
                   model: str | None = None, reasoning: str | None = None) -> subprocess.CompletedProcess:
    """Run `codex exec --full-auto` with the rendered prompt. Returns CompletedProcess."""
    cmd = ["codex", "exec", "--full-auto", "--skip-git-repo-check", "-C", str(REPO)]
    if model: cmd += ["-m", model]
    if reasoning: cmd += ["-c", f"model_reasoning_effort={reasoning}"]
    cmd.append("-")
    return subprocess.run(
        cmd, input=prompt, text=True, capture_output=True, timeout=timeout,
    )

def verify_section(num: str) -> bool:
    """Check that the encoding at library/penal_code/s<num>_*/ parses cleanly."""
    d = find_dir(num)
    if not d or not (d / "statute.yh").exists(): return False
    r = subprocess.run(
        [str(REPO / ".venv-scrape" / "bin" / "yuho"), "check", "--format", "json", str(d / "statute.yh")],
        capture_output=True, text=True, timeout=60,
    )
    try: return json.loads(r.stdout).get("valid", False)
    except Exception: return False

def main() -> None:
    p = argparse.ArgumentParser(prog="phase_d_reencode", description=__doc__)
    p.add_argument("specs", nargs="*", help="section numbers, ranges (1-20), or comma lists")
    p.add_argument("--list", action="store_true",
                   help="print sections still needing re-encoding (non-L3, has encoding)")
    p.add_argument("--all-remaining", action="store_true",
                   help="target every section that is not currently L3")
    p.add_argument("--dispatch", action="store_true",
                   help="actually invoke `codex exec --full-auto` instead of just printing")
    p.add_argument("--parallel", type=int, default=1, metavar="K",
                   help="with --dispatch, run up to K codex instances in parallel")
    p.add_argument("--progress", metavar="FILE", default="library/penal_code/_coverage/phase_d_reencode_progress.jsonl",
                   help="append-only JSONL file recording per-section outcomes")
    p.add_argument("--resume", action="store_true",
                   help="skip sections already marked done in the progress file")
    p.add_argument("--retries", type=int, default=1,
                   help="per-section retry count on dispatch or verify failure")
    p.add_argument("--to-files", metavar="DIR",
                   help="write one .md file per prompt to this directory (for Codex Cloud)")
    p.add_argument("--timeout", type=int, default=900,
                   help="per-section timeout for --dispatch in seconds (default 900)")
    p.add_argument("--model", metavar="NAME",
                   help="override codex model (e.g. gpt-5.5, gpt-5-fast). Defaults to codex config.")
    p.add_argument("--reasoning", metavar="LEVEL",
                   help="override reasoning effort (low|medium|high|xhigh). Default keeps config.")
    args = p.parse_args()

    raw, act_code = load_raw()
    l3 = load_l3_set()

    if args.list:
        for n in sorted(set(raw) - l3, key=_sortkey):
            print(f"{n}\t{raw[n].get('marginal_note','')[:80]}")
        return

    if args.all_remaining:
        targets = sorted(set(raw) - l3, key=_sortkey)
    else:
        targets = expand_spec(args.specs, raw) if args.specs else []
    if not targets: p.error("supply section numbers, --all-remaining, or --list")
    targets = [n for n in targets if n in raw]

    # resume: skip sections already marked done
    done_from_progress: set[str] = set()
    progress_path = REPO / args.progress
    if args.resume and progress_path.is_file():
        for line in progress_path.read_text().splitlines():
            try:
                r = json.loads(line)
                if r.get("status") == "done": done_from_progress.add(r["section"])
            except Exception:
                continue
        before = len(targets)
        targets = [n for n in targets if n not in done_from_progress]
        print(f"[resume] skipped {before - len(targets)} already-done sections; {len(targets)} remain", file=sys.stderr)

    body = load_template_body()
    prompts = {n: render(n, raw[n], act_code, body) for n in targets}

    if args.to_files:
        out_dir = Path(args.to_files); out_dir.mkdir(parents=True, exist_ok=True)
        for n, prompt in prompts.items():
            (out_dir / f"s{n}.md").write_text(prompt)
        print(f"wrote {len(prompts)} prompts to {out_dir}", file=sys.stderr)
        return

    if not args.dispatch:
        sep = SEPARATOR if len(prompts) > 1 else "\n"
        sys.stdout.write(sep.join(prompts.values()) + "\n")
        return

    # dispatch via codex, one attempt per section with optional retries
    def _run_with_retries(n: str) -> dict:
        prompt = prompts[n]
        last_err = None
        for attempt in range(1, args.retries + 2):
            try:
                r = dispatch_codex(prompt, n, args.timeout, args.model, args.reasoning)
                if r.returncode != 0:
                    last_err = f"exit={r.returncode}"
                    continue
                if verify_section(n):
                    return {"section": n, "status": "done", "attempts": attempt}
                last_err = "yuho check fail"
            except subprocess.TimeoutExpired:
                last_err = "timeout"
            except Exception as e:
                last_err = f"{e.__class__.__name__}"
        return {"section": n, "status": "failed", "attempts": args.retries + 1, "error": last_err}

    progress_path = REPO / args.progress
    progress_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(progress_path, "a")

    def _record(record: dict) -> None:
        fh.write(json.dumps(record) + "\n"); fh.flush()
        # stdout line = Monitor event; stderr = human-visible
        print(f"[{record['status']}] s{record['section']} (attempt {record.get('attempts','?')})", flush=True)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"[start] {len(targets)} sections, parallel={args.parallel}, timeout={args.timeout}s", flush=True)
    with ThreadPoolExecutor(max_workers=max(args.parallel, 1)) as pool:
        futs = {pool.submit(_run_with_retries, n): n for n in targets}
        for f in as_completed(futs):
            n = futs[f]
            try: _record(f.result())
            except Exception as e:
                _record({"section": n, "status": "failed", "error": f"{e.__class__.__name__}", "attempts": "?"})
    fh.close()
    print("[end] batch complete", flush=True)

if __name__ == "__main__":
    main()
