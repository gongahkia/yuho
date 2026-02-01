"""
Scope analysis visitor for Yuho AST.

Builds symbol tables and resolves references:
- Variable declarations and their scopes
- Function definitions and their signatures
- Struct definitions and their members
- Undeclared identifier detection
- Duplicate declaration detection
"""

from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum, auto

from yuho.ast import nodes
from yuho.ast.visitor import Visitor


class SymbolKind(Enum):
    """Type of symbol in the symbol table."""
    
    VARIABLE = auto()
    FUNCTION = auto()
    STRUCT = auto()
    PARAMETER = auto()
    FIELD = auto()
    ENUM_VARIANT = auto()


@dataclass
class Symbol:
    """Represents a symbol in the symbol table."""
    
    name: str
    kind: SymbolKind
    declaration_node: Optional[nodes.ASTNode] = None
    type_annotation: Optional[str] = None
    scope_level: int = 0
    line: int = 0
    column: int = 0
    
    # For structs: field names
    members: Dict[str, "Symbol"] = field(default_factory=dict)


@dataclass
class Scope:
    """Represents a lexical scope with its own symbol table."""
    
    name: str
    parent: Optional["Scope"] = None
    symbols: Dict[str, Symbol] = field(default_factory=dict)
    children: List["Scope"] = field(default_factory=list)
    level: int = 0
    
    def define(self, symbol: Symbol) -> Optional[str]:
        """
        Define a symbol in this scope.
        Returns error message if duplicate, None if success.
        """
        if symbol.name in self.symbols:
            existing = self.symbols[symbol.name]
            return f"Symbol '{symbol.name}' already declared at line {existing.line}"
        
        symbol.scope_level = self.level
        self.symbols[symbol.name] = symbol
        return None
    
    def lookup(self, name: str, recursive: bool = True) -> Optional[Symbol]:
        """
        Look up a symbol, optionally searching parent scopes.
        """
        if name in self.symbols:
            return self.symbols[name]
        if recursive and self.parent:
            return self.parent.lookup(name, recursive=True)
        return None
    
    def lookup_local(self, name: str) -> Optional[Symbol]:
        """Look up a symbol only in this scope."""
        return self.symbols.get(name)
    
    def all_symbols(self) -> Dict[str, Symbol]:
        """Get all symbols visible from this scope."""
        result: Dict[str, Symbol] = {}
        if self.parent:
            result.update(self.parent.all_symbols())
        result.update(self.symbols)
        return result


@dataclass
class ScopeError:
    """Represents a scope-related error."""
    
    message: str
    line: int = 0
    column: int = 0
    severity: str = "error"
    
    def __str__(self) -> str:
        loc = f"{self.line}:{self.column}" if self.line else ""
        return f"[{self.severity}] {loc} {self.message}"


@dataclass
class ScopeAnalysisResult:
    """Result of scope analysis."""
    
    # Root scope (module level)
    root_scope: Scope = field(default_factory=lambda: Scope(name="module", level=0))
    
    # All errors found
    errors: List[ScopeError] = field(default_factory=list)
    
    # All warnings found
    warnings: List[ScopeError] = field(default_factory=list)
    
    # Map from node id to its resolved symbol
    references: Dict[int, Symbol] = field(default_factory=dict)
    
    # All scopes created
    all_scopes: List[Scope] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def is_valid(self) -> bool:
        return not self.has_errors
    
    def add_error(
        self,
        message: str,
        node: Optional[nodes.ASTNode] = None,
        severity: str = "error",
    ) -> None:
        """Add a scope error."""
        line = 0
        column = 0
        
        if node and node.source_location:
            line = node.source_location.start_line
            column = node.source_location.start_column
        
        error = ScopeError(
            message=message,
            line=line,
            column=column,
            severity=severity,
        )
        
        if severity == "error":
            self.errors.append(error)
        else:
            self.warnings.append(error)
    
    def get_symbol(self, node: nodes.ASTNode) -> Optional[Symbol]:
        """Get the symbol that a node references."""
        return self.references.get(id(node))
    
    def set_reference(self, node: nodes.ASTNode, symbol: Symbol) -> None:
        """Set the symbol that a node references."""
        self.references[id(node)] = symbol


class ScopeAnalysisVisitor(Visitor):
    """
    Visitor that builds symbol tables and resolves references.
    
    Usage:
        visitor = ScopeAnalysisVisitor()
        module.accept(visitor)
        result = visitor.result
        
        if result.has_errors:
            for error in result.errors:
                print(error)
        
        # Get symbol for any identifier
        symbol = result.get_symbol(some_identifier_node)
    """
    
    def __init__(self) -> None:
        self.result = ScopeAnalysisResult()
        self._current_scope = self.result.root_scope
        self.result.all_scopes.append(self._current_scope)
    
    def _push_scope(self, name: str) -> Scope:
        """Create a new child scope and enter it."""
        new_scope = Scope(
            name=name,
            parent=self._current_scope,
            level=self._current_scope.level + 1,
        )
        self._current_scope.children.append(new_scope)
        self._current_scope = new_scope
        self.result.all_scopes.append(new_scope)
        return new_scope
    
    def _pop_scope(self) -> None:
        """Exit the current scope."""
        if self._current_scope.parent:
            self._current_scope = self._current_scope.parent
    
    def _define_symbol(
        self,
        name: str,
        kind: SymbolKind,
        node: Optional[nodes.ASTNode] = None,
        type_annotation: Optional[str] = None,
    ) -> Symbol:
        """Define a new symbol in the current scope."""
        line = 0
        column = 0
        if node and node.source_location:
            line = node.source_location.start_line
            column = node.source_location.start_column
        
        symbol = Symbol(
            name=name,
            kind=kind,
            declaration_node=node,
            type_annotation=type_annotation,
            line=line,
            column=column,
        )
        
        error = self._current_scope.define(symbol)
        if error:
            self.result.add_error(error, node)
        
        return symbol
    
    def _resolve_identifier(self, name: str, node: nodes.ASTNode) -> Optional[Symbol]:
        """Resolve an identifier to its symbol."""
        symbol = self._current_scope.lookup(name)
        if symbol:
            self.result.set_reference(node, symbol)
        return symbol
    
    # =========================================================================
    # Struct definitions
    # =========================================================================
    
    def visit_struct_def(self, node: nodes.StructDefNode) -> Any:
        """Define struct and its fields."""
        # Define struct in current scope
        struct_symbol = self._define_symbol(
            name=node.name,
            kind=SymbolKind.STRUCT,
            node=node,
        )
        
        # Create scope for struct members
        self._push_scope(f"struct_{node.name}")
        
        # Define fields
        for field_def in node.fields:
            field_type = None
            if field_def.type_annotation:
                field_type = self._type_to_string(field_def.type_annotation)
            
            field_symbol = self._define_symbol(
                name=field_def.name,
                kind=SymbolKind.FIELD if field_type else SymbolKind.ENUM_VARIANT,
                node=field_def,
                type_annotation=field_type,
            )
            struct_symbol.members[field_def.name] = field_symbol
        
        self._pop_scope()
        return self.generic_visit(node)
    
    def _type_to_string(self, type_node: nodes.TypeNode) -> str:
        """Convert type node to string representation."""
        if isinstance(type_node, nodes.BuiltinType):
            return type_node.name
        elif isinstance(type_node, nodes.NamedType):
            return type_node.name
        elif isinstance(type_node, nodes.OptionalType):
            return f"{self._type_to_string(type_node.inner)}?"
        elif isinstance(type_node, nodes.ArrayType):
            return f"[{self._type_to_string(type_node.element_type)}]"
        elif isinstance(type_node, nodes.GenericType):
            return type_node.base
        return "unknown"
    
    # =========================================================================
    # Function definitions
    # =========================================================================
    
    def visit_function_def(self, node: nodes.FunctionDefNode) -> Any:
        """Define function and its parameters."""
        return_type = None
        if node.return_type:
            return_type = self._type_to_string(node.return_type)
        
        # Define function in current scope
        self._define_symbol(
            name=node.name,
            kind=SymbolKind.FUNCTION,
            node=node,
            type_annotation=return_type,
        )
        
        # Create scope for function body
        self._push_scope(f"function_{node.name}")
        
        # Define parameters
        for param in node.parameters:
            param_type = None
            if param.type_annotation:
                param_type = self._type_to_string(param.type_annotation)
            
            self._define_symbol(
                name=param.name,
                kind=SymbolKind.PARAMETER,
                node=param,
                type_annotation=param_type,
            )
        
        # Visit body
        if node.body:
            self.visit(node.body)
        
        self._pop_scope()
        return None  # Don't call generic_visit to avoid re-visiting
    
    # =========================================================================
    # Variable declarations
    # =========================================================================
    
    def visit_variable_decl(self, node: nodes.VariableDecl) -> Any:
        """Define variable in current scope."""
        var_type = None
        if node.type_annotation:
            var_type = self._type_to_string(node.type_annotation)
        
        self._define_symbol(
            name=node.name,
            kind=SymbolKind.VARIABLE,
            node=node,
            type_annotation=var_type,
        )
        
        # Visit initializer
        if node.value:
            self.visit(node.value)
        
        return self.generic_visit(node)
    
    # =========================================================================
    # Identifier references
    # =========================================================================
    
    def visit_identifier(self, node: nodes.IdentifierNode) -> Any:
        """Resolve identifier to its declaration."""
        symbol = self._resolve_identifier(node.name, node)
        if not symbol:
            # Check if it's a builtin or known constant
            if node.name not in ("TRUE", "FALSE", "pass"):
                self.result.add_error(
                    f"Undeclared identifier '{node.name}'",
                    node,
                )
        return self.generic_visit(node)
    
    def visit_field_access(self, node: nodes.FieldAccessNode) -> Any:
        """Resolve field access, handling enum variant access."""
        # Visit base expression
        self.visit(node.base)
        
        # Try to resolve as enum type.variant
        if isinstance(node.base, nodes.IdentifierNode):
            base_symbol = self.result.get_symbol(node.base)
            if base_symbol and base_symbol.kind == SymbolKind.STRUCT:
                # Check if field exists as member
                if node.field_name in base_symbol.members:
                    field_symbol = base_symbol.members[node.field_name]
                    self.result.set_reference(node, field_symbol)
                # It's an enum variant access - we trust it exists
        
        return self.generic_visit(node)
    
    # =========================================================================
    # Match expression
    # =========================================================================
    
    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        """Visit match expression, creating scope for each arm."""
        if node.scrutinee:
            self.visit(node.scrutinee)
        
        for arm in node.arms:
            self.visit(arm)
        
        return None
    
    def visit_match_arm(self, node: nodes.MatchArm) -> Any:
        """Create scope for match arm bindings."""
        # Create scope for arm (for binding patterns)
        self._push_scope("match_arm")
        
        # Visit pattern (may introduce bindings)
        self.visit(node.pattern)
        
        # Visit guard
        if node.guard:
            self.visit(node.guard)
        
        # Visit body
        self.visit(node.body)
        
        self._pop_scope()
        return None
    
    def visit_binding_pattern(self, node: nodes.BindingPattern) -> Any:
        """Define binding pattern as variable in current scope."""
        # Binding patterns introduce variables
        self._define_symbol(
            name=node.name,
            kind=SymbolKind.VARIABLE,
            node=node,
        )
        return self.generic_visit(node)
    
    # =========================================================================
    # Block statements
    # =========================================================================
    
    def visit_block(self, node: nodes.Block) -> Any:
        """Create new scope for block."""
        self._push_scope("block")
        
        for stmt in node.statements:
            self.visit(stmt)
        
        self._pop_scope()
        return None
    
    # =========================================================================
    # Statute blocks
    # =========================================================================
    
    def visit_statute(self, node: nodes.StatuteNode) -> Any:
        """Create scope for statute definitions."""
        scope_name = f"statute_{node.section_number}"
        self._push_scope(scope_name)
        
        # Visit all members
        for member in node.definitions:
            self.visit(member)
        for member in node.elements:
            self.visit(member)
        
        self._pop_scope()
        return None
    
    # =========================================================================
    # Module entry point
    # =========================================================================
    
    def visit_module(self, node: nodes.ModuleNode) -> Any:
        """Entry point: analyze all declarations."""
        # First pass: collect struct and function definitions
        for decl in node.declarations:
            if isinstance(decl, nodes.StructDefNode):
                self.visit_struct_def(decl)
            elif isinstance(decl, nodes.FunctionDefNode):
                # Just define the function signature
                return_type = None
                if decl.return_type:
                    return_type = self._type_to_string(decl.return_type)
                self._define_symbol(
                    name=decl.name,
                    kind=SymbolKind.FUNCTION,
                    node=decl,
                    type_annotation=return_type,
                )
        
        # Second pass: full traversal
        for decl in node.declarations:
            if isinstance(decl, nodes.StructDefNode):
                continue  # Already processed
            self.visit(decl)
        
        return self.result
