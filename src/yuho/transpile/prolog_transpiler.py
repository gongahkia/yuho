"""
Prolog transpiler -- export statute logic as Prolog facts and rules.

Generates SWI-Prolog compatible output with:
- Facts for definitions, elements, penalties
- Rules for offense satisfaction
- Exception defeat predicates
"""

from typing import List

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


class PrologTranspiler(TranspilerBase):
    """Transpile Yuho AST to Prolog facts and rules."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.PROLOG

    def transpile(self, ast: nodes.ModuleNode) -> str:
        lines: List[str] = []
        lines.append("%%% Auto-generated Prolog from Yuho statutes")
        lines.append("%%% Do not edit manually")
        lines.append(":- discontiguous statute/2, element/4, definition/3.")
        lines.append(":- discontiguous penalty/3, exception/3, caselaw/4.")
        lines.append(":- discontiguous exception_priority/3, defeats/3.")
        lines.append(":- discontiguous party/3, actor/3, patient/3.")
        lines.append(":- discontiguous guilty/2, element_satisfied/3.")
        lines.append("")
        for statute in ast.statutes:
            self._emit_statute(lines, statute)
        for lt in getattr(ast, "legal_tests", ()):
            self._emit_legal_test(lines, lt)
        for cc in getattr(ast, "conflict_checks", ()):
            self._emit_conflict_check(lines, cc)
        lines.append("")
        lines.append("%%% Guilt inference rule")
        lines.append("%%% guilty(Section, Facts) :- all elements satisfied, no exception applies")
        for statute in ast.statutes:
            self._emit_guilt_rule(lines, statute)
        return "\n".join(lines)

    def _emit_statute(self, lines: List[str], statute: nodes.StatuteNode) -> None:
        sec = self._safe_atom(statute.section_number)
        title = self._safe_str(statute.title.value if statute.title else "")
        lines.append(f"%%% Section {statute.section_number}")
        lines.append(f"statute(s{sec}, {title}).")
        # temporal metadata
        if getattr(statute, "effective_date", None):
            lines.append(f"effective(s{sec}, '{statute.effective_date}').")
        if getattr(statute, "repealed_date", None):
            lines.append(f"repealed(s{sec}, '{statute.repealed_date}').")
        subsumes = getattr(statute, "subsumes", None)
        if isinstance(subsumes, str):
            lines.append(f"subsumes(s{sec}, s{self._safe_atom(subsumes)}).")
        # parties
        for party in getattr(statute, "parties", ()):
            role = self._safe_atom(party.role)
            pname = self._safe_atom(party.name)
            lines.append(f"party(s{sec}, {role}, {pname}).")
        # definitions
        for defn in statute.definitions:
            term = self._safe_atom(defn.term)
            desc = self._safe_str(defn.definition.value)
            lines.append(f"definition(s{sec}, {term}, {desc}).")
        # elements
        flat = self._flatten_elements(statute.elements)
        for elem in flat:
            etype = self._safe_atom(elem.element_type)
            ename = self._safe_atom(elem.name)
            desc = self._safe_str(self._desc_text(elem.description))
            lines.append(f"element(s{sec}, {etype}, {ename}, {desc}).")
            if getattr(elem, "caused_by", None):
                lines.append(f"caused_by(s{sec}, {ename}, {self._safe_atom(elem.caused_by)}).")
            if getattr(elem, "burden", None):
                lines.append(f"burden(s{sec}, {ename}, {self._safe_atom(elem.burden)}).")
            if getattr(elem, "actor", None):
                lines.append(f"actor(s{sec}, {ename}, {self._safe_atom(elem.actor)}).")
            if getattr(elem, "patient", None):
                lines.append(f"patient(s{sec}, {ename}, {self._safe_atom(elem.patient)}).")
        # penalty
        if statute.penalty:
            self._emit_penalty(lines, sec, statute.penalty)
        # exceptions
        for exc in statute.exceptions:
            label = self._safe_atom(exc.label) if exc.label else "exception"
            cond = self._safe_str(exc.condition.value) if hasattr(exc.condition, "value") else "''"
            lines.append(f"exception(s{sec}, {label}, {cond}).")
            if getattr(exc, "priority", None) is not None:
                lines.append(f"exception_priority(s{sec}, {label}, {exc.priority}).")
            defeats = getattr(exc, "defeats", None)
            if isinstance(defeats, str):
                lines.append(f"defeats(s{sec}, {label}, {self._safe_atom(defeats)}).")
        # caselaw
        for cl in statute.case_law:
            case_name = self._safe_str(cl.case_name.value)
            citation = self._safe_str(cl.citation.value) if cl.citation else "''"
            holding = self._safe_str(cl.holding.value)
            lines.append(f"caselaw(s{sec}, {case_name}, {citation}, {holding}).")
        lines.append("")

    def _emit_penalty(self, lines: List[str], sec: str, p: nodes.PenaltyNode) -> None:
        if p.death_penalty:
            lines.append(f"penalty(s{sec}, death, true).")
        if p.imprisonment_max:
            lines.append(f"penalty(s{sec}, imprisonment_max, '{p.imprisonment_max}').")
        if p.imprisonment_min:
            lines.append(f"penalty(s{sec}, imprisonment_min, '{p.imprisonment_min}').")
        if p.fine_max:
            lines.append(f"penalty(s{sec}, fine_max, {p.fine_max.amount}).")
        if p.fine_min:
            lines.append(f"penalty(s{sec}, fine_min, {p.fine_min.amount}).")
        sentencing = getattr(p, "sentencing", None)
        if isinstance(sentencing, str):
            lines.append(f"penalty(s{sec}, sentencing, {self._safe_atom(sentencing)}).")
        if getattr(p, "mandatory_min_imprisonment", None):
            lines.append(
                f"penalty(s{sec}, mandatory_min_imprisonment, '{p.mandatory_min_imprisonment}')."
            )

    def _emit_guilt_rule(self, lines: List[str], statute: nodes.StatuteNode) -> None:
        sec = self._safe_atom(statute.section_number)
        flat = self._flatten_elements(statute.elements)
        if not flat:
            return
        elem_conditions = [
            f"element_satisfied(s{sec}, {self._safe_atom(e.name)}, Facts)" for e in flat
        ]
        exc_check = f"\\+ exception_applies(s{sec}, Facts)"
        body = ",\n    ".join(elem_conditions + [exc_check])
        lines.append(f"guilty(s{sec}, Facts) :-")
        lines.append(f"    {body}.")
        lines.append("")

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

    def _safe_atom(self, s: str) -> str:
        """Make a safe Prolog atom."""
        s = s.replace("'", "\\'").replace(" ", "_").lower()
        s = "".join(c if c.isalnum() or c == "_" else "_" for c in s)
        if s and s[0].isdigit():
            s = "s" + s
        return s

    def _emit_legal_test(self, lines: List[str], lt: nodes.LegalTestNode) -> None:
        name = self._safe_atom(lt.name)
        lines.append(f"%%% Legal test: {lt.name}")
        for req in lt.requirements:
            if isinstance(req, nodes.VariableDecl):
                rname = self._safe_atom(req.name)
                lines.append(f"legal_test_requirement({name}, {rname}).")
        if lt.requirements:
            req_conds = [
                f"requirement_met({name}, {self._safe_atom(r.name)}, Facts)"
                for r in lt.requirements
                if isinstance(r, nodes.VariableDecl)
            ]
            body = ",\n    ".join(req_conds)
            lines.append(f"legal_test_satisfied({name}, Facts) :-")
            lines.append(f"    {body}.")
        lines.append("")

    def _emit_conflict_check(self, lines: List[str], cc: nodes.ConflictCheckNode) -> None:
        name = self._safe_atom(cc.name)
        lines.append(f"%%% Conflict check: {cc.name}")
        lines.append(
            f"conflict_check({name}, {self._safe_str(cc.source)}, {self._safe_str(cc.target)})."
        )
        lines.append("")

    def _safe_str(self, s: str) -> str:
        """Make a safe Prolog string."""
        s = s.replace("'", "\\'")
        return f"'{s}'"
