"""
Completion handler for Yuho LSP.

Provides code completion for keywords, types, and user-defined symbols.
"""

from typing import List, Dict, Optional, TYPE_CHECKING

try:
    from lsprotocol import types as lsp
except ImportError:
    raise ImportError("LSP dependencies not installed. Install with: pip install yuho[lsp]")

if TYPE_CHECKING:
    from yuho.lsp.server import DocumentState

# Yuho keywords for completion
YUHO_KEYWORDS = [
    "struct",
    "fn",
    "match",
    "case",
    "consequence",
    "pass",
    "return",
    "statute",
    "subsection",                        # G5
    "definitions",
    "elements",
    "penalty",
    "illustration",
    "exception",
    "caselaw",
    "parties",
    "import",
    "from",
    "referencing",                       # cross-section refs
    "actus_reus",
    "mens_rea",
    "circumstance",
    "obligation",                        # deontic triple
    "prohibition",
    "permission",
    "all_of",
    "any_of",
    "imprisonment",
    "fine",
    "caning",
    "death",
    "supplementary",
    "minimum",
    "strokes",
    # G8 / G12 penalty combinators
    "cumulative",
    "alternative",
    "or_both",
    "when",                              # G9
    "concurrent",                        # sentencing
    "consecutive",
    "unlimited",                         # G8 sentinel (fine := unlimited)
    "unspecified",                       # G14 sentinel (caning := unspecified)
    # G6 / phase 11 / 13 lifecycle
    "effective",
    "repealed",
    "subsumes",
    "amends",
    # G13 exception priority
    "priority",
    "defeats",
    "burden",
    "prosecution",
    "defence",
    "beyond_reasonable_doubt",
    "balance_of_probabilities",
    "prima_facie",
    "caused_by",
    "actor",
    "patient",
    "temporal",
    "precedes",
    "during",
    "after",
    # value qualifiers
    "fact",
    "conclusion",
    "presumed",
    "unless",
    "TRUE",
    "FALSE",
]


# Context-sensitive completion hints. When the trigger character or
# previous token matches a key, only the listed keywords are suggested.
# Far more useful than dumping the full keyword table every time.
CONTEXTUAL_HINTS: Dict[str, List[str]] = {
    # after `penalty ` (outer block)
    "penalty": ["cumulative", "alternative", "or_both", "when",
                "concurrent", "consecutive"],
    # after `caning := `
    "caning_value": ["unspecified"],
    # after `fine := `
    "fine_value": ["unlimited"],
    # after `exception { "...";` — continuation keywords
    "exception": ["priority", "defeats", "when"],
    # inside element groups
    "element_group": ["actus_reus", "mens_rea", "circumstance",
                      "obligation", "prohibition", "permission",
                      "all_of", "any_of"],
    # statute-block members
    "statute_body": ["definitions", "elements", "penalty",
                     "illustration", "exception", "subsection",
                     "caselaw", "parties"],
}

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


def _line_prefix(doc_state: Optional["DocumentState"], position: lsp.Position) -> str:
    """Return the text of the current line up to the cursor, if we have it."""
    if not doc_state: return ""
    source = getattr(doc_state, "source", None) or getattr(doc_state, "text", None)
    if not source: return ""
    lines = source.splitlines()
    if position.line >= len(lines): return ""
    return lines[position.line][: position.character]


def _contextual_keywords(prefix: str) -> Optional[List[str]]:
    """Pick a contextual keyword subset based on what comes before the cursor.
    Returns None if no strong context match — caller falls back to full list.
    """
    import re as _re
    stripped = prefix.rstrip()
    # `caning := ` → suggest unspecified
    if _re.search(r"\bcaning\s*:=\s*$", stripped):
        return CONTEXTUAL_HINTS["caning_value"]
    # `fine := ` → suggest unlimited
    if _re.search(r"\bfine\s*:=\s*$", stripped):
        return CONTEXTUAL_HINTS["fine_value"]
    # `penalty ` alone on a line → penalty combinators + when + sentencing
    if _re.search(r"^\s*penalty\s*$", prefix):
        return CONTEXTUAL_HINTS["penalty"]
    # inside an open `all_of {` / `any_of {` / `elements {` block →
    # element-type keywords. Cheap heuristic: the prefix line has `all_of`
    # or `any_of` or starts under an `elements` block (imperfect but useful).
    if _re.search(r"\b(all_of|any_of)\s*\{?\s*$", stripped):
        return CONTEXTUAL_HINTS["element_group"]
    return None


def get_completions(
    doc_state: Optional["DocumentState"],
    uri: str,
    position: lsp.Position,
) -> lsp.CompletionList:
    """Get completion items for position."""
    items: List[lsp.CompletionItem] = []

    prefix = _line_prefix(doc_state, position)
    contextual = _contextual_keywords(prefix)

    if contextual:
        # Narrow list for a known-context position — much higher signal.
        for kw in contextual:
            items.append(
                lsp.CompletionItem(
                    label=kw,
                    kind=lsp.CompletionItemKind.Keyword,
                    detail="contextual keyword",
                    sort_text=f"00_{kw}",
                )
            )
        # Still return — skip the full-keyword dump when we have a
        # strong contextual signal. Symbols (structs/funcs/statutes)
        # are unlikely to be appropriate here.
        return lsp.CompletionList(is_incomplete=False, items=items)

    # Keywords
    for kw in YUHO_KEYWORDS:
        items.append(
            lsp.CompletionItem(
                label=kw,
                kind=lsp.CompletionItemKind.Keyword,
                detail="keyword",
            )
        )

    # Built-in types
    for typ in YUHO_TYPES:
        items.append(
            lsp.CompletionItem(
                label=typ,
                kind=lsp.CompletionItemKind.TypeParameter,
                detail="built-in type",
            )
        )

    # Symbols from current document
    if doc_state and doc_state.ast:
        # Struct names
        for struct in doc_state.ast.type_defs:
            items.append(
                lsp.CompletionItem(
                    label=struct.name,
                    kind=lsp.CompletionItemKind.Struct,
                    detail=f"struct {struct.name}",
                )
            )

        # Function names
        for func in doc_state.ast.function_defs:
            params = ", ".join(p.name for p in func.params)
            items.append(
                lsp.CompletionItem(
                    label=func.name,
                    kind=lsp.CompletionItemKind.Function,
                    detail=f"fn {func.name}({params})",
                )
            )

        # Statute sections
        for statute in doc_state.ast.statutes:
            title = statute.title.value if statute.title else ""
            items.append(
                lsp.CompletionItem(
                    label=f"S{statute.section_number}",
                    kind=lsp.CompletionItemKind.Module,
                    detail=f"statute {statute.section_number}: {title}",
                )
            )

    return lsp.CompletionList(is_incomplete=False, items=items)
