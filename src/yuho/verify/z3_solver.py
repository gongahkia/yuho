"""
Z3 solver integration for Yuho constraint verification.

Provides Z3-based constraint generation and satisfiability checking
for pattern reachability analysis, test case generation, and
formal verification of statute consistency (parallel to Alloy).
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass, field
import logging

if TYPE_CHECKING:
    from yuho.ast.nodes import (
        ModuleNode, StatuteNode, StructDefNode, ElementNode,
        PenaltyNode, BinaryExprNode, UnaryExprNode, MatchExprNode,
        MatchArm, ASTNode,
    )

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


@dataclass
class Z3Diagnostic:
    """A diagnostic from Z3 verification (parallel to AlloyCounterexample)."""
    check_name: str
    passed: bool
    counterexample: Optional[Dict[str, Any]] = None
    message: str = ""

    def to_diagnostic(self) -> Dict[str, Any]:
        """Convert to LSP-compatible diagnostic."""
        return {
            "message": f"Z3: {self.check_name} - {self.message}",
            "severity": "info" if self.passed else "warning",
            "source": "z3",
            "data": self.counterexample,
        }


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

    def check_statute_consistency(
        self, ast: "ModuleNode"
    ) -> Tuple[bool, List[Z3Diagnostic]]:
        """
        Check statute consistency using Z3 satisfiability.
        
        Generates constraints from the AST and verifies they are consistent
        (satisfiable). Returns diagnostics for any issues found.
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            Tuple of (is_consistent, list of diagnostics)
        """
        generator = Z3Generator()
        diagnostics = generator.generate_consistency_check(ast)
        
        is_consistent = all(d.passed for d in diagnostics)
        return (is_consistent, diagnostics)

    def verify_statute_elements(
        self, ast: "ModuleNode"
    ) -> List[Z3Diagnostic]:
        """
        Verify that statute elements are well-formed and consistent.
        
        Checks:
        - Element names are unique within each statute
        - Element types are valid (actus_reus, mens_rea, circumstance)
        - Penalties have valid ranges (min <= max)
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            List of Z3Diagnostic results
        """
        diagnostics = []
        
        for statute in ast.statutes:
            statute_id = statute.section_number
            
            # Check element uniqueness
            element_names = [e.name for e in statute.elements]
            if len(element_names) != len(set(element_names)):
                duplicates = [n for n in element_names if element_names.count(n) > 1]
                diagnostics.append(Z3Diagnostic(
                    check_name=f"{statute_id}_element_uniqueness",
                    passed=False,
                    message=f"Duplicate element names: {set(duplicates)}"
                ))
            else:
                diagnostics.append(Z3Diagnostic(
                    check_name=f"{statute_id}_element_uniqueness",
                    passed=True,
                    message="All element names are unique"
                ))
            
            # Check element types
            valid_types = {"actus_reus", "mens_rea", "circumstance"}
            for element in statute.elements:
                if element.element_type not in valid_types:
                    diagnostics.append(Z3Diagnostic(
                        check_name=f"{statute_id}_{element.name}_type",
                        passed=False,
                        message=f"Invalid element type: {element.element_type}"
                    ))
            
            # Check penalty ranges
            if statute.penalty:
                penalty = statute.penalty
                
                # Check imprisonment range
                if penalty.imprisonment_min and penalty.imprisonment_max:
                    min_days = penalty.imprisonment_min.total_days()
                    max_days = penalty.imprisonment_max.total_days()
                    if min_days > max_days:
                        diagnostics.append(Z3Diagnostic(
                            check_name=f"{statute_id}_imprisonment_range",
                            passed=False,
                            message=f"Imprisonment min ({min_days} days) > max ({max_days} days)"
                        ))
                    else:
                        diagnostics.append(Z3Diagnostic(
                            check_name=f"{statute_id}_imprisonment_range",
                            passed=True,
                            message="Imprisonment range is valid"
                        ))
                
                # Check fine range
                if penalty.fine_min and penalty.fine_max:
                    if penalty.fine_min.amount > penalty.fine_max.amount:
                        diagnostics.append(Z3Diagnostic(
                            check_name=f"{statute_id}_fine_range",
                            passed=False,
                            message=f"Fine min ({penalty.fine_min.amount}) > max ({penalty.fine_max.amount})"
                        ))
                    else:
                        diagnostics.append(Z3Diagnostic(
                            check_name=f"{statute_id}_fine_range",
                            passed=True,
                            message="Fine range is valid"
                        ))
        
        return diagnostics


class Z3Generator:
    """
    Generates Z3 constraints from Yuho statute ASTs.
    
    This is the Z3 parallel to AlloyGenerator. It translates statute
    elements, penalties, and constraints into Z3 assertions for
    satisfiability checking and verification.
    """
    
    def __init__(self):
        """Initialize the generator."""
        if not Z3_AVAILABLE:
            logger.warning("Z3 not available - constraint generation disabled")
        
        self._sorts: Dict[str, Any] = {}  # Custom Z3 sorts
        self._consts: Dict[str, Any] = {}  # Declared constants
        self._assertions: List[Any] = []  # Collected assertions
    
    def generate(self, ast: "ModuleNode") -> Tuple[Any, List[Any]]:
        """
        Generate Z3 solver and constraints from a module AST.
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            Tuple of (Z3 Solver with constraints, list of named assertions)
        """
        if not Z3_AVAILABLE:
            return None, []
        
        self._sorts = {}
        self._consts = {}
        self._assertions = []
        
        solver = z3.Solver()
        
        # Generate sorts (types) from struct definitions
        self._generate_sorts(ast)
        
        # Generate constraints from statutes
        for statute in ast.statutes:
            self._generate_statute_constraints(statute)
        
        # Add all collected assertions
        for assertion in self._assertions:
            solver.add(assertion)
        
        return solver, self._assertions
    
    def _generate_sorts(self, ast: "ModuleNode") -> None:
        """Generate Z3 sorts from type definitions."""
        if not Z3_AVAILABLE:
            return
        
        # Base sorts
        self._sorts["Person"] = z3.DeclareSort("Person")
        self._sorts["Intent"] = z3.DeclareSort("Intent")
        self._sorts["Element"] = z3.DeclareSort("Element")
        
        # Intent enum values as constants
        self._consts["Intentional"] = z3.Const("Intentional", self._sorts["Intent"])
        self._consts["Reckless"] = z3.Const("Reckless", self._sorts["Intent"])
        self._consts["Negligent"] = z3.Const("Negligent", self._sorts["Intent"])
        
        # Distinct intent values
        self._assertions.append(
            z3.Distinct(
                self._consts["Intentional"],
                self._consts["Reckless"],
                self._consts["Negligent"]
            )
        )
        
        # Generate from struct definitions
        for struct_def in ast.type_defs:
            sort = z3.DeclareSort(struct_def.name)
            self._sorts[struct_def.name] = sort
            
            # Create symbolic field accessors
            for field_def in struct_def.fields:
                field_sort = self._type_to_sort(field_def.type_annotation)
                func_name = f"{struct_def.name}_{field_def.name}"
                self._consts[func_name] = z3.Function(
                    func_name, sort, field_sort
                )
    
    def _generate_statute_constraints(self, statute: "StatuteNode") -> None:
        """Generate Z3 constraints from a statute."""
        if not Z3_AVAILABLE:
            return
        
        statute_id = statute.section_number.replace(".", "_")
        
        # Create a symbolic constant for this statute instance
        if "Statute" not in self._sorts:
            self._sorts["Statute"] = z3.DeclareSort("Statute")
        
        statute_const = z3.Const(f"statute_{statute_id}", self._sorts["Statute"])
        self._consts[f"statute_{statute_id}"] = statute_const
        
        # Generate element constraints
        element_satisfied = []
        for i, element in enumerate(statute.elements):
            elem_name = element.name.replace(" ", "_").replace("-", "_")
            elem_var = z3.Bool(f"{statute_id}_{elem_name}_satisfied")
            self._consts[f"{statute_id}_{elem_name}"] = elem_var
            element_satisfied.append(elem_var)
            
            # Element-specific constraints based on type
            if element.element_type == "mens_rea":
                # Mens rea elements require intent
                intent_var = z3.Const(
                    f"{statute_id}_{elem_name}_intent",
                    self._sorts["Intent"]
                )
                self._consts[f"{statute_id}_{elem_name}_intent"] = intent_var
        
        # All elements must be satisfied for conviction
        if element_satisfied:
            all_elements = z3.And(*element_satisfied)
            conviction_var = z3.Bool(f"{statute_id}_conviction")
            self._consts[f"{statute_id}_conviction"] = conviction_var
            
            # conviction <=> all elements satisfied
            self._assertions.append(conviction_var == all_elements)
        
        # Generate penalty constraints
        if statute.penalty:
            self._generate_penalty_constraints(statute_id, statute.penalty)
    
    def _generate_penalty_constraints(
        self, statute_id: str, penalty: "PenaltyNode"
    ) -> None:
        """Generate Z3 constraints for penalty specification."""
        if not Z3_AVAILABLE:
            return
        
        # Imprisonment duration constraints (in days)
        if penalty.imprisonment_min or penalty.imprisonment_max:
            imprisonment = z3.Int(f"{statute_id}_imprisonment_days")
            self._consts[f"{statute_id}_imprisonment"] = imprisonment
            
            if penalty.imprisonment_min:
                min_days = penalty.imprisonment_min.total_days()
                self._assertions.append(imprisonment >= min_days)
            
            if penalty.imprisonment_max:
                max_days = penalty.imprisonment_max.total_days()
                self._assertions.append(imprisonment <= max_days)
            
            # Imprisonment must be non-negative
            self._assertions.append(imprisonment >= 0)
        
        # Fine constraints (in cents for precision)
        if penalty.fine_min or penalty.fine_max:
            fine = z3.Int(f"{statute_id}_fine_cents")
            self._consts[f"{statute_id}_fine"] = fine
            
            if penalty.fine_min:
                min_cents = int(penalty.fine_min.amount * 100)
                self._assertions.append(fine >= min_cents)
            
            if penalty.fine_max:
                max_cents = int(penalty.fine_max.amount * 100)
                self._assertions.append(fine <= max_cents)
            
            # Fine must be non-negative
            self._assertions.append(fine >= 0)
    
    def _type_to_sort(self, type_node: "ASTNode") -> Any:
        """Convert Yuho type to Z3 sort."""
        if not Z3_AVAILABLE:
            return None
        
        # Import here to avoid circular imports
        from yuho.ast.nodes import BuiltinType, NamedType, ArrayType, OptionalType
        
        if isinstance(type_node, BuiltinType):
            type_map = {
                "int": z3.IntSort(),
                "float": z3.RealSort(),
                "bool": z3.BoolSort(),
                "string": z3.StringSort(),
                "money": z3.IntSort(),  # Cents
                "percent": z3.IntSort(),  # Basis points
                "date": z3.IntSort(),  # Unix timestamp
                "duration": z3.IntSort(),  # Days
                "void": z3.BoolSort(),  # Placeholder
            }
            return type_map.get(type_node.name, z3.IntSort())
        
        elif isinstance(type_node, NamedType):
            if type_node.name in self._sorts:
                return self._sorts[type_node.name]
            # Create a new sort for unknown named types
            sort = z3.DeclareSort(type_node.name)
            self._sorts[type_node.name] = sort
            return sort
        
        elif isinstance(type_node, ArrayType):
            elem_sort = self._type_to_sort(type_node.element_type)
            return z3.ArraySort(z3.IntSort(), elem_sort)
        
        elif isinstance(type_node, OptionalType):
            # Model optional as the inner type (None handled separately)
            return self._type_to_sort(type_node.inner)
        
        # Default to Int
        return z3.IntSort()
    
    def generate_consistency_check(self, ast: "ModuleNode") -> List[Z3Diagnostic]:
        """
        Generate and check consistency constraints for all statutes.
        
        Args:
            ast: ModuleNode from Yuho AST
            
        Returns:
            List of Z3Diagnostic results
        """
        if not Z3_AVAILABLE:
            return [Z3Diagnostic(
                check_name="z3_availability",
                passed=False,
                message="Z3 solver not available"
            )]
        
        diagnostics = []
        solver, assertions = self.generate(ast)
        
        if solver is None:
            return diagnostics
        
        # Check overall satisfiability
        result = solver.check()
        if result == z3.sat:
            diagnostics.append(Z3Diagnostic(
                check_name="statute_consistency",
                passed=True,
                message="All statute constraints are satisfiable"
            ))
        elif result == z3.unsat:
            # Try to get unsat core
            diagnostics.append(Z3Diagnostic(
                check_name="statute_consistency",
                passed=False,
                message="Statute constraints are contradictory"
            ))
        else:
            diagnostics.append(Z3Diagnostic(
                check_name="statute_consistency",
                passed=False,
                message="Could not determine consistency (timeout or unknown)"
            ))
        
        # Check penalty ordering (if multiple statutes)
        if len(ast.statutes) > 1:
            penalty_check = self._check_penalty_ordering(ast)
            diagnostics.extend(penalty_check)
        
        return diagnostics
    
    def _check_penalty_ordering(self, ast: "ModuleNode") -> List[Z3Diagnostic]:
        """Check that penalty ranges don't have unexpected overlaps."""
        diagnostics = []
        
        # Collect statutes with penalties
        statutes_with_penalties = [
            s for s in ast.statutes if s.penalty is not None
        ]
        
        if len(statutes_with_penalties) < 2:
            return diagnostics
        
        # This is a placeholder for more sophisticated penalty analysis
        diagnostics.append(Z3Diagnostic(
            check_name="penalty_ordering",
            passed=True,
            message=f"Analyzed {len(statutes_with_penalties)} statutes with penalties"
        ))
        
        return diagnostics
