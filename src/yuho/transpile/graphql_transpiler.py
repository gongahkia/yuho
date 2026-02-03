"""
GraphQL schema transpiler - generate GraphQL schema from Yuho AST.

Converts Yuho statutes and types to GraphQL schema definitions
suitable for building legal APIs. Includes:
- Type definitions for statutes, elements, penalties
- Query types for statute lookup
- Enum types for currencies, element types, etc.
"""

from typing import List, Set

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.transpile.base import TranspileTarget, TranspilerBase


class GraphQLTranspiler(TranspilerBase, Visitor):
    """
    Transpile Yuho AST to GraphQL schema definition language (SDL).

    Generates a complete GraphQL schema with types, queries, and enums
    for building legal statute APIs.
    """

    def __init__(self, include_descriptions: bool = True):
        """
        Initialize GraphQL transpiler.

        Args:
            include_descriptions: Whether to include description comments
        """
        self._output: List[str] = []
        self._indent_level = 0
        self.include_descriptions = include_descriptions
        self._defined_types: Set[str] = set()

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.GRAPHQL

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to GraphQL schema."""
        self._output = []
        self._defined_types = set()

        # Emit header comment
        self._emit("# Auto-generated GraphQL schema from Yuho statutes")
        self._emit("# Do not edit manually")
        self._emit("")

        # Emit built-in scalar types
        self._emit_scalars()

        # Emit enums
        self._emit_enums()

        # Emit custom struct types from AST
        for struct in ast.type_defs:
            self._visit_struct_def(struct)

        # Emit core legal types
        self._emit_core_types()

        # Emit statute types
        for statute in ast.statutes:
            self._visit_statute(statute)

        # Emit query root
        self._emit_query_root(ast)

        return "\n".join(self._output)

    def _emit(self, text: str) -> None:
        """Add a line to output with current indentation."""
        indent = "  " * self._indent_level
        self._output.append(f"{indent}{text}")

    def _emit_blank(self) -> None:
        """Add a blank line."""
        self._output.append("")

    def _emit_description(self, text: str, multiline: bool = False) -> None:
        """Emit a GraphQL description string."""
        if not self.include_descriptions:
            return
        if multiline or "\n" in text:
            self._emit('"""')
            for line in text.split("\n"):
                self._emit(line)
            self._emit('"""')
        else:
            self._emit(f'"{text}"')

    # =========================================================================
    # Scalar and Enum Types
    # =========================================================================

    def _emit_scalars(self) -> None:
        """Emit custom scalar type definitions."""
        self._emit_description("Monetary amount with currency")
        self._emit("scalar Money")
        self._emit_blank()

        self._emit_description("Duration of time (e.g., imprisonment term)")
        self._emit("scalar Duration")
        self._emit_blank()

        self._emit_description("Percentage value")
        self._emit("scalar Percent")
        self._emit_blank()

        self._emit_description("Date in ISO 8601 format")
        self._emit("scalar Date")
        self._emit_blank()

    def _emit_enums(self) -> None:
        """Emit enum type definitions."""
        # Currency enum
        self._emit_description("Supported currency types")
        self._emit("enum Currency {")
        self._indent_level += 1
        for currency in nodes.Currency:
            self._emit(currency.name)
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Element type enum
        self._emit_description("Types of legal elements")
        self._emit("enum ElementType {")
        self._indent_level += 1
        self._emit("ACTUS_REUS")
        self._emit("MENS_REA")
        self._emit("CIRCUMSTANCE")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

    # =========================================================================
    # Core Legal Types
    # =========================================================================

    def _emit_core_types(self) -> None:
        """Emit core legal type definitions."""
        # Definition type
        self._emit_description("Legal definition within a statute")
        self._emit("type Definition {")
        self._indent_level += 1
        self._emit_description("Term being defined")
        self._emit("term: String!")
        self._emit_description("Definition text")
        self._emit("definition: String!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Element type
        self._emit_description("Element of an offense (actus reus or mens rea)")
        self._emit("type Element {")
        self._indent_level += 1
        self._emit_description("Type of element")
        self._emit("elementType: ElementType!")
        self._emit_description("Element name/identifier")
        self._emit("name: String!")
        self._emit_description("Description of the element")
        self._emit("description: String!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Penalty type
        self._emit_description("Penalty specification for a statute")
        self._emit("type Penalty {")
        self._indent_level += 1
        self._emit_description("Minimum imprisonment term")
        self._emit("imprisonmentMin: Duration")
        self._emit_description("Maximum imprisonment term")
        self._emit("imprisonmentMax: Duration")
        self._emit_description("Minimum fine amount")
        self._emit("fineMin: Money")
        self._emit_description("Maximum fine amount")
        self._emit("fineMax: Money")
        self._emit_description("Additional penalty information")
        self._emit("supplementary: String")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Illustration type
        self._emit_description("Illustration example within a statute")
        self._emit("type Illustration {")
        self._indent_level += 1
        self._emit_description("Label (e.g., '(a)', '(b)')")
        self._emit("label: String")
        self._emit_description("Illustration description")
        self._emit("description: String!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Statute type
        self._emit_description("Legal statute/provision")
        self._emit("type Statute {")
        self._indent_level += 1
        self._emit_description("Section number (e.g., '299', '300')")
        self._emit("sectionNumber: String!")
        self._emit_description("Title of the statute")
        self._emit("title: String")
        self._emit_description("Legal definitions in this statute")
        self._emit("definitions: [Definition!]!")
        self._emit_description("Elements of the offense")
        self._emit("elements: [Element!]!")
        self._emit_description("Penalty specification")
        self._emit("penalty: Penalty")
        self._emit_description("Illustrative examples")
        self._emit("illustrations: [Illustration!]!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

    # =========================================================================
    # Struct Definitions
    # =========================================================================

    def _visit_struct_def(self, node: nodes.StructDefNode) -> None:
        """Generate GraphQL type for struct definition."""
        type_name = self._to_pascal_case(node.name)
        if type_name in self._defined_types:
            return
        self._defined_types.add(type_name)

        self._emit_description(f"Custom type: {node.name}")
        self._emit(f"type {type_name} {{")
        self._indent_level += 1

        for field in node.fields:
            field_name = self._to_camel_case(field.name)
            field_type = self._type_to_graphql(field.type_annotation)
            self._emit(f"{field_name}: {field_type}")

        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

    # =========================================================================
    # Statute Processing (for query generation)
    # =========================================================================

    def _visit_statute(self, node: nodes.StatuteNode) -> None:
        """Process statute for query type generation."""
        # Statutes are represented by the generic Statute type
        # Individual statute data will be resolved at runtime
        pass

    # =========================================================================
    # Query Root
    # =========================================================================

    def _emit_query_root(self, ast: nodes.ModuleNode) -> None:
        """Emit the Query root type."""
        self._emit_description("Root query type for statute API")
        self._emit("type Query {")
        self._indent_level += 1

        # Query for single statute by section number
        self._emit_description("Get a statute by section number")
        self._emit("statute(sectionNumber: String!): Statute")

        # Query for all statutes
        self._emit_description("Get all statutes")
        self._emit("statutes: [Statute!]!")

        # Query for statutes by element type
        self._emit_description("Find statutes containing a specific element type")
        self._emit("statutesByElementType(elementType: ElementType!): [Statute!]!")

        # Search statutes by text
        self._emit_description("Search statutes by text in title or definitions")
        self._emit("searchStatutes(query: String!): [Statute!]!")

        # Get statute definitions
        self._emit_description("Get all definitions across statutes")
        self._emit("allDefinitions: [Definition!]!")

        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Emit Mutation type for potential write operations
        self._emit_description("Root mutation type for statute API")
        self._emit("type Mutation {")
        self._indent_level += 1
        self._emit_description("Validate a statute definition (returns validation errors)")
        self._emit("validateStatute(input: StatuteInput!): ValidationResult!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Emit input types
        self._emit_input_types()

    def _emit_input_types(self) -> None:
        """Emit GraphQL input types for mutations."""
        # Statute input
        self._emit_description("Input type for statute validation")
        self._emit("input StatuteInput {")
        self._indent_level += 1
        self._emit("sectionNumber: String!")
        self._emit("title: String")
        self._emit("definitions: [DefinitionInput!]")
        self._emit("elements: [ElementInput!]")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Definition input
        self._emit_description("Input type for definition")
        self._emit("input DefinitionInput {")
        self._indent_level += 1
        self._emit("term: String!")
        self._emit("definition: String!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Element input
        self._emit_description("Input type for element")
        self._emit("input ElementInput {")
        self._indent_level += 1
        self._emit("elementType: ElementType!")
        self._emit("name: String!")
        self._emit("description: String!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Validation result
        self._emit_description("Result of statute validation")
        self._emit("type ValidationResult {")
        self._indent_level += 1
        self._emit("valid: Boolean!")
        self._emit("errors: [ValidationError!]!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

        # Validation error
        self._emit_description("Validation error details")
        self._emit("type ValidationError {")
        self._indent_level += 1
        self._emit("field: String!")
        self._emit("message: String!")
        self._emit("code: String!")
        self._indent_level -= 1
        self._emit("}")
        self._emit_blank()

    # =========================================================================
    # Type Conversion Helpers
    # =========================================================================

    def _type_to_graphql(self, node: nodes.TypeNode) -> str:
        """Convert Yuho type to GraphQL type."""
        if isinstance(node, nodes.BuiltinType):
            type_mapping = {
                "int": "Int",
                "float": "Float",
                "bool": "Boolean",
                "string": "String",
                "money": "Money",
                "percent": "Percent",
                "date": "Date",
                "duration": "Duration",
                "void": "Void",
            }
            return type_mapping.get(node.name, "String")

        elif isinstance(node, nodes.NamedType):
            return self._to_pascal_case(node.name)

        elif isinstance(node, nodes.OptionalType):
            inner = self._type_to_graphql(node.inner)
            # In GraphQL, types are nullable by default
            # Remove ! if present since optional
            return inner.rstrip("!")

        elif isinstance(node, nodes.ArrayType):
            elem = self._type_to_graphql(node.element_type)
            return f"[{elem}!]!"

        return "String"

    def _to_pascal_case(self, name: str) -> str:
        """Convert name to PascalCase for GraphQL types."""
        parts = name.replace("-", "_").split("_")
        return "".join(p.capitalize() for p in parts)

    def _to_camel_case(self, name: str) -> str:
        """Convert name to camelCase for GraphQL fields."""
        parts = name.replace("-", "_").split("_")
        if not parts:
            return name
        return parts[0].lower() + "".join(p.capitalize() for p in parts[1:])
