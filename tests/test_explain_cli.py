"""CLI tests for ``yuho explain``."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from yuho.cli.main import cli


STATUTE = """
statute 1 "Demo" {
    elements {
        actus_reus taking := "takes";
        mens_rea intent := "intends";
    }
}
"""


def _write_library(tmp_path: Path) -> Path:
    root = tmp_path / "library"
    section = root / "s1_demo"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(STATUTE, encoding="utf-8")
    return root


def test_explain_cli_outputs_element_trace(tmp_path: Path):
    root = _write_library(tmp_path)
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True, "intent": False}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert "Section 1 is not satisfied." in result.output
    assert "The actus_reus element taking is satisfied" in result.output
    assert "The mens_rea element intent is not satisfied" in result.output


def test_explain_cli_json_output(tmp_path: Path):
    root = _write_library(tmp_path)
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True, "intent": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "--json", "1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["overall_satisfied"] is True
    assert payload["elements"][0]["name"] == "taking"


def test_explain_cli_includes_typed_fact_metadata(tmp_path: Path):
    root = _write_library(tmp_path)
    facts = tmp_path / "facts.json"
    facts.write_text(
        json.dumps(
            {
                "facts": {
                    "taking": {
                        "value": True,
                        "type": "bool",
                        "source": "witness A",
                        "evidential_status": "admitted",
                        "burden": "prosecution",
                        "standard_of_proof": "beyond_reasonable_doubt",
                    },
                    "intent": {"value": False, "type": "bool"},
                }
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert "standard=beyond_reasonable_doubt" in result.output
    assert "source=witness A" in result.output


def test_explain_cli_element_predicate_uses_structured_facts(tmp_path: Path):
    root = tmp_path / "library"
    section = root / "s1_predicate"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(
        """
        statute 1 "Predicate" {
            elements {
                actus_reus deception := facts.representation.falsehood && facts.accused.knows_falsehood;
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(
        json.dumps(
            {
                "representation": {"falsehood": True},
                "accused": {"knows_falsehood": True},
            }
        ),
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert "predicate expression is truthy" in result.output
    assert "Section 1 is satisfied." in result.output


def test_explain_cli_includes_case_law_for_targeted_elements(tmp_path: Path):
    root = tmp_path / "library"
    section = root / "s1_precedent"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(
        """
        statute 1 "Precedent" {
            elements {
                actus_reus taking := "takes";
            }

            caselaw "Old v PP" "[1990] SGHC 1" {
                "Taking includes temporary control"
                element taking
            }

            caselaw "New v PP" "[2026] SGCA 1" {
                "Taking requires control plus deprivation"
                element taking
                treatment overruled "Old v PP" "[1990] SGHC 1"
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert "Case law New v PP [2026] SGCA 1 interprets element taking" in result.output
    assert "Case law Old v PP [1990] SGHC 1 is overruled by New v PP" in result.output
    assert "holding not treated as active for element taking" in result.output


def test_explain_cli_json_includes_precedent_status(tmp_path: Path):
    root = tmp_path / "library"
    section = root / "s1_precedent"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(
        """
        statute 1 "Precedent" {
            elements {
                actus_reus taking := "takes";
            }

            caselaw "New v PP" "[2026] SGCA 1" {
                "Taking requires control plus deprivation"
                element taking
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "--json", "1"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    precedent = payload["elements"][0]["precedents"][0]
    assert precedent["case_name"] == "New v PP"
    assert precedent["citation"] == "[2026] SGCA 1"
    assert precedent["status"] == "active"


def test_explain_cli_marks_distinguished_case_inactive(tmp_path: Path):
    root = tmp_path / "library"
    section = root / "s1_precedent"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(
        """
        statute 1 "Precedent" {
            elements {
                actus_reus taking := "takes";
            }

            caselaw "Old v PP" "[1990] SGHC 1" {
                "Taking includes temporary control"
                element taking
            }

            caselaw "Different Facts v PP" "[2026] SGCA 2" {
                "Old v PP does not apply on different facts"
                element taking
                treatment distinguished "Old v PP" "[1990] SGHC 1"
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert (
        "Case law Old v PP [1990] SGHC 1 is distinguished by Different Facts v PP" in result.output
    )
    assert "holding not treated as active for element taking" in result.output


def test_explain_cli_marks_disapproved_case_inactive(tmp_path: Path):
    root = tmp_path / "library"
    section = root / "s1_precedent"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(
        """
        statute 1 "Precedent" {
            elements {
                actus_reus taking := "takes";
            }

            caselaw "Old v PP" "[1990] SGHC 1" {
                "Taking includes temporary control"
                element taking
            }

            caselaw "Appeal v PP" "[2026] SGCA 2" {
                "Old v PP should not be followed"
                element taking
                treatment disapproves "Old v PP" "[1990] SGHC 1"
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"taking": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "1"],
    )

    assert result.exit_code == 0
    assert "Case law Old v PP [1990] SGHC 1 is disapproved by Appeal v PP" in result.output
    assert "holding not treated as active for element taking" in result.output


def test_explain_cli_resolves_apply_scope_in_predicate_elements(tmp_path: Path):
    root = tmp_path / "library"
    section = root / "s300_wrapper"
    section.mkdir(parents=True)
    (section / "statute.yh").write_text(
        """
        statute 299 "Base" {
            elements { all_of {
                actus_reus act := "act";
                mens_rea intent := "intent";
            } }
        }

        statute 300 "Wrapper" {
            elements {
                circumstance base := apply_scope(s299, facts);
            }
        }
        """,
        encoding="utf-8",
    )
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"act": True, "intent": True}), encoding="utf-8")

    result = CliRunner().invoke(
        cli,
        ["explain", "--facts", str(facts), "--library", str(root), "300"],
    )

    assert result.exit_code == 0
    assert "Section 300 is satisfied." in result.output
    assert "predicate expression is truthy" in result.output
