"""Regression tests for F* transpiler semantics."""

from __future__ import annotations

from pathlib import Path

from yuho.services.analysis import analyze_file
from yuho.transpile.fstar_transpiler import FStarTranspiler


STATUTE_PATH = (
    Path(__file__).resolve().parents[1]
    / "library"
    / "penal_code"
    / "s300_murder"
    / "statute.yh"
)


def test_fstar_preserves_any_of_groups_and_exception_guards() -> None:
    """F* output should preserve disjunctive limbs and guarded exceptions."""
    analysis = analyze_file(STATUTE_PATH)
    assert analysis.ast is not None

    output = FStarTranspiler().transpile(analysis.ast)

    assert (
        "facts.causeDeath && (facts.intent1 || facts.intent2 || facts.intent3 || facts.intent4)"
        in output
    )
    assert "exception: string; (* exception guard input *)" in output
    assert 'facts.exception == "provocation"' in output
    assert "placeholder: encode exception condition" not in output
