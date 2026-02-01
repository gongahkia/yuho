"""
Exhaustiveness checker for match expressions using pattern matrix algorithm.

Validates that match expressions cover all possible cases based on the
scrutinee type. Uses the pattern matrix algorithm as described in
"Warnings for pattern matching" (Maranget, 2007).
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Set, Dict, Tuple, Any, FrozenSet

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.ast.type_inference import (
    TypeAnnotation,
    TypeInferenceResult,
    BOOL_TYPE,
    INT_TYPE,
    STRING_TYPE,
    UNKNOWN_TYPE,
)


class PatternKind(Enum):
    """Classification of pattern types for exhaustiveness analysis."""
    
    WILDCARD = auto()     # _ or binding pattern
    LITERAL = auto()      # Specific value (bool, int, string)
    STRUCT = auto()       # Struct/enum destructuring
    GUARD = auto()        # Conditional pattern (treated as partial)


@dataclass(frozen=True)
class AbstractPattern:
    """
    Abstract representation of a pattern for exhaustiveness analysis.
    
    Patterns are simplified to focus on exhaustiveness:
    - Wildcards and bindings are equivalent (match anything)
    - Literals must be tracked for finite types (bool, enum)
    - Struct patterns track constructor and field patterns
    """
    
    kind: PatternKind
    value: Any = None  # Literal value or struct name
    children: Tuple["AbstractPattern", ...] = ()
    has_guard: bool = False
    
    def is_wildcard(self) -> bool:
        """True if this pattern matches all values."""
        return self.kind == PatternKind.WILDCARD and not self.has_guard
    
    def covers(self, other: "AbstractPattern") -> bool:
        """Check if this pattern covers another pattern."""
        if self.is_wildcard():
            return True
        if other.is_wildcard():
            return False
        if self.kind != other.kind:
            return False
        if self.value != other.value:
            return False
        if len(self.children) != len(other.children):
            return False
        return all(c1.covers(c2) for c1, c2 in zip(self.children, other.children))


@dataclass
class PatternRow:
    """Row in the pattern matrix representing one match arm."""
    
    patterns: List[AbstractPattern]
    arm_index: int
    
    def is_empty(self) -> bool:
        return len(self.patterns) == 0


@dataclass
class PatternMatrix:
    """
    Matrix of patterns for exhaustiveness checking.
    
    Rows represent match arms, columns represent pattern positions.
    The algorithm works by specialization: selecting a column and
    splitting the matrix based on constructors that appear there.
    """
    
    rows: List[PatternRow]
    column_types: List[TypeAnnotation] = field(default_factory=list)
    
    def is_empty(self) -> bool:
        """Matrix is empty if it has no rows."""
        return len(self.rows) == 0
    
    def has_empty_row(self) -> bool:
        """Check if matrix has a row with no patterns (matching all)."""
        return any(row.is_empty() for row in self.rows)
    
    def width(self) -> int:
        """Number of columns in the matrix."""
        return self.rows[0].patterns if self.rows else 0
    
    def specialize(self, col: int, constructor: AbstractPattern) -> "PatternMatrix":
        """
        Specialize matrix by a constructor in the given column.
        
        For each row:
        - If pattern at col is wildcard: expand to constructor's arity
        - If pattern at col matches constructor: include with children expanded
        - Otherwise: exclude row
        """
        new_rows = []
        
        for row in self.rows:
            if col >= len(row.patterns):
                continue
                
            pattern = row.patterns[col]
            
            if pattern.is_wildcard():
                # Wildcard matches constructor; expand to wildcard children
                new_patterns = (
                    row.patterns[:col] +
                    [AbstractPattern(PatternKind.WILDCARD) for _ in constructor.children] +
                    row.patterns[col + 1:]
                )
                new_rows.append(PatternRow(new_patterns, row.arm_index))
                
            elif pattern.kind == constructor.kind and pattern.value == constructor.value:
                # Same constructor; expand children
                new_patterns = (
                    row.patterns[:col] +
                    list(pattern.children) +
                    row.patterns[col + 1:]
                )
                new_rows.append(PatternRow(new_patterns, row.arm_index))
        
        return PatternMatrix(new_rows, self.column_types)
    
    def default_matrix(self, col: int) -> "PatternMatrix":
        """
        Create default matrix for patterns that don't match given constructors.
        
        Keeps only rows with wildcards at the given column.
        """
        new_rows = []
        
        for row in self.rows:
            if col >= len(row.patterns):
                continue
            
            pattern = row.patterns[col]
            
            if pattern.is_wildcard():
                new_patterns = row.patterns[:col] + row.patterns[col + 1:]
                new_rows.append(PatternRow(new_patterns, row.arm_index))
        
        return PatternMatrix(new_rows, self.column_types)


@dataclass
class ExhaustivenessResult:
    """Result of exhaustiveness checking."""
    
    is_exhaustive: bool
    missing_patterns: List[str] = field(default_factory=list)
    match_node: Optional[nodes.MatchExprNode] = None
    
    def __str__(self) -> str:
        if self.is_exhaustive:
            return "Match is exhaustive"
        patterns = ", ".join(self.missing_patterns) if self.missing_patterns else "unknown"
        return f"Non-exhaustive match: missing {patterns}"


@dataclass
class ExhaustivenessError:
    """Error information for non-exhaustive match."""
    
    message: str
    line: int = 0
    column: int = 0
    missing_patterns: List[str] = field(default_factory=list)
    
    def __str__(self) -> str:
        loc = f":{self.line}:{self.column}" if self.line else ""
        return f"{loc} {self.message}"


class PatternExtractor(Visitor):
    """Extracts AbstractPattern from AST PatternNode."""
    
    def __init__(self, type_info: Optional[TypeInferenceResult] = None):
        self.type_info = type_info
    
    def extract(self, pattern: nodes.PatternNode, has_guard: bool = False) -> AbstractPattern:
        """Extract abstract pattern from AST pattern node."""
        result = self.visit(pattern)
        if has_guard and result.kind != PatternKind.GUARD:
            # Wrap in guard pattern to indicate partial coverage
            return AbstractPattern(PatternKind.GUARD, has_guard=True)
        return result
    
    def visit_wildcard_pattern(self, node: nodes.WildcardPattern) -> AbstractPattern:
        return AbstractPattern(PatternKind.WILDCARD)
    
    def visit_binding_pattern(self, node: nodes.BindingPattern) -> AbstractPattern:
        # Binding patterns are wildcards from exhaustiveness perspective
        return AbstractPattern(PatternKind.WILDCARD)
    
    def visit_literal_pattern(self, node: nodes.LiteralPattern) -> AbstractPattern:
        literal = node.literal
        
        if isinstance(literal, nodes.BoolLit):
            return AbstractPattern(PatternKind.LITERAL, value=literal.value)
        elif isinstance(literal, nodes.IntLit):
            return AbstractPattern(PatternKind.LITERAL, value=literal.value)
        elif isinstance(literal, nodes.StringLit):
            return AbstractPattern(PatternKind.LITERAL, value=literal.value)
        else:
            # Other literals treated as specific values
            return AbstractPattern(PatternKind.LITERAL, value=str(literal))
    
    def visit_struct_pattern(self, node: nodes.StructPattern) -> AbstractPattern:
        children = tuple(
            self.visit(fp.pattern) if fp.pattern else AbstractPattern(PatternKind.WILDCARD)
            for fp in node.fields
        )
        return AbstractPattern(PatternKind.STRUCT, value=node.type_name, children=children)
    
    def visit_field_pattern(self, node: nodes.FieldPattern) -> AbstractPattern:
        if node.pattern:
            return self.visit(node.pattern)
        return AbstractPattern(PatternKind.WILDCARD)
    
    def generic_visit(self, node: nodes.ASTNode) -> AbstractPattern:
        # Unknown pattern types are treated as wildcards
        return AbstractPattern(PatternKind.WILDCARD)


class ExhaustivenessChecker(Visitor):
    """
    Checks exhaustiveness of match expressions using pattern matrix algorithm.
    
    For each match expression with ensure_exhaustiveness=True, verifies that
    all possible values of the scrutinee type are covered by at least one arm.
    
    Usage:
        type_visitor = TypeInferenceVisitor()
        module.accept(type_visitor)
        
        checker = ExhaustivenessChecker(type_visitor.result)
        module.accept(checker)
        
        for error in checker.errors:
            print(error)
    """
    
    def __init__(self, type_info: Optional[TypeInferenceResult] = None):
        self.type_info = type_info or TypeInferenceResult()
        self.errors: List[ExhaustivenessError] = []
        self.results: List[ExhaustivenessResult] = []
        self._extractor = PatternExtractor(type_info)
        
        # Known enum/sum types and their constructors
        self._enum_constructors: Dict[str, List[str]] = {}
    
    def check(self, module: nodes.ModuleNode) -> List[ExhaustivenessError]:
        """Check all match expressions in module."""
        # First pass: collect enum/struct definitions
        self._collect_type_info(module)
        
        # Second pass: check match expressions
        self.visit(module)
        
        return self.errors
    
    def _collect_type_info(self, module: nodes.ModuleNode) -> None:
        """Collect enum and struct definitions for constructor analysis."""
        for decl in module.declarations:
            if isinstance(decl, nodes.StructDefNode):
                # Check if this is an enum (fields without types are variants)
                variants = []
                for field_def in decl.fields:
                    if field_def.type_annotation is None:
                        # This is an enum variant
                        variants.append(field_def.name)
                
                if variants:
                    self._enum_constructors[decl.name] = variants
    
    def _get_type_constructors(self, type_ann: TypeAnnotation) -> List[AbstractPattern]:
        """
        Get all constructors for a type.
        
        For finite types (bool, enum), returns all possible values.
        For infinite types (int, string), returns empty list (use default).
        """
        type_name = type_ann.type_name
        
        if type_name == "bool":
            return [
                AbstractPattern(PatternKind.LITERAL, value=True),
                AbstractPattern(PatternKind.LITERAL, value=False),
            ]
        
        if type_name in self._enum_constructors:
            return [
                AbstractPattern(PatternKind.STRUCT, value=variant)
                for variant in self._enum_constructors[type_name]
            ]
        
        # Infinite types - no enumerable constructors
        return []
    
    def _check_usefulness(self, matrix: PatternMatrix, scrutinee_type: TypeAnnotation) -> Optional[List[str]]:
        """
        Check if a pattern would be useful (not covered by existing patterns).
        
        Returns None if matrix covers all cases (exhaustive).
        Returns list of missing patterns otherwise.
        """
        # Base case: empty matrix means pattern is useful (not covered)
        if matrix.is_empty():
            return ["_"]  # Wildcard represents uncovered case
        
        # Base case: row with no patterns means all inputs matched
        if matrix.has_empty_row():
            return None  # Exhaustive
        
        # No patterns to check
        if not matrix.rows or not matrix.rows[0].patterns:
            return None
        
        # Select first column for analysis
        col = 0
        constructors = self._get_column_constructors(matrix, col, scrutinee_type)
        
        if not constructors:
            # Infinite type - check default matrix
            default = matrix.default_matrix(col)
            return self._check_usefulness(default, UNKNOWN_TYPE)
        
        # Check if all constructors are covered
        missing = []
        all_constructors_present = self._all_constructors_present(matrix, col, constructors)
        
        for ctor in constructors:
            specialized = matrix.specialize(col, ctor)
            
            # Recursively check specialized matrix
            # For simplicity, treat struct children as unknown type
            child_type = UNKNOWN_TYPE
            sub_result = self._check_usefulness(specialized, child_type)
            
            if sub_result is not None:
                # This constructor has uncovered cases
                if ctor.kind == PatternKind.LITERAL:
                    missing.append(str(ctor.value))
                elif ctor.kind == PatternKind.STRUCT:
                    missing.append(str(ctor.value))
                else:
                    missing.extend(sub_result)
        
        # If not all constructors present, check default matrix
        if not all_constructors_present:
            default = matrix.default_matrix(col)
            if not default.is_empty():
                default_result = self._check_usefulness(default, UNKNOWN_TYPE)
                if default_result is not None:
                    missing.extend(default_result)
            else:
                # Default cases not covered
                missing.append("_")
        
        return missing if missing else None
    
    def _get_column_constructors(
        self, 
        matrix: PatternMatrix, 
        col: int,
        scrutinee_type: TypeAnnotation
    ) -> List[AbstractPattern]:
        """Get all constructors used in a column + type-defined constructors."""
        seen: Set[Tuple[PatternKind, Any]] = set()
        result = []
        
        # First add type-defined constructors
        type_ctors = self._get_type_constructors(scrutinee_type)
        for ctor in type_ctors:
            key = (ctor.kind, ctor.value)
            if key not in seen:
                seen.add(key)
                result.append(ctor)
        
        # Then add constructors from patterns (for non-finite types)
        for row in matrix.rows:
            if col < len(row.patterns):
                pattern = row.patterns[col]
                if not pattern.is_wildcard() and pattern.kind != PatternKind.GUARD:
                    key = (pattern.kind, pattern.value)
                    if key not in seen:
                        seen.add(key)
                        result.append(pattern)
        
        return result
    
    def _all_constructors_present(
        self,
        matrix: PatternMatrix,
        col: int,
        constructors: List[AbstractPattern]
    ) -> bool:
        """Check if all type constructors appear in the column."""
        if not constructors:
            return False
        
        present: Set[Tuple[PatternKind, Any]] = set()
        
        for row in matrix.rows:
            if col < len(row.patterns):
                pattern = row.patterns[col]
                if not pattern.is_wildcard():
                    present.add((pattern.kind, pattern.value))
        
        required = {(c.kind, c.value) for c in constructors}
        return required <= present
    
    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        """Check exhaustiveness of match expression."""
        # Visit children first
        self.generic_visit(node)
        
        # Skip if exhaustiveness check is disabled
        if not node.ensure_exhaustiveness:
            return
        
        # Build pattern matrix from arms
        rows = []
        for i, arm in enumerate(node.arms):
            pattern = self._extractor.extract(arm.pattern, has_guard=arm.guard is not None)
            rows.append(PatternRow([pattern], i))
        
        matrix = PatternMatrix(rows)
        
        # Get scrutinee type
        scrutinee_type = UNKNOWN_TYPE
        if node.scrutinee and self.type_info:
            scrutinee_type = self.type_info.get_type(node.scrutinee)
        
        # Check exhaustiveness
        missing = self._check_usefulness(matrix, scrutinee_type)
        
        result = ExhaustivenessResult(
            is_exhaustive=(missing is None),
            missing_patterns=missing or [],
            match_node=node,
        )
        self.results.append(result)
        
        if not result.is_exhaustive:
            # Extract source location
            line = 0
            column = 0
            if node.source_location:
                line = node.source_location.start_line
                column = node.source_location.start_column
            
            patterns_str = ", ".join(result.missing_patterns[:5])
            if len(result.missing_patterns) > 5:
                patterns_str += ", ..."
            
            self.errors.append(ExhaustivenessError(
                message=f"Non-exhaustive match: patterns not covered: {patterns_str}",
                line=line,
                column=column,
                missing_patterns=result.missing_patterns,
            ))
    
    def visit_module(self, node: nodes.ModuleNode) -> Any:
        """Entry point: check all match expressions in module."""
        self._collect_type_info(node)
        return self.generic_visit(node)


def check_exhaustiveness(
    module: nodes.ModuleNode,
    type_info: Optional[TypeInferenceResult] = None
) -> List[ExhaustivenessError]:
    """
    Check exhaustiveness of all match expressions in a module.
    
    Args:
        module: The module AST to check
        type_info: Optional type inference result for better analysis
    
    Returns:
        List of errors for non-exhaustive match expressions
    """
    checker = ExhaustivenessChecker(type_info)
    return checker.check(module)
