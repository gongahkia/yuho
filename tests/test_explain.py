"""Tests for ``yuho explain`` — prose-first per-section summary."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from yuho.cli.commands.explain import run_explain


def _run(file: str, **kw) -> str:
    buf = io.StringIO()
    with redirect_stdout(buf):
        run_explain(file, color=False, **kw)
    return buf.getvalue()


def test_explain_emits_five_section_structure(tmp_path: Path):
    p = tmp_path / "demo.yh"
    p.write_text('''
        statute 415 "Cheating" effective 1872-01-01 {
          elements { all_of {
            actus_reus deception := "Deceives any person";
            mens_rea fraud := "Fraudulent intent";
          } }
          penalty {
            imprisonment := 1 year .. 7 years;
            fine := $0.00 .. $50,000.00;
          }
          illustration ex1 { "A deceives B and takes B's watch." }
        }
    ''')
    out = _run(str(p))
    # Header
    assert "Section 415: Cheating" in out
    assert "Effective: 1872-01-01" in out
    # All five canonical headings
    assert "What it covers" in out
    assert "Elements" in out
    assert "Penalty" in out
    assert "Worked example" in out
    assert "NOT LEGAL ADVICE" in out


def test_explain_lists_elements_in_doctrinal_form(tmp_path: Path):
    p = tmp_path / "demo.yh"
    p.write_text('''
        statute 1 "Demo" {
          elements { all_of {
            actus_reus deception := "Deceives";
            mens_rea fraud := "Fraudulent";
          } }
        }
    ''')
    out = _run(str(p))
    assert "To prove this offence, the prosecution must show:" in out
    assert "- actus_reus deception: Deceives" in out
    assert "- mens_rea fraud: Fraudulent" in out


def test_explain_handles_no_offence(tmp_path: Path):
    """Sections without elements (interpretation provisions) shouldn't crash."""
    p = tmp_path / "demo.yh"
    p.write_text('statute 1 "Defines term X" { definitions { x := "y"; } elements {} }')
    out = _run(str(p))
    assert "defines a term or carves out an exception" in out


def test_explain_multi_penalty_g12(tmp_path: Path):
    p = tmp_path / "demo.yh"
    p.write_text('''
        statute 363 "Demo" {
          elements { actus_reus a := "x"; }
          penalty cumulative { imprisonment := 0 years .. 7 years; }
          penalty or_both { fine := unlimited; caning := unspecified; }
        }
    ''')
    out = _run(str(p))
    assert "multiple penalty clauses" in out
    assert "imprisonment of 0 days to 7 years" in out
    assert "fine (no statutory cap specified)" in out
    assert "caning (no stroke count specified)" in out


def test_explain_filters_by_section(tmp_path: Path):
    p = tmp_path / "demo.yh"
    p.write_text('''
        statute 1 "First" { elements { actus_reus a := "x"; } }
        statute 2 "Second" { elements { actus_reus a := "x"; } }
    ''')
    out = _run(str(p), section="2")
    assert "Section 2" in out
    assert "First" not in out


def test_explain_section_with_s_prefix(tmp_path: Path):
    p = tmp_path / "demo.yh"
    p.write_text('statute 415 "Cheating" { elements { actus_reus a := "x"; } }')
    # Both `s415` and `415` should resolve to the same section.
    assert "Section 415" in _run(str(p), section="415")
    assert "Section 415" in _run(str(p), section="s415")


def test_explain_unknown_section_exits_nonzero(tmp_path: Path):
    p = tmp_path / "demo.yh"
    p.write_text('statute 415 "Cheating" { elements { actus_reus a := "x"; } }')
    with pytest.raises(SystemExit):
        _run(str(p), section="9999")


def test_explain_real_s415_round_trip():
    yh = "library/penal_code/s415_cheating/statute.yh"
    if not Path(yh).exists():
        pytest.skip("library not present")
    out = _run(yh)
    assert "Section 415: Cheating" in out
    assert "Worked example" in out
    assert "NOT LEGAL ADVICE" in out
