"""
Overlap detector for match expression patterns.

Detects when match arm patterns overlap, which may indicate legal ambiguity
in statute definitions. Two patterns overlap when they can both match
the same value, creating potential interpretation conflicts.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Set, Tuple, Any

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.ast.type_inference import TypeInferenceResult
from yuho.ast.exhaustiveness import (
    AbstractPattern,
    PatternKind,
    PatternExtractor,
)


@dataclass
class PatternOverlap:
    """Information about overlapping patterns."""
    
    arm1_index: int
    arm2_index: int
    arm1_line: int = 0
    arm2_line: int = 0
    description: str = ""
    
    def __str__(self) -> str:
        return (
            f"Arms #{self.arm1_index + 1} and #{self.arm2_index + 1} overlap: "
            f"{self.description}"
        )


@dataclass
class OverlapWarning:
    """Warning for overlapping patterns."""
    
    message: str
    line: int = 0
    column: int = 0
    arm1_index: int = -1
    arm2_index: int = -1
    severity: str = "warning"
    
    def __str__(self) -> str:
        loc = f":{self.line}:{self.column}" if self.line else ""
        return f"{loc} warning: {self.message}"


@dataclass
class OverlapResult:
    """Result of overlap analysis for a match expression."""
    
    match_node: Optional[nodes.MatchExprNode]
    overlaps: List[PatternOverlap] = field(default_factory=list)
    
    @property
    def has_overlaps(self) -> bool:
        return len(self.overlaps) > 0


class OverlapDetector(Visitor):
    """
    Detects overlapping patterns in match expressions.
    
    Two patterns overlap if they can match the same value. This is important
    in legal contexts where overlapping statute elements may create ambiguity
    about which provision applies.
    
    Note: This differs from reachability - overlapping patterns can both be
    reachable if neither completely covers the other, but they share some
    common cases.
    
    Usage:
        detector = OverlapDetector()
        module.accept(detector)
        
        for warning in detector.warnings:
            print(warning)
    """
    
    def __init__(self, type_info: Optional[TypeInferenceResult] = None):
        self.type_info = type_info or TypeInferenceResult()
        self.warnings: List[OverlapWarning] = []
        self.results: List[OverlapResult] = []
        self._extractor = PatternExtractor(type_info)
    
    def check(self, module: nodes.ModuleNode) -> List[OverlapWarning]:
        """Check all match expressions in module for overlapping patterns."""
        self.visit(module)
        return self.warnings
    
    def _patterns_overlap(
        self,
        p1: AbstractPattern,
        p2: AbstractPattern,
    ) -> bool:
        """
        Check if two patterns can match the same value.
        
        Patterns overlap if there exists some value v such that
        both p1 and p2 would match v.
        
        Cases:
        - Wildcard overlaps with everything
        - Same literal values overlap
        - Different literal values don't overlap
        - Struct patterns overlap if same constructor and all fields overlap
        """
        # Wildcards overlap with everything
        if p1.is_wildcard() or p2.is_wildcard():
            return True
        
        # Guards make overlap uncertain - assume overlap to be safe
        if p1.has_guard or p2.has_guard:
            return True
        
        # Different kinds don't overlap (except with wildcards, handled above)
        if p1.kind != p2.kind:
            return False
        
        if p1.kind == PatternKind.LITERAL:
            # Literals overlap only if same value
            return p1.value == p2.value
        
        if p1.kind == PatternKind.STRUCT:
            # Struct patterns overlap if same constructor and fields overlap
            if p1.value != p2.value:
                return False
            
            # Check field patterns
            if len(p1.children) != len(p2.children):
                # Different arities - shouldn't happen for same constructor
                return False
            
            # All corresponding fields must overlap for structs to overlap
            for c1, c2 in zip(p1.children, p2.children):
                if not self._patterns_overlap(c1, c2):
                    return False
            
            return True
        
        # Unknown pattern kinds - assume overlap to be safe
        return True
    
    def _describe_overlap(
        self,
        p1: AbstractPattern,
        p2: AbstractPattern,
    ) -> str:
        """Generate a description of why patterns overlap."""
        if p1.is_wildcard() and p2.is_wildcard():
            return "both are catch-all patterns"
        
        if p1.is_wildcard():
            return f"wildcard overlaps with {self._pattern_str(p2)}"
        
        if p2.is_wildcard():
            return f"{self._pattern_str(p1)} overlaps with wildcard"
        
        if p1.kind == PatternKind.LITERAL and p2.kind == PatternKind.LITERAL:
            if p1.value == p2.value:
                return f"duplicate literal pattern: {p1.value}"
        
        if p1.kind == PatternKind.STRUCT and p2.kind == PatternKind.STRUCT:
            if p1.value == p2.value:
                return f"both match constructor '{p1.value}'"
        
        return "patterns can match the same value"
    
    def _pattern_str(self, p: AbstractPattern) -> str:
        """Convert pattern to string for display."""
        if p.is_wildcard():
            return "_"
        
        if p.kind == PatternKind.LITERAL:
            if isinstance(p.value, bool):
                return "TRUE" if p.value else "FALSE"
            if isinstance(p.value, str):
                return f'"{p.value}"'
            return str(p.value)
        
        if p.kind == PatternKind.STRUCT:
            children_str = ", ".join(self._pattern_str(c) for c in p.children)
            if children_str:
                return f"{p.value}({children_str})"
            return str(p.value)
        
        return "?"
    
    def _get_arm_location(self, arm: nodes.MatchArm) -> Tuple[int, int]:
        """Extract source location from match arm."""
        if arm.source_location:
            return arm.source_location.start_line, arm.source_location.start_column
        if arm.pattern.source_location:
            return arm.pattern.source_location.start_line, arm.pattern.source_location.start_column
        return 0, 0
    
    def _check_match_overlaps(
        self,
        node: nodes.MatchExprNode,
    ) -> OverlapResult:
        """Check for overlapping patterns in a match expression."""
        overlaps: List[PatternOverlap] = []
        
        # Extract all patterns
        patterns = []
        for arm in node.arms:
            pattern = self._extractor.extract(arm.pattern, has_guard=arm.guard is not None)
            patterns.append(pattern)
        
        # Compare each pair of patterns
        for i in range(len(patterns)):
            for j in range(i + 1, len(patterns)):
                p1, p2 = patterns[i], patterns[j]
                
                # Skip if one completely covers the other (handled by reachability)
                # We only care about partial overlaps
                if p1.covers(p2) or p2.covers(p1):
                    continue
                
                if self._patterns_overlap(p1, p2):
                    line1, col1 = self._get_arm_location(node.arms[i])
                    line2, col2 = self._get_arm_location(node.arms[j])
                    
                    overlaps.append(PatternOverlap(
                        arm1_index=i,
                        arm2_index=j,
                        arm1_line=line1,
                        arm2_line=line2,
                        description=self._describe_overlap(p1, p2),
                    ))
        
        return OverlapResult(
            match_node=node,
            overlaps=overlaps,
        )
    
    def visit_match_expr(self, node: nodes.MatchExprNode) -> Any:
        """Check for overlapping patterns in match expression."""
        # Visit children first
        self.generic_visit(node)
        
        result = self._check_match_overlaps(node)
        self.results.append(result)
        
        # Generate warnings for overlaps
        for overlap in result.overlaps:
            # Use location of first arm
            line = overlap.arm1_line
            column = 0
            
            self.warnings.append(OverlapWarning(
                message=(
                    f"Match arms #{overlap.arm1_index + 1} and #{overlap.arm2_index + 1} "
                    f"overlap: {overlap.description}"
                ),
                line=line,
                column=column,
                arm1_index=overlap.arm1_index,
                arm2_index=overlap.arm2_index,
            ))
        
        return None
    
    def visit_module(self, node: nodes.ModuleNode) -> Any:
        """Entry point: check all match expressions in module."""
        return self.generic_visit(node)


def check_overlaps(
    module: nodes.ModuleNode,
    type_info: Optional[TypeInferenceResult] = None,
) -> List[OverlapWarning]:
    """
    Check for overlapping patterns in all match expressions.
    
    Args:
        module: The module AST to check
        type_info: Optional type inference result for better analysis
    
    Returns:
        List of warnings for overlapping patterns
    """
    detector = OverlapDetector(type_info)
    return detector.check(module)
