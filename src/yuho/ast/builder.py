"""
ASTBuilder class that walks a tree-sitter Tree and constructs AST nodes.
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List, Tuple

from yuho.ast import nodes
from yuho.parser.source_location import SourceLocation


class ASTBuilder:
    """
    Builds Yuho AST from a tree-sitter parse tree.

    Usage:
        from yuho.parser import Parser
        from yuho.ast import ASTBuilder

        parser = Parser()
        result = parser.parse(source_code)

        builder = ASTBuilder(source_code, file_path)
        module = builder.build(result.tree.root_node)
    """

    def __init__(self, source: str, file: str = "<string>"):
        """
        Initialize the builder.

        Args:
            source: The original source code (needed to extract text from nodes)
            file: File path for source locations
        """
        self.source = source
        self.source_bytes = source.encode("utf-8")
        self.file = file
        self._doc_comment_lines = self._extract_doc_comments()

    def _extract_doc_comments(self) -> dict:
        """Extract /// doc-comments indexed by end line number."""
        result = {} # line_number -> comment text
        lines = self.source.split("\n")
        comment_block = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("///"):
                comment_block.append(stripped[3:].strip())
            else:
                if comment_block:
                    result[i] = "\n".join(comment_block) # key = first non-comment line
                    comment_block = []
        return result

    def _get_doc_comment(self, node) -> Optional[str]:
        """Get doc-comment for a node from named children or line proximity."""
        doc_nodes = [c for c in node.children if c.type == "doc_comment"]
        if doc_nodes:
            lines = []
            for dn in doc_nodes:
                text = self._text(dn)
                lines.append(text.lstrip("/").strip())
            return "\n".join(lines)
        if not self._doc_comment_lines:
            return None
        start_line = node.start_point[0]
        return self._doc_comment_lines.get(start_line)

    @staticmethod
    def _extract_jurisdiction(doc: Optional[str]) -> tuple:
        """Extract @jurisdiction and @meta annotations from doc-comment."""
        if not doc:
            return None, None
        jurisdiction = None
        meta = {}
        for line in doc.split("\n"):
            stripped = line.strip()
            if stripped.startswith("@jurisdiction "):
                jurisdiction = stripped[len("@jurisdiction "):].strip()
            elif stripped.startswith("@meta "):
                rest = stripped[len("@meta "):].strip()
                if "=" in rest:
                    k, _, v = rest.partition("=")
                    meta[k.strip()] = v.strip()
        return jurisdiction, meta if meta else None

    def build(self, root_node) -> nodes.ModuleNode:
        """
        Build a ModuleNode from a tree-sitter root node.

        Args:
            root_node: The root node from tree-sitter (should be 'source_file')

        Returns:
            A ModuleNode representing the complete AST
        """
        return self._build_module(root_node)

    def _loc(self, node) -> SourceLocation:
        """Extract source location from a tree-sitter node."""
        return SourceLocation.from_tree_sitter_node(node, self.file)

    def _text(self, node) -> str:
        """Extract text content from a tree-sitter node."""
        return self.source_bytes[node.start_byte:node.end_byte].decode("utf-8")

    def _children_by_type(self, node, *types: str):
        """Get all children matching the given types."""
        return [c for c in node.children if c.type in types]

    def _child_by_type(self, node, *types: str):
        """Get first child matching the given types, or None."""
        for c in node.children:
            if c.type in types:
                return c
        return None

    def _child_by_field(self, node, field_name: str):
        """Get child by field name."""
        return node.child_by_field_name(field_name)

    # =========================================================================
    # Module and top-level declarations
    # =========================================================================

    def _build_module(self, node) -> nodes.ModuleNode:
        """Build ModuleNode from source_file node."""
        imports: List[nodes.ImportNode] = []
        type_defs: List[nodes.StructDefNode] = []
        function_defs: List[nodes.FunctionDefNode] = []
        statutes: List[nodes.StatuteNode] = []
        variables: List[nodes.VariableDecl] = []
        references: List[nodes.ReferencingStmt] = []
        assertions: List[nodes.AssertStmt] = []
        enum_defs: List[nodes.EnumDefNode] = []
        type_aliases: List[nodes.TypeAliasNode] = []

        for child in node.children:
            if child.type == "import_statement":
                imports.append(self._build_import(child))
            elif child.type == "referencing_statement":
                references.append(self._build_referencing(child))
            elif child.type == "struct_definition":
                type_defs.append(self._build_struct_def(child))
            elif child.type == "enum_definition":
                enum_defs.append(self._build_enum_def(child))
            elif child.type == "type_alias":
                type_aliases.append(self._build_type_alias(child))
            elif child.type == "function_definition":
                function_defs.append(self._build_function_def(child))
            elif child.type == "statute_block":
                statutes.append(self._build_statute(child))
            elif child.type == "variable_declaration":
                variables.append(self._build_variable_decl(child))
            elif child.type == "assert_statement":
                assertions.append(self._build_assert(child))

        return nodes.ModuleNode(
            imports=tuple(imports),
            type_defs=tuple(type_defs),
            function_defs=tuple(function_defs),
            statutes=tuple(statutes),
            variables=tuple(variables),
            references=tuple(references),
            assertions=tuple(assertions),
            enum_defs=tuple(enum_defs),
            type_aliases=tuple(type_aliases),
            source_location=self._loc(node),
        )

    def _build_referencing(self, node) -> nodes.ReferencingStmt:
        """Build ReferencingStmt from referencing_statement node."""
        path_node = self._child_by_field(node, "path")
        path = self._text(path_node) if path_node else ""
        return nodes.ReferencingStmt(
            path=path,
            source_location=self._loc(node),
        )

    def _build_assert(self, node) -> nodes.AssertStmt:
        """Build AssertStmt from assert_statement node."""
        condition_node = self._child_by_field(node, "condition")
        message_node = self._child_by_field(node, "message")

        condition = self._build_expression(condition_node) if condition_node else nodes.BoolLit(value=True)
        message = self._build_string_lit(message_node) if message_node else None

        return nodes.AssertStmt(
            condition=condition,
            message=message,
            source_location=self._loc(node),
        )

    def _build_import(self, node) -> nodes.ImportNode:
        """Build ImportNode from import_statement node."""
        path_node = self._child_by_type(node, "import_path")
        path = self._text(path_node).strip('"') if path_node else ""

        # Check for named imports
        names: List[str] = []
        for child in node.children:
            if child.type == "identifier":
                names.append(self._text(child))
            elif child.type == "*":
                names.append("*")

        return nodes.ImportNode(
            path=path,
            imported_names=tuple(names),
            source_location=self._loc(node),
        )

    # =========================================================================
    # Struct definition
    # =========================================================================

    def _build_struct_def(self, node) -> nodes.StructDefNode:
        """Build StructDefNode from struct_definition node."""
        name_node = self._child_by_field(node, "name")
        name = self._text(name_node) if name_node else ""

        # Type parameters
        type_params: List[str] = []
        tp_node = self._child_by_type(node, "type_parameters")
        if tp_node:
            for child in tp_node.children:
                if child.type == "identifier":
                    type_params.append(self._text(child))

        # Fields
        fields: List[nodes.FieldDef] = []
        for child in node.children:
            if child.type == "field_definition":
                fields.append(self._build_field_def(child))

        return nodes.StructDefNode(
            name=name,
            fields=tuple(fields),
            type_params=tuple(type_params),
            doc_comment=self._get_doc_comment(node),
            source_location=self._loc(node),
        )

    def _build_field_def(self, node) -> nodes.FieldDef:
        """Build FieldDef from field_definition node."""
        type_node = self._child_by_field(node, "type")
        name_node = self._child_by_field(node, "name")

        type_ann = self._build_type(type_node) if type_node else nodes.BuiltinType(name="void")
        name = self._text(name_node) if name_node else ""

        return nodes.FieldDef(
            type_annotation=type_ann,
            name=name,
            doc_comment=self._get_doc_comment(node),
            source_location=self._loc(node),
        )

    # =========================================================================
    # Enum definition (Phase 9A)
    # =========================================================================

    def _build_enum_def(self, node) -> nodes.EnumDefNode:
        """Build EnumDefNode from enum_definition node."""
        name_node = self._child_by_field(node, "name")
        name = self._text(name_node) if name_node else ""
        variants: List[nodes.EnumVariant] = []
        for child in node.children:
            if child.type == "enum_variant":
                vname_node = self._child_by_field(child, "name")
                vname = self._text(vname_node) if vname_node else ""
                payload: List[nodes.TypeNode] = []
                for tc in child.children:
                    if tc.type in ("builtin_type", "identifier", "generic_type", "optional_type", "array_type"):
                        payload.append(self._build_type(tc))
                variants.append(nodes.EnumVariant(
                    name=vname,
                    payload_types=tuple(payload),
                    source_location=self._loc(child),
                ))
        return nodes.EnumDefNode(
            name=name,
            variants=tuple(variants),
            doc_comment=self._get_doc_comment(node),
            source_location=self._loc(node),
        )

    # =========================================================================
    # Type alias (Phase 9B)
    # =========================================================================

    def _build_type_alias(self, node) -> nodes.TypeAliasNode:
        """Build TypeAliasNode from type_alias node."""
        name_node = self._child_by_field(node, "name")
        name = self._text(name_node) if name_node else ""
        target_node = self._child_by_field(node, "target")
        target = self._build_type(target_node) if target_node else nodes.BuiltinType(name="void")
        return nodes.TypeAliasNode(
            name=name,
            target_type=target,
            doc_comment=self._get_doc_comment(node),
            source_location=self._loc(node),
        )

    # =========================================================================
    # Function definition
    # =========================================================================

    def _build_function_def(self, node) -> nodes.FunctionDefNode:
        """Build FunctionDefNode from function_definition node."""
        name_node = self._child_by_field(node, "name")
        name = self._text(name_node) if name_node else ""

        # Parameters
        params: List[nodes.ParamDef] = []
        param_list = self._child_by_type(node, "parameter_list")
        if param_list:
            for child in param_list.children:
                if child.type == "parameter":
                    params.append(self._build_param_def(child))

        # Return type
        return_type_node = self._child_by_field(node, "return_type")
        return_type = self._build_type(return_type_node) if return_type_node else None

        # Body
        body_node = self._child_by_type(node, "block")
        body = self._build_block(body_node) if body_node else nodes.Block(statements=())

        return nodes.FunctionDefNode(
            name=name,
            params=tuple(params),
            return_type=return_type,
            body=body,
            doc_comment=self._get_doc_comment(node),
            source_location=self._loc(node),
        )

    def _build_param_def(self, node) -> nodes.ParamDef:
        """Build ParamDef from parameter node."""
        type_node = self._child_by_field(node, "type")
        name_node = self._child_by_field(node, "name")

        type_ann = self._build_type(type_node) if type_node else nodes.BuiltinType(name="void")
        name = self._text(name_node) if name_node else ""

        return nodes.ParamDef(
            type_annotation=type_ann,
            name=name,
            source_location=self._loc(node),
        )

    def _build_block(self, node) -> nodes.Block:
        """Build Block from block node."""
        statements: List[nodes.ASTNode] = []
        for child in node.children:
            stmt = self._build_statement(child)
            if stmt:
                statements.append(stmt)
        return nodes.Block(
            statements=tuple(statements),
            source_location=self._loc(node),
        )

    # =========================================================================
    # Statements
    # =========================================================================

    def _build_statement(self, node) -> Optional[nodes.ASTNode]:
        """Build a statement node."""
        if node.type == "variable_declaration":
            return self._build_variable_decl(node)
        elif node.type == "assignment_statement":
            return self._build_assignment_stmt(node)
        elif node.type == "return_statement":
            return self._build_return_stmt(node)
        elif node.type == "pass_statement":
            return nodes.PassStmt(source_location=self._loc(node))
        elif node.type == "expression_statement":
            expr_node = node.children[0] if node.children else None
            if expr_node:
                return nodes.ExpressionStmt(
                    expression=self._build_expression(expr_node),
                    source_location=self._loc(node),
                )
        elif node.type in ("{", "}", ";"):
            return None
        else:
            # Try to build as expression
            expr = self._build_expression(node)
            if expr:
                return nodes.ExpressionStmt(
                    expression=expr,
                    source_location=self._loc(node),
                )
        return None

    def _build_variable_decl(self, node) -> nodes.VariableDecl:
        """Build VariableDecl from variable_declaration node."""
        type_node = self._child_by_field(node, "type")
        name_node = self._child_by_field(node, "name")
        value_node = self._child_by_field(node, "value")

        type_ann = self._build_type(type_node) if type_node else nodes.BuiltinType(name="void")
        name = self._text(name_node) if name_node else ""
        value = self._build_expression(value_node) if value_node else None

        return nodes.VariableDecl(
            type_annotation=type_ann,
            name=name,
            value=value,
            source_location=self._loc(node),
        )

    def _build_assignment_stmt(self, node) -> nodes.AssignmentStmt:
        """Build AssignmentStmt from assignment_statement node."""
        target_node = self._child_by_field(node, "target")
        value_node = self._child_by_field(node, "value")

        target = self._build_expression(target_node) if target_node else nodes.IdentifierNode(name="")
        value = self._build_expression(value_node) if value_node else nodes.PassExprNode()

        return nodes.AssignmentStmt(
            target=target,
            value=value,
            source_location=self._loc(node),
        )

    def _build_return_stmt(self, node) -> nodes.ReturnStmt:
        """Build ReturnStmt from return_statement node."""
        value = None
        for child in node.children:
            if child.type not in ("return", ";"):
                value = self._build_expression(child)
                break
        return nodes.ReturnStmt(
            value=value,
            source_location=self._loc(node),
        )

    # =========================================================================
    # Expressions
    # =========================================================================

    def _build_expression(self, node) -> nodes.ASTNode:
        """Build an expression node."""
        if node is None:
            return nodes.PassExprNode()

        node_type = node.type

        # Literals
        if node_type == "integer_literal":
            return self._build_int_lit(node)
        elif node_type == "float_literal":
            return self._build_float_lit(node)
        elif node_type == "boolean_literal":
            return self._build_bool_lit(node)
        elif node_type == "string_literal":
            return self._build_string_lit(node)
        elif node_type == "money_literal":
            return self._build_money(node)
        elif node_type == "percent_literal":
            return self._build_percent(node)
        elif node_type == "date_literal":
            return self._build_date(node)
        elif node_type == "duration_literal":
            return self._build_duration(node)

        # Expressions
        elif node_type == "identifier":
            return nodes.IdentifierNode(
                name=self._text(node),
                source_location=self._loc(node),
            )
        elif node_type == "field_access":
            return self._build_field_access(node)
        elif node_type == "index_access":
            return self._build_index_access(node)
        elif node_type == "function_call":
            return self._build_function_call(node)
        elif node_type == "binary_expression":
            return self._build_binary_expr(node)
        elif node_type == "unary_expression":
            return self._build_unary_expr(node)
        elif node_type == "parenthesized_expression":
            # Unwrap parentheses
            for child in node.children:
                if child.type not in ("(", ")"):
                    return self._build_expression(child)
        elif node_type == "match_expression":
            return self._build_match_expr(node)
        elif node_type == "struct_literal":
            return self._build_struct_literal(node)
        elif node_type in ("pass_expression", "pass"):
            return nodes.PassExprNode(source_location=self._loc(node))

        # Fallback - try to find first non-trivial child
        for child in node.children:
            if child.type not in ("{", "}", "(", ")", ",", ";", ":="):
                return self._build_expression(child)

        return nodes.PassExprNode(source_location=self._loc(node))

    def _build_int_lit(self, node) -> nodes.IntLit:
        """Build IntLit from integer_literal node."""
        text = self._text(node)
        return nodes.IntLit(
            value=int(text),
            source_location=self._loc(node),
        )

    def _build_float_lit(self, node) -> nodes.FloatLit:
        """Build FloatLit from float_literal node."""
        text = self._text(node)
        return nodes.FloatLit(
            value=float(text),
            source_location=self._loc(node),
        )

    def _build_bool_lit(self, node) -> nodes.BoolLit:
        """Build BoolLit from boolean_literal node."""
        text = self._text(node)
        return nodes.BoolLit(
            value=(text == "TRUE"),
            source_location=self._loc(node),
        )

    def _build_string_lit(self, node) -> nodes.StringLit:
        """Build StringLit from string_literal node."""
        text = self._text(node)
        # Remove quotes and process escape sequences
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]
        # Process common escape sequences
        text = (text
            .replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace("\\r", "\r")
            .replace('\\"', '"')
            .replace("\\\\", "\\"))
        return nodes.StringLit(
            value=text,
            source_location=self._loc(node),
        )

    def _build_money(self, node) -> nodes.MoneyNode:
        """Build MoneyNode from money_literal node."""
        currency_node = self._child_by_type(node, "currency_symbol")
        amount_node = self._child_by_type(node, "money_amount")

        currency_text = self._text(currency_node) if currency_node else "$"
        currency = nodes.Currency.from_symbol(currency_text)

        amount_text = self._text(amount_node).replace(",", "") if amount_node else "0"
        amount = Decimal(amount_text)

        return nodes.MoneyNode(
            currency=currency,
            amount=amount,
            source_location=self._loc(node),
        )

    def _build_percent(self, node) -> nodes.PercentNode:
        """Build PercentNode from percent_literal node."""
        int_node = self._child_by_type(node, "integer_literal")
        value = int(self._text(int_node)) if int_node else 0
        return nodes.PercentNode(
            value=Decimal(value),
            source_location=self._loc(node),
        )

    def _build_date(self, node) -> nodes.DateNode:
        """Build DateNode from date_literal node."""
        text = self._text(node)
        return nodes.DateNode.from_iso8601(text, self._loc(node))

    def _build_duration(self, node) -> nodes.DurationNode:
        """Build DurationNode from duration_literal node."""
        years = months = days = hours = minutes = seconds = 0

        i = 0
        children = node.children
        while i < len(children):
            child = children[i]
            if child.type == "integer_literal":
                value = int(self._text(child))
                # Look for unit
                if i + 1 < len(children) and children[i + 1].type == "duration_unit":
                    unit = self._text(children[i + 1])
                    if unit in ("year", "years"):
                        years += value
                    elif unit in ("month", "months"):
                        months += value
                    elif unit in ("day", "days"):
                        days += value
                    elif unit in ("hour", "hours"):
                        hours += value
                    elif unit in ("minute", "minutes"):
                        minutes += value
                    elif unit in ("second", "seconds"):
                        seconds += value
                    i += 1
            i += 1

        return nodes.DurationNode(
            years=years,
            months=months,
            days=days,
            hours=hours,
            minutes=minutes,
            seconds=seconds,
            source_location=self._loc(node),
        )

    def _build_field_access(self, node) -> nodes.FieldAccessNode:
        """Build FieldAccessNode from field_access node."""
        base_node = self._child_by_field(node, "base")
        field_node = self._child_by_field(node, "field")

        base = self._build_expression(base_node) if base_node else nodes.PassExprNode()
        field_name = self._text(field_node) if field_node else ""

        return nodes.FieldAccessNode(
            base=base,
            field_name=field_name,
            source_location=self._loc(node),
        )

    def _build_index_access(self, node) -> nodes.IndexAccessNode:
        """Build IndexAccessNode from index_access node."""
        base_node = self._child_by_field(node, "base")
        index_node = self._child_by_field(node, "index")

        base = self._build_expression(base_node) if base_node else nodes.PassExprNode()
        index = self._build_expression(index_node) if index_node else nodes.PassExprNode()

        return nodes.IndexAccessNode(
            base=base,
            index=index,
            source_location=self._loc(node),
        )

    def _build_function_call(self, node) -> nodes.FunctionCallNode:
        """Build FunctionCallNode from function_call node."""
        callee_node = self._child_by_field(node, "callee")
        callee = self._build_expression(callee_node) if callee_node else nodes.IdentifierNode(name="")

        args: List[nodes.ASTNode] = []
        arg_list = self._child_by_type(node, "argument_list")
        if arg_list:
            for child in arg_list.children:
                if child.type not in (",", "(", ")"):
                    args.append(self._build_expression(child))

        return nodes.FunctionCallNode(
            callee=callee,
            args=tuple(args),
            source_location=self._loc(node),
        )

    def _build_binary_expr(self, node) -> nodes.BinaryExprNode:
        """Build BinaryExprNode from binary_expression node."""
        children = [c for c in node.children if c.type not in ("(", ")")]

        if len(children) < 3:
            return nodes.BinaryExprNode(
                left=nodes.PassExprNode(),
                operator="?",
                right=nodes.PassExprNode(),
                source_location=self._loc(node),
            )

        left = self._build_expression(children[0])
        operator = self._text(children[1])
        right = self._build_expression(children[2])

        return nodes.BinaryExprNode(
            left=left,
            operator=operator,
            right=right,
            source_location=self._loc(node),
        )

    def _build_unary_expr(self, node) -> nodes.UnaryExprNode:
        """Build UnaryExprNode from unary_expression node."""
        children = [c for c in node.children if c.type not in ("(", ")")]

        if len(children) < 2:
            return nodes.UnaryExprNode(
                operator="?",
                operand=nodes.PassExprNode(),
                source_location=self._loc(node),
            )

        operator = self._text(children[0])
        operand = self._build_expression(children[1])

        return nodes.UnaryExprNode(
            operator=operator,
            operand=operand,
            source_location=self._loc(node),
        )

    # =========================================================================
    # Match expression
    # =========================================================================

    def _build_match_expr(self, node) -> nodes.MatchExprNode:
        """Build MatchExprNode from match_expression node."""
        scrutinee_node = self._child_by_field(node, "scrutinee")
        scrutinee = self._build_expression(scrutinee_node) if scrutinee_node else None

        arms: List[nodes.MatchArm] = []
        for child in node.children:
            if child.type == "match_arm":
                arms.append(self._build_match_arm(child))

        return nodes.MatchExprNode(
            scrutinee=scrutinee,
            arms=tuple(arms),
            ensure_exhaustiveness=True,
            source_location=self._loc(node),
        )

    def _build_match_arm(self, node) -> nodes.MatchArm:
        """Build MatchArm from match_arm node."""
        pattern_node = self._child_by_field(node, "pattern")
        guard_node = self._child_by_field(node, "guard")
        body_node = self._child_by_field(node, "body")

        pattern = self._build_pattern(pattern_node) if pattern_node else nodes.WildcardPattern()
        guard = self._build_expression(guard_node) if guard_node else None
        body = self._build_expression(body_node) if body_node else nodes.PassExprNode()

        return nodes.MatchArm(
            pattern=pattern,
            guard=guard,
            body=body,
            source_location=self._loc(node),
        )

    def _build_pattern(self, node) -> nodes.PatternNode:
        """Build a pattern node."""
        if node.type == "wildcard_pattern" or self._text(node) == "_":
            return nodes.WildcardPattern(source_location=self._loc(node))
        elif node.type == "literal_pattern":
            literal_child = node.children[0] if node.children else None
            return nodes.LiteralPattern(
                literal=self._build_expression(literal_child) if literal_child else nodes.PassExprNode(),
                source_location=self._loc(node),
            )
        elif node.type == "binding_pattern" or node.type == "identifier":
            return nodes.BindingPattern(
                name=self._text(node),
                source_location=self._loc(node),
            )
        elif node.type == "struct_pattern":
            type_name_node = self._child_by_field(node, "type_name")
            type_name = self._text(type_name_node) if type_name_node else ""

            field_patterns: List[nodes.FieldPattern] = []
            for child in node.children:
                if child.type == "field_pattern":
                    fp = self._build_field_pattern(child)
                    field_patterns.append(fp)

            return nodes.StructPattern(
                type_name=type_name,
                fields=tuple(field_patterns),
                source_location=self._loc(node),
            )
        else:
            # Try to match as literal or identifier
            text = self._text(node)
            if text == "_":
                return nodes.WildcardPattern(source_location=self._loc(node))
            elif text in ("TRUE", "FALSE"):
                return nodes.LiteralPattern(
                    literal=nodes.BoolLit(value=(text == "TRUE"), source_location=self._loc(node)),
                    source_location=self._loc(node),
                )
            else:
                return nodes.BindingPattern(
                    name=text,
                    source_location=self._loc(node),
                )

    def _build_field_pattern(self, node) -> nodes.FieldPattern:
        """Build FieldPattern from field_pattern node."""
        name_node = self._child_by_field(node, "name")
        pattern_node = self._child_by_field(node, "pattern")

        name = self._text(name_node) if name_node else ""
        pattern = self._build_pattern(pattern_node) if pattern_node else None

        return nodes.FieldPattern(
            name=name,
            pattern=pattern,
            source_location=self._loc(node),
        )

    # =========================================================================
    # Struct literal
    # =========================================================================

    def _build_struct_literal(self, node) -> nodes.StructLiteralNode:
        """Build StructLiteralNode from struct_literal node."""
        type_name_node = self._child_by_field(node, "type_name")
        struct_name = self._text(type_name_node) if type_name_node else None

        field_values: List[nodes.FieldAssignment] = []
        for child in node.children:
            if child.type == "field_assignment":
                field_values.append(self._build_field_assignment(child))

        return nodes.StructLiteralNode(
            struct_name=struct_name,
            field_values=tuple(field_values),
            source_location=self._loc(node),
        )

    def _build_field_assignment(self, node) -> nodes.FieldAssignment:
        """Build FieldAssignment from field_assignment node."""
        name_node = self._child_by_field(node, "name")
        value_node = self._child_by_field(node, "value")

        name = self._text(name_node) if name_node else ""
        value = self._build_expression(value_node) if value_node else nodes.PassExprNode()

        return nodes.FieldAssignment(
            name=name,
            value=value,
            source_location=self._loc(node),
        )

    # =========================================================================
    # Types
    # =========================================================================

    def _build_type(self, node) -> nodes.TypeNode:
        """Build a type node."""
        if node is None:
            return nodes.BuiltinType(name="void")

        node_type = node.type

        if node_type == "builtin_type":
            return nodes.BuiltinType(
                name=self._text(node),
                source_location=self._loc(node),
            )
        elif node_type == "identifier":
            text = self._text(node)
            if text in ("int", "float", "bool", "string", "money", "percent", "date", "duration", "void"):
                return nodes.BuiltinType(name=text, source_location=self._loc(node))
            return nodes.NamedType(
                name=text,
                source_location=self._loc(node),
            )
        elif node_type == "generic_type":
            base_node = node.children[0] if node.children else None
            base = self._text(base_node) if base_node else ""

            type_args: List[nodes.TypeNode] = []
            for child in node.children:
                if child.type not in ("<", ">", ",") and child != base_node:
                    type_args.append(self._build_type(child))

            return nodes.GenericType(
                base=base,
                type_args=tuple(type_args),
                source_location=self._loc(node),
            )
        elif node_type == "optional_type":
            inner = node.children[0] if node.children else None
            return nodes.OptionalType(
                inner=self._build_type(inner),
                source_location=self._loc(node),
            )
        elif node_type == "array_type":
            elem = None
            for child in node.children:
                if child.type not in ("[", "]"):
                    elem = child
                    break
            return nodes.ArrayType(
                element_type=self._build_type(elem),
                source_location=self._loc(node),
            )
        elif node_type == "refinement_type":
            base_node = self._child_by_field(node, "base")
            lower_node = self._child_by_field(node, "lower")
            upper_node = self._child_by_field(node, "upper")
            return nodes.RefinementTypeNode(
                base_type=self._build_type(base_node),
                lower_bound=self._build_expression(lower_node) if lower_node else nodes.IntLit(value=0),
                upper_bound=self._build_expression(upper_node) if upper_node else nodes.IntLit(value=0),
                source_location=self._loc(node),
            )
        else:
            # Fallback - treat as identifier type
            text = self._text(node)
            if text in ("int", "float", "bool", "string", "money", "percent", "date", "duration", "void"):
                return nodes.BuiltinType(name=text, source_location=self._loc(node))
            return nodes.NamedType(name=text, source_location=self._loc(node))

    # =========================================================================
    # Statute blocks
    # =========================================================================

    def _build_statute(self, node) -> nodes.StatuteNode:
        """Build StatuteNode from statute_block node."""
        section_node = self._child_by_field(node, "section_number")
        title_node = self._child_by_field(node, "title")

        section_number = self._text(section_node) if section_node else ""
        title = self._build_string_lit(title_node) if title_node else None

        definitions: List[nodes.DefinitionEntry] = []
        elements: list = []
        penalty: Optional[nodes.PenaltyNode] = None
        illustrations: List[nodes.IllustrationNode] = []
        exceptions: List[nodes.ExceptionNode] = []
        case_law: List[nodes.CaseLawNode] = []

        for child in node.children:
            if child.type == "definitions_block":
                definitions.extend(self._build_definitions_block(child))
            elif child.type == "elements_block":
                elements.extend(self._build_elements_block(child))
            elif child.type == "penalty_block":
                penalty = self._build_penalty_block(child)
            elif child.type == "illustration_block":
                illustrations.append(self._build_illustration(child))
            elif child.type == "exception_block":
                exceptions.append(self._build_exception(child))
            elif child.type == "caselaw_block":
                case_law.append(self._build_caselaw(child))

        doc = self._get_doc_comment(node)
        jurisdiction, jurisdiction_meta = self._extract_jurisdiction(doc)

        # phase 11/13: temporal and hierarchy metadata
        effective_node = self._child_by_field(node, "effective_date")
        repealed_node = self._child_by_field(node, "repealed_date")
        subsumes_node = self._child_by_field(node, "subsumes")
        amends_node = self._child_by_field(node, "amends")

        return nodes.StatuteNode(
            section_number=section_number,
            title=title,
            definitions=tuple(definitions),
            elements=tuple(elements),
            penalty=penalty,
            illustrations=tuple(illustrations),
            exceptions=tuple(exceptions),
            case_law=tuple(case_law),
            doc_comment=doc,
            jurisdiction=jurisdiction,
            jurisdiction_meta=jurisdiction_meta,
            effective_date=self._text(effective_node) if effective_node else None,
            repealed_date=self._text(repealed_node) if repealed_node else None,
            subsumes=self._text(subsumes_node) if subsumes_node else None,
            amends=self._text(amends_node) if amends_node else None,
            source_location=self._loc(node),
        )

    def _build_definitions_block(self, node) -> List[nodes.DefinitionEntry]:
        """Build list of DefinitionEntry from definitions_block node."""
        entries: List[nodes.DefinitionEntry] = []
        for child in node.children:
            if child.type == "definition_entry":
                term_node = self._child_by_field(child, "term")
                def_node = self._child_by_field(child, "definition")

                term = self._text(term_node) if term_node else ""
                definition = self._build_string_lit(def_node) if def_node else nodes.StringLit(value="")

                entries.append(nodes.DefinitionEntry(
                    term=term,
                    definition=definition,
                    source_location=self._loc(child),
                ))
        return entries

    def _build_elements_block(self, node) -> list:
        """Build list of ElementNode/ElementGroupNode from elements_block node."""
        elements: list = []
        for child in node.children:
            if child.type == "element_entry":
                type_node = self._child_by_field(child, "element_type")
                name_node = self._child_by_field(child, "name")
                desc_node = self._child_by_field(child, "description")

                elem_type = self._text(type_node) if type_node else "actus_reus"
                name = self._text(name_node) if name_node else ""
                description = self._build_expression(desc_node) if desc_node else nodes.StringLit(value="")

                caused_by_node = self._child_by_field(child, "caused_by")
                burden_node = self._child_by_type(child, "burden_qualifier")
                burden = burden_standard = None
                if burden_node:
                    for bc in burden_node.children:
                        t = self._text(bc)
                        if t in ("prosecution", "defence"):
                            burden = t
                        elif t in ("beyond_reasonable_doubt", "balance_of_probabilities", "prima_facie"):
                            burden_standard = t
                elements.append(nodes.ElementNode(
                    element_type=elem_type,
                    name=name,
                    description=description,
                    caused_by=self._text(caused_by_node) if caused_by_node else None,
                    burden=burden,
                    burden_standard=burden_standard,
                    doc_comment=self._get_doc_comment(child),
                    source_location=self._loc(child),
                ))
            elif child.type == "element_group":
                elements.append(self._build_element_group(child))
        return elements

    def _build_element_group(self, node) -> nodes.ElementGroupNode:
        """Build ElementGroupNode from element_group node."""
        combinator_node = self._child_by_field(node, "combinator")
        combinator = self._text(combinator_node) if combinator_node else "all_of"
        members: list = []
        for child in node.children:
            if child.type == "element_entry":
                type_node = self._child_by_field(child, "element_type")
                name_node = self._child_by_field(child, "name")
                desc_node = self._child_by_field(child, "description")
                elem_type = self._text(type_node) if type_node else "actus_reus"
                name = self._text(name_node) if name_node else ""
                description = self._build_expression(desc_node) if desc_node else nodes.StringLit(value="")
                members.append(nodes.ElementNode(
                    element_type=elem_type, name=name, description=description,
                    doc_comment=self._get_doc_comment(child),
                    source_location=self._loc(child),
                ))
            elif child.type == "element_group":
                members.append(self._build_element_group(child))
        return nodes.ElementGroupNode(
            combinator=combinator,
            members=tuple(members),
            source_location=self._loc(node),
        )

    def _build_penalty_block(self, node) -> nodes.PenaltyNode:
        """Build PenaltyNode from penalty_block node."""
        imprisonment_min = imprisonment_max = None
        fine_min = fine_max = None
        caning_min = caning_max = None
        death_penalty = None
        supplementary = None
        mandatory_min_imprisonment = None
        mandatory_min_fine = None

        # phase 14: sentencing mode
        sentencing_node = self._child_by_field(node, "sentencing")
        sentencing = self._text(sentencing_node) if sentencing_node else None

        for child in node.children:
            if child.type == "imprisonment_clause":
                duration_nodes = self._children_by_type(child, "duration_literal")
                range_node = self._child_by_type(child, "duration_range")
                if range_node:
                    durs = self._children_by_type(range_node, "duration_literal")
                    if len(durs) >= 2:
                        imprisonment_min = self._build_duration(durs[0])
                        imprisonment_max = self._build_duration(durs[1])
                elif duration_nodes:
                    imprisonment_max = self._build_duration(duration_nodes[0])
            elif child.type == "fine_clause":
                money_nodes = self._children_by_type(child, "money_literal")
                range_node = self._child_by_type(child, "money_range")
                if range_node:
                    moneys = self._children_by_type(range_node, "money_literal")
                    if len(moneys) >= 2:
                        fine_min = self._build_money(moneys[0])
                        fine_max = self._build_money(moneys[1])
                elif money_nodes:
                    fine_max = self._build_money(money_nodes[0])
            elif child.type == "caning_clause":
                int_nodes = self._children_by_type(child, "integer_literal")
                if len(int_nodes) >= 2:
                    caning_min = int(self._text(int_nodes[0]))
                    caning_max = int(self._text(int_nodes[1]))
                elif int_nodes:
                    caning_min = int(self._text(int_nodes[0]))
                    caning_max = caning_min
            elif child.type == "death_penalty_clause":
                bool_node = self._child_by_type(child, "boolean_literal")
                if bool_node:
                    death_penalty = self._text(bool_node) == "TRUE"
            elif child.type == "supplementary_clause":
                string_node = self._child_by_type(child, "string_literal")
                if string_node:
                    supplementary = self._build_string_lit(string_node)
            elif child.type == "mandatory_minimum_clause":
                dur_node = self._child_by_type(child, "duration_literal")
                money_node = self._child_by_type(child, "money_literal")
                if dur_node:
                    mandatory_min_imprisonment = self._build_duration(dur_node)
                if money_node:
                    mandatory_min_fine = self._build_money(money_node)

        return nodes.PenaltyNode(
            imprisonment_min=imprisonment_min,
            imprisonment_max=imprisonment_max,
            fine_min=fine_min,
            fine_max=fine_max,
            caning_min=caning_min,
            caning_max=caning_max,
            death_penalty=death_penalty,
            supplementary=supplementary,
            sentencing=sentencing,
            mandatory_min_imprisonment=mandatory_min_imprisonment,
            mandatory_min_fine=mandatory_min_fine,
            source_location=self._loc(node),
        )

    def _build_illustration(self, node) -> nodes.IllustrationNode:
        """Build IllustrationNode from illustration_block node."""
        label_node = self._child_by_field(node, "label")
        desc_node = self._child_by_field(node, "description")

        label = self._text(label_node) if label_node else None
        description = self._build_string_lit(desc_node) if desc_node else nodes.StringLit(value="")

        return nodes.IllustrationNode(
            label=label,
            description=description,
            source_location=self._loc(node),
        )

    def _build_exception(self, node) -> nodes.ExceptionNode:
        """Build ExceptionNode from exception_block node."""
        label_node = self._child_by_field(node, "label")
        condition_node = self._child_by_field(node, "condition")
        effect_node = self._child_by_field(node, "effect")
        guard_node = self._child_by_field(node, "guard")

        label = self._text(label_node) if label_node else None
        condition = self._build_string_lit(condition_node) if condition_node else nodes.StringLit(value="")
        effect = self._build_string_lit(effect_node) if effect_node else None
        guard = self._build_expression(guard_node) if guard_node else None

        return nodes.ExceptionNode(
            label=label,
            condition=condition,
            effect=effect,
            guard=guard,
            source_location=self._loc(node),
        )

    def _build_caselaw(self, node) -> nodes.CaseLawNode:
        """Build CaseLawNode from caselaw_block node."""
        case_name_node = self._child_by_field(node, "case_name")
        citation_node = self._child_by_field(node, "citation")
        holding_node = self._child_by_field(node, "holding")
        element_ref_node = self._child_by_field(node, "element_ref")

        case_name = self._build_string_lit(case_name_node) if case_name_node else nodes.StringLit(value="")
        citation = self._build_string_lit(citation_node) if citation_node else None
        holding = self._build_string_lit(holding_node) if holding_node else nodes.StringLit(value="")
        element_ref = self._text(element_ref_node) if element_ref_node else None

        return nodes.CaseLawNode(
            case_name=case_name,
            citation=citation,
            holding=holding,
            element_ref=element_ref,
            source_location=self._loc(node),
        )
