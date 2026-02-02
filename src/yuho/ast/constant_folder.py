"""
Constant folding optimization for Yuho AST.

Evaluates compile-time constant expressions and replaces them with
their literal values. This includes:
- Arithmetic operations on numeric literals (+, -, *, /)
- Boolean operations on boolean literals (&&, ||, !)
- Comparison operations on numeric literals (==, !=, <, >, <=, >=)
- String concatenation on string literals (+)
- Negation of numeric literals (-)
"""

from typing import Optional, Union

from yuho.ast import nodes
from yuho.ast.transformer import Transformer


class ConstantFoldingError(Exception):
    """Error during constant folding (e.g., division by zero)."""
    pass


class ConstantFolder(Transformer):
    """
    AST transformer that evaluates compile-time constant expressions.

    Traverses the AST and replaces constant expressions with their
    computed literal values. Preserves source location information
    for error reporting.

    Usage:
        folder = ConstantFolder()
        optimized_ast = folder.transform(ast)

    Handles:
        - Integer arithmetic: 1 + 2 -> 3
        - Float arithmetic: 1.5 * 2.0 -> 3.0
        - Boolean logic: TRUE && FALSE -> FALSE
        - Comparisons: 5 > 3 -> TRUE
        - String concatenation: "a" + "b" -> "ab"
        - Unary negation: -5 -> IntLit(-5)
        - Unary not: !TRUE -> FALSE
    """

    def __init__(self, *, fold_division_by_zero: bool = False):
        """
        Initialize the constant folder.

        Args:
            fold_division_by_zero: If True, division by zero will raise
                ConstantFoldingError. If False (default), the expression
                is left unchanged for runtime error handling.
        """
        self.fold_division_by_zero = fold_division_by_zero

    def transform_binary_expr(self, node: nodes.BinaryExprNode) -> nodes.ASTNode:
        """
        Transform binary expressions, folding constants where possible.

        First transforms children (bottom-up folding), then attempts
        to evaluate if both operands are literals.
        """
        # First, transform children to fold nested expressions
        node = super().transform_binary_expr(node)

        # Check if both operands are now literals
        left = node.left
        right = node.right
        op = node.operator

        # Integer operations
        if isinstance(left, nodes.IntLit) and isinstance(right, nodes.IntLit):
            result = self._fold_int_binary(left.value, op, right.value, node)
            if result is not None:
                return result

        # Float operations (including mixed int/float)
        if self._is_numeric_literal(left) and self._is_numeric_literal(right):
            left_val = self._get_numeric_value(left)
            right_val = self._get_numeric_value(right)
            result = self._fold_float_binary(left_val, op, right_val, node)
            if result is not None:
                return result

        # Boolean operations
        if isinstance(left, nodes.BoolLit) and isinstance(right, nodes.BoolLit):
            result = self._fold_bool_binary(left.value, op, right.value, node)
            if result is not None:
                return result

        # String concatenation
        if isinstance(left, nodes.StringLit) and isinstance(right, nodes.StringLit):
            if op == "+":
                return nodes.StringLit(
                    value=left.value + right.value,
                    source_location=node.source_location,
                )

        # Cannot fold, return transformed node
        return node

    def transform_unary_expr(self, node: nodes.UnaryExprNode) -> nodes.ASTNode:
        """
        Transform unary expressions, folding constants where possible.

        Handles:
            - Negation of numeric literals: -5 -> IntLit(-5)
            - Logical not of booleans: !TRUE -> FALSE
        """
        # First, transform the operand
        node = super().transform_unary_expr(node)

        operand = node.operand
        op = node.operator

        # Numeric negation
        if op == "-":
            if isinstance(operand, nodes.IntLit):
                return nodes.IntLit(
                    value=-operand.value,
                    source_location=node.source_location,
                )
            if isinstance(operand, nodes.FloatLit):
                return nodes.FloatLit(
                    value=-operand.value,
                    source_location=node.source_location,
                )

        # Logical not
        if op == "!":
            if isinstance(operand, nodes.BoolLit):
                return nodes.BoolLit(
                    value=not operand.value,
                    source_location=node.source_location,
                )

        # Cannot fold, return transformed node
        return node

    def _is_numeric_literal(self, node: nodes.ASTNode) -> bool:
        """Check if a node is a numeric literal (int or float)."""
        return isinstance(node, (nodes.IntLit, nodes.FloatLit))

    def _get_numeric_value(self, node: nodes.ASTNode) -> Union[int, float]:
        """Extract numeric value from an IntLit or FloatLit."""
        if isinstance(node, nodes.IntLit):
            return node.value
        if isinstance(node, nodes.FloatLit):
            return node.value
        raise TypeError(f"Expected numeric literal, got {type(node).__name__}")

    def _fold_int_binary(
        self,
        left: int,
        op: str,
        right: int,
        node: nodes.BinaryExprNode,
    ) -> Optional[nodes.ASTNode]:
        """Fold binary operations on two integers."""
        loc = node.source_location

        # Arithmetic operations
        if op == "+":
            return nodes.IntLit(value=left + right, source_location=loc)
        if op == "-":
            return nodes.IntLit(value=left - right, source_location=loc)
        if op == "*":
            return nodes.IntLit(value=left * right, source_location=loc)
        if op == "/":
            if right == 0:
                if self.fold_division_by_zero:
                    raise ConstantFoldingError(
                        f"Division by zero at {loc}" if loc else "Division by zero"
                    )
                return None  # Leave for runtime
            # Integer division
            return nodes.IntLit(value=left // right, source_location=loc)

        # Comparison operations
        if op == "==":
            return nodes.BoolLit(value=left == right, source_location=loc)
        if op == "!=":
            return nodes.BoolLit(value=left != right, source_location=loc)
        if op == "<":
            return nodes.BoolLit(value=left < right, source_location=loc)
        if op == ">":
            return nodes.BoolLit(value=left > right, source_location=loc)
        if op == "<=":
            return nodes.BoolLit(value=left <= right, source_location=loc)
        if op == ">=":
            return nodes.BoolLit(value=left >= right, source_location=loc)

        return None

    def _fold_float_binary(
        self,
        left: Union[int, float],
        op: str,
        right: Union[int, float],
        node: nodes.BinaryExprNode,
    ) -> Optional[nodes.ASTNode]:
        """Fold binary operations involving at least one float."""
        loc = node.source_location

        # If both are actually ints, let _fold_int_binary handle it
        if isinstance(left, int) and isinstance(right, int):
            return None

        # Arithmetic operations (result is float)
        if op == "+":
            return nodes.FloatLit(value=float(left + right), source_location=loc)
        if op == "-":
            return nodes.FloatLit(value=float(left - right), source_location=loc)
        if op == "*":
            return nodes.FloatLit(value=float(left * right), source_location=loc)
        if op == "/":
            if right == 0:
                if self.fold_division_by_zero:
                    raise ConstantFoldingError(
                        f"Division by zero at {loc}" if loc else "Division by zero"
                    )
                return None  # Leave for runtime
            return nodes.FloatLit(value=float(left) / float(right), source_location=loc)

        # Comparison operations (result is bool)
        if op == "==":
            return nodes.BoolLit(value=left == right, source_location=loc)
        if op == "!=":
            return nodes.BoolLit(value=left != right, source_location=loc)
        if op == "<":
            return nodes.BoolLit(value=left < right, source_location=loc)
        if op == ">":
            return nodes.BoolLit(value=left > right, source_location=loc)
        if op == "<=":
            return nodes.BoolLit(value=left <= right, source_location=loc)
        if op == ">=":
            return nodes.BoolLit(value=left >= right, source_location=loc)

        return None

    def _fold_bool_binary(
        self,
        left: bool,
        op: str,
        right: bool,
        node: nodes.BinaryExprNode,
    ) -> Optional[nodes.ASTNode]:
        """Fold binary operations on two booleans."""
        loc = node.source_location

        if op == "&&":
            return nodes.BoolLit(value=left and right, source_location=loc)
        if op == "||":
            return nodes.BoolLit(value=left or right, source_location=loc)
        if op == "==":
            return nodes.BoolLit(value=left == right, source_location=loc)
        if op == "!=":
            return nodes.BoolLit(value=left != right, source_location=loc)

        return None


def fold_constants(ast: nodes.ASTNode, **kwargs) -> nodes.ASTNode:
    """
    Convenience function to fold constants in an AST.

    Args:
        ast: The AST to transform.
        **kwargs: Options passed to ConstantFolder constructor.

    Returns:
        A new AST with constant expressions folded.

    Example:
        from yuho.ast.constant_folder import fold_constants
        optimized = fold_constants(parsed_ast)
    """
    folder = ConstantFolder(**kwargs)
    return folder.transform(ast)
