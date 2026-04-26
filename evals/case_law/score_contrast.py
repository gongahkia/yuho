"""Score `yuho contrast` against curated Singapore case-law fixtures.

For every fixture under ``evals/case_law/fixtures/`` that carries
both an ``actual_charge`` and an ``alternative_charge`` (the
section the court considered as an alternative — e.g. s299
culpable homicide considered as alternative to s302 murder),
this driver:

1. Runs ``yuho contrast(actual_charge, alternative_charge)``.
2. Extracts the *distinguishing-elements* set the contrast tool
   surfaces (elements true under the actual charge that are
   false under the alternative).
3. Scores that set against ``court_distinguished_on`` — the
   element-level reasons the court itself gave for choosing
   actual over alternative.

Headline metric: **F1 over the distinguishing-elements set**,
averaged across fixtures, plus per-fixture Jaccard for
inspection. The aggregate measures structural alignment between
Yuho's Z3-derived contrast and judicial reasoning at the element
level — the formal-methods analogue of the prosecutor-alignment
claim that ``score_recommend.py`` ships.

NOT legal advice. The score measures Yuho's structural model
versus the court's structural reasoning, not legal correctness
of either side. Where Yuho's encoded element decomposition
differs from a court's framing, the disagreement is informative
about Yuho's encoding, not about the court.

Usage::

    python evals/case_law/score_contrast.py
    python evals/case_law/score_contrast.py --json
    python evals/case_law/score_contrast.py --out evals/case_law/results-contrast.json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(REPO / "src"))


def _load_fixture(path: Path) -> Dict[str, Any]:
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


def _coerce_list(v: Any) -> List[str]:
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


def _f1(predicted: Set[str], expected: Set[str]) -> Tuple[float, float, float]:
    if not predicted and not expected:
        return 1.0, 1.0, 1.0
    if not predicted or not expected:
        return 0.0, 0.0, 0.0
    tp = len(predicted & expected)
    p = tp / len(predicted)
    r = tp / len(expected)
    f1 = (2 * p * r / (p + r)) if (p + r) else 0.0
    return f1, p, r


def _jaccard(a: Set[str], b: Set[str]) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


@dataclass
class FixtureContrastResult:
    fixture_id: str
    actual_charge: str
    alternative_charge: str
    yuho_distinguishing: List[str]
    court_distinguishing: List[str]
    f1: float
    precision: float
    recall: float
    jaccard: float
    contrast_status: str  # "ok" / "no-contrast" / "error: ..."
    notes: str = ""


@dataclass
class ContrastScoreReport:
    n: int
    n_with_alternative: int
    n_contrast_sat: int
    mean_f1: float
    mean_jaccard: float
    fixtures: List[FixtureContrastResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "n_with_alternative": self.n_with_alternative,
            "n_contrast_sat": self.n_contrast_sat,
            "mean_f1": self.mean_f1,
            "mean_jaccard": self.mean_jaccard,
            "fixtures": [
                {
                    "fixture_id": fr.fixture_id,
                    "actual_charge": fr.actual_charge,
                    "alternative_charge": fr.alternative_charge,
                    "yuho_distinguishing": fr.yuho_distinguishing,
                    "court_distinguishing": fr.court_distinguishing,
                    "f1": fr.f1,
                    "precision": fr.precision,
                    "recall": fr.recall,
                    "jaccard": fr.jaccard,
                    "contrast_status": fr.contrast_status,
                    "notes": fr.notes,
                }
                for fr in self.fixtures
            ],
            "not_legal_advice": True,
            "disclaimer": (
                "F1 measures alignment between Yuho's Z3-derived "
                "structural contrast and the court's stated "
                "element-level reasoning. Disagreement is "
                "informative about the encoded model, not about "
                "the court's correctness."
            ),
        }


def _run_contrast(
    section_a: str, section_b: str, library: Path,
) -> Tuple[str, Optional[List[str]]]:
    """Run the contrast core directly (not via the CLI's sys.exit
    path) and return (status, distinguishing_elements_or_none)."""
    try:
        import z3  # noqa: F401
    except ImportError:
        return "error: z3 not installed", None

    from yuho.cli.commands.contrast import (
        _build_combined_module, _read_model_facts, _statute_yh_for,
    )
    from yuho.verify.z3_solver import Z3Generator

    a_path = _statute_yh_for(library, section_a)
    b_path = _statute_yh_for(library, section_b)
    if a_path is None or b_path is None:
        return f"error: could not locate s{section_a} or s{section_b}", None

    try:
        module = _build_combined_module([a_path, b_path])
    except Exception as exc:
        return f"error: build_combined_module: {exc}", None

    gen = Z3Generator()
    gen.generate(module)

    a_id = section_a.lstrip("sS").replace(".", "_")
    b_id = section_b.lstrip("sS").replace(".", "_")
    a_conv = gen._consts.get(f"{a_id}_conviction")
    b_conv = gen._consts.get(f"{b_id}_conviction")
    if a_conv is None or b_conv is None:
        return "error: missing conviction Bool (no elements?)", None

    import z3
    solver = z3.Solver()
    solver.set("timeout", 30000)
    for assertion in gen._assertions:
        solver.add(assertion)
    solver.add(a_conv)
    solver.add(z3.Not(b_conv))
    result = solver.check()
    if result != z3.sat:
        return "no-contrast", None

    model = solver.model()
    a_facts = _read_model_facts(model, gen._consts, a_id)
    b_facts = _read_model_facts(model, gen._consts, b_id)
    distinguishing = sorted(
        n for n, v_a in a_facts.items()
        if v_a and not b_facts.get(n, False) and n in b_facts
    )
    # When the actual charge has elements not present in the alternative
    # at all (different vocabulary), surface those too — they're also
    # structural distinguishers from the court's perspective.
    only_in_a = sorted(
        n for n, v in a_facts.items()
        if v and n not in b_facts
    )
    return "ok", sorted(set(distinguishing + only_in_a))


def score(
    fixtures: List[Dict[str, Any]],
    *, library: Optional[Path] = None,
) -> ContrastScoreReport:
    library = library or (REPO / "library" / "penal_code")
    fixture_results: List[FixtureContrastResult] = []
    n_with_alternative = 0
    n_contrast_sat = 0
    f1_scores: List[float] = []
    jaccard_scores: List[float] = []

    for fx in fixtures:
        actual = str(fx.get("actual_charge") or fx.get("section") or "")
        alternative = str(fx.get("alternative_charge") or "")
        if not alternative:
            continue
        n_with_alternative += 1
        court_distinguishing = _coerce_list(fx.get("court_distinguished_on"))

        # Strip limb suffix (e.g. "300(c)" → "300") for the contrast call.
        import re
        actual_bare = re.sub(r"\(.*", "", actual).strip()
        alternative_bare = re.sub(r"\(.*", "", alternative).strip()

        status, distinguishing = _run_contrast(
            actual_bare, alternative_bare, library,
        )
        if status == "ok":
            n_contrast_sat += 1
            yuho_set: Set[str] = set(distinguishing or [])
            court_set: Set[str] = set(court_distinguishing)
            f1, p, r = _f1(yuho_set, court_set)
            jacc = _jaccard(yuho_set, court_set)
            f1_scores.append(f1)
            jaccard_scores.append(jacc)
            fr = FixtureContrastResult(
                fixture_id=str(fx.get("id", fx.get("__path__"))),
                actual_charge=actual,
                alternative_charge=alternative,
                yuho_distinguishing=sorted(yuho_set),
                court_distinguishing=sorted(court_set),
                f1=f1, precision=p, recall=r, jaccard=jacc,
                contrast_status="ok",
            )
        else:
            fr = FixtureContrastResult(
                fixture_id=str(fx.get("id", fx.get("__path__"))),
                actual_charge=actual,
                alternative_charge=alternative,
                yuho_distinguishing=[],
                court_distinguishing=sorted(court_distinguishing),
                f1=0.0, precision=0.0, recall=0.0, jaccard=0.0,
                contrast_status=status,
            )
        fixture_results.append(fr)

    n = len(fixture_results)
    return ContrastScoreReport(
        n=n,
        n_with_alternative=n_with_alternative,
        n_contrast_sat=n_contrast_sat,
        mean_f1=(sum(f1_scores) / len(f1_scores)) if f1_scores else 0.0,
        mean_jaccard=(sum(jaccard_scores) / len(jaccard_scores)) if jaccard_scores else 0.0,
        fixtures=fixture_results,
    )


def render_report(report: ContrastScoreReport) -> str:
    lines = [
        f"Case-law differential testing — yuho contrast vs court reasoning",
        f"  n with alternative_charge field : {report.n_with_alternative}",
        f"  n where Z3 found a contrast model: {report.n_contrast_sat}",
        "",
        f"  Mean F1  (yuho vs court element sets) : {report.mean_f1:.3f}",
        f"  Mean Jaccard                          : {report.mean_jaccard:.3f}",
        "",
        "Per fixture:",
    ]
    for fr in report.fixtures:
        if fr.contrast_status != "ok":
            lines.append(
                f"  ✗ {fr.fixture_id:42s} {fr.contrast_status}"
            )
            continue
        lines.append(
            f"    {fr.fixture_id:42s} F1={fr.f1:.2f} J={fr.jaccard:.2f}"
        )
        lines.append(
            f"      yuho  : {', '.join(fr.yuho_distinguishing) or '(empty)'}"
        )
        lines.append(
            f"      court : {', '.join(fr.court_distinguishing) or '(empty)'}"
        )
    lines.append("")
    lines.append("Not legal advice — structural alignment, not legal correctness.")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    p.add_argument("--library", type=Path, default=None)
    p.add_argument("--json", dest="json_out", action="store_true")
    p.add_argument("--out", type=Path, default=None)
    args = p.parse_args()

    fixtures = _load_fixtures(args.fixtures)
    print(f"Scoring {len(fixtures)} case-law fixtures (contrast)…", file=sys.stderr)
    report = score(fixtures, library=args.library)
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
