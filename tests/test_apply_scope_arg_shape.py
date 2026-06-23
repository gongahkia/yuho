"""Static type-check pass for `apply_scope(<section>, <args>)`.

Most apply_scope call sites pass an identifier (`apply_scope(s299, facts)`)
which is statically opaque. Three structurally checkable shapes still
deserve a warning:

1. The target section has zero top-level elements — calling apply_scope
   on it is structurally meaningless.
2. The first arg is a *struct literal* whose fields don't cover the
   element names the target reads.
3. A struct literal override names a field the target's elements do not
   read.

This test pins those diagnostics + the silent-on-identifier path.
"""

from __future__ import annotations

import json
from pathlib import Path

from yuho.ast import nodes
from yuho.library.graph_lint import check_apply_scope_arg_shape
from yuho.services.analysis import analyze_file, analyze_source
from yuho.transpile.json_transpiler import JSONTranspiler


_LIBRARY = """
statute 299 "Culpable homicide" {
  elements { all_of {
    actus_reus death := "Causes death of a person";
    mens_rea intent := "Intent to kill";
  } }
}

statute 999 "Empty placeholder" {
}
"""

_CONTRACT_LIBRARY = """
struct HomicideFacts { bool death, bool intent, }
struct OtherFacts { bool death, bool intent, }

/// @input HomicideFacts
/// @output bool
statute 299 "Culpable homicide" {
  elements {
    actus_reus death := "Causes death of a person";
  }
}
"""


def _registry(src: str):
    result = analyze_source(src, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    return result.ast, {st.section_number: st for st in result.ast.statutes}


def _scope_module(call_site: str) -> nodes.ModuleNode:
    """Build a module containing the base library + a wrapper fn."""
    src = _LIBRARY + f"\n{call_site}\n"
    result = analyze_source(src, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    return result.ast


def _contract_module(call_site: str) -> nodes.ModuleNode:
    src = _CONTRACT_LIBRARY + f"\n{call_site}\n"
    result = analyze_source(src, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    return result.ast


def test_doc_declared_section_contract_is_preserved_in_ast_and_json():
    result = analyze_source(_CONTRACT_LIBRARY, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    statute = result.ast.statutes[0]

    assert isinstance(statute.input_type, nodes.NamedType)
    assert statute.input_type.name == "HomicideFacts"
    assert isinstance(statute.output_type, nodes.BuiltinType)
    assert statute.output_type.name == "bool"

    payload = json.loads(JSONTranspiler(include_locations=False).transpile(result.ast).output)
    encoded = payload["statutes"][0]
    assert encoded["input_type"] == {"_type": "NamedType", "name": "HomicideFacts"}
    assert encoded["output_type"] == {"_type": "BuiltinType", "name": "bool"}


def test_identifier_arg_is_silent():
    """The common case `apply_scope(sX, facts)` is opaque — no warning."""
    module = _scope_module(
        """
        fn run(string facts) : bool { return apply_scope(s299, facts); }
    """
    )
    warnings = check_apply_scope_arg_shape(module)
    assert warnings == []


def test_section_contract_schema_checks_beyond_element_names():
    module = _contract_module(
        """
        HomicideFacts ctx := { death := TRUE };
        fn run() : bool { return apply_scope(s299, ctx); }
    """
    )

    warnings = check_apply_scope_arg_shape(module)

    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_arg_missing_fields"
    assert "target input schema" in warnings[0].message
    assert "intent" in warnings[0].message


def test_section_contract_rejects_visible_input_type_mismatch():
    module = _contract_module(
        """
        OtherFacts ctx := { death := TRUE, intent := TRUE };
        fn run() : bool { return apply_scope(s299, ctx); }
    """
    )

    warnings = check_apply_scope_arg_shape(module)

    assert any(w.code == "apply_scope_arg_input_type_mismatch" for w in warnings)
    assert any("expected HomicideFacts" in w.message for w in warnings)


def test_semantic_analysis_rejects_section_contract_missing_fields():
    src = _CONTRACT_LIBRARY + """
        fn run() : bool {
            HomicideFacts ctx := { death := TRUE };
            return apply_scope(s299, ctx);
        }
    """

    result = analyze_source(src, run_semantic=True)

    assert result.semantic_summary is not None
    assert result.semantic_summary.errors == 1
    assert "target input schema" in result.semantic_summary.issues[0].message
    assert "intent" in result.semantic_summary.issues[0].message


def test_target_with_no_elements_warns():
    module = _scope_module(
        """
        fn run() : bool { return apply_scope(s999); }
    """
    )
    warnings = check_apply_scope_arg_shape(module)
    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_target_empty"
    assert warnings[0].sections == ("999",)


def test_unresolved_target_is_skipped():
    """Resolution lint owns unresolved refs; arg-shape lint stays quiet."""
    module = _scope_module(
        """
        fn run() : bool { return apply_scope(s9999); }
    """
    )
    warnings = check_apply_scope_arg_shape(module)
    assert warnings == []


def test_explicit_registry_overrides_module_scope():
    """When a library-wide registry is passed, it takes precedence."""
    module = _scope_module(
        """
        fn run() : bool { return apply_scope(s299); }
    """
    )
    # Empty registry: target s299 is no longer resolvable, so the lint
    # silently skips (resolution lint owns this case).
    warnings = check_apply_scope_arg_shape(module, registry={})
    assert warnings == []


def test_first_struct_literal_missing_fields_warns():
    module = _scope_module(
        """
        fn run() : bool { return apply_scope(s299, { death := TRUE }); }
    """
    )
    warnings = check_apply_scope_arg_shape(module)
    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_arg_missing_fields"
    assert "intent" in warnings[0].message


def test_struct_literal_unknown_override_field_warns():
    module = _scope_module(
        """
        fn run(string facts) : bool {
            return apply_scope(s299, facts, { typo_intent := TRUE });
        }
    """
    )
    warnings = check_apply_scope_arg_shape(module)
    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_arg_unknown_fields"
    assert "typo_intent" in warnings[0].message


def test_struct_literal_non_bool_element_field_warns():
    module = _scope_module(
        """
        fn run() : bool {
            return apply_scope(s299, { death := TRUE, intent := "yes" });
        }
    """
    )
    warnings = check_apply_scope_arg_shape(module)
    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_arg_incompatible_field_type"
    assert "intent (string)" in warnings[0].message


def test_identifier_bound_struct_literal_missing_fields_warns():
    module = _scope_module(
        """
        Facts ctx := { death := TRUE };
        fn run() : bool { return apply_scope(s299, ctx); }
    """
    )

    warnings = check_apply_scope_arg_shape(module)

    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_arg_missing_fields"
    assert "identifier 'ctx'" in warnings[0].message
    assert "intent" in warnings[0].message


def test_identifier_bound_struct_literal_non_bool_field_warns():
    module = _scope_module(
        """
        Facts ctx := { death := TRUE, intent := "yes" };
        fn run() : bool { return apply_scope(s299, ctx); }
    """
    )

    warnings = check_apply_scope_arg_shape(module)

    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_arg_incompatible_field_type"
    assert "identifier 'ctx'" in warnings[0].message
    assert "intent (string)" in warnings[0].message


def test_semantic_analysis_rejects_missing_apply_scope_fields():
    src = _LIBRARY + """
        fn run() : bool { return apply_scope(s299, { death := TRUE }); }
    """

    result = analyze_source(src, run_semantic=True)

    assert result.semantic_summary is not None
    assert result.semantic_summary.errors == 1
    assert "missing fields" in result.semantic_summary.issues[0].message


def test_semantic_analysis_rejects_identifier_fact_shape_missing_fields():
    src = _LIBRARY + """
        struct Facts { bool death, bool intent, }
        fn run() : bool {
            Facts ctx := { death := TRUE };
            return apply_scope(s299, ctx);
        }
    """

    result = analyze_source(src, run_semantic=True)

    assert result.semantic_summary is not None
    assert result.semantic_summary.errors == 1
    assert "identifier 'ctx'" in result.semantic_summary.issues[0].message
    assert "missing fields" in result.semantic_summary.issues[0].message


def test_semantic_analysis_rejects_non_bool_apply_scope_fields():
    src = _LIBRARY + """
        fn run() : bool {
            return apply_scope(s299, { death := TRUE, intent := "yes" });
        }
    """

    result = analyze_source(src, run_semantic=True)

    assert result.semantic_summary is not None
    assert result.semantic_summary.errors == 1
    assert "non-bool values" in result.semantic_summary.issues[0].message


def test_semantic_analysis_checks_imported_identifier_fact_shape(tmp_path: Path):
    helper = tmp_path / "helper.yh"
    helper.write_text(
        """
struct Facts { bool death, bool intent, }
Facts ctx := { death := TRUE };
""",
        encoding="utf-8",
    )
    main = tmp_path / "main.yh"
    main.write_text(
        _LIBRARY
        + """
import { ctx } from "helper.yh";
fn run() : bool { return apply_scope(s299, ctx); }
""",
        encoding="utf-8",
    )

    result = analyze_file(main, run_semantic=True)

    assert result.semantic_summary is not None
    assert result.semantic_summary.errors == 1
    assert "identifier 'ctx'" in result.semantic_summary.issues[0].message
    assert "missing fields" in result.semantic_summary.issues[0].message
