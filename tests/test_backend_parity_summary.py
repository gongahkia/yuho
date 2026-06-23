"""Backend parity summary contract."""

from __future__ import annotations

from scripts.verify_backend_parity import build_summary


def test_backend_parity_summary_lists_evidence_and_boundaries() -> None:
    summary = build_summary()

    assert "runtime-z3: scripts/verify_runtime_tests.py" in summary
    assert "z3-lean: scripts/verify_structural_diff.py" in summary
    assert "alloy=explicit-unsupported" in summary
    assert "Unsupported feature boundaries:" in summary
