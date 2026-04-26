"""Tests for the evaluator-side apply_scope semantics.

`StatuteEvaluator.apply_scope(section_ref, facts, registry)` returns a
full :class:`EvaluationResult` whose ``bindings()`` are the per-element
satisfied/unsatisfied map the parent scope can compose with. This is
the Catala-style scope-composition contract.
"""

from __future__ import annotations

import pytest

from yuho.ast import nodes
from yuho.eval.interpreter import StructInstance, Value
from yuho.eval.statute_evaluator import StatuteEvaluator
from yuho.services.analysis import analyze_source


def _facts(**fields: bool) -> StructInstance:
    """Build a StructInstance with boolean fields for testing."""
    return StructInstance(
        type_name="Facts",
        fields={k: Value(raw=v, type_tag="bool") for k, v in fields.items()},
    )


def _registry_from_module(module: nodes.ModuleNode):
    return {st.section_number: st for st in module.statutes}


_BASE_LIBRARY = '''
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
    circumstance s300_limb := "Falls within s300 limbs";
  } }
}

statute 107 "Abetment" {
  elements { all_of {
    actus_reus instigation := "Instigates the doing of a thing";
    mens_rea abet_intent := "With knowledge that the thing is an offence";
  } }
}
'''


@pytest.fixture
def registry():
    result = analyze_source(_BASE_LIBRARY, run_semantic=False)
    assert not result.parse_errors, [str(e) for e in result.parse_errors]
    return _registry_from_module(result.ast)


class TestApplyScopeReturnsBindings:
    def test_satisfied_scope_returns_bindings(self, registry):
        """When all base elements are met, bindings reflect that and overall_satisfied is True."""
        facts = _facts(death=True, intent=True)
        ev = StatuteEvaluator()
        result = ev.apply_scope("299", facts, registry)
        assert result.overall_satisfied is True
        bindings = result.bindings()
        assert bindings == {"death": True, "intent": True}
        assert result.statute_section == "299"

    def test_partial_facts_yield_partial_bindings(self, registry):
        facts = _facts(death=True, intent=False)
        result = StatuteEvaluator().apply_scope("299", facts, registry)
        assert result.overall_satisfied is False
        bindings = result.bindings()
        assert bindings["death"] is True
        assert bindings["intent"] is False

    def test_section_ref_canonicalisation(self, registry):
        """Accepts s299 / s.299 / Section 299 / 299."""
        facts = _facts(death=True, intent=True)
        ev = StatuteEvaluator()
        for ref in ("299", "s299", "S.299", "Section 299"):
            r = ev.apply_scope(ref, facts, registry)
            assert r.overall_satisfied is True, f"failed for ref={ref!r}"


class TestApplyScopeRegistryContract:
    def test_unknown_section_raises_keyerror(self, registry):
        with pytest.raises(KeyError):
            StatuteEvaluator().apply_scope("9999", _facts(), registry)

    def test_empty_registry_raises_keyerror(self):
        with pytest.raises(KeyError):
            StatuteEvaluator().apply_scope("299", _facts(), {})


class TestParentScopeCompositionPattern:
    """Demonstrates the load-bearing use case: s107 abetment composed
    over a base offence via apply_scope, then the parent reads bindings
    to enforce its own cumulative requirements."""

    def test_compose_abetment_over_culpable_homicide(self, registry):
        # Facts that satisfy s299 (the abetted base offence) AND s107's
        # own elements (instigation + abet intent).
        facts = _facts(
            death=True, intent=True,           # s299 base
            instigation=True, abet_intent=True,  # s107 wrapper
        )
        ev = StatuteEvaluator()
        base_result = ev.apply_scope("299", facts, registry)
        wrapper_result = ev.apply_scope("107", facts, registry)

        # Parent-scope predicate: "abetment of s299 is made out iff both
        # the base scope and this scope's own elements are satisfied".
        composed = base_result.overall_satisfied and wrapper_result.overall_satisfied
        assert composed is True

        # The parent can also inspect individual bindings from the base.
        base_bindings = base_result.bindings()
        assert base_bindings["death"] is True
        assert base_bindings["intent"] is True

    def test_parent_short_circuits_when_base_not_satisfied(self, registry):
        # Wrapper elements present, but base offence is missing intent.
        facts = _facts(
            death=True, intent=False,
            instigation=True, abet_intent=True,
        )
        ev = StatuteEvaluator()
        base_result = ev.apply_scope("299", facts, registry)
        assert base_result.overall_satisfied is False
        # The parent's composition predicate would fail.
        wrapper_result = ev.apply_scope("107", facts, registry)
        assert wrapper_result.overall_satisfied is True  # wrapper alone is fine
        assert (base_result.overall_satisfied
                and wrapper_result.overall_satisfied) is False


class TestRecursionGuard:
    def test_explicit_self_call_is_caught(self, registry):
        """When the caller threads a trace that already names the target,
        apply_scope raises RecursionError."""
        ev = StatuteEvaluator()
        with pytest.raises(RecursionError):
            ev.apply_scope("299", _facts(), registry, _trace=["299"])
