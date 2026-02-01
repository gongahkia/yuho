"""
JSON-LD transpiler with legal ontology context.

Extends JSON output with @context, @type, and @id annotations
following schema.org/Legislation patterns.
"""

import json
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase
from yuho.transpile.json_transpiler import JSONTranspiler


# JSON-LD context for legal ontology
LEGAL_CONTEXT = {
    "@vocab": "https://schema.org/",
    "yuho": "https://yuho.dev/ontology#",
    "eli": "http://data.europa.eu/eli/ontology#",

    # Schema.org Legislation mappings
    "Statute": "Legislation",
    "section_number": "legislationIdentifier",
    "title": "name",
    "definitions": "yuho:definitions",
    "elements": "yuho:elements",
    "penalty": "yuho:penalty",
    "illustrations": "yuho:illustrations",

    # Element types
    "ElementNode": "yuho:LegalElement",
    "actus_reus": "yuho:actusReus",
    "mens_rea": "yuho:mensRea",
    "circumstance": "yuho:circumstance",

    # Penalty mappings
    "PenaltyNode": "yuho:Penalty",
    "imprisonment": "yuho:imprisonment",
    "fine": "yuho:fine",
    "supplementary": "yuho:supplementaryPunishment",

    # Duration/Money
    "DurationNode": "Duration",
    "MoneyNode": "MonetaryAmount",
    "currency": "currency",
    "amount": "value",

    # Struct mappings
    "StructDefNode": "yuho:TypeDefinition",
    "StructLiteralNode": "yuho:Instance",
    "FieldDef": "yuho:Field",

    # Function mappings
    "FunctionDefNode": "yuho:Function",

    # Match expression
    "MatchExprNode": "yuho:DecisionTree",
    "MatchArm": "yuho:DecisionBranch",
    "pattern": "yuho:condition",
    "body": "yuho:consequence",
}


class JSONLDTranspiler(TranspilerBase):
    """
    Transpile Yuho AST to JSON-LD format with legal ontology annotations.

    Adds @context, @type, and @id to enable linked data queries
    and integration with legal knowledge graphs.
    """

    def __init__(self, base_uri: str = "https://yuho.dev/statutes/", include_locations: bool = False):
        """
        Initialize the JSON-LD transpiler.

        Args:
            base_uri: Base URI for @id generation
            include_locations: Whether to include source locations
        """
        self.base_uri = base_uri
        self.include_locations = include_locations
        self._json_transpiler = JSONTranspiler(include_locations=include_locations)

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.JSON_LD

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to JSON-LD string."""
        data = self._to_jsonld(ast)
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _to_jsonld(self, node: nodes.ASTNode) -> Dict[str, Any]:
        """Convert AST node to JSON-LD format."""
        # Start with basic JSON representation
        base = self._json_transpiler._to_dict(node)

        # Transform to JSON-LD
        result = self._transform_to_jsonld(base, node)

        # Add context at top level for ModuleNode
        if isinstance(node, nodes.ModuleNode):
            result = {
                "@context": LEGAL_CONTEXT,
                "@graph": result if isinstance(result, list) else [result],
            }

        return result

    def _transform_to_jsonld(self, data: Dict[str, Any], node: nodes.ASTNode) -> Dict[str, Any]:
        """Transform a JSON dict to JSON-LD format."""
        result = {}

        # Map _type to @type
        if "_type" in data:
            node_type = data["_type"]
            result["@type"] = self._map_type(node_type)

        # Generate @id for identifiable nodes
        if isinstance(node, nodes.StatuteNode):
            result["@id"] = f"{self.base_uri}{quote(node.section_number)}"
        elif isinstance(node, nodes.StructDefNode):
            result["@id"] = f"{self.base_uri}types/{quote(node.name)}"
        elif isinstance(node, nodes.FunctionDefNode):
            result["@id"] = f"{self.base_uri}functions/{quote(node.name)}"

        # Copy and transform remaining fields
        for key, value in data.items():
            if key.startswith("_"):
                continue  # Skip internal fields

            new_key = self._map_property(key)

            if isinstance(value, dict):
                # Recursively transform nested objects
                child_node = self._get_child_node(node, key)
                result[new_key] = self._transform_to_jsonld(value, child_node) if child_node else value
            elif isinstance(value, list):
                # Transform list items
                result[new_key] = [
                    self._transform_to_jsonld(item, self._get_list_item_node(node, key, i))
                    if isinstance(item, dict) else item
                    for i, item in enumerate(value)
                ]
            else:
                result[new_key] = value

        return result

    def _map_type(self, node_type: str) -> str:
        """Map internal type name to JSON-LD type."""
        type_mapping = {
            "ModuleNode": "yuho:Module",
            "StatuteNode": "Legislation",
            "StructDefNode": "yuho:TypeDefinition",
            "StructLiteralNode": "yuho:Instance",
            "FunctionDefNode": "yuho:Function",
            "MatchExprNode": "yuho:DecisionTree",
            "MatchArm": "yuho:DecisionBranch",
            "ElementNode": "yuho:LegalElement",
            "PenaltyNode": "yuho:Penalty",
            "DurationNode": "Duration",
            "MoneyNode": "MonetaryAmount",
            "StringLit": "Text",
            "IntLit": "Integer",
            "FloatLit": "Number",
            "BoolLit": "Boolean",
            "DateNode": "Date",
            "PercentNode": "yuho:Percentage",
            "ImportNode": "yuho:Import",
            "IllustrationNode": "yuho:Illustration",
            "DefinitionEntry": "DefinedTerm",
        }
        return type_mapping.get(node_type, f"yuho:{node_type}")

    def _map_property(self, prop: str) -> str:
        """Map internal property name to JSON-LD property."""
        prop_mapping = {
            "section_number": "legislationIdentifier",
            "title": "name",
            "definitions": "yuho:hasDefinition",
            "elements": "yuho:hasElement",
            "penalty": "yuho:hasPenalty",
            "illustrations": "yuho:hasIllustration",
            "element_type": "yuho:elementType",
            "description": "description",
            "term": "name",
            "definition": "description",
            "imprisonment_min": "yuho:minImprisonment",
            "imprisonment_max": "yuho:maxImprisonment",
            "fine_min": "yuho:minFine",
            "fine_max": "yuho:maxFine",
            "supplementary": "yuho:supplementaryPunishment",
            "scrutinee": "yuho:subject",
            "arms": "yuho:hasBranch",
            "pattern": "yuho:condition",
            "guard": "yuho:guard",
            "body": "yuho:consequence",
            "struct_name": "yuho:instanceOf",
            "fields": "yuho:hasField",
            "field_values": "yuho:hasFieldValue",
            "type_defs": "yuho:definesType",
            "function_defs": "yuho:definesFunction",
            "statutes": "yuho:containsLegislation",
            "imports": "yuho:imports",
            "variables": "yuho:definesVariable",
            "params": "yuho:hasParameter",
            "return_type": "yuho:returnType",
            "type": "yuho:type",
            "value": "yuho:value",
            "name": "name",
            "callee": "yuho:callee",
            "args": "yuho:arguments",
            "operator": "yuho:operator",
            "left": "yuho:leftOperand",
            "right": "yuho:rightOperand",
            "operand": "yuho:operand",
            "base": "yuho:base",
            "field_name": "yuho:fieldName",
            "index": "yuho:index",
            "currency": "priceCurrency",
            "amount": "value",
            "years": "yuho:years",
            "months": "yuho:months",
            "days": "yuho:days",
            "hours": "yuho:hours",
            "minutes": "yuho:minutes",
            "seconds": "yuho:seconds",
        }
        return prop_mapping.get(prop, prop)

    def _get_child_node(self, parent: nodes.ASTNode, field: str) -> Optional[nodes.ASTNode]:
        """Get child node for a field."""
        if hasattr(parent, field):
            child = getattr(parent, field)
            if isinstance(child, nodes.ASTNode):
                return child
        return None

    def _get_list_item_node(self, parent: nodes.ASTNode, field: str, index: int) -> Optional[nodes.ASTNode]:
        """Get node for list item at index."""
        if hasattr(parent, field):
            children = getattr(parent, field)
            if isinstance(children, (list, tuple)) and index < len(children):
                item = children[index]
                if isinstance(item, nodes.ASTNode):
                    return item
        return None
