"""Report mechanisation feature coverage and claim boundaries."""

from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yuho.ast import nodes
from yuho.services.analysis import analyze_file


FEATURE_COVERAGE = (
    ("simple_elements", "s299 smoke fixture", "covered"),
    ("nested_all_of_any_of", "s300/s415 smoke fixtures", "covered"),
    ("exceptions", "s300/s378 smoke fixtures + Lean exception lemmas", "covered"),
    ("cross_section_apply_scope", "Yuho/CrossDeep.lean v9 theorems", "covered"),
    ("penalties", "Yuho/Penalty.lean lemmas", "covered"),
    ("case_law_doctrine", "Yuho/CaseLaw.lean surface-alias + surface-precedence-rank + fact-key + same-kind-nonconflict + effect + cumulative-effect + ordered-cumulative + negative-treatment-nonadoption + own-effect + missing-target + target-remap + payload-preserve + transitive/cyclic adoption + metadata + inactive-authority + jurisdiction-burden-metadata + precedence-rank/conflict lemmas", "partial"),
    ("typed_fact_burdens", "Yuho/Facts.lean + Yuho/Eval.lean burden/proof-standard guard lemmas", "partial"),
    ("rich_evidential_facts", "metadata provenance beyond typed burden guards", "out-of-scope"),
)

CORPUS_STRATA = (
    "simple_flat_elements",
    "nested_all_of_any_of",
    "exception_heavy",
    "cross_ref_heavy",
    "penalty_heavy",
)


def build_report(library: Path | None = None) -> str:
    lines = ["=== mechanisation feature coverage ==="]
    for feature, evidence, status in FEATURE_COVERAGE:
        lines.append(f"- {feature}: {status} ({evidence})")
    lines.append("")
    lines.append("Full-corpus Lean fixture source:")
    lines.append(
        "- mechanisation/scripts/generate_fixtures.py -> "
        "mechanisation/scripts/Fixtures.lean::representativeFixtures"
    )
    lines.append("")
    lines.append("Corpus strata representatives:")
    representatives = corpus_strata_representatives(
        library or REPO / "library" / "penal_code"
    )
    for stratum in CORPUS_STRATA:
        item = representatives.get(stratum)
        if item is None:
            lines.append(f"- {stratum}: missing")
            continue
        section, path = item
        lines.append(f"- {stratum}: s{section} ({path})")
    lines.append(
        "Mechanisation coverage: "
        + "; ".join(f"{feature}={status}" for feature, _, status in FEATURE_COVERAGE)
    )
    lines.append(
        "Mechanisation corpus strata: "
        + "; ".join(
            f"{stratum}={'covered' if stratum in representatives else 'missing'}"
            for stratum in CORPUS_STRATA
        )
    )
    return "\n".join(lines)


def corpus_strata_representatives(
    library: Path,
) -> dict[str, tuple[str, str]]:
    if not library.is_dir():
        return {}
    found: dict[str, tuple[str, str]] = {}
    for path in sorted(library.glob("*/statute.yh")):
        analysis = analyze_file(path, run_semantic=False)
        if analysis.errors or analysis.ast is None or not analysis.ast.statutes:
            continue
        statute = analysis.ast.statutes[0]
        rel = path.relative_to(REPO).as_posix() if path.is_relative_to(REPO) else str(path)
        for stratum in _matching_strata(statute):
            found.setdefault(stratum, (statute.section_number, rel))
        if len(found) == len(CORPUS_STRATA):
            break
    return found


def _matching_strata(statute: nodes.StatuteNode) -> set[str]:
    result: set[str] = set()
    if statute.elements and not any(
        isinstance(member, nodes.ElementGroupNode) for member in statute.elements
    ):
        result.add("simple_flat_elements")
    if _has_nested_group(statute.elements):
        result.add("nested_all_of_any_of")
    if len(statute.exceptions) >= 2 or any(
        exc.priority is not None or exc.defeats for exc in statute.exceptions
    ):
        result.add("exception_heavy")
    if any(
        isinstance(item, (nodes.ApplyScopeNode, nodes.IsInfringedNode))
        for item in _walk(statute)
    ):
        result.add("cross_ref_heavy")
    if statute.penalty is not None or statute.additional_penalties:
        result.add("penalty_heavy")
    return result


def _has_nested_group(items) -> bool:
    def walk_group(item, depth: int) -> bool:
        if not isinstance(item, nodes.ElementGroupNode):
            return False
        if depth > 0:
            return True
        return any(walk_group(member, depth + 1) for member in item.members)

    return any(walk_group(item, 0) for item in items)


def _walk(root: nodes.ASTNode):
    yield root
    for child in root.children():
        if child is not None:
            yield from _walk(child)


def main() -> int:
    print(build_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
