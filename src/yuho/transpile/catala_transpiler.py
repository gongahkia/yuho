"""
Catala transpiler -- export statute logic as Catala declarations.

Generates Catala (https://catala-lang.org/) compatible output with:
- Scope declarations for statutes
- Data structures for definitions/elements
- Rules for element satisfaction
- Exception handling via Catala's exception mechanism
"""

from typing import List

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


class CatalaTranspiler(TranspilerBase):
    """Transpile Yuho AST to Catala legal DSL."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.CATALA

    def transpile(self, ast: nodes.ModuleNode) -> str:
        lines: List[str] = []
        lines.append("> Auto-generated Catala from Yuho statutes")
        lines.append("> Do not edit manually")
        lines.append("")
        for struct in ast.type_defs:
            self._emit_struct(lines, struct)
        for enum in ast.enum_defs:
            self._emit_enum(lines, enum)
        for statute in ast.statutes:
            self._emit_statute(lines, statute)
        for lt in getattr(ast, 'legal_tests', ()):
            self._emit_legal_test(lines, lt)
        for cc in getattr(ast, 'conflict_checks', ()):
            self._emit_conflict_check(lines, cc)
        return "\n".join(lines)

    def _emit_struct(self, lines: List[str], struct: nodes.StructDefNode) -> None:
        lines.append(f"declaration structure {struct.name}:")
        for f in struct.fields:
            ctype = self._catala_type(f.type_annotation)
            lines.append(f"  data {f.name} content {ctype}")
        lines.append("")

    def _emit_enum(self, lines: List[str], enum: nodes.EnumDefNode) -> None:
        lines.append(f"declaration enumeration {enum.name}:")
        for v in enum.variants:
            if v.payload_types:
                ptypes = " content " + " * ".join(self._catala_type(t) for t in v.payload_types)
            else:
                ptypes = ""
            lines.append(f"  -- {v.name}{ptypes}")
        lines.append("")

    def _emit_statute(self, lines: List[str], statute: nodes.StatuteNode) -> None:
        sec = self._safe_name(statute.section_number)
        title = statute.title.value if statute.title else sec
        lines.append(f"## Section {statute.section_number}: {title}")
        lines.append("")
        lines.append("```catala")
        # annotations
        for ann in getattr(statute, 'annotations', ()):
            args = ", ".join(f'"{a}"' for a in ann.args)
            lines.append(f"# @{ann.name}({args})")
        # scope declaration
        lines.append(f"declaration scope Section{sec}:")
        # definitions as context variables
        for defn in statute.definitions:
            lines.append(f"  context {self._safe_name(defn.term)} content text")
        # elements as context variables
        flat = self._flatten_elements(statute.elements)
        for elem in flat:
            lines.append(f"  context {self._safe_name(elem.name)} content boolean")
        # guilt output
        lines.append(f"  context guilty content boolean")
        # penalty output
        if statute.penalty:
            lines.append(f"  context penalty_applies content boolean")
        lines.append("")
        # scope body
        lines.append(f"scope Section{sec}:")
        # definition rules
        for defn in statute.definitions:
            name = self._safe_name(defn.term)
            val = self._safe_str(defn.definition.value)
            lines.append(f'  definition {name} equals "{val}"')
        lines.append("")
        # element descriptions
        for elem in flat:
            name = self._safe_name(elem.name)
            desc = self._desc_text(elem.description)
            lines.append(f"  # {elem.element_type}: {desc}")
            if getattr(elem, 'burden', None):
                lines.append(f"  # burden: {elem.burden}")
        lines.append("")
        # guilt rule: all elements required
        if flat:
            conditions = " and\n    ".join(self._safe_name(e.name) for e in flat)
            lines.append(f"  definition guilty equals")
            lines.append(f"    {conditions}")
        lines.append("")
        # exceptions
        for i, exc in enumerate(statute.exceptions):
            label = exc.label or f"exception_{i}"
            lines.append(f"  exception {self._safe_name(label)}")
            lines.append(f"  definition guilty equals false")
            cond = exc.condition.value if hasattr(exc.condition, 'value') else str(exc.condition)
            lines.append(f'  # condition: "{cond}"')
            lines.append("")
        # illustrations as comments
        for ill in statute.illustrations:
            label = ill.label or "illustration"
            lines.append(f"  # {label}: {ill.description.value}")
        # caselaw as comments
        for cl in statute.case_law:
            cite = cl.citation.value if cl.citation else ""
            lines.append(f"  # caselaw: {cl.case_name.value} ({cite})")
            lines.append(f"  #   holding: {cl.holding.value}")
        lines.append("```")
        lines.append("")

    def _emit_legal_test(self, lines: List[str], lt: nodes.LegalTestNode) -> None:
        name = self._safe_name(lt.name)
        lines.append(f"```catala")
        lines.append(f"declaration scope LegalTest{name}:")
        for req in lt.requirements:
            if isinstance(req, nodes.VariableDecl):
                rtype = self._catala_type(req.type_annotation)
                lines.append(f"  context {self._safe_name(req.name)} content {rtype}")
        lines.append(f"  context test_satisfied content boolean")
        lines.append("")
        lines.append(f"scope LegalTest{name}:")
        if lt.condition:
            lines.append(f"  definition test_satisfied equals")
            lines.append(f"    {self._expr_to_catala(lt.condition)}")
        lines.append("```")
        lines.append("")

    def _emit_conflict_check(self, lines: List[str], cc: nodes.ConflictCheckNode) -> None:
        name = self._safe_name(cc.name)
        lines.append(f"```catala")
        lines.append(f"# Conflict check: {name}")
        lines.append(f'# source: "{cc.source}"')
        lines.append(f'# target: "{cc.target}"')
        lines.append(f"# Verify no contradictory elements between source and target")
        lines.append("```")
        lines.append("")

    def _expr_to_catala(self, expr: nodes.ASTNode) -> str:
        if isinstance(expr, nodes.BinaryExprNode):
            left = self._expr_to_catala(expr.left)
            right = self._expr_to_catala(expr.right)
            op = expr.operator
            if op == "&&":
                op = "and"
            elif op == "||":
                op = "or"
            return f"{left} {op} {right}"
        elif isinstance(expr, nodes.UnaryExprNode):
            operand = self._expr_to_catala(expr.operand)
            if expr.operator == "!":
                return f"not {operand}"
            return f"{expr.operator}{operand}"
        elif isinstance(expr, nodes.IdentifierNode):
            return self._safe_name(expr.name)
        elif isinstance(expr, nodes.BoolLit):
            return "true" if expr.value else "false"
        elif isinstance(expr, nodes.StringLit):
            return f'"{expr.value}"'
        elif isinstance(expr, nodes.IntLit):
            return str(expr.value)
        return "false"

    def _catala_type(self, t: nodes.TypeNode) -> str:
        if isinstance(t, nodes.BuiltinType):
            mapping = {
                "int": "integer", "float": "decimal", "bool": "boolean",
                "string": "text", "money": "money", "date": "date",
                "duration": "duration", "percent": "decimal", "void": "boolean",
            }
            return mapping.get(t.name, t.name)
        elif isinstance(t, nodes.NamedType):
            return t.name
        elif isinstance(t, nodes.ArrayType):
            return f"list of {self._catala_type(t.element_type)}"
        elif isinstance(t, nodes.OptionalType):
            return f"{self._catala_type(t.inner)} option"
        return "text"

    def _flatten_elements(self, elements) -> list:
        result = []
        for elem in elements:
            if isinstance(elem, nodes.ElementGroupNode):
                result.extend(self._flatten_elements(elem.members))
            else:
                result.append(elem)
        return result

    def _desc_text(self, desc) -> str:
        if isinstance(desc, nodes.StringLit):
            return desc.value
        return str(desc)

    def _safe_name(self, s: str) -> str:
        s = s.replace(" ", "_").replace(".", "_").replace("-", "_")
        s = "".join(c if c.isalnum() or c == '_' else '_' for c in s)
        if s and s[0].isdigit():
            s = "s" + s
        return s

    def _safe_str(self, s: str) -> str:
        return s.replace('"', '\\"')
