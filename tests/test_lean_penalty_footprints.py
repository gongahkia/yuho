from __future__ import annotations

import pytest

from scripts.verify_lean_penalty_footprints import compare_penalty_footprints
from yuho.verify.z3_solver import Z3_AVAILABLE


pytestmark = pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")


def test_lean_penalty_footprint_rows_match_z3_constraints() -> None:
    rows = [
        {
            "name": "imprisonment_admits",
            "footprint": {
                "imp_lo": 1,
                "imp_hi": 5,
                "fine_lo": 0,
                "fine_hi": 0,
                "fine_unlimited": False,
                "caning_lo": 0,
                "caning_hi": 0,
                "caning_unspecified": False,
                "death": False,
            },
            "expected": True,
        },
        {
            "name": "imprisonment_rejects_hi",
            "footprint": {
                "imp_lo": 1,
                "imp_hi": 6,
                "fine_lo": 0,
                "fine_hi": 0,
                "fine_unlimited": False,
                "caning_lo": 0,
                "caning_hi": 0,
                "caning_unspecified": False,
                "death": False,
            },
            "expected": False,
        },
        {
            "name": "cumulative_admits",
            "footprint": {
                "imp_lo": 1,
                "imp_hi": 5,
                "fine_lo": 1000,
                "fine_hi": 2000,
                "fine_unlimited": False,
                "caning_lo": 3,
                "caning_hi": 6,
                "caning_unspecified": False,
                "death": True,
            },
            "expected": True,
        },
    ]

    checked, mismatches = compare_penalty_footprints(rows)

    assert checked == 3
    assert mismatches == []
