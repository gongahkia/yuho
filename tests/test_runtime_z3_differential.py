from __future__ import annotations

import pytest

from scripts import verify_runtime_tests
from yuho.verify.z3_solver import Z3_AVAILABLE


pytestmark = pytest.mark.skipif(not Z3_AVAILABLE, reason="z3-solver not installed")


def test_runtime_z3_differential_agrees_on_concrete_assertions(tmp_path):
    pytest.importorskip("z3")
    test_file = tmp_path / "test_statute.yh"
    test_file.write_text(
        """
        struct Facts {
            bool action,
            int amount,
            string label,
        }

        Facts facts := Facts {
            action := TRUE,
            amount := 3,
            label := "ok",
        }

        assert facts.action == TRUE
        assert facts.amount + 2 == 5
        assert facts.label == "ok"
        """,
        encoding="utf-8",
    )

    summary = verify_runtime_tests.run_z3_differential([test_file])

    assert summary is not None
    assert summary.checked == 1
    assert summary.assertions == 3
    assert summary.failures == ()
    assert summary.errors == ()


def test_runtime_z3_differential_covers_nested_scope_calls(tmp_path):
    pytest.importorskip("z3")
    test_file = tmp_path / "test_statute.yh"
    test_file.write_text(
        """
        struct Facts {
            bool act,
            bool intent,
            bool recklessness,
        }

        statute 1 "Nested base" {
          elements { all_of {
            actus_reus act := "act";
            any_of {
              mens_rea intent := "intent";
              mens_rea recklessness := "recklessness";
            }
          } }
        }

        Facts facts := Facts {
            act := TRUE,
            intent := TRUE,
            recklessness := FALSE,
        }

        assert apply_scope(s1, facts) == TRUE
        assert apply_scope(s1, facts, { intent := FALSE }) == FALSE
        assert apply_scope(s1, facts, { intent := FALSE, recklessness := TRUE }) == TRUE
        """,
        encoding="utf-8",
    )

    summary = verify_runtime_tests.run_z3_differential([test_file])

    assert summary is not None
    assert summary.checked == 1
    assert summary.assertions == 3
    assert summary.failures == ()
    assert summary.errors == ()


def test_runtime_z3_differential_covers_exception_guards(tmp_path):
    pytest.importorskip("z3")
    test_file = tmp_path / "test_statute.yh"
    test_file.write_text(
        """
        struct Facts {
            bool act,
            bool lawful,
        }

        statute 1 "Guarded exception" {
          elements {
            actus_reus act := "act";
          }

          exception lawful_authority {
            "lawful authority applies"
            "no conviction"
            when lawful
          }
        }

        Facts guilty := Facts {
            act := TRUE,
            lawful := FALSE,
        }

        Facts excused := Facts {
            act := TRUE,
            lawful := TRUE,
        }

        assert apply_scope(s1, guilty) == TRUE
        assert apply_scope(s1, excused) == FALSE
        """,
        encoding="utf-8",
    )

    summary = verify_runtime_tests.run_z3_differential([test_file])

    assert summary is not None
    assert summary.checked == 1
    assert summary.assertions == 2
    assert summary.failures == ()
    assert summary.errors == ()


def test_runtime_z3_differential_covers_optional_pass_values(tmp_path):
    pytest.importorskip("z3")
    test_file = tmp_path / "test_statute.yh"
    test_file.write_text(
        """
        int? maybe := pass
        string? label := "known"

        assert maybe == pass
        assert label != pass
        """,
        encoding="utf-8",
    )

    summary = verify_runtime_tests.run_z3_differential([test_file])

    assert summary is not None
    assert summary.checked == 1
    assert summary.assertions == 2
    assert summary.failures == ()
    assert summary.errors == ()
