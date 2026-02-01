"""
Transformer base class for immutable AST transformation.

Unlike Visitor which traverses without returning new nodes,
Transformer returns new AST nodes allowing immutable transformations.
"""

from typing import Any, Optional, Tuple, List

from yuho.ast import nodes


class Transformer:
    """
    Base transformer class for immutable AST transformation.

    Each transform_* method returns a new node (or the same node if unchanged).
    The default implementation recursively transforms children and reconstructs
    the node only if children changed.

    Usage:
        class ConstantFolder(Transformer):
            def transform_binary_expr(self, node):
                node = super().transform_binary_expr(node)
                if isinstance(node.left, nodes.IntLit) and isinstance(node.right, nodes.IntLit):
                    if node.operator == '+':
                        return nodes.IntLit(
                            value=node.left.value + node.right.value,
                            source_location=node.source_location
                        )
                return node

        folder = ConstantFolder()
        new_ast = folder.transform(ast)
    """

    def transform(self, node: nodes.ASTNode) -> nodes.ASTNode:
        """
        Dispatch to the appropriate transform_* method.

        This is the main entry point for transforming a node.
        """
        return node.accept(self)

    def _transform_children(self, children: List[nodes.ASTNode]) -> Tuple[Tuple[nodes.ASTNode, ...], bool]:
        """
        Transform a list of children and return whether any changed.

        Returns (transformed_tuple, changed).
        """
        transformed = []
        changed = False
        for child in children:
            new_child = self.transform(child)
            if new_child is not child:
                changed = True
            transformed.append(new_child)
        return tuple(transformed), changed

    # =========================================================================
    # Type nodes
    # =========================================================================

    def transform_type(self, node: nodes.TypeNode) -> nodes.TypeNode:
        return node

    def transform_builtin_type(self, node: nodes.BuiltinType) -> nodes.BuiltinType:
        return node

    def transform_named_type(self, node: nodes.NamedType) -> nodes.NamedType:
        return node

    def transform_generic_type(self, node: nodes.GenericType) -> nodes.GenericType:
        new_args, changed = self._transform_children(list(node.type_args))
        if changed:
            return nodes.GenericType(
                base=node.base,
                type_args=new_args,
                source_location=node.source_location,
            )
        return node

    def transform_optional_type(self, node: nodes.OptionalType) -> nodes.OptionalType:
        new_inner = self.transform(node.inner)
        if new_inner is not node.inner:
            return nodes.OptionalType(
                inner=new_inner,
                source_location=node.source_location,
            )
        return node

    def transform_array_type(self, node: nodes.ArrayType) -> nodes.ArrayType:
        new_elem = self.transform(node.element_type)
        if new_elem is not node.element_type:
            return nodes.ArrayType(
                element_type=new_elem,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Literal nodes (typically unchanged)
    # =========================================================================

    def transform_int_lit(self, node: nodes.IntLit) -> nodes.IntLit:
        return node

    def transform_float_lit(self, node: nodes.FloatLit) -> nodes.FloatLit:
        return node

    def transform_bool_lit(self, node: nodes.BoolLit) -> nodes.BoolLit:
        return node

    def transform_string_lit(self, node: nodes.StringLit) -> nodes.StringLit:
        return node

    def transform_money(self, node: nodes.MoneyNode) -> nodes.MoneyNode:
        return node

    def transform_percent(self, node: nodes.PercentNode) -> nodes.PercentNode:
        return node

    def transform_date(self, node: nodes.DateNode) -> nodes.DateNode:
        return node

    def transform_duration(self, node: nodes.DurationNode) -> nodes.DurationNode:
        return node

    # =========================================================================
    # Expression nodes
    # =========================================================================

    def transform_identifier(self, node: nodes.IdentifierNode) -> nodes.IdentifierNode:
        return node

    def transform_field_access(self, node: nodes.FieldAccessNode) -> nodes.ASTNode:
        new_base = self.transform(node.base)
        if new_base is not node.base:
            return nodes.FieldAccessNode(
                base=new_base,
                field_name=node.field_name,
                source_location=node.source_location,
            )
        return node

    def transform_index_access(self, node: nodes.IndexAccessNode) -> nodes.ASTNode:
        new_base = self.transform(node.base)
        new_index = self.transform(node.index)
        if new_base is not node.base or new_index is not node.index:
            return nodes.IndexAccessNode(
                base=new_base,
                index=new_index,
                source_location=node.source_location,
            )
        return node

    def transform_function_call(self, node: nodes.FunctionCallNode) -> nodes.ASTNode:
        new_callee = self.transform(node.callee)
        new_args, args_changed = self._transform_children(list(node.args))
        if new_callee is not node.callee or args_changed:
            return nodes.FunctionCallNode(
                callee=new_callee,
                args=new_args,
                source_location=node.source_location,
            )
        return node

    def transform_binary_expr(self, node: nodes.BinaryExprNode) -> nodes.ASTNode:
        new_left = self.transform(node.left)
        new_right = self.transform(node.right)
        if new_left is not node.left or new_right is not node.right:
            return nodes.BinaryExprNode(
                left=new_left,
                operator=node.operator,
                right=new_right,
                source_location=node.source_location,
            )
        return node

    def transform_unary_expr(self, node: nodes.UnaryExprNode) -> nodes.ASTNode:
        new_operand = self.transform(node.operand)
        if new_operand is not node.operand:
            return nodes.UnaryExprNode(
                operator=node.operator,
                operand=new_operand,
                source_location=node.source_location,
            )
        return node

    def transform_pass_expr(self, node: nodes.PassExprNode) -> nodes.PassExprNode:
        return node

    # =========================================================================
    # Pattern nodes
    # =========================================================================

    def transform_pattern(self, node: nodes.PatternNode) -> nodes.PatternNode:
        return node

    def transform_wildcard_pattern(self, node: nodes.WildcardPattern) -> nodes.WildcardPattern:
        return node

    def transform_literal_pattern(self, node: nodes.LiteralPattern) -> nodes.LiteralPattern:
        new_lit = self.transform(node.literal)
        if new_lit is not node.literal:
            return nodes.LiteralPattern(
                literal=new_lit,
                source_location=node.source_location,
            )
        return node

    def transform_binding_pattern(self, node: nodes.BindingPattern) -> nodes.BindingPattern:
        return node

    def transform_field_pattern(self, node: nodes.FieldPattern) -> nodes.FieldPattern:
        if node.pattern:
            new_pattern = self.transform(node.pattern)
            if new_pattern is not node.pattern:
                return nodes.FieldPattern(
                    name=node.name,
                    pattern=new_pattern,
                    source_location=node.source_location,
                )
        return node

    def transform_struct_pattern(self, node: nodes.StructPattern) -> nodes.StructPattern:
        new_fields, changed = self._transform_children(list(node.fields))
        if changed:
            return nodes.StructPattern(
                type_name=node.type_name,
                fields=new_fields,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Match expression
    # =========================================================================

    def transform_match_arm(self, node: nodes.MatchArm) -> nodes.MatchArm:
        new_pattern = self.transform(node.pattern)
        new_guard = self.transform(node.guard) if node.guard else None
        new_body = self.transform(node.body)

        if (new_pattern is not node.pattern or
            new_guard is not node.guard or
            new_body is not node.body):
            return nodes.MatchArm(
                pattern=new_pattern,
                guard=new_guard,
                body=new_body,
                source_location=node.source_location,
            )
        return node

    def transform_match_expr(self, node: nodes.MatchExprNode) -> nodes.ASTNode:
        new_scrutinee = self.transform(node.scrutinee) if node.scrutinee else None
        new_arms, changed = self._transform_children(list(node.arms))

        if new_scrutinee is not node.scrutinee or changed:
            return nodes.MatchExprNode(
                scrutinee=new_scrutinee,
                arms=new_arms,
                ensure_exhaustiveness=node.ensure_exhaustiveness,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Struct definition and literal
    # =========================================================================

    def transform_field_def(self, node: nodes.FieldDef) -> nodes.FieldDef:
        new_type = self.transform(node.type_annotation)
        if new_type is not node.type_annotation:
            return nodes.FieldDef(
                type_annotation=new_type,
                name=node.name,
                source_location=node.source_location,
            )
        return node

    def transform_struct_def(self, node: nodes.StructDefNode) -> nodes.StructDefNode:
        new_fields, changed = self._transform_children(list(node.fields))
        if changed:
            return nodes.StructDefNode(
                name=node.name,
                fields=new_fields,
                type_params=node.type_params,
                source_location=node.source_location,
            )
        return node

    def transform_field_assignment(self, node: nodes.FieldAssignment) -> nodes.FieldAssignment:
        new_value = self.transform(node.value)
        if new_value is not node.value:
            return nodes.FieldAssignment(
                name=node.name,
                value=new_value,
                source_location=node.source_location,
            )
        return node

    def transform_struct_literal(self, node: nodes.StructLiteralNode) -> nodes.ASTNode:
        new_fields, changed = self._transform_children(list(node.field_values))
        if changed:
            return nodes.StructLiteralNode(
                struct_name=node.struct_name,
                field_values=new_fields,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Function definition
    # =========================================================================

    def transform_param_def(self, node: nodes.ParamDef) -> nodes.ParamDef:
        new_type = self.transform(node.type_annotation)
        if new_type is not node.type_annotation:
            return nodes.ParamDef(
                type_annotation=new_type,
                name=node.name,
                source_location=node.source_location,
            )
        return node

    def transform_block(self, node: nodes.Block) -> nodes.Block:
        new_stmts, changed = self._transform_children(list(node.statements))
        if changed:
            return nodes.Block(
                statements=new_stmts,
                source_location=node.source_location,
            )
        return node

    def transform_function_def(self, node: nodes.FunctionDefNode) -> nodes.FunctionDefNode:
        new_params, params_changed = self._transform_children(list(node.params))
        new_return_type = self.transform(node.return_type) if node.return_type else None
        new_body = self.transform(node.body)

        if (params_changed or
            new_return_type is not node.return_type or
            new_body is not node.body):
            return nodes.FunctionDefNode(
                name=node.name,
                params=new_params,
                return_type=new_return_type,
                body=new_body,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Statements
    # =========================================================================

    def transform_variable_decl(self, node: nodes.VariableDecl) -> nodes.VariableDecl:
        new_type = self.transform(node.type_annotation)
        new_value = self.transform(node.value) if node.value else None

        if new_type is not node.type_annotation or new_value is not node.value:
            return nodes.VariableDecl(
                type_annotation=new_type,
                name=node.name,
                value=new_value,
                source_location=node.source_location,
            )
        return node

    def transform_assignment_stmt(self, node: nodes.AssignmentStmt) -> nodes.AssignmentStmt:
        new_target = self.transform(node.target)
        new_value = self.transform(node.value)

        if new_target is not node.target or new_value is not node.value:
            return nodes.AssignmentStmt(
                target=new_target,
                value=new_value,
                source_location=node.source_location,
            )
        return node

    def transform_return_stmt(self, node: nodes.ReturnStmt) -> nodes.ReturnStmt:
        new_value = self.transform(node.value) if node.value else None
        if new_value is not node.value:
            return nodes.ReturnStmt(
                value=new_value,
                source_location=node.source_location,
            )
        return node

    def transform_pass_stmt(self, node: nodes.PassStmt) -> nodes.PassStmt:
        return node

    def transform_expression_stmt(self, node: nodes.ExpressionStmt) -> nodes.ExpressionStmt:
        new_expr = self.transform(node.expression)
        if new_expr is not node.expression:
            return nodes.ExpressionStmt(
                expression=new_expr,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Statute-specific nodes
    # =========================================================================

    def transform_definition_entry(self, node: nodes.DefinitionEntry) -> nodes.DefinitionEntry:
        new_def = self.transform(node.definition)
        if new_def is not node.definition:
            return nodes.DefinitionEntry(
                term=node.term,
                definition=new_def,
                source_location=node.source_location,
            )
        return node

    def transform_element(self, node: nodes.ElementNode) -> nodes.ElementNode:
        new_desc = self.transform(node.description)
        if new_desc is not node.description:
            return nodes.ElementNode(
                element_type=node.element_type,
                name=node.name,
                description=new_desc,
                source_location=node.source_location,
            )
        return node

    def transform_penalty(self, node: nodes.PenaltyNode) -> nodes.PenaltyNode:
        # Penalties contain immutable duration/money nodes, typically unchanged
        return node

    def transform_illustration(self, node: nodes.IllustrationNode) -> nodes.IllustrationNode:
        new_desc = self.transform(node.description)
        if new_desc is not node.description:
            return nodes.IllustrationNode(
                label=node.label,
                description=new_desc,
                source_location=node.source_location,
            )
        return node

    def transform_statute(self, node: nodes.StatuteNode) -> nodes.StatuteNode:
        new_title = self.transform(node.title) if node.title else None
        new_defs, defs_changed = self._transform_children(list(node.definitions))
        new_elems, elems_changed = self._transform_children(list(node.elements))
        new_penalty = self.transform(node.penalty) if node.penalty else None
        new_illus, illus_changed = self._transform_children(list(node.illustrations))

        if (new_title is not node.title or
            defs_changed or
            elems_changed or
            new_penalty is not node.penalty or
            illus_changed):
            return nodes.StatuteNode(
                section_number=node.section_number,
                title=new_title,
                definitions=new_defs,
                elements=new_elems,
                penalty=new_penalty,
                illustrations=new_illus,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Import and module
    # =========================================================================

    def transform_import(self, node: nodes.ImportNode) -> nodes.ImportNode:
        return node

    def transform_module(self, node: nodes.ModuleNode) -> nodes.ModuleNode:
        new_imports, imports_changed = self._transform_children(list(node.imports))
        new_types, types_changed = self._transform_children(list(node.type_defs))
        new_funcs, funcs_changed = self._transform_children(list(node.function_defs))
        new_statutes, statutes_changed = self._transform_children(list(node.statutes))
        new_vars, vars_changed = self._transform_children(list(node.variables))

        if (imports_changed or types_changed or funcs_changed or
            statutes_changed or vars_changed):
            return nodes.ModuleNode(
                imports=new_imports,
                type_defs=new_types,
                function_defs=new_funcs,
                statutes=new_statutes,
                variables=new_vars,
                source_location=node.source_location,
            )
        return node
