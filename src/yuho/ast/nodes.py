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
class IsInfringedNode(ASTNode):
    """lam4-style ``is_infringed(<section>)`` predicate.

    Built when the AST builder sees a call to the reserved identifier
    ``is_infringed`` with a single argument that names a section. The
    argument is canonicalised to a section number string (e.g. ``"299"``,
    ``"376AA"``).

    Semantics: at evaluation time, ``IS_INFRINGED`` evaluates ``true``
    iff the encoded fact pattern satisfies every required element of
    the named section, after applying its prioritised exceptions. The
    intent is to let composing sections (s107 abetment, s34 common
    intention) compose with arbitrary base offences without re-stating
    every element.
    """

    section_ref: str  # canonical section number, e.g. "299", "376AA"

    def accept(self, visitor: "Visitor"):
        return visitor.visit_is_infringed(self)

    def children(self) -> List[ASTNode]:
        return []


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
        result: List[ASTNode] = [self.pattern]
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
        result: List[ASTNode] = []
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
    doc_comment: Optional[str] = None

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
    doc_comment: Optional[str] = None

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
    doc_comment: Optional[str] = None

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
        result: List[ASTNode] = [self.type_annotation]
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

    element_type: str  # actus_reus, mens_rea, circumstance, obligation, prohibition, permission
    name: str
    description: ASTNode  # usually StringLit or match expression
    caused_by: Optional[str] = None  # phase 12: causal link to another element
    burden: Optional[str] = None  # phase 12: "prosecution" or "defence"
    burden_standard: Optional[str] = None  # phase 12: proof standard
    doc_comment: Optional[str] = None
    actor: Optional[str] = None  # party role performing the act
    patient: Optional[str] = None  # party role receiving the act

    def accept(self, visitor: "Visitor"):
        return visitor.visit_element(self)

    def children(self) -> List[ASTNode]:
        return [self.description]


@dataclass(frozen=True)
class ElementGroupNode(ASTNode):
    """
    Group of elements with a logical combinator.

    combinator: "all_of" (conjunctive/AND) or "any_of" (disjunctive/OR)
    members: nested elements or element groups
    """

    combinator: str  # "all_of" or "any_of"
    members: Tuple[Union["ElementNode", "ElementGroupNode"], ...]

    def accept(self, visitor: "Visitor"):
        return visitor.visit_element_group(self)

    def children(self) -> List[ASTNode]:
        return list(self.members)


@dataclass(frozen=True)
class PenaltyNode(ASTNode):
    """
    Penalty specification for a statute.

    Can specify imprisonment, fine, caning, death penalty, or combinations.
    """

    imprisonment_min: Optional[DurationNode] = None
    imprisonment_max: Optional[DurationNode] = None
    fine_min: Optional[MoneyNode] = None
    fine_max: Optional[MoneyNode] = None
    fine_unlimited: bool = False  # G8: `fine := unlimited` — statute-level uncapped fine
    caning_min: Optional[int] = None
    caning_max: Optional[int] = None
    caning_unspecified: bool = False  # G14: `caning := unspecified` — statute-level "liable to caning" without a stroke count
    death_penalty: Optional[bool] = None
    supplementary: Optional[StringLit] = None
    sentencing: Optional[str] = None  # phase 14: "concurrent" or "consecutive"
    combinator: Optional[str] = None  # G8: "cumulative" | "alternative" | "or_both"; None = cumulative (back-compat)
    condition: Optional[str] = None  # G9: identifier from `penalty when <ident> { ... }` — names a conditional branch
    nested: Optional["PenaltyNode"] = None  # G12: nested sub-combinator (e.g. `penalty cumulative { imprisonment; or_both { fine; caning } }`)
    mandatory_min_imprisonment: Optional[DurationNode] = None  # phase 14
    mandatory_min_fine: Optional[MoneyNode] = None  # phase 14

    def accept(self, visitor: "Visitor"):
        return visitor.visit_penalty(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = []
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
class ExceptionNode(ASTNode):
    """
    Exception/proviso/defence within a statute.

    Models General Exceptions (e.g., Ch IV ss76-106), provisos, and
    statutory defences that modify the main offense.
    """

    label: Optional[str]
    condition: StringLit
    effect: Optional[StringLit] = None
    guard: Optional[ASTNode] = None
    priority: Optional[int] = None
    defeats: Optional[str] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_exception(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = [self.condition]
        if self.effect:
            result.append(self.effect)
        if self.guard:
            result.append(self.guard)
        return result


@dataclass(frozen=True)
class CaseLawNode(ASTNode):
    """
    Case law reference associated with a statute.

    Links judicial interpretations to specific statutory elements.
    """

    case_name: StringLit
    citation: Optional[StringLit] = None
    holding: StringLit = field(default_factory=lambda: StringLit(value=""))
    element_ref: Optional[str] = None  # name of element this case interprets

    def accept(self, visitor: "Visitor"):
        return visitor.visit_caselaw(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = [self.case_name, self.holding]
        if self.citation:
            result.append(self.citation)
        return result


@dataclass(frozen=True)
class TemporalConstraintNode(ASTNode):
    """Temporal ordering constraint between elements (e.g., act precedes death)."""

    subject: str
    relation: str  # "precedes", "during", "after"
    object: str

    def accept(self, visitor: "Visitor"):
        return visitor.visit_temporal_constraint(self)


@dataclass(frozen=True)
class AnnotationNode(ASTNode):
    """Metadata annotation (@presumed, @precedent, @hierarchy, @amended)."""

    name: str  # "presumed", "precedent", "hierarchy", "amended"
    args: Tuple[str, ...] = ()

    def accept(self, visitor: "Visitor"):
        return visitor.visit_annotation(self)


@dataclass(frozen=True)
class LegalTestNode(ASTNode):
    """Conjunctive legal test: all requirements must hold for the test to pass."""

    name: str
    requirements: Tuple[ASTNode, ...]  # variable decls (bool fields)
    condition: Optional[ASTNode] = None  # requires expression (conjunction)
    annotations: Tuple[AnnotationNode, ...] = ()

    def accept(self, visitor: "Visitor"):
        return visitor.visit_legal_test(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = list(self.requirements)
        if self.condition:
            result.append(self.condition)
        return result


@dataclass(frozen=True)
class ConflictCheckNode(ASTNode):
    """Inter-file contradiction detection between statutes."""

    name: str
    source: str  # path or section reference
    target: str  # path or section reference
    annotations: Tuple[AnnotationNode, ...] = ()

    def accept(self, visitor: "Visitor"):
        return visitor.visit_conflict_check(self)


@dataclass(frozen=True)
class PartyNode(ASTNode):
    """Party/role declaration within a statute (e.g., offender, victim)."""

    role: str
    name: str
    type_annotation: Optional[TypeNode] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_party(self)

    def children(self) -> List[ASTNode]:
        return [self.type_annotation] if self.type_annotation else []


@dataclass(frozen=True)
class SubsectionNode(ASTNode):
    """
    G5: a numbered subsection inside a statute. Carries its own members
    (definitions / elements / penalty / illustrations / exceptions / nested
    subsections), matching the real structure of sections like s377BO (7
    subsections) and s511 (3). Effective/repealed dates are inherited from
    the parent statute unless overridden later.
    """

    number: str  # e.g. "(1)", "(2A)", "(a)"
    definitions: Tuple[DefinitionEntry, ...] = ()
    elements: Tuple[Union[ElementNode, ElementGroupNode], ...] = ()
    penalty: Optional[PenaltyNode] = None
    illustrations: Tuple[IllustrationNode, ...] = ()
    exceptions: Tuple[ExceptionNode, ...] = ()
    subsections: Tuple["SubsectionNode", ...] = ()           # nested subsections
    doc_comment: Optional[str] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_subsection(self) if hasattr(visitor, "visit_subsection") else None

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = []
        result.extend(self.definitions)
        result.extend(self.elements)
        if self.penalty: result.append(self.penalty)
        result.extend(self.illustrations)
        result.extend(self.exceptions)
        result.extend(self.subsections)
        return result


@dataclass(frozen=True)
class StatuteNode(ASTNode):
    """
    Statute block representing a legal provision.

    Contains section number, title, definitions, elements, penalties,
    illustrations, exceptions, and case law references.
    """

    section_number: str
    title: Optional[StringLit]
    definitions: Tuple[DefinitionEntry, ...]
    elements: Tuple[Union[ElementNode, ElementGroupNode], ...]
    penalty: Optional[PenaltyNode]
    illustrations: Tuple[IllustrationNode, ...]
    exceptions: Tuple[ExceptionNode, ...] = ()
    case_law: Tuple[CaseLawNode, ...] = ()
    subsections: Tuple[SubsectionNode, ...] = ()             # G5
    doc_comment: Optional[str] = None
    jurisdiction: Optional[str] = None
    jurisdiction_meta: Optional[Dict[str, str]] = None
    effective_date: Optional[str] = None  # phase 11: ISO date; first `effective` clause
    effective_dates: Tuple[str, ...] = ()  # G6: all effective clauses (orig + amendments)
    repealed_date: Optional[str] = None  # phase 11: ISO date
    subsumes: Optional[str] = None  # phase 13: section number
    amends: Optional[str] = None  # phase 11: section number
    parties: Tuple["PartyNode", ...] = ()
    temporal_constraints: Tuple["TemporalConstraintNode", ...] = ()
    annotations: Tuple["AnnotationNode", ...] = ()

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
        result.extend(self.exceptions)
        result.extend(self.case_law)
        result.extend(self.subsections)
        return result


# =============================================================================
# Enum Definition (Phase 9A)
# =============================================================================


@dataclass(frozen=True)
class EnumVariant(ASTNode):
    """Single variant in an enum definition."""

    name: str
    payload_types: Tuple[TypeNode, ...] = ()  # optional carried data

    def accept(self, visitor: "Visitor"):
        return visitor.visit_enum_variant(self)

    def children(self) -> List[ASTNode]:
        return list(self.payload_types)


@dataclass(frozen=True)
class EnumDefNode(ASTNode):
    """Enum type definition with named variants."""

    name: str
    variants: Tuple[EnumVariant, ...]
    doc_comment: Optional[str] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_enum_def(self)

    def children(self) -> List[ASTNode]:
        return list(self.variants)


# =============================================================================
# Type Alias (Phase 9B)
# =============================================================================


@dataclass(frozen=True)
class TypeAliasNode(ASTNode):
    """Type alias declaration: type MensRea = string"""

    name: str
    target_type: TypeNode
    doc_comment: Optional[str] = None

    def accept(self, visitor: "Visitor"):
        return visitor.visit_type_alias(self)

    def children(self) -> List[ASTNode]:
        return [self.target_type]


# =============================================================================
# Refinement Type (Phase 9C)
# =============================================================================


@dataclass(frozen=True)
class RefinementTypeNode(TypeNode):
    """Refinement type with range constraint: int{0..99}"""

    base_type: TypeNode
    lower_bound: ASTNode
    upper_bound: ASTNode

    def accept(self, visitor: "Visitor"):
        return visitor.visit_refinement_type(self)

    def children(self) -> List[ASTNode]:
        return [self.base_type, self.lower_bound, self.upper_bound]


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
    enum_defs: Tuple[EnumDefNode, ...] = ()
    type_aliases: Tuple[TypeAliasNode, ...] = ()
    legal_tests: Tuple[LegalTestNode, ...] = ()
    conflict_checks: Tuple[ConflictCheckNode, ...] = ()

    def accept(self, visitor: "Visitor"):
        return visitor.visit_module(self)

    def children(self) -> List[ASTNode]:
        result: List[ASTNode] = []
        result.extend(self.imports)
        result.extend(self.references)
        result.extend(self.type_defs)
        result.extend(self.enum_defs)
        result.extend(self.type_aliases)
        result.extend(self.function_defs)
        result.extend(self.statutes)
        result.extend(self.variables)
        result.extend(self.assertions)
        result.extend(self.legal_tests)
        result.extend(self.conflict_checks)
        return result
