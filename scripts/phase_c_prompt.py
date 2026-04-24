"""phase_c_prompt.py — emit a paste-ready encoding prompt for one or more PC sections.

renders doc/PHASE_C_ENCODING_PROMPT.md with `{N}` substituted by each section
number, and prefixes each prompt with a pre-filled "Section context" block
(marginal note, SSO anchor/URL, suggested slug) so the agent does not have
to look those up.

usage:
    python scripts/phase_c_prompt.py 34                 # one section
    python scripts/phase_c_prompt.py 34 300 304A        # multiple
    python scripts/phase_c_prompt.py --next 10          # next 10 unencoded in section order
    python scripts/phase_c_prompt.py --list             # tab-separated: number<TAB>marginal_note
    python scripts/phase_c_prompt.py 415 | pbcopy       # copy one prompt to clipboard (macOS)
    python scripts/phase_c_prompt.py --next 5 --stdout-split  # print sentinel-separated prompts,
                                                        # one per section, for scripted fan-out

output separator between multiple prompts: a single line `<<<---NEXT_SECTION--->>>`.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = REPO / "doc" / "PHASE_C_ENCODING_PROMPT.md"
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

def main() -> None:
    p = argparse.ArgumentParser(prog="phase_c_prompt", description=__doc__)
    p.add_argument("nums", nargs="*", help="PC section numbers (e.g. 34 304A 511)")
    p.add_argument("--next", type=int, metavar="K", dest="next_k",
                   help="emit the next K unencoded sections (in section order)")
    p.add_argument("--list", action="store_true",
                   help="just list unencoded sections as TAB-separated num\\tmarginal_note")
    p.add_argument("--stdout-split", action="store_true",
                   help="emit each prompt followed by the sentinel separator (for scripted fan-out)")
    args = p.parse_args()

    raw, act_code = load_raw()
    encoded = load_encoded_numbers()
    unencoded = [n for n in raw if n not in encoded]

    if args.list:
        for n in sorted(unencoded, key=_sortkey):
            print(f"{n}\t{raw[n].get('marginal_note','')}")
        return

    targets: list[str] = list(args.nums)
    if args.next_k:
        ordered = sorted(unencoded, key=_sortkey)
        targets.extend([n for n in ordered if n not in targets][:args.next_k])

    if not targets:
        p.error("supply section numbers, or --next K, or --list")

    missing = [n for n in targets if n not in raw]
    if missing:
        print(f"warn: not in raw corpus: {missing}", file=sys.stderr)

    body = load_template_body()
    prompts = [render(n, raw[n], act_code, body) for n in targets if n in raw]
    sep = SEPARATOR if (args.stdout_split or len(prompts) > 1) else "\n"
    sys.stdout.write(sep.join(prompts) + ("\n" if prompts else ""))

if __name__ == "__main__":
    main()
