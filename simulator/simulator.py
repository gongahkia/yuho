#!/usr/bin/env python3
"""Yuho fact-pattern simulator.

Loads a fact pattern (YAML/JSON), pulls the corresponding encoded
section's elements/exceptions from the corpus, and emits a structural
trace: which elements the facts satisfy / contradict / leave unresolved,
which asserted exceptions match recognised encoded exceptions.

This is **not** a legal adjudicator. It does not decide whether an
offence is made out, predict case outcomes, or substitute for legal
advice. It is a teaching / research demo over the encoded grammar.

Usage:
    python3 simulator/simulator.py simulator/fixtures/s415_classic.yaml
    python3 simulator/simulator.py --json out.json simulator/fixtures/s378_theft.yaml
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"


# ---------------------------------------------------------------------------
# Fact-pattern parsing
# ---------------------------------------------------------------------------


def _load_yaml_or_json(path: Path) -> Dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    # Tiny YAML loader: support a useful subset (top-level keys, lists,
    # nested dicts via indent). Falls back to json if file looks JSON.
    if raw.lstrip().startswith("{"):
        return json.loads(raw)
    try:
        import yaml  # type: ignore
        return yaml.safe_load(raw)
    except ImportError:
        return _mini_yaml(raw)


def _mini_yaml(text: str) -> Dict[str, Any]:
    """Minimal YAML parser sufficient for our simple fact-pattern docs.

    Supports: top-level mappings, scalar values, simple list of strings or
    list of mappings, two-space-indented nested mappings. Does not support
    anchors, multi-line scalars (>, |), tags, or aliases.
    """
    lines = [ln for ln in text.splitlines() if not ln.lstrip().startswith("#")]
    out: Dict[str, Any] = {}
    stack: List[Tuple[int, Any]] = [(0, out)]
    i = 0
    n = len(lines)

    def parse_scalar(s: str) -> Any:
        s = s.strip()
        if s == "" or s.lower() == "null" or s == "~":
            return None
        if s.lower() in ("true", "false"):
            return s.lower() == "true"
        if (s.startswith('"') and s.endswith('"')) or (
            s.startswith("'") and s.endswith("'")
        ):
            return s[1:-1]
        try:
            if "." in s:
                return float(s)
            return int(s)
        except ValueError:
            return s

    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        indent = len(line) - len(line.lstrip())
        # Pop deeper containers.
        while stack and indent < stack[-1][0]:
            stack.pop()
        cur = stack[-1][1]
        stripped = line.strip()
        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            if isinstance(cur, list):
                if ":" in item_text and not item_text.startswith('"'):
                    # list of mappings
                    new_map: Dict[str, Any] = {}
                    cur.append(new_map)
                    stack.append((indent + 2, new_map))
                    # The "- " line itself may carry a key:value.
                    k, _, v = item_text.partition(":")
                    new_map[k.strip()] = parse_scalar(v)
                else:
                    cur.append(parse_scalar(item_text))
            else:
                # We expected a mapping-context but got a list item; ignore.
                pass
        elif ":" in stripped:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                # Could be opening a nested mapping or list.
                # Peek next line.
                nxt = lines[i + 1] if i + 1 < n else ""
                nxt_strip = nxt.strip()
                nxt_indent = len(nxt) - len(nxt.lstrip())
                if nxt_strip.startswith("- ") and nxt_indent > indent:
                    new_list: List[Any] = []
                    cur[key] = new_list
                    stack.append((nxt_indent, new_list))
                else:
                    new_map = {}
                    cur[key] = new_map
                    stack.append((indent + 2, new_map))
            elif val.startswith("|") or val.startswith(">"):
                # Multi-line block scalar: collect indented lines.
                buf: List[str] = []
                j = i + 1
                while j < n:
                    nxt = lines[j]
                    nxt_indent = len(nxt) - len(nxt.lstrip())
                    if nxt.strip() == "":
                        buf.append("")
                        j += 1
                        continue
                    if nxt_indent <= indent:
                        break
                    buf.append(nxt[indent + 2:])
                    j += 1
                cur[key] = "\n".join(buf).rstrip() if val.startswith("|") else " ".join(b.strip() for b in buf if b.strip())
                i = j - 1
            else:
                cur[key] = parse_scalar(val)
        i += 1
    return out


# ---------------------------------------------------------------------------
# Corpus lookup
# ---------------------------------------------------------------------------


def _load_section_record(num: str) -> Optional[Dict[str, Any]]:
    path = CORPUS / "sections" / f"s{num}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Element extraction
# ---------------------------------------------------------------------------


_ELEMENT_RE = re.compile(
    r"\b(actus_reus|mens_rea|circumstance|obligation|prohibition|permission)"
    r"\s+(\w+)\s*:=\s*\"([^\"]+)\""
)
_EXCEPTION_RE = re.compile(
    r'^\s*exception\s+"([^"]+)"', re.MULTILINE
)


def _extract_elements(yh: str) -> List[Dict[str, str]]:
    """Pull element declarations from the .yh source."""
    out: List[Dict[str, str]] = []
    for m in _ELEMENT_RE.finditer(yh):
        out.append({"kind": m.group(1), "name": m.group(2), "description": m.group(3)})
    return out


def _extract_exceptions(yh: str) -> List[str]:
    return [m.group(1) for m in _EXCEPTION_RE.finditer(yh)]


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def _all_fact_strings(facts: Dict[str, Any]) -> List[str]:
    """Collect every prose fact field for substring matching."""
    out: List[str] = []
    for act in facts.get("acts", []) or []:
        if isinstance(act, dict):
            d = act.get("description", "")
            if d:
                out.append(str(d))
    ms = facts.get("mental_states", {}) or {}
    if isinstance(ms, dict):
        for party, states in ms.items():
            if isinstance(states, dict):
                for k, v in states.items():
                    out.append(f"{k}: {v}")
            else:
                out.append(str(states))
    for c in facts.get("circumstances", []) or []:
        if c:
            out.append(str(c))
    for o in facts.get("outcomes", []) or []:
        if isinstance(o, dict):
            d = o.get("description", "")
            if d:
                out.append(str(d))
    return out


def _suggests(elem_desc: str, fact_strings: List[str]) -> Optional[str]:
    """Return a fact string that overlaps with the element description, if any."""
    desc_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", elem_desc)}
    for fact in fact_strings:
        fact_words = {w.lower() for w in re.findall(r"[A-Za-z]{4,}", fact)}
        if len(desc_words & fact_words) >= 2:
            return fact
    return None


def evaluate(facts: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a fact pattern against the encoded section's elements."""
    section_num = str(facts.get("section", "")).strip()
    if not section_num:
        return {"error": "fact pattern is missing required 'section' field"}
    rec = _load_section_record(section_num)
    if not rec:
        return {"error": f"section {section_num!r} not in corpus"}

    yh = rec.get("encoded", {}).get("yh_source") or ""
    elements = _extract_elements(yh)
    exceptions = _extract_exceptions(yh)
    fact_strings = _all_fact_strings(facts)
    fact_facts = facts.get("fact_facts", {}) or {}

    satisfied: List[str] = []
    contradicted: List[str] = []
    unresolved: List[str] = []
    suggested: List[Tuple[str, str]] = []
    warnings: List[str] = []

    for el in elements:
        name = el["name"]
        if name in fact_facts:
            if fact_facts[name] is True:
                satisfied.append(name)
            elif fact_facts[name] is False:
                contradicted.append(name)
            else:
                unresolved.append(name)
            continue
        hit = _suggests(el["description"], fact_strings)
        if hit:
            suggested.append((name, hit[:80]))
        else:
            unresolved.append(name)

    if not elements:
        warnings.append("no typed elements found in encoded source")

    asserted = facts.get("asserted_exceptions", []) or []
    raised_names = []
    matched_names = []
    for entry in asserted:
        if isinstance(entry, dict):
            n = entry.get("name", "")
        else:
            n = str(entry)
        raised_names.append(n)
        # Naive match: substring against encoded exception labels.
        for ex in exceptions:
            if n.lower() in ex.lower() or ex.lower() in n.lower():
                matched_names.append(n)
                break

    verdict = _verdict(satisfied, contradicted, unresolved, suggested, raised_names, matched_names, elements)

    return {
        "section_number": rec["section_number"],
        "section_title": rec.get("section_title"),
        "fact_pattern_name": facts.get("name"),
        "n_elements": len(elements),
        "satisfied": satisfied,
        "contradicted": contradicted,
        "unresolved": unresolved,
        "suggested": [{"element": n, "fact": f} for (n, f) in suggested],
        "exceptions_raised": raised_names,
        "exceptions_matched": matched_names,
        "verdict": verdict,
        "warnings": warnings,
        "disclaimer": (
            "Structural trace over the encoded section, not a legal "
            "adjudication. The simulator does not decide whether an offence "
            "is made out and does not provide legal advice."
        ),
    }


def _verdict(sat, contradict, unresolved, sug, raised, matched, elements) -> str:
    if not elements:
        return "no elements to evaluate"
    if contradict:
        return f"{len(contradict)} element(s) contradicted by the facts; offence not made out on a structural read"
    if unresolved or sug:
        return (
            f"{len(sat)}/{len(elements)} elements satisfied directly, "
            f"{len(sug)} suggested, {len(unresolved)} unresolved; "
            "fact pattern under-specifies the section"
        )
    if matched:
        return f"all {len(sat)} elements satisfied; {len(matched)} asserted exception(s) match recognised encoded exceptions"
    if raised:
        return f"all {len(sat)} elements satisfied; asserted exceptions {raised} not recognised by the encoded section"
    return f"all {len(sat)} elements satisfied; no exceptions asserted"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("fact_pattern", help="Path to a YAML or JSON fact pattern")
    parser.add_argument("--json", dest="json_output", action="store_true",
                        help="Emit raw JSON trace; otherwise human-readable text")
    args = parser.parse_args()

    path = Path(args.fact_pattern)
    if not path.exists():
        sys.exit(f"error: fact pattern not found: {path}")

    facts = _load_yaml_or_json(path)
    result = evaluate(facts)

    if args.json_output:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    if "error" in result:
        print(f"error: {result['error']}")
        return 1

    print(f"Section: s{result['section_number']} · {result['section_title']}")
    if result.get("fact_pattern_name"):
        print(f"Fact pattern: {result['fact_pattern_name']}")
    print()
    print(f"Verdict: {result['verdict']}")
    print()
    print(f"Elements ({result['n_elements']}):")
    for n in result["satisfied"]:
        print(f"  ✓ satisfied:    {n}")
    for n in result["contradicted"]:
        print(f"  ✗ contradicted: {n}")
    for s in result["suggested"]:
        print(f"  ~ suggested:    {s['element']}  ← {s['fact']}")
    for n in result["unresolved"]:
        print(f"  ? unresolved:   {n}")
    if result["exceptions_raised"]:
        print()
        print(f"Asserted exceptions: {', '.join(result['exceptions_raised'])}")
        if result["exceptions_matched"]:
            print(f"  matched encoded: {', '.join(result['exceptions_matched'])}")
        else:
            print("  none matched any encoded exception in this section")
    if result.get("warnings"):
        print()
        for w in result["warnings"]:
            print(f"warning: {w}")
    print()
    print(f"Disclaimer: {result['disclaimer']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
