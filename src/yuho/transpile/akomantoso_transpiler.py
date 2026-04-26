"""Akoma Ntoso (LegalDocML) transpiler — Yuho AST -> AKN 1.0 XML.

Akoma Ntoso is the OASIS standard for legislative XML
(https://docs.oasis-open.org/legaldocml/akn-core/v1.0/csprd03/). This
transpiler emits a minimal, valid AKN 1.0 ``<act>`` document for an
encoded Yuho module: each statute becomes an ``<section>`` with nested
``<num>``, ``<heading>``, ``<content>`` containing definitions and
elements, and ``<exception>`` blocks for prioritised exceptions.

Scope (intentional, per ``TODO.md`` Akoma Ntoso decision criterion):
this transpiler is the structural on-ramp described in the
applicability section of the paper. It produces a syntactically valid
AKN skeleton; full schema validation requires the OASIS XSD and is
out of scope for the proof of concept (``xmllint --schema akoma-ntoso-1.0.xsd``
is the natural follow-up).

Output shape
------------

An emitted AKN document looks like::

    <?xml version="1.0" encoding="UTF-8"?>
    <akomaNtoso xmlns="http://docs.oasis-open.org/legaldocml/ns/akn/3.0">
      <act name="penalCode">
        <meta>
          <identification source="#yuho">
            <FRBRWork>
              <FRBRthis value="/akn/sg/act/penalCode/main"/>
              <FRBRuri value="/akn/sg/act/penalCode"/>
              <FRBRdate date="1872-01-01" name="Generation"/>
              <FRBRauthor href="#yuho"/>
              <FRBRcountry value="sg"/>
            </FRBRWork>
          </identification>
        </meta>
        <body>
          <section eId="sec_415">
            <num>415</num>
            <heading>Cheating</heading>
            <content>
              <p>...</p>
              <blockList ...>
                <item ...>actus_reus deception ...</item>
                ...
              </blockList>
            </content>
            <exception>
              <num>private_defence</num>
              <p>private defence under sections 96-106</p>
            </exception>
          </section>
        </body>
      </act>
    </akomaNtoso>
"""

from __future__ import annotations

from html import escape
from typing import List, Optional

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


_AKN_NAMESPACE = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"


class AkomaNtosoTranspiler(TranspilerBase):
    """Emit Akoma Ntoso 1.0 XML from a Yuho ``ModuleNode``."""

    def __init__(
        self,
        *,
        country: str = "sg",
        act_name: str = "penalCode",
        author_id: str = "yuho",
        indent: int = 2,
    ) -> None:
        self.country = country
        self.act_name = act_name
        self.author_id = author_id
        self.indent = indent
        self._depth = 0

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.AKOMANTOSO

    # ------------------------------------------------------------------
    # Top level
    # ------------------------------------------------------------------

    def transpile(self, ast: nodes.ModuleNode) -> str:
        self._depth = 0
        lines: List[str] = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append(f'<akomaNtoso xmlns="{_AKN_NAMESPACE}">')
        self._depth = 1
        lines.extend(self._render_act(ast))
        lines.append("</akomaNtoso>")
        return "\n".join(lines) + "\n"

    def _render_act(self, ast: nodes.ModuleNode) -> List[str]:
        lines: List[str] = []
        lines.append(self._pad(f'<act name="{escape(self.act_name)}">'))
        self._depth += 1
        lines.extend(self._render_meta(ast))
        lines.extend(self._render_body(ast))
        self._depth -= 1
        lines.append(self._pad("</act>"))
        return lines

    def _render_meta(self, ast: nodes.ModuleNode) -> List[str]:
        first_effective = self._earliest_effective_date(ast)
        date_attr = first_effective or "1872-01-01"
        lines: List[str] = []
        lines.append(self._pad("<meta>"))
        self._depth += 1
        lines.append(self._pad(f'<identification source="#{escape(self.author_id)}">'))
        self._depth += 1
        # FRBRWork — abstract Work level (the Act itself).
        lines.append(self._pad("<FRBRWork>"))
        self._depth += 1
        lines.append(self._pad(
            f'<FRBRthis value="/akn/{self.country}/act/{self.act_name}/main"/>'
        ))
        lines.append(self._pad(
            f'<FRBRuri value="/akn/{self.country}/act/{self.act_name}"/>'
        ))
        lines.append(self._pad(
            f'<FRBRdate date="{escape(date_attr)}" name="Generation"/>'
        ))
        lines.append(self._pad(f'<FRBRauthor href="#{escape(self.author_id)}"/>'))
        lines.append(self._pad(f'<FRBRcountry value="{escape(self.country)}"/>'))
        self._depth -= 1
        lines.append(self._pad("</FRBRWork>"))
        # FRBRExpression — required sibling per OASIS XSD; carries the
        # language-level realisation of the Work.
        lines.append(self._pad("<FRBRExpression>"))
        self._depth += 1
        lines.append(self._pad(
            f'<FRBRthis value="/akn/{self.country}/act/{self.act_name}/eng@/main"/>'
        ))
        lines.append(self._pad(
            f'<FRBRuri value="/akn/{self.country}/act/{self.act_name}/eng@"/>'
        ))
        lines.append(self._pad(
            f'<FRBRdate date="{escape(date_attr)}" name="Generation"/>'
        ))
        lines.append(self._pad(f'<FRBRauthor href="#{escape(self.author_id)}"/>'))
        lines.append(self._pad('<FRBRlanguage language="eng"/>'))
        self._depth -= 1
        lines.append(self._pad("</FRBRExpression>"))
        # FRBRManifestation — required third FRBR sibling per XSD.
        lines.append(self._pad("<FRBRManifestation>"))
        self._depth += 1
        lines.append(self._pad(
            f'<FRBRthis value="/akn/{self.country}/act/{self.act_name}/eng@/main.xml"/>'
        ))
        lines.append(self._pad(
            f'<FRBRuri value="/akn/{self.country}/act/{self.act_name}/eng@/main.xml"/>'
        ))
        lines.append(self._pad(
            f'<FRBRdate date="{escape(date_attr)}" name="Generation"/>'
        ))
        lines.append(self._pad(f'<FRBRauthor href="#{escape(self.author_id)}"/>'))
        self._depth -= 1
        lines.append(self._pad("</FRBRManifestation>"))
        self._depth -= 1
        lines.append(self._pad("</identification>"))
        self._depth -= 1
        lines.append(self._pad("</meta>"))
        return lines

    def _render_body(self, ast: nodes.ModuleNode) -> List[str]:
        lines: List[str] = []
        lines.append(self._pad("<body>"))
        self._depth += 1
        for statute in ast.statutes:
            lines.extend(self._render_section(statute))
        self._depth -= 1
        lines.append(self._pad("</body>"))
        return lines

    # ------------------------------------------------------------------
    # Section / exception / element rendering
    # ------------------------------------------------------------------

    def _render_section(self, stat: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        eid = f"sec_{self._slug(stat.section_number)}"
        lines.append(self._pad(f'<section eId="{escape(eid)}">'))
        self._depth += 1
        lines.append(self._pad(f"<num>{escape(stat.section_number)}</num>"))
        if stat.title is not None:
            lines.append(self._pad(f"<heading>{escape(stat.title.value)}</heading>"))
        # AKN's `hierarchy` content model presents an exclusive choice:
        # either a single `<content>` block, or a sequence of `<intro>` +
        # hierarchy children. When the section carries exceptions or
        # subsections, take the second branch.
        has_subdivisions = bool(stat.exceptions or stat.subsections)
        if has_subdivisions:
            lines.extend(self._render_intro(stat))
            for exc in stat.exceptions:
                lines.extend(self._render_exception(exc))
            for sub in stat.subsections:
                lines.extend(self._render_subsection(sub))
        else:
            lines.extend(self._render_content(stat))
        self._depth -= 1
        lines.append(self._pad("</section>"))
        return lines

    def _render_intro(self, stat: nodes.StatuteNode) -> List[str]:
        """Emit the section body as `<intro>` block elements.

        `<intro>` is `blocksreq` per the XSD (block elements only, no
        `<content>`), so we re-use the same body builders as
        `_render_content` but wrap them in `<intro>` instead.
        """
        lines: List[str] = []
        lines.append(self._pad("<intro>"))
        self._depth += 1
        lines.extend(self._render_content_body(stat))
        self._depth -= 1
        lines.append(self._pad("</intro>"))
        return lines

    def _render_content(self, stat: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        lines.append(self._pad("<content>"))
        self._depth += 1
        lines.extend(self._render_content_body(stat))
        self._depth -= 1
        lines.append(self._pad("</content>"))
        return lines

    def _render_content_body(self, stat: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        # Effective dates
        if stat.effective_dates:
            for d in stat.effective_dates:
                lines.append(self._pad(
                    f'<p refersTo="#effective"><date date="{escape(d)}">{escape(d)}</date></p>'
                ))
        # Definitions
        if stat.definitions:
            lines.append(self._pad('<blockList class="definitions">'))
            self._depth += 1
            for defn in stat.definitions:
                term = getattr(defn, "term", None) or getattr(defn, "name", "")
                value = getattr(defn, "definition", None)
                value_str = value.value if hasattr(value, "value") else str(value or "")
                # `itemType` (XSD) requires block-level children. `<term>`
                # demands a `refersTo` attribute pointing into a TLCConcept
                # ontology we don't carry; surface the term as plain text
                # inside a `<def>`-tagged `<p>` so the document validates.
                term_id = self._slug(str(term)) or "term"
                lines.append(self._pad(
                    f'<item><p><def refersTo="#term_{escape(term_id)}">'
                    f"{escape(str(term))}</def>: {escape(value_str)}</p></item>"
                ))
            self._depth -= 1
            lines.append(self._pad("</blockList>"))
        # Elements
        elements_flat = self._flatten_elements(stat.elements)
        if elements_flat:
            lines.append(self._pad('<blockList class="elements">'))
            self._depth += 1
            for el in elements_flat:
                attrs = f'class="{escape(el.element_type)}"'
                desc_node = getattr(el, "description", None)
                desc = desc_node.value if hasattr(desc_node, "value") else (desc_node or "")
                # `<term>` requires a `refersTo` ontology reference per
                # the XSD; render the element name as plain bold text
                # inside `<p>` instead.
                lines.append(self._pad(
                    f"<item {attrs}><p><b>{escape(el.name)}</b>: "
                    f"{escape(str(desc))}</p></item>"
                ))
            self._depth -= 1
            lines.append(self._pad("</blockList>"))
        # Penalty as a single descriptive paragraph (no AKN canonical form)
        if stat.penalty is not None:
            lines.append(self._pad(
                f'<p class="penalty">{escape(self._render_penalty(stat.penalty))}</p>'
            ))
        # Illustrations
        for illus in stat.illustrations:
            label = getattr(illus, "label", None) or getattr(illus, "name", "")
            desc = getattr(illus, "description", None)
            text = desc.value if hasattr(desc, "value") else str(desc or "")
            lines.append(self._pad(
                f'<p class="illustration" eId="ill_{escape(self._slug(label))}">'
                f"{escape(text)}</p>"
            ))
        return lines

    def _render_exception(self, exc: nodes.ExceptionNode) -> List[str]:
        # AKN has no first-class `<exception>` element; the canonical
        # extension point for "named hierarchical block that isn't
        # section/subsection" is `<hcontainer name="…">`. Required `eId`
        # comes from `corereq`.
        lines: List[str] = []
        eid = f"exc_{self._slug(exc.label or 'unlabeled')}"
        attrs = [f'eId="{escape(eid)}"', 'name="exception"']
        priority = getattr(exc, "priority", None)
        if priority is not None:
            attrs.append(f'refersTo="#priority-{escape(str(priority))}"')
        lines.append(self._pad(f"<hcontainer {' '.join(attrs)}>"))
        self._depth += 1
        lines.append(self._pad(f"<num>{escape(exc.label or 'unlabeled')}</num>"))
        # Wrap body in `<content>` (a hierarchy may contain at most one
        # of intro+children OR content; we use the simpler content branch).
        body_paragraphs: List[str] = []
        guard = getattr(exc, "guard", None)
        if guard is not None:
            text = guard.value if hasattr(guard, "value") else str(guard)
            body_paragraphs.append(f"<p>{escape(text)}</p>")
        defeats = getattr(exc, "defeats", None)
        if defeats:
            body_paragraphs.append(
                f'<p class="defeats" refersTo="#exc_{escape(self._slug(defeats))}">'
                f"defeats {escape(defeats)}</p>"
            )
        # `<content>` is required to be non-empty; emit a placeholder if
        # the source has no guard or defeats text.
        if not body_paragraphs:
            body_paragraphs.append("<p>(see source)</p>")
        lines.append(self._pad("<content>"))
        self._depth += 1
        for p in body_paragraphs:
            lines.append(self._pad(p))
        self._depth -= 1
        lines.append(self._pad("</content>"))
        self._depth -= 1
        lines.append(self._pad("</hcontainer>"))
        return lines

    def _render_subsection(self, sub: nodes.SubsectionNode) -> List[str]:
        lines: List[str] = []
        num = getattr(sub, "number", None) or getattr(sub, "label", "")
        eid = f"sub_{self._slug(str(num))}"
        lines.append(self._pad(f'<subsection eId="{escape(eid)}">'))
        self._depth += 1
        lines.append(self._pad(f"<num>({escape(str(num))})</num>"))
        elements_flat = self._flatten_elements(getattr(sub, "elements", ()) or ())
        if elements_flat:
            lines.append(self._pad("<content>"))
            self._depth += 1
            lines.append(self._pad('<blockList class="elements">'))
            self._depth += 1
            for el in elements_flat:
                desc_node = getattr(el, "description", None)
                desc = desc_node.value if hasattr(desc_node, "value") else (desc_node or "")
                lines.append(self._pad(
                    f'<item class="{escape(el.element_type)}">'
                    f"<p><b>{escape(el.name)}</b>: "
                    f"{escape(str(desc))}</p></item>"
                ))
            self._depth -= 1
            lines.append(self._pad("</blockList>"))
            self._depth -= 1
            lines.append(self._pad("</content>"))
        self._depth -= 1
        lines.append(self._pad("</subsection>"))
        return lines

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _flatten_elements(elements) -> List[nodes.ElementNode]:
        out: List[nodes.ElementNode] = []
        stack = list(elements)
        while stack:
            item = stack.pop(0)
            if isinstance(item, nodes.ElementNode):
                out.append(item)
            elif isinstance(item, nodes.ElementGroupNode):
                stack[:0] = list(item.members)
        return out

    @staticmethod
    def _render_penalty(penalty: nodes.PenaltyNode) -> str:
        """Best-effort one-line summary of a penalty for AKN <p> embedding.

        Akoma Ntoso has no first-class penalty primitive; we surface the
        Yuho structural shape as a class-tagged paragraph and rely on
        downstream consumers to parse the prose.
        """
        bits: List[str] = []
        for attr in ("imprisonment", "fine", "caning", "death"):
            val = getattr(penalty, attr, None)
            if val is not None and val is not False:
                bits.append(attr)
        return "; ".join(bits) if bits else "(structured penalty — see source)"

    @staticmethod
    def _earliest_effective_date(ast: nodes.ModuleNode) -> Optional[str]:
        candidates = []
        for s in ast.statutes:
            if s.effective_dates:
                candidates.extend(s.effective_dates)
            elif s.effective_date:
                candidates.append(s.effective_date)
        return min(candidates) if candidates else None

    @staticmethod
    def _slug(s: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in s)

    def _pad(self, line: str) -> str:
        return " " * (self.indent * self._depth) + line
