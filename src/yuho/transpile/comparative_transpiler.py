"""
Comparative table transpiler - side-by-side statute comparison.

Generates markdown tables comparing elements, penalties, and
definitions across multiple statutes in a single module.
"""

from typing import List

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


class ComparativeTranspiler(TranspilerBase):
    """Transpile multiple statutes to a comparative markdown table."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.COMPARATIVE

    def transpile(self, ast: nodes.ModuleNode) -> str:
        if len(ast.statutes) < 2:
            return "<!-- Need at least 2 statutes for comparison -->\n"
        statutes = list(ast.statutes)
        lines: List[str] = []
        lines.append(self._header(statutes))
        lines.append("")
        lines.append(self._elements_table(statutes))
        lines.append("")
        lines.append(self._penalty_table(statutes))
        lines.append("")
        lines.append(self._definitions_table(statutes))
        return "\n".join(lines) + "\n"

    def _title(self, s: nodes.StatuteNode) -> str:
        t = s.title.value if s.title else "Untitled"
        return f"s{s.section_number} {t}"

    def _header(self, statutes: List[nodes.StatuteNode]) -> str:
        titles = [self._title(s) for s in statutes]
        return "# Comparative Analysis: " + " vs ".join(titles)

    def _elements_table(self, statutes: List[nodes.StatuteNode]) -> str:
        lines = ["## Elements"]
        headers = ["Element Type"] + [self._title(s) for s in statutes]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        all_types = ["actus_reus", "mens_rea", "circumstance"]
        for etype in all_types:
            row = [etype]
            for s in statutes:
                elems = [e for e in s.elements if isinstance(e, nodes.ElementNode) and e.element_type == etype]
                if elems:
                    row.append("; ".join(e.name for e in elems))
                else:
                    row.append("--")
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def _penalty_table(self, statutes: List[nodes.StatuteNode]) -> str:
        lines = ["## Penalties"]
        headers = ["Penalty"] + [self._title(s) for s in statutes]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for field_label, getter in [
            ("Imprisonment", lambda p: f"{p.imprisonment_min or '--'} to {p.imprisonment_max or '--'}" if p else "--"),
            ("Fine", lambda p: f"${p.fine_min.amount if p.fine_min else 0} to ${p.fine_max.amount if p.fine_max else '?'}" if p else "--"),
            ("Death", lambda p: "Yes" if p and p.death_penalty else "No"),
            ("Caning", lambda p: f"{p.caning_min or 0}-{p.caning_max}" if p and p.caning_max else "--"),
        ]:
            row = [field_label]
            for s in statutes:
                row.append(getter(s.penalty))
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)

    def _definitions_table(self, statutes: List[nodes.StatuteNode]) -> str:
        lines = ["## Shared Definitions"]
        all_terms = set()
        for s in statutes:
            for d in s.definitions:
                all_terms.add(d.term)
        if not all_terms:
            return "## Definitions\n\nNo definitions found."
        headers = ["Term"] + [self._title(s) for s in statutes]
        lines.append("| " + " | ".join(headers) + " |")
        lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for term in sorted(all_terms):
            row = [term]
            for s in statutes:
                defs = [d for d in s.definitions if d.term == term]
                if defs:
                    row.append(defs[0].definition.value[:80])
                else:
                    row.append("--")
            lines.append("| " + " | ".join(row) + " |")
        return "\n".join(lines)
