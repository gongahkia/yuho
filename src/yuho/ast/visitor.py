"""
Visitor base class for AST traversal.

Provides default implementations that traverse all child nodes,
allowing subclasses to override only the methods they need.
"""

from typing import Any, TypeVar

from yuho.ast import nodes

T = TypeVar("T")


class Visitor:
    """
    Base visitor class for AST traversal.

    Default implementations visit all child nodes and return None.
    Subclasses can override specific visit_* methods to implement
    custom behavior.

    Usage:
        class MyVisitor(Visitor):
            def visit_struct_def(self, node):
                print(f"Found struct: {node.name}")
                return self.generic_visit(node)

        visitor = MyVisitor()
        module.accept(visitor)
    """

    def visit(self, node: nodes.ASTNode) -> Any:
        """
        Dispatch to the appropriate visit_* method.

        This is the main entry point for visiting a node.
        """
        return node.accept(self)

    def generic_visit(self, node: nodes.ASTNode) -> Any:
        """
        Default visitor that traverses all children.

        Override this to change default traversal behavior.
        """
        for child in node.children():
            self.visit(child)
        return None

    # =========================================================================
    # Type nodes
    # =========================================================================

    def visit_type(self, node: nodes.TypeNode) -> Any:
        return self.generic_visit(node)

    def visit_builtin_type(self, node: nodes.BuiltinType) -> Any:
        return self.generic_visit(node)

    def visit_named_type(self, node: nodes.NamedType) -> Any:
        return self.generic_visit(node)

    def visit_generic_type(self, node: nodes.GenericType) -> Any:
        return self.generic_visit(node)

    def visit_optional_type(self, node: nodes.OptionalType) -> Any:
        return self.generic_visit(node)

    def visit_array_type(self, node: nodes.ArrayType) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Literal nodes
    # =========================================================================

    def visit_int_lit(self, node: nodes.IntLit) -> Any:
        return self.generic_visit(node)

    def visit_float_lit(self, node: nodes.FloatLit) -> Any:
        return self.generic_visit(node)

    def visit_bool_lit(self, node: nodes.BoolLit) -> Any:
        return self.generic_visit(node)

    def visit_string_lit(self, node: nodes.StringLit) -> Any:
        return self.generic_visit(node)

    def visit_money(self, node: nodes.MoneyNode) -> Any:
        return self.generic_visit(node)

    def visit_percent(self, node: nodes.PercentNode) -> Any:
        return self.generic_visit(node)

    def visit_date(self, node: nodes.DateNode) -> Any:
        return self.generic_visit(node)

    def visit_duration(self, node: nodes.DurationNode) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Expression nodes
    # =========================================================================

    def visit_identifier(self, node: nodes.IdentifierNode) -> Any:
        return self.generic_visit(node)

    def visit_field_access(self, node: nodes.FieldAccessNode) -> Any:
        return self.generic_visit(node)

    def visit_index_access(self, node: nodes.IndexAccessNode) -> Any:
        return self.generic_visit(node)

    def visit_function_call(self, node: nodes.FunctionCallNode) -> Any:
        return self.generic_visit(node)

    def visit_binary_expr(self, node: nodes.BinaryExprNode) -> Any:
        return self.generic_visit(node)

    def visit_unary_expr(self, node: nodes.UnaryExprNode) -> Any:
        return self.generic_visit(node)

    def visit_pass_expr(self, node: nodes.PassExprNode) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Pattern nodes
    # =========================================================================

    def visit_pattern(self, node: nodes.PatternNode) -> Any:
        return self.generic_visit(node)

    def visit_wildcard_pattern(self, node: nodes.WildcardPattern) -> Any:
        return self.generic_visit(node)

    def visit_literal_pattern(self, node: nodes.LiteralPattern) -> Any:
        return self.generic_visit(node)

    def visit_binding_pattern(self, node: nodes.BindingPattern) -> Any:
        return self.generic_visit(node)

    def visit_field_pattern(self, node: nodes.FieldPattern) -> Any:
        return self.generic_visit(node)

    def visit_struct_pattern(self, node: nodes.StructPattern) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Match expression
    # =========================================================================

    def visit_match_arm(self, node: nodes.MatchArm) -> Any:
        return self.generic_visit(node)

    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Struct definition and literal
    # =========================================================================

    def visit_field_def(self, node: nodes.FieldDef) -> Any:
        return self.generic_visit(node)

    def visit_struct_def(self, node: nodes.StructDefNode) -> Any:
        return self.generic_visit(node)

    def visit_field_assignment(self, node: nodes.FieldAssignment) -> Any:
        return self.generic_visit(node)

    def visit_struct_literal(self, node: nodes.StructLiteralNode) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Function definition
    # =========================================================================

    def visit_param_def(self, node: nodes.ParamDef) -> Any:
        return self.generic_visit(node)

    def visit_block(self, node: nodes.Block) -> Any:
        return self.generic_visit(node)

    def visit_function_def(self, node: nodes.FunctionDefNode) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Statements
    # =========================================================================

    def visit_variable_decl(self, node: nodes.VariableDecl) -> Any:
        return self.generic_visit(node)

    def visit_assignment_stmt(self, node: nodes.AssignmentStmt) -> Any:
        return self.generic_visit(node)

    def visit_return_stmt(self, node: nodes.ReturnStmt) -> Any:
        return self.generic_visit(node)

    def visit_pass_stmt(self, node: nodes.PassStmt) -> Any:
        return self.generic_visit(node)

    def visit_expression_stmt(self, node: nodes.ExpressionStmt) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Statute-specific nodes
    # =========================================================================

    def visit_definition_entry(self, node: nodes.DefinitionEntry) -> Any:
        return self.generic_visit(node)

    def visit_element(self, node: nodes.ElementNode) -> Any:
        return self.generic_visit(node)

    def visit_penalty(self, node: nodes.PenaltyNode) -> Any:
        return self.generic_visit(node)

    def visit_illustration(self, node: nodes.IllustrationNode) -> Any:
        return self.generic_visit(node)

    def visit_statute(self, node: nodes.StatuteNode) -> Any:
        return self.generic_visit(node)

    # =========================================================================
    # Import and module
    # =========================================================================

    def visit_import(self, node: nodes.ImportNode) -> Any:
        return self.generic_visit(node)

    def visit_module(self, node: nodes.ModuleNode) -> Any:
        return self.generic_visit(node)
