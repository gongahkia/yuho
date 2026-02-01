"""
Type checking visitor for Yuho AST.

Validates type consistency and reports type errors:
- Assignment type compatibility
- Binary operator type compatibility
- Function argument type matching
- Return type matching
- Match arm type consistency
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

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
            line = node.source_location.start_line
            column = node.source_location.start_column
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
    
    Usage:
        # First run type inference
        infer_visitor = TypeInferenceVisitor()
        module.accept(infer_visitor)
        
        # Then run type checking
        check_visitor = TypeCheckVisitor(infer_visitor.result)
        module.accept(check_visitor)
        result = check_visitor.result
        
        if result.has_errors:
            for error in result.errors:
                print(error)
    """
    
    # Types that are compatible with each other for numeric operations
    NUMERIC_TYPES = frozenset({"int", "float", "money", "percent"})
    
    # Types that can be compared with equality
    COMPARABLE_TYPES = frozenset({
        "int", "float", "bool", "string", "money", "percent", "date", "duration"
    })
    
    # Types that can be ordered (< > <= >=)
    ORDERABLE_TYPES = frozenset({
        "int", "float", "money", "percent", "date", "duration"
    })
    
    def __init__(self, type_info: TypeInferenceResult) -> None:
        self.type_info = type_info
        self.result = TypeCheckResult()
        self._current_function_return: Optional[TypeAnnotation] = None
    
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
        # Unknown types are always compatible (inference failed)
        if expected == UNKNOWN_TYPE or actual == UNKNOWN_TYPE:
            return True
        
        # Pass type is compatible with anything (placeholder)
        if actual == PASS_TYPE:
            return True
        
        # Exact match
        if expected.type_name == actual.type_name:
            return True
        
        # Optional type is compatible with base type
        if expected.is_optional and not actual.is_optional:
            return expected.type_name == actual.type_name
        
        # Numeric coercion: int -> float
        if allow_coercion:
            if expected.type_name == "float" and actual.type_name == "int":
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
        
        # Logical operators require bool
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
        
        # Comparison operators
        elif op in ("==", "!="):
            if not self._types_compatible(left_type, right_type):
                self.result.add_error(
                    f"Cannot compare {left_type} with {right_type}",
                    node,
                )
        
        # Ordering operators
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
        
        # Arithmetic operators
        elif op in ("+", "-", "*", "/", "%"):
            # String concatenation with +
            if op == "+" and left_type.type_name == "string":
                if right_type.type_name != "string":
                    self.result.add_error(
                        f"Cannot concatenate string with {right_type}",
                        node,
                    )
            # Duration arithmetic
            elif left_type.type_name == "duration" or right_type.type_name == "duration":
                if op not in ("+", "-"):
                    self.result.add_error(
                        f"Invalid operation '{op}' on duration",
                        node,
                    )
            # Numeric arithmetic
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
    # Expression nodes
    # =========================================================================
    
    def visit_binary_expr(self, node: nodes.BinaryExprNode) -> Any:
        """Check binary expression type compatibility."""
        self.visit(node.left)
        self.visit(node.right)
        
        left_type = self._get_type(node.left)
        right_type = self._get_type(node.right)
        
        self._check_binary_types(node, left_type, right_type)
        return self.generic_visit(node)
    
    def visit_unary_expr(self, node: nodes.UnaryExprNode) -> Any:
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
    
    def visit_variable_decl(self, node: nodes.VariableDecl) -> Any:
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
    
    def visit_assignment_stmt(self, node: nodes.AssignmentStmt) -> Any:
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
    
    def visit_function_call(self, node: nodes.FunctionCallNode) -> Any:
        """Check function argument types match parameters."""
        func_name = node.callee if isinstance(node.callee, str) else getattr(node.callee, "name", "")
        
        if func_name in self.type_info.function_sigs:
            param_types, _ = self.type_info.function_sigs[func_name]
            
            # Check argument count
            if len(node.arguments) != len(param_types):
                self.result.add_error(
                    f"Function '{func_name}' expects {len(param_types)} arguments, got {len(node.arguments)}",
                    node,
                )
            else:
                # Check each argument type
                for i, (arg, expected_type) in enumerate(zip(node.arguments, param_types)):
                    self.visit(arg)
                    arg_type = self._get_type(arg)
                    if not self._types_compatible(expected_type, arg_type):
                        self.result.add_error(
                            f"Argument {i + 1} of '{func_name}' expected {expected_type}, got {arg_type}",
                            arg,
                        )
        else:
            for arg in node.arguments:
                self.visit(arg)
        
        return self.generic_visit(node)
    
    def visit_function_def(self, node: nodes.FunctionDefNode) -> Any:
        """Check function body return statements match declared return type."""
        if node.return_type:
            from yuho.ast.type_inference import TypeInferenceVisitor
            # Get return type from type info
            if node.name in self.type_info.function_sigs:
                _, return_type = self.type_info.function_sigs[node.name]
                self._current_function_return = return_type
            else:
                self._current_function_return = VOID_TYPE
        else:
            self._current_function_return = VOID_TYPE
        
        # Visit body
        if node.body:
            self.visit(node.body)
        
        self._current_function_return = None
        return self.generic_visit(node)
    
    def visit_return_stmt(self, node: nodes.ReturnStmt) -> Any:
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
    
    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        """Check all match arms have consistent types."""
        if node.scrutinee:
            self.visit(node.scrutinee)
        
        arm_types: List[TypeAnnotation] = []
        for arm in node.arms:
            self.visit(arm)
            arm_type = self._get_type(arm)
            if arm_type != PASS_TYPE and arm_type != UNKNOWN_TYPE:
                arm_types.append(arm_type)
        
        # Check all non-pass arms have the same type
        if len(arm_types) > 1:
            first_type = arm_types[0]
            for i, arm_type in enumerate(arm_types[1:], 1):
                if not self._types_compatible(first_type, arm_type):
                    self.result.add_error(
                        f"Match arm {i + 1} has type {arm_type}, expected {first_type}",
                        node.arms[i] if i < len(node.arms) else node,
                        severity="warning",
                    )
        
        return self.generic_visit(node)
    
    def visit_match_arm(self, node: nodes.MatchArm) -> Any:
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
    
    def visit_struct_literal(self, node: nodes.StructLiteralNode) -> Any:
        """Check struct field assignments match field types."""
        if node.type_name and node.type_name in self.type_info.struct_defs:
            struct_fields = self.type_info.struct_defs[node.type_name]
            
            for field_assign in node.field_assignments:
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
            for field_assign in node.field_assignments:
                self.visit(field_assign)
        
        return self.generic_visit(node)
    
    # =========================================================================
    # Module entry point
    # =========================================================================
    
    def visit_module(self, node: nodes.ModuleNode) -> Any:
        """Entry point: check all declarations."""
        for decl in node.declarations:
            self.visit(decl)
        return self.result
