"""Tests for the Mermaid flowchart `schema` shape.

The schema-shape flowchart walks a *case struct*'s enum-typed fields
and surfaces the consuming fn's consequences as terminal nodes — the
shape depicted in `docs/user/5-minutes.md`. Linkage is by naming
convention: a struct field named ``deceptionType`` matches an enum
declared as ``enum DeceptionType {…}``.
"""

from __future__ import annotations

from yuho.services.analysis import analyze_source
from yuho.transpile.mermaid_transpiler import MermaidTranspiler


_SCHEMA_FIXTURE = '''
enum AttributionType { SoleInducement, NotSoleInducement, NA }
enum DeceptionType { Fraudulently, Dishonestly, NA }
enum InducementType { DeliverProperty, ConsentRetainProperty, DoOrOmit, NA }

struct CheatingCase {
    string deceptionType,
    string inducementType,
    bool causesDamageHarm,
}

fn evaluateCheating(string deceptionType, string inducementType, bool causesDamageHarm) : string {
    match {
        case TRUE if deceptionType == "none" := consequence "Not cheating - no deception";
        case TRUE if inducementType == "none" := consequence "Not cheating - no inducement";
        case TRUE if causesDamageHarm := consequence "Said to cheat";
        case _ := consequence "Not said to cheat";
    }
}

statute 415 "Cheating" {
    elements { all_of {
        actus_reus deception := "Deceiving any person";
    } }
}
'''


def _emit_schema(src: str) -> str:
    result = analyze_source(src, run_semantic=False)
    assert result.ast is not None, [str(e) for e in result.parse_errors]
    return MermaidTranspiler(shape="schema").transpile(result.ast)


def test_schema_shape_invalid_value_rejected():
    import pytest
    with pytest.raises(ValueError):
        MermaidTranspiler(shape="bogus")


def test_schema_emits_root_from_case_struct_name_minus_case_suffix():
    out = _emit_schema(_SCHEMA_FIXTURE)
    # 'CheatingCase' -> 'Cheating' as the root display label.
    assert '(["Cheating"])' in out


def test_schema_walks_case_struct_fields_in_order():
    out = _emit_schema(_SCHEMA_FIXTURE)
    # Each field becomes a {{decision-diamond}}; order matches struct decl.
    decep_idx = out.index('{{"deceptionType"}}')
    induc_idx = out.index('{{"inducementType"}}')
    causes_idx = out.index('{{"causesDamageHarm"}}')
    assert decep_idx < induc_idx < causes_idx


def test_schema_emits_one_edge_per_enum_variant():
    out = _emit_schema(_SCHEMA_FIXTURE)
    # DeceptionType has 3 variants; expect 3 edges out of the deceptionType diamond.
    assert '|"DeceptionType.Fraudulently"|' in out
    assert '|"DeceptionType.Dishonestly"|' in out
    assert '|"DeceptionType.NA"|' in out
    assert '|"InducementType.DeliverProperty"|' in out
    assert '|"InducementType.ConsentRetainProperty"|' in out
    assert '|"InducementType.DoOrOmit"|' in out


def test_schema_terminates_with_consequence_when_fn_supplies_one():
    out = _emit_schema(_SCHEMA_FIXTURE)
    # The fn's last (default/wildcard) arm or the first matching arm
    # is wired to the last field's terminal node.
    assert "Said to cheat" in out or "Not said to cheat" in out


def test_schema_falls_back_when_no_case_struct_present():
    """Module with statutes but no case struct + fn pair: the schema
    transpiler should annotate and fall back to statute shape."""
    src = '''
        statute 1 "Demo" {
          elements { actus_reus a := "x"; }
          penalty { fine := unlimited; }
        }
    '''
    out = _emit_schema(src)
    assert "No schema pair found" in out
    # Fallback emits the statute-shape body too so the diagram has content.
    assert "Section 1" in out


def test_schema_falls_back_when_fn_params_dont_match_struct():
    """Struct + fn both present, but fn signature doesn't align with struct."""
    src = '''
        enum Mood { Happy, Sad }

        struct Box {
            string mood,
        }

        fn unrelated(int x) : bool {
            match { case _ := consequence FALSE; }
        }

        statute 1 "Demo" {
          elements { actus_reus a := "x"; }
        }
    '''
    out = _emit_schema(src)
    assert "No schema pair found" in out


def test_schema_handles_struct_field_without_matching_enum():
    """Field 'mystery' with no enum 'Mystery' — emits a single
    placeholder edge instead of crashing."""
    src = '''
        struct DemoCase { string mystery, }
        fn run(string mystery) : bool {
            match { case _ := consequence TRUE; }
        }
        statute 1 "Demo" { elements { actus_reus a := "x"; } }
    '''
    out = _emit_schema(src)
    assert '{{"mystery"}}' in out
    # No enum -> straight-line "continue" edge from the diamond.
    assert "Mystery" not in out  # no enum variant edges emitted
