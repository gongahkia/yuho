"""
Abstract Syntax Tree node definitions for Yuho language
"""

from dataclasses import dataclass
from typing import List, Optional, Any, Union
from enum import Enum

# Enums for type safety
class YuhoType(Enum):
    INT = "int"
    FLOAT = "float"
    PERCENT = "percent"
    MONEY = "money"
    DATE = "date"
    DURATION = "duration"
    BOOL = "bool"
    STRING = "string"
    CUSTOM = "custom"

class Operator(Enum):
    PLUS = "+"
    MINUS = "-"
    MULT = "*"
    DIV = "/"
    EQUAL = "=="
    NOTEQUAL = "!="
    GT = ">"
    LT = "<"
    AND = "&&"
    OR = "||"

# Base AST Node
@dataclass
class ASTNode:
    """Base class for all AST nodes"""
    pass

# Program structure
@dataclass
class Program(ASTNode):
    """Root AST node representing a complete Yuho program"""
    statements: List[ASTNode]

@dataclass
class ImportStatement(ASTNode):
    """Import statement: referencing StructName from module_name"""
    struct_name: str
    module_name: str

# Type definitions
@dataclass
class TypeNode(ASTNode):
    """Type annotation node"""
    type_name: Union[YuhoType, str]

@dataclass
class QualifiedIdentifier(ASTNode):
    """Qualified identifier like module.StructName"""
    parts: List[str]

    def __str__(self):
        return ".".join(self.parts)

# Expressions
@dataclass
class Expression(ASTNode):
    """Base class for all expressions"""
    pass

@dataclass
class Literal(Expression):
    """Literal value expression"""
    value: Any
    literal_type: YuhoType

@dataclass
class Identifier(Expression):
    """Variable or function identifier"""
    name: str

@dataclass
class BinaryOperation(Expression):
    """Binary operation expression"""
    left: Expression
    operator: Operator
    right: Expression

@dataclass
class UnaryOperation(Expression):
    """Unary operation expression"""
    operator: str
    operand: Expression

# Statements
@dataclass
class Statement(ASTNode):
    """Base class for all statements"""
    pass

@dataclass
class Declaration(Statement):
    """Variable declaration"""
    type_node: TypeNode
    name: str
    value: Optional[Expression] = None

@dataclass
class Assignment(Statement):
    """Variable assignment"""
    name: str
    value: Expression

@dataclass
class PassStatement(Statement):
    """Pass statement (no-op)"""
    pass

# Structures
@dataclass
class StructMember(ASTNode):
    """Member of a struct definition"""
    type_node: TypeNode
    name: str

@dataclass
class StructDefinition(Statement):
    """Struct definition"""
    name: str
    members: List[StructMember]

@dataclass
class StructInstantiation(Expression):
    """Struct instantiation with field assignments"""
    struct_type: QualifiedIdentifier
    name: str
    fields: List['FieldAssignment']

@dataclass
class FieldAssignment(ASTNode):
    """Field assignment in struct instantiation"""
    field_name: str
    value: Expression

# Control structures
@dataclass
class CaseClause(ASTNode):
    """Case clause in match statement"""
    condition: Optional[Expression]  # None for wildcard (_)
    consequence: Expression

@dataclass
class MatchCase(Statement):
    """Match-case control structure"""
    expression: Optional[Expression]  # None for bare match {}
    cases: List[CaseClause]

# Functions
@dataclass
class Parameter(ASTNode):
    """Function parameter"""
    type_node: TypeNode
    name: str

@dataclass
class FunctionDefinition(Statement):
    """Function definition"""
    name: str
    parameters: List[Parameter]
    return_type: TypeNode
    body: List[Statement]

@dataclass
class FunctionCall(Expression):
    """Function call expression"""
    name: str
    arguments: List[Expression]