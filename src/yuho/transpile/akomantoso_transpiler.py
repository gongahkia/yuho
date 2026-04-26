"""Akoma Ntoso (LegalDocML) transpiler — Yuho AST -> AKN 1.0 XML.

Akoma Ntoso is the OASIS standard for legislative XML
(https://docs.oasis-open.org/legaldocml/akn-core/v1.0/csprd03/). This
transpiler emits a minimal, valid AKN 1.0 ``<act>`` document for an
encoded Yuho module: each statute becomes an ``<section>`` with nested
``<num>``, ``<heading>``, ``<content>`` containing definitions and
elements, and ``<exception>`` blocks for prioritised exceptions.

Scope (intentional, per ``todo.md`` Akoma Ntoso decision criterion):
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
        # Effective dates as AKN <FRBRdate> would normally live in <meta>
        # for a per-section-versioned AKN; we surface them as <p> for now.
        lines.extend(self._render_content(stat))
        for exc in stat.exceptions:
            lines.extend(self._render_exception(exc))
        for sub in stat.subsections:
            lines.extend(self._render_subsection(sub))
        self._depth -= 1
        lines.append(self._pad("</section>"))
        return lines

    def _render_content(self, stat: nodes.StatuteNode) -> List[str]:
        lines: List[str] = []
        lines.append(self._pad("<content>"))
        self._depth += 1
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
                lines.append(self._pad(
                    f"<item><term>{escape(str(term))}</term><def>{escape(value_str)}</def></item>"
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
                lines.append(self._pad(
                    f"<item {attrs}><term>{escape(el.name)}</term>"
                    f"<p>{escape(str(desc))}</p></item>"
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
        self._depth -= 1
        lines.append(self._pad("</content>"))
        return lines

    def _render_exception(self, exc: nodes.ExceptionNode) -> List[str]:
        lines: List[str] = []
        attrs: List[str] = []
        if getattr(exc, "label", None):
            attrs.append(f'eId="exc_{escape(self._slug(exc.label))}"')
        priority = getattr(exc, "priority", None)
        if priority is not None:
            attrs.append(f'refersTo="#priority-{escape(str(priority))}"')
        attr_str = (" " + " ".join(attrs)) if attrs else ""
        lines.append(self._pad(f"<exception{attr_str}>"))
        self._depth += 1
        lines.append(self._pad(f"<num>{escape(exc.label or 'unlabeled')}</num>"))
        guard = getattr(exc, "guard", None)
        if guard is not None:
            text = guard.value if hasattr(guard, "value") else str(guard)
            lines.append(self._pad(f"<p>{escape(text)}</p>"))
        defeats = getattr(exc, "defeats", None)
        if defeats:
            lines.append(self._pad(
                f'<p class="defeats" refersTo="#elem_{escape(self._slug(defeats))}">'
                f"defeats {escape(defeats)}</p>"
            ))
        self._depth -= 1
        lines.append(self._pad("</exception>"))
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
                    f"<term>{escape(el.name)}</term><p>{escape(str(desc))}</p></item>"
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
