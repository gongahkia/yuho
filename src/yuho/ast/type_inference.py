"""
Type inference visitor for Yuho AST.

Annotates each expression node with its inferred type based on:
- Literal types (direct from node type)
- Variable types (from symbol table)
- Operator result types (from operand types)
- Function return types (from function signatures)
- Field access types (from struct definitions)
"""

from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field

from yuho.ast import nodes
from yuho.ast.visitor import Visitor


@dataclass
class TypeAnnotation:
    """Represents an inferred type annotation for a node."""
    
    type_name: str
    is_optional: bool = False
    is_array: bool = False
    element_type: Optional["TypeAnnotation"] = None
    struct_fields: Dict[str, "TypeAnnotation"] = field(default_factory=dict)
    
    def __str__(self) -> str:
        if self.is_array:
            return f"[{self.element_type}]"
        if self.is_optional:
            return f"{self.type_name}?"
        return self.type_name
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TypeAnnotation):
            return False
        return (
            self.type_name == other.type_name
            and self.is_optional == other.is_optional
            and self.is_array == other.is_array
        )


# Built-in type constants
INT_TYPE = TypeAnnotation("int")
FLOAT_TYPE = TypeAnnotation("float")
BOOL_TYPE = TypeAnnotation("bool")
STRING_TYPE = TypeAnnotation("string")
MONEY_TYPE = TypeAnnotation("money")
PERCENT_TYPE = TypeAnnotation("percent")
DATE_TYPE = TypeAnnotation("date")
DURATION_TYPE = TypeAnnotation("duration")
VOID_TYPE = TypeAnnotation("void")
PASS_TYPE = TypeAnnotation("pass")
UNKNOWN_TYPE = TypeAnnotation("unknown")


@dataclass
class TypeInferenceResult:
    """Result of type inference including all inferred types and any errors."""
    
    # Map of AST node id -> inferred type
    node_types: Dict[int, TypeAnnotation] = field(default_factory=dict)
    
    # Struct definitions found
    struct_defs: Dict[str, Dict[str, TypeAnnotation]] = field(default_factory=dict)
    
    # Function signatures found
    function_sigs: Dict[str, tuple] = field(default_factory=dict)
    
    # Variable types in scope
    variable_types: Dict[str, TypeAnnotation] = field(default_factory=dict)
    
    # Inference errors
    errors: List[str] = field(default_factory=list)
    
    def get_type(self, node: nodes.ASTNode) -> TypeAnnotation:
        """Get the inferred type for a node."""
        return self.node_types.get(id(node), UNKNOWN_TYPE)
    
    def set_type(self, node: nodes.ASTNode, type_ann: TypeAnnotation) -> None:
        """Set the inferred type for a node."""
        self.node_types[id(node)] = type_ann


class TypeInferenceVisitor(Visitor):
    """
    Visitor that infers and annotates types for all expression nodes.
    
    Usage:
        visitor = TypeInferenceVisitor()
        module.accept(visitor)
        result = visitor.result
        
        # Get type of any expression
        expr_type = result.get_type(some_expr_node)
    """
    
    def __init__(self) -> None:
        self.result = TypeInferenceResult()
        self._current_scope: Dict[str, TypeAnnotation] = {}
    
    def _type_node_to_annotation(self, type_node: nodes.TypeNode) -> TypeAnnotation:
        """Convert a TypeNode to a TypeAnnotation."""
        if isinstance(type_node, nodes.BuiltinType):
            return TypeAnnotation(type_node.name)
        elif isinstance(type_node, nodes.NamedType):
            return TypeAnnotation(type_node.name)
        elif isinstance(type_node, nodes.OptionalType):
            inner = self._type_node_to_annotation(type_node.inner)
            return TypeAnnotation(inner.type_name, is_optional=True)
        elif isinstance(type_node, nodes.ArrayType):
            elem = self._type_node_to_annotation(type_node.element_type)
            return TypeAnnotation("array", is_array=True, element_type=elem)
        elif isinstance(type_node, nodes.GenericType):
            # Handle generic types like List<T>
            return TypeAnnotation(type_node.base)
        return UNKNOWN_TYPE
    
    # =========================================================================
    # Literal nodes - direct type inference
    # =========================================================================
    
    def visit_int_lit(self, node: nodes.IntLit) -> Any:
        self.result.set_type(node, INT_TYPE)
        return INT_TYPE
    
    def visit_float_lit(self, node: nodes.FloatLit) -> Any:
        self.result.set_type(node, FLOAT_TYPE)
        return FLOAT_TYPE
    
    def visit_bool_lit(self, node: nodes.BoolLit) -> Any:
        self.result.set_type(node, BOOL_TYPE)
        return BOOL_TYPE
    
    def visit_string_lit(self, node: nodes.StringLit) -> Any:
        self.result.set_type(node, STRING_TYPE)
        return STRING_TYPE
    
    def visit_money(self, node: nodes.MoneyNode) -> Any:
        self.result.set_type(node, MONEY_TYPE)
        return MONEY_TYPE
    
    def visit_percent(self, node: nodes.PercentNode) -> Any:
        self.result.set_type(node, PERCENT_TYPE)
        return PERCENT_TYPE
    
    def visit_date(self, node: nodes.DateNode) -> Any:
        self.result.set_type(node, DATE_TYPE)
        return DATE_TYPE
    
    def visit_duration(self, node: nodes.DurationNode) -> Any:
        self.result.set_type(node, DURATION_TYPE)
        return DURATION_TYPE
    
    def visit_pass_expr(self, node: nodes.PassExprNode) -> Any:
        self.result.set_type(node, PASS_TYPE)
        return PASS_TYPE
    
    # =========================================================================
    # Expression nodes
    # =========================================================================
    
    def visit_identifier(self, node: nodes.IdentifierNode) -> Any:
        """Look up identifier in current scope."""
        name = node.name
        if name in self._current_scope:
            inferred_type = self._current_scope[name]
        elif name in self.result.variable_types:
            inferred_type = self.result.variable_types[name]
        elif name in self.result.struct_defs:
            # It's a struct type reference
            inferred_type = TypeAnnotation(name)
        else:
            inferred_type = UNKNOWN_TYPE
            
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    def visit_field_access(self, node: nodes.FieldAccessNode) -> Any:
        """Infer type from struct field access."""
        base_type = self.visit(node.base)
        field_name = node.field_name
        
        # Check if base is a known struct type
        if base_type.type_name in self.result.struct_defs:
            struct_fields = self.result.struct_defs[base_type.type_name]
            if field_name in struct_fields:
                inferred_type = struct_fields[field_name]
            else:
                # Could be enum variant access
                inferred_type = TypeAnnotation(base_type.type_name)
        else:
            # Enum variant access pattern: EnumType.Variant
            inferred_type = TypeAnnotation(base_type.type_name)
        
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    def visit_index_access(self, node: nodes.IndexAccessNode) -> Any:
        """Infer type from array indexing."""
        base_type = self.visit(node.base)
        self.visit(node.index)
        
        if base_type.is_array and base_type.element_type:
            inferred_type = base_type.element_type
        else:
            inferred_type = UNKNOWN_TYPE
            
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    def visit_binary_expr(self, node: nodes.BinaryExprNode) -> Any:
        """Infer type from binary expression based on operator and operands."""
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        op = node.operator
        
        # Comparison operators always return bool
        if op in ("==", "!=", "<", ">", "<=", ">="):
            inferred_type = BOOL_TYPE
        # Logical operators return bool
        elif op in ("&&", "||", "and", "or"):
            inferred_type = BOOL_TYPE
        # Arithmetic operators: result type depends on operands
        elif op in ("+", "-", "*", "/", "%"):
            if left_type == FLOAT_TYPE or right_type == FLOAT_TYPE:
                inferred_type = FLOAT_TYPE
            elif left_type == MONEY_TYPE or right_type == MONEY_TYPE:
                inferred_type = MONEY_TYPE
            elif left_type == DURATION_TYPE or right_type == DURATION_TYPE:
                inferred_type = DURATION_TYPE
            else:
                inferred_type = INT_TYPE
        else:
            inferred_type = UNKNOWN_TYPE
        
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    def visit_unary_expr(self, node: nodes.UnaryExprNode) -> Any:
        """Infer type from unary expression."""
        operand_type = self.visit(node.operand)
        
        op = node.operator
        if op in ("!", "not"):
            inferred_type = BOOL_TYPE
        elif op == "-":
            inferred_type = operand_type  # Negation preserves numeric type
        else:
            inferred_type = operand_type
            
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    def visit_function_call(self, node: nodes.FunctionCallNode) -> Any:
        """Infer return type from function signature."""
        # Visit arguments
        for arg in node.arguments:
            self.visit(arg)
        
        # Look up function return type
        func_name = node.callee if isinstance(node.callee, str) else getattr(node.callee, "name", "")
        if func_name in self.result.function_sigs:
            _, return_type = self.result.function_sigs[func_name]
            inferred_type = return_type
        else:
            inferred_type = UNKNOWN_TYPE
            
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    # =========================================================================
    # Match expression
    # =========================================================================
    
    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        """Infer type from match expression arms."""
        if node.scrutinee:
            self.visit(node.scrutinee)
        
        arm_types: List[TypeAnnotation] = []
        for arm in node.arms:
            arm_type = self.visit(arm)
            if arm_type:
                arm_types.append(arm_type)
        
        # All arms should have the same type; use first non-unknown
        if arm_types:
            inferred_type = next(
                (t for t in arm_types if t != UNKNOWN_TYPE and t != PASS_TYPE),
                arm_types[0]
            )
        else:
            inferred_type = UNKNOWN_TYPE
            
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    def visit_match_arm(self, node: nodes.MatchArm) -> Any:
        """Infer type from match arm body."""
        self.visit(node.pattern)
        if node.guard:
            self.visit(node.guard)
        body_type = self.visit(node.body)
        self.result.set_type(node, body_type)
        return body_type
    
    # =========================================================================
    # Struct definition and literal
    # =========================================================================
    
    def visit_struct_def(self, node: nodes.StructDefNode) -> Any:
        """Record struct field types."""
        fields: Dict[str, TypeAnnotation] = {}
        for field_def in node.fields:
            if field_def.type_annotation:
                fields[field_def.name] = self._type_node_to_annotation(field_def.type_annotation)
            else:
                # Enum variant (no type)
                fields[field_def.name] = TypeAnnotation(node.name)
        
        self.result.struct_defs[node.name] = fields
        return self.generic_visit(node)
    
    def visit_struct_literal(self, node: nodes.StructLiteralNode) -> Any:
        """Infer type from struct literal type name."""
        if node.type_name:
            inferred_type = TypeAnnotation(node.type_name)
        else:
            inferred_type = UNKNOWN_TYPE
        
        # Visit field assignments
        for field_assign in node.field_assignments:
            self.visit(field_assign)
        
        self.result.set_type(node, inferred_type)
        return inferred_type
    
    # =========================================================================
    # Variable and function definitions
    # =========================================================================
    
    def visit_variable_decl(self, node: nodes.VariableDecl) -> Any:
        """Record variable type in scope."""
        if node.type_annotation:
            var_type = self._type_node_to_annotation(node.type_annotation)
        elif node.value:
            var_type = self.visit(node.value)
        else:
            var_type = UNKNOWN_TYPE
        
        self._current_scope[node.name] = var_type
        self.result.variable_types[node.name] = var_type
        self.result.set_type(node, var_type)
        return var_type
    
    def visit_function_def(self, node: nodes.FunctionDefNode) -> Any:
        """Record function signature and infer body types."""
        # Record return type
        if node.return_type:
            return_type = self._type_node_to_annotation(node.return_type)
        else:
            return_type = VOID_TYPE
        
        # Record parameter types
        param_types: List[TypeAnnotation] = []
        for param in node.parameters:
            if param.type_annotation:
                p_type = self._type_node_to_annotation(param.type_annotation)
                param_types.append(p_type)
                self._current_scope[param.name] = p_type
        
        self.result.function_sigs[node.name] = (param_types, return_type)
        
        # Visit body
        if node.body:
            self.visit(node.body)
        
        self.result.set_type(node, return_type)
        return return_type
    
    # =========================================================================
    # Pattern nodes
    # =========================================================================
    
    def visit_wildcard_pattern(self, node: nodes.WildcardPattern) -> Any:
        self.result.set_type(node, UNKNOWN_TYPE)
        return UNKNOWN_TYPE
    
    def visit_literal_pattern(self, node: nodes.LiteralPattern) -> Any:
        literal_type = self.visit(node.literal)
        self.result.set_type(node, literal_type)
        return literal_type
    
    def visit_binding_pattern(self, node: nodes.BindingPattern) -> Any:
        self.result.set_type(node, UNKNOWN_TYPE)
        return UNKNOWN_TYPE
    
    # =========================================================================
    # Module entry point
    # =========================================================================
    
    def visit_module(self, node: nodes.ModuleNode) -> Any:
        """Entry point: visit all declarations in module."""
        # First pass: collect struct definitions
        for decl in node.declarations:
            if isinstance(decl, nodes.StructDefNode):
                self.visit_struct_def(decl)
            elif isinstance(decl, nodes.FunctionDefNode):
                # Just record signature
                if decl.return_type:
                    return_type = self._type_node_to_annotation(decl.return_type)
                else:
                    return_type = VOID_TYPE
                self.result.function_sigs[decl.name] = ([], return_type)
        
        # Second pass: full traversal
        for decl in node.declarations:
            self.visit(decl)
        
        return self.result
