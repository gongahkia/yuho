"""Report mechanisation feature coverage and claim boundaries."""

from __future__ import annotations


FEATURE_COVERAGE = (
    ("simple_elements", "s299 smoke fixture", "covered"),
    ("nested_all_of_any_of", "s300/s415 smoke fixtures", "covered"),
    ("exceptions", "s300/s378 smoke fixtures + Lean exception lemmas", "covered"),
    ("cross_section_apply_scope", "Yuho/CrossDeep.lean v9 theorems", "covered"),
    ("penalties", "Yuho/Penalty.lean lemmas", "covered"),
    ("case_law_doctrine", "mechanisation claim boundary", "out-of-scope"),
    ("rich_evidential_facts", "mechanisation claim boundary", "out-of-scope"),
)


def build_report() -> str:
    lines = ["=== mechanisation feature coverage ==="]
    for feature, evidence, status in FEATURE_COVERAGE:
        lines.append(f"- {feature}: {status} ({evidence})")
    lines.append(
        "Mechanisation coverage: "
        + "; ".join(f"{feature}={status}" for feature, _, status in FEATURE_COVERAGE)
    )
    return "\n".join(lines)


def main() -> int:
    print(build_report())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
