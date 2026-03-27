"""
Type checking visitor for Yuho AST.

Validates type consistency and reports type errors:
- Assignment type compatibility
- Binary operator type compatibility
- Function argument type matching
- Return type matching
- Match arm type consistency
- Cross-module NamedType resolution via ModuleResolver
"""

from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.ast.type_inference import (
    TypeAnnotation,
    TypeInferenceVisitor,
    TypeInferenceResult,
    INT_TYPE,
    FLOAT_TYPE,
    BOOL_TYPE,
    STRING_TYPE,
    MONEY_TYPE,
    PERCENT_TYPE,
    DATE_TYPE,
    DURATION_TYPE,
    VOID_TYPE,
    PASS_TYPE,
    UNKNOWN_TYPE,
)

logger = logging.getLogger(__name__)


@dataclass
class TypeErrorInfo:
    """Represents a type error with location and context."""

    message: str
    line: int = 0
    column: int = 0
    node_type: str = ""
    severity: str = "error"  # "error" or "warning"

    def __str__(self) -> str:
        loc = f"{self.line}:{self.column}" if self.line else ""
        return f"[{self.severity}] {loc} {self.message}"


@dataclass
class TypeCheckResult:
    """Result of type checking including all errors and warnings."""

    errors: List[TypeErrorInfo] = field(default_factory=list)
    warnings: List[TypeErrorInfo] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def is_valid(self) -> bool:
        return not self.has_errors

    def add_error(
        self,
        message: str,
        node: Optional[nodes.ASTNode] = None,
        severity: str = "error",
    ) -> None:
        """Add a type error."""
        line = 0
        column = 0
        node_type = ""
        if node and node.source_location:
            line = node.source_location.line
            column = node.source_location.col
        if node:
            node_type = type(node).__name__
        error = TypeErrorInfo(
            message=message,
            line=line,
            column=column,
            node_type=node_type,
            severity=severity,
        )
        if severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)


class TypeCheckVisitor(Visitor):
    """
    Visitor that validates type consistency and reports errors.

    Runs after TypeInferenceVisitor to validate inferred types are consistent.
    Optionally accepts a ModuleResolver + source_file for cross-module
    NamedType resolution.

    Usage:
        infer_visitor = TypeInferenceVisitor()
        module.accept(infer_visitor)

        check_visitor = TypeCheckVisitor(infer_visitor.result)
        module.accept(check_visitor)
        result = check_visitor.result
    """

    # types compatible with each other for numeric operations
    NUMERIC_TYPES = frozenset({"int", "float", "money", "percent"})
    # types that can be compared with equality
    COMPARABLE_TYPES = frozenset(
        {"int", "float", "bool", "string", "money", "percent", "date", "duration"}
    )
    # types that can be ordered (< > <= >=)
    ORDERABLE_TYPES = frozenset({"int", "float", "money", "percent", "date", "duration"})

    def __init__(
        self,
        type_info: TypeInferenceResult,
        resolver=None,
        source_file: Optional[Path] = None,
    ) -> None:
        self.type_info = type_info
        self.result = TypeCheckResult()
        self._current_function_return: Optional[TypeAnnotation] = None
        self._resolver = resolver  # Optional[ModuleResolver]
        self._source_file = Path(source_file) if source_file else None
        # cache of cross-module struct defs resolved via the resolver
        self._resolved_type_names: Dict[str, Dict[str, TypeAnnotation]] = {}

    def _get_type(self, node: nodes.ASTNode) -> TypeAnnotation:
        """Get the inferred type for a node."""
        return self.type_info.get_type(node)

    def _types_compatible(
        self,
        expected: TypeAnnotation,
        actual: TypeAnnotation,
        allow_coercion: bool = True,
    ) -> bool:
        """Check if two types are compatible."""
        if expected == UNKNOWN_TYPE or actual == UNKNOWN_TYPE:
            return True
        if actual == PASS_TYPE:
            return True
        if expected.type_name == actual.type_name:
            return True
        if expected.is_optional and not actual.is_optional:
            return expected.type_name == actual.type_name
        if allow_coercion:
            if expected.type_name == "float" and actual.type_name == "int":
                return True
        # type alias resolution
        aliases = getattr(self.type_info, "type_aliases", {})
        resolved_expected = aliases.get(expected.type_name, expected)
        resolved_actual = aliases.get(actual.type_name, actual)
        if resolved_expected.type_name == resolved_actual.type_name:
            return True
        # enum variant is compatible with its enum type
        enum_variants = getattr(self.type_info, "enum_variants", {})
        if (
            actual.type_name in enum_variants
            and enum_variants[actual.type_name] == expected.type_name
        ):
            return True
        return False

    def _check_binary_types(
        self,
        node: nodes.BinaryExprNode,
        left_type: TypeAnnotation,
        right_type: TypeAnnotation,
    ) -> None:
        """Check type compatibility for binary operators."""
        op = node.operator
        if op in ("&&", "||", "and", "or"):
            if left_type.type_name != "bool":
                self.result.add_error(
                    f"Left operand of '{op}' must be bool, got {left_type}",
                    node,
                )
            if right_type.type_name != "bool":
                self.result.add_error(
                    f"Right operand of '{op}' must be bool, got {right_type}",
                    node,
                )
        elif op in ("==", "!="):
            if not self._types_compatible(left_type, right_type):
                self.result.add_error(
                    f"Cannot compare {left_type} with {right_type}",
                    node,
                )
        elif op in ("<", ">", "<=", ">="):
            if left_type.type_name not in self.ORDERABLE_TYPES:
                self.result.add_error(
                    f"Type {left_type} is not orderable",
                    node,
                )
            if right_type.type_name not in self.ORDERABLE_TYPES:
                self.result.add_error(
                    f"Type {right_type} is not orderable",
                    node,
                )
            if left_type.type_name != right_type.type_name:
                self.result.add_error(
                    f"Cannot compare {left_type} with {right_type}",
                    node,
                )
        elif op in ("+", "-", "*", "/", "%"):
            if op == "+" and left_type.type_name == "string":
                if right_type.type_name != "string":
                    self.result.add_error(
                        f"Cannot concatenate string with {right_type}",
                        node,
                    )
            elif left_type.type_name == "duration" or right_type.type_name == "duration":
                if op not in ("+", "-"):
                    self.result.add_error(
                        f"Invalid operation '{op}' on duration",
                        node,
                    )
            elif left_type.type_name not in self.NUMERIC_TYPES:
                self.result.add_error(
                    f"Type {left_type} does not support arithmetic",
                    node,
                )
            elif right_type.type_name not in self.NUMERIC_TYPES:
                self.result.add_error(
                    f"Type {right_type} does not support arithmetic",
                    node,
                )

    # =========================================================================
    # Cross-module NamedType resolution
    # =========================================================================

    def _resolve_named_type(self, type_name: str) -> bool:
        """
        Try to resolve a NamedType by checking local struct/enum/alias defs first,
        then searching resolved modules via the resolver.

        Returns True if the type was found (locally or cross-module).
        """
        if type_name in self.type_info.struct_defs:
            return True
        if type_name in getattr(self.type_info, "enum_defs", {}):
            return True
        if type_name in getattr(self.type_info, "type_aliases", {}):
            return True
        if type_name in self._resolved_type_names:
            return True
        if self._resolver is None or self._source_file is None:
            return False
        # search modules cached by the resolver for this type name
        for _path, module in self._resolver.cached_modules.items():
            exported = self._resolver.get_exported_symbols(module)
            if type_name in exported:
                decl = exported[type_name]
                if isinstance(decl, nodes.StructDefNode):
                    # build field type map so type_check can use it
                    from yuho.ast.type_inference import TypeAnnotation as TA

                    fields: Dict[str, TypeAnnotation] = {}
                    for fld in decl.fields:
                        if fld.type_annotation:
                            fields[fld.name] = self._type_node_to_annotation(fld.type_annotation)
                    self._resolved_type_names[type_name] = fields
                return True
        return False

    @staticmethod
    def _type_node_to_annotation(type_node: nodes.TypeNode) -> TypeAnnotation:
        """Convert a TypeNode to a TypeAnnotation (minimal helper)."""
        if isinstance(type_node, nodes.BuiltinType):
            return TypeAnnotation(type_node.name)
        elif isinstance(type_node, nodes.NamedType):
            return TypeAnnotation(type_node.name)
        elif isinstance(type_node, nodes.OptionalType):
            inner = TypeCheckVisitor._type_node_to_annotation(type_node.inner)
            return TypeAnnotation(inner.type_name, is_optional=True)
        elif isinstance(type_node, nodes.ArrayType):
            elem = TypeCheckVisitor._type_node_to_annotation(type_node.element_type)
            return TypeAnnotation("array", is_array=True, element_type=elem)
        elif isinstance(type_node, nodes.GenericType):
            return TypeAnnotation(type_node.base)
        return UNKNOWN_TYPE

    def visit_named_type(self, node: nodes.NamedType) -> None:
        """Validate that a NamedType refers to a known type, including cross-module."""
        if not self._resolve_named_type(node.name):
            self.result.add_error(
                f"Unknown type '{node.name}'",
                node,
                severity="warning",
            )
        return self.generic_visit(node)

    # =========================================================================
    # Expression nodes
    # =========================================================================

    def visit_binary_expr(self, node: nodes.BinaryExprNode) -> None:
        """Check binary expression type compatibility."""
        self.visit(node.left)
        self.visit(node.right)
        left_type = self._get_type(node.left)
        right_type = self._get_type(node.right)
        self._check_binary_types(node, left_type, right_type)
        return self.generic_visit(node)

    def visit_unary_expr(self, node: nodes.UnaryExprNode) -> None:
        """Check unary expression type compatibility."""
        self.visit(node.operand)
        operand_type = self._get_type(node.operand)
        op = node.operator
        if op in ("!", "not"):
            if operand_type.type_name != "bool":
                self.result.add_error(
                    f"Operand of '{op}' must be bool, got {operand_type}",
                    node,
                )
        elif op == "-":
            if operand_type.type_name not in self.NUMERIC_TYPES:
                self.result.add_error(
                    f"Cannot negate non-numeric type {operand_type}",
                    node,
                )
        return self.generic_visit(node)

    # =========================================================================
    # Variable and assignment
    # =========================================================================

    def visit_variable_decl(self, node: nodes.VariableDecl) -> None:
        """Check variable declaration type matches initializer."""
        if node.type_annotation and node.value:
            declared_type = self.type_info.variable_types.get(node.name, UNKNOWN_TYPE)
            value_type = self._get_type(node.value)
            if not self._types_compatible(declared_type, value_type):
                self.result.add_error(
                    f"Cannot assign {value_type} to variable of type {declared_type}",
                    node,
                )
        if node.value:
            self.visit(node.value)
        return self.generic_visit(node)

    def visit_assignment_stmt(self, node: nodes.AssignmentStmt) -> None:
        """Check assignment type compatibility."""
        self.visit(node.target)
        self.visit(node.value)
        target_type = self._get_type(node.target)
        value_type = self._get_type(node.value)
        if not self._types_compatible(target_type, value_type):
            self.result.add_error(
                f"Cannot assign {value_type} to {target_type}",
                node,
            )
        return self.generic_visit(node)

    # =========================================================================
    # Function calls and returns
    # =========================================================================

    def visit_function_call(self, node: nodes.FunctionCallNode) -> None:
        """Check function argument types match parameters."""
        if isinstance(node.callee, nodes.IdentifierNode):
            func_name = node.callee.name
        elif isinstance(node.callee, nodes.FieldAccessNode):
            func_name = node.callee.field_name
        else:
            func_name = ""
        if func_name in self.type_info.function_sigs:
            param_types, _ = self.type_info.function_sigs[func_name]
            if len(node.args) != len(param_types):
                self.result.add_error(
                    f"Function '{func_name}' expects {len(param_types)} arguments, got {len(node.args)}",
                    node,
                )
            else:
                for i, (arg, expected_type) in enumerate(zip(node.args, param_types)):
                    self.visit(arg)
                    arg_type = self._get_type(arg)
                    if not self._types_compatible(expected_type, arg_type):
                        self.result.add_error(
                            f"Argument {i + 1} of '{func_name}' expected {expected_type}, got {arg_type}",
                            arg,
                        )
        else:
            for arg in node.args:
                self.visit(arg)
        return self.generic_visit(node)

    def visit_function_def(self, node: nodes.FunctionDefNode) -> None:
        """Check function body return statements match declared return type."""
        if node.return_type:
            if node.name in self.type_info.function_sigs:
                _, return_type = self.type_info.function_sigs[node.name]
                self._current_function_return = return_type
            else:
                self._current_function_return = VOID_TYPE
        else:
            self._current_function_return = VOID_TYPE
        if node.body:
            self.visit(node.body)
        self._current_function_return = None
        return self.generic_visit(node)

    def visit_return_stmt(self, node: nodes.ReturnStmt) -> None:
        """Check return statement type matches function return type."""
        if self._current_function_return:
            if node.value:
                self.visit(node.value)
                return_value_type = self._get_type(node.value)
                if not self._types_compatible(self._current_function_return, return_value_type):
                    self.result.add_error(
                        f"Return type {return_value_type} does not match expected {self._current_function_return}",
                        node,
                    )
            elif self._current_function_return != VOID_TYPE:
                self.result.add_error(
                    f"Missing return value, expected {self._current_function_return}",
                    node,
                )
        return self.generic_visit(node)

    # =========================================================================
    # Match expression
    # =========================================================================

    def visit_match_expr(self, node: nodes.MatchExprNode) -> None:
        """Check all match arms have consistent types and enum exhaustiveness."""
        if node.scrutinee:
            self.visit(node.scrutinee)
        arm_types: List[TypeAnnotation] = []
        for arm in node.arms:
            self.visit(arm)
            arm_type = self._get_type(arm)
            if arm_type != PASS_TYPE and arm_type != UNKNOWN_TYPE:
                arm_types.append(arm_type)
        if len(arm_types) > 1:
            first_type = arm_types[0]
            for i, arm_type in enumerate(arm_types[1:], 1):
                if not self._types_compatible(first_type, arm_type):
                    self.result.add_error(
                        f"Match arm {i + 1} has type {arm_type}, expected {first_type}",
                        node.arms[i] if i < len(node.arms) else node,
                        severity="warning",
                    )
        self._check_enum_exhaustiveness(node)
        return self.generic_visit(node)

    def _check_enum_exhaustiveness(self, node: nodes.MatchExprNode) -> None:
        """Warn when a match over an enum type does not cover all variants."""
        if not node.scrutinee:
            return
        if not getattr(node, "ensure_exhaustiveness", True):
            return
        scrutinee_type = self._get_type(node.scrutinee)
        enum_defs = getattr(self.type_info, "enum_defs", {})
        type_name = scrutinee_type.type_name
        # resolve type aliases to underlying enum
        aliases = getattr(self.type_info, "type_aliases", {})
        if type_name in aliases:
            type_name = aliases[type_name].type_name
        if type_name not in enum_defs:
            return
        all_variants: set = enum_defs[type_name]
        has_wildcard = False
        covered: set = set()
        for arm in node.arms:
            pat = arm.pattern
            if isinstance(pat, nodes.WildcardPattern):
                has_wildcard = True
                break
            if isinstance(pat, nodes.BindingPattern):
                covered.add(pat.name)
            elif isinstance(pat, nodes.StructPattern):
                covered.add(pat.type_name)
            elif isinstance(pat, nodes.LiteralPattern):
                lit = pat.literal
                if isinstance(lit, nodes.IdentifierNode):
                    covered.add(lit.name)
        if has_wildcard:
            return
        missing = all_variants - covered
        if missing:
            names = ", ".join(sorted(missing))
            self.result.add_error(
                f"Non-exhaustive match on enum '{type_name}': missing variants {names}",
                node,
                severity="warning",
            )

    def visit_match_arm(self, node: nodes.MatchArm) -> None:
        """Check guard expression is boolean."""
        self.visit(node.pattern)
        if node.guard:
            self.visit(node.guard)
            guard_type = self._get_type(node.guard)
            if guard_type.type_name != "bool":
                self.result.add_error(
                    f"Match arm guard must be bool, got {guard_type}",
                    node.guard,
                )
        self.visit(node.body)
        return self.generic_visit(node)

    # =========================================================================
    # Struct literal
    # =========================================================================

    def visit_struct_literal(self, node: nodes.StructLiteralNode) -> None:
        """Check struct field assignments match field types."""
        struct_name = node.struct_name
        struct_fields = None
        if struct_name:
            if struct_name in self.type_info.struct_defs:
                struct_fields = self.type_info.struct_defs[struct_name]
            elif struct_name in self._resolved_type_names:
                struct_fields = self._resolved_type_names[struct_name]
        if struct_fields is not None:
            for field_assign in node.field_values:
                self.visit(field_assign)
                if field_assign.name in struct_fields:
                    expected_type = struct_fields[field_assign.name]
                    actual_type = self._get_type(field_assign.value)
                    if not self._types_compatible(expected_type, actual_type):
                        self.result.add_error(
                            f"Field '{field_assign.name}' expected {expected_type}, got {actual_type}",
                            field_assign,
                        )
        else:
            for field_assign in node.field_values:
                self.visit(field_assign)
        return self.generic_visit(node)

    # =========================================================================
    # Module entry point
    # =========================================================================

    def visit_module(self, node: nodes.ModuleNode) -> TypeCheckResult:
        """Entry point: check all declarations."""
        for struct_def in node.type_defs:
            self.visit(struct_def)
        for enum_def in getattr(node, "enum_defs", ()):
            self.visit(enum_def)
        for type_alias in getattr(node, "type_aliases", ()):
            self.visit(type_alias)
        for func_def in node.function_defs:
            self.visit(func_def)
        for var_decl in node.variables:
            self.visit(var_decl)
        for statute in node.statutes:
            self.visit(statute)
        for assertion in node.assertions:
            self.visit(assertion)
        return self.result
