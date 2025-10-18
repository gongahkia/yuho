"""
Tests for Yuho Parser

Tests AST generation and transformation from parse trees.
"""

import pytest
from yuho_v3.parser import YuhoParser
from yuho_v3.ast_nodes import (
    Program, Declaration, StructDefinition, MatchCase,
    Literal, YuhoType, TypeNode, Identifier
)


class TestParserBasics:
    """Test basic parser functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_parser_initialization(self):
        """Test that parser initializes correctly"""
        assert self.parser is not None
        assert self.parser.lexer is not None
        assert self.parser.transformer is not None

    def test_parse_empty_program(self):
        """Test parsing empty program returns Program node"""
        ast = self.parser.parse("")
        assert isinstance(ast, Program)
        assert len(ast.statements) == 0


class TestParserDeclarations:
    """Test parsing variable declarations"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_parse_int_declaration(self):
        """Test parsing integer declaration"""
        code = "int x := 42;"
        ast = self.parser.parse(code)
        
        assert isinstance(ast, Program)
        assert len(ast.statements) == 1
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)
        assert decl.name == "x"
        assert isinstance(decl.value, Literal)
        assert decl.value.value == 42

    def test_parse_float_declaration(self):
        """Test parsing float declaration"""
        code = "float y := 3.14;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)
        assert decl.name == "y"
        assert decl.value.value == 3.14

    def test_parse_string_declaration(self):
        """Test parsing string declaration"""
        code = 'string s := "hello";'
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)
        assert decl.name == "s"
        assert decl.value.value == "hello"

    def test_parse_bool_declaration(self):
        """Test parsing boolean declaration"""
        code = "bool b := TRUE;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)
        assert decl.name == "b"
        assert decl.value.value is True

    def test_parse_declaration_without_value(self):
        """Test parsing declaration without initial value"""
        code = "int x;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)
        assert decl.name == "x"
        assert decl.value is None


class TestParserStructs:
    """Test parsing struct definitions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_parse_empty_struct(self):
        """Test parsing empty struct"""
        code = "struct Empty {}"
        ast = self.parser.parse(code)
        
        struct = ast.statements[0]
        assert isinstance(struct, StructDefinition)
        assert struct.name == "Empty"
        assert len(struct.members) == 0

    def test_parse_struct_single_field(self):
        """Test parsing struct with single field"""
        code = """
        struct Person {
            string name
        }
        """
        ast = self.parser.parse(code)
        
        struct = ast.statements[0]
        assert isinstance(struct, StructDefinition)
        assert struct.name == "Person"
        assert len(struct.members) == 1
        assert struct.members[0].name == "name"

    def test_parse_struct_multiple_fields(self):
        """Test parsing struct with multiple fields"""
        code = """
        struct Person {
            string name,
            int age,
            bool active
        }
        """
        ast = self.parser.parse(code)
        
        struct = ast.statements[0]
        assert isinstance(struct, StructDefinition)
        assert len(struct.members) == 3
        assert struct.members[0].name == "name"
        assert struct.members[1].name == "age"
        assert struct.members[2].name == "active"


class TestParserMatchCase:
    """Test parsing match-case constructs"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_parse_simple_match(self):
        """Test parsing simple match-case"""
        code = """
        match {
            case TRUE := consequence TRUE;
        }
        """
        ast = self.parser.parse(code)
        
        match = ast.statements[0]
        assert isinstance(match, MatchCase)
        assert match.expression is None  # Bare match
        assert len(match.cases) == 1

    def test_parse_match_with_wildcard(self):
        """Test parsing match with wildcard"""
        code = """
        match {
            case TRUE := consequence TRUE;
            case _ := consequence pass;
        }
        """
        ast = self.parser.parse(code)
        
        match = ast.statements[0]
        assert len(match.cases) == 2
        assert match.cases[1].condition is None  # Wildcard case


class TestParserExpressions:
    """Test parsing expressions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_parse_arithmetic_addition(self):
        """Test parsing addition expression"""
        code = "int result := 1 + 2;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)
        # The value should be a BinaryOperation

    def test_parse_arithmetic_nested(self):
        """Test parsing nested arithmetic"""
        code = "int result := 1 + 2 * 3;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)

    def test_parse_logical_and(self):
        """Test parsing logical AND"""
        code = "bool result := TRUE && FALSE;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)

    def test_parse_comparison(self):
        """Test parsing comparison"""
        code = "bool result := 5 > 3;"
        ast = self.parser.parse(code)
        
        decl = ast.statements[0]
        assert isinstance(decl, Declaration)


class TestParserEdgeCases:
    """Test parser edge cases"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_parse_with_comments(self):
        """Test parsing code with comments"""
        code = """
        // This is a comment
        int x := 42;
        /* Multi-line
           comment */
        int y := 100;
        """
        ast = self.parser.parse(code)
        
        assert len(ast.statements) == 2

    def test_parse_with_whitespace(self):
        """Test parsing with excessive whitespace"""
        code = """
        
        
        int    x    :=    42   ;
        
        
        """
        ast = self.parser.parse(code)
        
        assert len(ast.statements) == 1

    def test_parse_multistatement(self):
        """Test parsing multiple statements"""
        code = """
        int x := 1;
        int y := 2;
        int z := 3;
        """
        ast = self.parser.parse(code)
        
        assert len(ast.statements) == 3


class TestParserErrors:
    """Test parser error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.parser = YuhoParser()

    def test_syntax_error(self):
        """Test that syntax errors are caught"""
        code = "int x = 42;"  # Should use := not =
        with pytest.raises(SyntaxError):
            self.parser.parse(code)

    def test_incomplete_statement(self):
        """Test incomplete statement"""
        code = "int x :="  # Missing value
        with pytest.raises(SyntaxError):
            self.parser.parse(code)

    def test_unclosed_brace(self):
        """Test unclosed brace"""
        code = "struct Test {"
        with pytest.raises(SyntaxError):
            self.parser.parse(code)

