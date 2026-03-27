"""
Akoma Ntoso XML transpiler.

Converts Yuho AST to Akoma Ntoso 3.0 XML, the international
standard for legislative document markup (OASIS LegalDocumentML).
"""

from typing import List
from xml.sax.saxutils import escape

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


class AkomaNtosoTranspiler(TranspilerBase):
    """Transpile Yuho AST to Akoma Ntoso XML."""

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.AKOMA_NTOSO

    def transpile(self, ast: nodes.ModuleNode) -> str:
        lines: List[str] = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">')
        lines.append('  <act name="penal-code">')
        lines.append("    <meta>")
        lines.append('      <identification source="#yuho">')
        lines.append("        <FRBRWork>")
        lines.append('          <FRBRthis value="/akn/sg/act/penal-code"/>')
        lines.append('          <FRBRuri value="/akn/sg/act/penal-code"/>')
        lines.append('          <FRBRdate date="1872-01-01" name="enactment"/>')
        lines.append('          <FRBRauthor href="#parliament"/>')
        lines.append('          <FRBRcountry value="sg"/>')
        lines.append("        </FRBRWork>")
        lines.append("        <FRBRExpression>")
        lines.append('          <FRBRthis value="/akn/sg/act/penal-code/eng"/>')
        lines.append('          <FRBRuri value="/akn/sg/act/penal-code/eng"/>')
        lines.append('          <FRBRdate date="2025-01-01" name="publication"/>')
        lines.append('          <FRBRauthor href="#yuho"/>')
        lines.append('          <FRBRlanguage language="eng"/>')
        lines.append("        </FRBRExpression>")
        lines.append("        <FRBRManifestation>")
        lines.append('          <FRBRthis value="/akn/sg/act/penal-code/eng/main.xml"/>')
        lines.append('          <FRBRuri value="/akn/sg/act/penal-code/eng/main.xml"/>')
        lines.append('          <FRBRdate date="2025-01-01" name="transform"/>')
        lines.append('          <FRBRauthor href="#yuho"/>')
        lines.append("        </FRBRManifestation>")
        lines.append("      </identification>")
        lines.append('      <references source="#yuho">')
        lines.append(
            '        <TLCOrganization eId="yuho" href="/ontology/organization/yuho" showAs="Yuho DSL"/>'
        )
        lines.append(
            '        <TLCOrganization eId="parliament" href="/ontology/organization/sg.parliament" showAs="Parliament of Singapore"/>'
        )
        lines.append("      </references>")
        lines.append("    </meta>")
        lines.append("    <body>")
        for statute in ast.statutes:
            self._emit_statute(lines, statute)
        lines.append("    </body>")
        lines.append("  </act>")
        lines.append("</akomaNtoso>")
        return "\n".join(lines)

    def _emit_statute(self, lines: List[str], statute: nodes.StatuteNode) -> None:
        section = escape(statute.section_number)
        eid = f"sec_{section.replace('.', '_')}"
        title = escape(statute.title.value) if statute.title else f"Section {section}"
        lines.append(f'      <section eId="{eid}">')
        lines.append(f"        <num>{section}</num>")
        lines.append(f"        <heading>{title}</heading>")
        # definitions as intro
        if statute.definitions:
            lines.append("        <intro>")
            lines.append("          <p>In this section —</p>")
            for defn in statute.definitions:
                term = escape(defn.term)
                desc = escape(defn.definition.value)
                lines.append(f"          <def><term>{term}</term> — {desc}</def>")
            lines.append("        </intro>")
        # elements as content paragraphs
        if statute.elements:
            lines.append("        <content>")
            flat = self._flatten_elements(statute.elements)
            for i, elem in enumerate(flat, 1):
                elem_eid = f"{eid}__para_{i}"
                etype = escape(elem.element_type)
                name = escape(elem.name)
                desc = escape(self._desc_text(elem.description))
                lines.append(f'          <paragraph eId="{elem_eid}">')
                lines.append(f"            <num>({i})</num>")
                lines.append(
                    f'            <content><p class="{etype}" data-name="{name}">{desc}</p></content>'
                )
                lines.append(f"          </paragraph>")
            lines.append("        </content>")
        # penalty as wrapUp
        if statute.penalty:
            lines.append("        <wrapUp>")
            lines.append('          <p class="penalty">')
            parts = self._penalty_parts(statute.penalty)
            lines.append(f'            {escape("; ".join(parts))}')
            lines.append("          </p>")
            lines.append("        </wrapUp>")
        # exceptions as hcontainer
        if statute.exceptions:
            for exc in statute.exceptions:
                label = escape(exc.label) if exc.label else "exception"
                cond = escape(exc.condition.value) if hasattr(exc.condition, "value") else ""
                lines.append(f'        <hcontainer name="exception" eId="{eid}__{label}">')
                lines.append(f"          <heading>Exception: {label}</heading>")
                lines.append(f"          <content><p>{cond}</p></content>")
                lines.append(f"        </hcontainer>")
        lines.append(f"      </section>")

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

    def _penalty_parts(self, penalty: nodes.PenaltyNode) -> List[str]:
        parts = []
        if penalty.death_penalty:
            parts.append("Death")
        if penalty.imprisonment_max:
            parts.append(f"Imprisonment up to {penalty.imprisonment_max}")
        if penalty.fine_max:
            parts.append(f"Fine up to ${penalty.fine_max.amount}")
        if getattr(penalty, "sentencing", None):
            parts.append(f"Sentencing: {penalty.sentencing}")
        if penalty.supplementary:
            parts.append(penalty.supplementary.value)
        return parts or ["Penalty as prescribed"]
