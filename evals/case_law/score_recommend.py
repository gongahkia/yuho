"""Score `yuho recommend` against curated Singapore case-law fixtures.

For every YAML fixture under ``evals/case_law/fixtures/``, run the
``ChargeRecommender`` over the encoded fact pattern and score the
ranked output against the section the prosecution actually charged
(``actual_charge`` field).

Headline metrics:

* **Top-1 accuracy** — recommender's highest-coverage section
  matches ``actual_charge``.
* **Top-3 / Top-5 accuracy** — actual charge appears in the top
  3 / 5 of the ranked candidate list.
* **Mean Reciprocal Rank** — averaged over fixtures; 1.0 if every
  case is top-1, lower as the actual charge slips down the list.
* **Per-chapter agreement** — top-1 accuracy stratified by Penal
  Code chapter tag (``chapter:xvi``, ``chapter:xvii``, …).
* **Per-section confusion matrix** — when the recommender is
  wrong, what does it predict instead? Surfaces systematic
  failure modes (e.g. abetment cases scored as the underlying
  offence; the gpt-4o-mini run also exposed this).

Usage::

    python evals/case_law/score_recommend.py
    python evals/case_law/score_recommend.py --top-k 10 --json
    python evals/case_law/score_recommend.py --out evals/case_law/results-recommend.json

Output is the structural-agreement-against-courts claim that
§7.8 of the paper rests on. NOT legal advice: agreement-rate
measures Yuho-vs-prosecutor alignment, not legal correctness.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "evals"))


def _load_fixture(path: Path) -> Dict[str, Any]:
    """Load a case-law fixture (PyYAML preferred, simulator mini-YAML
    fallback so we don't add a hard dep)."""
    raw = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore
        return yaml.safe_load(raw)
    except ImportError:
        sim_dir = REPO / "simulator"
        if str(sim_dir) not in sys.path:
            sys.path.insert(0, str(sim_dir))
        from simulator import _mini_yaml  # type: ignore
        return _mini_yaml(raw)


def _canonical_section(s: Optional[str]) -> str:
    """Strip leading `s` / `S.` / 'Section' and trailing punctuation."""
    if not s:
        return ""
    raw = str(s).strip().strip(".").strip()
    import re
    raw = re.sub(r"^(?:section|sec\.?|s\.?)\s*", "", raw, flags=re.IGNORECASE)
    # The Penal Code style uses `300(c)` — peel the limb suffix to the bare
    # section number for ranking against the recommender's section ids.
    raw = re.sub(r"\(.*", "", raw)
    return raw.strip()


def _coerce_tag_list(v) -> List[str]:
    """Accept a list, an inline-list string `[a, b, c]`, or a single tag string."""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v]
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") and s.endswith("]"):
            inner = s[1:-1].strip()
            if not inner:
                return []
            return [p.strip().strip("\"' ") for p in inner.split(",") if p.strip()]
        return [s]
    return [str(v)]


def _chapter_tag(tags) -> Optional[str]:
    for t in _coerce_tag_list(tags):
        if t.startswith("chapter:"):
            return t.split(":", 1)[1]
    return None


@dataclass
class FixtureResult:
    fixture_id: str
    actual_charge: str
    predicted_top1: Optional[str]
    predicted_top5: List[str]
    rank_of_actual: Optional[int]   # 1-indexed; None if not in candidates
    chapter: Optional[str]
    notes: str = ""


@dataclass
class RecommendScoreReport:
    n: int
    top1_accuracy: float
    top3_accuracy: float
    top5_accuracy: float
    mean_reciprocal_rank: float
    per_chapter: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    confusion: Dict[str, Counter] = field(default_factory=dict)
    fixtures: List[FixtureResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "top1_accuracy": self.top1_accuracy,
            "top3_accuracy": self.top3_accuracy,
            "top5_accuracy": self.top5_accuracy,
            "mean_reciprocal_rank": self.mean_reciprocal_rank,
            "per_chapter": {
                chap: {
                    "n": stats["n"],
                    "top1_accuracy": stats["top1_accuracy"],
                    "top3_accuracy": stats["top3_accuracy"],
                    "top5_accuracy": stats["top5_accuracy"],
                }
                for chap, stats in self.per_chapter.items()
            },
            "confusion": {
                actual: dict(preds.most_common())
                for actual, preds in self.confusion.items()
            },
            "fixtures": [
                {
                    "fixture_id": fr.fixture_id,
                    "actual_charge": fr.actual_charge,
                    "predicted_top1": fr.predicted_top1,
                    "predicted_top5": fr.predicted_top5,
                    "rank_of_actual": fr.rank_of_actual,
                    "chapter": fr.chapter,
                    "notes": fr.notes,
                }
                for fr in self.fixtures
            ],
            "not_legal_advice": True,
            "disclaimer": (
                "Top-k agreement measures structural alignment between "
                "the encoded library and the section the Singapore "
                "prosecution actually brought. It is not a legal-"
                "correctness measure: prosecutors do not always charge "
                "every applicable section, and the encoded statute may "
                "diverge from a court's specific reading."
            ),
        }


def _load_fixtures(directory: Path) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for fp in sorted(directory.glob("*.yaml")):
        try:
            raw = _load_fixture(fp)
        except Exception as exc:
            print(f"warn: failed to load {fp.name}: {exc}", file=sys.stderr)
            continue
        if not isinstance(raw, dict):
            continue
        raw["__path__"] = str(fp)
        out.append(raw)
    return out


def score(
    fixtures: List[Dict[str, Any]],
    *, top_k: int = 5,
    max_candidates: int = 60,
) -> RecommendScoreReport:
    """Run the recommender against every fixture and aggregate."""
    from yuho.recommend.charge_recommender import ChargeRecommender

    rec = ChargeRecommender()
    fixture_results: List[FixtureResult] = []
    rank_reciprocals: List[float] = []
    confusion: Dict[str, Counter] = defaultdict(Counter)
    chapter_buckets: Dict[str, List[FixtureResult]] = defaultdict(list)

    for fx in fixtures:
        actual = _canonical_section(fx.get("actual_charge") or fx.get("section"))
        if not actual:
            print(f"warn: fixture {fx.get('id', fx.get('__path__'))} "
                  f"has no actual_charge; skipping", file=sys.stderr)
            continue
        # Build the recommender-input fact pattern by stripping the eval-
        # specific metadata fields. Keep the simulator-shaped fields
        # (`description`, `parties`, `acts`, `mental_states`,
        # `circumstances`, `outcomes`, `fact_facts`).
        facts = {
            k: v for k, v in fx.items()
            if k not in {"id", "case_citation", "actual_charge",
                         "alternative_charge", "court_distinguished_on",
                         "outcome", "case_summary", "tags",
                         "ground_truth", "__path__", "schema_version"}
        }
        # Ensure `section` field is set so the simulator/recommender don't
        # complain about a missing key for diagnostic-only purposes.
        facts.setdefault("section", actual)

        try:
            recommendation = rec.recommend(
                facts, top_k=top_k, max_candidates=max_candidates,
            )
        except Exception as exc:
            print(f"warn: recommender raised on {fx.get('id')}: {exc}",
                  file=sys.stderr)
            continue

        candidates = [
            _canonical_section(c.section)
            for c in recommendation.candidates
        ]
        top1 = candidates[0] if candidates else None
        top5 = candidates[:5]
        rank_of_actual = None
        for i, sec in enumerate(candidates, 1):
            if sec == actual:
                rank_of_actual = i
                break

        fr = FixtureResult(
            fixture_id=str(fx.get("id", fx.get("__path__"))),
            actual_charge=actual,
            predicted_top1=top1,
            predicted_top5=top5,
            rank_of_actual=rank_of_actual,
            chapter=_chapter_tag(fx.get("tags")),
        )
        fixture_results.append(fr)
        if fr.chapter:
            chapter_buckets[fr.chapter].append(fr)
        if top1 is not None and top1 != actual:
            confusion[actual][top1] += 1
        rank_reciprocals.append(
            1.0 / rank_of_actual if rank_of_actual else 0.0
        )

    n = len(fixture_results)
    if n == 0:
        return RecommendScoreReport(
            n=0, top1_accuracy=0, top3_accuracy=0, top5_accuracy=0,
            mean_reciprocal_rank=0,
        )

    top1 = sum(1 for fr in fixture_results
               if fr.rank_of_actual == 1) / n
    top3 = sum(1 for fr in fixture_results
               if fr.rank_of_actual is not None and fr.rank_of_actual <= 3) / n
    top5 = sum(1 for fr in fixture_results
               if fr.rank_of_actual is not None and fr.rank_of_actual <= 5) / n
    mrr = sum(rank_reciprocals) / n

    per_chapter: Dict[str, Dict[str, Any]] = {}
    for chap, frs in chapter_buckets.items():
        m = len(frs)
        per_chapter[chap] = {
            "n": m,
            "top1_accuracy":
                sum(1 for fr in frs if fr.rank_of_actual == 1) / m,
            "top3_accuracy":
                sum(1 for fr in frs
                    if fr.rank_of_actual is not None
                    and fr.rank_of_actual <= 3) / m,
            "top5_accuracy":
                sum(1 for fr in frs
                    if fr.rank_of_actual is not None
                    and fr.rank_of_actual <= 5) / m,
        }

    return RecommendScoreReport(
        n=n, top1_accuracy=top1, top3_accuracy=top3, top5_accuracy=top5,
        mean_reciprocal_rank=mrr,
        per_chapter=per_chapter, confusion=confusion,
        fixtures=fixture_results,
    )


def render_report(report: RecommendScoreReport) -> str:
    lines = [
        f"Case-law differential testing — yuho recommend vs SG courts",
        f"  n = {report.n}",
        "",
        f"  Top-1 accuracy : {report.top1_accuracy:.1%}",
        f"  Top-3 accuracy : {report.top3_accuracy:.1%}",
        f"  Top-5 accuracy : {report.top5_accuracy:.1%}",
        f"  Mean reciprocal rank : {report.mean_reciprocal_rank:.3f}",
    ]
    if report.per_chapter:
        lines.append("")
        lines.append("Per chapter:")
        lines.append(f"  {'chapter':12s} {'n':>4s} {'T1':>7s} {'T3':>7s} {'T5':>7s}")
        for chap in sorted(report.per_chapter):
            row = report.per_chapter[chap]
            lines.append(
                f"  {chap:12s} {row['n']:>4d} "
                f"{row['top1_accuracy']:>7.1%} "
                f"{row['top3_accuracy']:>7.1%} "
                f"{row['top5_accuracy']:>7.1%}"
            )
    if report.confusion:
        lines.append("")
        lines.append("Confusion matrix (actual → predicted top-1, when wrong):")
        for actual, preds in sorted(report.confusion.items()):
            for pred, count in preds.most_common(3):
                lines.append(f"  s{actual} → s{pred:6s}  ×{count}")
    lines.append("")
    lines.append("Per fixture:")
    for fr in report.fixtures:
        rank = str(fr.rank_of_actual) if fr.rank_of_actual else "—"
        mark = "✓" if fr.rank_of_actual == 1 else ("·" if fr.rank_of_actual else "✗")
        lines.append(
            f"  {mark} {fr.fixture_id:42s} actual=s{fr.actual_charge:6s} "
            f"top1=s{(fr.predicted_top1 or '?'):6s} rank={rank}"
        )
    lines.append("")
    lines.append("Not legal advice — structural agreement, not legal correctness.")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--max-candidates", type=int, default=60)
    p.add_argument("--json", dest="json_out", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    fixtures = _load_fixtures(args.fixtures)
    if not fixtures:
        print(f"error: no fixtures under {args.fixtures}", file=sys.stderr)
        return 2
    print(f"Scoring {len(fixtures)} case-law fixtures…", file=sys.stderr)
    report = score(fixtures, top_k=args.top_k, max_candidates=args.max_candidates)
    output = (
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        if args.json_out else render_report(report)
    )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output, encoding="utf-8")
        print(f"wrote: {args.out}", file=sys.stderr)
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
