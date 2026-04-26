"""Constrained contrast scoring — does the court's stated distinguisher
remain *satisfiable* in the Z3 model?

The unconstrained contrast scorer (``score_contrast.py``) asks Z3 to
find *some* fact pattern where ``s_A_conviction`` holds and
``s_B_conviction`` fails, then compares the picked element against
the court's reasoning. Z3 has no preference among valid
distinguishers, so the F1 against court reasoning is structurally
weak when multiple disjunctive elements distinguish the two
sections.

This **constrained** scorer asks the better question: *given the
court's stated distinguishing element, can Z3 still satisfy the
contrast?* That is, we add the court's element as a hard
constraint and check whether
``s_A_conviction AND NOT s_B_conviction AND court_element = true``
is satisfiable. If sat, the court's reasoning is **consistent with
Yuho's encoded model**; if unsat, the encoding rejects the court's
reading (a falsification signal worth flagging).

Headline metric: **% of fixtures where the court's reasoning is
satisfiable in the encoded model** — a soundness-style claim about
the encoding's expressive scope.

Usage::

    python evals/case_law/score_contrast_constrained.py
    python evals/case_law/score_contrast_constrained.py --json
    python evals/case_law/score_contrast_constrained.py --out evals/case_law/results-constrained.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

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


@dataclass
class ConstraintResult:
    fixture_id: str
    actual_charge: str
    alternative_charge: str
    court_distinguishing: List[str]
    status: str        # "consistent" / "unsat" / "no-element-in-encoding" / "error: ..."
    missing_in_encoding: List[str] = field(default_factory=list)


@dataclass
class ConstrainedReport:
    n: int
    n_consistent: int
    n_unsat: int
    n_no_encoding: int
    n_error: int
    results: List[ConstraintResult] = field(default_factory=list)

    @property
    def consistency_rate(self) -> float:
        denom = self.n - self.n_no_encoding
        return self.n_consistent / denom if denom else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "n": self.n,
            "n_consistent": self.n_consistent,
            "n_unsat": self.n_unsat,
            "n_no_encoding": self.n_no_encoding,
            "n_error": self.n_error,
            "consistency_rate": self.consistency_rate,
            "results": [
                {
                    "fixture_id": rr.fixture_id,
                    "actual_charge": rr.actual_charge,
                    "alternative_charge": rr.alternative_charge,
                    "court_distinguishing": rr.court_distinguishing,
                    "status": rr.status,
                    "missing_in_encoding": rr.missing_in_encoding,
                }
                for rr in self.results
            ],
            "not_legal_advice": True,
            "disclaimer": (
                "Consistency-rate measures whether the court's stated "
                "element-level reasoning has a satisfying assignment in "
                "Yuho's encoded model. A low rate flags either an "
                "encoding gap (missing element) or genuine model-vs-"
                "court divergence; high rate is evidence the encoding "
                "is expressively complete enough to host the court's "
                "reasoning."
            ),
        }


def _check_consistency(
    actual: str, alternative: str, court_elements: List[str], library: Path,
) -> ConstraintResult:
    """For each court-stated distinguishing element, check whether
    asserting it true alongside the contrast constraint is
    satisfiable in the Z3 model."""
    try:
        import z3
    except ImportError:
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status="error: z3 not installed",
        )

    from yuho.cli.commands.contrast import (
        _build_combined_module, _statute_yh_for,
    )
    from yuho.verify.z3_solver import Z3Generator

    a_path = _statute_yh_for(library, actual)
    b_path = _statute_yh_for(library, alternative)
    if a_path is None or b_path is None:
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status=f"error: could not locate s{actual} or s{alternative}",
        )

    try:
        module = _build_combined_module([a_path, b_path])
    except Exception as exc:  # noqa: BLE001
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status=f"error: {exc}",
        )

    gen = Z3Generator()
    gen.generate(module)

    a_id = actual.lstrip("sS").replace(".", "_")
    b_id = alternative.lstrip("sS").replace(".", "_")
    a_conv = gen._consts.get(f"{a_id}_conviction")
    b_conv = gen._consts.get(f"{b_id}_conviction")
    if a_conv is None or b_conv is None:
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status="error: missing conviction Bool (no elements)",
        )

    # For each court element, the encoded Bool name follows
    # `<section_id>_<element>_satisfied`.
    missing: List[str] = []
    constraint_bools = []
    for elem in court_elements:
        # Try the actual section first (most natural reading).
        for sec_id in (a_id, b_id):
            name = f"{sec_id}_{elem}_satisfied"
            if name in gen._consts:
                constraint_bools.append(gen._consts[name])
                break
        else:
            missing.append(elem)

    if missing and not constraint_bools:
        # Court reasoning names elements not present in either section's
        # encoded vocabulary — encoding gap, not a falsification.
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status="no-element-in-encoding",
            missing_in_encoding=missing,
        )

    solver = z3.Solver()
    solver.set("timeout", 30000)
    for assertion in gen._assertions:
        solver.add(assertion)
    solver.add(a_conv)
    solver.add(z3.Not(b_conv))
    for b in constraint_bools:
        solver.add(b)

    result = solver.check()
    if result == z3.sat:
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status="consistent",
            missing_in_encoding=missing,
        )
    if result == z3.unsat:
        return ConstraintResult(
            fixture_id="", actual_charge=actual, alternative_charge=alternative,
            court_distinguishing=court_elements,
            status="unsat",
            missing_in_encoding=missing,
        )
    return ConstraintResult(
        fixture_id="", actual_charge=actual, alternative_charge=alternative,
        court_distinguishing=court_elements,
        status=f"error: z3 returned {result}",
        missing_in_encoding=missing,
    )


def score(
    fixtures: List[Dict[str, Any]], *, library: Optional[Path] = None,
) -> ConstrainedReport:
    library = library or (REPO / "library" / "penal_code")
    results: List[ConstraintResult] = []
    n_consistent = n_unsat = n_no_encoding = n_error = 0
    for fx in fixtures:
        actual = str(fx.get("actual_charge") or "")
        alternative = str(fx.get("alternative_charge") or "")
        if not actual or not alternative:
            continue
        court_elements = _coerce_list(fx.get("court_distinguished_on"))
        if not court_elements:
            continue
        actual_bare = re.sub(r"\(.*", "", actual).strip()
        alternative_bare = re.sub(r"\(.*", "", alternative).strip()
        rr = _check_consistency(
            actual_bare, alternative_bare, court_elements, library,
        )
        rr.fixture_id = str(fx.get("id", fx.get("__path__")))
        results.append(rr)
        if rr.status == "consistent":
            n_consistent += 1
        elif rr.status == "unsat":
            n_unsat += 1
        elif rr.status == "no-element-in-encoding":
            n_no_encoding += 1
        else:
            n_error += 1

    return ConstrainedReport(
        n=len(results),
        n_consistent=n_consistent,
        n_unsat=n_unsat,
        n_no_encoding=n_no_encoding,
        n_error=n_error,
        results=results,
    )


def render_report(report: ConstrainedReport) -> str:
    lines = [
        f"Constrained-contrast scoring — court reasoning vs Z3 model",
        f"  n = {report.n}",
        "",
        f"  consistent             : {report.n_consistent}",
        f"  unsat (model rejects)  : {report.n_unsat}",
        f"  no-element-in-encoding : {report.n_no_encoding}",
        f"  errors                 : {report.n_error}",
        "",
        f"  consistency-rate (excl. encoding-gap): "
        f"{report.consistency_rate:.1%}",
        "",
        "Per fixture:",
    ]
    for rr in report.results:
        marker = {
            "consistent": "✓", "unsat": "✗",
            "no-element-in-encoding": "·",
        }.get(rr.status, "!")
        lines.append(
            f"  {marker} {rr.fixture_id:42s} {rr.status:25s} "
            f"court={rr.court_distinguishing}"
        )
        if rr.missing_in_encoding:
            lines.append(
                f"      missing-in-encoding: {rr.missing_in_encoding}"
            )
    lines.append("")
    lines.append("Not legal advice — soundness-of-encoding measure only.")
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
