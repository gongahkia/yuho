"""
Tests verifying interpreter behavior matches the formal semantics
defined in doc/FORMAL_SEMANTICS.md.
"""

import pytest
from decimal import Decimal
from yuho.eval.interpreter import (
    Interpreter,
    Environment,
    Value,
    StructInstance,
    InterpreterError,
    AssertionError_,
)
from yuho.ast.nodes import (
    IntLit,
    FloatLit,
    BoolLit,
    StringLit,
    MoneyNode,
    PercentNode,
    DateNode,
    DurationNode,
    Currency,
    BinaryExprNode,
    UnaryExprNode,
    IdentifierNode,
    PassExprNode,
    MatchExprNode,
    MatchArm,
    WildcardPattern,
    LiteralPattern,
    BindingPattern,
    FunctionDefNode,
    ParamDef,
    Block,
    ReturnStmt,
    VariableDecl,
    BuiltinType,
    AssertStmt,
    StructDefNode,
    FieldDef,
    StructLiteralNode,
    FieldAssignment,
    FieldAccessNode,
    ModuleNode,
)
from datetime import date


class TestLiteralEvaluation:
    """E-Int, E-Float, E-True, E-False, E-String, E-Pass rules."""

    def test_int_literal(self):
        interp = Interpreter()
        v = interp.visit(IntLit(value=42))
        assert v.raw == 42 and v.type_tag == "int"

    def test_float_literal(self):
        interp = Interpreter()
        v = interp.visit(FloatLit(value=3.14))
        assert v.raw == 3.14 and v.type_tag == "float"

    def test_bool_true(self):
        interp = Interpreter()
        v = interp.visit(BoolLit(value=True))
        assert v.raw is True and v.type_tag == "bool"

    def test_bool_false(self):
        interp = Interpreter()
        v = interp.visit(BoolLit(value=False))
        assert v.raw is False and v.type_tag == "bool"

    def test_string_literal(self):
        interp = Interpreter()
        v = interp.visit(StringLit(value="hello"))
        assert v.raw == "hello" and v.type_tag == "string"

    def test_pass_expr(self):
        interp = Interpreter()
        v = interp.visit(PassExprNode())
        assert v.raw is None and v.type_tag == "none"

    def test_money_literal(self):
        interp = Interpreter()
        v = interp.visit(MoneyNode(currency=Currency.SGD, amount=Decimal("100.50")))
        assert v.raw == Decimal("100.50") and v.type_tag == "money"

    def test_duration_literal(self):
        interp = Interpreter()
        d = DurationNode(years=5, months=3)
        v = interp.visit(d)
        assert v.type_tag == "duration"
        assert v.raw.years == 5 and v.raw.months == 3


class TestArithmeticSemantics:
    """E-BinOp rules for arithmetic."""

    def test_int_addition(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=2), operator="+", right=IntLit(value=3))
        v = interp.visit(expr)
        assert v.raw == 5 and v.type_tag == "int"

    def test_int_subtraction(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=10), operator="-", right=IntLit(value=4))
        assert interp.visit(expr).raw == 6

    def test_int_multiplication(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=3), operator="*", right=IntLit(value=7))
        assert interp.visit(expr).raw == 21

    def test_int_division(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=10), operator="/", right=IntLit(value=3))
        assert interp.visit(expr).raw == 3  # integer division

    def test_float_promotion(self):
        """T-ArithFloat: int + float -> float."""
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=2), operator="+", right=FloatLit(value=1.5))
        v = interp.visit(expr)
        assert v.raw == 3.5 and v.type_tag == "float"

    def test_division_by_zero(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=1), operator="/", right=IntLit(value=0))
        with pytest.raises(InterpreterError, match="Division by zero"):
            interp.visit(expr)

    def test_modulo(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=10), operator="%", right=IntLit(value=3))
        assert interp.visit(expr).raw == 1


class TestComparisonSemantics:
    """T-Compare rules."""

    def test_equality(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=5), operator="==", right=IntLit(value=5))
        assert interp.visit(expr).raw is True

    def test_inequality(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=5), operator="!=", right=IntLit(value=3))
        assert interp.visit(expr).raw is True

    def test_less_than(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=3), operator="<", right=IntLit(value=5))
        assert interp.visit(expr).raw is True

    def test_greater_equal(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=IntLit(value=5), operator=">=", right=IntLit(value=5))
        assert interp.visit(expr).raw is True

    def test_string_equality(self):
        interp = Interpreter()
        expr = BinaryExprNode(
            left=StringLit(value="abc"), operator="==", right=StringLit(value="abc")
        )
        assert interp.visit(expr).raw is True


class TestLogicSemantics:
    """T-Logic rules with short-circuit."""

    def test_and_true(self):
        interp = Interpreter()
        expr = BinaryExprNode(left=BoolLit(value=True), operator="&&", right=BoolLit(value=True))
        assert interp.visit(expr).raw is True

    def test_and_short_circuit(self):
        """&& should not evaluate right side if left is false."""
        interp = Interpreter()
        # if && evaluates right, it would error on undefined var
        expr = BinaryExprNode(
            left=BoolLit(value=False), operator="&&", right=IdentifierNode(name="undefined_var")
        )
        v = interp.visit(expr)
        assert v.raw is False

    def test_or_short_circuit(self):
        """|| should not evaluate right side if left is true."""
        interp = Interpreter()
        expr = BinaryExprNode(
            left=BoolLit(value=True), operator="||", right=IdentifierNode(name="undefined_var")
        )
        v = interp.visit(expr)
        assert v.raw is True


class TestUnarySemantics:
    """E-Not, E-Neg rules."""

    def test_not(self):
        interp = Interpreter()
        expr = UnaryExprNode(operator="!", operand=BoolLit(value=True))
        assert interp.visit(expr).raw is False

    def test_negate_int(self):
        interp = Interpreter()
        expr = UnaryExprNode(operator="-", operand=IntLit(value=42))
        assert interp.visit(expr).raw == -42


class TestVariableSemantics:
    """E-Var, E-VarDecl, E-Assign rules."""

    def test_variable_declaration(self):
        interp = Interpreter()
        decl = VariableDecl(
            type_annotation=BuiltinType(name="int"),
            name="x",
            value=IntLit(value=10),
        )
        interp.visit(decl)
        assert interp.env.get("x").raw == 10

    def test_variable_lookup(self):
        interp = Interpreter()
        interp.env.set("y", Value(42, "int"))
        v = interp.visit(IdentifierNode(name="y"))
        assert v.raw == 42

    def test_undefined_variable(self):
        interp = Interpreter()
        with pytest.raises(InterpreterError, match="Undefined variable"):
            interp.visit(IdentifierNode(name="nonexistent"))


class TestMatchSemantics:
    """E-Match rules with pattern matching."""

    def test_wildcard_match(self):
        interp = Interpreter()
        expr = MatchExprNode(
            scrutinee=IntLit(value=42),
            arms=(MatchArm(pattern=WildcardPattern(), body=StringLit(value="matched")),),
        )
        v = interp.visit(expr)
        assert v.raw == "matched"

    def test_literal_match(self):
        interp = Interpreter()
        expr = MatchExprNode(
            scrutinee=IntLit(value=1),
            arms=(
                MatchArm(
                    pattern=LiteralPattern(literal=IntLit(value=1)), body=StringLit(value="one")
                ),
                MatchArm(pattern=WildcardPattern(), body=StringLit(value="other")),
            ),
        )
        v = interp.visit(expr)
        assert v.raw == "one"

    def test_binding_match(self):
        interp = Interpreter()
        expr = MatchExprNode(
            scrutinee=IntLit(value=99),
            arms=(
                MatchArm(
                    pattern=BindingPattern(name="x"),
                    body=IdentifierNode(name="x"),
                ),
            ),
        )
        v = interp.visit(expr)
        assert v.raw == 99

    def test_guard_match(self):
        interp = Interpreter()
        expr = MatchExprNode(
            scrutinee=IntLit(value=5),
            arms=(
                MatchArm(
                    pattern=BindingPattern(name="n"),
                    guard=BinaryExprNode(
                        left=IdentifierNode(name="n"),
                        operator=">",
                        right=IntLit(value=3),
                    ),
                    body=StringLit(value="big"),
                ),
                MatchArm(pattern=WildcardPattern(), body=StringLit(value="small")),
            ),
        )
        v = interp.visit(expr)
        assert v.raw == "big"


class TestFunctionSemantics:
    """E-Call, E-Return rules."""

    def test_function_call(self):
        interp = Interpreter()
        fn = FunctionDefNode(
            name="double",
            params=(ParamDef(type_annotation=BuiltinType(name="int"), name="x"),),
            return_type=BuiltinType(name="int"),
            body=Block(
                statements=(
                    ReturnStmt(
                        value=BinaryExprNode(
                            left=IdentifierNode(name="x"),
                            operator="*",
                            right=IntLit(value=2),
                        )
                    ),
                )
            ),
        )
        interp.env.function_defs["double"] = fn
        from yuho.ast.nodes import FunctionCallNode

        call = FunctionCallNode(
            callee=IdentifierNode(name="double"),
            args=(IntLit(value=21),),
        )
        v = interp.visit(call)
        assert v.raw == 42


class TestStructSemantics:
    """T-StructLit, E-Field rules."""

    def test_struct_creation(self):
        interp = Interpreter()
        lit = StructLiteralNode(
            struct_name="Person",
            field_values=(
                FieldAssignment(name="name", value=StringLit(value="Alice")),
                FieldAssignment(name="age", value=IntLit(value=30)),
            ),
        )
        v = interp.visit(lit)
        assert v.type_tag == "struct"
        assert isinstance(v.raw, StructInstance)
        assert v.raw.type_name == "Person"

    def test_field_access(self):
        interp = Interpreter()
        lit = StructLiteralNode(
            struct_name="Point",
            field_values=(
                FieldAssignment(name="x", value=IntLit(value=10)),
                FieldAssignment(name="y", value=IntLit(value=20)),
            ),
        )
        interp.env.set("pt", interp.visit(lit))
        access = FieldAccessNode(base=IdentifierNode(name="pt"), field_name="x")
        v = interp.visit(access)
        assert v.raw == 10


class TestAssertSemantics:
    """E-AssertPass, E-AssertFail rules."""

    def test_assert_pass(self):
        interp = Interpreter()
        stmt = AssertStmt(condition=BoolLit(value=True))
        v = interp.visit(stmt)
        assert v.raw is True

    def test_assert_fail(self):
        interp = Interpreter()
        stmt = AssertStmt(condition=BoolLit(value=False))
        with pytest.raises(AssertionError_):
            interp.visit(stmt)

    def test_assert_with_message(self):
        interp = Interpreter()
        stmt = AssertStmt(condition=BoolLit(value=False), message=StringLit(value="custom msg"))
        with pytest.raises(AssertionError_, match="custom msg"):
            interp.visit(stmt)


class TestModuleInterpret:
    """Full module interpretation."""

    def test_interpret_module(self):
        module = ModuleNode(
            imports=(),
            type_defs=(
                StructDefNode(
                    name="Case",
                    fields=(FieldDef(type_annotation=BuiltinType(name="bool"), name="guilty"),),
                ),
            ),
            function_defs=(),
            statutes=(),
            variables=(
                VariableDecl(
                    type_annotation=BuiltinType(name="int"),
                    name="x",
                    value=IntLit(value=42),
                ),
            ),
            assertions=(
                AssertStmt(
                    condition=BinaryExprNode(
                        left=IdentifierNode(name="x"),
                        operator="==",
                        right=IntLit(value=42),
                    )
                ),
            ),
        )
        interp = Interpreter()
        env = interp.interpret(module)
        assert env.get("x").raw == 42
        assert "Case" in env.struct_defs
