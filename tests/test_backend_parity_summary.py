"""Backend parity summary contract."""

from __future__ import annotations

from scripts.verify_backend_parity import build_summary


def test_backend_parity_summary_lists_evidence_and_boundaries() -> None:
    summary = build_summary()

    assert "runtime-z3: scripts/verify_runtime_tests.py" in summary
    assert "penalty-verdicts: scripts/verify_penalty_verdicts.py" in summary
    assert "z3-lean: scripts/verify_structural_diff.py" in summary
    assert "lean-verdicts: scripts/verify_lean_expected_verdicts.py" in summary
    assert "lean-penalty-footprints: scripts/verify_lean_penalty_footprints.py" in summary
    assert "alloy=explicit-unsupported" in summary
    assert "Feature coverage:" in summary
    assert "nested_all_of_any_of: runtime-z3=covered" in summary
    assert "is_infringed_apply_scope: runtime-z3=covered" in summary
    assert "penalties_money_duration: runtime-z3=imprisonment/fine/caning/death-model-verdict" in summary
    assert "z3-lean=penalty-footprint-bridge" in summary
    assert "lean_expected_verdicts: runtime-z3-lean=smoke+full-corpus-mixed+bounded-arity-verdicts" in summary
    assert "optional_values: runtime-z3=covered" in summary
    assert "case_law_doctrine: runtime=active-effects/positive-treatment-adoption/ordered-positive-adoption/ordered-cumulative/negative-treatment-nonadoption/fact-key/same-kind-nonconflict/own-effect/missing-target/effectless-target/target-remap/payload-preserve/metadata-override/target-metadata-fallback/cycle-cutoff/inactive-authority/jurisdiction-burden-shift-precedence-partial; z3=unsupported; lean=typed-fact-burden+surface-alias+surface-precedence-rank+fact-key+same-kind-nonconflict+cumulative-effect+ordered-cumulative+negative-treatment-nonadoption+own-effect+ordered-positive-adoption+missing-target+effectless-target+target-remap+payload-preserve+adoption-cycle+effect-adoption-metadata+metadata-override+target-metadata-fallback+inactive-authority-jurisdiction-burden-precedence-rank-conflict-partial" in summary
    assert "typed_fact_burdens: runtime=element+case-law metadata guards" in summary
    assert "Unsupported feature boundaries:" in summary
    assert "precise calendar-duration verifier parity" in summary
