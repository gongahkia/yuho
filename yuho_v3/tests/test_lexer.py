"""
Tests for Yuho Lexer

Tests tokenization and parsing of Yuho source code.
"""

import pytest
from yuho_v3.lexer import YuhoLexer


class TestLexerBasics:
    """Test basic lexer functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.lexer = YuhoLexer()

    def test_lexer_initialization(self):
        """Test that lexer initializes correctly"""
        assert self.lexer is not None
        assert self.lexer.parser is not None

    def test_empty_program(self):
        """Test parsing empty program"""
        result = self.lexer.parse("")
        assert result is not None

    def test_comment_single_line(self):
        """Test single-line comments are ignored"""
        code = "// This is a comment"
        result = self.lexer.parse(code)
        assert result is not None

    def test_comment_multi_line(self):
        """Test multi-line comments are ignored"""
        code = """
        /* This is a
           multi-line comment */
        """
        result = self.lexer.parse(code)
        assert result is not None


class TestLexerLiterals:
    """Test lexing of literal values"""

    def setup_method(self):
        """Set up test fixtures"""
        self.lexer = YuhoLexer()

    def test_integer_literal(self):
        """Test integer literal parsing"""
        code = "int x := 42;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_float_literal(self):
        """Test float literal parsing"""
        code = "float y := 3.14;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_string_literal(self):
        """Test string literal parsing"""
        code = 'string s := "hello world";'
        result = self.lexer.parse(code)
        assert result is not None

    def test_boolean_true(self):
        """Test TRUE boolean literal"""
        code = "bool b := TRUE;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_boolean_false(self):
        """Test FALSE boolean literal"""
        code = "bool b := FALSE;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_percentage_literal(self):
        """Test percentage literal parsing"""
        code = "percent p := 25%;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_money_literal(self):
        """Test money literal parsing"""
        code = "money m := $100.50;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_date_literal(self):
        """Test date literal parsing"""
        code = "date d := 01-01-2024;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_duration_literal_days(self):
        """Test duration literal with days"""
        code = "duration dur := 5 days;"
        result = self.lexer.parse(code)
        assert result is not None

    def test_duration_literal_months(self):
        """Test duration literal with months"""
        code = "duration dur := 3 months;"
        result = self.lexer.parse(code)
        assert result is not None


class TestLexerStructs:
    """Test lexing of struct definitions"""

    def setup_method(self):
        """Set up test fixtures"""
        self.lexer = YuhoLexer()

    def test_empty_struct(self):
        """Test empty struct definition"""
        code = "struct Empty {}"
        result = self.lexer.parse(code)
        assert result is not None

    def test_simple_struct(self):
        """Test simple struct with one field"""
        code = """
        struct Person {
            string name
        }
        """
        result = self.lexer.parse(code)
        assert result is not None

    def test_struct_multiple_fields(self):
        """Test struct with multiple fields"""
        code = """
        struct Person {
            string name,
            int age,
            bool active
        }
        """
        result = self.lexer.parse(code)
        assert result is not None


class TestLexerMatchCase:
    """Test lexing of match-case constructs"""

    def setup_method(self):
        """Set up test fixtures"""
        self.lexer = YuhoLexer()

    def test_simple_match(self):
        """Test simple match-case"""
        code = """
        match {
            case TRUE := consequence pass;
        }
        """
        result = self.lexer.parse(code)
        assert result is not None

    def test_match_with_wildcard(self):
        """Test match with wildcard default case"""
        code = """
        match {
            case TRUE := consequence pass;
            case _ := consequence pass;
        }
        """
        result = self.lexer.parse(code)
        assert result is not None


class TestLexerErrors:
    """Test lexer error handling"""

    def setup_method(self):
        """Set up test fixtures"""
        self.lexer = YuhoLexer()

    def test_invalid_syntax(self):
        """Test that invalid syntax raises error"""
        code = "this is not valid yuho syntax @#$%"
        with pytest.raises(SyntaxError):
            self.lexer.parse(code)

    def test_unclosed_string(self):
        """Test unclosed string literal"""
        code = 'string s := "unclosed'
        with pytest.raises(SyntaxError):
            self.lexer.parse(code)

    def test_invalid_token(self):
        """Test invalid token"""
        code = "int x := @invalid;"
        with pytest.raises(SyntaxError):
            self.lexer.parse(code)

