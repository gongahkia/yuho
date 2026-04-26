"""Tests for the interpreter-level evaluation of section-composition
predicates (`apply_scope`, `is_infringed`).

Until this trench, the tree-walking :class:`Interpreter` had no
visitors for :class:`ApplyScopeNode` / :class:`IsInfringedNode`, so
expressions that contained them silently fell through to
``generic_visit`` and returned ``None``. This pinned the new
behaviour: both nodes evaluate to a boolean :class:`Value` whose
truth tracks the inner scope's ``overall_satisfied``.
"""

from __future__ import annotations

from yuho.ast import nodes
from yuho.eval.interpreter import Interpreter, StructInstance, Value
from yuho.services.analysis import analyze_source


_LIBRARY = '''
statute 299 "Culpable homicide" {
  elements { all_of {
    actus_reus death := "Causes death of a person";
    mens_rea intent := "With intention or knowledge";
  } }
}

statute 300 "Murder" subsumes 299 {
  elements { all_of {
    actus_reus death := "Causes death of a person";
    mens_rea murder_intent := "With intention to kill";
  } }
}
'''


def _interp_with_library() -> Interpreter:
    result = analyze_source(_LIBRARY, run_semantic=False)
    assert result.ast is not None, [str(e) for e in result.parse_errors]
    interp = Interpreter()
    interp.interpret(result.ast)
    return interp


def _bool_facts(**fields: bool) -> StructInstance:
    return StructInstance(
        type_name="Facts",
        fields={k: Value(raw=v, type_tag="bool") for k, v in fields.items()},
    )


def test_is_infringed_truthy_when_facts_satisfy_section():
    interp = _interp_with_library()
    # Plant the matching booleans into the interpreter env so the
    # implicit-facts path resolves them.
    interp.env.set("death", Value(raw=True, type_tag="bool"))
    interp.env.set("intent", Value(raw=True, type_tag="bool"))
    out = interp.visit(nodes.IsInfringedNode(section_ref="299"))
    assert isinstance(out, Value)
    assert out.type_tag == "bool"
    assert out.raw is True


def test_is_infringed_falsy_when_facts_miss_section():
    interp = _interp_with_library()
    interp.env.set("death", Value(raw=True, type_tag="bool"))
    interp.env.set("intent", Value(raw=False, type_tag="bool"))
    out = interp.visit(nodes.IsInfringedNode(section_ref="299"))
    assert out.raw is False


def test_apply_scope_uses_struct_arg_as_facts():
    interp = _interp_with_library()
    facts = _bool_facts(death=True, intent=True)
    # Stash the struct in an identifier so the arg AST resolves to it.
    interp.env.set("ctx", Value(raw=facts, type_tag="struct"))
    apply_node = nodes.ApplyScopeNode(
        section_ref="299",
        args=(nodes.IdentifierNode(name="ctx"),),
    )
    out = interp.visit(apply_node)
    assert isinstance(out, Value)
    assert out.type_tag == "bool"
    assert out.raw is True


def test_apply_scope_falls_back_to_env_when_no_struct_arg():
    interp = _interp_with_library()
    interp.env.set("death", Value(raw=True, type_tag="bool"))
    interp.env.set("intent", Value(raw=True, type_tag="bool"))
    out = interp.visit(nodes.ApplyScopeNode(section_ref="299"))
    assert out.raw is True


def test_unresolved_section_raises():
    import pytest
    from yuho.eval.interpreter import InterpreterError
    interp = _interp_with_library()
    with pytest.raises(InterpreterError):
        interp.visit(nodes.IsInfringedNode(section_ref="9999"))
