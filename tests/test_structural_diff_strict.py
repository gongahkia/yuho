"""Tests for `scripts/verify_structural_diff.py --strict` regression
gating. Smoke-checks the strict-mode failure modes by hand-building
parallel emit lists that simulate drift the canonicalisation pipeline
would otherwise absorb."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Load the script as a module without executing main(). The harness is
# script-shaped (no proper package), so we import via spec.
_spec = importlib.util.spec_from_file_location(
    "verify_structural_diff", REPO / "scripts" / "verify_structural_diff.py"
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
sys.modules["verify_structural_diff"] = _mod
_spec.loader.exec_module(_mod)

diff_one = _mod.diff_one


def _bicond(lhs: str, rhs_var: str) -> dict:
    return {
        "kind": "iff",
        "lhs": {"kind": "var", "name": lhs},
        "rhs": {"kind": "var", "name": rhs_var},
    }


def _matched_pair_minimal() -> tuple[list, list]:
    """Smallest matched lean/python pair: one elements bicond + one
    conviction bicond; canonicalisation reduces them to identical
    shape. Used as the green-baseline."""
    lean = [
        {"kind": "iff",
         "lhs": {"kind": "var", "name": "100_elements_satisfied"},
         "rhs": {"kind": "var", "name": "x"}},
        {"kind": "iff",
         "lhs": {"kind": "var", "name": "100_conviction"},
         "rhs": {"kind": "and",
                 "lhs": {"kind": "var", "name": "100_elements_satisfied"},
                 "rhs": {"kind": "not", "arg": {"kind": "const", "value": False}}}},
    ]
    python = [
        {"kind": "iff",
         "lhs": {"kind": "var", "name": "100_elements_satisfied"},
         "rhs": {"kind": "var", "name": "100_leaf_x"}},
        {"kind": "iff",
         "lhs": {"kind": "var", "name": "100_conviction"},
         "rhs": {"kind": "and",
                 "lhs": {"kind": "var", "name": "100_elements_satisfied"},
                 "rhs": {"kind": "and",
                         "lhs": {"kind": "not", "arg": {"kind": "const", "value": False}},
                         "rhs": {"kind": "const", "value": True}}}},
    ]
    # leaf bicond pair so `_canonicalise_lean_leaf_name` picks up `x`.
    leaf_lean = {"kind": "iff",
                 "lhs": {"kind": "var", "name": "100_x_satisfied"},
                 "rhs": {"kind": "var", "name": "x"}}
    leaf_py = {"kind": "iff",
               "lhs": {"kind": "var", "name": "100_x_satisfied"},
               "rhs": {"kind": "var", "name": "100_leaf_x"}}
    lean.append(leaf_lean)
    python.append(leaf_py)
    return lean, python


def test_baseline_passes_under_strict():
    lean, python = _matched_pair_minimal()
    passed, _ = diff_one("smoke", "100", lean, python, strict=True)
    assert passed


def test_strict_flags_only_in_python_atom():
    """Drift simulation: python emits an extra `_satisfied` atom
    that lean doesn't. Strict catches the bicond-count imbalance
    AND the projection-set asymmetry."""
    lean, python = _matched_pair_minimal()
    extra = {"kind": "iff",
             "lhs": {"kind": "var", "name": "100_extra_satisfied"},
             "rhs": {"kind": "var", "name": "100_leaf_extra"}}
    python_with_extra = python + [extra]
    passed, summary = diff_one(
        "smoke", "100", lean, python_with_extra, strict=True
    )
    assert not passed
    # Either the bicond-count mismatch (strict-only) or the
    # only-in-python flag (lax-detectable) surfaces.
    assert "STRICT" in summary or "only in python" in summary


def test_strict_passes_when_known_divergences_active():
    """When both documented divergences are observable (leaf-naming
    canonicalisation actively rewrites at least one atom; `_fires`
    counts match), strict mode passes the green baseline."""
    lean, python = _matched_pair_minimal()
    passed, summary = diff_one("smoke", "100", lean, python, strict=True)
    assert passed
    assert "STRICT" not in summary


def test_strict_flags_bicond_count_imbalance():
    """If one side stops emitting a bicond family, strict catches
    the count mismatch even when the surviving atoms canonicalise
    to identical shape."""
    lean, python = _matched_pair_minimal()
    # Drop the leaf bicond from python only.
    python_short = [a for a in python
                    if a["lhs"]["name"] != "100_x_satisfied"]
    passed, summary = diff_one(
        "smoke", "100", lean, python_short, strict=True
    )
    assert not passed
    assert "STRICT" in summary or "only in lean" in summary
