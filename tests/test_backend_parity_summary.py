"""Backend parity summary contract."""

from __future__ import annotations

from scripts.verify_backend_parity import build_summary


def test_backend_parity_summary_lists_evidence_and_boundaries() -> None:
    summary = build_summary()

    assert "runtime-z3: scripts/verify_runtime_tests.py" in summary
    assert "z3-lean: scripts/verify_structural_diff.py" in summary
    assert "alloy=explicit-unsupported" in summary
    assert "Feature coverage:" in summary
    assert "nested_all_of_any_of: runtime-z3=covered" in summary
    assert "case_law_doctrine: runtime-z3=unsupported" in summary
    assert "Unsupported feature boundaries:" in summary
    assert "precise calendar-duration verifier parity" in summary
