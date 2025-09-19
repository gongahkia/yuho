"""
Semantic Analyzer for Yuho language
Performs type checking, scope analysis, and semantic validation
"""

from typing import Dict, List, Set, Optional, Any
from .ast_nodes import *

class SemanticError(Exception):
    """Exception raised for semantic analysis errors"""
    pass

class SymbolTable:
    """Symbol table for tracking variable and type declarations"""

    def __init__(self, parent: Optional['SymbolTable'] = None):
        self.parent = parent
        self.symbols: Dict[str, Any] = {}
        self.types: Dict[str, StructDefinition] = {}

    def define(self, name: str, symbol: Any):
        """Define a symbol in current scope"""
        if name in self.symbols:
            raise SemanticError(f"Symbol '{name}' already defined in current scope")
        self.symbols[name] = symbol

    def define_type(self, name: str, struct_def: StructDefinition):
        """Define a struct type"""
        if name in self.types:
            raise SemanticError(f"Type '{name}' already defined")
        self.types[name] = struct_def

    def lookup(self, name: str) -> Optional[Any]:
        """Look up a symbol in current or parent scopes"""
        if name in self.symbols:
            return self.symbols[name]
        elif self.parent:
            return self.parent.lookup(name)
        return None

    def lookup_type(self, name: str) -> Optional[StructDefinition]:
        """Look up a type definition"""
        if name in self.types:
            return self.types[name]
        elif self.parent:
            return self.parent.lookup_type(name)
        return None

class SemanticAnalyzer:
    """Semantic analyzer for Yuho programs"""

    def __init__(self):
        self.global_scope = SymbolTable()
        self.current_scope = self.global_scope
        self.errors: List[str] = []
        self.imported_modules: Dict[str, Dict[str, Any]] = {}

    def analyze(self, program: Program) -> List[str]:
        """
        Analyze a Yuho program for semantic correctness

        Args:
            program: Program AST node

        Returns:
            List of error messages (empty if no errors)
        """
        self.errors = []

        try:
            for statement in program.statements:
                self.analyze_statement(statement)
        except SemanticError as e:
            self.errors.append(str(e))

        return self.errors

    def analyze_statement(self, stmt: Statement):
        """Analyze a statement"""
        if isinstance(stmt, ImportStatement):
            self.analyze_import(stmt)
        elif isinstance(stmt, Declaration):
            self.analyze_declaration(stmt)
        elif isinstance(stmt, Assignment):
            self.analyze_assignment(stmt)
        elif isinstance(stmt, StructDefinition):
            self.analyze_struct_definition(stmt)
        elif isinstance(stmt, FunctionDefinition):
            self.analyze_function_definition(stmt)
        elif isinstance(stmt, MatchCase):
            self.analyze_match_case(stmt)
        elif isinstance(stmt, PassStatement):
            pass  # No analysis needed for pass

    def analyze_import(self, stmt: ImportStatement):
        """Analyze import statement"""
        # For now, just record the import
        # In a full implementation, this would load and validate the module
        if stmt.module_name not in self.imported_modules:
            self.imported_modules[stmt.module_name] = {}

        # Add the imported struct to the type table
        qualified_name = f"{stmt.module_name}.{stmt.struct_name}"
        # This would normally load from the actual module file
        self.imported_modules[stmt.module_name][stmt.struct_name] = qualified_name

    def analyze_declaration(self, stmt: Declaration):
        """Analyze variable declaration"""
        # Check if type exists
        self.validate_type(stmt.type_node)

        # Check initial value if provided
        if stmt.value:
            value_type = self.analyze_expression(stmt.value)
            declared_type = self.get_type_from_node(stmt.type_node)

            if not self.types_compatible(declared_type, value_type):
                raise SemanticError(
                    f"Type mismatch in declaration of '{stmt.name}': "
                    f"declared as {declared_type}, but assigned {value_type}"
                )

        # Add to symbol table
        self.current_scope.define(stmt.name, stmt)

    def analyze_assignment(self, stmt: Assignment):
        """Analyze assignment statement"""
        # Check if variable exists
        symbol = self.current_scope.lookup(stmt.name)
        if not symbol:
            raise SemanticError(f"Undefined variable '{stmt.name}'")

        # Check type compatibility
        if isinstance(symbol, Declaration):
            declared_type = self.get_type_from_node(symbol.type_node)
            assigned_type = self.analyze_expression(stmt.value)

            if not self.types_compatible(declared_type, assigned_type):
                raise SemanticError(
                    f"Type mismatch in assignment to '{stmt.name}': "
                    f"expected {declared_type}, got {assigned_type}"
                )

    def analyze_struct_definition(self, stmt: StructDefinition):
        """Analyze struct definition"""
        # Check for duplicate member names
        member_names = set()
        for member in stmt.members:
            if member.name in member_names:
                raise SemanticError(
                    f"Duplicate member '{member.name}' in struct '{stmt.name}'"
                )
            member_names.add(member.name)

            # Validate member type
            self.validate_type(member.type_node)

        # Add to type table
        self.current_scope.define_type(stmt.name, stmt)

    def analyze_function_definition(self, stmt: FunctionDefinition):
        """Analyze function definition"""
        # Create new scope for function
        function_scope = SymbolTable(parent=self.current_scope)
        old_scope = self.current_scope
        self.current_scope = function_scope

        try:
            # Add parameters to scope
            param_names = set()
            for param in stmt.parameters:
                if param.name in param_names:
                    raise SemanticError(
                        f"Duplicate parameter '{param.name}' in function '{stmt.name}'"
                    )
                param_names.add(param.name)

                self.validate_type(param.type_node)
                self.current_scope.define(param.name, param)

            # Validate return type
            self.validate_type(stmt.return_type)

            # Analyze function body
            for body_stmt in stmt.body:
                self.analyze_statement(body_stmt)

        finally:
            self.current_scope = old_scope

        # Add function to symbol table
        self.current_scope.define(stmt.name, stmt)

    def analyze_match_case(self, stmt: MatchCase):
        """Analyze match-case statement"""
        if stmt.expression:
            expr_type = self.analyze_expression(stmt.expression)

        for case in stmt.cases:
            if case.condition:
                self.analyze_expression(case.condition)
            self.analyze_expression(case.consequence)

    def analyze_expression(self, expr: Expression) -> str:
        """Analyze expression and return its type"""
        if isinstance(expr, Literal):
            return expr.literal_type.value

        elif isinstance(expr, Identifier):
            symbol = self.current_scope.lookup(expr.name)
            if not symbol:
                raise SemanticError(f"Undefined identifier '{expr.name}'")

            if isinstance(symbol, Declaration):
                return self.get_type_from_node(symbol.type_node)
            elif isinstance(symbol, Parameter):
                return self.get_type_from_node(symbol.type_node)

        elif isinstance(expr, BinaryOperation):
            left_type = self.analyze_expression(expr.left)
            right_type = self.analyze_expression(expr.right)

            # Type checking for binary operations
            if expr.operator in [Operator.PLUS, Operator.MINUS, Operator.MULT, Operator.DIV]:
                if left_type in ["int", "float"] and right_type in ["int", "float"]:
                    return "float" if "float" in [left_type, right_type] else "int"
                else:
                    raise SemanticError(
                        f"Invalid operand types for {expr.operator.value}: {left_type}, {right_type}"
                    )

            elif expr.operator in [Operator.GT, Operator.LT, Operator.EQUAL, Operator.NOTEQUAL]:
                if self.types_compatible(left_type, right_type):
                    return "bool"
                else:
                    raise SemanticError(
                        f"Cannot compare {left_type} with {right_type}"
                    )

            elif expr.operator in [Operator.AND, Operator.OR]:
                if left_type == "bool" and right_type == "bool":
                    return "bool"
                else:
                    raise SemanticError(
                        f"Logical operators require bool operands, got {left_type}, {right_type}"
                    )

        elif isinstance(expr, FunctionCall):
            func_symbol = self.current_scope.lookup(expr.name)
            if not func_symbol:
                raise SemanticError(f"Undefined function '{expr.name}'")

            if isinstance(func_symbol, FunctionDefinition):
                # Check argument types
                if len(expr.arguments) != len(func_symbol.parameters):
                    raise SemanticError(
                        f"Function '{expr.name}' expects {len(func_symbol.parameters)} "
                        f"arguments, got {len(expr.arguments)}"
                    )

                for arg, param in zip(expr.arguments, func_symbol.parameters):
                    arg_type = self.analyze_expression(arg)
                    param_type = self.get_type_from_node(param.type_node)

                    if not self.types_compatible(arg_type, param_type):
                        raise SemanticError(
                            f"Argument type mismatch in call to '{expr.name}': "
                            f"expected {param_type}, got {arg_type}"
                        )

                return self.get_type_from_node(func_symbol.return_type)

        return "unknown"

    def validate_type(self, type_node: TypeNode):
        """Validate that a type exists"""
        if isinstance(type_node.type_name, YuhoType):
            return  # Built-in types are always valid

        type_name = type_node.type_name
        if not self.current_scope.lookup_type(type_name):
            # Check if it's a qualified type from imports
            if "." not in type_name:
                raise SemanticError(f"Undefined type '{type_name}'")

    def get_type_from_node(self, type_node: TypeNode) -> str:
        """Get type string from TypeNode"""
        if isinstance(type_node.type_name, YuhoType):
            return type_node.type_name.value
        return str(type_node.type_name)

    def types_compatible(self, type1: str, type2: str) -> bool:
        """Check if two types are compatible"""
        if type1 == type2:
            return True

        # Allow int to be used where float is expected
        if type1 == "float" and type2 == "int":
            return True

        return False