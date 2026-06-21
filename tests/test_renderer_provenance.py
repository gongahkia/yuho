"""Regression tests for doctrinal renderer provenance."""

from __future__ import annotations

from pathlib import Path

from yuho.services.analysis import analyze_file, analyze_source
from yuho.transpile.english_transpiler import EnglishTranspiler
from yuho.transpile.mermaid_transpiler import MermaidTranspiler


STATUTE_PATH = (
    Path(__file__).resolve().parents[1] / "library" / "penal_code" / "s300_murder" / "statute.yh"
)


def test_english_transpiler_marks_doctrinal_structure_and_provenance() -> None:
    """English output should distinguish combinators and cite provenance."""
    analysis = analyze_file(STATUTE_PATH)
    assert analysis.ast is not None

    output = EnglishTranspiler().transpile(analysis.ast)

    assert "Conjunctive requirement (all_of)" in output
    assert "Alternative requirement (any_of)" in output
    assert 'Guard: facts\'s exception equals "provocation"' in output
    assert "Provenance: statutory illustration attached to Section 300." in output
    assert "Provenance: judicial authority linked to element intent1." in output


def test_mermaid_transpiler_links_provenance_nodes() -> None:
    """Mermaid output should expose exception defeat and provenance edges."""
    analysis = analyze_file(STATUTE_PATH)
    assert analysis.ast is not None

    output = MermaidTranspiler().transpile(analysis.ast)

    assert '"ALL OF (conjunctive)"' in output
    assert '"Exceptions / defences"' in output
    assert '"illustration provenance"' in output
    assert '"interprets"' in output
    assert "guard: facts.exception ==" in output


def test_mermaid_transpiler_color_codes_doctrinal_nodes() -> None:
    source = '''
        statute 1 "Demo" {
          elements {
            all_of {
              actus_reus act := "act";
              mens_rea intent := "intent";
              circumstance context := "context";
            }
          }
          exception defence {
            "defence applies"
            "no liability"
          }
        }
    '''
    analysis = analyze_source(source, run_semantic=False)
    assert analysis.ast is not None

    output = MermaidTranspiler().transpile(analysis.ast)
    lines = {line.strip() for line in output.splitlines()}

    assert "classDef ar fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;" in lines
    assert "classDef mr fill:#dbeafe,stroke:#2563eb,color:#1e3a8a;" in lines
    assert "classDef circumstance fill:#dcfce7,stroke:#16a34a,color:#14532d;" in lines
    assert "classDef exception fill:#fef3c7,stroke:#d97706,color:#78350f;" in lines
    assert any(line.startswith("class ELEM") and line.endswith(" ar;") for line in lines)
    assert any(line.startswith("class ELEM") and line.endswith(" mr;") for line in lines)
    assert any(line.startswith("class ELEM") and line.endswith(" circumstance;") for line in lines)
    assert any(line.startswith("class EXC") and line.endswith(" exception;") for line in lines)
