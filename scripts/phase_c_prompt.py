"""phase_c_prompt.py — emit a paste-ready encoding prompt for one or more PC sections.

renders doc/PHASE_C_ENCODING_PROMPT.md with `{N}` substituted by each section
number, and prefixes each prompt with a pre-filled "Section context" block
(marginal note, SSO anchor/URL, suggested slug) so the agent does not have
to look those up.

usage:
    python scripts/phase_c_prompt.py 34                 # one section
    python scripts/phase_c_prompt.py 1-20               # range (20 prompts, sentinel-separated)
    python scripts/phase_c_prompt.py 34,35,304A         # comma list
    python scripts/phase_c_prompt.py 1-10,34,304A       # range + list mix
    python scripts/phase_c_prompt.py 34 300 304A        # space-separated positional args
    python scripts/phase_c_prompt.py --next 10          # next K unencoded in section order
    python scripts/phase_c_prompt.py --list             # tab-separated: number<TAB>marginal_note
    python scripts/phase_c_prompt.py 415 | pbcopy       # copy one prompt to clipboard (macOS)
    python scripts/phase_c_prompt.py 1-20 --batch       # ONE prompt telling a single long-running
                                                        # agent to do all 20 sequentially

modes:
    default (N prompts for N agents)     emit one prompt per section, separated by the sentinel
                                         `<<<---NEXT_SECTION--->>>`. Dispatch to N parallel agents.
    --batch (1 prompt for 1 agent)       wrap all sections in a single meta-prompt telling one
                                         agent to work through them sequentially. Best for Codex
                                         Cloud or Claude Code sessions running unattended.
    already-encoded sections are dropped from the output (dispatcher respects coverage.json).
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "docs" / "researcher" / "phase-c-encoding-prompt.md"
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
    cut = slug[:maxlen].rsplit("_", 1)[0]                # truncate at word boundary
    return cut or slug[:maxlen]

def _sortkey(n: str) -> tuple:
    m = re.match(r"(\d+)([A-Z]*)", n)                    # "304A" sorts after "304"
    return (int(m.group(1)), m.group(2)) if m else (9999, n)

def expand_spec(specs: list[str], raw: dict[str, dict]) -> list[str]:
    """resolve a mixed list of tokens into explicit section numbers present in raw.
    tokens may be: single ("34", "304A"), range ("1-20"), comma list ("a,b,c"), or
    any combination: ["1-10,34", "304A"] → [1..10 ∩ raw, 34, 304A]."""
    out: list[str] = []
    seen: set[str] = set()
    # flatten comma-separated pieces
    tokens = [t.strip() for s in specs for t in s.split(",") if t.strip()]
    for tok in tokens:
        m = re.fullmatch(r"(\d+)\s*-\s*(\d+)", tok)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
            if lo > hi: lo, hi = hi, lo
            for i in range(lo, hi + 1):
                # include base number and any letter-suffixed variants present in raw
                for cand in sorted([k for k in raw if re.fullmatch(rf"{i}[A-Z]*", k)], key=_sortkey):
                    if cand not in seen:
                        seen.add(cand); out.append(cand)
        else:
            if tok in seen: continue
            seen.add(tok); out.append(tok)
    return out

def load_template_body() -> str:
    """extract just the agent-facing body of the doc (between '## PROMPT' and the
    human-only 'Orchestration tips' section)."""
    doc = TEMPLATE_PATH.read_text()
    start = doc.find("## PROMPT")
    if start < 0: return doc
    start = doc.find("\n", start) + 1
    end = doc.find("\n## Orchestration tips")
    end = end if end > 0 else len(doc)
    return doc[start:end].strip() + "\n"

def load_raw() -> tuple[dict[str, dict], str]:
    d = json.loads(RAW_PATH.read_text())
    by_num = {s["number"]: s for s in d["sections"] if s.get("number")}
    return by_num, d.get("act_code", "PC1871")

def load_encoded_numbers() -> set[str]:
    if not COVERAGE_PATH.is_file(): return set()
    d = json.loads(COVERAGE_PATH.read_text())
    return {s["number"] for s in d.get("sections", []) if s.get("encoded_path")}

def render(num: str, sec: dict, act_code: str, body: str) -> str:
    marginal = sec.get("marginal_note") or f"Section {num}"
    anchor = sec.get("anchor_id") or f"pr{num}-"
    sso = f"https://sso.agc.gov.sg/Act/{act_code}?ProvIds={anchor}#{anchor}"
    slug = slugify(marginal)
    header = (
        f"## Section context (pre-filled by dispatcher)\n\n"
        f"- Section: **{num}**\n"
        f"- Marginal note: **{marginal}**\n"
        f"- SSO anchor id: `{anchor}`\n"
        f"- SSO URL: {sso}\n"
        f"- Suggested directory: `library/penal_code/s{num}_{slug}/`\n"
        f"- Canonical text: look up `number == \"{num}\"` in `library/penal_code/_raw/act.json`\n\n"
        f"---\n\n"
    )
    return header + body.replace("{N}", num)

def render_batch(nums: list[str], raw: dict[str, dict], act_code: str, body: str) -> str:
    """single prompt instructing ONE agent to do multiple sections sequentially."""
    lines = [
        "# Phase C Batch — Encode Multiple PC Sections",
        "",
        "You will encode **{k} Singapore Penal Code sections** in this session. Each".format(k=len(nums)),
        "gets its own directory (`library/penal_code/s<N>_<slug>/`). Work sequentially:",
        "read the section's canonical text, write the deliverables, run `yuho check`,",
        "commit mentally, move to the next section.",
        "",
        "## Sections to encode (in order)",
        "",
    ]
    for n in nums:
        s = raw[n]
        marginal = s.get("marginal_note") or f"Section {n}"
        anchor = s.get("anchor_id") or f"pr{n}-"
        slug = slugify(marginal)
        lines.append(
            f"- **s{n}** — {marginal}  "
            f"  anchor=`{anchor}`  dir=`library/penal_code/s{n}_{slug}/`"
        )
    lines += [
        "",
        "## Instructions per section",
        "",
        "Apply the instructions below **once per section**, in order. Maintain",
        "separation — do not cross-reference data between sections while working.",
        "After finishing each section, print a single line `completed: s<N>` and",
        "move on. If you hit a hard blocker on one section, write its `GAPS.md`,",
        "skip the failing deliverables, print `skipped: s<N> — <reason>`, and",
        "continue to the next.",
        "",
        "---",
        "",
        body.replace("{N}", "<N>"),
        "",
        "---",
        "",
        "## Batch completion report",
        "",
        "At the end, print a summary:",
        "",
        "```",
        "batch summary:",
        "  completed: <count>",
        "  skipped: <count> (list sections)",
        "  gaps: <count> (list sections with GAPS.md)",
        "```",
    ]
    return "\n".join(lines) + "\n"

def main() -> None:
    p = argparse.ArgumentParser(prog="phase_c_prompt", description=__doc__)
    p.add_argument("specs", nargs="*",
                   help="section numbers, ranges (1-20), comma lists (34,35,36), or a mix")
    p.add_argument("--next", type=int, metavar="K", dest="next_k",
                   help="emit the next K unencoded sections (in section order)")
    p.add_argument("--list", action="store_true",
                   help="list unencoded sections as TAB-separated num<TAB>marginal_note")
    p.add_argument("--batch", action="store_true",
                   help="emit ONE prompt for ONE agent to do all requested sections sequentially")
    p.add_argument("--include-encoded", action="store_true",
                   help="include sections that already have an encoding (off by default)")
    p.add_argument("--stdout-split", action="store_true",
                   help="force the sentinel separator even when emitting a single prompt")
    args = p.parse_args()

    raw, act_code = load_raw()
    encoded = load_encoded_numbers()
    unencoded = [n for n in raw if n not in encoded]

    if args.list:
        for n in sorted(unencoded, key=_sortkey):
            print(f"{n}\t{raw[n].get('marginal_note','')}")
        return

    targets: list[str] = expand_spec(args.specs, raw) if args.specs else []
    if args.next_k:
        ordered = sorted(unencoded, key=_sortkey)
        targets.extend([n for n in ordered if n not in targets][:args.next_k])

    if not targets:
        p.error("supply section numbers (e.g. 1-20 or 34 304A), or --next K, or --list")

    missing = [n for n in targets if n not in raw]
    if missing:
        print(f"warn: not in raw corpus, dropping: {missing}", file=sys.stderr)
    targets = [n for n in targets if n in raw]

    if not args.include_encoded:
        skipped = [n for n in targets if n in encoded]
        if skipped:
            print(f"info: already encoded, skipping: {skipped}", file=sys.stderr)
        targets = [n for n in targets if n not in encoded]

    if not targets:
        print("nothing to do — all requested sections are already encoded", file=sys.stderr)
        sys.exit(0)

    body = load_template_body()
    if args.batch:
        sys.stdout.write(render_batch(targets, raw, act_code, body))
        return
    prompts = [render(n, raw[n], act_code, body) for n in targets]
    sep = SEPARATOR if (args.stdout_split or len(prompts) > 1) else "\n"
    sys.stdout.write(sep.join(prompts) + ("\n" if prompts else ""))

if __name__ == "__main__":
    main()
