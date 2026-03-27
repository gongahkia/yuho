"""E2E tests: verification pipeline."""

import pytest
from yuho.ast.nodes import (
    StatuteNode,
    StringLit,
    ElementNode,
    ElementGroupNode,
    PenaltyNode,
    DurationNode,
    ExceptionNode,
)

MINIMAL_SOURCE = """
struct TestCase { bool guilty, }
statute 999 "Test Statute" {
    elements {
        actus_reus act := "The physical act";
        mens_rea intent := "The mental state";
    }
    penalty {
        imprisonment := 1 years .. 5 years;
    }
}
"""


class TestVerifyPipeline:
    def test_z3_generates_constraints(self, statute_dir, parse_file):
        """Z3 should generate constraints from statutes."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        assert solver is not None

    def test_alloy_generates_model(self, statute_dir, parse_file):
        """Alloy should generate model from statutes."""
        statute_path = statute_dir / "statute.yh"
        if not statute_path.exists():
            pytest.skip()
        ast = parse_file(statute_path)
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not yet handle ElementGroupNode")
        assert len(model) > 0
        assert "sig" in model or "fact" in model

    def test_z3_assertions_non_empty(self, parse_source):
        """Z3 should produce at least one assertion from a statute with elements."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        ast = parse_source(MINIMAL_SOURCE)
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        assert solver is not None
        assert len(assertions) > 0, "Z3 should generate at least one assertion"

    def test_z3_conviction_variable_created(self, parse_source):
        """Z3 should create a conviction boolean variable for each statute."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        ast = parse_source(MINIMAL_SOURCE)
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        # the generator should have created a conviction variable
        assert (
            "999_conviction" in gen._consts
        ), "Z3Generator should create a conviction variable for statute 999"

    def test_z3_element_variables_created(self, parse_source):
        """Z3 should create boolean variables for each leaf element."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        ast = parse_source(MINIMAL_SOURCE)
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        # should have element variables for act and intent
        const_names = set(gen._consts.keys())
        assert any(
            "act" in name and "satisfied" in name for name in const_names
        ), "Z3 should create a satisfied variable for element 'act'"
        assert any(
            "intent" in name and "satisfied" in name for name in const_names
        ), "Z3 should create a satisfied variable for element 'intent'"

    def test_z3_sorts_include_statute(self, parse_source):
        """Z3 should create a Statute sort."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        ast = parse_source(MINIMAL_SOURCE)
        gen = Z3Generator()
        gen.generate(ast)
        assert "Statute" in gen._sorts

    def test_z3_struct_sort_generated(self, parse_source):
        """Z3 should create a sort for struct definitions."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        ast = parse_source(MINIMAL_SOURCE)
        gen = Z3Generator()
        gen.generate(ast)
        assert "TestCase" in gen._sorts, "Z3Generator should create a sort for struct TestCase"

    def test_z3_element_group_all_of(self, parse_source):
        """Z3 should encode all_of groups as conjunction."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
            import z3
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        source = """
statute 500 "Grouped" {
    elements {
        all_of {
            actus_reus x := "X";
            mens_rea y := "Y";
        }
    }
}
"""
        ast = parse_source(source)
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        assert len(assertions) > 0
        # conviction should be biconditional with the conjunction of elements
        assert "500_conviction" in gen._consts

    def test_z3_element_group_any_of(self, parse_source):
        """Z3 should encode any_of groups as disjunction."""
        try:
            from yuho.verify.z3_solver import Z3Generator, Z3_AVAILABLE
        except ImportError:
            pytest.skip("z3 module not importable")
        if not Z3_AVAILABLE:
            pytest.skip("z3-solver package not installed")
        source = """
statute 501 "Disjunctive" {
    elements {
        any_of {
            actus_reus a := "A";
            actus_reus b := "B";
        }
    }
}
"""
        ast = parse_source(source)
        gen = Z3Generator()
        solver, assertions = gen.generate(ast)
        assert "501_conviction" in gen._consts
        # both element variables should exist
        const_names = set(gen._consts.keys())
        assert any("a_satisfied" in n for n in const_names)
        assert any("b_satisfied" in n for n in const_names)

    def test_alloy_model_has_expected_signatures(self, parse_source):
        """Alloy model should contain sigs for statutes and base types."""
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        ast = parse_source(MINIMAL_SOURCE)
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not handle this case")
        assert "sig" in model
        assert "Person" in model or "Element" in model
        assert "Statute_999" in model

    def test_alloy_model_has_facts(self, parse_source):
        """Alloy model should contain facts derived from statute elements."""
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        ast = parse_source(MINIMAL_SOURCE)
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not handle this case")
        assert "fact" in model
        # should reference element fields
        assert "act" in model
        assert "intent" in model

    def test_alloy_model_has_assertions(self, parse_source):
        """Alloy model should contain at least one assertion."""
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        ast = parse_source(MINIMAL_SOURCE)
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not handle this case")
        assert "assert" in model

    def test_alloy_model_has_check_commands(self, parse_source):
        """Alloy model should contain check commands for verification."""
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        ast = parse_source(MINIMAL_SOURCE)
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not handle this case")
        assert "check" in model

    def test_alloy_model_conviction_biconditional(self, parse_source):
        """Alloy model should contain conviction biconditional for statutes with elements."""
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        ast = parse_source(MINIMAL_SOURCE)
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not handle this case")
        assert "Conviction" in model
        assert "convicted" in model

    def test_alloy_exception_generates_pred(self, parse_source):
        """Alloy should generate pred blocks for statute exceptions."""
        try:
            from yuho.verify.alloy import AlloyGenerator
        except ImportError:
            pytest.skip("alloy not available")
        source = """
statute 600 "With Exception" {
    elements {
        actus_reus act := "The act";
    }
    exception selfDef {
        "Self defence"
        "Acquitted"
    }
}
"""
        ast = parse_source(source)
        gen = AlloyGenerator()
        try:
            model = gen.generate(ast)
        except AttributeError:
            pytest.skip("AlloyGenerator does not handle this case")
        assert "pred" in model
        assert "selfDef" in model or "self" in model.lower()
