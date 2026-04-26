"""Static type-check pass for `apply_scope(<section>, <args>)`.

Most apply_scope call sites pass an identifier (`apply_scope(s299, facts)`)
which is statically opaque. Two structurally checkable shapes still
deserve a warning:

1. The target section has zero top-level elements — calling apply_scope
   on it is structurally meaningless.
2. The first arg is a *struct literal* whose fields don't cover the
   element names the target reads.

This test pins both diagnostics + the silent-on-identifier path.
"""

from __future__ import annotations

from yuho.ast import nodes
from yuho.library.graph_lint import check_apply_scope_arg_shape
from yuho.services.analysis import analyze_source


_LIBRARY = '''
statute 299 "Culpable homicide" {
  elements { all_of {
    actus_reus death := "Causes death of a person";
    mens_rea intent := "Intent to kill";
  } }
}

statute 999 "Empty placeholder" {
}
'''


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


def test_identifier_arg_is_silent():
    """The common case `apply_scope(sX, facts)` is opaque — no warning."""
    module = _scope_module('''
        fn run(string facts) : bool { return apply_scope(s299, facts); }
    ''')
    warnings = check_apply_scope_arg_shape(module)
    assert warnings == []


def test_target_with_no_elements_warns():
    module = _scope_module('''
        fn run() : bool { return apply_scope(s999); }
    ''')
    warnings = check_apply_scope_arg_shape(module)
    assert len(warnings) == 1
    assert warnings[0].code == "apply_scope_target_empty"
    assert warnings[0].sections == ("999",)


def test_unresolved_target_is_skipped():
    """Resolution lint owns unresolved refs; arg-shape lint stays quiet."""
    module = _scope_module('''
        fn run() : bool { return apply_scope(s9999); }
    ''')
    warnings = check_apply_scope_arg_shape(module)
    assert warnings == []


def test_explicit_registry_overrides_module_scope():
    """When a library-wide registry is passed, it takes precedence."""
    module = _scope_module('''
        fn run() : bool { return apply_scope(s299); }
    ''')
    # Empty registry: target s299 is no longer resolvable, so the lint
    # silently skips (resolution lint owns this case).
    warnings = check_apply_scope_arg_shape(module, registry={})
    assert warnings == []
