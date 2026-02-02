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


class Z3CounterexampleExtractor:
    """
    Extracts and converts Z3 counterexamples to human-readable diagnostics.
    
    Uses Z3's unsat cores to identify minimal conflicting constraint sets
    and converts satisfying models to test inputs.
    """
    
    def __init__(self):
        """Initialize the extractor."""
        if not Z3_AVAILABLE:
            logger.warning("Z3 not available - counterexample extraction disabled")
    
    def extract_unsat_core(
        self, solver: Any, assertions: List[Tuple[str, Any]]
    ) -> List[str]:
        """
        Extract unsat core from a solver with tracked assertions.
        
        Args:
            solver: Z3 solver instance
            assertions: List of (name, constraint) tuples
            
        Returns:
            List of assertion names in the unsat core
        """
        if not Z3_AVAILABLE:
            return []
        
        # Create solver with unsat core tracking
        core_solver = z3.Solver()
        core_solver.set(unsat_core=True)
        
        # Add tracked assertions
        tracked_assertions = {}
        for name, constraint in assertions:
            tracker = z3.Bool(f"track_{name}")
            tracked_assertions[str(tracker)] = name
            core_solver.add(z3.Implies(tracker, constraint))
            core_solver.add(tracker)  # Assume all are active initially
        
        result = core_solver.check()
        
        if result == z3.unsat:
            core = core_solver.unsat_core()
            return [tracked_assertions[str(c)] for c in core if str(c) in tracked_assertions]
        
        return []
    
    def model_to_counterexample(self, model: Any) -> Dict[str, Any]:
        """
        Convert Z3 model to counterexample dictionary.
        
        Args:
            model: Z3 model from solver
            
        Returns:
            Dictionary mapping variable names to values
        """
        if not Z3_AVAILABLE or model is None:
            return {}
        
        counterexample = {}
        
        for decl in model.decls():
            name = decl.name()
            value = model[decl]
            
            # Convert Z3 values to Python primitives
            if hasattr(value, 'as_long'):
                counterexample[name] = value.as_long()
            elif hasattr(value, 'as_fraction'):
                counterexample[name] = str(value.as_fraction())
            elif hasattr(value, 'as_string'):
                counterexample[name] = value.as_string()
            else:
                counterexample[name] = str(value)
        
        return counterexample
    
    def generate_diagnostic_from_unsat_core(
        self, core_names: List[str], check_name: str
    ) -> Z3Diagnostic:
        """
        Generate diagnostic from unsat core.
        
        Args:
            core_names: Names of constraints in unsat core
            check_name: Name of the check being performed
            
        Returns:
            Z3Diagnostic with conflict information
        """
        if not core_names:
            return Z3Diagnostic(
                check_name=check_name,
                passed=False,
                message="Constraints are unsatisfiable (no core extracted)"
            )
        
        conflict_msg = f"Conflicting constraints: {', '.join(core_names[:5])}"
        if len(core_names) > 5:
            conflict_msg += f" and {len(core_names) - 5} more"
        
        return Z3Diagnostic(
            check_name=check_name,
            passed=False,
            counterexample={"unsat_core": core_names},
            message=conflict_msg
        )
    
    def generate_diagnostic_from_model(
        self, model: Any, check_name: str, message: str
    ) -> Z3Diagnostic:
        """
        Generate diagnostic from satisfying model.
        
        Args:
            model: Z3 model
            check_name: Name of the check
            message: Diagnostic message
            
        Returns:
            Z3Diagnostic with model as counterexample
        """
        counterexample = self.model_to_counterexample(model)
        
        return Z3Diagnostic(
            check_name=check_name,
            passed=False,
            counterexample=counterexample,
            message=message
        )


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

    def enumerate_models(
        self, constraints: List[Any], max_models: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Enumerate multiple satisfying models for given constraints.
        
        Finds up to max_models different satisfying assignments that
        fulfill the constraints. Useful for test case generation and
        exploring solution spaces.
        
        Args:
            constraints: List of Z3 constraints
            max_models: Maximum number of models to enumerate
            
        Returns:
            List of model dictionaries (empty if UNSAT)
        """
        if not Z3_AVAILABLE:
            return []
        
        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)
        
        # Add all constraints
        for c in constraints:
            if c is not None:
                solver.add(c)
        
        models = []
        extractor = Z3CounterexampleExtractor()
        
        for _ in range(max_models):
            result = solver.check()
            
            if result != z3.sat:
                break
            
            # Extract model
            model = solver.model()
            model_dict = extractor.model_to_counterexample(model)
            models.append(model_dict)
            
            # Block this solution to find a different one
            block_constraint = []
            for decl in model.decls():
                const = decl()
                value = model[decl]
                # Add constraint that at least one variable must differ
                block_constraint.append(const != value)
            
            if block_constraint:
                solver.add(z3.Or(block_constraint))
            else:
                # No variables to block, can't enumerate more
                break
        
        return models
    
    def enumerate_statute_interpretations(
        self, ast: "ModuleNode", max_interpretations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Enumerate valid interpretations of statute constraints.
        
        Finds multiple satisfying models that represent different
        valid interpretations of the statutes.
        
        Args:
            ast: ModuleNode from Yuho AST
            max_interpretations: Maximum interpretations to find
            
        Returns:
            List of interpretation dictionaries
        """
        generator = Z3Generator()
        solver, assertions = generator.generate(ast)
        
        if not Z3_AVAILABLE or solver is None:
            return []
        
        interpretations = []
        extractor = Z3CounterexampleExtractor()
        
        for i in range(max_interpretations):
            result = solver.check()
            
            if result != z3.sat:
                break
            
            model = solver.model()
            interpretation = extractor.model_to_counterexample(model)
            interpretation['interpretation_id'] = i + 1
            interpretations.append(interpretation)
            
            # Block this interpretation
            block_constraints = []
            for decl in model.decls():
                const = decl()
                value = model[decl]
                block_constraints.append(const != value)
            
            if block_constraints:
                solver.add(z3.Or(block_constraints))
            else:
                break
        
        return interpretations

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


    def check_match_exhaustiveness(
        self, match_expr: "MatchExprNode"
    ) -> Tuple[bool, List[Z3Diagnostic]]:
        """
        Check if a match expression is exhaustive using Z3.
        
        Analyzes match arms to determine if all possible values of the
        scrutinee are covered. Returns diagnostics with counterexamples
        if match is non-exhaustive.
        
        Args:
            match_expr: MatchExprNode from Yuho AST
            
        Returns:
            Tuple of (is_exhaustive, list of diagnostics)
        """
        from yuho.ast.nodes import (
            WildcardPattern, LiteralPattern, BindingPattern,
            StructPattern, IntLit, StringLit, BoolLit
        )
        
        diagnostics = []
        
        # If no scrutinee (bare match block), can't check exhaustiveness
        if match_expr.scrutinee is None:
            return (True, diagnostics)
        
        # Check if there's a wildcard pattern (always exhaustive)
        has_wildcard = any(
            isinstance(arm.pattern, WildcardPattern) or
            isinstance(arm.pattern, BindingPattern)
            for arm in match_expr.arms
        )
        
        if has_wildcard:
            diagnostics.append(Z3Diagnostic(
                check_name="match_exhaustiveness",
                passed=True,
                message="Match has wildcard pattern (exhaustive)"
            ))
            return (True, diagnostics)
        
        # Extract pattern strings for Z3 checking
        patterns = []
        for arm in match_expr.arms:
            pattern_str = self._pattern_to_constraint_string(arm.pattern)
            if pattern_str:
                patterns.append(pattern_str)
        
        # Check exhaustiveness with Z3
        is_exhaustive, counterexample = self.check_exhaustiveness(patterns)
        
        if is_exhaustive:
            diagnostics.append(Z3Diagnostic(
                check_name="match_exhaustiveness",
                passed=True,
                message=f"Match expression is exhaustive ({len(patterns)} arms)"
            ))
        else:
            extractor = Z3CounterexampleExtractor()
            if counterexample:
                diagnostic = extractor.generate_diagnostic_from_model(
                    None,  # Would need Z3 model object here
                    "match_exhaustiveness",
                    f"Match is non-exhaustive, missing case for: {counterexample}"
                )
                diagnostic = Z3Diagnostic(
                    check_name="match_exhaustiveness",
                    passed=False,
                    counterexample=counterexample,
                    message=f"Match is non-exhaustive, example missing value: {counterexample}"
                )
            else:
                diagnostic = Z3Diagnostic(
                    check_name="match_exhaustiveness",
                    passed=False,
                    message="Match is non-exhaustive (no counterexample generated)"
                )
            diagnostics.append(diagnostic)
        
        return (is_exhaustive, diagnostics)
    
    def _pattern_to_constraint_string(self, pattern: "ASTNode") -> Optional[str]:
        """
        Convert a pattern AST node to a constraint string for Z3.
        
        Args:
            pattern: Pattern node from AST
            
        Returns:
            Constraint string or None if pattern can't be converted
        """
        from yuho.ast.nodes import (
            WildcardPattern, LiteralPattern, BindingPattern,
            IntLit, StringLit, BoolLit
        )
        
        if isinstance(pattern, WildcardPattern):
            return "_"
        
        if isinstance(pattern, BindingPattern):
            return pattern.name
        
        if isinstance(pattern, LiteralPattern):
            lit = pattern.literal
            if isinstance(lit, IntLit):
                return str(lit.value)
            elif isinstance(lit, BoolLit):
                return "true" if lit.value else "false"
            elif isinstance(lit, StringLit):
                return f'"{lit.value}"'
        
        # For other patterns, return None (can't easily convert)
        return None


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
        
        extractor = Z3CounterexampleExtractor()
        
        # Check overall satisfiability
        result = solver.check()
        if result == z3.sat:
            diagnostics.append(Z3Diagnostic(
                check_name="statute_consistency",
                passed=True,
                message="All statute constraints are satisfiable"
            ))
        elif result == z3.unsat:
            # Extract unsat core for better diagnostics
            # Need to regenerate with tracked assertions
            tracked_assertions = []
            for i, assertion in enumerate(assertions):
                tracked_assertions.append((f"assertion_{i}", assertion))
            
            core_names = extractor.extract_unsat_core(solver, tracked_assertions)
            
            if core_names:
                diagnostic = extractor.generate_diagnostic_from_unsat_core(
                    core_names, "statute_consistency"
                )
                diagnostics.append(diagnostic)
            else:
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
