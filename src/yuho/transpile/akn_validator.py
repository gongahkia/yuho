"""Akoma Ntoso structural validator for emitted XML.

Runs a focused, dependency-free structural check on AKN documents
emitted by :class:`yuho.transpile.AkomaNtosoTranspiler`. The checks
encode the AKN 1.0 invariants the Yuho transpiler depends on:

* Root element is ``<akomaNtoso>`` in the OASIS namespace.
* Direct child is ``<act>``.
* ``<act>`` has both ``<meta>`` and ``<body>`` children.
* ``<meta>`` carries an ``<identification>`` -> ``<FRBRWork>`` block
  with ``<FRBRthis>``, ``<FRBRuri>``, ``<FRBRdate>``, ``<FRBRauthor>``,
  and ``<FRBRcountry>``.
* Every ``<section>`` carries a ``<num>``.
* All ``eId`` attribute values follow the ``<prefix>_<slug>`` pattern
  used by the transpiler (``sec_``, ``sub_``, ``exc_``, ``ill_``).
* ``<defeats>`` paragraphs that name a target via
  ``refersTo="#exc_<slug>"`` resolve within the section scope to an
  ``<hcontainer name="exception">`` with that ``eId``.

This is intentionally a structural validator, not a schema validator.
A future strengthening can layer XSD validation via ``lxml`` when the
caller provides the OASIS schema path; that path is exposed as
:func:`validate_akn_against_xsd`.

Returns
-------
:class:`AKNValidationResult` with ``ok: bool`` and ``errors: list[str]``.
The function never raises on invalid input; callers decide how to react.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

# Prefer lxml when available — Python 3.14 + Homebrew ship a stdlib
# ElementTree whose pyexpat dlopen fails against the system libexpat
# (`_XML_SetAllocTrackerActivationThreshold` symbol mismatch). lxml
# bundles its own libxml2 parser and exposes a compatible API.
try:
    from lxml import etree as _ET  # type: ignore[import-not-found]
    _PARSE_ERROR: tuple = (_ET.XMLSyntaxError,)
    _BACKEND = "lxml"
except ImportError:  # pragma: no cover
    from xml.etree import ElementTree as _ET  # type: ignore[no-redef]
    _PARSE_ERROR = (_ET.ParseError,)
    _BACKEND = "stdlib"

ET = _ET


_AKN_NS = "http://docs.oasis-open.org/legaldocml/ns/akn/3.0"
_AKN_TAG = "{" + _AKN_NS + "}"

_REQUIRED_FRBR = (
    "FRBRthis",
    "FRBRuri",
    "FRBRdate",
    "FRBRauthor",
    "FRBRcountry",
)

_EID_PATTERN = re.compile(r"^(sec|sub|exc|ill)_[A-Za-z0-9_]+$")


@dataclass(frozen=True)
class AKNValidationResult:
    """Structural validation outcome."""

    ok: bool
    errors: tuple = field(default_factory=tuple)


def _qual(local: str) -> str:
    return _AKN_TAG + local


def validate_akn(xml: str) -> AKNValidationResult:
    """Structurally validate an AKN document.

    Returns a result with all collected errors (does not short-circuit
    on the first failure, so the caller sees the full picture in one
    pass). Catches XML parse errors and reports them as the sole error.
    """
    errors: List[str] = []
    try:
        if _BACKEND == "lxml":
            root = ET.fromstring(xml.encode("utf-8"))
        else:
            root = ET.fromstring(xml)
    except _PARSE_ERROR as exc:
        return AKNValidationResult(ok=False, errors=(f"XML not well-formed: {exc}",))

    if root.tag != _qual("akomaNtoso"):
        errors.append(
            f"root element must be {{{_AKN_NS}}}akomaNtoso, got {root.tag!r}"
        )

    act = root.find(_qual("act"))
    if act is None:
        errors.append("<act> is missing as a direct child of <akomaNtoso>")
        return AKNValidationResult(ok=False, errors=tuple(errors))

    meta = act.find(_qual("meta"))
    body = act.find(_qual("body"))
    if meta is None:
        errors.append("<act> is missing required <meta> child")
    if body is None:
        errors.append("<act> is missing required <body> child")

    if meta is not None:
        identification = meta.find(_qual("identification"))
        if identification is None:
            errors.append("<meta> is missing <identification>")
        else:
            frbr_work = identification.find(_qual("FRBRWork"))
            if frbr_work is None:
                errors.append(
                    "<identification> is missing <FRBRWork> block"
                )
            else:
                for tag in _REQUIRED_FRBR:
                    if frbr_work.find(_qual(tag)) is None:
                        errors.append(f"<FRBRWork> is missing required <{tag}>")

    if body is not None:
        for sec in body.findall(_qual("section")):
            sec_eid = sec.attrib.get("eId")
            if sec_eid is None:
                errors.append("<section> is missing eId attribute")
            elif not _EID_PATTERN.match(sec_eid):
                errors.append(
                    f"<section eId={sec_eid!r}> does not match expected "
                    f"<prefix>_<slug> pattern"
                )
            num = sec.find(_qual("num"))
            if num is None or not (num.text or "").strip():
                errors.append(
                    f"<section eId={sec_eid!r}> is missing <num> with content"
                )
            # Defeats refersTo must resolve within this section's
            # exception eIds (the priority DAG names other exceptions
            # by label, not elements).
            # AKN has no first-class `<exception>`; the transpiler emits
            # exceptions as `<hcontainer name="exception" eId="exc_…">`,
            # so resolve the priority-DAG cross-refs against that shape.
            sec_exception_eids = {
                h.attrib["eId"]
                for h in sec.findall(_qual("hcontainer"))
                if h.attrib.get("name") == "exception" and "eId" in h.attrib
            }
            for p in sec.findall(f".//{_qual('p')}[@class='defeats']"):
                refers = p.attrib.get("refersTo", "")
                if refers.startswith("#") and refers[1:] not in sec_exception_eids:
                    errors.append(
                        f"<section eId={sec_eid!r}>: defeats refersTo "
                        f"{refers!r} does not resolve to a known exception"
                    )
            # Nested subsections inherit the eId pattern requirement.
            for sub in sec.findall(_qual("subsection")):
                sub_eid = sub.attrib.get("eId")
                if sub_eid is None or not _EID_PATTERN.match(sub_eid):
                    errors.append(
                        f"<subsection eId={sub_eid!r}> in section "
                        f"{sec_eid!r} does not match eId pattern"
                    )

    return AKNValidationResult(ok=not errors, errors=tuple(errors))


def validate_akn_against_xsd(xml: str, xsd_path: str) -> AKNValidationResult:
    """Optional XSD validation. Requires ``lxml`` and the OASIS XSD.

    The OASIS Akoma Ntoso schema bundle is ``akomantoso30.xsd`` (with
    its dependencies in the same directory). Pass the path to
    ``akomantoso30.xsd``; this function returns an
    :class:`AKNValidationResult` with parser-level + schema-level errors,
    or a single error indicating ``lxml`` is unavailable.
    """
    try:
        from lxml import etree  # type: ignore[import-not-found]
    except ImportError:
        return AKNValidationResult(
            ok=False,
            errors=("lxml is required for XSD validation; pip install lxml",),
        )
    try:
        with open(xsd_path, "rb") as f:
            schema_root = etree.parse(f)
        schema = etree.XMLSchema(schema_root)
    except (OSError, etree.XMLSchemaParseError) as exc:
        return AKNValidationResult(ok=False, errors=(f"failed to load XSD: {exc}",))
    try:
        doc = etree.fromstring(xml.encode("utf-8"))
    except etree.XMLSyntaxError as exc:
        return AKNValidationResult(ok=False, errors=(f"XML not well-formed: {exc}",))
    if schema.validate(doc):
        return AKNValidationResult(ok=True)
    errs = tuple(str(e) for e in schema.error_log)
    return AKNValidationResult(ok=False, errors=errs)


def _slug(s: Optional[str]) -> str:
    """Mirror of ``AkomaNtosoTranspiler._slug``: alnum + underscore only."""
    if not s:
        return ""
    return "".join(c if c.isalnum() else "_" for c in s)
