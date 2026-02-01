"""
Alloy transpiler - formal verification model generation.

Converts Yuho AST to Alloy specifications for bounded model checking.
"""

from typing import List, Set, Dict, Optional

from yuho.ast import nodes
from yuho.ast.visitor import Visitor
from yuho.transpile.base import TranspileTarget, TranspilerBase


class AlloyTranspiler(TranspilerBase, Visitor):
    """
    Transpile Yuho AST to Alloy specification language.

    Generates:
    - sig declarations from struct definitions
    - fact constraints from statute elements
    - pred functions from function definitions
    - assert statements for cross-statute consistency
    """

    def __init__(self):
        self._output: List[str] = []
        self._indent = 0
        self._known_sigs: Set[str] = set()

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.ALLOY

    def transpile(self, ast: nodes.ModuleNode) -> str:
        """Transpile AST to Alloy specification."""
        self._output = []
        self._indent = 0
        self._known_sigs = set()

        # Module header
        self._emit("-- Alloy specification generated from Yuho")
        self._emit("-- Formal verification model for legal statutes")
        self._emit("")

        # Built-in types
        self._emit_builtins()

        # Struct definitions -> sig declarations
        for struct in ast.type_defs:
            self._transpile_struct(struct)
            self._emit("")

        # Function definitions -> pred declarations
        for func in ast.function_defs:
            self._transpile_function(func)
            self._emit("")

        # Statutes -> facts and assertions
        for statute in ast.statutes:
            self._transpile_statute(statute)
            self._emit("")

        # Cross-statute consistency assertions
        if len(ast.statutes) > 1:
            self._emit_consistency_assertions(ast.statutes)

        # Run commands
        self._emit_run_commands(ast)

        return "\n".join(self._output)

    def _emit(self, line: str = "") -> None:
        """Add a line to output with indentation."""
        if line:
            indent = "  " * self._indent
            self._output.append(f"{indent}{line}")
        else:
            self._output.append("")

    def _emit_builtins(self) -> None:
        """Emit built-in type signatures."""
        self._emit("-- Built-in types")
        self._emit("sig Bool {}")
        self._emit("one sig True, False extends Bool {}")
        self._emit("")
        self._emit("sig Money {")
        self._indent += 1
        self._emit("amount: Int")
        self._indent -= 1
        self._emit("}")
        self._emit("")
        self._emit("sig Duration {")
        self._indent += 1
        self._emit("years: Int,")
        self._emit("months: Int,")
        self._emit("days: Int")
        self._indent -= 1
        self._emit("}")
        self._emit("")
        self._emit("sig Percent {")
        self._indent += 1
        self._emit("value: Int")
        self._indent -= 1
        self._emit("}")
        self._emit("")
        self._emit("-- Percent must be 0-100")
        self._emit("fact PercentRange {")
        self._indent += 1
        self._emit("all p: Percent | p.value >= 0 and p.value <= 100")
        self._indent -= 1
        self._emit("}")
        self._emit("")

        # Track built-in sigs
        self._known_sigs.update(["Bool", "True", "False", "Money", "Duration", "Percent"])

    # =========================================================================
    # Struct -> sig
    # =========================================================================

    def _transpile_struct(self, struct: nodes.StructDefNode) -> None:
        """Generate Alloy sig from struct definition."""
        self._emit(f"-- Type: {struct.name}")
        self._emit(f"sig {struct.name} {{")
        self._indent += 1

        for i, field in enumerate(struct.fields):
            field_type = self._type_to_alloy(field.type_annotation)
            comma = "," if i < len(struct.fields) - 1 else ""
            self._emit(f"{field.name}: {field_type}{comma}")

        self._indent -= 1
        self._emit("}")

        self._known_sigs.add(struct.name)

    def _type_to_alloy(self, typ: nodes.TypeNode) -> str:
        """Convert Yuho type to Alloy type."""
        if isinstance(typ, nodes.BuiltinType):
            type_map = {
                "int": "Int",
                "float": "Int",  # Alloy doesn't have floats
                "bool": "Bool",
                "string": "String",  # May need to be modeled
                "money": "Money",
                "percent": "Percent",
                "date": "Int",  # Model as day count
                "duration": "Duration",
                "void": "none",
            }
            return type_map.get(typ.name, "univ")
        elif isinstance(typ, nodes.NamedType):
            return typ.name
        elif isinstance(typ, nodes.OptionalType):
            inner = self._type_to_alloy(typ.inner)
            return f"lone {inner}"
        elif isinstance(typ, nodes.ArrayType):
            elem = self._type_to_alloy(typ.element_type)
            return f"set {elem}"
        elif isinstance(typ, nodes.GenericType):
            # Simplify generics
            return typ.base
        else:
            return "univ"

    # =========================================================================
    # Function -> pred
    # =========================================================================

    def _transpile_function(self, func: nodes.FunctionDefNode) -> None:
        """Generate Alloy pred from function definition."""
        self._emit(f"-- Function: {func.name}")

        # Build parameter list
        params = []
        for param in func.params:
            param_type = self._type_to_alloy(param.type_annotation)
            params.append(f"{param.name}: {param_type}")

        param_str = ", ".join(params) if params else ""

        self._emit(f"pred {func.name}[{param_str}] {{")
        self._indent += 1

        # Transpile body
        for stmt in func.body.statements:
            self._transpile_statement(stmt)

        # If empty, add trivial constraint
        if not func.body.statements:
            self._emit("some univ")

        self._indent -= 1
        self._emit("}")

    def _transpile_statement(self, stmt: nodes.ASTNode) -> None:
        """Transpile statement to Alloy constraint."""
        if isinstance(stmt, nodes.ReturnStmt):
            if stmt.value:
                expr = self._expr_to_alloy(stmt.value)
                self._emit(f"-- return: {expr}")
        elif isinstance(stmt, nodes.ExpressionStmt):
            expr = self._expr_to_alloy(stmt.expression)
            if isinstance(stmt.expression, nodes.MatchExprNode):
                self._transpile_match_as_constraint(stmt.expression)
            else:
                self._emit(expr)
        elif isinstance(stmt, nodes.VariableDecl):
            typ = self._type_to_alloy(stmt.type_annotation)
            if stmt.value:
                val = self._expr_to_alloy(stmt.value)
                self._emit(f"some {stmt.name}: {typ} | {stmt.name} = {val}")
            else:
                self._emit(f"some {stmt.name}: {typ}")

    # =========================================================================
    # Statute -> facts
    # =========================================================================

    def _transpile_statute(self, statute: nodes.StatuteNode) -> None:
        """Generate Alloy facts from statute."""
        title = statute.title.value if statute.title else statute.section_number
        safe_name = self._safe_name(statute.section_number)

        self._emit(f"-- Statute: Section {statute.section_number} - {title}")

        # Create sig for offense
        self._emit(f"sig {safe_name}Offense {{")
        self._indent += 1

        # Fields for each element
        for elem in statute.elements:
            elem_name = self._safe_name(elem.name)
            self._emit(f"{elem_name}: Bool,")

        # Add penalty fields if present
        if statute.penalty:
            if statute.penalty.imprisonment_max:
                self._emit("imprisonmentApplies: Bool,")
            if statute.penalty.fine_max:
                self._emit("fineApplies: Bool,")

        self._emit("guilty: Bool")
        self._indent -= 1
        self._emit("}")
        self._emit("")

        self._known_sigs.add(f"{safe_name}Offense")

        # Facts for element requirements
        self._emit(f"fact {safe_name}ElementRequirements {{")
        self._indent += 1

        # All elements must be true for guilt (conjunction)
        actus_reus_elems = [self._safe_name(e.name) for e in statute.elements if e.element_type == "actus_reus"]
        mens_rea_elems = [self._safe_name(e.name) for e in statute.elements if e.element_type == "mens_rea"]

        self._emit(f"all o: {safe_name}Offense |")
        self._indent += 1

        conditions = []
        for elem in statute.elements:
            elem_name = self._safe_name(elem.name)
            conditions.append(f"o.{elem_name} = True")

        if conditions:
            condition_str = " and\n    ".join(conditions)
            self._emit(f"o.guilty = True iff ({condition_str})")
        else:
            self._emit("o.guilty = True")

        self._indent -= 2
        self._emit("}")
        self._emit("")

        # Generate match expression constraints
        for elem in statute.elements:
            if isinstance(elem.description, nodes.MatchExprNode):
                self._emit(f"-- Element: {elem.name}")
                self._emit(f"fact {safe_name}_{self._safe_name(elem.name)} {{")
                self._indent += 1
                self._transpile_match_as_constraint(elem.description)
                self._indent -= 1
                self._emit("}")
                self._emit("")

    def _transpile_match_as_constraint(self, match: nodes.MatchExprNode) -> None:
        """Convert match expression to Alloy disjunction constraint."""
        if not match.arms:
            self._emit("some univ")
            return

        # Each arm becomes a disjunct
        arm_constraints = []
        for arm in match.arms:
            pattern_constraint = self._pattern_to_constraint(arm.pattern)
            guard_constraint = self._expr_to_alloy(arm.guard) if arm.guard else "some univ"
            body_constraint = self._expr_to_alloy(arm.body)

            if isinstance(arm.pattern, nodes.WildcardPattern):
                # Wildcard is the default case
                arm_constraints.append(f"({body_constraint})")
            else:
                arm_constraints.append(f"({pattern_constraint} and {guard_constraint} implies {body_constraint})")

        self._emit(" or\n    ".join(arm_constraints))

    def _pattern_to_constraint(self, pattern: nodes.PatternNode) -> str:
        """Convert pattern to Alloy constraint."""
        if isinstance(pattern, nodes.WildcardPattern):
            return "some univ"
        elif isinstance(pattern, nodes.LiteralPattern):
            return self._expr_to_alloy(pattern.literal)
        elif isinstance(pattern, nodes.BindingPattern):
            return f"some {pattern.name}"
        elif isinstance(pattern, nodes.StructPattern):
            fields = " and ".join(f"some _.{fp.name}" for fp in pattern.fields)
            return f"some _: {pattern.type_name} | {fields}"
        else:
            return "some univ"

    def _expr_to_alloy(self, expr: nodes.ASTNode) -> str:
        """Convert expression to Alloy."""
        if isinstance(expr, nodes.IntLit):
            return str(expr.value)
        elif isinstance(expr, nodes.FloatLit):
            return str(int(expr.value))  # Truncate to int
        elif isinstance(expr, nodes.BoolLit):
            return "True" if expr.value else "False"
        elif isinstance(expr, nodes.StringLit):
            # Strings need to be modeled; use placeholder
            return f'"{expr.value}"'
        elif isinstance(expr, nodes.IdentifierNode):
            return expr.name
        elif isinstance(expr, nodes.FieldAccessNode):
            base = self._expr_to_alloy(expr.base)
            return f"{base}.{expr.field_name}"
        elif isinstance(expr, nodes.BinaryExprNode):
            left = self._expr_to_alloy(expr.left)
            right = self._expr_to_alloy(expr.right)
            op = self._op_to_alloy(expr.operator)
            return f"({left} {op} {right})"
        elif isinstance(expr, nodes.UnaryExprNode):
            operand = self._expr_to_alloy(expr.operand)
            if expr.operator == "!":
                return f"not {operand}"
            return f"({expr.operator}{operand})"
        elif isinstance(expr, nodes.PassExprNode):
            return "none"
        elif isinstance(expr, nodes.FunctionCallNode):
            callee = self._expr_to_alloy(expr.callee)
            args = ", ".join(self._expr_to_alloy(a) for a in expr.args)
            return f"{callee}[{args}]"
        else:
            return "some univ"

    def _op_to_alloy(self, op: str) -> str:
        """Convert operator to Alloy operator."""
        op_map = {
            "+": "add",
            "-": "sub",
            "*": "mul",
            "/": "div",
            "==": "=",
            "!=": "!=",
            "<": "<",
            ">": ">",
            "<=": "<=",
            ">=": ">=",
            "&&": "and",
            "||": "or",
        }
        return op_map.get(op, op)

    # =========================================================================
    # Assertions
    # =========================================================================

    def _emit_consistency_assertions(self, statutes: tuple) -> None:
        """Emit cross-statute consistency assertions."""
        self._emit("-- Cross-statute consistency assertions")
        self._emit("")

        # Assert: no contradictory elements
        self._emit("assert NoContradictoryElements {")
        self._indent += 1
        self._emit("-- No offense can have contradictory required elements")
        self._emit("-- (This is a placeholder; specific contradictions should be modeled)")
        self._emit("some univ")
        self._indent -= 1
        self._emit("}")
        self._emit("")

        # Assert: penalty ordering (more serious offenses have higher penalties)
        if len(statutes) >= 2:
            self._emit("assert PenaltyOrdering {")
            self._indent += 1
            self._emit("-- More serious offenses should have higher or equal penalties")
            self._emit("-- (Specific ordering relationships should be modeled)")
            self._emit("some univ")
            self._indent -= 1
            self._emit("}")
            self._emit("")

    def _emit_run_commands(self, ast: nodes.ModuleNode) -> None:
        """
        Emit run and check commands for bounded model checking.
        
        Generates:
        - run commands to find satisfying instances
        - check commands to verify assertions
        - parameterized scope bounds
        """
        self._emit("-- =========================================================================")
        self._emit("-- Verification commands for bounded model checking")
        self._emit("-- =========================================================================")
        self._emit("")
        
        # Configuration comment
        self._emit("-- Scope configuration (adjust bounds as needed)")
        self._emit("-- Default scope is 5 atoms per sig, Int scope is 4 bits (-8 to 7)")
        self._emit("")
        
        # Run commands for finding satisfying offense instances
        self._emit("-- Run commands: find satisfying instances")
        for statute in ast.statutes:
            safe_name = self._safe_name(statute.section_number)
            offense_sig = f"{safe_name}Offense"
            
            # Basic run: find any instance
            self._emit(f"run show{safe_name}Instance {{")
            self._indent += 1
            self._emit(f"some o: {offense_sig} | o.guilty = True")
            self._indent -= 1
            self._emit("} for 3 but 4 Int")
            self._emit("")
            
            # Run with all elements satisfied
            self._emit(f"run show{safe_name}GuiltyScenario {{")
            self._indent += 1
            self._emit(f"some o: {offense_sig} |")
            self._indent += 1
            conditions = [f"o.{self._safe_name(e.name)} = True" for e in statute.elements]
            if conditions:
                self._emit(" and ".join(conditions))
            else:
                self._emit("o.guilty = True")
            self._indent -= 1
            self._indent -= 1
            self._emit("} for 5 but 4 Int")
            self._emit("")
            
            # Run to find innocent scenario (not guilty)
            self._emit(f"run show{safe_name}InnocentScenario {{")
            self._indent += 1
            self._emit(f"some o: {offense_sig} | o.guilty = False")
            self._indent -= 1
            self._emit("} for 3 but 4 Int")
            self._emit("")
        
        # Check commands for assertions
        self._emit("-- Check commands: verify assertions with counterexample search")
        self._emit("")
        
        # Check element consistency
        for statute in ast.statutes:
            safe_name = self._safe_name(statute.section_number)
            offense_sig = f"{safe_name}Offense"
            
            # Check that guilty implies all elements true
            self._emit(f"assert {safe_name}GuiltyImpliesElements {{")
            self._indent += 1
            self._emit(f"all o: {offense_sig} | o.guilty = True implies (")
            self._indent += 1
            conditions = [f"o.{self._safe_name(e.name)} = True" for e in statute.elements]
            if conditions:
                self._emit(" and ".join(conditions))
            else:
                self._emit("True = True")  # Trivially true
            self._indent -= 1
            self._emit(")")
            self._indent -= 1
            self._emit("}")
            self._emit(f"check {safe_name}GuiltyImpliesElements for 5 but 4 Int")
            self._emit("")
            
            # Check that all elements true implies guilty
            if statute.elements:
                self._emit(f"assert {safe_name}ElementsImplyGuilty {{")
                self._indent += 1
                self._emit(f"all o: {offense_sig} | (")
                self._indent += 1
                self._emit(" and ".join(conditions))
                self._indent -= 1
                self._emit(f") implies o.guilty = True")
                self._indent -= 1
                self._emit("}")
                self._emit(f"check {safe_name}ElementsImplyGuilty for 5 but 4 Int")
                self._emit("")
        
        # Global consistency assertions
        self._emit("check NoContradictoryElements for 5 but 4 Int")
        if len(ast.statutes) >= 2:
            self._emit("check PenaltyOrdering for 5 but 4 Int")
        self._emit("")
        
        # Negative checks (looking for counterexamples to impossibilities)
        self._emit("-- Negative checks: these should find NO counterexamples")
        for statute in ast.statutes:
            safe_name = self._safe_name(statute.section_number)
            offense_sig = f"{safe_name}Offense"
            
            # Check: it's impossible to be guilty with no elements satisfied
            if statute.elements:
                self._emit(f"assert {safe_name}NoElementsNoGuilt {{")
                self._indent += 1
                no_conditions = [f"o.{self._safe_name(e.name)} = False" for e in statute.elements]
                self._emit(f"all o: {offense_sig} | (")
                self._indent += 1
                self._emit(" and ".join(no_conditions))
                self._indent -= 1
                self._emit(") implies o.guilty = False")
                self._indent -= 1
                self._emit("}")
                self._emit(f"check {safe_name}NoElementsNoGuilt for 5 but 4 Int")
                self._emit("")
        
        # Exhaustive exploration hint
        self._emit("-- =========================================================================")
        self._emit("-- To run in Alloy Analyzer:")
        self._emit("--   1. Open this file in Alloy Analyzer")
        self._emit("--   2. Execute 'run' commands to find satisfying instances")
        self._emit("--   3. Execute 'check' commands to verify assertions")
        self._emit("--   4. Green checkmark = assertion holds within scope")
        self._emit("--   5. Red X = counterexample found (click to view)")
        self._emit("-- =========================================================================")

    def _safe_name(self, name: str) -> str:
        """Convert name to safe Alloy identifier."""
        # Remove special chars, capitalize
        safe = "".join(c if c.isalnum() else "_" for c in name)
        # Ensure starts with letter
        if safe and safe[0].isdigit():
            safe = "S" + safe
        return safe

