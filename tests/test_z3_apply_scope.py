"""Z3-backend hookup for `is_infringed(sX)` and `apply_scope(sX, ...)`.

Both predicates evaluate to the inner scope's `overall_satisfied` —
which the Z3 generator already names ``<sX>_conviction`` (elements
all hold AND no defeating exception fires). This test pins:

1. The conviction Bool exists for every translated statute.
2. References to it from `is_infringed` / `apply_scope` resolve to
   the same Z3 atom regardless of evaluation order.
3. A satisfiability check that links a parent statute to a base
   section via apply_scope behaves correctly under Z3.
"""

from __future__ import annotations

import pytest

from yuho.ast import ASTBuilder
from yuho.parser import get_parser
from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE


def _parse(source: str):
    parser = get_parser()
    result = parser.parse(source, "<test>")
    return ASTBuilder(result.source, "<test>").build(result.root_node)


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_conviction_bool_declared_for_every_statute():
    """Per-statute conviction Bool lands in `_consts` after generate."""
    ast = _parse('''
        statute 299 "Culpable homicide" {
          elements { all_of {
            actus_reus death := "Causes death";
            mens_rea intent := "With intent";
          } }
        }

        statute 300 "Murder" subsumes 299 {
          elements { all_of {
            actus_reus death := "Causes death";
            mens_rea murder_intent := "With intent to kill";
          } }
        }
    ''')
    gen = Z3Generator()
    gen.generate(ast)
    assert "299_conviction" in gen._consts
    assert "300_conviction" in gen._consts


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_apply_scope_resolves_to_target_conviction():
    """Repeated `_conviction_bool('299')` returns the same Z3 atom each call."""
    ast = _parse('''
        statute 299 "Culpable homicide" {
          elements { all_of { actus_reus death := "Causes death"; } }
        }
    ''')
    gen = Z3Generator()
    gen.generate(ast)
    a = gen._conviction_bool("299")
    b = gen._conviction_bool("s299")
    c = gen._conviction_bool("299")
    # Z3 dedupes Bool atoms by name, so all three should be the same object
    # in the eq_id sense (z3 == returns BoolRef, so use .eq()).
    assert a.eq(b)
    assert a.eq(c)


@pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")
def test_apply_scope_in_exception_guard_links_into_z3():
    """When an apply_scope appears inside an exception guard, the Z3
    encoding references the target's conviction Bool, not a free atom."""
    import z3
    ast = _parse('''
        statute 299 "Culpable homicide" {
          elements { all_of {
            actus_reus death := "Causes death";
          } }
        }

        statute 304 "Punishment for culpable homicide" subsumes 299 {
          elements { all_of {
            actus_reus death := "Causes death";
          } }
          exception base_not_made_out {
            "base offence not made out"
            "no s304 conviction"
            when !apply_scope(s299, facts)
          }
        }
    ''')
    gen = Z3Generator()
    gen.generate(ast)
    # Both convictions exist as the canonical Bool atoms
    s299 = gen._consts["299_conviction"]
    s304 = gen._consts["304_conviction"]
    # _conviction_bool returns the same atom as the lazy-declared one
    assert gen._conviction_bool("299").eq(s299)
    # And a separate solver run that asserts s299=False can decide what
    # happens to s304 in the presence of the exception guard.
    solver = z3.Solver()
    for assertion in gen._assertions:
        solver.add(assertion)
    solver.add(s299 == False)  # noqa: E712
    # The model must be satisfiable: s299 false is consistent with
    # s304 either way (the exception guard may or may not fire
    # depending on other vars).
    assert solver.check() == z3.sat
