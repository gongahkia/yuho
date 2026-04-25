#!/usr/bin/env python3
"""Score model predictions against the Yuho benchmark gold answers.

Input format: a JSONL file where each line has at minimum:

    {"id": "<task id>", "task": "<task name>", "prediction": <model output>}

Where ``prediction`` matches the shape of the ``answer`` field for that
task. Extra fields are ignored.

Usage:
    python3 benchmarks/scorers/score.py --predictions out.jsonl
    python3 benchmarks/scorers/score.py --task penalty_extraction --predictions ...
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO = Path(__file__).resolve().parent.parent.parent
TASKS = Path(__file__).resolve().parent.parent / "tasks"


# ---------------------------------------------------------------------------
# Task scorers
# ---------------------------------------------------------------------------


def _exact(a, b) -> bool:
    return a == b


def _norm_section(s: Any) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip().strip(".").upper()
    if s.startswith("S."):
        s = s[2:].strip()
    if s.startswith("S") and len(s) > 1 and s[1].isdigit():
        s = s[1:]
    return s or None


def score_citation_grounding(answer: Dict[str, Any], pred: Any) -> Dict[str, Any]:
    gold = _norm_section(answer.get("section_number"))
    pred_section = _norm_section(
        pred.get("section_number") if isinstance(pred, dict) else pred
    )
    correct = gold is not None and gold == pred_section
    return {"correct": correct, "gold": gold, "pred": pred_section}


def score_element_classification(answer: Dict[str, Any], pred: Any) -> Dict[str, Any]:
    gold = (answer.get("kind") or "").strip().lower()
    pred_kind = (
        pred.get("kind") if isinstance(pred, dict) else pred
    )
    pred_kind = (str(pred_kind or "")).strip().lower()
    return {"correct": gold == pred_kind, "gold": gold, "pred": pred_kind}


def score_cross_reference(answer: Dict[str, Any], pred: Any) -> Dict[str, Any]:
    gold = set(_norm_section(s) for s in (answer.get("outgoing_sections") or []))
    gold.discard(None)
    pred_set = set()
    if isinstance(pred, dict):
        for s in (pred.get("outgoing_sections") or []):
            n = _norm_section(s)
            if n:
                pred_set.add(n)
    elif isinstance(pred, list):
        for s in pred:
            n = _norm_section(s)
            if n:
                pred_set.add(n)
    if not gold and not pred_set:
        return {"correct": True, "f1": 1.0, "precision": 1.0, "recall": 1.0,
                "gold": [], "pred": []}
    tp = len(gold & pred_set)
    p = tp / len(pred_set) if pred_set else 0.0
    r = tp / len(gold) if gold else 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) else 0.0
    return {"correct": gold == pred_set, "f1": round(f1, 3),
            "precision": round(p, 3), "recall": round(r, 3),
            "gold": sorted(gold), "pred": sorted(pred_set)}


def score_illustration_recognition(answer: Dict[str, Any], pred: Any) -> Dict[str, Any]:
    return score_citation_grounding(answer, pred)


def score_penalty_extraction(answer: Dict[str, Any], pred: Any) -> Dict[str, Any]:
    gold = (answer.get("encoded_penalty_block") or "").strip()
    pred_block = (
        pred.get("encoded_penalty_block") if isinstance(pred, dict) else pred
    )
    pred_block = str(pred_block or "").strip()
    # Normalise whitespace on both sides for forgiving exact-match.
    gn = " ".join(gold.split())
    pn = " ".join(pred_block.split())
    return {"correct": gn == pn, "gold": gold, "pred": pred_block}


SCORERS = {
    "citation_grounding": score_citation_grounding,
    "penalty_extraction": score_penalty_extraction,
    "element_classification": score_element_classification,
    "cross_reference": score_cross_reference,
    "illustration_recognition": score_illustration_recognition,
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--predictions", required=True, help="JSONL file with model predictions")
    parser.add_argument("--task", choices=list(SCORERS), help="Score only this task")
    parser.add_argument("--detail", action="store_true", help="Print per-row results")
    args = parser.parse_args()

    pred_rows = _load_jsonl(Path(args.predictions))
    pred_index = {r["id"]: r for r in pred_rows}

    overall: Dict[str, Dict[str, int]] = {}
    detail_rows: List[Dict[str, Any]] = []

    targets = [args.task] if args.task else list(SCORERS.keys())
    for task_name in targets:
        path = TASKS / f"{task_name}.jsonl"
        if not path.exists():
            print(f"warning: missing {path}", file=sys.stderr)
            continue
        gold_rows = _load_jsonl(path)
        n_total = len(gold_rows)
        n_scored = 0
        n_correct = 0
        f1_sum = 0.0
        scorer = SCORERS[task_name]
        for gold in gold_rows:
            pred = pred_index.get(gold["id"])
            if not pred:
                continue
            result = scorer(gold["answer"], pred.get("prediction"))
            n_scored += 1
            if result.get("correct"):
                n_correct += 1
            if "f1" in result:
                f1_sum += result["f1"]
            if args.detail:
                detail_rows.append({"task": task_name, "id": gold["id"], **result})

        overall[task_name] = {
            "n_total": n_total,
            "n_scored": n_scored,
            "n_correct": n_correct,
            "accuracy": round(n_correct / n_scored, 3) if n_scored else 0.0,
        }
        if f1_sum:
            overall[task_name]["mean_f1"] = round(f1_sum / n_scored, 3) if n_scored else 0.0

    print(json.dumps({"results": overall}, indent=2))
    if args.detail:
        Path("benchmarks/score-detail.jsonl").write_text(
            "\n".join(json.dumps(r) for r in detail_rows) + "\n"
        )
        print("Wrote per-row detail to benchmarks/score-detail.jsonl", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
