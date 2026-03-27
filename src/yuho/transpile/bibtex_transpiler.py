"""
BibTeX transpiler - export caselaw entries as BibTeX records.

Extracts CaseLawNode entries from statutes and produces
standard BibTeX @misc entries for legal citation management.
"""

import re
from typing import List

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


class BibTeXTranspiler(TranspilerBase):
    """Transpile Yuho AST caselaw blocks to BibTeX format."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.BIBTEX

    def transpile(self, ast: nodes.ModuleNode) -> str:
        entries: List[str] = []
        for statute in ast.statutes:
            if not statute.case_law:
                continue
            section = statute.section_number
            title = statute.title.value if statute.title else f"Section {section}"
            for cl in statute.case_law:
                entries.append(self._caselaw_to_bibtex(cl, section, title))
        if not entries:
            return "% No caselaw entries found.\n"
        return "\n\n".join(entries) + "\n"

    def _caselaw_to_bibtex(self, cl: nodes.CaseLawNode, section: str, statute_title: str) -> str:
        case_name = cl.case_name.value
        key = self._make_key(case_name)
        citation = cl.citation.value if cl.citation else ""
        holding = cl.holding.value if cl.holding else ""
        lines = [f"@misc{{{key},"]
        lines.append(f"  title = {{{case_name}}},")
        if citation:
            lines.append(f"  howpublished = {{{citation}}},")
        if holding:
            lines.append(f"  note = {{{holding}}},")
        lines.append(f"  keywords = {{s{section}, {statute_title}}},")
        if cl.element_ref:
            lines.append(f"  annote = {{Interprets element: {cl.element_ref}}},")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _make_key(case_name: str) -> str:
        """Derive a BibTeX citation key from a case name."""
        cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", case_name)
        parts = cleaned.split()
        if not parts:
            return "unknown"
        if len(parts) >= 3:  # e.g. "Tan v State" -> "Tan2026"
            return parts[0].lower() + "Case"
        return parts[0].lower() + "Case"
