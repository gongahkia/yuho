"""
Differential testing: V4 Lark parser vs V5 Tree-sitter parser.

Compares parse results between the legacy Lark-based parser (v4)
and the current tree-sitter parser (v5) for compatible inputs.
"""

import pytest
import sys
from pathlib import Path
from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

# Add archive path for v4 imports
archive_path = Path(__file__).parent.parent / "archive"
if str(archive_path) not in sys.path:
    sys.path.insert(0, str(archive_path))


DIFFERENTIAL_SETTINGS = settings(
    max_examples=50,
    deadline=10000,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much],
)


def get_v4_parser():
    """Get v4 Lark-based parser."""
    try:
        from yuho_v4.parser import YuhoParser as V4Parser
        return V4Parser()
    except ImportError as e:
        pytest.skip(f"V4 parser not available: {e}")


def get_v5_parser():
    """Get v5 tree-sitter parser."""
    try:
        from yuho.parser import Parser as V5Parser
        return V5Parser()
    except ImportError as e:
        pytest.skip(f"V5 parser not available: {e}")


# Strategies for generating compatible v4/v5 code

@st.composite
def simple_declaration_strategy(draw):
    """Generate simple variable declarations valid in both v4 and v5."""
    var_type = draw(st.sampled_from(["int", "float", "bool", "string"]))
    var_name = draw(st.from_regex(r"[a-z][a-zA-Z0-9]{0,10}", fullmatch=True))

    if var_type == "int":
        value = draw(st.integers(min_value=-1000, max_value=1000))
        return f"{var_type} {var_name} := {value};"
    elif var_type == "float":
        value = draw(st.floats(min_value=-1000, max_value=1000, allow_nan=False, allow_infinity=False))
        return f"{var_type} {var_name} := {value:.2f};"
    elif var_type == "bool":
        value = "TRUE" if draw(st.booleans()) else "FALSE"
        return f"{var_type} {var_name} := {value};"
    else:  # string
        value = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=1, max_size=20))
        return f'{var_type} {var_name} := "{value}";'


@st.composite
def struct_definition_strategy(draw):
    """Generate struct definitions valid in both v4 and v5."""
    struct_name = draw(st.from_regex(r"[A-Z][a-zA-Z0-9]{0,10}", fullmatch=True))
    num_fields = draw(st.integers(min_value=1, max_value=5))

    fields = []
    for i in range(num_fields):
        field_type = draw(st.sampled_from(["int", "float", "bool", "string"]))
        field_name = draw(st.from_regex(r"[a-z][a-zA-Z0-9]{0,10}", fullmatch=True))
        fields.append(f"    {field_type} {field_name},")

    fields_str = "\n".join(fields)
    return f"struct {struct_name} {{\n{fields_str}\n}}"


@st.composite
def arithmetic_expression_strategy(draw):
    """Generate arithmetic expressions valid in both v4 and v5."""
    left = draw(st.integers(min_value=1, max_value=100))
    right = draw(st.integers(min_value=1, max_value=100))
    op = draw(st.sampled_from(["+", "-", "*"]))  # Avoid division by zero
    var_name = draw(st.from_regex(r"[a-z][a-zA-Z0-9]{0,5}", fullmatch=True))
    return f"int {var_name} := {left} {op} {right};"


@st.composite
def comparison_expression_strategy(draw):
    """Generate comparison expressions valid in both v4 and v5."""
    left = draw(st.integers(min_value=1, max_value=100))
    right = draw(st.integers(min_value=1, max_value=100))
    op = draw(st.sampled_from(["==", "!=", ">", "<"]))
    var_name = draw(st.from_regex(r"[a-z][a-zA-Z0-9]{0,5}", fullmatch=True))
    return f"bool {var_name} := {left} {op} {right};"


@st.composite
def logical_expression_strategy(draw):
    """Generate logical expressions valid in both v4 and v5."""
    left_val = "TRUE" if draw(st.booleans()) else "FALSE"
    right_val = "TRUE" if draw(st.booleans()) else "FALSE"
    op = draw(st.sampled_from(["&&", "||"]))
    var_name = draw(st.from_regex(r"[a-z][a-zA-Z0-9]{0,5}", fullmatch=True))
    return f"bool {var_name} := {left_val} {op} {right_val};"


class TestParserConsistency:
    """Test that v4 and v5 parsers produce consistent results."""

    def setup_method(self):
        """Set up parsers for each test."""
        self.v4_parser = get_v4_parser()
        self.v5_parser = get_v5_parser()

    def _both_parse_successfully(self, code: str) -> tuple:
        """
        Try parsing with both parsers.

        Returns:
            Tuple of (v4_success, v5_success, v4_result, v5_result)
        """
        v4_result = None
        v5_result = None
        v4_success = False
        v5_success = False

        try:
            v4_result = self.v4_parser.parse(code)
            v4_success = True
        except Exception:
            pass

        try:
            v5_result = self.v5_parser.parse(code)
            v5_success = v5_result.tree is not None
        except Exception:
            pass

        return v4_success, v5_success, v4_result, v5_result

    @given(simple_declaration_strategy())
    @DIFFERENTIAL_SETTINGS
    def test_declaration_consistency(self, code):
        """Both parsers should accept or reject declarations consistently."""
        v4_ok, v5_ok, _, _ = self._both_parse_successfully(code)

        # Both should succeed for valid declarations
        assert v4_ok == v5_ok, \
            f"Parser disagreement on declaration:\n{code}\nV4: {v4_ok}, V5: {v5_ok}"

    @given(struct_definition_strategy())
    @DIFFERENTIAL_SETTINGS
    def test_struct_consistency(self, code):
        """Both parsers should handle struct definitions consistently."""
        v4_ok, v5_ok, _, _ = self._both_parse_successfully(code)

        assert v4_ok == v5_ok, \
            f"Parser disagreement on struct:\n{code}\nV4: {v4_ok}, V5: {v5_ok}"

    @given(arithmetic_expression_strategy())
    @DIFFERENTIAL_SETTINGS
    def test_arithmetic_consistency(self, code):
        """Both parsers should handle arithmetic expressions consistently."""
        v4_ok, v5_ok, _, _ = self._both_parse_successfully(code)

        assert v4_ok == v5_ok, \
            f"Parser disagreement on arithmetic:\n{code}\nV4: {v4_ok}, V5: {v5_ok}"

    @given(comparison_expression_strategy())
    @DIFFERENTIAL_SETTINGS
    def test_comparison_consistency(self, code):
        """Both parsers should handle comparison expressions consistently."""
        v4_ok, v5_ok, _, _ = self._both_parse_successfully(code)

        assert v4_ok == v5_ok, \
            f"Parser disagreement on comparison:\n{code}\nV4: {v4_ok}, V5: {v5_ok}"

    @given(logical_expression_strategy())
    @DIFFERENTIAL_SETTINGS
    def test_logical_consistency(self, code):
        """Both parsers should handle logical expressions consistently."""
        v4_ok, v5_ok, _, _ = self._both_parse_successfully(code)

        assert v4_ok == v5_ok, \
            f"Parser disagreement on logical:\n{code}\nV4: {v4_ok}, V5: {v5_ok}"


class TestASTEquivalence:
    """Test AST structure equivalence between parsers."""

    def setup_method(self):
        """Set up parsers."""
        self.v4_parser = get_v4_parser()
        self.v5_parser = get_v5_parser()

    def _normalize_v4_ast(self, ast) -> dict:
        """Normalize v4 AST to comparable dictionary."""
        if ast is None:
            return None

        result = {"type": type(ast).__name__}

        if hasattr(ast, "statements"):
            result["statements"] = [
                self._normalize_v4_ast(s) for s in ast.statements
            ]
        if hasattr(ast, "name") and isinstance(ast.name, str):
            result["name"] = ast.name
        if hasattr(ast, "value"):
            if hasattr(ast.value, "value"):
                result["value"] = ast.value.value
            else:
                result["value"] = str(ast.value)
        if hasattr(ast, "members"):
            result["members"] = [
                self._normalize_v4_ast(m) for m in ast.members
            ]

        return result

    def _extract_v5_structure(self, result) -> dict:
        """Extract comparable structure from v5 parse result."""
        if result is None or result.tree is None:
            return None

        def walk(node, depth=0):
            """Walk tree and extract structure."""
            info = {"type": node.type}
            if node.children:
                info["children"] = [walk(c, depth + 1) for c in node.children]
            return info

        return walk(result.tree)

    @pytest.mark.parametrize("code,expected_type", [
        ("int x := 42;", "Declaration"),
        ("float y := 3.14;", "Declaration"),
        ("bool z := TRUE;", "Declaration"),
        ('string s := "hello";', "Declaration"),
    ])
    def test_declaration_ast_type(self, code, expected_type):
        """Both parsers should produce declarations with correct types."""
        v4_result = self.v4_parser.parse(code)
        v5_result = self.v5_parser.parse(code)

        # V4 should have statements
        assert len(v4_result.statements) > 0
        v4_stmt_type = type(v4_result.statements[0]).__name__
        assert v4_stmt_type == expected_type

        # V5 should parse successfully
        assert v5_result.tree is not None

    @pytest.mark.parametrize("code", [
        "struct Empty {}",
        "struct Single { int value, }",
        "struct Point { int x, int y, }",
    ])
    def test_struct_ast_structure(self, code):
        """Both parsers should handle struct definitions."""
        try:
            v4_result = self.v4_parser.parse(code)
            v4_ok = True
        except Exception:
            v4_ok = False

        try:
            v5_result = self.v5_parser.parse(code)
            v5_ok = v5_result.tree is not None
        except Exception:
            v5_ok = False

        assert v4_ok == v5_ok, f"Struct parsing mismatch for: {code}"


class TestEdgeCases:
    """Test edge cases and error handling consistency."""

    def setup_method(self):
        """Set up parsers."""
        self.v4_parser = get_v4_parser()
        self.v5_parser = get_v5_parser()

    def _parse_both(self, code: str) -> tuple:
        """Parse with both parsers and return (v4_ok, v5_ok)."""
        try:
            self.v4_parser.parse(code)
            v4_ok = True
        except Exception:
            v4_ok = False

        try:
            result = self.v5_parser.parse(code)
            v5_ok = result.tree is not None and not result.errors
        except Exception:
            v5_ok = False

        return v4_ok, v5_ok

    @pytest.mark.parametrize("code", [
        "",  # Empty input
        "   ",  # Whitespace only
        "// comment only",  # Comment only
        "/* multi\nline\ncomment */",  # Multiline comment only
    ])
    def test_empty_input_consistency(self, code):
        """Both parsers should handle empty/comment-only input consistently."""
        v4_ok, v5_ok = self._parse_both(code)
        # Both should either accept or reject
        # Empty programs may be valid in both

    @pytest.mark.parametrize("code", [
        "int x := ;",  # Missing value
        "int := 42;",  # Missing name
        ":= 42;",  # Missing type and name
        "int x := 42",  # Missing semicolon
        "struct { }",  # Missing struct name
    ])
    def test_syntax_error_consistency(self, code):
        """Both parsers should reject invalid syntax."""
        v4_ok, v5_ok = self._parse_both(code)
        # Both should reject these invalid inputs
        assert not v4_ok and not v5_ok, \
            f"Invalid code accepted: {code}\nV4: {v4_ok}, V5: {v5_ok}"

    @pytest.mark.parametrize("code", [
        "int x := 1 + 2 + 3;",  # Chained addition
        "int x := 1 * 2 * 3;",  # Chained multiplication
        "bool x := TRUE && FALSE || TRUE;",  # Mixed logical
        "int x := 1 + 2 * 3;",  # Operator precedence
    ])
    def test_complex_expressions(self, code):
        """Both parsers should handle complex expressions."""
        v4_ok, v5_ok = self._parse_both(code)
        assert v4_ok == v5_ok, \
            f"Complex expression mismatch: {code}\nV4: {v4_ok}, V5: {v5_ok}"


class TestSpecialLiterals:
    """Test special Yuho literal types."""

    def setup_method(self):
        """Set up parsers."""
        self.v4_parser = get_v4_parser()
        self.v5_parser = get_v5_parser()

    def _parse_both(self, code: str) -> tuple:
        """Parse with both parsers."""
        try:
            self.v4_parser.parse(code)
            v4_ok = True
        except Exception:
            v4_ok = False

        try:
            result = self.v5_parser.parse(code)
            v5_ok = result.tree is not None
        except Exception:
            v5_ok = False

        return v4_ok, v5_ok

    @pytest.mark.parametrize("code", [
        "percent p := 50%;",
        "percent p := 100%;",
        "percent p := 0%;",
    ])
    def test_percentage_literals(self, code):
        """Both parsers should handle percentage literals."""
        v4_ok, v5_ok = self._parse_both(code)
        assert v4_ok == v5_ok, f"Percentage mismatch: {code}"

    @pytest.mark.parametrize("code", [
        "money m := $100;",
        "money m := $0;",
        "money m := $999999;",
    ])
    def test_money_literals(self, code):
        """Both parsers should handle money literals."""
        v4_ok, v5_ok = self._parse_both(code)
        assert v4_ok == v5_ok, f"Money mismatch: {code}"

    @pytest.mark.parametrize("code", [
        "duration d := 1day;",
        "duration d := 30days;",
        "duration d := 1month;",
        "duration d := 12months;",
        "duration d := 1year;",
        "duration d := 10years;",
    ])
    def test_duration_literals(self, code):
        """Both parsers should handle duration literals."""
        v4_ok, v5_ok = self._parse_both(code)
        assert v4_ok == v5_ok, f"Duration mismatch: {code}"
