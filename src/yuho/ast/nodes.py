"""
AST node definitions for Yuho v5.

All nodes are immutable dataclasses with source_location tracking
and an accept(visitor) method for the Visitor pattern.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional, List, Dict, Tuple, Union

if TYPE_CHECKING:
    from yuho.ast.visitor import Visitor
    from yuho.parser.source_location import SourceLocation


# =============================================================================
# Currency Enum
# =============================================================================


class Currency(Enum):
    """Supported currency types for MoneyNode."""

    SGD = auto()
    USD = auto()
    EUR = auto()
    GBP = auto()
    JPY = auto()
    CNY = auto()
    INR = auto()
    AUD = auto()
    CAD = auto()
    CHF = auto()

    @classmethod
    def from_symbol(cls, symbol: str) -> "Currency":
        """Convert currency symbol to Currency enum."""
        mapping = {
            "$": cls.SGD,  # Default $ to SGD for Singapore context
            "£": cls.GBP,
            "€": cls.EUR,
            "¥": cls.JPY,
            "₹": cls.INR,
            "SGD": cls.SGD,
            "USD": cls.USD,
            "EUR": cls.EUR,
            "GBP": cls.GBP,
            "JPY": cls.JPY,
            "CNY": cls.CNY,
            "INR": cls.INR,
            "AUD": cls.AUD,
            "CAD": cls.CAD,
            "CHF": cls.CHF,
        }
        return mapping.get(symbol, cls.USD)


# =============================================================================
# Base AST Node
# =============================================================================


@dataclass(frozen=True)
class ASTNode(ABC):
    """
    Base class for all AST nodes.

    All nodes are immutable (frozen dataclass) and carry source location
    information for error reporting and IDE features.
    """

    source_location: Optional["SourceLocation"] = field(default=None, compare=False, kw_only=True)

    @abstractmethod
    def accept(self, visitor: "Visitor"):
        """Accept a visitor for double-dispatch traversal."""
        pass

    def children(self) -> List["ASTNode"]:
        """Return child nodes for generic traversal. Override in subclasses."""
        return []


# =============================================================================
# Type Nodes
# =============================================================================


@dataclass(frozen=True)
class TypeNode(ASTNode):
    """Base class for type annotations."""

    def accept(self, visitor: "Visitor"):
        return visitor.visit_type(self)


@dataclass(frozen=True)
class BuiltinType(TypeNode):
    """Built-in primitive type (int, float, bool, string, money, etc.)."""

    name: str  # "int", "float", "bool", "string", "money", "percent", "date", "duration", "void"

    def accept(self, visitor: "Visitor"):
        return visitor.visit_builtin_type(self)


@dataclass(frozen=True)
class NamedType(TypeNode):
    """User-defined type reference (struct name)."""

    name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_named_type(self)


@dataclass(frozen=True)
class GenericType(TypeNode):
    """Generic type application, e.g., List<int>."""

    base: str
    type_args: Tuple[TypeNode, ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_generic_type(self)

    def children(self) -> List[ASTNode]:
        return list(self.type_args)


@dataclass(frozen=True)
class OptionalType(TypeNode):
    """Optional type, e.g., int?."""

    inner: TypeNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_optional_type(self)

    def children(self) -> List[ASTNode]:
        return [self.inner]


@dataclass(frozen=True)
class ArrayType(TypeNode):
    """Array type, e.g., [int]."""

    element_type: TypeNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_array_type(self)

    def children(self) -> List[ASTNode]:
        return [self.element_type]


# =============================================================================
# Literal Nodes
# =============================================================================


@dataclass(frozen=True)
class IntLit(ASTNode):
    """Integer literal."""

    value: int

    def accept(self, visitor: "Visitor"):
        return visitor.visit_int_lit(self)


@dataclass(frozen=True)
class FloatLit(ASTNode):
    """Floating-point literal."""

    value: float

    def accept(self, visitor: "Visitor"):
        return visitor.visit_float_lit(self)


@dataclass(frozen=True)
class BoolLit(ASTNode):
    """Boolean literal (TRUE/FALSE)."""

    value: bool

    def accept(self, visitor: "Visitor"):
        return visitor.visit_bool_lit(self)


@dataclass(frozen=True)
class StringLit(ASTNode):
    """String literal with escape sequences processed."""

    value: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_string_lit(self)


@dataclass(frozen=True)
class MoneyNode(ASTNode):
    """
    Money literal with currency and amount.

    The amount is stored as Decimal for precise financial calculations.
    """

    currency: Currency
    amount: Decimal

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

    def accept(self, visitor: "Visitor"):
        return visitor.visit_money(self)


@dataclass(frozen=True)
class PercentNode(ASTNode):
    """
    Percentage literal.

    The value is stored as Decimal and validated to be in 0-100 range.
    """

    value: Decimal

    def __post_init__(self):
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))
        if not (0 <= self.value <= 100):
            raise ValueError(f"Percent value must be 0-100, got {self.value}")

    def accept(self, visitor: "Visitor"):
        return visitor.visit_percent(self)


@dataclass(frozen=True)
class DateNode(ASTNode):
    """
    Date literal in ISO8601 format (YYYY-MM-DD).

    Wraps datetime.date for date operations.
    """

    value: date

    @classmethod
    def from_iso8601(cls, date_str: str, source_location=None) -> "DateNode":
        """Parse ISO8601 date string."""
        return cls(value=date.fromisoformat(date_str), source_location=source_location)

    def accept(self, visitor: "Visitor"):
        return visitor.visit_date(self)


@dataclass(frozen=True)
class DurationNode(ASTNode):
    """
    Duration literal with years, months, days, hours, minutes, seconds.

    Any component can be 0. The total duration is the sum of all components.
    """

    years: int = 0
    months: int = 0
    days: int = 0
    hours: int = 0
    minutes: int = 0
    seconds: int = 0

    def accept(self, visitor: "Visitor"):
        return visitor.visit_duration(self)

    def total_days(self) -> int:
        """Approximate total days (assumes 30 days/month, 365 days/year)."""
        return self.years * 365 + self.months * 30 + self.days

    def __str__(self) -> str:
        parts = []
        if self.years:
            parts.append(f"{self.years} year{'s' if self.years != 1 else ''}")
        if self.months:
            parts.append(f"{self.months} month{'s' if self.months != 1 else ''}")
        if self.days:
            parts.append(f"{self.days} day{'s' if self.days != 1 else ''}")
        if self.hours:
            parts.append(f"{self.hours} hour{'s' if self.hours != 1 else ''}")
        if self.minutes:
            parts.append(f"{self.minutes} minute{'s' if self.minutes != 1 else ''}")
        if self.seconds:
            parts.append(f"{self.seconds} second{'s' if self.seconds != 1 else ''}")
        return ", ".join(parts) if parts else "0 days"


# =============================================================================
# Expression Nodes
# =============================================================================


@dataclass(frozen=True)
class IdentifierNode(ASTNode):
    """Identifier reference."""

    name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_identifier(self)


@dataclass(frozen=True)
class FieldAccessNode(ASTNode):
    """Field access expression: base.field."""

    base: ASTNode  # ExprNode
    field_name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_field_access(self)

    def children(self) -> List[ASTNode]:
        return [self.base]


@dataclass(frozen=True)
class IndexAccessNode(ASTNode):
    """Index access expression: base[index]."""

    base: ASTNode  # ExprNode
    index: ASTNode  # ExprNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_index_access(self)

    def children(self) -> List[ASTNode]:
        return [self.base, self.index]


@dataclass(frozen=True)
class FunctionCallNode(ASTNode):
    """Function call expression: callee(args...)."""

    callee: Union[IdentifierNode, FieldAccessNode]
    args: Tuple[ASTNode, ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_function_call(self)

    def children(self) -> List[ASTNode]:
        return [self.callee] + list(self.args)


@dataclass(frozen=True)
class BinaryExprNode(ASTNode):
    """Binary expression: left op right."""

    left: ASTNode
    operator: str  # "+", "-", "*", "/", "==", "!=", "<", ">", "<=", ">=", "&&", "||"
    right: ASTNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_binary_expr(self)

    def children(self) -> List[ASTNode]:
        return [self.left, self.right]


@dataclass(frozen=True)
class UnaryExprNode(ASTNode):
    """Unary expression: op operand."""

    operator: str  # "!", "-"
    operand: ASTNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_unary_expr(self)

    def children(self) -> List[ASTNode]:
        return [self.operand]


@dataclass(frozen=True)
class PassExprNode(ASTNode):
    """Pass expression (null/none equivalent)."""

    def accept(self, visitor: "Visitor"):
        return visitor.visit_pass_expr(self)


# =============================================================================
# Pattern Nodes
# =============================================================================


@dataclass(frozen=True)
class PatternNode(ASTNode):
    """Base class for match patterns."""

    def accept(self, visitor: "Visitor"):
        return visitor.visit_pattern(self)


@dataclass(frozen=True)
class WildcardPattern(PatternNode):
    """Wildcard pattern (_) that matches anything."""

    def accept(self, visitor: "Visitor"):
        return visitor.visit_wildcard_pattern(self)


@dataclass(frozen=True)
class LiteralPattern(PatternNode):
    """Literal pattern that matches a specific value."""

    literal: ASTNode  # IntLit, StringLit, BoolLit, etc.

    def accept(self, visitor: "Visitor"):
        return visitor.visit_literal_pattern(self)

    def children(self) -> List[ASTNode]:
        return [self.literal]


@dataclass(frozen=True)
class BindingPattern(PatternNode):
    """Binding pattern that captures the matched value."""

    name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_binding_pattern(self)


@dataclass(frozen=True)
class FieldPattern(ASTNode):
    """Field pattern within a struct pattern."""

    name: str
    pattern: Optional[PatternNode] = None  # None means just match by name

    def accept(self, visitor: "Visitor"):
        return visitor.visit_field_pattern(self)

    def children(self) -> List[ASTNode]:
        return [self.pattern] if self.pattern else []


@dataclass(frozen=True)
class StructPattern(PatternNode):
    """Struct pattern for destructuring."""

    type_name: str
    fields: Tuple[FieldPattern, ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_struct_pattern(self)

    def children(self) -> List[ASTNode]:
        return list(self.fields)


# =============================================================================
# Match Expression
# =============================================================================


@dataclass(frozen=True)
class MatchArm(ASTNode):
    """A single arm in a match expression."""

    pattern: PatternNode
    guard: Optional[ASTNode] = None  # Optional guard expression
    body: ASTNode = field(default_factory=PassExprNode)  # ExprNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_match_arm(self)

    def children(self) -> List[ASTNode]:
        result = [self.pattern]
        if self.guard:
            result.append(self.guard)
        result.append(self.body)
        return result


@dataclass(frozen=True)
class MatchExprNode(ASTNode):
    """
    Match expression with scrutinee and arms.

    The ensure_exhaustiveness flag indicates whether the type checker
    should verify that all cases are covered.
    """

    scrutinee: Optional[ASTNode]  # None for bare match blocks
    arms: Tuple[MatchArm, ...]
    ensure_exhaustiveness: bool = True

    def accept(self, visitor: "Visitor"):
        return visitor.visit_match_expr(self)

    def children(self) -> List[ASTNode]:
        result = []
        if self.scrutinee:
            result.append(self.scrutinee)
        result.extend(self.arms)
        return result


# =============================================================================
# Struct Definition and Literal
# =============================================================================


@dataclass(frozen=True)
class FieldDef(ASTNode):
    """Field definition within a struct."""

    type_annotation: TypeNode
    name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_field_def(self)

    def children(self) -> List[ASTNode]:
        return [self.type_annotation]


@dataclass(frozen=True)
class StructDefNode(ASTNode):
    """Struct type definition."""

    name: str
    fields: Tuple[FieldDef, ...]
    type_params: Tuple[str, ...] = ()  # Generic type parameters

    def accept(self, visitor: "Visitor"):
        return visitor.visit_struct_def(self)

    def children(self) -> List[ASTNode]:
        return list(self.fields)


@dataclass(frozen=True)
class FieldAssignment(ASTNode):
    """Field assignment within a struct literal."""

    name: str
    value: ASTNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_field_assignment(self)

    def children(self) -> List[ASTNode]:
        return [self.value]


@dataclass(frozen=True)
class StructLiteralNode(ASTNode):
    """Struct literal instantiation."""

    struct_name: Optional[str]  # None for anonymous struct literals
    field_values: Tuple[FieldAssignment, ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_struct_literal(self)

    def children(self) -> List[ASTNode]:
        return list(self.field_values)

    def get_field(self, name: str) -> Optional[FieldAssignment]:
        """Get a field assignment by name."""
        for fa in self.field_values:
            if fa.name == name:
                return fa
        return None


# =============================================================================
# Function Definition
# =============================================================================


@dataclass(frozen=True)
class ParamDef(ASTNode):
    """Parameter definition in a function."""

    type_annotation: TypeNode
    name: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_param_def(self)

    def children(self) -> List[ASTNode]:
        return [self.type_annotation]


@dataclass(frozen=True)
class Block(ASTNode):
    """Block of statements."""

    statements: Tuple[ASTNode, ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_block(self)

    def children(self) -> List[ASTNode]:
        return list(self.statements)


@dataclass(frozen=True)
class FunctionDefNode(ASTNode):
    """Function definition."""

    name: str
    params: Tuple[ParamDef, ...]
    return_type: Optional[TypeNode]
    body: Block

    def accept(self, visitor: "Visitor"):
        return visitor.visit_function_def(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = list(self.params)
        if self.return_type:
            result.append(self.return_type)
        result.append(self.body)
        return result


# =============================================================================
# Statements
# =============================================================================


@dataclass(frozen=True)
class VariableDecl(ASTNode):
    """Variable declaration statement."""

    type_annotation: TypeNode
    name: str
    value: Optional[ASTNode] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_variable_decl(self)

    def children(self) -> List[ASTNode]:
        result = [self.type_annotation]
        if self.value:
            result.append(self.value)
        return result


@dataclass(frozen=True)
class AssignmentStmt(ASTNode):
    """Assignment statement."""

    target: ASTNode  # IdentifierNode, FieldAccessNode, or IndexAccessNode
    value: ASTNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_assignment_stmt(self)

    def children(self) -> List[ASTNode]:
        return [self.target, self.value]


@dataclass(frozen=True)
class ReturnStmt(ASTNode):
    """Return statement."""

    value: Optional[ASTNode] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_return_stmt(self)

    def children(self) -> List[ASTNode]:
        return [self.value] if self.value else []


@dataclass(frozen=True)
class PassStmt(ASTNode):
    """Pass statement (no-op)."""

    def accept(self, visitor: "Visitor"):
        return visitor.visit_pass_stmt(self)


@dataclass(frozen=True)
class AssertStmt(ASTNode):
    """Assert statement for test files."""

    condition: ASTNode  # Usually a BinaryExprNode with ==
    message: Optional[StringLit] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_assert_stmt(self)

    def children(self) -> List[ASTNode]:
        result = [self.condition]
        if self.message:
            result.append(self.message)
        return result


@dataclass(frozen=True)
class ReferencingStmt(ASTNode):
    """Referencing statement for test files to import statutes."""

    path: str  # e.g., "s300_murder/statute"

    def accept(self, visitor: "Visitor"):
        return visitor.visit_referencing_stmt(self)


@dataclass(frozen=True)
class ExpressionStmt(ASTNode):
    """Expression statement."""

    expression: ASTNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_expression_stmt(self)

    def children(self) -> List[ASTNode]:
        return [self.expression]


# =============================================================================
# Statute-specific Nodes
# =============================================================================


@dataclass(frozen=True)
class DefinitionEntry(ASTNode):
    """Definition entry within a statute's definitions block."""

    term: str
    definition: StringLit

    def accept(self, visitor: "Visitor"):
        return visitor.visit_definition_entry(self)

    def children(self) -> List[ASTNode]:
        return [self.definition]


@dataclass(frozen=True)
class ElementNode(ASTNode):
    """
    Element of an offense (actus reus or mens rea).

    element_type: "actus_reus", "mens_rea", or "circumstance"
    """

    element_type: str
    name: str
    description: ASTNode  # Usually StringLit or match expression

    def accept(self, visitor: "Visitor"):
        return visitor.visit_element(self)

    def children(self) -> List[ASTNode]:
        return [self.description]


@dataclass(frozen=True)
class PenaltyNode(ASTNode):
    """
    Penalty specification for a statute.

    Can specify imprisonment, fine, or both, with optional ranges.
    """

    imprisonment_min: Optional[DurationNode] = None
    imprisonment_max: Optional[DurationNode] = None
    fine_min: Optional[MoneyNode] = None
    fine_max: Optional[MoneyNode] = None
    supplementary: Optional[StringLit] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_penalty(self)

    def children(self) -> List[ASTNode]:
        result = []
        if self.imprisonment_min:
            result.append(self.imprisonment_min)
        if self.imprisonment_max:
            result.append(self.imprisonment_max)
        if self.fine_min:
            result.append(self.fine_min)
        if self.fine_max:
            result.append(self.fine_max)
        if self.supplementary:
            result.append(self.supplementary)
        return result


@dataclass(frozen=True)
class IllustrationNode(ASTNode):
    """Illustration example within a statute."""

    label: Optional[str]
    description: StringLit

    def accept(self, visitor: "Visitor"):
        return visitor.visit_illustration(self)

    def children(self) -> List[ASTNode]:
        return [self.description]


@dataclass(frozen=True)
class StatuteNode(ASTNode):
    """
    Statute block representing a legal provision.

    Contains section number, title, definitions, elements, penalties,
    and illustrations.
    """

    section_number: str
    title: Optional[StringLit]
    definitions: Tuple[DefinitionEntry, ...]
    elements: Tuple[ElementNode, ...]
    penalty: Optional[PenaltyNode]
    illustrations: Tuple[IllustrationNode, ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_statute(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = []
        if self.title:
            result.append(self.title)
        result.extend(self.definitions)
        result.extend(self.elements)
        if self.penalty:
            result.append(self.penalty)
        result.extend(self.illustrations)
        return result


# =============================================================================
# Import Node
# =============================================================================


@dataclass(frozen=True)
class ImportNode(ASTNode):
    """
    Import statement for referencing other .yh files.

    imported_names: List of names to import, or ["*"] for wildcard
    """

    path: str
    imported_names: Tuple[str, ...]  # Empty tuple means import whole module

    def accept(self, visitor: "Visitor"):
        return visitor.visit_import(self)

    @property
    def is_wildcard(self) -> bool:
        return "*" in self.imported_names


# =============================================================================
# Module Node (Root)
# =============================================================================


@dataclass(frozen=True)
class ModuleNode(ASTNode):
    """
    Root AST node representing a complete Yuho module (.yh file).
    """

    imports: Tuple[ImportNode, ...]
    type_defs: Tuple[StructDefNode, ...]
    function_defs: Tuple[FunctionDefNode, ...]
    statutes: Tuple[StatuteNode, ...]
    variables: Tuple[VariableDecl, ...]
    references: Tuple["ReferencingStmt", ...] = ()
    assertions: Tuple["AssertStmt", ...] = ()

    def accept(self, visitor: "Visitor"):
        return visitor.visit_module(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = []
        result.extend(self.imports)
        result.extend(self.references)
        result.extend(self.type_defs)
        result.extend(self.function_defs)
        result.extend(self.statutes)
        result.extend(self.variables)
        result.extend(self.assertions)
        return result
