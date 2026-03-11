"""
Unit tests covering AST nodes, constant folding, scope analysis,
type checking, interpreter edge cases, transpile target enum, and
source location utilities.

These tests exercise internal APIs directly (no parsing required) and
fill coverage gaps left by the existing property-based / E2E suites.
"""

from __future__ import annotations

import pytest
from datetime import date
from decimal import Decimal

from yuho.ast.nodes import (
    ASTNode,
    ArrayType,
    AssertStmt,
    AssignmentStmt,
    BinaryExprNode,
    BindingPattern,
    Block,
    BoolLit,
    BuiltinType,
    CaseLawNode,
    Currency,
    DateNode,
    DefinitionEntry,
    DurationNode,
    ElementGroupNode,
    ElementNode,
    ExceptionNode,
    ExpressionStmt,
    FieldAccessNode,
    FieldAssignment,
    FieldDef,
    FieldPattern,
    FloatLit,
    FunctionCallNode,
    FunctionDefNode,
    GenericType,
    IdentifierNode,
    IllustrationNode,
    ImportNode,
    IndexAccessNode,
    IntLit,
    LiteralPattern,
    MatchArm,
    MatchExprNode,
    ModuleNode,
    MoneyNode,
    NamedType,
    OptionalType,
    ParamDef,
    PassExprNode,
    PassStmt,
    PenaltyNode,
    PercentNode,
    ReferencingStmt,
    ReturnStmt,
    StatuteNode,
    StringLit,
    StructDefNode,
    StructLiteralNode,
    StructPattern,
    UnaryExprNode,
    VariableDecl,
    WildcardPattern,
)
from yuho.parser.source_location import SourceLocation


# =========================================================================
# 1. Currency.from_symbol mapping
# =========================================================================


class TestCurrencyEnum:
    """Tests for Currency.from_symbol edge cases."""

    def test_dollar_sign_defaults_to_sgd(self):
        assert Currency.from_symbol("$") == Currency.SGD

    def test_named_currency_codes(self):
        assert Currency.from_symbol("EUR") == Currency.EUR
        assert Currency.from_symbol("GBP") == Currency.GBP
        assert Currency.from_symbol("JPY") == Currency.JPY

    def test_unknown_symbol_defaults_to_usd(self):
        assert Currency.from_symbol("XYZ") == Currency.USD
        assert Currency.from_symbol("") == Currency.USD

    def test_currency_symbols(self):
        assert Currency.from_symbol("£") == Currency.GBP
        assert Currency.from_symbol("€") == Currency.EUR
        assert Currency.from_symbol("¥") == Currency.JPY
        assert Currency.from_symbol("₹") == Currency.INR


# =========================================================================
# 2. DurationNode helpers
# =========================================================================


class TestDurationNode:
    """Tests for DurationNode utility methods."""

    def test_total_days_basic(self):
        d = DurationNode(years=1, months=0, days=0)
        assert d.total_days() == 365

    def test_total_days_mixed(self):
        d = DurationNode(years=1, months=6, days=15)
        assert d.total_days() == 365 + 180 + 15

    def test_total_days_zero(self):
        d = DurationNode()
        assert d.total_days() == 0

    def test_str_singular(self):
        d = DurationNode(years=1, months=1, days=1)
        s = str(d)
        assert "1 year" in s and "years" not in s
        assert "1 month" in s and "months" not in s
        assert "1 day" in s and "days" not in s

    def test_str_plural(self):
        d = DurationNode(years=3, months=2, days=10)
        s = str(d)
        assert "3 years" in s
        assert "2 months" in s
        assert "10 days" in s

    def test_str_empty(self):
        d = DurationNode()
        assert str(d) == "0 days"


# =========================================================================
# 3. PercentNode validation
# =========================================================================


class TestPercentNode:
    """Tests for PercentNode value range validation."""

    def test_valid_range(self):
        p = PercentNode(value=Decimal("50"))
        assert p.value == Decimal("50")

    def test_zero_and_hundred(self):
        assert PercentNode(value=Decimal("0")).value == Decimal("0")
        assert PercentNode(value=Decimal("100")).value == Decimal("100")

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="0-100"):
            PercentNode(value=Decimal("101"))
        with pytest.raises(ValueError, match="0-100"):
            PercentNode(value=Decimal("-1"))

    def test_auto_decimal_conversion(self):
        p = PercentNode(value=50)
        assert isinstance(p.value, Decimal)


# =========================================================================
# 4. MoneyNode auto-conversion
# =========================================================================


class TestMoneyNode:
    """Tests for MoneyNode Decimal auto-conversion."""

    def test_auto_decimal_conversion(self):
        m = MoneyNode(currency=Currency.SGD, amount=100)
        assert isinstance(m.amount, Decimal)
        assert m.amount == Decimal("100")

    def test_decimal_passthrough(self):
        m = MoneyNode(currency=Currency.USD, amount=Decimal("99.99"))
        assert m.amount == Decimal("99.99")


# =========================================================================
# 5. DateNode.from_iso8601
# =========================================================================


class TestDateNode:
    """Tests for DateNode factory method."""

    def test_from_iso8601(self):
        d = DateNode.from_iso8601("2024-03-15")
        assert d.value == date(2024, 3, 15)

    def test_invalid_iso8601_raises(self):
        with pytest.raises(ValueError):
            DateNode.from_iso8601("not-a-date")


# =========================================================================
# 6. AST Node children() traversal
# =========================================================================


class TestASTNodeChildren:
    """Tests for children() on various AST nodes."""

    def test_binary_expr_children(self):
        left = IntLit(value=1)
        right = IntLit(value=2)
        expr = BinaryExprNode(left=left, operator="+", right=right)
        assert expr.children() == [left, right]

    def test_unary_expr_children(self):
        operand = BoolLit(value=True)
        expr = UnaryExprNode(operator="!", operand=operand)
        assert expr.children() == [operand]

    def test_function_def_children_includes_return_type(self):
        ret = BuiltinType(name="int")
        body = Block(statements=())
        fn = FunctionDefNode(name="f", params=(), return_type=ret, body=body)
        children = fn.children()
        assert ret in children
        assert body in children

    def test_function_def_children_no_return_type(self):
        body = Block(statements=())
        fn = FunctionDefNode(name="f", params=(), return_type=None, body=body)
        assert body in fn.children()

    def test_match_arm_children_with_guard(self):
        pattern = WildcardPattern()
        guard = BoolLit(value=True)
        body = StringLit(value="x")
        arm = MatchArm(pattern=pattern, guard=guard, body=body)
        children = arm.children()
        assert pattern in children
        assert guard in children
        assert body in children

    def test_match_arm_children_no_guard(self):
        pattern = WildcardPattern()
        body = StringLit(value="x")
        arm = MatchArm(pattern=pattern, body=body)
        children = arm.children()
        assert len(children) == 2
        assert pattern in children

    def test_module_node_children(self):
        imp = ImportNode(path="foo", imported_names=())
        struct = StructDefNode(name="S", fields=())
        fn = FunctionDefNode(name="f", params=(), return_type=None, body=Block(statements=()))
        mod = ModuleNode(
            imports=(imp,), type_defs=(struct,), function_defs=(fn,),
            statutes=(), variables=(), references=(), assertions=(),
        )
        children = mod.children()
        assert imp in children
        assert struct in children
        assert fn in children

    def test_optional_type_children(self):
        inner = BuiltinType(name="int")
        opt = OptionalType(inner=inner)
        assert opt.children() == [inner]

    def test_array_type_children(self):
        elem = BuiltinType(name="string")
        arr = ArrayType(element_type=elem)
        assert arr.children() == [elem]

    def test_generic_type_children(self):
        t1 = BuiltinType(name="int")
        t2 = BuiltinType(name="string")
        gen = GenericType(base="Map", type_args=(t1, t2))
        assert gen.children() == [t1, t2]

    def test_penalty_node_children(self):
        imp_min = DurationNode(years=1)
        imp_max = DurationNode(years=5)
        penalty = PenaltyNode(imprisonment_min=imp_min, imprisonment_max=imp_max)
        children = penalty.children()
        assert imp_min in children
        assert imp_max in children

    def test_exception_node_children_with_guard(self):
        cond = StringLit(value="provocation")
        effect = StringLit(value="not murder")
        guard = BoolLit(value=True)
        exc = ExceptionNode(label="prov", condition=cond, effect=effect, guard=guard)
        children = exc.children()
        assert cond in children
        assert effect in children
        assert guard in children

    def test_statute_node_children(self):
        title = StringLit(value="Theft")
        elem = ElementNode(element_type="actus_reus", name="taking", description=StringLit(value="taking property"))
        illus = IllustrationNode(label="a", description=StringLit(value="example"))
        statute = StatuteNode(
            section_number="378", title=title, definitions=(),
            elements=(elem,), penalty=None, illustrations=(illus,),
        )
        children = statute.children()
        assert title in children
        assert elem in children
        assert illus in children

    def test_import_node_wildcard(self):
        imp = ImportNode(path="foo", imported_names=("*",))
        assert imp.is_wildcard

    def test_import_node_not_wildcard(self):
        imp = ImportNode(path="foo", imported_names=("Bar",))
        assert not imp.is_wildcard

    def test_struct_literal_get_field(self):
        fa = FieldAssignment(name="x", value=IntLit(value=42))
        sl = StructLiteralNode(struct_name="Foo", field_values=(fa,))
        assert sl.get_field("x") == fa
        assert sl.get_field("nonexistent") is None


# =========================================================================
# 7. SourceLocation utilities
# =========================================================================


class TestSourceLocation:
    """Tests for SourceLocation methods."""

    def test_from_values(self):
        loc = SourceLocation(file="test.yh", line=1, col=1, end_line=1, end_col=10)
        assert loc.file == "test.yh"
        assert loc.line == 1

    def test_contains(self):
        outer = SourceLocation(file="a.yh", line=1, col=1, end_line=10, end_col=1)
        inner = SourceLocation(file="a.yh", line=3, col=1, end_line=5, end_col=1)
        assert outer.contains(inner)
        assert not inner.contains(outer)

    def test_merge(self):
        a = SourceLocation(file="a.yh", line=1, col=1, end_line=3, end_col=5)
        b = SourceLocation(file="a.yh", line=5, col=1, end_line=8, end_col=10)
        merged = SourceLocation.merge(a, b)
        assert merged.line == 1
        assert merged.end_line == 8

    def test_merge_preserves_zero_offset(self):
        a = SourceLocation(file="a.yh", line=1, col=1, end_line=1, end_col=5, offset=0, end_offset=5)
        b = SourceLocation(file="a.yh", line=2, col=1, end_line=2, end_col=3, offset=10, end_offset=13)
        merged = SourceLocation.merge(a, b)
        assert merged.offset == 0
        assert merged.end_offset == 13


# =========================================================================
# 8. Constant folding
# =========================================================================


class TestConstantFolder:
    """Tests for the constant folding optimizer."""

    def test_fold_int_addition(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=IntLit(value=3), operator="+", right=IntLit(value=4))
        result = folder.transform(expr)
        assert isinstance(result, IntLit)
        assert result.value == 7

    def test_fold_int_subtraction(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=IntLit(value=10), operator="-", right=IntLit(value=3))
        result = folder.transform(expr)
        assert isinstance(result, IntLit)
        assert result.value == 7

    def test_fold_int_multiplication(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=IntLit(value=6), operator="*", right=IntLit(value=7))
        result = folder.transform(expr)
        assert isinstance(result, IntLit)
        assert result.value == 42

    def test_fold_int_division(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=IntLit(value=10), operator="/", right=IntLit(value=3))
        result = folder.transform(expr)
        assert isinstance(result, IntLit)
        assert result.value == 3  # integer division

    def test_fold_division_by_zero_left_unchanged(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder(fold_division_by_zero=False)
        expr = BinaryExprNode(left=IntLit(value=1), operator="/", right=IntLit(value=0))
        result = folder.transform(expr)
        assert isinstance(result, BinaryExprNode)  # not folded

    def test_fold_division_by_zero_raises_when_enabled(self):
        from yuho.ast.constant_folder import ConstantFolder, ConstantFoldingError
        folder = ConstantFolder(fold_division_by_zero=True)
        expr = BinaryExprNode(left=IntLit(value=1), operator="/", right=IntLit(value=0))
        with pytest.raises(ConstantFoldingError):
            folder.transform(expr)

    def test_fold_float_arithmetic(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=FloatLit(value=1.5), operator="*", right=FloatLit(value=2.0))
        result = folder.transform(expr)
        assert isinstance(result, FloatLit)
        assert result.value == pytest.approx(3.0)

    def test_fold_bool_and(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=BoolLit(value=True), operator="&&", right=BoolLit(value=False))
        result = folder.transform(expr)
        assert isinstance(result, BoolLit)
        assert result.value is False

    def test_fold_bool_or(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=BoolLit(value=False), operator="||", right=BoolLit(value=True))
        result = folder.transform(expr)
        assert isinstance(result, BoolLit)
        assert result.value is True

    def test_fold_string_concat(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=StringLit(value="hello "), operator="+", right=StringLit(value="world"))
        result = folder.transform(expr)
        assert isinstance(result, StringLit)
        assert result.value == "hello world"

    def test_fold_comparison(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=IntLit(value=5), operator=">", right=IntLit(value=3))
        result = folder.transform(expr)
        assert isinstance(result, BoolLit)
        assert result.value is True

    def test_fold_unary_negation(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = UnaryExprNode(operator="-", operand=IntLit(value=42))
        result = folder.transform(expr)
        assert isinstance(result, IntLit)
        assert result.value == -42

    def test_fold_unary_not(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = UnaryExprNode(operator="!", operand=BoolLit(value=True))
        result = folder.transform(expr)
        assert isinstance(result, BoolLit)
        assert result.value is False

    def test_fold_nested_expression(self):
        from yuho.ast.constant_folder import fold_constants
        # (2 + 3) * 4 -> 5 * 4 -> 20
        inner = BinaryExprNode(left=IntLit(value=2), operator="+", right=IntLit(value=3))
        outer = BinaryExprNode(left=inner, operator="*", right=IntLit(value=4))
        result = fold_constants(outer)
        assert isinstance(result, IntLit)
        assert result.value == 20

    def test_fold_mixed_int_float(self):
        from yuho.ast.constant_folder import ConstantFolder
        folder = ConstantFolder()
        expr = BinaryExprNode(left=IntLit(value=3), operator="+", right=FloatLit(value=0.5))
        result = folder.transform(expr)
        assert isinstance(result, FloatLit)
        assert result.value == pytest.approx(3.5)


# =========================================================================
# 9. Scope analysis
# =========================================================================


class TestScopeAnalysis:
    """Tests for scope analysis on directly-constructed ASTs."""

    def _analyze(self, module: ModuleNode):
        from yuho.ast.scope_analysis import ScopeAnalysisVisitor
        visitor = ScopeAnalysisVisitor()
        return module.accept(visitor)

    def test_struct_defines_symbol(self):
        struct = StructDefNode(
            name="Foo",
            fields=(FieldDef(type_annotation=BuiltinType(name="int"), name="x"),),
        )
        mod = ModuleNode(imports=(), type_defs=(struct,), function_defs=(), statutes=(), variables=())
        result = self._analyze(mod)
        assert result.is_valid
        sym = result.root_scope.lookup("Foo")
        assert sym is not None
        assert sym.kind.name == "STRUCT"

    def test_duplicate_struct_is_error(self):
        s1 = StructDefNode(name="Foo", fields=())
        s2 = StructDefNode(name="Foo", fields=())
        mod = ModuleNode(imports=(), type_defs=(s1, s2), function_defs=(), statutes=(), variables=())
        result = self._analyze(mod)
        assert result.has_errors
        assert any("already declared" in e.message for e in result.errors)

    def test_function_params_in_scope(self):
        param = ParamDef(type_annotation=BuiltinType(name="int"), name="x")
        body = Block(statements=(
            ReturnStmt(value=IdentifierNode(name="x")),
        ))
        fn = FunctionDefNode(name="f", params=(param,), return_type=BuiltinType(name="int"), body=body)
        mod = ModuleNode(imports=(), type_defs=(), function_defs=(fn,), statutes=(), variables=())
        result = self._analyze(mod)
        assert result.is_valid

    def test_undeclared_identifier_error(self):
        body = Block(statements=(
            ExpressionStmt(expression=IdentifierNode(name="unknown_var")),
        ))
        fn = FunctionDefNode(name="f", params=(), return_type=None, body=body)
        mod = ModuleNode(imports=(), type_defs=(), function_defs=(fn,), statutes=(), variables=())
        result = self._analyze(mod)
        assert result.has_errors
        assert any("Undeclared" in e.message and "unknown_var" in e.message for e in result.errors)

    def test_function_forward_reference_ok(self):
        """Functions should be able to call each other regardless of definition order."""
        body_a = Block(statements=(
            ExpressionStmt(expression=FunctionCallNode(
                callee=IdentifierNode(name="b"), args=(),
            )),
        ))
        body_b = Block(statements=(ReturnStmt(value=IntLit(value=1)),))
        fn_a = FunctionDefNode(name="a", params=(), return_type=None, body=body_a)
        fn_b = FunctionDefNode(name="b", params=(), return_type=BuiltinType(name="int"), body=body_b)
        mod = ModuleNode(imports=(), type_defs=(), function_defs=(fn_a, fn_b), statutes=(), variables=())
        result = self._analyze(mod)
        assert result.is_valid


# =========================================================================
# 10. Interpreter
# =========================================================================


class TestInterpreterEdgeCases:
    """Tests for interpreter edge cases not covered by test_semantics.py."""

    def _interp(self):
        from yuho.eval.interpreter import Interpreter, Environment
        return Interpreter()

    def test_string_concatenation(self):
        from yuho.eval.interpreter import Value
        interp = self._interp()
        expr = BinaryExprNode(left=StringLit(value="foo"), operator="+", right=StringLit(value="bar"))
        result = interp.visit(expr)
        assert result.raw == "foobar"
        assert result.type_tag == "string"

    def test_modulo_operation(self):
        interp = self._interp()
        expr = BinaryExprNode(left=IntLit(value=10), operator="%", right=IntLit(value=3))
        result = interp.visit(expr)
        assert result.raw == 1

    def test_modulo_by_zero_raises(self):
        from yuho.eval.interpreter import InterpreterError
        interp = self._interp()
        expr = BinaryExprNode(left=IntLit(value=10), operator="%", right=IntLit(value=0))
        with pytest.raises(InterpreterError, match="Modulo by zero"):
            interp.visit(expr)

    def test_division_by_zero_raises(self):
        from yuho.eval.interpreter import InterpreterError
        interp = self._interp()
        expr = BinaryExprNode(left=IntLit(value=10), operator="/", right=IntLit(value=0))
        with pytest.raises(InterpreterError, match="Division by zero"):
            interp.visit(expr)

    def test_integer_division_truncates(self):
        interp = self._interp()
        expr = BinaryExprNode(left=IntLit(value=7), operator="/", right=IntLit(value=2))
        result = interp.visit(expr)
        assert result.raw == 3
        assert result.type_tag == "int"

    def test_float_promotion(self):
        interp = self._interp()
        expr = BinaryExprNode(left=IntLit(value=3), operator="+", right=FloatLit(value=0.14))
        result = interp.visit(expr)
        assert result.type_tag == "float"
        assert result.raw == pytest.approx(3.14)

    def test_short_circuit_and(self):
        """&& should not evaluate right side when left is false."""
        from yuho.eval.interpreter import InterpreterError
        interp = self._interp()
        # right side would error if evaluated (undefined var)
        expr = BinaryExprNode(
            left=BoolLit(value=False),
            operator="&&",
            right=IdentifierNode(name="undefined_var"),
        )
        result = interp.visit(expr)
        assert result.raw is False

    def test_short_circuit_or(self):
        """|| should not evaluate right side when left is true."""
        interp = self._interp()
        expr = BinaryExprNode(
            left=BoolLit(value=True),
            operator="||",
            right=IdentifierNode(name="undefined_var"),
        )
        result = interp.visit(expr)
        assert result.raw is True

    def test_negate_float(self):
        interp = self._interp()
        expr = UnaryExprNode(operator="-", operand=FloatLit(value=3.14))
        result = interp.visit(expr)
        assert result.raw == pytest.approx(-3.14)
        assert result.type_tag == "float"

    def test_undefined_variable_raises(self):
        from yuho.eval.interpreter import InterpreterError
        interp = self._interp()
        with pytest.raises(InterpreterError, match="Undefined variable"):
            interp.visit(IdentifierNode(name="no_such_var"))

    def test_undefined_function_raises(self):
        from yuho.eval.interpreter import InterpreterError
        interp = self._interp()
        call = FunctionCallNode(callee=IdentifierNode(name="no_func"), args=())
        with pytest.raises(InterpreterError, match="Undefined function"):
            interp.visit(call)

    def test_assert_pass(self):
        interp = self._interp()
        stmt = AssertStmt(condition=BoolLit(value=True))
        result = interp.visit(stmt)
        assert result.raw is True

    def test_assert_fail(self):
        from yuho.eval.interpreter import AssertionError_
        interp = self._interp()
        stmt = AssertStmt(condition=BoolLit(value=False))
        with pytest.raises(AssertionError_):
            interp.visit(stmt)

    def test_pass_expr_returns_none(self):
        interp = self._interp()
        result = interp.visit(PassExprNode())
        assert result.type_tag == "none"
        assert result.raw is None

    def test_pass_stmt_returns_none(self):
        interp = self._interp()
        result = interp.visit(PassStmt())
        assert result.type_tag == "none"


# =========================================================================
# 11. Value truthiness
# =========================================================================


class TestValueTruthiness:
    """Tests for Value.is_truthy() across all type tags."""

    def test_bool_true(self):
        from yuho.eval.interpreter import Value
        assert Value(True, "bool").is_truthy() is True

    def test_bool_false(self):
        from yuho.eval.interpreter import Value
        assert Value(False, "bool").is_truthy() is False

    def test_none_is_falsy(self):
        from yuho.eval.interpreter import Value
        assert Value(None, "none").is_truthy() is False

    def test_zero_int_is_falsy(self):
        from yuho.eval.interpreter import Value
        assert Value(0, "int").is_truthy() is False

    def test_nonzero_int_is_truthy(self):
        from yuho.eval.interpreter import Value
        assert Value(42, "int").is_truthy() is True

    def test_empty_string_is_falsy(self):
        from yuho.eval.interpreter import Value
        assert Value("", "string").is_truthy() is False

    def test_nonempty_string_is_truthy(self):
        from yuho.eval.interpreter import Value
        assert Value("hello", "string").is_truthy() is True

    def test_zero_decimal_is_falsy(self):
        from yuho.eval.interpreter import Value
        assert Value(Decimal(0), "money").is_truthy() is False

    def test_nonzero_decimal_is_truthy(self):
        from yuho.eval.interpreter import Value
        assert Value(Decimal("10.50"), "money").is_truthy() is True

    def test_empty_list_is_falsy(self):
        from yuho.eval.interpreter import Value
        assert Value([], "list").is_truthy() is False

    def test_nonempty_list_is_truthy(self):
        from yuho.eval.interpreter import Value
        assert Value([1], "list").is_truthy() is True

    def test_zero_float_is_falsy(self):
        from yuho.eval.interpreter import Value
        assert Value(0.0, "float").is_truthy() is False


# =========================================================================
# 12. Value.from_node factory
# =========================================================================


class TestValueFromNode:
    """Tests for Value.from_node static method."""

    def test_from_int_lit(self):
        from yuho.eval.interpreter import Value
        v = Value.from_node(IntLit(value=42))
        assert v.raw == 42 and v.type_tag == "int"

    def test_from_float_lit(self):
        from yuho.eval.interpreter import Value
        v = Value.from_node(FloatLit(value=3.14))
        assert v.type_tag == "float"

    def test_from_bool_lit(self):
        from yuho.eval.interpreter import Value
        v = Value.from_node(BoolLit(value=True))
        assert v.raw is True and v.type_tag == "bool"

    def test_from_string_lit(self):
        from yuho.eval.interpreter import Value
        v = Value.from_node(StringLit(value="hello"))
        assert v.raw == "hello" and v.type_tag == "string"

    def test_from_pass_expr(self):
        from yuho.eval.interpreter import Value
        v = Value.from_node(PassExprNode())
        assert v.type_tag == "none"

    def test_from_money_node(self):
        from yuho.eval.interpreter import Value
        v = Value.from_node(MoneyNode(currency=Currency.SGD, amount=Decimal("99.99")))
        assert v.type_tag == "money"
        assert v.raw == Decimal("99.99")

    def test_from_unsupported_raises(self):
        from yuho.eval.interpreter import Value, InterpreterError
        with pytest.raises(InterpreterError):
            Value.from_node(IdentifierNode(name="x"))


# =========================================================================
# 13. Environment chained scope
# =========================================================================


class TestEnvironment:
    """Tests for Environment scope chaining."""

    def test_child_inherits_parent(self):
        from yuho.eval.interpreter import Environment, Value
        parent = Environment()
        parent.set("x", Value(10, "int"))
        child = parent.child()
        assert child.get("x").raw == 10

    def test_child_shadows_parent(self):
        from yuho.eval.interpreter import Environment, Value
        parent = Environment()
        parent.set("x", Value(10, "int"))
        child = parent.child()
        child.set("x", Value(20, "int"))
        assert child.get("x").raw == 20
        assert parent.get("x").raw == 10

    def test_assign_updates_nearest_scope(self):
        from yuho.eval.interpreter import Environment, Value
        parent = Environment()
        parent.set("x", Value(10, "int"))
        child = parent.child()
        child.assign("x", Value(99, "int"))
        assert parent.get("x").raw == 99

    def test_assign_returns_false_if_not_found(self):
        from yuho.eval.interpreter import Environment, Value
        env = Environment()
        assert env.assign("missing", Value(1, "int")) is False

    def test_get_struct_def_from_parent(self):
        from yuho.eval.interpreter import Environment
        parent = Environment()
        struct = StructDefNode(name="Foo", fields=())
        parent.struct_defs["Foo"] = struct
        child = parent.child()
        assert child.get_struct_def("Foo") is struct

    def test_get_function_def_from_parent(self):
        from yuho.eval.interpreter import Environment
        parent = Environment()
        fn = FunctionDefNode(name="f", params=(), return_type=None, body=Block(statements=()))
        parent.function_defs["f"] = fn
        child = parent.child()
        assert child.get_function_def("f") is fn


# =========================================================================
# 14. TranspileTarget enum
# =========================================================================


class TestTranspileTarget:
    """Tests for TranspileTarget.from_string and file_extension."""

    def test_from_string_aliases(self):
        from yuho.transpile.base import TranspileTarget
        assert TranspileTarget.from_string("json") == TranspileTarget.JSON
        assert TranspileTarget.from_string("jsonld") == TranspileTarget.JSON_LD
        assert TranspileTarget.from_string("json-ld") == TranspileTarget.JSON_LD
        assert TranspileTarget.from_string("en") == TranspileTarget.ENGLISH
        assert TranspileTarget.from_string("tex") == TranspileTarget.LATEX
        assert TranspileTarget.from_string("mmd") == TranspileTarget.MERMAID
        assert TranspileTarget.from_string("gql") == TranspileTarget.GRAPHQL
        assert TranspileTarget.from_string("bib") == TranspileTarget.BIBTEX
        assert TranspileTarget.from_string("compare") == TranspileTarget.COMPARATIVE

    def test_from_string_case_insensitive(self):
        from yuho.transpile.base import TranspileTarget
        assert TranspileTarget.from_string("JSON") == TranspileTarget.JSON
        assert TranspileTarget.from_string("English") == TranspileTarget.ENGLISH

    def test_from_string_unknown_raises(self):
        from yuho.transpile.base import TranspileTarget
        with pytest.raises(ValueError, match="Unknown"):
            TranspileTarget.from_string("foobar")

    def test_file_extensions(self):
        from yuho.transpile.base import TranspileTarget
        assert TranspileTarget.JSON.file_extension == ".json"
        assert TranspileTarget.LATEX.file_extension == ".tex"
        assert TranspileTarget.MERMAID.file_extension == ".mmd"
        assert TranspileTarget.ALLOY.file_extension == ".als"
        assert TranspileTarget.HTML.file_extension == ".html"
        assert TranspileTarget.COMPARATIVE.file_extension == ".md"


# =========================================================================
# 15. Scope: lookup_local vs recursive
# =========================================================================


class TestScopeObject:
    """Tests for the Scope data structure directly."""

    def test_lookup_local_only(self):
        from yuho.ast.scope_analysis import Scope, Symbol, SymbolKind
        parent = Scope(name="module", level=0)
        parent.define(Symbol(name="x", kind=SymbolKind.VARIABLE))
        child = Scope(name="block", parent=parent, level=1)
        assert child.lookup_local("x") is None
        assert child.lookup("x", recursive=True) is not None

    def test_define_duplicate_returns_error(self):
        from yuho.ast.scope_analysis import Scope, Symbol, SymbolKind
        scope = Scope(name="test", level=0)
        scope.define(Symbol(name="x", kind=SymbolKind.VARIABLE, line=1))
        err = scope.define(Symbol(name="x", kind=SymbolKind.VARIABLE, line=5))
        assert err is not None
        assert "already declared" in err

    def test_all_symbols_merges_parent(self):
        from yuho.ast.scope_analysis import Scope, Symbol, SymbolKind
        parent = Scope(name="module", level=0)
        parent.define(Symbol(name="a", kind=SymbolKind.VARIABLE))
        child = Scope(name="block", parent=parent, level=1)
        child.define(Symbol(name="b", kind=SymbolKind.VARIABLE))
        all_syms = child.all_symbols()
        assert "a" in all_syms
        assert "b" in all_syms


# =========================================================================
# 16. Interpreter: struct instantiation and field access
# =========================================================================


class TestInterpreterStructs:
    """Tests for interpreter struct creation and field access."""

    def test_struct_literal_creates_instance(self):
        from yuho.eval.interpreter import Interpreter, StructInstance
        interp = Interpreter()
        fa = FieldAssignment(name="x", value=IntLit(value=42))
        sl = StructLiteralNode(struct_name="Point", field_values=(fa,))
        result = interp.visit(sl)
        assert result.type_tag == "struct"
        assert isinstance(result.raw, StructInstance)
        assert result.raw.fields["x"].raw == 42

    def test_struct_field_access(self):
        from yuho.eval.interpreter import Interpreter, Value, StructInstance
        interp = Interpreter()
        inst = StructInstance(type_name="Point", fields={"x": Value(10, "int"), "y": Value(20, "int")})
        interp.env.set("p", Value(inst, "struct"))
        expr = FieldAccessNode(base=IdentifierNode(name="p"), field_name="x")
        result = interp.visit(expr)
        assert result.raw == 10

    def test_struct_missing_field_raises(self):
        from yuho.eval.interpreter import Interpreter, Value, StructInstance, InterpreterError
        interp = Interpreter()
        inst = StructInstance(type_name="Point", fields={"x": Value(10, "int")})
        interp.env.set("p", Value(inst, "struct"))
        expr = FieldAccessNode(base=IdentifierNode(name="p"), field_name="z")
        with pytest.raises(InterpreterError, match="No field 'z'"):
            interp.visit(expr)


# =========================================================================
# 17. Interpreter: match expression evaluation
# =========================================================================


class TestInterpreterMatch:
    """Tests for match expression evaluation in interpreter."""

    def test_wildcard_always_matches(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        match = MatchExprNode(
            scrutinee=IntLit(value=42),
            arms=(MatchArm(pattern=WildcardPattern(), body=StringLit(value="matched")),),
        )
        result = interp.visit(match)
        assert result.raw == "matched"

    def test_literal_match(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        match = MatchExprNode(
            scrutinee=IntLit(value=1),
            arms=(
                MatchArm(pattern=LiteralPattern(literal=IntLit(value=2)), body=StringLit(value="two")),
                MatchArm(pattern=LiteralPattern(literal=IntLit(value=1)), body=StringLit(value="one")),
                MatchArm(pattern=WildcardPattern(), body=StringLit(value="other")),
            ),
        )
        result = interp.visit(match)
        assert result.raw == "one"

    def test_no_match_returns_none(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        match = MatchExprNode(
            scrutinee=IntLit(value=99),
            arms=(
                MatchArm(pattern=LiteralPattern(literal=IntLit(value=1)), body=StringLit(value="one")),
            ),
            ensure_exhaustiveness=False,
        )
        result = interp.visit(match)
        assert result.type_tag == "none"

    def test_binding_pattern_captures_value(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        match = MatchExprNode(
            scrutinee=IntLit(value=42),
            arms=(
                MatchArm(
                    pattern=BindingPattern(name="x"),
                    body=IdentifierNode(name="x"),
                ),
            ),
        )
        result = interp.visit(match)
        assert result.raw == 42

    def test_guard_filters_arms(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        match = MatchExprNode(
            scrutinee=None,
            arms=(
                MatchArm(
                    pattern=LiteralPattern(literal=BoolLit(value=True)),
                    guard=BoolLit(value=False),
                    body=StringLit(value="skipped"),
                ),
                MatchArm(
                    pattern=WildcardPattern(),
                    body=StringLit(value="fallthrough"),
                ),
            ),
        )
        result = interp.visit(match)
        assert result.raw == "fallthrough"


# =========================================================================
# 18. Interpreter: full module interpretation
# =========================================================================


class TestInterpreterModule:
    """Tests for full module interpretation."""

    def test_interpret_registers_statutes(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        statute = StatuteNode(
            section_number="999", title=StringLit(value="Test"),
            definitions=(), elements=(), penalty=None, illustrations=(),
        )
        mod = ModuleNode(imports=(), type_defs=(), function_defs=(), statutes=(statute,), variables=())
        env = interp.interpret(mod)
        assert "999" in env.statutes

    def test_interpret_registers_structs(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        struct = StructDefNode(name="Foo", fields=())
        mod = ModuleNode(imports=(), type_defs=(struct,), function_defs=(), statutes=(), variables=())
        env = interp.interpret(mod)
        assert "Foo" in env.struct_defs

    def test_interpret_registers_functions(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        fn = FunctionDefNode(name="greet", params=(), return_type=None, body=Block(statements=()))
        mod = ModuleNode(imports=(), type_defs=(), function_defs=(fn,), statutes=(), variables=())
        env = interp.interpret(mod)
        assert "greet" in env.function_defs

    def test_interpret_executes_variable_decls(self):
        from yuho.eval.interpreter import Interpreter
        interp = Interpreter()
        var = VariableDecl(type_annotation=BuiltinType(name="int"), name="x", value=IntLit(value=42))
        mod = ModuleNode(imports=(), type_defs=(), function_defs=(), statutes=(), variables=(var,))
        env = interp.interpret(mod)
        assert env.get("x").raw == 42
