#!/usr/bin/env python3
"""Grounded AI answer verifier — does a model output cite real Yuho corpus?

Input: a JSON document representing a model's answer to a question about
the Singapore Penal Code, with explicit citations and source spans.

Schema (input):

    {
      "question": "<the question, optional>",
      "answer": "<the model's prose answer>",
      "claims": [
        {
          "text": "<a propositional claim from the answer>",
          "citations": [
            {
              "section": "415",                      # Penal Code section
              "kind": "raw" | "yh" | "english",      # which artefact backs it
              "span": "<verbatim quote from that artefact>"
            }
          ]
        }
      ]
    }

The verifier:

* checks every cited section exists in the corpus
* checks every cited span actually appears in the named artefact
* flags claims with no supporting citation
* emits a per-answer score: percent of claims with valid grounding,
  list of orphan claims, list of spurious citations

This is research infrastructure. It does not adjudicate truth or
correctness; it adjudicates whether the citations the model produced
match the corpus the model claims to be citing.

Usage:
    python3 scripts/verify_grounded.py answer.json
    python3 scripts/verify_grounded.py answer.json --strict   # fail on any orphan
    python3 scripts/verify_grounded.py answer.json --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent
CORPUS = REPO / "library" / "penal_code" / "_corpus"


# ---------------------------------------------------------------------------
# Corpus lookup (lazy)
# ---------------------------------------------------------------------------


_CACHE: Dict[str, Dict[str, Any]] = {}


def _load_section(num: str) -> Optional[Dict[str, Any]]:
    if num in _CACHE:
        return _CACHE[num]
    path = CORPUS / "sections" / f"s{num}.json"
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        rec = json.load(f)
    _CACHE[num] = rec
    return rec


# ---------------------------------------------------------------------------
# Span matching
# ---------------------------------------------------------------------------


def _normalise(s: str) -> str:
    """Collapse whitespace, lower case for forgiving substring match."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def _find_span(span: str, haystack: str) -> Optional[Dict[str, int]]:
    """Return {start, end} in haystack if span is a substring (whitespace-insensitive)."""
    if not span or not haystack:
        return None
    h = _normalise(haystack)
    s = _normalise(span)
    if s in h:
        return {"normalised_start": h.index(s), "normalised_end": h.index(s) + len(s)}
    return None


def _artefact(rec: Dict[str, Any], kind: str) -> str:
    """Return the artefact text for a citation kind."""
    if kind == "raw":
        return rec.get("raw", {}).get("text") or ""
    if kind == "yh":
        return rec.get("encoded", {}).get("yh_source") or ""
    if kind == "english":
        return rec.get("transpiled", {}).get("english") or ""
    return ""


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


def verify_citation(citation: Dict[str, Any]) -> Dict[str, Any]:
    sec = str(citation.get("section", "")).strip()
    kind = (citation.get("kind") or "raw").strip()
    span = (citation.get("span") or "").strip()

    if not sec:
        return {"ok": False, "reason": "missing 'section' field"}
    if kind not in ("raw", "yh", "english"):
        return {"ok": False, "reason": f"unknown kind {kind!r}"}

    rec = _load_section(sec)
    if rec is None:
        return {"ok": False, "reason": f"section s{sec} not in corpus"}

    artefact = _artefact(rec, kind)
    if not artefact:
        return {"ok": False, "reason": f"no '{kind}' artefact for s{sec}"}

    if not span:
        return {"ok": False, "reason": "missing 'span' field"}

    hit = _find_span(span, artefact)
    if hit is None:
        return {
            "ok": False,
            "reason": f"span not found in s{sec}'s {kind} artefact",
        }
    return {
        "ok": True,
        "section": sec,
        "kind": kind,
        "section_title": rec.get("section_title"),
        "raw_sha256": rec.get("raw", {}).get("hash_sha256"),
    }


def verify_answer(answer: Dict[str, Any]) -> Dict[str, Any]:
    claims = answer.get("claims") or []
    if not isinstance(claims, list):
        return {"error": "expected 'claims' to be a list"}

    n_claims = len(claims)
    n_grounded = 0
    n_orphans = 0
    per_claim: List[Dict[str, Any]] = []
    spurious: List[Dict[str, Any]] = []

    for i, claim in enumerate(claims):
        text = (claim.get("text") or "").strip()
        cites = claim.get("citations") or []
        if not cites:
            per_claim.append({
                "index": i,
                "text": text,
                "ok": False,
                "reason": "claim has no citations",
                "citations_total": 0,
                "citations_valid": 0,
            })
            n_orphans += 1
            continue
        results = [verify_citation(c) for c in cites]
        valid = [r for r in results if r.get("ok")]
        invalid = [r for r in results if not r.get("ok")]
        if valid:
            n_grounded += 1
        else:
            n_orphans += 1
        for inv, c in zip(invalid, [c for c in cites]):
            spurious.append({"claim_index": i, "citation": c, "reason": inv.get("reason")})
        per_claim.append({
            "index": i,
            "text": text,
            "ok": bool(valid),
            "citations_total": len(cites),
            "citations_valid": len(valid),
            "citations": results,
        })

    pct = round(n_grounded / n_claims, 3) if n_claims else 0.0
    return {
        "n_claims": n_claims,
        "n_grounded": n_grounded,
        "n_orphans": n_orphans,
        "grounded_fraction": pct,
        "per_claim": per_claim,
        "spurious_citations": spurious,
        "verdict": (
            "all claims grounded" if n_orphans == 0 and n_claims > 0
            else f"{n_orphans}/{n_claims} claims un-grounded"
        ),
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("answer_file", help="Path to a JSON answer document")
    parser.add_argument("--strict", action="store_true",
                        help="Exit non-zero if any claim is un-grounded")
    parser.add_argument("--json", dest="json_output", action="store_true",
                        help="Emit raw JSON report (default: human-readable)")
    args = parser.parse_args()

    path = Path(args.answer_file)
    if not path.exists():
        sys.exit(f"error: answer file not found: {path}")
    answer = json.loads(path.read_text(encoding="utf-8"))
    report = verify_answer(answer)

    if "error" in report:
        sys.exit(f"error: {report['error']}")

    if args.json_output:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"Verdict: {report['verdict']}")
        print(f"Grounded: {report['n_grounded']}/{report['n_claims']} claims "
              f"({report['grounded_fraction']*100:.0f}%)")
        if report["spurious_citations"]:
            print(f"\nSpurious citations ({len(report['spurious_citations'])}):")
            for s in report["spurious_citations"]:
                c = s["citation"]
                print(f"  [{s['claim_index']}] s{c.get('section')} ({c.get('kind')}): {s['reason']}")
        for entry in report["per_claim"]:
            mark = "✓" if entry["ok"] else "✗"
            print(f"  {mark} claim {entry['index']}: {entry['citations_valid']}/{entry['citations_total']} cites valid")
            if not entry["ok"]:
                print(f"     {entry.get('reason') or '(orphan or all citations spurious)'}")

    if args.strict and report["n_orphans"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
