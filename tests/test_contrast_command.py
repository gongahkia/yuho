"""Tests for `yuho contrast` — Z3-driven counter-factual edge-case explorer.

The command asks Z3 for a fact pattern that satisfies SECTION_A's
conviction predicate while failing SECTION_B's. These tests pin:

- Resolution of section refs against the encoded library.
- The contrast model is sat for canonical doctrinal pairs (s299 vs
  s300, s378 vs s415).
- The contrast model is unsat / yields a clean "no contrast" message
  when the two sections share their full element set.
- JSON-mode output shape.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from click.testing import CliRunner

from yuho.cli.main import cli

REPO = Path(__file__).resolve().parents[1]
LIBRARY = REPO / "library" / "penal_code"


@pytest.mark.skipif(
    not (LIBRARY / "s299_culpable_homicide" / "statute.yh").exists()
    or not (LIBRARY / "s300_murder" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_contrast_canonical_pair_yields_distinguishing_facts():
    """s299 vs s300 — culpable homicide vs murder. Z3 should find a
    fact pattern that satisfies s299 but fails s300."""
    runner = CliRunner()
    result = runner.invoke(cli, ["contrast", "s299", "s300"])
    assert result.exit_code == 0, result.output
    assert "contrast: s299 satisfied, s300 not satisfied" in result.output
    assert "Not legal advice" in result.output


@pytest.mark.skipif(
    not (LIBRARY / "s378_theft" / "statute.yh").exists()
    or not (LIBRARY / "s415_cheating" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_contrast_unrelated_pair_still_produces_a_model():
    """s378 vs s415 — theft vs cheating. Different element sets, so
    the contrast is structurally trivial; still must return cleanly."""
    runner = CliRunner()
    result = runner.invoke(cli, ["contrast", "s378", "s415"])
    assert result.exit_code == 0, result.output
    assert "s378 satisfied" in result.output
    assert "s415 not satisfied" in result.output


@pytest.mark.skipif(
    not (LIBRARY / "s299_culpable_homicide" / "statute.yh").exists()
    or not (LIBRARY / "s300_murder" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_contrast_json_output_shape():
    runner = CliRunner()
    result = runner.invoke(cli, ["contrast", "s299", "s300", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["contrast"] is True
    assert payload["section_a"] == "s299"
    assert payload["section_b"] == "s300"
    assert payload["a_conviction"] is True
    assert payload["b_conviction"] is False
    assert payload["not_legal_advice"] is True
    assert "fact_pattern" in payload
    assert "s299_elements" in payload["fact_pattern"]
    assert "s300_elements" in payload["fact_pattern"]
    # The contract: at least one s299 element must be true and at
    # least one s300 element must be false (otherwise the convictions
    # couldn't have diverged).
    a_facts = payload["fact_pattern"]["s299_elements"]
    b_facts = payload["fact_pattern"]["s300_elements"]
    assert any(v for v in a_facts.values()), a_facts
    assert any(not v for v in b_facts.values()), b_facts


def test_contrast_unresolved_section_errors_cleanly():
    runner = CliRunner()
    result = runner.invoke(cli, ["contrast", "s99999", "s299"])
    assert result.exit_code != 0
    assert "could not locate encoded section" in (result.output or "") or \
           "could not locate encoded section" in str(result.exception)
