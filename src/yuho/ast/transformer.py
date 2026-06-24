"""
Transformer base class for immutable AST transformation.

Unlike Visitor which traverses without returning new nodes,
Transformer returns new AST nodes allowing immutable transformations.
"""

from typing import Any, List, Optional, Tuple, TypeVar, cast

from yuho.ast import nodes
from yuho.ast.visitor import Visitor

TNode = TypeVar("TNode", bound=nodes.ASTNode)


class Transformer(Visitor):
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

    # visit_* aliases so node.accept(self) dispatches correctly
    def visit_builtin_type(self, node):
        return self.transform_builtin_type(node)

    def visit_named_type(self, node):
        return self.transform_named_type(node)

    def visit_generic_type(self, node):
        return self.transform_generic_type(node)

    def visit_optional_type(self, node):
        return self.transform_optional_type(node)

    def visit_array_type(self, node):
        return self.transform_array_type(node)

    def visit_int_lit(self, node):
        return self.transform_int_lit(node)

    def visit_float_lit(self, node):
        return self.transform_float_lit(node)

    def visit_bool_lit(self, node):
        return self.transform_bool_lit(node)

    def visit_string_lit(self, node):
        return self.transform_string_lit(node)

    def visit_money(self, node):
        return self.transform_money(node)

    def visit_percent(self, node):
        return self.transform_percent(node)

    def visit_date(self, node):
        return self.transform_date(node)

    def visit_duration(self, node):
        return self.transform_duration(node)

    def visit_identifier(self, node):
        return self.transform_identifier(node)

    def visit_field_access(self, node):
        return self.transform_field_access(node)

    def visit_index_access(self, node):
        return self.transform_index_access(node)

    def visit_function_call(self, node):
        return self.transform_function_call(node)

    def visit_exists_at_most(self, node):
        return self.transform_exists_at_most(node)

    def visit_binary_expr(self, node):
        return self.transform_binary_expr(node)

    def visit_unary_expr(self, node):
        return self.transform_unary_expr(node)

    def visit_pass_expr(self, node):
        return self.transform_pass_expr(node)

    def visit_wildcard_pattern(self, node):
        return self.transform_wildcard_pattern(node)

    def visit_literal_pattern(self, node):
        return self.transform_literal_pattern(node)

    def visit_binding_pattern(self, node):
        return self.transform_binding_pattern(node)

    def visit_field_pattern(self, node):
        return self.transform_field_pattern(node)

    def visit_struct_pattern(self, node):
        return self.transform_struct_pattern(node)

    def visit_match_arm(self, node):
        return self.transform_match_arm(node)

    def visit_match_expr(self, node):
        return self.transform_match_expr(node)

    def visit_field_def(self, node):
        return self.transform_field_def(node)

    def visit_struct_def(self, node):
        return self.transform_struct_def(node)

    def visit_field_assignment(self, node):
        return self.transform_field_assignment(node)

    def visit_struct_literal(self, node):
        return self.transform_struct_literal(node)

    def visit_fact_participant(self, node):
        return self.transform_fact_participant(node)

    def visit_fact_event(self, node):
        return self.transform_fact_event(node)

    def visit_param_def(self, node):
        return self.transform_param_def(node)

    def visit_block(self, node):
        return self.transform_block(node)

    def visit_function_def(self, node):
        return self.transform_function_def(node)

    def visit_variable_decl(self, node):
        return self.transform_variable_decl(node)

    def visit_assignment_stmt(self, node):
        return self.transform_assignment_stmt(node)

    def visit_return_stmt(self, node):
        return self.transform_return_stmt(node)

    def visit_pass_stmt(self, node):
        return self.transform_pass_stmt(node)

    def visit_expression_stmt(self, node):
        return self.transform_expression_stmt(node)

    def visit_definition_entry(self, node):
        return self.transform_definition_entry(node)

    def visit_interpretation(self, node):
        return self.transform_interpretation(node)

    def visit_element(self, node):
        return self.transform_element(node)

    def visit_civil_primitive(self, node):
        return self.transform_civil_primitive(node)

    def visit_element_group(self, node):
        return self.transform_element_group(node)

    def visit_penalty(self, node):
        return self.transform_penalty(node)

    def visit_illustration(self, node):
        return self.transform_illustration(node)

    def visit_exception(self, node):
        return self.transform_exception(node)

    def visit_case_treatment(self, node):
        return self.transform_case_treatment(node)

    def visit_caselaw(self, node):
        return self.transform_caselaw(node)

    def visit_statute(self, node):
        return self.transform_statute(node)

    def visit_jurisdiction(self, node):
        return self.transform_jurisdiction(node)

    def visit_import(self, node):
        return self.transform_import(node)

    def visit_module(self, node):
        return self.transform_module(node)

    def visit_assert_stmt(self, node):
        return node

    def visit_referencing_stmt(self, node):
        return node

    def _transform_children(
        self, children: List[nodes.ASTNode]
    ) -> Tuple[Tuple[nodes.ASTNode, ...], bool]:
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

    def _transform_typed(self, node: TNode) -> TNode:
        """Transform a node while preserving its declared static type."""
        return cast(TNode, self.transform(node))

    def _transform_optional_typed(self, node: Optional[TNode]) -> Optional[TNode]:
        """Transform an optional node while preserving its declared type."""
        if node is None:
            return None
        return cast(TNode, self.transform(node))

    def _transform_children_typed(self, children: List[TNode]) -> Tuple[Tuple[TNode, ...], bool]:
        """Transform a homogeneous child collection with a preserved element type."""
        transformed, changed = self._transform_children(cast(List[nodes.ASTNode], children))
        return cast(Tuple[TNode, ...], transformed), changed

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
        new_args, changed = self._transform_children_typed(list(node.type_args))
        if changed:
            return nodes.GenericType(
                base=node.base,
                type_args=new_args,
                source_location=node.source_location,
            )
        return node

    def transform_optional_type(self, node: nodes.OptionalType) -> nodes.OptionalType:
        new_inner = self._transform_typed(node.inner)
        if new_inner is not node.inner:
            return nodes.OptionalType(
                inner=new_inner,
                source_location=node.source_location,
            )
        return node

    def transform_array_type(self, node: nodes.ArrayType) -> nodes.ArrayType:
        new_elem = self._transform_typed(node.element_type)
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

    def transform_exists_at_most(self, node: nodes.ExistsAtMostNode) -> nodes.ASTNode:
        new_limit = self._transform_typed(node.limit)
        new_window = self._transform_typed(node.window)
        if new_limit is not node.limit or new_window is not node.window:
            return nodes.ExistsAtMostNode(
                limit=new_limit,
                window=new_window,
                source_location=node.source_location,
            )
        return node

    def transform_function_call(self, node: nodes.FunctionCallNode) -> nodes.ASTNode:
        new_callee = self._transform_typed(node.callee)
        new_args, args_changed = self._transform_children_typed(list(node.args))
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
            new_pattern = self._transform_typed(node.pattern)
            if new_pattern is not node.pattern:
                return nodes.FieldPattern(
                    name=node.name,
                    pattern=new_pattern,
                    source_location=node.source_location,
                )
        return node

    def transform_struct_pattern(self, node: nodes.StructPattern) -> nodes.StructPattern:
        new_fields, changed = self._transform_children_typed(list(node.fields))
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
        new_pattern = self._transform_typed(node.pattern)
        new_guard = self._transform_optional_typed(node.guard)
        new_body = self._transform_typed(node.body)

        if (
            new_pattern is not node.pattern
            or new_guard is not node.guard
            or new_body is not node.body
        ):
            return nodes.MatchArm(
                pattern=new_pattern,
                guard=new_guard,
                body=new_body,
                source_location=node.source_location,
            )
        return node

    def transform_match_expr(self, node: nodes.MatchExprNode) -> nodes.ASTNode:
        new_scrutinee = self._transform_optional_typed(node.scrutinee)
        new_arms, changed = self._transform_children_typed(list(node.arms))

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
        new_type = self._transform_typed(node.type_annotation)
        if new_type is not node.type_annotation:
            return nodes.FieldDef(
                type_annotation=new_type,
                name=node.name,
                doc_comment=node.doc_comment,
                agent=node.agent,
                patient=node.patient,
                source_location=node.source_location,
            )
        return node

    def transform_struct_def(self, node: nodes.StructDefNode) -> nodes.StructDefNode:
        new_fields, changed = self._transform_children_typed(list(node.fields))
        if changed:
            return nodes.StructDefNode(
                name=node.name,
                fields=new_fields,
                type_params=node.type_params,
                doc_comment=node.doc_comment,
                parent=node.parent,
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
        new_fields, changed = self._transform_children_typed(list(node.field_values))
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
        new_type = self._transform_typed(node.type_annotation)
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
        new_params, params_changed = self._transform_children_typed(list(node.params))
        new_return_type = self._transform_optional_typed(node.return_type)
        new_body = self._transform_typed(node.body)

        if params_changed or new_return_type is not node.return_type or new_body is not node.body:
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
        new_type = self._transform_typed(node.type_annotation)
        new_value = self._transform_optional_typed(node.value)

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
        new_def = self._transform_typed(node.definition)
        if new_def is not node.definition:
            return nodes.DefinitionEntry(
                term=node.term,
                definition=new_def,
                source_location=node.source_location,
            )
        return node

    def transform_interpretation(
        self, node: nodes.InterpretationNode
    ) -> nodes.InterpretationNode:
        new_reading = self._transform_typed(node.reading)
        new_citation = self._transform_optional_typed(node.citation)
        new_court = self._transform_optional_typed(node.court)
        if (
            new_reading is not node.reading
            or new_citation is not node.citation
            or new_court is not node.court
        ):
            return nodes.InterpretationNode(
                name=node.name,
                reading=new_reading,
                citation=new_citation,
                court=new_court,
                endorsement=node.endorsement,
                source_location=node.source_location,
            )
        return node

    def transform_element(self, node: nodes.ElementNode) -> nodes.ElementNode:
        new_desc = self.transform(node.description)
        new_interpretations, interpretations_changed = self._transform_children_typed(
            list(node.interpretations)
        )
        if new_desc is not node.description or interpretations_changed:
            return nodes.ElementNode(
                element_type=node.element_type,
                name=node.name,
                description=new_desc,
                caused_by=node.caused_by,
                burden=node.burden,
                burden_standard=node.burden_standard,
                doc_comment=node.doc_comment,
                actor=node.actor,
                patient=node.patient,
                interpretations=new_interpretations,
                agent=node.agent,
                source_location=node.source_location,
            )
        return node

    def transform_civil_primitive(
        self, node: nodes.CivilPrimitiveNode
    ) -> nodes.CivilPrimitiveNode:
        new_desc = self.transform(node.description)
        if new_desc is not node.description:
            return nodes.CivilPrimitiveNode(
                primitive_type=node.primitive_type,
                name=node.name,
                description=new_desc,
                doc_comment=node.doc_comment,
                agent=node.agent,
                patient=node.patient,
                source_location=node.source_location,
            )
        return node

    def transform_element_group(self, node: nodes.ElementGroupNode) -> nodes.ElementGroupNode:
        new_members, changed = self._transform_children_typed(list(node.members))
        if changed:
            return nodes.ElementGroupNode(
                combinator=node.combinator,
                members=new_members,
                source_location=node.source_location,
            )
        return node

    def transform_fact_participant(
        self, node: nodes.FactParticipantNode
    ) -> nodes.FactParticipantNode:
        new_type = self._transform_optional_typed(node.type_annotation)
        if new_type is not node.type_annotation:
            return nodes.FactParticipantNode(
                role=node.role,
                name=node.name,
                type_annotation=new_type,
                source_location=node.source_location,
            )
        return node

    def transform_fact_event(self, node: nodes.FactEventNode) -> nodes.FactEventNode:
        new_timestamp = self._transform_typed(node.timestamp)
        new_participants, participants_changed = self._transform_children_typed(
            list(node.participants)
        )
        if new_timestamp is not node.timestamp or participants_changed:
            return nodes.FactEventNode(
                name=node.name,
                action=node.action,
                timestamp=new_timestamp,
                participants=new_participants,
                meta=dict(node.meta),
                source_location=node.source_location,
            )
        return node

    def transform_penalty(self, node: nodes.PenaltyNode) -> nodes.PenaltyNode:
        return node

    def transform_exception(self, node: nodes.ExceptionNode) -> nodes.ExceptionNode:
        return node

    def transform_case_treatment(
        self, node: nodes.CaseTreatmentNode
    ) -> nodes.CaseTreatmentNode:
        new_target = self._transform_typed(node.target)
        new_citation = self._transform_optional_typed(node.citation)
        if new_target is not node.target or new_citation is not node.citation:
            return nodes.CaseTreatmentNode(
                kind=node.kind,
                target=new_target,
                citation=new_citation,
                source_location=node.source_location,
            )
        return node

    def transform_caselaw(self, node: nodes.CaseLawNode) -> nodes.CaseLawNode:
        new_case_name = self._transform_typed(node.case_name)
        new_citation = self._transform_optional_typed(node.citation)
        new_holding = self._transform_typed(node.holding)
        new_treatments, treatments_changed = self._transform_children_typed(
            list(node.treatments)
        )
        if (
            new_case_name is not node.case_name
            or new_citation is not node.citation
            or new_holding is not node.holding
            or treatments_changed
        ):
            return nodes.CaseLawNode(
                case_name=new_case_name,
                citation=new_citation,
                holding=new_holding,
                element_ref=node.element_ref,
                treatments=new_treatments,
                doctrine_role=node.doctrine_role,
                jurisdiction=node.jurisdiction,
                court_level=node.court_level,
                decision_date=node.decision_date,
                interpretive_effect=node.interpretive_effect,
                effect_fact=node.effect_fact,
                burden_shift=node.burden_shift,
                burden_shift_standard=node.burden_shift_standard,
                doc_comment=node.doc_comment,
                source_location=node.source_location,
            )
        return node

    def transform_illustration(self, node: nodes.IllustrationNode) -> nodes.IllustrationNode:
        new_desc = self._transform_typed(node.description)
        if new_desc is not node.description:
            return nodes.IllustrationNode(
                label=node.label,
                description=new_desc,
                source_location=node.source_location,
            )
        return node

    def transform_jurisdiction(self, node: nodes.JurisdictionNode) -> nodes.JurisdictionNode:
        return node

    def transform_statute(self, node: nodes.StatuteNode) -> nodes.StatuteNode:
        new_jurisdiction = self._transform_optional_typed(node.jurisdiction_node)
        new_title = self._transform_optional_typed(node.title)
        new_input_type = self._transform_optional_typed(node.input_type)
        new_output_type = self._transform_optional_typed(node.output_type)
        new_defs, defs_changed = self._transform_children_typed(list(node.definitions))
        new_elems, elems_changed = self._transform_children_typed(list(node.elements))
        new_penalty = self._transform_optional_typed(node.penalty)
        new_additional_penalties, additional_penalties_changed = self._transform_children_typed(
            list(node.additional_penalties)
        )
        new_illus, illus_changed = self._transform_children_typed(list(node.illustrations))
        new_exc, exc_changed = self._transform_children_typed(list(node.exceptions))
        new_cl, cl_changed = self._transform_children_typed(list(node.case_law))
        new_subsections, subsections_changed = self._transform_children_typed(
            list(node.subsections)
        )

        if (
            new_jurisdiction is not node.jurisdiction_node
            or new_title is not node.title
            or new_input_type is not node.input_type
            or new_output_type is not node.output_type
            or defs_changed
            or elems_changed
            or new_penalty is not node.penalty
            or additional_penalties_changed
            or illus_changed
            or exc_changed
            or cl_changed
            or subsections_changed
        ):
            return nodes.StatuteNode(
                section_number=node.section_number,
                title=new_title,
                definitions=new_defs,
                elements=new_elems,
                penalty=new_penalty,
                input_type=new_input_type,
                output_type=new_output_type,
                illustrations=new_illus,
                exceptions=new_exc,
                case_law=new_cl,
                subsections=new_subsections,
                additional_penalties=new_additional_penalties,
                doc_comment=node.doc_comment,
                jurisdiction=node.jurisdiction,
                jurisdiction_meta=node.jurisdiction_meta,
                jurisdiction_node=new_jurisdiction,
                effective_date=node.effective_date,
                effective_dates=node.effective_dates,
                repealed_date=node.repealed_date,
                subsumes=node.subsumes,
                amends=node.amends,
                parties=node.parties,
                temporal_constraints=node.temporal_constraints,
                annotations=node.annotations,
                source_location=node.source_location,
            )
        return node

    # =========================================================================
    # Import and module
    # =========================================================================

    def transform_import(self, node: nodes.ImportNode) -> nodes.ImportNode:
        return node

    def transform_module(self, node: nodes.ModuleNode) -> nodes.ModuleNode:
        new_imports, imports_changed = self._transform_children_typed(list(node.imports))
        new_types, types_changed = self._transform_children_typed(list(node.type_defs))
        new_funcs, funcs_changed = self._transform_children_typed(list(node.function_defs))
        new_statutes, statutes_changed = self._transform_children_typed(list(node.statutes))
        new_vars, vars_changed = self._transform_children_typed(list(node.variables))
        new_facts, facts_changed = self._transform_children_typed(list(node.fact_events))

        if (
            imports_changed
            or types_changed
            or funcs_changed
            or statutes_changed
            or vars_changed
            or facts_changed
        ):
            return nodes.ModuleNode(
                imports=new_imports,
                type_defs=new_types,
                function_defs=new_funcs,
                statutes=new_statutes,
                variables=new_vars,
                references=node.references,
                assertions=node.assertions,
                enum_defs=node.enum_defs,
                type_aliases=node.type_aliases,
                legal_tests=node.legal_tests,
                conflict_checks=node.conflict_checks,
                fact_events=new_facts,
                source_location=node.source_location,
            )
        return node
