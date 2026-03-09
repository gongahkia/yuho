"""Tree-walking interpreter for Yuho."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple
from yuho.ast import nodes
from yuho.ast.visitor import Visitor


# ---------------------------------------------------------------------------
# Control flow / error signals
# ---------------------------------------------------------------------------

class ReturnSignal(Exception):
    """Exception-based control flow for return statements."""
    def __init__(self, value: "Value"):
        self.value = value


class InterpreterError(Exception):
    """Runtime error during interpretation."""
    def __init__(self, message: str, node: Optional[nodes.ASTNode] = None):
        self.node = node
        loc = ""
        if node and node.source_location:
            loc = f" at {node.source_location.line}:{node.source_location.col}"
        super().__init__(f"{message}{loc}")


class AssertionError_(Exception):
    """Assertion failure with source location."""
    def __init__(self, message: str, node: Optional[nodes.ASTNode] = None):
        self.node = node
        loc = ""
        if node and node.source_location:
            loc = f" at {node.source_location.line}:{node.source_location.col}"
        super().__init__(f"Assertion failed{loc}: {message}")


# ---------------------------------------------------------------------------
# Runtime value wrapper
# ---------------------------------------------------------------------------

@dataclass
class Value:
    """Runtime value wrapper with type tag."""
    raw: Any # int, float, bool, str, Decimal, date, nodes.DurationNode, StructInstance, list, None
    type_tag: str = "" # "int","float","bool","string","money","percent","date","duration","struct","list","none"

    def __post_init__(self):
        if self.type_tag:
            return
        # auto-detect
        if self.raw is None:
            self.type_tag = "none"
        elif isinstance(self.raw, bool):
            self.type_tag = "bool"
        elif isinstance(self.raw, int):
            self.type_tag = "int"
        elif isinstance(self.raw, float):
            self.type_tag = "float"
        elif isinstance(self.raw, str):
            self.type_tag = "string"
        elif isinstance(self.raw, Decimal):
            self.type_tag = "money" # ambiguous with percent; caller should set explicitly
        elif isinstance(self.raw, date):
            self.type_tag = "date"
        elif isinstance(self.raw, nodes.DurationNode):
            self.type_tag = "duration"
        elif isinstance(self.raw, StructInstance):
            self.type_tag = "struct"
        elif isinstance(self.raw, list):
            self.type_tag = "list"

    @staticmethod
    def from_node(node: nodes.ASTNode) -> "Value":
        """Create Value from a literal AST node."""
        if isinstance(node, nodes.IntLit):
            return Value(node.value, "int")
        if isinstance(node, nodes.FloatLit):
            return Value(node.value, "float")
        if isinstance(node, nodes.BoolLit):
            return Value(node.value, "bool")
        if isinstance(node, nodes.StringLit):
            return Value(node.value, "string")
        if isinstance(node, nodes.MoneyNode):
            return Value(node.amount, "money")
        if isinstance(node, nodes.PercentNode):
            return Value(node.value, "percent")
        if isinstance(node, nodes.DateNode):
            return Value(node.value, "date")
        if isinstance(node, nodes.DurationNode):
            return Value(node, "duration")
        if isinstance(node, nodes.PassExprNode):
            return Value(None, "none")
        raise InterpreterError(f"Cannot create Value from {type(node).__name__}", node)

    @staticmethod
    def none() -> "Value":
        return Value(None, "none")

    def is_truthy(self) -> bool:
        if self.type_tag == "bool":
            return self.raw
        if self.type_tag == "none":
            return False
        if self.type_tag == "int":
            return self.raw != 0
        if self.type_tag == "float":
            return self.raw != 0.0
        if self.type_tag == "string":
            return len(self.raw) > 0
        if self.type_tag == "list":
            return len(self.raw) > 0
        if self.type_tag in ("money", "percent"):
            return self.raw != Decimal(0)
        return True

    def __repr__(self) -> str:
        return f"Value({self.raw!r}, {self.type_tag!r})"


# ---------------------------------------------------------------------------
# Runtime struct instance
# ---------------------------------------------------------------------------

@dataclass
class StructInstance:
    """Runtime representation of a struct value."""
    type_name: str
    fields: Dict[str, Value]

    def get_field(self, name: str) -> Value:
        if name not in self.fields:
            raise InterpreterError(f"No field '{name}' on struct '{self.type_name}'")
        return self.fields[name]

    def set_field(self, name: str, value: Value) -> None:
        self.fields[name] = value

    def __repr__(self) -> str:
        flds = ", ".join(f"{k}={v!r}" for k, v in self.fields.items())
        return f"{self.type_name}{{{flds}}}"


# ---------------------------------------------------------------------------
# Environment (chained scopes)
# ---------------------------------------------------------------------------

@dataclass
class Environment:
    """Chained-scope environment for variable/function/struct/statute bindings."""
    bindings: Dict[str, Value] = field(default_factory=dict)
    struct_defs: Dict[str, nodes.StructDefNode] = field(default_factory=dict)
    function_defs: Dict[str, nodes.FunctionDefNode] = field(default_factory=dict)
    statutes: Dict[str, nodes.StatuteNode] = field(default_factory=dict)
    parent: Optional["Environment"] = None

    def get(self, name: str) -> Optional[Value]:
        if name in self.bindings:
            return self.bindings[name]
        if self.parent:
            return self.parent.get(name)
        return None

    def set(self, name: str, value: Value) -> None:
        self.bindings[name] = value

    def assign(self, name: str, value: Value) -> bool:
        """Update existing binding in nearest scope. Returns False if not found."""
        if name in self.bindings:
            self.bindings[name] = value
            return True
        if self.parent:
            return self.parent.assign(name, value)
        return False

    def child(self) -> "Environment":
        return Environment(parent=self)

    def get_struct_def(self, name: str) -> Optional[nodes.StructDefNode]:
        if name in self.struct_defs:
            return self.struct_defs[name]
        if self.parent:
            return self.parent.get_struct_def(name)
        return None

    def get_function_def(self, name: str) -> Optional[nodes.FunctionDefNode]:
        if name in self.function_defs:
            return self.function_defs[name]
        if self.parent:
            return self.parent.get_function_def(name)
        return None

    def get_statute(self, section: str) -> Optional[nodes.StatuteNode]:
        if section in self.statutes:
            return self.statutes[section]
        if self.parent:
            return self.parent.get_statute(section)
        return None


# ---------------------------------------------------------------------------
# Interpreter (tree-walking, visitor-based)
# ---------------------------------------------------------------------------

class Interpreter(Visitor):
    """Tree-walking interpreter for Yuho AST."""

    def __init__(self, env: Optional[Environment] = None):
        self.env = env or Environment()

    # -- module entry point -------------------------------------------------

    def interpret(self, module: nodes.ModuleNode) -> Environment:
        """Interpret a complete module, populating the environment."""
        # register struct defs
        for sd in module.type_defs:
            self.env.struct_defs[sd.name] = sd
        # register function defs
        for fd in module.function_defs:
            self.env.function_defs[fd.name] = fd
        # register statutes
        for st in module.statutes:
            self.env.statutes[st.section_number] = st
        # execute variable declarations
        for var in module.variables:
            self.visit(var)
        # execute assertions
        for assertion in module.assertions:
            self.visit(assertion)
        return self.env

    # -- helpers ------------------------------------------------------------

    def _numeric(self, v: Value, node: nodes.ASTNode) -> Any:
        """Extract a numeric raw value (int, float, or Decimal)."""
        if v.type_tag in ("int", "float", "money", "percent"):
            return v.raw
        raise InterpreterError(f"Expected numeric value, got {v.type_tag}", node)

    def _coerce_pair(self, a: Value, b: Value) -> Tuple[Any, Any, str]:
        """Coerce a pair of numeric values to a common type.
        Returns (raw_a, raw_b, result_type_tag)."""
        ra, rb = a.raw, b.raw
        # Decimal stays Decimal
        if isinstance(ra, Decimal) or isinstance(rb, Decimal):
            return (Decimal(str(ra)), Decimal(str(rb)), a.type_tag if isinstance(ra, Decimal) else b.type_tag)
        # int + float -> float
        if isinstance(ra, float) or isinstance(rb, float):
            return (float(ra), float(rb), "float")
        return (ra, rb, "int")

    # ======================================================================
    # Literal visitors
    # ======================================================================

    def visit_int_lit(self, node: nodes.IntLit) -> Value:
        return Value(node.value, "int")

    def visit_float_lit(self, node: nodes.FloatLit) -> Value:
        return Value(node.value, "float")

    def visit_bool_lit(self, node: nodes.BoolLit) -> Value:
        return Value(node.value, "bool")

    def visit_string_lit(self, node: nodes.StringLit) -> Value:
        return Value(node.value, "string")

    def visit_money(self, node: nodes.MoneyNode) -> Value:
        return Value(node.amount, "money")

    def visit_percent(self, node: nodes.PercentNode) -> Value:
        return Value(node.value, "percent")

    def visit_date(self, node: nodes.DateNode) -> Value:
        return Value(node.value, "date")

    def visit_duration(self, node: nodes.DurationNode) -> Value:
        return Value(node, "duration")

    # ======================================================================
    # Expression visitors
    # ======================================================================

    def visit_identifier(self, node: nodes.IdentifierNode) -> Value:
        val = self.env.get(node.name)
        if val is not None:
            return val
        # check if it's a struct name (for enum-style access patterns)
        sd = self.env.get_struct_def(node.name)
        if sd is not None:
            return Value(node.name, "string")
        raise InterpreterError(f"Undefined variable '{node.name}'", node)

    def visit_field_access(self, node: nodes.FieldAccessNode) -> Value:
        base = self.visit(node.base)
        if base.type_tag == "struct":
            return base.raw.get_field(node.field_name)
        # string base -> enum-style "Type.Field" reference
        if base.type_tag == "string":
            return Value(f"{base.raw}.{node.field_name}", "string")
        raise InterpreterError(f"Cannot access field '{node.field_name}' on {base.type_tag}", node)

    def visit_index_access(self, node: nodes.IndexAccessNode) -> Value:
        base = self.visit(node.base)
        idx = self.visit(node.index)
        if base.type_tag == "list":
            if idx.type_tag != "int":
                raise InterpreterError("List index must be an integer", node)
            try:
                return base.raw[idx.raw]
            except IndexError:
                raise InterpreterError(f"Index {idx.raw} out of range", node)
        if base.type_tag == "string":
            if idx.type_tag != "int":
                raise InterpreterError("String index must be an integer", node)
            try:
                return Value(base.raw[idx.raw], "string")
            except IndexError:
                raise InterpreterError(f"Index {idx.raw} out of range", node)
        raise InterpreterError(f"Cannot index into {base.type_tag}", node)

    def visit_binary_expr(self, node: nodes.BinaryExprNode) -> Value:
        op = node.operator
        # short-circuit logical operators
        if op == "&&":
            left = self.visit(node.left)
            if not left.is_truthy():
                return Value(False, "bool")
            right = self.visit(node.right)
            return Value(right.is_truthy(), "bool")
        if op == "||":
            left = self.visit(node.left)
            if left.is_truthy():
                return Value(True, "bool")
            right = self.visit(node.right)
            return Value(right.is_truthy(), "bool")

        left = self.visit(node.left)
        right = self.visit(node.right)

        # string concatenation
        if op == "+" and (left.type_tag == "string" or right.type_tag == "string"):
            return Value(str(left.raw) + str(right.raw), "string")

        # equality / inequality (work on any types)
        if op == "==":
            return Value(left.raw == right.raw, "bool")
        if op == "!=":
            return Value(left.raw != right.raw, "bool")

        # arithmetic & comparison require numeric
        if left.type_tag in ("int", "float", "money", "percent") and right.type_tag in ("int", "float", "money", "percent"):
            la, ra, tag = self._coerce_pair(left, right)
            if op == "+":
                return Value(la + ra, tag)
            if op == "-":
                return Value(la - ra, tag)
            if op == "*":
                return Value(la * ra, tag)
            if op == "/":
                if ra == 0:
                    raise InterpreterError("Division by zero", node)
                if tag == "int":
                    return Value(la // ra, tag) # integer division
                return Value(la / ra, tag)
            if op == "%":
                if ra == 0:
                    raise InterpreterError("Modulo by zero", node)
                return Value(la % ra, tag)
            if op == "<":
                return Value(la < ra, "bool")
            if op == ">":
                return Value(la > ra, "bool")
            if op == "<=":
                return Value(la <= ra, "bool")
            if op == ">=":
                return Value(la >= ra, "bool")

        # date comparison
        if left.type_tag == "date" and right.type_tag == "date":
            if op == "<":
                return Value(left.raw < right.raw, "bool")
            if op == ">":
                return Value(left.raw > right.raw, "bool")
            if op == "<=":
                return Value(left.raw <= right.raw, "bool")
            if op == ">=":
                return Value(left.raw >= right.raw, "bool")

        # duration comparison via total_days
        if left.type_tag == "duration" and right.type_tag == "duration":
            ld = left.raw.total_days()
            rd = right.raw.total_days()
            if op == "<":
                return Value(ld < rd, "bool")
            if op == ">":
                return Value(ld > rd, "bool")
            if op == "<=":
                return Value(ld <= rd, "bool")
            if op == ">=":
                return Value(ld >= rd, "bool")

        raise InterpreterError(f"Unsupported operator '{op}' for types {left.type_tag}, {right.type_tag}", node)

    def visit_unary_expr(self, node: nodes.UnaryExprNode) -> Value:
        operand = self.visit(node.operand)
        if node.operator == "!":
            return Value(not operand.is_truthy(), "bool")
        if node.operator == "-":
            if operand.type_tag == "int":
                return Value(-operand.raw, "int")
            if operand.type_tag == "float":
                return Value(-operand.raw, "float")
            if operand.type_tag in ("money", "percent"):
                return Value(-operand.raw, operand.type_tag)
            raise InterpreterError(f"Cannot negate {operand.type_tag}", node)
        raise InterpreterError(f"Unknown unary operator '{node.operator}'", node)

    def visit_pass_expr(self, node: nodes.PassExprNode) -> Value:
        return Value(None, "none")

    # ======================================================================
    # Match expression
    # ======================================================================

    def visit_match_expr(self, node: nodes.MatchExprNode) -> Value:
        if node.scrutinee is not None:
            scrutinee = self.visit(node.scrutinee)
        else:
            scrutinee = Value(True, "bool") # bare match -> match TRUE against guards

        for arm in node.arms:
            bindings = self._match_pattern(arm.pattern, scrutinee)
            if bindings is None:
                continue
            # check guard
            if arm.guard is not None:
                saved = self.env
                self.env = self.env.child()
                for k, v in bindings.items():
                    self.env.set(k, v)
                guard_val = self.visit(arm.guard)
                self.env = saved
                if not guard_val.is_truthy():
                    continue
            # evaluate body in scope with bindings
            saved = self.env
            self.env = self.env.child()
            for k, v in bindings.items():
                self.env.set(k, v)
            result = self.visit(arm.body)
            self.env = saved
            return result

        # no arm matched
        return Value(None, "none")

    def _match_pattern(self, pattern: nodes.PatternNode, value: Value) -> Optional[Dict[str, Value]]:
        """Try to match a value against a pattern. Returns bindings dict or None."""
        if isinstance(pattern, nodes.WildcardPattern):
            return {}
        if isinstance(pattern, nodes.LiteralPattern):
            lit_val = self.visit(pattern.literal)
            if lit_val.raw == value.raw:
                return {}
            return None
        if isinstance(pattern, nodes.BindingPattern):
            return {pattern.name: value}
        if isinstance(pattern, nodes.StructPattern):
            if not isinstance(value.raw, StructInstance):
                return None
            if value.raw.type_name != pattern.type_name:
                return None
            bindings: Dict[str, Value] = {}
            for fp in pattern.fields:
                if fp.name not in value.raw.fields:
                    return None
                field_val = value.raw.fields[fp.name]
                if fp.pattern:
                    sub = self._match_pattern(fp.pattern, field_val)
                    if sub is None:
                        return None
                    bindings.update(sub)
                else:
                    bindings[fp.name] = field_val
            return bindings
        return None

    def visit_match_arm(self, node: nodes.MatchArm) -> Value:
        # arms are handled inside visit_match_expr; standalone visit is a no-op
        return Value(None, "none")

    # ======================================================================
    # Function call
    # ======================================================================

    def visit_function_call(self, node: nodes.FunctionCallNode) -> Value:
        # resolve callee name
        if isinstance(node.callee, nodes.IdentifierNode):
            fn_name = node.callee.name
        elif isinstance(node.callee, nodes.FieldAccessNode):
            # method-style calls not yet supported; treat as plain name
            base = self.visit(node.callee.base)
            fn_name = node.callee.field_name
        else:
            raise InterpreterError("Unsupported callee form", node)

        fn_def = self.env.get_function_def(fn_name)
        if fn_def is None:
            raise InterpreterError(f"Undefined function '{fn_name}'", node)

        # evaluate arguments
        arg_vals = [self.visit(a) for a in node.args]
        if len(arg_vals) != len(fn_def.params):
            raise InterpreterError(
                f"Function '{fn_name}' expects {len(fn_def.params)} args, got {len(arg_vals)}", node
            )

        # create child scope, bind params
        call_env = self.env.child()
        for param, val in zip(fn_def.params, arg_vals):
            call_env.set(param.name, val)

        # execute body
        saved = self.env
        self.env = call_env
        try:
            self.visit(fn_def.body)
        except ReturnSignal as rs:
            self.env = saved
            return rs.value
        self.env = saved
        return Value(None, "none")

    # ======================================================================
    # Struct literal
    # ======================================================================

    def visit_struct_literal(self, node: nodes.StructLiteralNode) -> Value:
        fields: Dict[str, Value] = {}
        for fa in node.field_values:
            fields[fa.name] = self.visit(fa.value)
        name = node.struct_name or "<anonymous>"
        inst = StructInstance(type_name=name, fields=fields)
        return Value(inst, "struct")

    def visit_field_assignment(self, node: nodes.FieldAssignment) -> Value:
        return self.visit(node.value)

    # ======================================================================
    # Statement visitors
    # ======================================================================

    def visit_variable_decl(self, node: nodes.VariableDecl) -> Value:
        if node.value is not None:
            val = self.visit(node.value)
        else:
            val = Value(None, "none")
        self.env.set(node.name, val)
        return val

    def visit_assignment_stmt(self, node: nodes.AssignmentStmt) -> Value:
        val = self.visit(node.value)
        if isinstance(node.target, nodes.IdentifierNode):
            if not self.env.assign(node.target.name, val):
                self.env.set(node.target.name, val)
        elif isinstance(node.target, nodes.FieldAccessNode):
            base = self.visit(node.target.base)
            if base.type_tag == "struct":
                base.raw.set_field(node.target.field_name, val)
            else:
                raise InterpreterError(f"Cannot assign field on {base.type_tag}", node)
        elif isinstance(node.target, nodes.IndexAccessNode):
            base = self.visit(node.target.base)
            idx = self.visit(node.target.index)
            if base.type_tag == "list" and idx.type_tag == "int":
                try:
                    base.raw[idx.raw] = val
                except IndexError:
                    raise InterpreterError(f"Index {idx.raw} out of range", node)
            else:
                raise InterpreterError(f"Cannot index-assign on {base.type_tag}", node)
        else:
            raise InterpreterError("Invalid assignment target", node)
        return val

    def visit_return_stmt(self, node: nodes.ReturnStmt) -> Value:
        if node.value is not None:
            val = self.visit(node.value)
        else:
            val = Value(None, "none")
        raise ReturnSignal(val)

    def visit_pass_stmt(self, node: nodes.PassStmt) -> Value:
        return Value(None, "none")

    def visit_assert_stmt(self, node: nodes.AssertStmt) -> Value:
        cond = self.visit(node.condition)
        if not cond.is_truthy():
            msg = ""
            if node.message:
                msg = node.message.value
            else:
                msg = f"condition evaluated to {cond.raw!r}"
            raise AssertionError_(msg, node)
        return Value(True, "bool")

    def visit_block(self, node: nodes.Block) -> Value:
        result = Value(None, "none")
        for stmt in node.statements:
            result = self.visit(stmt)
        return result

    def visit_expression_stmt(self, node: nodes.ExpressionStmt) -> Value:
        return self.visit(node.expression)

    # ======================================================================
    # Definition visitors (registration happens in interpret())
    # ======================================================================

    def visit_function_def(self, node: nodes.FunctionDefNode) -> Value:
        self.env.function_defs[node.name] = node
        return Value(None, "none")

    def visit_struct_def(self, node: nodes.StructDefNode) -> Value:
        self.env.struct_defs[node.name] = node
        return Value(None, "none")

    # ======================================================================
    # Type visitors (no runtime effect)
    # ======================================================================

    def visit_type(self, node: nodes.TypeNode) -> Value:
        return Value(None, "none")

    def visit_builtin_type(self, node: nodes.BuiltinType) -> Value:
        return Value(None, "none")

    def visit_named_type(self, node: nodes.NamedType) -> Value:
        return Value(None, "none")

    def visit_generic_type(self, node: nodes.GenericType) -> Value:
        return Value(None, "none")

    def visit_optional_type(self, node: nodes.OptionalType) -> Value:
        return Value(None, "none")

    def visit_array_type(self, node: nodes.ArrayType) -> Value:
        return Value(None, "none")

    # ======================================================================
    # Pattern visitors (handled in _match_pattern; standalone is no-op)
    # ======================================================================

    def visit_pattern(self, node: nodes.PatternNode) -> Value:
        return Value(None, "none")

    def visit_wildcard_pattern(self, node: nodes.WildcardPattern) -> Value:
        return Value(None, "none")

    def visit_literal_pattern(self, node: nodes.LiteralPattern) -> Value:
        return self.visit(node.literal)

    def visit_binding_pattern(self, node: nodes.BindingPattern) -> Value:
        return Value(None, "none")

    def visit_field_pattern(self, node: nodes.FieldPattern) -> Value:
        return Value(None, "none")

    def visit_struct_pattern(self, node: nodes.StructPattern) -> Value:
        return Value(None, "none")

    def visit_param_def(self, node: nodes.ParamDef) -> Value:
        return Value(None, "none")

    def visit_field_def(self, node: nodes.FieldDef) -> Value:
        return Value(None, "none")

    # ======================================================================
    # Statute-specific visitors (structural; no runtime evaluation)
    # ======================================================================

    def visit_statute(self, node: nodes.StatuteNode) -> Value:
        self.env.statutes[node.section_number] = node
        return Value(None, "none")

    def visit_definition_entry(self, node: nodes.DefinitionEntry) -> Value:
        return Value(None, "none")

    def visit_element(self, node: nodes.ElementNode) -> Value:
        return Value(None, "none")

    def visit_element_group(self, node: nodes.ElementGroupNode) -> Value:
        return Value(None, "none")

    def visit_penalty(self, node: nodes.PenaltyNode) -> Value:
        return Value(None, "none")

    def visit_illustration(self, node: nodes.IllustrationNode) -> Value:
        return Value(None, "none")

    def visit_exception(self, node: nodes.ExceptionNode) -> Value:
        return Value(None, "none")

    def visit_caselaw(self, node: nodes.CaseLawNode) -> Value:
        return Value(None, "none")

    # ======================================================================
    # Import / referencing / module
    # ======================================================================

    def visit_import(self, node: nodes.ImportNode) -> Value:
        return Value(None, "none")

    def visit_referencing_stmt(self, node: nodes.ReferencingStmt) -> Value:
        return Value(None, "none")

    def visit_module(self, node: nodes.ModuleNode) -> Value:
        self.interpret(node)
        return Value(None, "none")
