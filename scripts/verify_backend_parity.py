"""Summarize backend parity coverage and unsupported feature boundaries."""

from __future__ import annotations

from pathlib import Path
import sys

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from yuho.cli.commands.verify import BACKEND_METADATA


PARITY_LINKS = (
    ("runtime-z3", "scripts/verify_runtime_tests.py"),
    ("penalty-verdicts", "scripts/verify_penalty_verdicts.py"),
    ("z3-lean", "scripts/verify_structural_diff.py"),
    ("lean-verdicts", "scripts/verify_lean_expected_verdicts.py"),
    ("lean-penalty-footprints", "scripts/verify_lean_penalty_footprints.py"),
    ("alloy", "explicit unsupported-feature failures"),
)

FEATURE_COVERAGE = (
    (
        "flat_elements",
        "runtime-z3=covered; z3-lean=smoke; alloy=basic",
    ),
    (
        "nested_all_of_any_of",
        "runtime-z3=covered; z3-lean=smoke; alloy=unsupported-boundary",
    ),
    (
        "exceptions_defeats",
        "runtime-z3=covered; z3-lean=smoke; alloy=unsupported-boundary",
    ),
    (
        "is_infringed_apply_scope",
        "runtime-z3=covered; z3-lean=structural-link; alloy=unsupported-boundary",
    ),
    (
        "penalties_money_duration",
        "runtime-z3=imprisonment/fine/caning/death-model-verdict; z3-lean=penalty-footprint-bridge; alloy=unsupported-boundary",
    ),
    (
        "lean_expected_verdicts",
        "runtime-z3-lean=smoke+full-corpus-mixed+bounded-arity-verdicts; z3-lean=structural; alloy=unsupported-boundary",
    ),
    (
        "optional_values",
        "runtime-z3=covered; z3-lean=unsupported-boundary; alloy=unsupported-boundary",
    ),
    (
        "case_law_doctrine",
        "runtime=active-effects/positive-treatment-adoption/burden-shift-precedence-partial; z3=unsupported; lean=effect-adoption-inactivation-burden-precedence-bucket-partial; alloy=unsupported",
    ),
)


def build_summary() -> str:
    lines = ["=== backend parity ==="]
    for name, evidence in PARITY_LINKS:
        lines.append(f"{name}: {evidence}")
    lines.append("")
    lines.append("Feature coverage:")
    for feature, status in FEATURE_COVERAGE:
        lines.append(f"- {feature}: {status}")
    lines.append("")
    lines.append("Unsupported feature boundaries:")
    for backend in ("alloy", "z3", "lean", "combined"):
        metadata = BACKEND_METADATA[backend]
        unsupported = ", ".join(metadata["unsupported_features"])
        lines.append(f"- {backend} ({metadata['status']}): {unsupported}")
    lines.append(
        "Backend parity: runtime-z3=runtime-tests; penalty-verdicts=z3-model; "
        "z3-lean=structural-diff; "
        "lean-verdicts=expected-verdicts; lean-penalty-footprints=z3-footprint; "
        "alloy=explicit-unsupported"
    )
    return "\n".join(lines)


def main() -> int:
    print(build_summary())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
