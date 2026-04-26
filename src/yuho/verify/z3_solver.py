"""
Z3 solver integration for Yuho constraint verification.

Provides Z3-based constraint generation and satisfiability checking
for pattern reachability analysis, test case generation, and
formal verification of statute consistency (parallel to Alloy).
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Set, Tuple, Union, TYPE_CHECKING
from dataclasses import dataclass, field
import logging

if TYPE_CHECKING:
    from yuho.ast.nodes import (
        ModuleNode,
        StatuteNode,
        StructDefNode,
        ElementNode,
        ElementGroupNode,
        ExceptionNode,
        PenaltyNode,
        BinaryExprNode,
        UnaryExprNode,
        MatchExprNode,
        MatchArm,
        ASTNode,
    )
    from yuho.parser.source_location import SourceLocation

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
    source_location: Optional["SourceLocation"] = None

    def to_diagnostic(self) -> Dict[str, Any]:
        """Convert to LSP-compatible diagnostic."""
        diag: Dict[str, Any] = {
            "message": f"Z3: {self.check_name} - {self.message}",
            "severity": "info" if self.passed else "warning",
            "source": "z3",
            "data": self.counterexample,
        }
        if self.source_location is not None:
            diag["range"] = {
                "start": {
                    "line": self.source_location.line - 1,
                    "character": self.source_location.col - 1,
                },
                "end": {
                    "line": self.source_location.end_line - 1,
                    "character": self.source_location.end_col - 1,
                },
            }
            diag["file"] = self.source_location.file
        return diag


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

    def extract_unsat_core(self, solver: Any, assertions: List[Tuple[str, Any]]) -> List[str]:
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
            if hasattr(value, "as_long"):
                counterexample[name] = value.as_long()
            elif hasattr(value, "as_fraction"):
                counterexample[name] = str(value.as_fraction())
            elif hasattr(value, "as_string"):
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
                message="Constraints are unsatisfiable (no core extracted)",
            )

        conflict_msg = f"Conflicting constraints: {', '.join(core_names[:5])}"
        if len(core_names) > 5:
            conflict_msg += f" and {len(core_names) - 5} more"

        return Z3Diagnostic(
            check_name=check_name,
            passed=False,
            counterexample={"unsat_core": core_names},
            message=conflict_msg,
        )

    def generate_diagnostic_from_model(
        self,
        model: Any,
        check_name: str,
        message: str,
        source_location: Optional["SourceLocation"] = None,
    ) -> Z3Diagnostic:
        """
        Generate diagnostic from satisfying model.

        Args:
            model: Z3 model
            check_name: Name of the check
            message: Diagnostic message
            source_location: Optional AST source location for mapping

        Returns:
            Z3Diagnostic with model as counterexample
        """
        counterexample = self.model_to_counterexample(model)

        return Z3Diagnostic(
            check_name=check_name,
            passed=False,
            counterexample=counterexample,
            message=message,
            source_location=source_location,
        )

    def generate_source_mapped_diagnostic(
        self,
        check_name: str,
        passed: bool,
        message: str,
        ast_node: "ASTNode",
        counterexample: Optional[Dict[str, Any]] = None,
    ) -> Z3Diagnostic:
        """
        Generate diagnostic mapped to an AST node's source location.

        Args:
            check_name: Name of the check
            passed: Whether the check passed
            message: Diagnostic message
            ast_node: AST node to extract source location from
            counterexample: Optional counterexample data

        Returns:
            Z3Diagnostic with source location from AST
        """
        loc = getattr(ast_node, "source_location", None)
        return Z3Diagnostic(
            check_name=check_name,
            passed=passed,
            counterexample=counterexample,
            message=message,
            source_location=loc,
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
            return z3.And(self._parse_condition(parts[0]), self._parse_condition(parts[1]))

        if " || " in expr:
            parts = expr.split(" || ", 1)
            return z3.Or(self._parse_condition(parts[0]), self._parse_condition(parts[1]))

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

    def generate_from_match_arm(self, pattern: str, guard: Optional[str] = None) -> Optional[Any]:
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

    def check_satisfiability(self, constraints: List[Any]) -> SatisfiabilityResult:
        """
        Check if constraints are satisfiable.

        Args:
            constraints: List of Z3 constraints

        Returns:
            SatisfiabilityResult with model if SAT
        """
        if not Z3_AVAILABLE:
            return SatisfiabilityResult(satisfiable=False, message="Z3 not available")

        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)

        for c in constraints:
            if c is not None:
                solver.add(c)

        result = solver.check()

        if result == z3.sat:
            model = solver.model()
            model_dict = {
                str(d): (model[d].as_long() if hasattr(model[d], "as_long") else str(model[d]))
                for d in model.decls()
            }
            return SatisfiabilityResult(satisfiable=True, model=model_dict, message="Satisfiable")
        elif result == z3.unsat:
            return SatisfiabilityResult(satisfiable=False, message="Unsatisfiable")
        else:
            return SatisfiabilityResult(
                satisfiable=False, message="Unknown (timeout or incomplete)"
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

    def generate_test_case(self, constraints: List[str]) -> Optional[Dict[str, Any]]:
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
            interpretation["interpretation_id"] = i + 1
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

    def check_statute_consistency(self, ast: "ModuleNode") -> Tuple[bool, List[Z3Diagnostic]]:
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

    def verify_statute_elements(self, ast: "ModuleNode") -> List[Z3Diagnostic]:
        """
        Verify that statute elements are well-formed and consistent.

        Checks:
        - Element names are unique within each statute
        - Element types are valid (actus_reus, mens_rea, circumstance)
        - Penalties have valid ranges (min <= max)

        Diagnostics are source-mapped to AST node locations.

        Args:
            ast: ModuleNode from Yuho AST

        Returns:
            List of Z3Diagnostic results
        """
        from yuho.ast.nodes import ElementNode, ElementGroupNode

        diagnostics: List[Z3Diagnostic] = []
        extractor = Z3CounterexampleExtractor()

        def _collect_elements(elem):
            """Recursively collect ElementNode instances from element tree."""
            if isinstance(elem, ElementNode):
                return [elem]
            if isinstance(elem, ElementGroupNode):
                result = []
                for m in elem.members:
                    result.extend(_collect_elements(m))
                return result
            return []

        for statute in ast.statutes:
            statute_id = statute.section_number
            statute_loc = getattr(statute, "source_location", None)

            # Collect all leaf elements
            all_elements = []
            for e in statute.elements:
                all_elements.extend(_collect_elements(e))

            # Check element uniqueness
            element_names = [e.name for e in all_elements]
            if len(element_names) != len(set(element_names)):
                duplicates = [n for n in element_names if element_names.count(n) > 1]
                diagnostics.append(
                    Z3Diagnostic(
                        check_name=f"{statute_id}_element_uniqueness",
                        passed=False,
                        message=f"Duplicate element names: {set(duplicates)}",
                        source_location=statute_loc,
                    )
                )
            else:
                diagnostics.append(
                    Z3Diagnostic(
                        check_name=f"{statute_id}_element_uniqueness",
                        passed=True,
                        message="All element names are unique",
                        source_location=statute_loc,
                    )
                )

            # Check element types
            valid_types = {"actus_reus", "mens_rea", "circumstance"}
            for element in all_elements:
                elem_loc = getattr(element, "source_location", None)
                if element.element_type not in valid_types:
                    diagnostics.append(
                        Z3Diagnostic(
                            check_name=f"{statute_id}_{element.name}_type",
                            passed=False,
                            message=f"Invalid element type: {element.element_type}",
                            source_location=elem_loc,
                        )
                    )

            # Check penalty ranges
            if statute.penalty:
                penalty = statute.penalty
                penalty_loc = getattr(penalty, "source_location", None)

                # Check imprisonment range
                if penalty.imprisonment_min and penalty.imprisonment_max:
                    min_days = penalty.imprisonment_min.total_days()
                    max_days = penalty.imprisonment_max.total_days()
                    if min_days > max_days:
                        diagnostics.append(
                            Z3Diagnostic(
                                check_name=f"{statute_id}_imprisonment_range",
                                passed=False,
                                message=f"Imprisonment min ({min_days} days) > max ({max_days} days)",
                                source_location=penalty_loc,
                            )
                        )
                    else:
                        diagnostics.append(
                            Z3Diagnostic(
                                check_name=f"{statute_id}_imprisonment_range",
                                passed=True,
                                message="Imprisonment range is valid",
                                source_location=penalty_loc,
                            )
                        )

                # Check fine range
                if penalty.fine_min and penalty.fine_max:
                    if penalty.fine_min.amount > penalty.fine_max.amount:
                        diagnostics.append(
                            Z3Diagnostic(
                                check_name=f"{statute_id}_fine_range",
                                passed=False,
                                message=f"Fine min ({penalty.fine_min.amount}) > max ({penalty.fine_max.amount})",
                                source_location=penalty_loc,
                            )
                        )
                    else:
                        diagnostics.append(
                            Z3Diagnostic(
                                check_name=f"{statute_id}_fine_range",
                                passed=True,
                                message="Fine range is valid",
                                source_location=penalty_loc,
                            )
                        )

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
            WildcardPattern,
            LiteralPattern,
            BindingPattern,
            StructPattern,
            IntLit,
            StringLit,
            BoolLit,
        )

        diagnostics: List[Z3Diagnostic] = []

        # If no scrutinee (bare match block), can't check exhaustiveness
        if match_expr.scrutinee is None:
            return (True, diagnostics)

        # Check if there's a wildcard pattern (always exhaustive)
        has_wildcard = any(
            isinstance(arm.pattern, WildcardPattern) or isinstance(arm.pattern, BindingPattern)
            for arm in match_expr.arms
        )

        if has_wildcard:
            diagnostics.append(
                Z3Diagnostic(
                    check_name="match_exhaustiveness",
                    passed=True,
                    message="Match has wildcard pattern (exhaustive)",
                )
            )
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
            diagnostics.append(
                Z3Diagnostic(
                    check_name="match_exhaustiveness",
                    passed=True,
                    message=f"Match expression is exhaustive ({len(patterns)} arms)",
                )
            )
        else:
            extractor = Z3CounterexampleExtractor()
            if counterexample:
                diagnostic = extractor.generate_diagnostic_from_model(
                    None,  # Would need Z3 model object here
                    "match_exhaustiveness",
                    f"Match is non-exhaustive, missing case for: {counterexample}",
                )
                diagnostic = Z3Diagnostic(
                    check_name="match_exhaustiveness",
                    passed=False,
                    counterexample=counterexample,
                    message=f"Match is non-exhaustive, example missing value: {counterexample}",
                )
            else:
                diagnostic = Z3Diagnostic(
                    check_name="match_exhaustiveness",
                    passed=False,
                    message="Match is non-exhaustive (no counterexample generated)",
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
            WildcardPattern,
            LiteralPattern,
            BindingPattern,
            IntLit,
            StringLit,
            BoolLit,
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

        # Apply refinement type bounds to variable declarations
        self._apply_refinement_bounds(ast)

        # Add all collected assertions
        for assertion in self._assertions:
            solver.add(assertion)

        return solver, self._assertions

    def _generate_sorts(self, ast: "ModuleNode") -> None:
        """
        Generate Z3 sorts dynamically from AST struct definitions.

        Walks ast.type_defs to create Z3 DatatypeSorts for each
        StructDefNode, with constructor fields matching the struct's
        fields. Falls back to DeclareSort only for base infrastructure
        sorts that are not user-defined.
        """
        if not Z3_AVAILABLE:
            return

        # Infrastructure sorts (kept for statute/element modeling)
        self._sorts["Statute"] = z3.DeclareSort("Statute")

        # Walk struct definitions to create DatatypeSorts
        for struct_def in ast.type_defs:
            self._generate_struct_sort(struct_def)

        # Walk enum definitions to create Z3 EnumSorts
        for enum_def in getattr(ast, "enum_defs", ()):
            self._generate_enum_sort(enum_def)

        # If no struct defined Intent-like enum, create a default one
        if "Intent" not in self._sorts:
            self._sorts["Intent"] = z3.DeclareSort("Intent")
            self._consts["Intentional"] = z3.Const("Intentional", self._sorts["Intent"])
            self._consts["Reckless"] = z3.Const("Reckless", self._sorts["Intent"])
            self._consts["Negligent"] = z3.Const("Negligent", self._sorts["Intent"])
            self._assertions.append(
                z3.Distinct(
                    self._consts["Intentional"],
                    self._consts["Reckless"],
                    self._consts["Negligent"],
                )
            )

    def _apply_refinement_bounds(self, ast: "ModuleNode") -> None:
        """Emit z3.And(var >= lo, var <= hi) for variables with RefinementTypeNode."""
        if not Z3_AVAILABLE:
            return
        from yuho.ast.nodes import RefinementTypeNode, IntLit, FloatLit

        for var_decl in ast.variables:
            if not isinstance(var_decl.type_annotation, RefinementTypeNode):
                continue
            rt = var_decl.type_annotation
            lo = rt.lower_bound.value if isinstance(rt.lower_bound, (IntLit, FloatLit)) else None
            hi = rt.upper_bound.value if isinstance(rt.upper_bound, (IntLit, FloatLit)) else None
            if lo is None or hi is None:
                continue
            var = z3.Int(var_decl.name)
            self._consts[var_decl.name] = var
            self._assertions.append(z3.And(var >= int(lo), var <= int(hi)))

    def _generate_struct_sort(self, struct_def: "StructDefNode") -> None:
        """
        Create a Z3 DatatypeSort for a single StructDefNode.

        Each struct becomes a Z3 Datatype with a single constructor
        whose arguments correspond to the struct's fields.
        """
        if not Z3_AVAILABLE:
            return

        from yuho.ast.nodes import BuiltinType

        dt = z3.Datatype(struct_def.name)

        # Collect (accessor_name, sort) pairs; we need all field sorts
        # resolved before declaring so we pre-compute them.
        field_specs: List[Tuple[str, Any]] = []
        for field_def in struct_def.fields:
            acc_name = f"{struct_def.name}_{field_def.name}"
            field_sort = self._type_to_sort(field_def.type_annotation)
            field_specs.append((acc_name, field_sort))

        # Declare the constructor with all fields
        constructor_name = f"mk_{struct_def.name}"
        dt.declare(constructor_name, *field_specs)

        try:
            created_sort = dt.create()
            self._sorts[struct_def.name] = created_sort
            # Store the constructor
            self._consts[constructor_name] = getattr(created_sort, constructor_name)
            # Store field accessor functions
            for acc_name, _ in field_specs:
                self._consts[acc_name] = getattr(created_sort, acc_name)
        except Exception as e:
            # Fallback: if Datatype creation fails (e.g. recursive types),
            # use uninterpreted sort with function accessors
            logger.debug(
                f"DatatypeSort creation failed for {struct_def.name}: {e}, using DeclareSort fallback"
            )
            sort = z3.DeclareSort(struct_def.name)
            self._sorts[struct_def.name] = sort
            for acc_name, field_sort in field_specs:
                self._consts[acc_name] = z3.Function(acc_name, sort, field_sort)

    def _generate_enum_sort(self, enum_def) -> None:
        """Create a Z3 EnumSort for an EnumDefNode."""
        if not Z3_AVAILABLE:
            return
        variant_names = [v.name for v in enum_def.variants]
        if not variant_names:
            return
        sort, consts = z3.EnumSort(enum_def.name, variant_names)
        self._sorts[enum_def.name] = sort
        for vname, const in zip(variant_names, consts):
            self._consts[vname] = const
        # all variants are distinct (Z3 EnumSort guarantees this)

    def _generate_statute_constraints(self, statute: "StatuteNode") -> None:
        """
        Generate Z3 constraints from a statute, driven by actual AST
        ElementNode / ElementGroupNode structure.
        """
        if not Z3_AVAILABLE:
            return

        from yuho.ast.nodes import ElementNode, ElementGroupNode

        statute_id = statute.section_number.replace(".", "_")

        # Create a symbolic constant for this statute instance
        statute_const = z3.Const(f"statute_{statute_id}", self._sorts["Statute"])
        self._consts[f"statute_{statute_id}"] = statute_const

        # Recursively translate element tree into a Z3 boolean expression.
        # When a section declares its elements only inside subsections
        # (the typical shape for general-defence statutes — s76–s106
        # under Chapter IV — and for any provision whose drafting splits
        # by subsection), we hoist every subsection's elements to the
        # top level. The Z3 model treats the top-level conjunction as
        # the section's predicate; the subsection split is structurally
        # irrelevant once elements are flattened. Without this hoist,
        # `<sX>_elements_satisfied` would not exist for any defence
        # statute, breaking `yuho narrow-defence` and any cross-section
        # query that names them.
        element_exprs = []
        for elem in statute.elements:
            expr = self._translate_element(statute_id, elem)
            if expr is not None:
                element_exprs.append(expr)
        if not element_exprs:
            for sub in getattr(statute, "subsections", ()) or ():
                for elem in getattr(sub, "elements", ()) or ():
                    expr = self._translate_element(statute_id, elem)
                    if expr is not None:
                        element_exprs.append(expr)

        # Top-level elements are implicitly conjunctive (all must hold).
        # We split the original biconditional `conviction == all_elements`
        # into two named vars so a satisfied-but-excused fact pattern
        # (elements all true *and* an exception fires) is representable:
        #     elements_satisfied <=> all top-level elements hold
        #     conviction         <=> elements_satisfied AND NOT any_exc_fires
        # Without the split, an exception firing would force one of the
        # elements to be false (since exc_fires => NOT conviction was
        # asserted alongside the original biconditional), which forbids
        # the doctrinal reading "elements met but offence excused".
        if element_exprs:
            if len(element_exprs) == 1:
                all_elements = element_exprs[0]
            else:
                all_elements = z3.And(*element_exprs)

            elements_satisfied = z3.Bool(f"{statute_id}_elements_satisfied")
            self._consts[f"{statute_id}_elements_satisfied"] = elements_satisfied
            self._assertions.append(elements_satisfied == all_elements)

            conviction_var = z3.Bool(f"{statute_id}_conviction")
            self._consts[f"{statute_id}_conviction"] = conviction_var
            # The conviction biconditional is closed in
            # _generate_exception_constraints once the exc_fires set is
            # known — it sets `conviction <=> elements_satisfied AND NOT any_fires`.
            # If a statute has no exceptions, the bicond degenerates to
            # `conviction <=> elements_satisfied`.

        # Temporal ordering constraints
        self._generate_temporal_constraints(statute_id, statute)

        # Exception constraints (also closes the conviction biconditional).
        self._generate_exception_constraints(statute_id, statute)

        # Penalty constraints
        if statute.penalty:
            self._generate_penalty_constraints(statute_id, statute.penalty)

    def _generate_temporal_constraints(self, statute_id: str, statute: "StatuteNode") -> None:
        """Create Int time variables per element and assert ordering from temporal constraints."""
        if not Z3_AVAILABLE:
            return
        for tc in getattr(statute, "temporal_constraints", ()):
            subj_name = f"{statute_id}_{tc.subject}_time"
            obj_name = f"{statute_id}_{tc.object}_time"
            if subj_name not in self._consts:
                self._consts[subj_name] = z3.Int(subj_name)
            if obj_name not in self._consts:
                self._consts[obj_name] = z3.Int(obj_name)
            subj_var = self._consts[subj_name]
            obj_var = self._consts[obj_name]
            if tc.relation == "precedes":
                self._assertions.append(subj_var < obj_var)
            elif tc.relation == "after":
                self._assertions.append(subj_var > obj_var)
            elif tc.relation == "during":
                self._assertions.append(subj_var == obj_var)

    def _translate_element(
        self, statute_id: str, elem: "Union[ElementNode, ElementGroupNode]"
    ) -> Optional[Any]:
        """
        Recursively translate an ElementNode or ElementGroupNode to Z3.

        ElementNode -> Bool variable (+ intent variable for mens_rea)
        ElementGroupNode(all_of) -> And(members...)
        ElementGroupNode(any_of) -> Or(members...)
        """
        if not Z3_AVAILABLE:
            return None

        from yuho.ast.nodes import ElementNode, ElementGroupNode

        if isinstance(elem, ElementNode):
            safe_name = elem.name.replace(" ", "_").replace("-", "_")
            var_name = f"{statute_id}_{safe_name}_satisfied"
            elem_var = z3.Bool(var_name)
            self._consts[var_name] = elem_var

            # Mens rea elements carry an intent variable
            if elem.element_type == "mens_rea":
                intent_name = f"{statute_id}_{safe_name}_intent"
                intent_var = z3.Const(intent_name, self._sorts["Intent"])
                self._consts[intent_name] = intent_var

            # Translate match-expression descriptions to constraints
            self._translate_element_description(statute_id, safe_name, elem)

            return elem_var

        elif isinstance(elem, ElementGroupNode):
            child_exprs = []
            for child in elem.members:
                child_expr = self._translate_element(statute_id, child)
                if child_expr is not None:
                    child_exprs.append(child_expr)

            if not child_exprs:
                return z3.BoolVal(True)

            if elem.combinator == "all_of":
                return z3.And(*child_exprs) if len(child_exprs) > 1 else child_exprs[0]
            elif elem.combinator == "any_of":
                return z3.Or(*child_exprs) if len(child_exprs) > 1 else child_exprs[0]
            else:
                # Unknown combinator, treat as conjunction
                return z3.And(*child_exprs) if len(child_exprs) > 1 else child_exprs[0]

        return None

    def _translate_element_description(
        self, statute_id: str, elem_name: str, elem: "ElementNode"
    ) -> None:
        """
        Translate an element's description AST node to Z3 constraints.

        If the description is a MatchExprNode, translate each arm to a
        disjunctive constraint on the element's satisfaction.
        """
        if not Z3_AVAILABLE:
            return

        from yuho.ast.nodes import MatchExprNode, MatchArm, StringLit

        desc = elem.description
        if not isinstance(desc, MatchExprNode):
            return  # StringLit descriptions don't generate constraints

        var_name = f"{statute_id}_{elem_name}_satisfied"
        if var_name not in self._consts:
            return

        elem_var = self._consts[var_name]
        arm_constraints = []

        for arm in desc.arms:
            arm_c = self._translate_match_arm_to_constraint(statute_id, arm)
            if arm_c is not None:
                arm_constraints.append(arm_c)

        # If any arm is satisfiable, the element can be satisfied
        if arm_constraints:
            arm_disjunction = (
                z3.Or(*arm_constraints) if len(arm_constraints) > 1 else arm_constraints[0]
            )
            # Element satisfied => at least one arm condition holds
            self._assertions.append(z3.Implies(elem_var, arm_disjunction))

    def _translate_match_arm_to_constraint(self, statute_id: str, arm: "MatchArm") -> Optional[Any]:
        """Translate a single MatchArm to a Z3 constraint."""
        if not Z3_AVAILABLE:
            return None

        from yuho.ast.nodes import (
            WildcardPattern,
            LiteralPattern,
            BindingPattern,
            BinaryExprNode,
            UnaryExprNode,
            IdentifierNode,
            IntLit,
            BoolLit,
            StringLit,
        )

        # Wildcard matches everything
        if isinstance(arm.pattern, WildcardPattern):
            constraint = z3.BoolVal(True)
        elif isinstance(arm.pattern, LiteralPattern):
            lit = arm.pattern.literal
            if isinstance(lit, BoolLit):
                constraint = z3.BoolVal(lit.value)
            else:
                constraint = z3.BoolVal(True)
        elif isinstance(arm.pattern, BindingPattern):
            constraint = z3.BoolVal(True)
        else:
            constraint = z3.BoolVal(True)

        # Translate guard expression
        if arm.guard is not None:
            guard_c = self._translate_expr_to_z3(statute_id, arm.guard)
            if guard_c is not None:
                constraint = z3.And(constraint, guard_c) if constraint is not None else guard_c

        return constraint

    def _conviction_bool(self, section_ref: str) -> Any:
        """Return the Z3 Bool that represents `s<ref>_conviction`.

        Used to encode lam4-style ``is_infringed(sX)`` and Catala-style
        ``apply_scope(sX, ...)`` references. Declared lazily — when
        ``_generate_statute_constraints`` later defines the same Bool,
        both references point at the same Z3 atom (Z3 dedupes by name).

        ``section_ref`` is the canonical section number string the AST
        builder emits; we strip an optional leading ``s`` and replace
        ``.`` with ``_`` to mirror ``_generate_statute_constraints``.
        """
        if not Z3_AVAILABLE:
            return None
        ref = section_ref.lstrip("sS").replace(".", "_")
        name = f"{ref}_conviction"
        if name in self._consts:
            return self._consts[name]
        b = z3.Bool(name)
        self._consts[name] = b
        return b

    def _translate_expr_to_z3(self, statute_id: str, expr: "ASTNode") -> Optional[Any]:
        """Translate an AST expression node to a Z3 formula."""
        if not Z3_AVAILABLE:
            return None

        from yuho.ast.nodes import (
            BinaryExprNode,
            UnaryExprNode,
            IdentifierNode,
            IntLit,
            BoolLit,
            StringLit,
            FieldAccessNode,
            IsInfringedNode,
            ApplyScopeNode,
        )

        if isinstance(expr, BoolLit):
            return z3.BoolVal(expr.value)

        if isinstance(expr, IntLit):
            return z3.IntVal(expr.value)

        if isinstance(expr, StringLit):
            return z3.StringVal(expr.value)

        # Section-composition predicates. Both `is_infringed(sX)` and
        # `apply_scope(sX, …)` evaluate to the inner scope's
        # `overall_satisfied` — which in the Z3 model is the
        # `<sX>_conviction` Bool: elements all hold AND no defeating
        # exception fires. The Bool is declared lazily so the order in
        # which statutes get translated does not matter (z3.Bool dedupes
        # by name; if `_generate_statute_constraints` later declares
        # the same Bool, both references point at the same Z3 atom).
        if isinstance(expr, IsInfringedNode):
            return self._conviction_bool(expr.section_ref)

        if isinstance(expr, ApplyScopeNode):
            return self._conviction_bool(expr.section_ref)

        if isinstance(expr, IdentifierNode):
            name = f"{statute_id}_{expr.name}"
            if name in self._consts:
                return self._consts[name]
            # Create as bool variable
            var = z3.Bool(name)
            self._consts[name] = var
            return var

        if isinstance(expr, UnaryExprNode):
            operand = self._translate_expr_to_z3(statute_id, expr.operand)
            if operand is None:
                return None
            if expr.operator == "!":
                return z3.Not(operand)
            if expr.operator == "-":
                return -operand
            return None

        if isinstance(expr, BinaryExprNode):
            left = self._translate_expr_to_z3(statute_id, expr.left)
            right = self._translate_expr_to_z3(statute_id, expr.right)
            if left is None or right is None:
                return None
            op_map = {
                "&&": z3.And,
                "||": z3.Or,
                "==": lambda a, b: a == b,
                "!=": lambda a, b: a != b,
                "<": lambda a, b: a < b,
                ">": lambda a, b: a > b,
                "<=": lambda a, b: a <= b,
                ">=": lambda a, b: a >= b,
                "+": lambda a, b: a + b,
                "-": lambda a, b: a - b,
                "*": lambda a, b: a * b,
            }
            fn = op_map.get(expr.operator)
            if fn is not None:
                return fn(left, right)
            return None

        return None

    def _generate_exception_constraints(self, statute_id: str, statute: "StatuteNode") -> None:
        """
        Encode exception guards as Z3 implications.

        For each ExceptionNode: if exception guard is satisfied,
        then conviction is negated.
            exception_satisfied && NOT(defeated_by_higher) => NOT(conviction)

        G13: respect the `defeats` edges and the `priority` ordering. A higher-
        priority exception (lower priority integer, or explicit `defeats`)
        suppresses a lower-priority exception when both would fire — this
        encodes Catala-style default-logic / prioritised-rewriting semantics.
        """
        if not Z3_AVAILABLE:
            return

        conviction_key = f"{statute_id}_conviction"
        if conviction_key not in self._consts:
            return

        conviction_var = self._consts[conviction_key]

        # First pass: build exc_var per exception, with guard equivalence.
        exc_vars: dict[str, Any] = {}        # label -> z3 Bool
        exc_fires: dict[str, Any] = {}       # label -> z3 Bool (after priority suppression)
        label_of_index: list[str | None] = []
        priorities: dict[str, int] = {}
        defeats_of: dict[str, str] = {}
        for i, exc in enumerate(statute.exceptions):
            exc_label = exc.label or f"exception_{i}"
            safe_label = exc_label.replace(" ", "_").replace("-", "_")
            exc_var = z3.Bool(f"{statute_id}_exc_{safe_label}")
            self._consts[f"{statute_id}_exc_{safe_label}"] = exc_var
            exc_vars[exc_label] = exc_var
            label_of_index.append(exc_label)
            if exc.priority is not None:
                priorities[exc_label] = exc.priority
            if exc.defeats:
                defeats_of[exc_label] = exc.defeats

            if exc.guard is not None:
                guard_z3 = self._translate_expr_to_z3(statute_id, exc.guard)
                if guard_z3 is not None:
                    self._assertions.append(exc_var == guard_z3)

        # Second pass: compute "fires" for each exception — fires iff guard
        # satisfied AND not defeated by a higher-priority or explicitly-
        # dominating exception.
        for exc_label, exc_var in exc_vars.items():
            defeaters: list[Any] = []
            # explicit `defeats <me>` edges from other exceptions
            for other_label, other_defeats in defeats_of.items():
                if other_defeats == exc_label and other_label != exc_label:
                    defeaters.append(exc_vars[other_label])
            # implicit priority: lower priority integer = higher precedence
            my_pri = priorities.get(exc_label)
            if my_pri is not None:
                for other_label, other_pri in priorities.items():
                    if other_label == exc_label: continue
                    if other_pri < my_pri:  # other has higher precedence (lower number)
                        defeaters.append(exc_vars[other_label])

            if defeaters:
                # fires = exc_var AND NOT any defeater
                safe_label = exc_label.replace(" ", "_").replace("-", "_")
                fires_var = z3.Bool(f"{statute_id}_exc_{safe_label}_fires")
                self._consts[f"{statute_id}_exc_{safe_label}_fires"] = fires_var
                self._assertions.append(
                    fires_var == z3.And(exc_var, z3.Not(z3.Or(*defeaters)))
                )
                exc_fires[exc_label] = fires_var
            else:
                # no defeaters — fires == satisfied
                exc_fires[exc_label] = exc_var

        # Close the conviction biconditional now that the per-exception
        # `_fires` vars are settled. With elements_satisfied (asserted in
        # the caller) and the gathered fires list:
        #     conviction <=> elements_satisfied AND NOT (any fires)
        # If the statute has no exceptions, the second conjunct collapses
        # to True and we recover the original `conviction <=> elements`.
        elements_key = f"{statute_id}_elements_satisfied"
        elements_satisfied = self._consts.get(elements_key)
        if elements_satisfied is not None:
            if exc_fires:
                any_fires = (z3.Or(*exc_fires.values())
                             if len(exc_fires) > 1
                             else next(iter(exc_fires.values())))
                self._assertions.append(
                    conviction_var == z3.And(elements_satisfied, z3.Not(any_fires))
                )
            else:
                self._assertions.append(conviction_var == elements_satisfied)

    def _generate_penalty_constraints(self, statute_id: str, penalty: "PenaltyNode") -> None:
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
        from yuho.ast.nodes import (
            BuiltinType,
            NamedType,
            ArrayType,
            OptionalType,
            RefinementTypeNode,
        )

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

        elif isinstance(type_node, RefinementTypeNode):
            return self._type_to_sort(type_node.base_type)

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
            return [
                Z3Diagnostic(
                    check_name="z3_availability",
                    passed=False,
                    message="Z3 solver not available",
                )
            ]

        diagnostics: List[Z3Diagnostic] = []
        solver, assertions = self.generate(ast)

        if solver is None:
            return diagnostics

        extractor = Z3CounterexampleExtractor()

        # Check overall satisfiability
        result = solver.check()
        if result == z3.sat:
            diagnostics.append(
                Z3Diagnostic(
                    check_name="statute_consistency",
                    passed=True,
                    message="All statute constraints are satisfiable",
                )
            )
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
                diagnostics.append(
                    Z3Diagnostic(
                        check_name="statute_consistency",
                        passed=False,
                        message="Statute constraints are contradictory",
                    )
                )
        else:
            diagnostics.append(
                Z3Diagnostic(
                    check_name="statute_consistency",
                    passed=False,
                    message="Could not determine consistency (timeout or unknown)",
                )
            )

        # Check penalty ordering (if multiple statutes)
        if len(ast.statutes) > 1:
            penalty_check = self._check_penalty_ordering(ast)
            diagnostics.extend(penalty_check)

        # Cross-statute consistency (if multiple statutes)
        if len(ast.statutes) > 1:
            cross_diags = self.check_cross_statute_consistency(list(ast.statutes))
            diagnostics.extend(cross_diags)

        return diagnostics

    def check_cross_statute_consistency(self, statutes: List["StatuteNode"]) -> List[Z3Diagnostic]:
        """
        Check logical relationships across multiple statutes.

        Verifies implications such as:
        - If s300 (murder) conviction holds, then s299 (culpable homicide)
          conviction must also hold (murder is a subset of culpable homicide).
        - Penalty severity ordering is respected across related statutes.

        Args:
            statutes: List of StatuteNode instances to cross-check

        Returns:
            List of Z3Diagnostic results
        """
        if not Z3_AVAILABLE:
            return [
                Z3Diagnostic(
                    check_name="cross_statute_consistency",
                    passed=False,
                    message="Z3 not available",
                )
            ]

        diagnostics = []
        extractor = Z3CounterexampleExtractor()

        # Build conviction var lookup: section_number -> conviction var name
        conviction_map: Dict[str, str] = {}
        for s in statutes:
            sid = s.section_number.replace(".", "_")
            key = f"{sid}_conviction"
            if key in self._consts:
                conviction_map[s.section_number] = key

        # Detect subsumption relationships from statute metadata.
        # Heuristic: statutes whose definitions reference another
        # section number, or whose title references another offense,
        # imply the referenced offense.
        subsumption_pairs = self._detect_subsumption_pairs(statutes)

        for parent_sec, child_sec in subsumption_pairs:
            parent_key = conviction_map.get(parent_sec)
            child_key = conviction_map.get(child_sec)
            if parent_key is None or child_key is None:
                continue

            parent_var = self._consts[parent_key]
            child_var = self._consts[child_key]

            # parent conviction should imply child conviction
            # (e.g., murder => culpable homicide)
            check_solver = z3.Solver()
            check_solver.set("timeout", 5000)

            # Add all existing assertions as background
            for a in self._assertions:
                check_solver.add(a)

            # Check: is it possible for parent to be convicted but NOT child?
            check_solver.add(parent_var)
            check_solver.add(z3.Not(child_var))

            result = check_solver.check()
            check_name = f"cross_{parent_sec}_implies_{child_sec}"

            if result == z3.sat:
                model = check_solver.model()
                ce = extractor.model_to_counterexample(model)
                diagnostics.append(
                    Z3Diagnostic(
                        check_name=check_name,
                        passed=False,
                        counterexample=ce,
                        message=(
                            f"Conviction under s{parent_sec} does not imply "
                            f"conviction under s{child_sec}"
                        ),
                    )
                )
            elif result == z3.unsat:
                diagnostics.append(
                    Z3Diagnostic(
                        check_name=check_name,
                        passed=True,
                        message=(
                            f"Conviction under s{parent_sec} correctly implies "
                            f"conviction under s{child_sec}"
                        ),
                    )
                )
            else:
                diagnostics.append(
                    Z3Diagnostic(
                        check_name=check_name,
                        passed=False,
                        message="Solver returned unknown (timeout)",
                    )
                )

        # Penalty severity cross-check
        diagnostics.extend(self._check_cross_penalty_severity(statutes, subsumption_pairs))

        if not diagnostics:
            diagnostics.append(
                Z3Diagnostic(
                    check_name="cross_statute_consistency",
                    passed=True,
                    message=f"No cross-statute relationships detected among {len(statutes)} statutes",
                )
            )

        return diagnostics

    def _detect_subsumption_pairs(self, statutes: List["StatuteNode"]) -> List[Tuple[str, str]]:
        """
        Detect (parent, child) pairs where parent offense subsumes child.

        Uses heuristics: checks definitions for section references,
        title containment (e.g., "Murder" definition mentions "Section 299").

        Returns:
            List of (parent_section, child_section) tuples
        """
        import re

        pairs: Set[Tuple[str, str]] = set()
        section_nums = {s.section_number for s in statutes}

        for statute in statutes:
            direct_parent = getattr(statute, "subsumes", None)
            if (
                isinstance(direct_parent, str)
                and direct_parent in section_nums
                and direct_parent != statute.section_number
            ):
                pairs.add((statute.section_number, direct_parent))

            # Scan definitions for references to other section numbers
            for defn in statute.definitions:
                text = (
                    defn.definition.value
                    if hasattr(defn.definition, "value")
                    else str(defn.definition)
                )
                for ref_match in re.finditer(r"[Ss]ection\s+(\d+[A-Za-z]*)", text):
                    ref_sec = ref_match.group(1)
                    if ref_sec in section_nums and ref_sec != statute.section_number:
                        pairs.add((statute.section_number, ref_sec))

        return sorted(pairs)

    def _check_cross_penalty_severity(
        self,
        statutes: List["StatuteNode"],
        subsumption_pairs: List[Tuple[str, str]],
    ) -> List[Z3Diagnostic]:
        """Check that parent offenses have >= penalty maximums than child offenses."""
        diagnostics: List[Z3Diagnostic] = []

        statute_map = {s.section_number: s for s in statutes}

        for parent_sec, child_sec in subsumption_pairs:
            parent = statute_map.get(parent_sec)
            child = statute_map.get(child_sec)
            if parent is None or child is None:
                continue
            if parent.penalty is None or child.penalty is None:
                continue

            # Compare imprisonment maximums
            p_max = parent.penalty.imprisonment_max
            c_max = child.penalty.imprisonment_max
            if p_max is not None and c_max is not None:
                if p_max.total_days() < c_max.total_days():
                    diagnostics.append(
                        Z3Diagnostic(
                            check_name=f"penalty_severity_{parent_sec}_vs_{child_sec}",
                            passed=False,
                            message=(
                                f"s{parent_sec} max imprisonment ({p_max.total_days()} days) "
                                f"< s{child_sec} max ({c_max.total_days()} days)"
                            ),
                        )
                    )
                else:
                    diagnostics.append(
                        Z3Diagnostic(
                            check_name=f"penalty_severity_{parent_sec}_vs_{child_sec}",
                            passed=True,
                            message="Penalty severity ordering is correct",
                        )
                    )

        return diagnostics

    def _check_penalty_ordering(self, ast: "ModuleNode") -> List[Z3Diagnostic]:
        """Check that penalty ranges don't have unexpected overlaps."""
        diagnostics: List[Z3Diagnostic] = []

        statutes_with_penalties = [s for s in ast.statutes if s.penalty is not None]
        if len(statutes_with_penalties) < 2:
            return diagnostics

        statute_map = {statute.section_number: statute for statute in ast.statutes}
        related_pairs = self._detect_subsumption_pairs(list(ast.statutes))

        comparable_pairs = 0
        for parent_sec, child_sec in related_pairs:
            parent = statute_map.get(parent_sec)
            child = statute_map.get(child_sec)
            if parent is None or child is None or parent.penalty is None or child.penalty is None:
                continue

            comparable_pairs += 1
            issues = self._describe_penalty_ordering_issues(parent.penalty, child.penalty)
            if issues:
                diagnostics.append(
                    Z3Diagnostic(
                        check_name=f"penalty_ordering_{parent_sec}_vs_{child_sec}",
                        passed=False,
                        message=(
                            f"s{parent_sec} subsumes s{child_sec} but its penalty structure is weaker "
                            f"or indistinguishable: {'; '.join(issues)}"
                        ),
                        source_location=getattr(parent.penalty, "source_location", None),
                    )
                )
                continue

            diagnostics.append(
                Z3Diagnostic(
                    check_name=f"penalty_ordering_{parent_sec}_vs_{child_sec}",
                    passed=True,
                    message=f"s{parent_sec} preserves a stronger or distinguishable penalty than s{child_sec}",
                    source_location=getattr(parent.penalty, "source_location", None),
                )
            )

        diagnostics.append(
            Z3Diagnostic(
                check_name="penalty_ordering_summary",
                passed=True,
                message=(
                    f"Analyzed {len(statutes_with_penalties)} statutes with penalties across "
                    f"{comparable_pairs} comparable related-statute pair"
                    f"{'' if comparable_pairs == 1 else 's'}"
                ),
            )
        )

        return diagnostics

    def _describe_penalty_ordering_issues(
        self, parent: "PenaltyNode", child: "PenaltyNode"
    ) -> List[str]:
        """Return human-readable issues when a subsuming offense is not more severe."""
        issues: List[str] = []

        parent_imprisonment = self._penalty_imprisonment_bounds(parent)
        child_imprisonment = self._penalty_imprisonment_bounds(child)
        if parent_imprisonment is not None and child_imprisonment is not None:
            _, parent_max = parent_imprisonment
            _, child_max = child_imprisonment
            if parent_max < child_max:
                issues.append(
                    f"max imprisonment {parent_max} days is below child max {child_max} days"
                )
            elif parent_imprisonment == child_imprisonment:
                issues.append("imprisonment range is identical")

        parent_fine = self._penalty_fine_bounds(parent)
        child_fine = self._penalty_fine_bounds(child)
        if parent_fine is not None and child_fine is not None:
            _, parent_max = parent_fine
            _, child_max = child_fine
            if parent_max < child_max:
                issues.append(f"max fine {parent_max} cents is below child max {child_max} cents")
            elif parent_fine == child_fine:
                issues.append("fine range is identical")

        if child.death_penalty and not parent.death_penalty:
            issues.append("child statute allows death penalty but parent does not")
        elif parent.death_penalty is not None and parent.death_penalty == child.death_penalty:
            issues.append("death-penalty exposure is identical")

        if parent.caning_max is not None and child.caning_max is not None:
            if parent.caning_max < child.caning_max:
                issues.append(
                    f"max caning {parent.caning_max} strokes is below child max {child.caning_max}"
                )
            elif parent.caning_min == child.caning_min and parent.caning_max == child.caning_max:
                issues.append("caning range is identical")

        if issues and not self._has_penalty_distinction(parent, child):
            issues.append("no distinguishing penalty feature remains between the two statutes")

        return issues

    def _has_penalty_distinction(self, parent: "PenaltyNode", child: "PenaltyNode") -> bool:
        """Check whether any declared penalty dimension differentiates the statutes."""
        return any(
            (
                self._penalty_imprisonment_bounds(parent)
                != self._penalty_imprisonment_bounds(child),
                self._penalty_fine_bounds(parent) != self._penalty_fine_bounds(child),
                (parent.caning_min, parent.caning_max) != (child.caning_min, child.caning_max),
                parent.death_penalty != child.death_penalty,
                parent.supplementary != child.supplementary,
                parent.sentencing != child.sentencing,
                parent.mandatory_min_imprisonment != child.mandatory_min_imprisonment,
                parent.mandatory_min_fine != child.mandatory_min_fine,
            )
        )

    def _penalty_imprisonment_bounds(self, penalty: "PenaltyNode") -> Optional[Tuple[int, int]]:
        """Return imprisonment bounds in days when a statute declares them."""
        min_days = (
            penalty.imprisonment_min.total_days() if penalty.imprisonment_min is not None else 0
        )
        max_duration = penalty.imprisonment_max or penalty.imprisonment_min
        if max_duration is None:
            return None
        return min_days, max_duration.total_days()

    def _penalty_fine_bounds(self, penalty: "PenaltyNode") -> Optional[Tuple[int, int]]:
        """Return fine bounds in cents when a statute declares them."""
        min_cents = int(penalty.fine_min.amount * 100) if penalty.fine_min is not None else 0
        max_fine = penalty.fine_max or penalty.fine_min
        if max_fine is None:
            return None
        return min_cents, int(max_fine.amount * 100)
