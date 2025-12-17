"""
Alloy Transpiler for Yuho
Generates Alloy specifications from Yuho AST for formal verification
"""

from typing import List, Dict, Set
from ..ast_nodes import *

class AlloyTranspiler:
    """Transpiles Yuho AST to Alloy specification language"""

    def __init__(self):
        self.signatures = []
        self.facts = []
        self.predicates = []
        self.functions = []

    def transpile(self, program: Program) -> str:
        """
        Generate Alloy specification from Yuho program

        Args:
            program: Yuho Program AST

        Returns:
            Alloy specification text
        """
        self.signatures = []
        self.facts = []
        self.predicates = []
        self.functions = []

        # Process all statements
        for stmt in program.statements:
            self._process_statement(stmt)

        # Generate final Alloy code
        return self._generate_alloy_code()

    def _process_statement(self, stmt: Statement):
        """Process a statement for Alloy generation"""
        if isinstance(stmt, StructDefinition):
            self._process_struct_definition(stmt)
        elif isinstance(stmt, MatchCase):
            self._process_match_case(stmt)
        elif isinstance(stmt, FunctionDefinition):
            self._process_function_definition(stmt)

    def _process_struct_definition(self, struct: StructDefinition):
        """Convert struct definition to Alloy signature"""
        sig_lines = [f"sig {struct.name} {{"]

        # Add fields
        for member in struct.members:
            alloy_type = self._get_alloy_type(member.type_node)
            sig_lines.append(f"  {member.name}: {alloy_type},")

        # Remove last comma and close signature
        if sig_lines[-1].endswith(','):
            sig_lines[-1] = sig_lines[-1][:-1]

        sig_lines.append("}")

        self.signatures.append("\\n".join(sig_lines))

    def _process_match_case(self, match_case: MatchCase):
        """Convert match-case to Alloy predicates"""
        pred_name = f"MatchCase{len(self.predicates)}"
        pred_lines = [f"pred {pred_name}[x: univ] {{"]

        if match_case.expression:
            # Add condition for the expression being matched
            pred_lines.append("  // Match expression conditions")

        # Process each case
        for i, case in enumerate(match_case.cases):
            if case.condition is None:
                # Default case
                pred_lines.append("  // Default case")
                pred_lines.append("  else {")
            else:
                # Specific case condition
                condition_alloy = self._expression_to_alloy(case.condition)
                if i == 0:
                    pred_lines.append(f"  {condition_alloy} => {{")
                else:
                    pred_lines.append(f"  else {condition_alloy} => {{")

            # Add consequence
            if not isinstance(case.consequence, PassStatement):
                consequence_alloy = self._expression_to_alloy(case.consequence)
                pred_lines.append(f"    {consequence_alloy}")

            pred_lines.append("  }")

        pred_lines.append("}")
        self.predicates.append("\\n".join(pred_lines))

    def _process_function_definition(self, func: FunctionDefinition):
        """Convert function definition to Alloy function"""
        # Create parameter list
        params = []
        for param in func.parameters:
            alloy_type = self._get_alloy_type(param.type_node)
            params.append(f"{param.name}: {alloy_type}")

        param_str = ", ".join(params)
        return_type = self._get_alloy_type(func.return_type)

        func_lines = [f"fun {func.name}[{param_str}]: {return_type} {{"]

        # For now, just add a placeholder body
        func_lines.append("  // Function body would be implemented here")

        func_lines.append("}")
        self.functions.append("\\n".join(func_lines))

    def _expression_to_alloy(self, expr: Expression) -> str:
        """Convert expression to Alloy syntax"""
        if isinstance(expr, Literal):
            return self._literal_to_alloy(expr)
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, BinaryOperation):
            left = self._expression_to_alloy(expr.left)
            right = self._expression_to_alloy(expr.right)
            op = self._operator_to_alloy(expr.operator)
            return f"({left} {op} {right})"
        else:
            return "// Expression translation not implemented"

    def _literal_to_alloy(self, literal: Literal) -> str:
        """Convert literal value to Alloy representation"""
        if literal.literal_type == YuhoType.BOOL:
            return "True" if literal.value else "False"
        elif literal.literal_type == YuhoType.STRING:
            return f'"{literal.value}"'
        elif literal.literal_type in [YuhoType.INT, YuhoType.FLOAT]:
            return str(literal.value)
        else:
            return f"// {literal.value}"

    def _operator_to_alloy(self, operator: Operator) -> str:
        """Convert Yuho operator to Alloy operator"""
        mapping = {
            Operator.PLUS: "add",
            Operator.MINUS: "sub",
            Operator.MULT: "mul",
            Operator.DIV: "div",
            Operator.EQUAL: "=",
            Operator.NOTEQUAL: "!=",
            Operator.GT: ">",
            Operator.LT: "<",
            Operator.AND: "and",
            Operator.OR: "or"
        }
        return mapping.get(operator, str(operator.value))

    def _get_alloy_type(self, type_node: TypeNode) -> str:
        """Convert Yuho type to Alloy type"""
        if isinstance(type_node.type_name, YuhoType):
            mapping = {
                YuhoType.INT: "Int",
                YuhoType.FLOAT: "Int",  # Alloy doesn't have floats
                YuhoType.BOOL: "Bool",
                YuhoType.STRING: "String",
                YuhoType.PERCENT: "Int",
                YuhoType.MONEY: "Int",
                YuhoType.DATE: "String",
                YuhoType.DURATION: "String"
            }
            return mapping.get(type_node.type_name, "univ")
        else:
            # Custom type
            return str(type_node.type_name)

    def _generate_alloy_code(self) -> str:
        """Generate complete Alloy specification"""
        lines = []

        # Add module header
        lines.append("// Generated Alloy specification from Yuho")
        lines.append("module YuhoGenerated")
        lines.append("")

        # Add standard predicates for boolean values
        lines.append("abstract sig Bool {}")
        lines.append("one sig True, False extends Bool {}")
        lines.append("")

        # Add signatures
        for sig in self.signatures:
            lines.append(sig)
            lines.append("")

        # Add functions
        for func in self.functions:
            lines.append(func)
            lines.append("")

        # Add predicates
        for pred in self.predicates:
            lines.append(pred)
            lines.append("")

        # Add facts if any
        for fact in self.facts:
            lines.append(fact)
            lines.append("")

        # Add basic run command
        lines.append("// Run command to check satisfiability")
        lines.append("run {} for 5")

        return "\\n".join(lines)