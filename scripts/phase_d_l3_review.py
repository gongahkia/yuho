"""phase_d_l3_review.py — dispatch L3 reviewer agents to audit encoded
sections and stamp metadata.toml when faithful.

renders doc/PHASE_D_L3_REVIEW_PROMPT.md with per-section context and
invokes `codex exec --full-auto -m gpt-5.4 -c model_reasoning_effort=high`
by default. Each agent either stamps [verification].last_verified on a
passing section, or appends a flag to library/penal_code/_L3_flags.md
for human review.

usage:
    python scripts/phase_d_l3_review.py --list
    python scripts/phase_d_l3_review.py 415
    python scripts/phase_d_l3_review.py 400-500
    python scripts/phase_d_l3_review.py --all-unstamped --dispatch --parallel 8
    python scripts/phase_d_l3_review.py --all-unstamped --dispatch --parallel 8 \\
        --progress library/penal_code/_coverage/phase_d_l3_progress.jsonl --resume

defaults for dispatch:
    --model gpt-5.4
    --reasoning high
"""
from __future__ import annotations
import argparse, json, re, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "docs" / "researcher" / "phase-d-l3-review-prompt.md"
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

def load_l3_stamped() -> set[str]:
    """Sections that already have a stamped [verification].last_verified."""
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
        f"- Directory: `library/penal_code/s{num}_{slug}/`\n"
        f"- Canonical text: the entry in `library/penal_code/_raw/act.json` with `number == \"{num}\"`\n\n"
        f"---\n\n"
    )
    return header + body.replace("{N}", num)

def dispatch_codex(prompt: str, timeout: int = 900,
                   model: str | None = None, reasoning: str | None = None) -> subprocess.CompletedProcess:
    """Run `codex exec --full-auto` with the rendered prompt. Returns CompletedProcess."""
    cmd = ["codex", "exec", "--full-auto", "--skip-git-repo-check", "-C", str(REPO)]
    if model: cmd += ["-m", model]
    if reasoning: cmd += ["-c", f"model_reasoning_effort={reasoning}"]
    cmd.append("-")
    return subprocess.run(
        cmd, input=prompt, text=True, capture_output=True, timeout=timeout,
    )

def is_stamped_on_disk(n: str) -> bool:
    """Check whether the section's metadata.toml already has last_verified set."""
    d = find_dir(n)
    if not d: return False
    meta = d / "metadata.toml"
    if not meta.is_file(): return False
    try:
        txt = meta.read_text()
        return bool(re.search(r"last_verified\s*=\s*\"[^\"]+\"", txt))
    except Exception:
        return False

def main() -> None:
    p = argparse.ArgumentParser(prog="phase_d_l3_review", description=__doc__)
    p.add_argument("specs", nargs="*",
                   help="section numbers, ranges (1-20), or comma lists")
    p.add_argument("--list", action="store_true",
                   help="list sections still needing L3 review")
    p.add_argument("--all-unstamped", action="store_true",
                   help="target every section without a stamped [verification]")
    p.add_argument("--dispatch", action="store_true",
                   help="actually invoke `codex exec` instead of just printing")
    p.add_argument("--parallel", type=int, default=1, metavar="K",
                   help="with --dispatch, run up to K codex instances in parallel")
    p.add_argument("--progress", metavar="FILE", default="library/penal_code/_coverage/phase_d_l3_progress.jsonl",
                   help="append-only JSONL file recording per-section decisions")
    p.add_argument("--resume", action="store_true",
                   help="skip sections already recorded in the progress file")
    p.add_argument("--timeout", type=int, default=900,
                   help="per-section timeout for --dispatch in seconds")
    p.add_argument("--model", default="gpt-5.4",
                   help="codex model (default: gpt-5.4)")
    p.add_argument("--reasoning", default="high",
                   help="reasoning effort (low|medium|high|xhigh; default: high)")
    args = p.parse_args()

    raw, act_code = load_raw()
    stamped = load_l3_stamped()

    if args.list:
        for n in sorted(set(raw) - stamped, key=_sortkey):
            print(f"{n}\t{raw[n].get('marginal_note','')[:80]}")
        return

    if args.all_unstamped:
        targets = sorted(set(raw) - stamped, key=_sortkey)
    else:
        targets = expand_spec(args.specs, raw) if args.specs else []
    if not targets: p.error("supply section numbers, --all-unstamped, or --list")
    targets = [n for n in targets if n in raw]

    # resume: skip sections already in the progress file
    processed: set[str] = set()
    progress_path = REPO / args.progress
    if args.resume and progress_path.is_file():
        for line in progress_path.read_text().splitlines():
            try:
                r = json.loads(line)
                processed.add(r["section"])
            except Exception:
                continue
        before = len(targets)
        targets = [n for n in targets if n not in processed]
        print(f"[resume] skipped {before - len(targets)} already-reviewed sections; {len(targets)} remain", flush=True)

    body = load_template_body()
    prompts = {n: render(n, raw[n], act_code, body) for n in targets}

    if not args.dispatch:
        sep = SEPARATOR if len(prompts) > 1 else "\n"
        sys.stdout.write(sep.join(prompts.values()) + "\n")
        return

    def _run(n: str) -> dict:
        prompt = prompts[n]
        try:
            r = dispatch_codex(prompt, args.timeout, args.model, args.reasoning)
            if r.returncode != 0:
                return {"section": n, "decision": "ERROR", "error": f"exit={r.returncode}"}
            stamped_now = is_stamped_on_disk(n)
            return {"section": n, "decision": "STAMP" if stamped_now else "FLAG"}
        except subprocess.TimeoutExpired:
            return {"section": n, "decision": "ERROR", "error": "timeout"}
        except Exception as e:
            return {"section": n, "decision": "ERROR", "error": e.__class__.__name__}

    progress_path.parent.mkdir(parents=True, exist_ok=True)
    fh = open(progress_path, "a")

    def _record(record: dict) -> None:
        fh.write(json.dumps(record) + "\n"); fh.flush()
        print(f"[{record['decision']}] s{record['section']}" +
              (f" — {record['error']}" if "error" in record else ""), flush=True)

    from concurrent.futures import ThreadPoolExecutor, as_completed
    print(f"[start] {len(targets)} sections, model={args.model}, reasoning={args.reasoning}, parallel={args.parallel}", flush=True)
    with ThreadPoolExecutor(max_workers=max(args.parallel, 1)) as pool:
        futs = {pool.submit(_run, n): n for n in targets}
        for f in as_completed(futs):
            n = futs[f]
            try: _record(f.result())
            except Exception as e:
                _record({"section": n, "decision": "ERROR", "error": e.__class__.__name__})
    fh.close()
    # quick summary
    counts = {"STAMP": 0, "FLAG": 0, "ERROR": 0}
    for line in progress_path.read_text().splitlines():
        try: counts[json.loads(line)["decision"]] = counts.get(json.loads(line)["decision"], 0) + 1
        except Exception: continue
    print(f"[end] STAMP={counts.get('STAMP',0)} FLAG={counts.get('FLAG',0)} ERROR={counts.get('ERROR',0)}", flush=True)

    # aggregate per-section _L3_FLAG.md files into the canonical combined file.
    # Parallel agents write to disjoint per-section files; we stitch them here.
    flags_dir = REPO / "library" / "penal_code"
    out_path = flags_dir / "_L3_flags.md"
    entries: list[tuple[str, str]] = []
    for p in sorted(flags_dir.glob("s*/_L3_FLAG.md")):
        section_dir = p.parent
        m = re.match(r"s(\d+[A-Z]*)_", section_dir.name)
        if not m: continue
        section = m.group(1)
        entries.append((section, p.read_text()))
    entries.sort(key=lambda e: _sortkey(e[0]))

    with open(out_path, "w") as f:
        f.write("# Phase D L3 — flagged sections for human review\n\n")
        f.write("_Aggregated from per-section `_L3_FLAG.md` files. "
                "Regenerate by re-running `phase_d_l3_review.py`._\n\n")
        for _section, content in entries:
            # per-section files start with a `# sN — L3 flag` header; demote to `##` for the combined doc
            demoted = re.sub(r"^#\s+", "## ", content, count=1, flags=re.MULTILINE)
            f.write(demoted.rstrip() + "\n\n")
    print(f"[aggregate] {len(entries)} flags → {out_path}", flush=True)

if __name__ == "__main__":
    main()
