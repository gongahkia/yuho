"""DOCX transpiler — emits a Word-compatible .docx package from a Yuho AST.

Implements a minimal OOXML (WordprocessingML) writer on top of the stdlib
zipfile + xml.etree machinery, so there is no runtime dependency on
python-docx. transpile() returns the document.xml body fragment as a string
(for registry/CLI stdout compatibility). write_docx(ast, path) writes the
full .docx zip to disk.
"""

from __future__ import annotations

import io
import zipfile
from dataclasses import dataclass
from typing import List, Optional, Tuple
from xml.sax.saxutils import escape as xml_escape

from yuho.ast import nodes
from yuho.transpile.base import TranspileTarget, TranspilerBase


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W_PREFIX = 'xmlns:w="' + W_NS + '"'


@dataclass
class _Para:
    style: str                           # Heading1 / Heading2 / Heading3 / Normal / Quote / ListNumber
    runs: Tuple[Tuple[str, str], ...]    # (formatting flag, text) — flag ∈ "", "b", "i", "bi"


class DOCXTranspiler(TranspilerBase):
    """Transpile Yuho AST to an Office Open XML (.docx) body fragment."""

    def __init__(self) -> None:
        self._paras: List[_Para] = []

    @property
    def target(self) -> TranspileTarget:
        return TranspileTarget.DOCX

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def transpile(self, ast: nodes.ModuleNode) -> str:
        self._paras = []
        self._visit_module(ast)
        return self._serialize_document_xml()

    def write_docx(self, ast: nodes.ModuleNode, path: str) -> None:
        self._paras = []
        self._visit_module(ast)
        document_xml = self._serialize_document_xml()
        _write_docx_package(document_xml, path)

    # ------------------------------------------------------------------
    # AST walk
    # ------------------------------------------------------------------

    def _visit_module(self, node: nodes.ModuleNode) -> None:
        for statute in node.statutes:
            self._visit_statute(statute)

    def _visit_statute(self, s: nodes.StatuteNode) -> None:
        title = s.title.value if s.title else ""
        heading = f"§ {s.section_number}"
        if title:
            heading += f" — {title}"
        self._h1(heading)

        if s.jurisdiction:
            self._quote(f"Jurisdiction: {s.jurisdiction}")
        if s.effective_date:
            self._quote(f"Effective: {s.effective_date}")
        if s.repealed_date:
            self._quote(f"Repealed: {s.repealed_date}")

        if s.definitions:
            self._h2("Definitions")
            for d in s.definitions:
                name = getattr(d, "name", None) or getattr(d, "identifier", "?")
                desc = _stringify(getattr(d, "value", None) or getattr(d, "description", None))
                self._para_rich(((b"b", f"{name}: ".encode()),), bold_prefix=True, rest=desc)

        if s.elements:
            self._h2("Elements")
            for el in s.elements:
                self._emit_element(el, depth=0)

        if s.penalty:
            self._h2("Penalty")
            for line in _format_penalty(s.penalty):
                self._normal(line)

        if s.illustrations:
            self._h2("Illustrations")
            for i, ill in enumerate(s.illustrations, 1):
                label = ill.label or str(i)
                self._list(f"({label}) {ill.description.value}")

        if s.exceptions:
            self._h2("Exceptions")
            for ex in s.exceptions:
                lbl = ex.label or "Exception"
                text = ex.condition.value
                if ex.effect:
                    text += f" — {ex.effect.value}"
                if ex.priority is not None:
                    text += f"  [priority={ex.priority}]"
                if ex.defeats:
                    text += f"  [defeats {ex.defeats}]"
                self._list(f"{lbl}: {text}")

        if s.case_law:
            self._h2("Case law")
            for c in s.case_law:
                cite = f" ({c.citation.value})" if c.citation else ""
                holding = c.holding.value if c.holding and c.holding.value else ""
                self._list(f"{c.case_name.value}{cite}: {holding}")

        for sub in s.subsections:
            self._visit_subsection(sub, depth=1)

    def _visit_subsection(self, sub: nodes.SubsectionNode, depth: int) -> None:
        header_level = min(2 + depth, 3)
        header = f"Subsection {sub.number}"
        if header_level == 2:
            self._h2(header)
        else:
            self._h3(header)
        for el in sub.elements:
            self._emit_element(el, depth=depth)
        if sub.penalty:
            self._normal("Penalty:")
            for line in _format_penalty(sub.penalty):
                self._normal("  " + line)
        for ill in sub.illustrations:
            self._list(f"({ill.label or '?'}) {ill.description.value}")
        for ex in sub.exceptions:
            self._list(f"{ex.label or 'Exception'}: {ex.condition.value}")
        for nested in sub.subsections:
            self._visit_subsection(nested, depth=depth + 1)

    def _emit_element(self, node: nodes.ASTNode, depth: int) -> None:
        if isinstance(node, nodes.ElementGroupNode):
            combinator = "ALL OF" if node.combinator == "all_of" else "ANY OF"
            self._normal(f"{'  ' * depth}{combinator}:")
            for m in node.members:
                self._emit_element(m, depth + 1)
            return
        if isinstance(node, nodes.ElementNode):
            kind = node.element_type.replace("_", " ")
            desc = _stringify(node.description)
            line = f"{'  ' * depth}[{kind}] {node.name}: {desc}"
            if node.burden:
                line += f"  (burden: {node.burden}"
                if node.burden_standard:
                    line += f", {node.burden_standard}"
                line += ")"
            self._list(line)

    # ------------------------------------------------------------------
    # Paragraph helpers
    # ------------------------------------------------------------------

    def _h1(self, text: str) -> None:
        self._paras.append(_Para("Heading1", (("", text),)))

    def _h2(self, text: str) -> None:
        self._paras.append(_Para("Heading2", (("", text),)))

    def _h3(self, text: str) -> None:
        self._paras.append(_Para("Heading3", (("", text),)))

    def _normal(self, text: str) -> None:
        self._paras.append(_Para("Normal", (("", text),)))

    def _quote(self, text: str) -> None:
        self._paras.append(_Para("Quote", (("i", text),)))

    def _list(self, text: str) -> None:
        self._paras.append(_Para("ListBullet", (("", text),)))

    def _para_rich(self, lead: Tuple[Tuple[bytes, str], ...], bold_prefix: bool, rest: str) -> None:
        runs: List[Tuple[str, str]] = []
        for flag_b, txt_b in lead:
            flag = flag_b.decode() if isinstance(flag_b, bytes) else flag_b
            txt = txt_b.decode() if isinstance(txt_b, bytes) else txt_b
            runs.append((flag, txt))
        runs.append(("", rest))
        self._paras.append(_Para("Normal", tuple(runs)))

    # ------------------------------------------------------------------
    # document.xml serialisation
    # ------------------------------------------------------------------

    def _serialize_document_xml(self) -> str:
        out: List[str] = []
        out.append('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>')
        out.append(f'<w:document {W_PREFIX}><w:body>')
        for p in self._paras:
            out.append(_para_xml(p))
        out.append(_sectPr_xml())
        out.append('</w:body></w:document>')
        return "".join(out)


# ---------------------------------------------------------------------------
# OOXML helpers
# ---------------------------------------------------------------------------


def _para_xml(p: _Para) -> str:
    runs = "".join(_run_xml(flag, text) for flag, text in p.runs)
    return f'<w:p><w:pPr><w:pStyle w:val="{p.style}"/></w:pPr>{runs}</w:p>'


def _run_xml(flag: str, text: str) -> str:
    rpr = ""
    if "b" in flag or "i" in flag:
        parts = []
        if "b" in flag:
            parts.append("<w:b/>")
        if "i" in flag:
            parts.append("<w:i/>")
        rpr = f"<w:rPr>{''.join(parts)}</w:rPr>"
    return f'<w:r>{rpr}<w:t xml:space="preserve">{xml_escape(text)}</w:t></w:r>'


def _sectPr_xml() -> str:
    return (
        '<w:sectPr>'
        '<w:pgSz w:w="12240" w:h="15840"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" '
        'w:header="720" w:footer="720" w:gutter="0"/>'
        '</w:sectPr>'
    )


def _stringify(n: Optional[nodes.ASTNode]) -> str:
    if n is None:
        return ""
    if isinstance(n, nodes.StringLit):
        return n.value
    val = getattr(n, "value", None)
    if isinstance(val, str):
        return val
    return repr(n)


def _format_penalty(p: nodes.PenaltyNode) -> List[str]:
    lines: List[str] = []
    if p.imprisonment_max or p.imprisonment_min:
        lo = _fmt_duration(p.imprisonment_min)
        hi = _fmt_duration(p.imprisonment_max)
        if lo and hi and lo != hi:
            lines.append(f"imprisonment: {lo} to {hi}")
        else:
            lines.append(f"imprisonment: up to {hi or lo}")
    if p.fine_unlimited:
        lines.append("fine: unlimited")
    elif p.fine_max or p.fine_min:
        lo = _fmt_money(p.fine_min)
        hi = _fmt_money(p.fine_max)
        if lo and hi and lo != hi:
            lines.append(f"fine: {lo} to {hi}")
        else:
            lines.append(f"fine: up to {hi or lo}")
    if p.caning_unspecified:
        lines.append("caning: liable to caning (strokes unspecified)")
    elif p.caning_max is not None:
        lo = p.caning_min or 0
        lines.append(f"caning: {lo}–{p.caning_max} strokes")
    if p.death_penalty:
        lines.append("death penalty")
    if p.combinator:
        lines.append(f"(combinator: {p.combinator})")
    if p.condition:
        lines.append(f"(when: {p.condition})")
    if p.nested:
        lines.append("Nested:")
        for sub in _format_penalty(p.nested):
            lines.append("  " + sub)
    if p.mandatory_min_imprisonment:
        lines.append(f"mandatory minimum imprisonment: {_fmt_duration(p.mandatory_min_imprisonment)}")
    if p.mandatory_min_fine:
        lines.append(f"mandatory minimum fine: {_fmt_money(p.mandatory_min_fine)}")
    return lines


def _fmt_duration(d: Optional[nodes.ASTNode]) -> str:
    if d is None:
        return ""
    val = getattr(d, "value", None)
    unit = getattr(d, "unit", None)
    if val is not None and unit:
        return f"{val} {unit}"
    return _stringify(d)


def _fmt_money(m: Optional[nodes.MoneyNode]) -> str:
    if m is None:
        return ""
    amt = getattr(m, "amount", None)
    cur = getattr(m, "currency", None)
    sym = getattr(cur, "value", cur) if cur else ""
    if amt is not None:
        try:
            return f"{sym}{int(amt):,}" if float(amt).is_integer() else f"{sym}{amt}"
        except (TypeError, ValueError):
            return f"{sym}{amt}"
    return _stringify(m)


# ---------------------------------------------------------------------------
# .docx package writer
# ---------------------------------------------------------------------------


_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

_DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

_STYLES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    f'<w:styles {W_PREFIX}>'
    '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
    '<w:name w:val="Normal"/><w:qFormat/></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading1">'
    '<w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading2">'
    '<w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="200" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="26"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Heading3">'
    '<w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:spacing w:before="160" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr>'
    '<w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="Quote">'
    '<w:name w:val="Quote"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:ind w:left="720"/></w:pPr>'
    '<w:rPr><w:i/></w:rPr></w:style>'
    '<w:style w:type="paragraph" w:styleId="ListBullet">'
    '<w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:qFormat/>'
    '<w:pPr><w:ind w:left="360" w:hanging="360"/></w:pPr></w:style>'
    '</w:styles>'
)


def _write_docx_package(document_xml: str, path: str) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CONTENT_TYPES)
        z.writestr("_rels/.rels", _ROOT_RELS)
        z.writestr("word/_rels/document.xml.rels", _DOCUMENT_RELS)
        z.writestr("word/document.xml", document_xml)
        z.writestr("word/styles.xml", _STYLES_XML)
    with open(path, "wb") as fh:
        fh.write(buf.getvalue())
