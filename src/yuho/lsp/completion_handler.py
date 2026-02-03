"""
Completion handler for Yuho LSP.

Provides code completion for keywords, types, and user-defined symbols.
"""

from typing import List, Dict, Optional, TYPE_CHECKING

try:
    from lsprotocol import types as lsp
except ImportError:
    raise ImportError(
        "LSP dependencies not installed. Install with: pip install yuho[lsp]"
    )

if TYPE_CHECKING:
    from yuho.lsp.server import DocumentState

# Yuho keywords for completion
YUHO_KEYWORDS = [
    "struct", "fn", "match", "case", "consequence", "pass", "return",
    "statute", "definitions", "elements", "penalty", "illustration",
    "import", "from", "actus_reus", "mens_rea", "circumstance",
    "imprisonment", "fine", "supplementary", "TRUE", "FALSE",
]

# Yuho built-in types
YUHO_TYPES = [
    "int", "float", "bool", "string", "money", "percent", "date", "duration", "void",
]


def get_completions(
    doc_state: Optional["DocumentState"],
    uri: str,
    position: lsp.Position,
) -> lsp.CompletionList:
    """Get completion items for position."""
    items: List[lsp.CompletionItem] = []

    # Keywords
    for kw in YUHO_KEYWORDS:
        items.append(lsp.CompletionItem(
            label=kw,
            kind=lsp.CompletionItemKind.Keyword,
            detail="keyword",
        ))

    # Built-in types
    for typ in YUHO_TYPES:
        items.append(lsp.CompletionItem(
            label=typ,
            kind=lsp.CompletionItemKind.TypeParameter,
            detail="built-in type",
        ))

    # Symbols from current document
    if doc_state and doc_state.ast:
        # Struct names
        for struct in doc_state.ast.type_defs:
            items.append(lsp.CompletionItem(
                label=struct.name,
                kind=lsp.CompletionItemKind.Struct,
                detail=f"struct {struct.name}",
            ))

        # Function names
        for func in doc_state.ast.function_defs:
            params = ", ".join(p.name for p in func.params)
            items.append(lsp.CompletionItem(
                label=func.name,
                kind=lsp.CompletionItemKind.Function,
                detail=f"fn {func.name}({params})",
            ))

        # Statute sections
        for statute in doc_state.ast.statutes:
            title = statute.title.value if statute.title else ""
            items.append(lsp.CompletionItem(
                label=f"S{statute.section_number}",
                kind=lsp.CompletionItemKind.Module,
                detail=f"statute {statute.section_number}: {title}",
            ))

    return lsp.CompletionList(is_incomplete=False, items=items)
