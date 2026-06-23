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


def test_runtime_z3_differential_covers_mixed_groups_and_is_infringed(tmp_path):
    pytest.importorskip("z3")
    test_file = tmp_path / "test_statute.yh"
    test_file.write_text(
        """
        bool act := TRUE
        bool intent := FALSE
        bool alternative := TRUE

        struct Facts {
            bool act,
            bool intent,
            bool alternative,
        }

        statute 1 "Mixed groups" {
          elements {
            any_of {
              all_of {
                actus_reus act := "act";
                mens_rea intent := "intent";
              }
              circumstance alternative := "alternative";
            }
          }
        }

        Facts facts := Facts {
            act := TRUE,
            intent := FALSE,
            alternative := TRUE,
        }

        assert is_infringed(s1) == TRUE
        assert apply_scope(s1, facts) == TRUE
        assert apply_scope(s1, facts, { alternative := FALSE }) == FALSE
        """,
        encoding="utf-8",
    )

    summary = verify_runtime_tests.run_z3_differential([test_file])

    assert summary is not None
    assert summary.checked == 1
    assert summary.assertions == 3
    assert summary.failures == ()
    assert summary.errors == ()


def test_runtime_z3_differential_covers_money_and_duration_assertions(tmp_path):
    pytest.importorskip("z3")
    test_file = tmp_path / "test_statute.yh"
    test_file.write_text(
        """
        money low_fine := $10.00
        money high_fine := $20.00
        duration short_term := 1 day
        duration long_term := 2 days

        assert low_fine < high_fine
        assert short_term < long_term
        """,
        encoding="utf-8",
    )

    summary = verify_runtime_tests.run_z3_differential([test_file])

    assert summary is not None
    assert summary.checked == 1
    assert summary.assertions == 2
    assert summary.failures == ()
    assert summary.errors == ()
