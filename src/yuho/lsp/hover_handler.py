"""
Hover handler for Yuho LSP.

Provides hover information for keywords, types, and user-defined symbols.
"""

from typing import List, Optional, TYPE_CHECKING, Callable, Dict, Any
from pathlib import Path

from yuho.ast import nodes

try:
    from lsprotocol import types as lsp
except ImportError:
    raise ImportError("LSP dependencies not installed. Install with: pip install yuho[lsp]")

if TYPE_CHECKING:
    from yuho.lsp.server import DocumentState
    from yuho.ast.nodes import TypeNode

# Yuho keywords for hover
YUHO_KEYWORDS = [
    "struct",
    "fn",
    "match",
    "case",
    "consequence",
    "pass",
    "return",
    "statute",
    "definitions",
    "elements",
    "penalty",
    "illustration",
    "import",
    "from",
    "actus_reus",
    "mens_rea",
    "circumstance",
    "imprisonment",
    "fine",
    "supplementary",
    "TRUE",
    "FALSE",
]

# Yuho built-in types
YUHO_TYPES = [
    "int",
    "float",
    "bool",
    "string",
    "money",
    "percent",
    "date",
    "duration",
    "void",
]

KEYWORD_DOCS = {
    "struct": "Defines a structured type with named fields.",
    "fn": "Defines a function.",
    "match": "Pattern matching expression.",
    "case": "Case arm in a match expression.",
    "statute": "Defines a legal statute with elements and penalties.",
    "elements": "Section containing the elements of an offense.",
    "penalty": "Section specifying the punishment for an offense.",
    "actus_reus": "Physical/conduct element of an offense (guilty act).",
    "mens_rea": "Mental element of an offense (guilty mind).",
    "circumstance": "Circumstantial element required for the offense.",
}

TYPE_DOCS = {
    "int": "Integer number type (whole numbers).",
    "float": "Floating-point number type (decimals).",
    "bool": "Boolean type: TRUE or FALSE.",
    "string": "Text string type.",
    "money": "Monetary amount with currency (e.g., $1000.00 SGD).",
    "percent": "Percentage value (0-100%).",
    "date": "Calendar date (YYYY-MM-DD).",
    "duration": "Time duration (years, months, days, etc.).",
    "void": "No value type (for procedures).",
}


# Cached canonical-section lookup (loaded once per LSP process). Each
# entry maps section number → {marginal_note, text, amendments, sso_url,
# L1, L2, L3 …}. Lazy-loaded on first hover query.
_CANONICAL_CACHE: Optional[Dict[str, Dict[str, Any]]] = None
_COVERAGE_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def _load_canonical_and_coverage() -> None:
    """Populate the module-level caches from _raw/act.json + coverage.json."""
    global _CANONICAL_CACHE, _COVERAGE_CACHE
    if _CANONICAL_CACHE is not None and _COVERAGE_CACHE is not None:
        return
    try:
        import json
        # Walk up until we find a `library/penal_code` directory or give up.
        here = Path(__file__).resolve()
        root = here
        for _ in range(6):
            root = root.parent
            if (root / "library" / "penal_code").is_dir():
                break
        raw = root / "library" / "penal_code" / "_raw" / "act.json"
        cov = root / "library" / "penal_code" / "_coverage" / "coverage.json"
        _CANONICAL_CACHE = {}
        _COVERAGE_CACHE = {}
        if raw.is_file():
            d = json.loads(raw.read_text())
            act_code = d.get("act_code", "PC1871")
            for s in d.get("sections", []):
                n = s.get("number")
                if not n: continue
                anchor = s.get("anchor_id") or f"pr{n}-"
                _CANONICAL_CACHE[n] = {
                    "marginal_note": s.get("marginal_note", ""),
                    "text": s.get("text", ""),
                    "sub_items": s.get("sub_items", []),
                    "amendments": s.get("amendments", []),
                    "sso_url": f"https://sso.agc.gov.sg/Act/{act_code}?ProvIds={anchor}#{anchor}",
                }
        if cov.is_file():
            d = json.loads(cov.read_text())
            for row in d.get("sections", []):
                n = row.get("number")
                if n: _COVERAGE_CACHE[n] = row
    except Exception:
        _CANONICAL_CACHE = {}
        _COVERAGE_CACHE = {}


def _canonical_for(section: str) -> Optional[Dict[str, Any]]:
    _load_canonical_and_coverage()
    return (_CANONICAL_CACHE or {}).get(section)


def _coverage_for(section: str) -> Optional[Dict[str, Any]]:
    _load_canonical_and_coverage()
    return (_COVERAGE_CACHE or {}).get(section)


def get_hover(
    doc_state: Optional["DocumentState"],
    word: Optional[str],
    type_to_str: Callable[["TypeNode"], str],
) -> Optional[lsp.Hover]:
    """Get hover information for word at position."""
    if not word:
        return None

    hover_content: List[str] = []

    def _append_element_summary(
        elements: (
            List[nodes.ElementNode | nodes.ElementGroupNode]
            | tuple[nodes.ElementNode | nodes.ElementGroupNode, ...]
        )
    ) -> None:
        for elem in elements:
            if isinstance(elem, nodes.ElementNode):
                hover_content.append(f"- {elem.element_type}: {elem.name}")
                continue
            _append_element_summary(elem.members)

    # Check if it's a keyword
    if word in YUHO_KEYWORDS:
        hover_content.append(f"**keyword** `{word}`")
        if word in KEYWORD_DOCS:
            hover_content.append(KEYWORD_DOCS[word])

    # Check if it's a built-in type
    elif word in YUHO_TYPES:
        hover_content.append(f"**type** `{word}`")
        if word in TYPE_DOCS:
            hover_content.append(TYPE_DOCS[word])

    # Check AST for user-defined symbols
    elif doc_state and doc_state.ast:
        # Check structs
        for struct in doc_state.ast.type_defs:
            if struct.name == word:
                fields = ", ".join(
                    f"{f.name}: {type_to_str(f.type_annotation)}" for f in struct.fields
                )
                hover_content.append(f"```yuho\nstruct {struct.name} {{\n  {fields}\n}}\n```")
                break

        # Check functions
        for func in doc_state.ast.function_defs:
            if func.name == word:
                params = ", ".join(
                    f"{p.name}: {type_to_str(p.type_annotation)}" for p in func.params
                )
                ret = f" -> {type_to_str(func.return_type)}" if func.return_type else ""
                hover_content.append(f"```yuho\nfn {func.name}({params}){ret}\n```")
                break

        # Check statutes
        for statute in doc_state.ast.statutes:
            if statute.section_number == word or f"S{statute.section_number}" == word:
                title = statute.title.value if statute.title else "Untitled"
                hover_content.append(f"**Statute Section {statute.section_number}** — {title}")

                # LSP buff-up: SSO link + canonical excerpt + coverage
                canonical = _canonical_for(statute.section_number)
                coverage = _coverage_for(statute.section_number)
                if canonical:
                    if canonical.get("sso_url"):
                        hover_content.append(f"[↗ canonical SSO]({canonical['sso_url']})")
                    marg = canonical.get("marginal_note", "")
                    if marg and marg != title:
                        hover_content.append(f"*Canonical marginal note:* {marg}")
                    text = canonical.get("text", "")
                    if text:
                        # first ~280 chars
                        excerpt = text[:280].rstrip()
                        if len(text) > 280: excerpt += "…"
                        hover_content.append(f"\n> {excerpt}")
                if coverage:
                    def _tick(b): return "✓" if b else "·"
                    l1 = _tick(coverage.get("L1")); l2 = _tick(coverage.get("L2"))
                    l3 = _tick(coverage.get("L3"))
                    verify = (coverage.get("L3_verified_on") or "") + " " + (coverage.get("L3_verified_by") or "")
                    hover_content.append(
                        f"\n**Coverage:** L1 {l1} · L2 {l2} · L3 {l3}"
                        + (f" — verified {verify.strip()}" if verify.strip() else "")
                    )

                # Add element summary
                if statute.elements:
                    hover_content.append("\n**Elements:**")
                    _append_element_summary(statute.elements)

                # Add penalty summary
                if statute.penalty:
                    hover_content.append("\n**Penalty:**")
                    if statute.penalty.imprisonment_max:
                        hover_content.append(
                            f"- Imprisonment: up to {statute.penalty.imprisonment_max}"
                        )
                    if statute.penalty.fine_max:
                        hover_content.append(f"- Fine: up to {statute.penalty.fine_max}")
                    elif statute.penalty.fine_unlimited:
                        hover_content.append("- Fine: unlimited")
                    if statute.penalty.caning_max:
                        hover_content.append(
                            f"- Caning: up to {statute.penalty.caning_max} strokes"
                        )
                    elif statute.penalty.caning_unspecified:
                        hover_content.append("- Caning: liable (no stroke count specified)")

                # Illustration / subsection / exception counts
                counts = []
                if statute.illustrations: counts.append(f"{len(statute.illustrations)} illustration(s)")
                if statute.subsections: counts.append(f"{len(statute.subsections)} subsection(s)")
                if statute.exceptions: counts.append(f"{len(statute.exceptions)} exception(s)")
                if counts:
                    hover_content.append(f"\n*Structure:* {', '.join(counts)}")
                break

    if not hover_content:
        return None

    return lsp.Hover(
        contents=lsp.MarkupContent(
            kind=lsp.MarkupKind.Markdown,
            value="\n".join(hover_content),
        )
    )
