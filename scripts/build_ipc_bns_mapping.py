"""Generate IPC 1860 -> BNS 2023 structural mapping candidates.

The mapper compares each BNS section against every IPC raw section using
title similarity plus body/subitem token overlap. It emits top candidates,
not a human-certified concordance.

Usage:
    python scripts/build_ipc_bns_mapping.py \\
        --out library/_index/ipc_bns_mapping.json
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent
IPC_RAW = REPO / "library" / "indian_penal_code" / "_raw" / "act.json"
BNS_RAW = REPO / "library" / "bharatiya_nyaya_sanhita" / "_raw" / "act.json"
OUT = REPO / "library" / "_index" / "ipc_bns_mapping.json"

STOPWORDS = {
    "a", "an", "and", "any", "are", "as", "be", "by", "code", "for",
    "from", "in", "india", "indian", "is", "nyaya", "of", "or",
    "penal", "person", "sanhita", "section", "sections", "shall", "that",
    "the", "this", "to", "under", "with", "without", "who", "whoever",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _section_blob(section: dict[str, Any]) -> str:
    parts = [section.get("marginal_note", ""), section.get("text", "")]
    parts.extend(item.get("text", "") for item in section.get("sub_items", ()))
    return " ".join(parts)


def _tokens(text: str) -> Counter[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return Counter(w for w in words if len(w) > 1 and w not in STOPWORDS)


def _weighted_jaccard(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    keys = set(left) | set(right)
    numerator = sum(min(left[k], right[k]) for k in keys)
    denominator = sum(max(left[k], right[k]) for k in keys)
    return numerator / denominator if denominator else 0.0


def _title_ratio(left: str, right: str) -> float:
    norm_left = left.strip().strip(".").lower()
    norm_right = right.strip().strip(".").lower()
    if not norm_left or not norm_right:
        return 0.0
    return SequenceMatcher(None, norm_left, norm_right).ratio()


def _shared_terms(left: Counter[str], right: Counter[str], limit: int = 12) -> list[str]:
    overlap = set(left) & set(right)
    ranked = sorted(overlap, key=lambda t: (left[t] + right[t], t), reverse=True)
    return ranked[:limit]


def score_pair(bns: dict[str, Any], ipc: dict[str, Any]) -> dict[str, Any]:
    bns_tokens = _tokens(_section_blob(bns))
    ipc_tokens = _tokens(_section_blob(ipc))
    title = _title_ratio(bns.get("marginal_note", ""), ipc.get("marginal_note", ""))
    body = _weighted_jaccard(bns_tokens, ipc_tokens)
    title_equal = (
        bns.get("marginal_note", "").strip().strip(".").lower()
        == ipc.get("marginal_note", "").strip().strip(".").lower()
    )
    score = 0.55 * body + 0.35 * title + (0.10 if title_equal else 0.0)
    return {
        "score": round(score, 6),
        "title_ratio": round(title, 6),
        "token_overlap": round(body, 6),
        "shared_terms": _shared_terms(bns_tokens, ipc_tokens),
    }


def _confidence(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "medium"
    if score >= 0.25:
        return "low"
    return "weak"


def build_mapping(ipc_raw: Path = IPC_RAW, bns_raw: Path = BNS_RAW, top_n: int = 5) -> dict:
    ipc = _load(ipc_raw)
    bns = _load(bns_raw)
    ipc_sections = ipc.get("sections", [])
    rows = []
    for bns_section in bns.get("sections", []):
        candidates = []
        for ipc_section in ipc_sections:
            scored = score_pair(bns_section, ipc_section)
            candidates.append({
                "ipc_number": ipc_section.get("number", ""),
                "ipc_title": ipc_section.get("marginal_note", ""),
                **scored,
            })
        candidates.sort(
            key=lambda c: (c["score"], c["title_ratio"], c["token_overlap"]),
            reverse=True,
        )
        top = candidates[:top_n]
        best = top[0] if top else None
        rows.append({
            "bns_number": bns_section.get("number", ""),
            "bns_title": bns_section.get("marginal_note", ""),
            "confidence": _confidence(float(best["score"])) if best else "none",
            "best_ipc": best,
            "ipc_candidates": top,
        })
    return {
        "generated_at": _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds"),
        "method": "structural_title_body_token_overlap_v1",
        "note": "Generated candidates; not a human-certified concordance.",
        "sources": {
            "ipc": str(ipc_raw.relative_to(REPO)),
            "bns": str(bns_raw.relative_to(REPO)),
        },
        "stats": {
            "ipc_sections": len(ipc_sections),
            "bns_sections": len(bns.get("sections", [])),
            "top_n": top_n,
        },
        "mappings": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ipc", type=Path, default=IPC_RAW)
    parser.add_argument("--bns", type=Path, default=BNS_RAW)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--top-n", type=int, default=5)
    args = parser.parse_args()

    payload = build_mapping(args.ipc, args.bns, args.top_n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"wrote {payload['stats']['bns_sections']} BNS mappings -> {args.out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
