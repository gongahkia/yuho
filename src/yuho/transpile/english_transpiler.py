"""
English transpiler - controlled natural language generation.

Converts Yuho AST to readable English text using templates
for legal documents.
"""

from typing import List, Optional

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.transpile.base import TranspileTarget, TranspilerBase


class EnglishTranspiler(TranspilerBase, Visitor):
    """
    Transpile Yuho AST to controlled natural language (English).

    Uses templates for legal text generation with proper clause
    connectors and penalty formatting.
    """

    def __init__(self):
        self._output: List[str] = []
        self._indent_level = 0

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.ENGLISH

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to English text."""
        self._output = []
        self._indent_level = 0
        self._visit_module(ast)
        return "\n".join(self._output)

    def _emit(self, text: str) -> None:
        """Add a line to output with current indentation."""
        indent = "  " * self._indent_level
        self._output.append(f"{indent}{text}")

    def _emit_blank(self) -> None:
        """Add a blank line."""
        self._output.append("")

    # =========================================================================
    # Module and imports
    # =========================================================================

    def _visit_module(self, node: nodes.ModuleNode) -> None:
        """Generate English for entire module."""
        # Imports
        if node.imports:
            for imp in node.imports:
                self._visit_import(imp)
            self._emit_blank()

        # Type definitions
        if node.type_defs:
            self._emit("TYPE DEFINITIONS")
            self._emit("=" * 50)
            self._emit_blank()
            for struct in node.type_defs:
                self._visit_struct_def(struct)
                self._emit_blank()

        # Functions
        if node.function_defs:
            self._emit("FUNCTIONS")
            self._emit("=" * 50)
            self._emit_blank()
            for func in node.function_defs:
                self._visit_function_def(func)
                self._emit_blank()

        # Statutes (main content)
        for statute in node.statutes:
            self._visit_statute(statute)
            self._emit_blank()

        # Variables
        if node.variables:
            self._emit("DECLARATIONS")
            self._emit("=" * 50)
            self._emit_blank()
            for var in node.variables:
                self._visit_variable_decl(var)

    def _visit_import(self, node: nodes.ImportNode) -> None:
        """Generate English for import."""
        if node.is_wildcard:
            self._emit(f"Reference: All definitions from \"{node.path}\"")
        elif node.imported_names:
            names = ", ".join(node.imported_names)
            self._emit(f"Reference: {names} from \"{node.path}\"")
        else:
            self._emit(f"Reference: \"{node.path}\"")

    # =========================================================================
    # Statute blocks
    # =========================================================================

    def _visit_statute(self, node: nodes.StatuteNode) -> None:
        """Generate English for statute."""
        # Header
        title = node.title.value if node.title else "Untitled"
        self._emit(f"SECTION {node.section_number}: {title}")
        self._emit("=" * 60)
        self._emit_blank()

        # Definitions
        if node.definitions:
            self._emit("Definitions:")
            self._indent_level += 1
            for defn in node.definitions:
                self._emit(f'"{defn.term}" means {defn.definition.value}')
            self._indent_level -= 1
            self._emit_blank()

        # Elements
        if node.elements:
            self._emit("Elements of the offence:")
            self._indent_level += 1
            for elem in node.elements:
                self._visit_element(elem)
            self._indent_level -= 1
            self._emit_blank()

        # Penalty
        if node.penalty:
            self._visit_penalty(node.penalty)
            self._emit_blank()

        # Illustrations
        if node.illustrations:
            self._emit("Illustrations:")
            self._emit_blank()
            for i, illus in enumerate(node.illustrations, 1):
                label = illus.label or f"({chr(ord('a') + i - 1)})"
                self._emit(f"{label} {illus.description.value}")
            self._emit_blank()

    def _visit_element(self, node: nodes.ElementNode) -> None:
        """Generate English for element."""
        type_labels = {
            "actus_reus": "Physical element (actus reus)",
            "mens_rea": "Mental element (mens rea)",
            "circumstance": "Circumstance",
        }
        label = type_labels.get(node.element_type, node.element_type)

        # Handle description
        if isinstance(node.description, nodes.StringLit):
            self._emit(f"{label}: {node.description.value}")
        elif isinstance(node.description, nodes.MatchExprNode):
            self._emit(f"{label}: {node.name}")
            self._indent_level += 1
            self._visit_match_expr_english(node.description)
            self._indent_level -= 1
        else:
            desc = self._expr_to_english(node.description)
            self._emit(f"{label}: {desc}")

    def _visit_penalty(self, node: nodes.PenaltyNode) -> None:
        """Generate English for penalty."""
        self._emit("Penalty:")
        self._indent_level += 1

        parts: List[str] = []

        # Imprisonment
        if node.imprisonment_max:
            if node.imprisonment_min:
                min_str = self._duration_to_english(node.imprisonment_min)
                max_str = self._duration_to_english(node.imprisonment_max)
                parts.append(f"imprisonment for a term of not less than {min_str} and not more than {max_str}")
            else:
                max_str = self._duration_to_english(node.imprisonment_max)
                parts.append(f"imprisonment for a term which may extend to {max_str}")

        # Fine
        if node.fine_max:
            if node.fine_min:
                min_str = self._money_to_english(node.fine_min)
                max_str = self._money_to_english(node.fine_max)
                parts.append(f"a fine of not less than {min_str} and not more than {max_str}")
            else:
                max_str = self._money_to_english(node.fine_max)
                parts.append(f"a fine which may extend to {max_str}")

        # Combine parts
        if len(parts) == 2:
            self._emit(f"Shall be punished with {parts[0]}, or with {parts[1]}, or with both.")
        elif len(parts) == 1:
            self._emit(f"Shall be punished with {parts[0]}.")
        else:
            self._emit("Penalty to be determined.")

        # Supplementary
        if node.supplementary:
            self._emit_blank()
            self._emit(f"Additionally: {node.supplementary.value}")

        self._indent_level -= 1

    # =========================================================================
    # Match expressions
    # =========================================================================

    def _visit_match_expr_english(self, node: nodes.MatchExprNode) -> None:
        """Generate English for match expression."""
        if node.scrutinee:
            scrutinee = self._expr_to_english(node.scrutinee)
            self._emit(f"Based on {scrutinee}:")

        for i, arm in enumerate(node.arms):
            self._visit_match_arm_english(arm, i, len(node.arms))

    def _visit_match_arm_english(self, node: nodes.MatchArm, index: int, total: int) -> None:
        """Generate English for match arm."""
        # Pattern
        pattern = self._pattern_to_english(node.pattern)

        # Guard
        guard_str = ""
        if node.guard:
            guard = self._expr_to_english(node.guard)
            guard_str = f", provided that {guard}"

        # Body
        body = self._expr_to_english(node.body)

        # Connectors based on position
        if index == 0:
            connector = "If"
        elif isinstance(node.pattern, nodes.WildcardPattern):
            connector = "Otherwise"
            pattern = ""
        else:
            connector = "If"

        if pattern:
            self._emit(f"{connector} {pattern}{guard_str}: {body}")
        else:
            self._emit(f"{connector}{guard_str}: {body}")

    # =========================================================================
    # Struct definitions
    # =========================================================================

    def _visit_struct_def(self, node: nodes.StructDefNode) -> None:
        """Generate English for struct definition."""
        self._emit(f"Type \"{node.name}\" consists of:")
        self._indent_level += 1
        for field in node.fields:
            type_str = self._type_to_english(field.type_annotation)
            self._emit(f"- {field.name}: {type_str}")
        self._indent_level -= 1

    # =========================================================================
    # Function definitions
    # =========================================================================

    def _visit_function_def(self, node: nodes.FunctionDefNode) -> None:
        """Generate English for function definition."""
        params_str = ", ".join(
            f"{p.name} ({self._type_to_english(p.type_annotation)})"
            for p in node.params
        )
        ret_str = f" returning {self._type_to_english(node.return_type)}" if node.return_type else ""

        self._emit(f"Function \"{node.name}\"({params_str}){ret_str}:")
        self._indent_level += 1
        for stmt in node.body.statements:
            self._visit_statement(stmt)
        self._indent_level -= 1

    # =========================================================================
    # Statements
    # =========================================================================

    def _visit_variable_decl(self, node: nodes.VariableDecl) -> None:
        """Generate English for variable declaration."""
        type_str = self._type_to_english(node.type_annotation)
        if node.value:
            value_str = self._expr_to_english(node.value)
            self._emit(f"Let {node.name} be a {type_str} with value {value_str}.")
        else:
            self._emit(f"Let {node.name} be a {type_str}.")

    def _visit_statement(self, node: nodes.ASTNode) -> None:
        """Generate English for statement."""
        if isinstance(node, nodes.VariableDecl):
            self._visit_variable_decl(node)
        elif isinstance(node, nodes.AssignmentStmt):
            target = self._expr_to_english(node.target)
            value = self._expr_to_english(node.value)
            self._emit(f"Set {target} to {value}.")
        elif isinstance(node, nodes.ReturnStmt):
            if node.value:
                value = self._expr_to_english(node.value)
                self._emit(f"Return {value}.")
            else:
                self._emit("Return.")
        elif isinstance(node, nodes.PassStmt):
            self._emit("(No action)")
        elif isinstance(node, nodes.ExpressionStmt):
            expr = self._expr_to_english(node.expression)
            self._emit(f"{expr}")

    # =========================================================================
    # Helper methods for English generation
    # =========================================================================

    def _expr_to_english(self, node: nodes.ASTNode) -> str:
        """Convert expression to English."""
        if isinstance(node, nodes.IntLit):
            return str(node.value)
        elif isinstance(node, nodes.FloatLit):
            return str(node.value)
        elif isinstance(node, nodes.BoolLit):
            return "true" if node.value else "false"
        elif isinstance(node, nodes.StringLit):
            return f'"{node.value}"'
        elif isinstance(node, nodes.MoneyNode):
            return self._money_to_english(node)
        elif isinstance(node, nodes.PercentNode):
            return f"{node.value}%"
        elif isinstance(node, nodes.DateNode):
            return node.value.strftime("%d %B %Y")
        elif isinstance(node, nodes.DurationNode):
            return self._duration_to_english(node)
        elif isinstance(node, nodes.IdentifierNode):
            return node.name
        elif isinstance(node, nodes.FieldAccessNode):
            base = self._expr_to_english(node.base)
            return f"{base}'s {node.field_name}"
        elif isinstance(node, nodes.IndexAccessNode):
            base = self._expr_to_english(node.base)
            index = self._expr_to_english(node.index)
            return f"{base}[{index}]"
        elif isinstance(node, nodes.FunctionCallNode):
            callee = self._expr_to_english(node.callee)
            args = ", ".join(self._expr_to_english(a) for a in node.args)
            return f"{callee}({args})"
        elif isinstance(node, nodes.BinaryExprNode):
            left = self._expr_to_english(node.left)
            right = self._expr_to_english(node.right)
            op = self._operator_to_english(node.operator)
            return f"{left} {op} {right}"
        elif isinstance(node, nodes.UnaryExprNode):
            operand = self._expr_to_english(node.operand)
            if node.operator == "!":
                return f"not {operand}"
            return f"{node.operator}{operand}"
        elif isinstance(node, nodes.PassExprNode):
            return "nothing"
        elif isinstance(node, nodes.MatchExprNode):
            return "(see decision tree below)"
        elif isinstance(node, nodes.StructLiteralNode):
            if node.struct_name:
                return f"a {node.struct_name}"
            return "a record"
        else:
            return str(node)

    def _pattern_to_english(self, node: nodes.PatternNode) -> str:
        """Convert pattern to English."""
        if isinstance(node, nodes.WildcardPattern):
            return "in any other case"
        elif isinstance(node, nodes.LiteralPattern):
            return f"the value is {self._expr_to_english(node.literal)}"
        elif isinstance(node, nodes.BindingPattern):
            return f"the value (let us call it {node.name})"
        elif isinstance(node, nodes.StructPattern):
            fields = ", ".join(fp.name for fp in node.fields)
            return f"it matches {node.type_name} with {fields}"
        else:
            return "the condition is met"

    def _type_to_english(self, node: nodes.TypeNode) -> str:
        """Convert type to English."""
        if isinstance(node, nodes.BuiltinType):
            type_names = {
                "int": "integer",
                "float": "decimal number",
                "bool": "boolean",
                "string": "text",
                "money": "monetary amount",
                "percent": "percentage",
                "date": "date",
                "duration": "time period",
                "void": "nothing",
            }
            return type_names.get(node.name, node.name)
        elif isinstance(node, nodes.NamedType):
            return node.name
        elif isinstance(node, nodes.OptionalType):
            inner = self._type_to_english(node.inner)
            return f"optional {inner}"
        elif isinstance(node, nodes.ArrayType):
            elem = self._type_to_english(node.element_type)
            return f"list of {elem}"
        elif isinstance(node, nodes.GenericType):
            args = ", ".join(self._type_to_english(a) for a in node.type_args)
            return f"{node.base} of {args}"
        else:
            return "value"

    def _operator_to_english(self, op: str) -> str:
        """Convert operator to English."""
        operators = {
            "+": "plus",
            "-": "minus",
            "*": "times",
            "/": "divided by",
            "%": "modulo",
            "==": "equals",
            "!=": "does not equal",
            "<": "is less than",
            ">": "is greater than",
            "<=": "is at most",
            ">=": "is at least",
            "&&": "and",
            "||": "or",
        }
        return operators.get(op, op)

    def _duration_to_english(self, node: nodes.DurationNode) -> str:
        """Convert duration to English."""
        parts: List[str] = []
        if node.years:
            parts.append(f"{node.years} year{'s' if node.years != 1 else ''}")
        if node.months:
            parts.append(f"{node.months} month{'s' if node.months != 1 else ''}")
        if node.days:
            parts.append(f"{node.days} day{'s' if node.days != 1 else ''}")
        if node.hours:
            parts.append(f"{node.hours} hour{'s' if node.hours != 1 else ''}")
        if node.minutes:
            parts.append(f"{node.minutes} minute{'s' if node.minutes != 1 else ''}")
        if node.seconds:
            parts.append(f"{node.seconds} second{'s' if node.seconds != 1 else ''}")

        if not parts:
            return "no time"
        elif len(parts) == 1:
            return parts[0]
        else:
            return ", ".join(parts[:-1]) + " and " + parts[-1]

    def _money_to_english(self, node: nodes.MoneyNode) -> str:
        """Convert money to English."""
        currency_symbols = {
            nodes.Currency.SGD: "S$",
            nodes.Currency.USD: "US$",
            nodes.Currency.EUR: "€",
            nodes.Currency.GBP: "£",
            nodes.Currency.JPY: "¥",
            nodes.Currency.CNY: "¥",
            nodes.Currency.INR: "₹",
            nodes.Currency.AUD: "A$",
            nodes.Currency.CAD: "C$",
            nodes.Currency.CHF: "CHF ",
        }
        symbol = currency_symbols.get(node.currency, "$")
        # Format with thousands separator
        amount_str = f"{node.amount:,.2f}"
        return f"{symbol}{amount_str}"
