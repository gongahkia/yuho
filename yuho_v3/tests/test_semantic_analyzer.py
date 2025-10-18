"""
Tests for Yuho Semantic Analyzer

Tests type checking, scope analysis, and semantic validation.
"""

import pytest
from yuho_v3.parser import YuhoParser
from yuho_v3.semantic_analyzer import SemanticAnalyzer, SemanticError


class TestSemanticAnalyzerBasics:
    """Test basic semantic analyzer functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_analyzer_initialization(self):
        """Test that analyzer initializes correctly"""
        assert self.analyzer is not None
        assert self.analyzer.global_scope is not None

    def test_analyze_empty_program(self):
        """Test analyzing empty program"""
        ast = self.parser.parse("")
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0


class TestSemanticAnalyzerTypeChecking:
    """Test type checking"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_valid_int_declaration(self):
        """Test valid integer declaration"""
        code = "int x := 42;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_valid_string_declaration(self):
        """Test valid string declaration"""
        code = 'string s := "hello";'
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_type_mismatch_declaration(self):
        """Test type mismatch in declaration"""
        code = 'int x := "not an int";'
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) > 0

    def test_type_compatible_int_to_float(self):
        """Test that int is compatible with float"""
        code = "float x := 42;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0


class TestSemanticAnalyzerStructs:
    """Test struct semantic analysis"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_valid_struct_definition(self):
        """Test valid struct definition"""
        code = """
        struct Person {
            string name,
            int age
        }
        """
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_duplicate_member_names(self):
        """Test duplicate member names in struct"""
        code = """
        struct Person {
            string name,
            string name
        }
        """
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) > 0
        assert "Duplicate member" in errors[0]


class TestSemanticAnalyzerScope:
    """Test scope analysis"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_undefined_variable(self):
        """Test reference to undefined variable"""
        code = "int y := x;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) > 0
        assert "Undefined" in errors[0]

    def test_valid_variable_reference(self):
        """Test valid variable reference"""
        code = """
        int x := 42;
        int y := x;
        """
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_duplicate_variable_definition(self):
        """Test duplicate variable definition"""
        code = """
        int x := 1;
        int x := 2;
        """
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) > 0


class TestSemanticAnalyzerExpressions:
    """Test expression type checking"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_arithmetic_int_addition(self):
        """Test integer addition type checking"""
        code = "int result := 1 + 2;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_logical_and_bools(self):
        """Test logical AND with booleans"""
        code = "bool result := TRUE && FALSE;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_logical_and_non_bools(self):
        """Test logical AND with non-booleans"""
        code = "bool result := 1 && 2;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) > 0

    def test_comparison_compatible_types(self):
        """Test comparison with compatible types"""
        code = "bool result := 5 > 3;"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0


class TestSemanticAnalyzerMatchCase:
    """Test match-case semantic analysis"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_valid_match_case(self):
        """Test valid match-case"""
        code = """
        match {
            case TRUE := consequence TRUE;
            case _ := consequence pass;
        }
        """
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0


class TestSemanticAnalyzerEdgeCases:
    """Test edge cases in semantic analysis"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()
        self.analyzer = SemanticAnalyzer()

    def test_complex_nested_expressions(self):
        """Test complex nested expressions"""
        code = "int result := (1 + 2) * (3 + 4);"
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

    def test_multiple_statements_with_dependencies(self):
        """Test multiple statements with dependencies"""
        code = """
        int x := 1;
        int y := x + 1;
        int z := x + y;
        """
        ast = self.parser.parse(code)
        errors = self.analyzer.analyze(ast)
        assert len(errors) == 0

