"""
Yuho AST (Abstract Syntax Tree) module.

This module provides immutable AST node classes for representing
parsed Yuho source code, along with Visitor and Transformer base
classes for AST traversal and transformation.
"""

from yuho.ast.nodes import (
    # Base
    ASTNode,
    # Literals
    IntLit,
    FloatLit,
    BoolLit,
    StringLit,
    MoneyNode,
    PercentNode,
    DateNode,
    DurationNode,
    # Expressions
    IdentifierNode,
    FieldAccessNode,
    IndexAccessNode,
    FunctionCallNode,
    BinaryExprNode,
    UnaryExprNode,
    PassExprNode,
    # Patterns
    PatternNode,
    WildcardPattern,
    LiteralPattern,
    BindingPattern,
    StructPattern,
    FieldPattern,
    # Match
    MatchArm,
    MatchExprNode,
    # Structs
    FieldDef,
    StructDefNode,
    FieldAssignment,
    StructLiteralNode,
    # Functions
    ParamDef,
    FunctionDefNode,
    # Statements
    VariableDecl,
    AssignmentStmt,
    ReturnStmt,
    PassStmt,
    ExpressionStmt,
    Block,
    # Statutes
    DefinitionEntry,
    ElementNode,
    PenaltyNode,
    IllustrationNode,
    StatuteNode,
    # Imports
    ImportNode,
    # Module
    ModuleNode,
    # Types
    TypeNode,
    BuiltinType,
    NamedType,
    GenericType,
    OptionalType,
    ArrayType,
    # Currency
    Currency,
)

from yuho.ast.visitor import Visitor
from yuho.ast.transformer import Transformer
from yuho.ast.builder import ASTBuilder
from yuho.ast.exhaustiveness import (
    ExhaustivenessChecker,
    ExhaustivenessError,
    ExhaustivenessResult,
    check_exhaustiveness,
)

__all__ = [
    # Base
    "ASTNode",
    # Literals
    "IntLit",
    "FloatLit",
    "BoolLit",
    "StringLit",
    "MoneyNode",
    "PercentNode",
    "DateNode",
    "DurationNode",
    # Expressions
    "IdentifierNode",
    "FieldAccessNode",
    "IndexAccessNode",
    "FunctionCallNode",
    "BinaryExprNode",
    "UnaryExprNode",
    "PassExprNode",
    # Patterns
    "PatternNode",
    "WildcardPattern",
    "LiteralPattern",
    "BindingPattern",
    "StructPattern",
    "FieldPattern",
    # Match
    "MatchArm",
    "MatchExprNode",
    # Structs
    "FieldDef",
    "StructDefNode",
    "FieldAssignment",
    "StructLiteralNode",
    # Functions
    "ParamDef",
    "FunctionDefNode",
    # Statements
    "VariableDecl",
    "AssignmentStmt",
    "ReturnStmt",
    "PassStmt",
    "ExpressionStmt",
    "Block",
    # Statutes
    "DefinitionEntry",
    "ElementNode",
    "PenaltyNode",
    "IllustrationNode",
    "StatuteNode",
    # Imports
    "ImportNode",
    # Module
    "ModuleNode",
    # Types
    "TypeNode",
    "BuiltinType",
    "NamedType",
    "GenericType",
    "OptionalType",
    "ArrayType",
    # Currency
    "Currency",
    # Traversal
    "Visitor",
    "Transformer",
    "ASTBuilder",
    # Analysis
    "ExhaustivenessChecker",
    "ExhaustivenessError",
    "ExhaustivenessResult",
    "check_exhaustiveness",
]
