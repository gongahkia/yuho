"""E2E tests: defeasible reasoning."""
import pytest
from yuho.ast import nodes
from yuho.ast.nodes import (
    StatuteNode, StringLit, ElementNode, ElementGroupNode,
    PenaltyNode, ExceptionNode, DurationNode, MoneyNode,
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
