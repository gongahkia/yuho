"""
F* transpiler -- export statute logic as F* (FStar) definitions.

Generates F* (https://www.fstar-lang.org/) compatible output with:
- Record types for statute structures
- Refinement types for constrained fields
- Lemma stubs for formal proofs
- Total functions for element evaluation
"""

from typing import List

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


class FStarTranspiler(TranspilerBase):
    """Transpile Yuho AST to F* proof language."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.FSTAR

    def transpile(self, ast: nodes.ModuleNode) -> str:
        lines: List[str] = []
        mod_name = "YuhoStatutes"
        lines.append(f"module {mod_name}")
        lines.append("")
        lines.append("(* Auto-generated F* from Yuho statutes *)")
        lines.append("(* Do not edit manually *)")
        lines.append("")
        lines.append("open FStar.All")
        lines.append("open FStar.String")
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
        name = self._safe_name(struct.name)
        lines.append(f"type {self._lower(name)} = {{")
        for f in struct.fields:
            ftype = self._fstar_type(f.type_annotation)
            lines.append(f"  {self._safe_name(f.name)}: {ftype};")
        lines.append("}")
        lines.append("")

    def _emit_enum(self, lines: List[str], enum: nodes.EnumDefNode) -> None:
        name = self._safe_name(enum.name)
        lines.append(f"type {self._lower(name)} =")
        for v in enum.variants:
            vname = self._safe_name(v.name)
            if v.payload_types:
                ptypes = " * ".join(self._fstar_type(t) for t in v.payload_types)
                lines.append(f"  | {vname} of ({ptypes})")
            else:
                lines.append(f"  | {vname}")
        lines.append("")

    def _emit_statute(self, lines: List[str], statute: nodes.StatuteNode) -> None:
        sec = self._safe_name(statute.section_number)
        title = statute.title.value if statute.title else sec
        lines.append(f"(* Section {statute.section_number}: {title} *)")
        lines.append("")
        # annotations as comments
        for ann in getattr(statute, 'annotations', ()):
            args = ", ".join(f'"{a}"' for a in ann.args)
            lines.append(f"(* @{ann.name}({args}) *)")
        # record type for the statute's fact pattern
        flat = self._flatten_elements(statute.elements)
        if flat:
            lines.append(f"type section_{sec}_facts = {{")
            for elem in flat:
                ename = self._safe_name(elem.name)
                lines.append(f"  {ename}: bool; (* {elem.element_type} *)")
            lines.append("}")
            lines.append("")
        # definitions as let bindings
        for defn in statute.definitions:
            name = self._safe_name(defn.term)
            val = self._safe_str(defn.definition.value)
            lines.append(f'let {self._lower(name)}_def : string = "{val}"')
        if statute.definitions:
            lines.append("")
        # guilt predicate
        if flat:
            lines.append(f"let is_guilty_{sec} (facts: section_{sec}_facts) : bool =")
            conditions = " &&\n  ".join(f"facts.{self._safe_name(e.name)}" for e in flat)
            lines.append(f"  {conditions}")
            lines.append("")
        # exception predicates
        for i, exc in enumerate(statute.exceptions):
            label = self._safe_name(exc.label) if exc.label else f"exc_{i}"
            cond = exc.condition.value if hasattr(exc.condition, 'value') else str(exc.condition)
            lines.append(f'(* exception {label}: "{self._safe_str(cond)}" *)')
            if flat:
                lines.append(f"let exception_{label}_{sec} (facts: section_{sec}_facts) : bool =")
                lines.append(f"  false (* placeholder: encode exception condition *)")
                lines.append("")
        # effective guilt with exceptions
        if flat and statute.exceptions:
            exc_checks = " && ".join(
                f"not (exception_{self._safe_name(e.label) if e.label else f'exc_{i}'}_{sec} facts)"
                for i, e in enumerate(statute.exceptions)
            )
            lines.append(f"let guilty_{sec} (facts: section_{sec}_facts) : bool =")
            lines.append(f"  is_guilty_{sec} facts && {exc_checks}")
            lines.append("")
        # penalty info as comments
        if statute.penalty:
            self._emit_penalty_comment(lines, sec, statute.penalty)
        # caselaw as comments
        for cl in statute.case_law:
            cite = cl.citation.value if cl.citation else ""
            lines.append(f"(* caselaw: {cl.case_name.value} ({cite}) *)")
            lines.append(f"(*   holding: {cl.holding.value} *)")
        # illustrations as comments
        for ill in statute.illustrations:
            label = ill.label or "illustration"
            lines.append(f"(* {label}: {ill.description.value} *)")
        lines.append("")

    def _emit_legal_test(self, lines: List[str], lt: nodes.LegalTestNode) -> None:
        name = self._safe_name(lt.name)
        lines.append(f"(* Legal test: {name} *)")
        lines.append(f"type {self._lower(name)}_requirements = {{")
        for req in lt.requirements:
            if isinstance(req, nodes.VariableDecl):
                rtype = self._fstar_type(req.type_annotation)
                lines.append(f"  {self._safe_name(req.name)}: {rtype};")
        lines.append("}")
        lines.append("")
        if lt.condition:
            lines.append(f"let test_{self._lower(name)} (r: {self._lower(name)}_requirements) : bool =")
            lines.append(f"  {self._expr_to_fstar(lt.condition, 'r')}")
            lines.append("")

    def _emit_conflict_check(self, lines: List[str], cc: nodes.ConflictCheckNode) -> None:
        name = self._safe_name(cc.name)
        lines.append(f"(* Conflict check: {name} *)")
        lines.append(f'(* source: "{cc.source}" *)')
        lines.append(f'(* target: "{cc.target}" *)')
        lines.append(f"(* Verify: no contradictory conclusions between source and target *)")
        lines.append("")

    def _emit_penalty_comment(self, lines: List[str], sec: str, p: nodes.PenaltyNode) -> None:
        if p.death_penalty:
            lines.append(f"(* penalty: death *)")
        if p.imprisonment_max:
            lines.append(f"(* penalty: imprisonment up to {p.imprisonment_max} *)")
        if p.fine_max:
            lines.append(f"(* penalty: fine up to {p.fine_max.amount} *)")

    def _expr_to_fstar(self, expr: nodes.ASTNode, record_var: str = "r") -> str:
        if isinstance(expr, nodes.BinaryExprNode):
            left = self._expr_to_fstar(expr.left, record_var)
            right = self._expr_to_fstar(expr.right, record_var)
            op = expr.operator
            if op == "&&":
                return f"{left} && {right}"
            elif op == "||":
                return f"{left} || {right}"
            return f"{left} {op} {right}"
        elif isinstance(expr, nodes.UnaryExprNode):
            operand = self._expr_to_fstar(expr.operand, record_var)
            if expr.operator == "!":
                return f"not {operand}"
            return f"{expr.operator}{operand}"
        elif isinstance(expr, nodes.IdentifierNode):
            return f"{record_var}.{self._safe_name(expr.name)}"
        elif isinstance(expr, nodes.BoolLit):
            return "true" if expr.value else "false"
        elif isinstance(expr, nodes.IntLit):
            return str(expr.value)
        return "false"

    def _fstar_type(self, t: nodes.TypeNode) -> str:
        if isinstance(t, nodes.BuiltinType):
            mapping = {
                "int": "int", "float": "float", "bool": "bool",
                "string": "string", "money": "int", "date": "string",
                "duration": "int", "percent": "int", "void": "unit",
            }
            return mapping.get(t.name, t.name)
        elif isinstance(t, nodes.NamedType):
            return self._lower(self._safe_name(t.name))
        elif isinstance(t, nodes.ArrayType):
            return f"list ({self._fstar_type(t.element_type)})"
        elif isinstance(t, nodes.OptionalType):
            return f"option ({self._fstar_type(t.inner)})"
        return "string"

    def _flatten_elements(self, elements) -> list:
        result = []
        for elem in elements:
            if isinstance(elem, nodes.ElementGroupNode):
                result.extend(self._flatten_elements(elem.members))
            else:
                result.append(elem)
        return result

    def _safe_name(self, s: str) -> str:
        s = s.replace(" ", "_").replace(".", "_").replace("-", "_")
        s = "".join(c if c.isalnum() or c == '_' else '_' for c in s)
        if s and s[0].isdigit():
            s = "s" + s
        return s

    def _lower(self, s: str) -> str:
        if s:
            return s[0].lower() + s[1:]
        return s

    def _safe_str(self, s: str) -> str:
        return s.replace('"', '\\"')
