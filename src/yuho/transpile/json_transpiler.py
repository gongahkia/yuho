"""
JSON transpiler - serialize AST to JSON with type discriminators.
"""

import json
from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.transpile.base import TranspileTarget, TranspilerBase


class JSONTranspiler(TranspilerBase, Visitor):
    """
    Transpile Yuho AST to JSON format.

    Includes type discriminators ("_type" field) and source locations
    for each node to enable round-trip parsing.
    """

    def __init__(self, include_locations: bool = True, indent: int = 2):
        """
        Initialize the JSON transpiler.

        Args:
            include_locations: Whether to include source locations
            indent: JSON indentation level (0 for compact)
        """
        self.include_locations = include_locations
        self.indent = indent

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.JSON

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to JSON string."""
        data = self._to_dict(ast)
        return json.dumps(data, indent=self.indent if self.indent else None, ensure_ascii=False)

    def _to_dict(self, node: nodes.ASTNode) -> Dict[str, Any]:
        """Convert an AST node to a dictionary."""
        result: Dict[str, Any] = {"_type": type(node).__name__}

        # Add source location if enabled
        if self.include_locations and node.source_location:
            loc = node.source_location
            result["_loc"] = {
                "file": loc.file,
                "line": loc.line,
                "col": loc.col,
                "end_line": loc.end_line,
                "end_col": loc.end_col,
            }

        # Handle specific node types
        if isinstance(node, nodes.IntLit):
            result["value"] = node.value
        elif isinstance(node, nodes.FloatLit):
            result["value"] = node.value
        elif isinstance(node, nodes.BoolLit):
            result["value"] = node.value
        elif isinstance(node, nodes.StringLit):
            result["value"] = node.value
        elif isinstance(node, nodes.MoneyNode):
            result["currency"] = node.currency.name
            result["amount"] = str(node.amount)
        elif isinstance(node, nodes.PercentNode):
            result["value"] = str(node.value)
        elif isinstance(node, nodes.DateNode):
            result["value"] = node.value.isoformat()
        elif isinstance(node, nodes.DurationNode):
            result["years"] = node.years
            result["months"] = node.months
            result["days"] = node.days
            result["hours"] = node.hours
            result["minutes"] = node.minutes
            result["seconds"] = node.seconds
        elif isinstance(node, nodes.IdentifierNode):
            result["name"] = node.name
        elif isinstance(node, nodes.FieldAccessNode):
            result["base"] = self._to_dict(node.base)
            result["field_name"] = node.field_name
        elif isinstance(node, nodes.IndexAccessNode):
            result["base"] = self._to_dict(node.base)
            result["index"] = self._to_dict(node.index)
        elif isinstance(node, nodes.FunctionCallNode):
            result["callee"] = self._to_dict(node.callee)
            result["args"] = [self._to_dict(a) for a in node.args]
        elif isinstance(node, nodes.BinaryExprNode):
            result["left"] = self._to_dict(node.left)
            result["operator"] = node.operator
            result["right"] = self._to_dict(node.right)
        elif isinstance(node, nodes.UnaryExprNode):
            result["operator"] = node.operator
            result["operand"] = self._to_dict(node.operand)
        elif isinstance(node, nodes.PassExprNode):
            pass  # Just the type is enough
        elif isinstance(node, nodes.WildcardPattern):
            pass
        elif isinstance(node, nodes.LiteralPattern):
            result["literal"] = self._to_dict(node.literal)
        elif isinstance(node, nodes.BindingPattern):
            result["name"] = node.name
        elif isinstance(node, nodes.FieldPattern):
            result["name"] = node.name
            if node.pattern:
                result["pattern"] = self._to_dict(node.pattern)
        elif isinstance(node, nodes.StructPattern):
            result["type_name"] = node.type_name
            result["fields"] = [self._to_dict(f) for f in node.fields]
        elif isinstance(node, nodes.MatchArm):
            result["pattern"] = self._to_dict(node.pattern)
            if node.guard:
                result["guard"] = self._to_dict(node.guard)
            result["body"] = self._to_dict(node.body)
        elif isinstance(node, nodes.MatchExprNode):
            if node.scrutinee:
                result["scrutinee"] = self._to_dict(node.scrutinee)
            result["arms"] = [self._to_dict(a) for a in node.arms]
            result["ensure_exhaustiveness"] = node.ensure_exhaustiveness
        elif isinstance(node, nodes.BuiltinType):
            result["name"] = node.name
        elif isinstance(node, nodes.NamedType):
            result["name"] = node.name
        elif isinstance(node, nodes.GenericType):
            result["base"] = node.base
            result["type_args"] = [self._to_dict(t) for t in node.type_args]
        elif isinstance(node, nodes.OptionalType):
            result["inner"] = self._to_dict(node.inner)
        elif isinstance(node, nodes.ArrayType):
            result["element_type"] = self._to_dict(node.element_type)
        elif isinstance(node, nodes.FieldDef):
            result["type"] = self._to_dict(node.type_annotation)
            result["name"] = node.name
        elif isinstance(node, nodes.StructDefNode):
            result["name"] = node.name
            result["fields"] = [self._to_dict(f) for f in node.fields]
            if node.type_params:
                result["type_params"] = list(node.type_params)
        elif isinstance(node, nodes.FieldAssignment):
            result["name"] = node.name
            result["value"] = self._to_dict(node.value)
        elif isinstance(node, nodes.StructLiteralNode):
            if node.struct_name:
                result["struct_name"] = node.struct_name
            result["fields"] = [self._to_dict(f) for f in node.field_values]
        elif isinstance(node, nodes.ParamDef):
            result["type"] = self._to_dict(node.type_annotation)
            result["name"] = node.name
        elif isinstance(node, nodes.Block):
            result["statements"] = [self._to_dict(s) for s in node.statements]
        elif isinstance(node, nodes.FunctionDefNode):
            result["name"] = node.name
            result["params"] = [self._to_dict(p) for p in node.params]
            if node.return_type:
                result["return_type"] = self._to_dict(node.return_type)
            result["body"] = self._to_dict(node.body)
        elif isinstance(node, nodes.VariableDecl):
            result["type"] = self._to_dict(node.type_annotation)
            result["name"] = node.name
            if node.value:
                result["value"] = self._to_dict(node.value)
        elif isinstance(node, nodes.AssignmentStmt):
            result["target"] = self._to_dict(node.target)
            result["value"] = self._to_dict(node.value)
        elif isinstance(node, nodes.ReturnStmt):
            if node.value:
                result["value"] = self._to_dict(node.value)
        elif isinstance(node, nodes.PassStmt):
            pass
        elif isinstance(node, nodes.ExpressionStmt):
            result["expression"] = self._to_dict(node.expression)
        elif isinstance(node, nodes.DefinitionEntry):
            result["term"] = node.term
            result["definition"] = self._to_dict(node.definition)
        elif isinstance(node, nodes.ElementNode):
            result["element_type"] = node.element_type
            result["name"] = node.name
            result["description"] = self._to_dict(node.description)
        elif isinstance(node, nodes.PenaltyNode):
            if node.imprisonment_min:
                result["imprisonment_min"] = self._to_dict(node.imprisonment_min)
            if node.imprisonment_max:
                result["imprisonment_max"] = self._to_dict(node.imprisonment_max)
            if node.fine_min:
                result["fine_min"] = self._to_dict(node.fine_min)
            if node.fine_max:
                result["fine_max"] = self._to_dict(node.fine_max)
            if node.supplementary:
                result["supplementary"] = self._to_dict(node.supplementary)
        elif isinstance(node, nodes.IllustrationNode):
            if node.label:
                result["label"] = node.label
            result["description"] = self._to_dict(node.description)
        elif isinstance(node, nodes.StatuteNode):
            result["section_number"] = node.section_number
            if node.title:
                result["title"] = self._to_dict(node.title)
            result["definitions"] = [self._to_dict(d) for d in node.definitions]
            result["elements"] = [self._to_dict(e) for e in node.elements]
            if node.penalty:
                result["penalty"] = self._to_dict(node.penalty)
            result["illustrations"] = [self._to_dict(i) for i in node.illustrations]
        elif isinstance(node, nodes.ImportNode):
            result["path"] = node.path
            result["imported_names"] = list(node.imported_names)
        elif isinstance(node, nodes.ModuleNode):
            result["imports"] = [self._to_dict(i) for i in node.imports]
            result["type_defs"] = [self._to_dict(t) for t in node.type_defs]
            result["function_defs"] = [self._to_dict(f) for f in node.function_defs]
            result["statutes"] = [self._to_dict(s) for s in node.statutes]
            result["variables"] = [self._to_dict(v) for v in node.variables]

        return result
