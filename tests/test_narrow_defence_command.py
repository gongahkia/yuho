"""Tests for `yuho narrow-defence` — structural-availability floor.

Pins:
- Subsection-element flattening at the Z3 layer: defence sections
  (s76–s106) declare their elements inside `subsection (1) {…}` and
  must still resolve to a sat overlap with an offence section.
- Clear error when neither section declares elements anywhere.
- JSON-mode output shape.
- `--minimal` reduces the count of True element Bools.
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
    not (LIBRARY / "s302_punishment_for_murder" / "statute.yh").exists()
    or not (LIBRARY / "s84_act_person_unsound_mind" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_narrow_defence_with_subsection_only_defence():
    """s302 vs s84 — s84's elements live inside subsection (1). The
    Z3 generator's subsection-elements hoist must make this resolve."""
    runner = CliRunner()
    result = runner.invoke(cli, ["narrow-defence", "s302", "s84"])
    assert result.exit_code == 0, result.output
    assert "structural overlap" in result.output
    assert "Not legal advice" in result.output


@pytest.mark.skipif(
    not (LIBRARY / "s302_punishment_for_murder" / "statute.yh").exists()
    or not (LIBRARY / "s79_act_done_person_mistake_fact_believing" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_narrow_defence_minimal_flag_yields_smaller_facts():
    """--minimal should not increase the count of True element Bools."""
    runner = CliRunner()
    plain = runner.invoke(cli, ["narrow-defence", "s302", "s79", "--json"])
    minimal = runner.invoke(cli, ["narrow-defence", "s302", "s79", "--minimal", "--json"])
    assert plain.exit_code == 0, plain.output
    assert minimal.exit_code == 0, minimal.output
    p = json.loads(plain.output)
    m = json.loads(minimal.output)

    def _count_true(payload):
        n = 0
        for fp in payload["fact_pattern"].values():
            n += sum(1 for v in fp.values() if v)
        return n

    # Minimisation gives at-most-as-many True bools as the any-model run.
    # (Equal is fine — Z3 may pick the same model when minimal already.)
    assert _count_true(m) <= _count_true(p), (m, p)
    assert m["minimal"] is True
    assert p["minimal"] is False


@pytest.mark.skipif(
    not (LIBRARY / "s302_punishment_for_murder" / "statute.yh").exists()
    or not (LIBRARY / "s79_act_done_person_mistake_fact_believing" / "statute.yh").exists(),
    reason="Penal Code library not present",
)
def test_narrow_defence_json_shape_carries_disclaimer():
    runner = CliRunner()
    result = runner.invoke(cli, ["narrow-defence", "s302", "s79", "--json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["overlap"] is True
    assert payload["offence"] == "s302"
    assert payload["defence"] == "s79"
    assert payload["not_legal_advice"] is True
    assert "disclaimer" in payload
    assert "fact_pattern" in payload
    assert "shared_satisfied_names" in payload


def test_narrow_defence_unresolved_section_errors_cleanly():
    runner = CliRunner()
    result = runner.invoke(cli, ["narrow-defence", "s99999", "s302"])
    assert result.exit_code != 0
    output = result.output or ""
    assert "could not locate encoded section" in output \
           or "could not locate encoded section" in str(result.exception)
