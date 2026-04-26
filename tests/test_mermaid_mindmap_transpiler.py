"""Tests for the Mermaid mindmap transpiler (statute-shape).

The mindmap target shows the *structural* shape of an encoded statute
(definitions → elements → penalty → illustrations), as opposed to the
flowchart target which shows the *evaluation* shape. These tests pin
the output structure so future refactors don't silently regress it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from yuho.services.analysis import analyze_source
from yuho.transpile import TranspileTarget, get_transpiler


def _emit(yh: str) -> str:
    result = analyze_source(yh, run_semantic=False)
    assert result.ast is not None, [str(e) for e in result.parse_errors]
    return get_transpiler(TranspileTarget.MINDMAP).transpile(result.ast)


# =============================================================================
# Target plumbing
# =============================================================================


def test_target_string_aliases():
    assert TranspileTarget.from_string("mindmap") is TranspileTarget.MINDMAP
    assert TranspileTarget.from_string("mermaid-mindmap") is TranspileTarget.MINDMAP


def test_file_extension_is_mmd():
    assert TranspileTarget.MINDMAP.file_extension == ".mmd"


# =============================================================================
# Output shape
# =============================================================================


def test_starts_with_mindmap_directive():
    out = _emit('statute 1 "Demo" { elements { actus_reus a := "x"; } }')
    assert out.splitlines()[0] == "mindmap"


def test_root_is_section_title_round():
    out = _emit('statute 415 "Cheating" { elements { actus_reus a := "x"; } }')
    # Mermaid mindmap root is decorated with `((round))` syntax.
    assert "((s415 Cheating))" in out


def test_definitions_cluster_emitted():
    out = _emit(
        'statute 1 "Demo" {'
        '  definitions { foo := "bar"; baz := "qux"; }'
        '  elements { actus_reus a := "x"; }'
        '}'
    )
    assert "Definitions" in out
    assert "foo" in out
    assert "baz" in out


def test_elements_cluster_with_combinator_tag():
    out = _emit('''
        statute 1 "Demo" {
          elements { all_of {
            actus_reus deception := "Deceives";
            any_of {
              mens_rea fraudulent := "Intent to defraud";
              mens_rea dishonest := "Dishonest intent";
            }
          } }
        }
    ''')
    assert "Elements [ALL OF]" in out
    assert "[ANY OF]" in out
    assert "actus_reus deception" in out
    assert "mens_rea fraudulent" in out


def test_penalty_with_unlimited_fine():
    out = _emit('''
        statute 1 "Demo" {
          elements { actus_reus a := "x"; }
          penalty { fine := unlimited; }
        }
    ''')
    assert "Penalty" in out
    assert "Fine [unlimited]" in out  # parens get rewritten to brackets


def test_penalty_with_caning_unspecified():
    out = _emit('''
        statute 1 "Demo" {
          elements { actus_reus a := "x"; }
          penalty { caning := unspecified; }
        }
    ''')
    assert "Caning [unspecified]" in out


def test_multi_penalty_g12_pattern_preserved():
    """The G12 multi-penalty pattern must surface both blocks in the mindmap."""
    out = _emit('''
        statute 363 "Demo" {
          elements { actus_reus a := "x"; }
          penalty cumulative {
            imprisonment := 0 years .. 7 years;
          }
          penalty or_both {
            fine := unlimited;
            caning := unspecified;
          }
        }
    ''')
    # Sanitiser rewrites () to [] so the mindmap parser doesn't mistake
    # them for node decorators.
    assert "Penalty [1]" in out
    assert "Penalty [2] [or_both]" in out
    assert "Imprisonment 0 days..7 years" in out
    assert "Fine [unlimited]" in out
    assert "Caning [unspecified]" in out


def test_illustrations_listed():
    out = _emit('''
        statute 1 "Demo" {
          elements { actus_reus a := "x"; }
          illustration first { "When A does X, A commits the offence." }
          illustration second { "When B does Y, B commits the offence." }
        }
    ''')
    assert "Illustrations" in out
    assert "first" in out
    assert "second" in out


def test_exceptions_listed():
    out = _emit('''
        statute 1 "Demo" {
          elements { actus_reus a := "x"; }
          exception consent {
            "victim consents"
            "no offence"
            when facts.consent == "true"
          }
        }
    ''')
    assert "Exceptions" in out
    assert "consent" in out


def test_indentation_two_spaces():
    """Mermaid mindmap parser is whitespace-sensitive; pin the indent."""
    out = _emit('statute 1 "Demo" { elements { actus_reus a := "x"; } }')
    lines = out.splitlines()
    # Root sits at depth 1 (two spaces), elements cluster at depth 2 (four).
    root_line = next(l for l in lines if "((s1 Demo))" in l)
    assert root_line.startswith("  ((")
    elements_line = next(l for l in lines if l.strip() == "Elements [ALL OF]")
    assert elements_line.startswith("    ")


def test_no_unescaped_parentheses_break_parser():
    """Free-form description text with parens shouldn't crash the parser."""
    out = _emit('''
        statute 1 "Demo" {
          definitions { term := "Some text (with parens)"; }
          elements { actus_reus a := "Action (with parens)"; }
        }
    ''')
    # Sanitised to brackets so mindmap doesn't treat them as decorators.
    assert "(with parens)" not in out
    # Output should still build successfully.
    assert "term" in out


# =============================================================================
# Real library smoke
# =============================================================================


@pytest.mark.skipif(
    not Path("library/penal_code/s415_cheating/statute.yh").exists(),
    reason="library/penal_code not present in this checkout",
)
def test_real_s415_round_trip():
    text = Path("library/penal_code/s415_cheating/statute.yh").read_text()
    out = _emit(text)
    assert out.startswith("mindmap")
    assert "s415" in out
    # All five top-level clusters should be present.
    assert "Definitions" in out
    assert "Elements" in out
    assert "Penalty" in out
    assert "Illustrations" in out
