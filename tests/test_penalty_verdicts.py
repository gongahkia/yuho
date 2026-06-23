from __future__ import annotations

import pytest

from scripts.verify_penalty_verdicts import run_penalty_verdict_checks
from yuho.verify.z3_solver import Z3_AVAILABLE


pytestmark = pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")


def test_penalty_verdict_fixtures_match_runtime_and_z3_model() -> None:
    summary = run_penalty_verdict_checks()

    assert summary is not None
    assert summary.checked == 3
    assert summary.conviction_matches == 3
    assert summary.penalty_bound_checks == 12
    assert summary.mismatches == ()
    assert summary.errors == ()
