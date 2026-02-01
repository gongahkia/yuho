"""
Reachability checker for match expressions.

Detects unreachable match arms (dead code) by analyzing whether
earlier patterns already cover all cases that a later pattern would match.
Uses the same pattern matrix techniques as exhaustiveness checking.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Dict, Any

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.ast.type_inference import TypeInferenceResult, UNKNOWN_TYPE
from yuho.ast.exhaustiveness import (
    AbstractPattern,
    PatternKind,
    PatternMatrix,
    PatternRow,
    PatternExtractor,
)


@dataclass
class UnreachableArm:
    """Information about an unreachable match arm."""
    
    arm_index: int
    line: int = 0
    column: int = 0
    reason: str = "arm is unreachable"
    
    def __str__(self) -> str:
        loc = f":{self.line}:{self.column}" if self.line else ""
        return f"{loc} {self.reason}"


@dataclass
class ReachabilityError:
    """Error for unreachable code detection."""
    
    message: str
    line: int = 0
    column: int = 0
    arm_index: int = -1
    severity: str = "warning"  # Unreachable code is typically a warning
    
    def __str__(self) -> str:
        loc = f":{self.line}:{self.column}" if self.line else ""
        return f"{loc} warning: {self.message}"


@dataclass
class ReachabilityResult:
    """Result of reachability analysis for a match expression."""
    
    match_node: Optional[nodes.MatchExprNode]
    unreachable_arms: List[UnreachableArm] = field(default_factory=list)
    
    @property
    def all_reachable(self) -> bool:
        return len(self.unreachable_arms) == 0


class ReachabilityChecker(Visitor):
    """
    Checks for unreachable match arms (dead code).
    
    A match arm is unreachable if all patterns it could match are already
    covered by earlier arms. This is determined by checking if adding the
    arm's pattern to the matrix of previous arms would be "useless".
    
    Usage:
        type_visitor = TypeInferenceVisitor()
        module.accept(type_visitor)
        
        checker = ReachabilityChecker(type_visitor.result)
        module.accept(checker)
        
        for error in checker.errors:
            print(error)
    """
    
    def __init__(self, type_info: Optional[TypeInferenceResult] = None):
        self.type_info = type_info or TypeInferenceResult()
        self.errors: List[ReachabilityError] = []
        self.results: List[ReachabilityResult] = []
        self._extractor = PatternExtractor(type_info)
    
    def check(self, module: nodes.ModuleNode) -> List[ReachabilityError]:
        """Check all match expressions in module for unreachable arms."""
        self.visit(module)
        return self.errors
    
    def _is_pattern_useful(
        self,
        pattern: AbstractPattern,
        preceding_patterns: List[AbstractPattern],
    ) -> bool:
        """
        Check if a pattern is useful given preceding patterns.
        
        A pattern is useful if it can match some value that is not
        already matched by any of the preceding patterns.
        
        Uses the pattern matrix algorithm: a pattern P is useful w.r.t
        matrix M if there exists some value v such that P matches v
        and no row in M matches v.
        """
        if not preceding_patterns:
            # First pattern is always useful
            return True
        
        # If any preceding pattern is a pure wildcard, this pattern is useless
        for prev in preceding_patterns:
            if prev.is_wildcard():
                return False
        
        # Build matrix from preceding patterns
        rows = [PatternRow([p], i) for i, p in enumerate(preceding_patterns)]
        matrix = PatternMatrix(rows)
        
        # Check usefulness of new pattern
        return self._pattern_useful_in_matrix(pattern, matrix)
    
    def _pattern_useful_in_matrix(
        self,
        pattern: AbstractPattern,
        matrix: PatternMatrix,
    ) -> bool:
        """
        Check if pattern is useful against the given matrix.
        
        Algorithm:
        1. If matrix is empty, pattern is useful
        2. If pattern is wildcard and matrix has wildcard rows, not useful
        3. Otherwise, specialize by constructors
        """
        # Empty matrix - pattern is useful
        if matrix.is_empty():
            return True
        
        # Check if matrix has any rows
        if not matrix.rows or not matrix.rows[0].patterns:
            return True
        
        col = 0
        
        # If pattern is wildcard, check if all constructors are covered
        if pattern.is_wildcard():
            # Pattern can match anything not already matched
            # Check if there are any wildcards in the matrix at this column
            for row in matrix.rows:
                if col < len(row.patterns) and row.patterns[col].is_wildcard():
                    # Wildcard already covers everything
                    return False
            # No wildcard in matrix means this pattern can match something new
            return True
        
        # Non-wildcard pattern: specialize matrix by this constructor
        specialized = matrix.specialize(col, pattern)
        
        # If specialized matrix is empty, pattern matches something new
        if specialized.is_empty():
            return True
        
        # Check children recursively
        if pattern.children:
            child_patterns = list(pattern.children)
            child_matrix = specialized
            
            for i, child in enumerate(child_patterns):
                if not child_matrix.rows:
                    return True
                if not self._child_useful(child, child_matrix, i):
                    return False
            return True
        
        # No children, check if any row completely covers this
        for row in specialized.rows:
            if not row.patterns:
                # Row with no remaining patterns = complete match
                return False
        
        return True
    
    def _child_useful(
        self,
        child: AbstractPattern,
        matrix: PatternMatrix,
        col: int,
    ) -> bool:
        """Check if a child pattern adds useful discrimination."""
        # Extract column patterns from matrix
        col_patterns = []
        for row in matrix.rows:
            if col < len(row.patterns):
                col_patterns.append(row.patterns[col])
        
        if not col_patterns:
            return True
        
        # Check if any pattern fully covers the child
        for p in col_patterns:
            if p.is_wildcard():
                return not child.is_wildcard()
            if p.covers(child):
                return False
        
        return True
    
    def _check_match_reachability(
        self,
        node: nodes.MatchExprNode,
    ) -> ReachabilityResult:
        """Check reachability of all arms in a match expression."""
        unreachable: List[UnreachableArm] = []
        preceding_patterns: List[AbstractPattern] = []
        
        for i, arm in enumerate(node.arms):
            pattern = self._extractor.extract(arm.pattern, has_guard=arm.guard is not None)
            
            # Check if this arm is reachable
            is_useful = self._is_pattern_useful(pattern, preceding_patterns)
            
            if not is_useful:
                # Extract source location
                line = 0
                column = 0
                if arm.source_location:
                    line = arm.source_location.start_line
                    column = arm.source_location.start_column
                elif arm.pattern.source_location:
                    line = arm.pattern.source_location.start_line
                    column = arm.pattern.source_location.start_column
                
                unreachable.append(UnreachableArm(
                    arm_index=i,
                    line=line,
                    column=column,
                    reason=f"match arm #{i + 1} is unreachable (covered by earlier patterns)",
                ))
            
            # Add to preceding patterns only if no guard
            # (guards make coverage conditional)
            if arm.guard is None:
                preceding_patterns.append(pattern)
        
        return ReachabilityResult(
            match_node=node,
            unreachable_arms=unreachable,
        )
    
    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        """Check reachability of match expression arms."""
        # Visit children first
        self.generic_visit(node)
        
        result = self._check_match_reachability(node)
        self.results.append(result)
        
        # Add errors for unreachable arms
        for arm in result.unreachable_arms:
            self.errors.append(ReachabilityError(
                message=arm.reason,
                line=arm.line,
                column=arm.column,
                arm_index=arm.arm_index,
            ))
        
        return None
    
    def visit_module(self, node: nodes.ModuleNode) -> Any:
        """Entry point: check all match expressions in module."""
        return self.generic_visit(node)


def check_reachability(
    module: nodes.ModuleNode,
    type_info: Optional[TypeInferenceResult] = None,
) -> List[ReachabilityError]:
    """
    Check for unreachable match arms in all match expressions.
    
    Args:
        module: The module AST to check
        type_info: Optional type inference result for better analysis
    
    Returns:
        List of warnings for unreachable match arms
    """
    checker = ReachabilityChecker(type_info)
    return checker.check(module)
