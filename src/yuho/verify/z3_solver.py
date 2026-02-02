"""
Z3 solver integration for Yuho constraint verification.

Provides Z3-based constraint generation and satisfiability checking
for pattern reachability analysis and test case generation.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# Try to import z3, provide stub if not available
try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    logger.debug("z3-solver not installed, Z3 features disabled")


@dataclass
class SatisfiabilityResult:
    """Result of a Z3 satisfiability check."""
    satisfiable: bool
    model: Optional[Dict[str, Any]] = None
    message: str = ""


class ConstraintGenerator:
    """
    Generates Z3 constraints from Yuho match-case conditions.
    
    Translates Yuho expressions into Z3 formulas for
    satisfiability checking and model extraction.
    """
    
    def __init__(self):
        """Initialize the constraint generator."""
        if not Z3_AVAILABLE:
            logger.warning("Z3 not available - constraint generation disabled")
        
        self._variables: Dict[str, Any] = {}
    
    def _get_or_create_var(self, name: str, sort: str = "int"):
        """Get or create a Z3 variable."""
        if not Z3_AVAILABLE:
            return None
            
        if name not in self._variables:
            if sort == "int":
                self._variables[name] = z3.Int(name)
            elif sort == "bool":
                self._variables[name] = z3.Bool(name)
            elif sort == "real":
                self._variables[name] = z3.Real(name)
            else:
                self._variables[name] = z3.Int(name)
        
        return self._variables[name]
    
    def generate_from_condition(self, condition_str: str) -> Optional[Any]:
        """
        Generate Z3 constraint from a condition string.
        
        Args:
            condition_str: Condition expression (e.g., "x > 5 && y < 10")
            
        Returns:
            Z3 constraint or None if generation fails
        """
        if not Z3_AVAILABLE:
            return None
        
        try:
            return self._parse_condition(condition_str)
        except Exception as e:
            logger.warning(f"Failed to generate Z3 constraint: {e}")
            return None
    
    def _parse_condition(self, expr: str) -> Any:
        """Parse a condition expression into Z3 constraints."""
        expr = expr.strip()
        
        # Handle boolean operators
        if " && " in expr:
            parts = expr.split(" && ", 1)
            return z3.And(
                self._parse_condition(parts[0]),
                self._parse_condition(parts[1])
            )
        
        if " || " in expr:
            parts = expr.split(" || ", 1)
            return z3.Or(
                self._parse_condition(parts[0]),
                self._parse_condition(parts[1])
            )
        
        if expr.startswith("!"):
            return z3.Not(self._parse_condition(expr[1:].strip()))
        
        # Handle comparisons
        for op, z3_op in [
            (">=", lambda a, b: a >= b),
            ("<=", lambda a, b: a <= b),
            ("!=", lambda a, b: a != b),
            ("==", lambda a, b: a == b),
            (">", lambda a, b: a > b),
            ("<", lambda a, b: a < b),
        ]:
            if op in expr:
                parts = expr.split(op, 1)
                left = self._parse_value(parts[0].strip())
                right = self._parse_value(parts[1].strip())
                return z3_op(left, right)
        
        # Boolean literal or variable
        if expr.lower() == "true":
            return z3.BoolVal(True)
        if expr.lower() == "false":
            return z3.BoolVal(False)
        
        # Variable reference
        return self._get_or_create_var(expr, "bool")
    
    def _parse_value(self, val: str) -> Any:
        """Parse a value into Z3 expression."""
        val = val.strip()
        
        # Try as integer
        try:
            return z3.IntVal(int(val))
        except ValueError:
            pass
        
        # Try as float/real
        try:
            return z3.RealVal(float(val))
        except ValueError:
            pass
        
        # Must be a variable
        return self._get_or_create_var(val, "int")
    
    def generate_from_match_arm(
        self, pattern: str, guard: Optional[str] = None
    ) -> Optional[Any]:
        """
        Generate constraint for a match arm.
        
        Args:
            pattern: Match pattern (e.g., "42", "_", "x if x > 0")
            guard: Optional guard condition
            
        Returns:
            Z3 constraint or None
        """
        if not Z3_AVAILABLE:
            return None
        
        constraints = []
        
        # Handle wildcard
        if pattern.strip() == "_":
            return z3.BoolVal(True)
        
        # Handle literal patterns
        try:
            lit_val = int(pattern)
            match_var = self._get_or_create_var("match_value")
            constraints.append(match_var == lit_val)
        except ValueError:
            # Variable binding pattern
            if pattern.isidentifier():
                pass  # No constraint, just binds
            else:
                # Complex pattern
                constraints.append(self._parse_condition(pattern))
        
        # Add guard constraint
        if guard:
            constraints.append(self._parse_condition(guard))
        
        if not constraints:
            return z3.BoolVal(True)
        
        return z3.And(*constraints) if len(constraints) > 1 else constraints[0]


class Z3Solver:
    """
    Z3-based solver for Yuho verification queries.
    
    Supports:
    - Pattern reachability checking
    - Exhaustiveness verification
    - Test case generation from satisfying models
    """
    
    def __init__(self, timeout_ms: int = 5000):
        """
        Initialize the solver.
        
        Args:
            timeout_ms: Solver timeout in milliseconds
        """
        self.timeout_ms = timeout_ms
        self.constraint_generator = ConstraintGenerator()
    
    def is_available(self) -> bool:
        """Check if Z3 is available."""
        return Z3_AVAILABLE
    
    def check_satisfiability(
        self, constraints: List[Any]
    ) -> SatisfiabilityResult:
        """
        Check if constraints are satisfiable.
        
        Args:
            constraints: List of Z3 constraints
            
        Returns:
            SatisfiabilityResult with model if SAT
        """
        if not Z3_AVAILABLE:
            return SatisfiabilityResult(
                satisfiable=False,
                message="Z3 not available"
            )
        
        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)
        
        for c in constraints:
            if c is not None:
                solver.add(c)
        
        result = solver.check()
        
        if result == z3.sat:
            model = solver.model()
            model_dict = {
                str(d): model[d].as_long() if hasattr(model[d], 'as_long') else str(model[d])
                for d in model.decls()
            }
            return SatisfiabilityResult(
                satisfiable=True,
                model=model_dict,
                message="Satisfiable"
            )
        elif result == z3.unsat:
            return SatisfiabilityResult(
                satisfiable=False,
                message="Unsatisfiable"
            )
        else:
            return SatisfiabilityResult(
                satisfiable=False,
                message="Unknown (timeout or incomplete)"
            )
    
    def check_pattern_reachable(
        self,
        pattern: str,
        previous_patterns: List[str],
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if a pattern is reachable given previous patterns.
        
        A pattern is unreachable if:
        - It's subsumed by previous patterns (they cover all its cases)
        
        Args:
            pattern: The pattern to check
            previous_patterns: Patterns that appear before it
            
        Returns:
            Tuple of (is_reachable, example_input if reachable)
        """
        if not Z3_AVAILABLE:
            return (True, None)  # Assume reachable if can't verify
        
        # Generate constraint: pattern is matched AND no previous pattern matches
        this_constraint = self.constraint_generator.generate_from_match_arm(pattern)
        
        prev_constraints = []
        for prev in previous_patterns:
            prev_c = self.constraint_generator.generate_from_match_arm(prev)
            if prev_c is not None:
                prev_constraints.append(z3.Not(prev_c))
        
        # Pattern is reachable if: this_pattern AND NOT(prev1) AND NOT(prev2) ... is SAT
        all_constraints = [this_constraint] + prev_constraints
        
        result = self.check_satisfiability(all_constraints)
        
        return (result.satisfiable, result.model)
    
    def check_exhaustiveness(
        self, patterns: List[str], type_constraints: Optional[str] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if patterns are exhaustive.
        
        Args:
            patterns: List of patterns in the match expression
            type_constraints: Optional type domain constraint (e.g., "x >= 0")
            
        Returns:
            Tuple of (is_exhaustive, counterexample if not exhaustive)
        """
        if not Z3_AVAILABLE:
            return (True, None)  # Assume exhaustive if can't verify
        
        # Generate constraint: none of the patterns match
        none_match_constraints = []
        for pattern in patterns:
            pattern_c = self.constraint_generator.generate_from_match_arm(pattern)
            if pattern_c is not None:
                none_match_constraints.append(z3.Not(pattern_c))
        
        # Add type constraints if provided
        all_constraints = none_match_constraints
        if type_constraints:
            type_c = self.constraint_generator.generate_from_condition(type_constraints)
            if type_c is not None:
                all_constraints.append(type_c)
        
        # If SAT, patterns are not exhaustive (found an input that matches nothing)
        result = self.check_satisfiability(all_constraints)
        
        if result.satisfiable:
            return (False, result.model)  # Found counterexample
        else:
            return (True, None)  # Exhaustive
    
    def generate_test_case(
        self, constraints: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a concrete test case satisfying constraints.
        
        Args:
            constraints: List of constraint expressions
            
        Returns:
            Dictionary of variable assignments or None if UNSAT
        """
        if not Z3_AVAILABLE:
            return None
        
        z3_constraints = []
        for c in constraints:
            z3_c = self.constraint_generator.generate_from_condition(c)
            if z3_c is not None:
                z3_constraints.append(z3_c)
        
        result = self.check_satisfiability(z3_constraints)
        return result.model if result.satisfiable else None
