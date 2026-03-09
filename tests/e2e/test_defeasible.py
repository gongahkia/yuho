"""E2E tests: defeasible reasoning."""
import pytest
from yuho.ast import nodes
from yuho.ast.nodes import (
    StatuteNode, StringLit, ElementNode, ElementGroupNode,
    PenaltyNode, ExceptionNode, DurationNode, MoneyNode,
    BinaryExprNode, IdentifierNode,
)

def make_simple_statute(with_exception=False, guard_expr=None):
    """Create a simple statute for testing."""
    elements = (
        ElementGroupNode(
            combinator="all_of",
            members=(
                ElementNode(element_type="actus_reus", name="act", description=StringLit(value="The act")),
                ElementNode(element_type="mens_rea", name="intent", description=StringLit(value="The intent")),
            ),
        ),
    )
    exceptions = ()
    if with_exception:
        exceptions = (
            ExceptionNode(
                label="selfDefence",
                condition=StringLit(value="Self defence applies"),
                effect=StringLit(value="Acquitted"),
                guard=guard_expr,
            ),
        )
    return StatuteNode(
        section_number="999",
        title=StringLit(value="Test Offence"),
        definitions=(),
        elements=elements,
        penalty=None,
        illustrations=(),
        exceptions=exceptions,
    )

class TestDefeasibleReasoning:
    def test_base_satisfied(self):
        """All elements satisfied -> base_satisfied=True."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": True}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is True
        assert result.final_verdict == "convicted"

    def test_base_not_satisfied(self):
        """Missing element -> base_satisfied=False."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": False}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is False
        assert result.final_verdict == "not_satisfied"

    def test_exception_defeats_conviction(self):
        """Exception with matching label defeats conviction."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=True)
        facts = {"act": True, "intent": True, "exception": "selfDefence"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is True
        assert result.defeated is True
        assert result.final_verdict == "exception_applied"

    def test_exception_not_triggered(self):
        """Exception label doesn't match -> conviction stands."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=True)
        facts = {"act": True, "intent": True, "exception": "other"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is True
        assert result.defeated is False
        assert result.final_verdict == "convicted"

    def test_reasoning_chain_populated(self):
        """Reasoning chain should have entries for all steps."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=True)
        facts = {"act": True, "intent": True, "exception": "selfDefence"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert len(result.reasoning_chain) > 0

    def test_multiple_exceptions(self):
        """Multiple exceptions - first matching one applies."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = StatuteNode(
            section_number="999",
            title=StringLit(value="Test"),
            definitions=(),
            elements=(
                ElementNode(element_type="actus_reus", name="act", description=StringLit(value="act")),
            ),
            penalty=None,
            illustrations=(),
            exceptions=(
                ExceptionNode(label="exc1", condition=StringLit(value="c1")),
                ExceptionNode(label="exc2", condition=StringLit(value="c2")),
            ),
        )
        facts = {"act": True, "exception": "exc2"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.defeated is True
        applied = [e for e in result.exceptions_applied if e.guard_satisfied]
        assert len(applied) == 1
        assert applied[0].label == "exc2"

    def test_no_exceptions_defined(self):
        """Statute with no exceptions -> convicted when base satisfied."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=False)
        facts = {"act": True, "intent": True}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is True
        assert result.defeated is False
        assert len(result.exceptions_applied) == 0
        assert result.final_verdict == "convicted"

    def test_no_exceptions_base_not_satisfied(self):
        """Statute with no exceptions and missing element -> not_satisfied."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=False)
        facts = {"act": True} # missing intent
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is False
        assert result.final_verdict == "not_satisfied"
        assert len(result.exceptions_applied) == 0

    def test_all_exceptions_matching(self):
        """When all exceptions match, result should be exception_applied."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = StatuteNode(
            section_number="777",
            title=StringLit(value="Multi Exception"),
            definitions=(),
            elements=(
                ElementNode(element_type="actus_reus", name="act", description=StringLit(value="act")),
            ),
            penalty=None,
            illustrations=(),
            exceptions=(
                ExceptionNode(label="exc1", condition=StringLit(value="c1")),
                ExceptionNode(label="exc2", condition=StringLit(value="c2")),
                ExceptionNode(label="exc3", condition=StringLit(value="c3")),
            ),
        )
        # use exc1 - should match first
        facts = {"act": True, "exception": "exc1"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is True
        assert result.defeated is True
        assert result.final_verdict == "exception_applied"
        applied = [e for e in result.exceptions_applied if e.guard_satisfied]
        assert len(applied) >= 1
        assert applied[0].label == "exc1"

    def test_empty_facts_all_unsatisfied(self):
        """Empty facts dict -> all elements unsatisfied."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is False
        assert result.final_verdict == "not_satisfied"

    def test_reasoning_chain_has_final_verdict_step(self):
        """Reasoning chain should always end with a final verdict step."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": True}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert len(result.reasoning_chain) > 0
        last_step = result.reasoning_chain[-1]
        assert "final verdict" in last_step.description.lower()

    def test_reasoning_chain_records_element_checks(self):
        """Reasoning chain should include individual element check steps."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": True}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        descriptions = [s.description.lower() for s in result.reasoning_chain]
        # should mention act and intent elements
        assert any("act" in d for d in descriptions), (
            "Reasoning chain should reference element 'act'"
        )
        assert any("intent" in d for d in descriptions), (
            "Reasoning chain should reference element 'intent'"
        )

    def test_reasoning_chain_records_exception_checks(self):
        """Reasoning chain should include exception check steps when exceptions exist."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=True)
        facts = {"act": True, "intent": True, "exception": "selfDefence"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        descriptions = [s.description.lower() for s in result.reasoning_chain]
        assert any("exception" in d for d in descriptions)
        assert any("selfdefence" in d for d in descriptions)

    def test_defeated_property(self):
        """The defeated property should be True iff any exception has guard_satisfied."""
        from yuho.eval.defeasible import DefeasibleReasoner, DefeasibleResult, ExceptionApplication
        # manually construct result to test the property
        result_defeated = DefeasibleResult(
            statute_section="1",
            statute_title="T",
            base_satisfied=True,
            exceptions_applied=[
                ExceptionApplication(label="a", condition="c", guard_satisfied=False),
                ExceptionApplication(label="b", condition="c", guard_satisfied=True),
            ],
            final_verdict="exception_applied",
            reasoning_chain=[],
        )
        assert result_defeated.defeated is True
        result_not_defeated = DefeasibleResult(
            statute_section="1",
            statute_title="T",
            base_satisfied=True,
            exceptions_applied=[
                ExceptionApplication(label="a", condition="c", guard_satisfied=False),
            ],
            final_verdict="convicted",
            reasoning_chain=[],
        )
        assert result_not_defeated.defeated is False

    def test_any_of_element_group(self):
        """any_of element group: only one element needed for base satisfaction."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = StatuteNode(
            section_number="888",
            title=StringLit(value="Any Of Test"),
            definitions=(),
            elements=(
                ElementGroupNode(
                    combinator="any_of",
                    members=(
                        ElementNode(element_type="actus_reus", name="a", description=StringLit(value="A")),
                        ElementNode(element_type="actus_reus", name="b", description=StringLit(value="B")),
                    ),
                ),
            ),
            penalty=None,
            illustrations=(),
            exceptions=(),
        )
        # only 'a' satisfied -> should still satisfy any_of group
        result = reasoner.evaluate_with_exceptions(statute, {"a": True, "b": False})
        assert result.base_satisfied is True
        assert result.final_verdict == "convicted"
        # only 'b' satisfied -> should still satisfy
        result2 = reasoner.evaluate_with_exceptions(statute, {"a": False, "b": True})
        assert result2.base_satisfied is True
        # neither satisfied -> not satisfied
        result3 = reasoner.evaluate_with_exceptions(statute, {"a": False, "b": False})
        assert result3.base_satisfied is False

    def test_nested_element_groups(self):
        """Nested all_of inside any_of should evaluate correctly."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = StatuteNode(
            section_number="777",
            title=StringLit(value="Nested Groups"),
            definitions=(),
            elements=(
                ElementGroupNode(
                    combinator="all_of",
                    members=(
                        ElementNode(element_type="actus_reus", name="act", description=StringLit(value="act")),
                        ElementGroupNode(
                            combinator="any_of",
                            members=(
                                ElementNode(element_type="mens_rea", name="intent1", description=StringLit(value="i1")),
                                ElementNode(element_type="mens_rea", name="intent2", description=StringLit(value="i2")),
                            ),
                        ),
                    ),
                ),
            ),
            penalty=None,
            illustrations=(),
            exceptions=(),
        )
        # act + intent1 -> satisfied (all_of: act=True, any_of: intent1=True)
        r1 = reasoner.evaluate_with_exceptions(statute, {"act": True, "intent1": True, "intent2": False})
        assert r1.base_satisfied is True
        # act + intent2 -> satisfied
        r2 = reasoner.evaluate_with_exceptions(statute, {"act": True, "intent1": False, "intent2": True})
        assert r2.base_satisfied is True
        # act only, no intent -> not satisfied (any_of fails)
        r3 = reasoner.evaluate_with_exceptions(statute, {"act": True, "intent1": False, "intent2": False})
        assert r3.base_satisfied is False
        # intent but no act -> not satisfied (all_of fails)
        r4 = reasoner.evaluate_with_exceptions(statute, {"act": False, "intent1": True, "intent2": True})
        assert r4.base_satisfied is False

    def test_guard_expression_evaluation(self):
        """Exception with a guard expression that evaluates against facts."""
        from yuho.eval.defeasible import DefeasibleReasoner
        # guard: facts.provoked == True -> IdentifierNode("provoked")
        guard = IdentifierNode(name="provoked")
        statute = StatuteNode(
            section_number="555",
            title=StringLit(value="Guard Test"),
            definitions=(),
            elements=(
                ElementNode(element_type="actus_reus", name="act", description=StringLit(value="act")),
            ),
            penalty=None,
            illustrations=(),
            exceptions=(
                ExceptionNode(
                    label="provocation",
                    condition=StringLit(value="Provoked"),
                    effect=StringLit(value="Reduced"),
                    guard=guard,
                ),
            ),
        )
        reasoner = DefeasibleReasoner()
        # provoked=True -> guard satisfied -> exception applied
        r1 = reasoner.evaluate_with_exceptions(statute, {"act": True, "provoked": True})
        assert r1.base_satisfied is True
        assert r1.defeated is True
        assert r1.final_verdict == "exception_applied"
        # provoked=False -> guard not satisfied -> convicted
        r2 = reasoner.evaluate_with_exceptions(statute, {"act": True, "provoked": False})
        assert r2.base_satisfied is True
        assert r2.defeated is False
        assert r2.final_verdict == "convicted"

    def test_guard_complex_binary_expression(self):
        """Exception with a complex binary guard expression (age > 18)."""
        from yuho.eval.defeasible import DefeasibleReasoner
        # guard: age > 18
        guard = BinaryExprNode(
            left=IdentifierNode(name="age"),
            operator=">",
            right=nodes.IntLit(value=18),
        )
        statute = StatuteNode(
            section_number="556",
            title=StringLit(value="Binary Guard"),
            definitions=(),
            elements=(
                ElementNode(element_type="actus_reus", name="act", description=StringLit(value="act")),
            ),
            penalty=None,
            illustrations=(),
            exceptions=(
                ExceptionNode(
                    label="adultConsent",
                    condition=StringLit(value="Consent by adult"),
                    effect=StringLit(value="Acquitted"),
                    guard=guard,
                ),
            ),
        )
        reasoner = DefeasibleReasoner()
        # age=25 -> 25 > 18 -> guard satisfied
        r1 = reasoner.evaluate_with_exceptions(statute, {"act": True, "age": 25})
        assert r1.base_satisfied is True
        assert r1.defeated is True
        # age=16 -> 16 > 18 is false -> guard not satisfied
        r2 = reasoner.evaluate_with_exceptions(statute, {"act": True, "age": 16})
        assert r2.base_satisfied is True
        assert r2.defeated is False

    def test_exception_application_details(self):
        """ExceptionApplication should record condition, effect, and label."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute(with_exception=True)
        facts = {"act": True, "intent": True, "exception": "selfDefence"}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert len(result.exceptions_applied) == 1
        app = result.exceptions_applied[0]
        assert app.label == "selfDefence"
        assert app.condition == "Self defence applies"
        assert app.effect == "Acquitted"
        assert app.guard_satisfied is True

    def test_statute_section_and_title_in_result(self):
        """DefeasibleResult should carry the statute section and title."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": True}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.statute_section == "999"
        assert result.statute_title == "Test Offence"

    def test_none_valued_facts_treated_as_false(self):
        """Facts with None values should be treated as not satisfied."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": None}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is False

    def test_extra_facts_ignored(self):
        """Extra facts not referenced by elements should be ignored."""
        from yuho.eval.defeasible import DefeasibleReasoner
        reasoner = DefeasibleReasoner()
        statute = make_simple_statute()
        facts = {"act": True, "intent": True, "irrelevant": "data", "extra": 42}
        result = reasoner.evaluate_with_exceptions(statute, facts)
        assert result.base_satisfied is True
        assert result.final_verdict == "convicted"
