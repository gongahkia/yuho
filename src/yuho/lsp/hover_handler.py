"""
Hover handler for Yuho LSP.

Provides hover information for keywords, types, and user-defined symbols.
"""

from typing import List, Optional, TYPE_CHECKING, Callable

try:
    from lsprotocol import types as lsp
except ImportError:
    raise ImportError(
        "LSP dependencies not installed. Install with: pip install yuho[lsp]"
    )

if TYPE_CHECKING:
    from yuho.lsp.server import DocumentState
    from yuho.ast.nodes import TypeNode

# Yuho keywords for hover
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


def get_hover(
    doc_state: Optional["DocumentState"],
    word: Optional[str],
    type_to_str: Callable[["TypeNode"], str],
) -> Optional[lsp.Hover]:
    """Get hover information for word at position."""
    if not word:
        return None
    
    hover_content: List[str] = []
    
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
                fields = ", ".join(f"{f.name}: {type_to_str(f.type_annotation)}" 
                                   for f in struct.fields)
                hover_content.append(f"```yuho\nstruct {struct.name} {{\n  {fields}\n}}\n```")
                break
        
        # Check functions
        for func in doc_state.ast.function_defs:
            if func.name == word:
                params = ", ".join(f"{p.name}: {type_to_str(p.type_annotation)}" 
                                  for p in func.params)
                ret = f" -> {type_to_str(func.return_type)}" if func.return_type else ""
                hover_content.append(f"```yuho\nfn {func.name}({params}){ret}\n```")
                break
        
        # Check statutes
        for statute in doc_state.ast.statutes:
            if statute.section_number == word or f"S{statute.section_number}" == word:
                title = statute.title.value if statute.title else "Untitled"
                hover_content.append(f"**Statute Section {statute.section_number}**: {title}")
                
                # Add element summary
                if statute.elements:
                    hover_content.append("\n**Elements:**")
                    for elem in statute.elements:
                        hover_content.append(f"- {elem.element_type}: {elem.name}")
                
                # Add penalty summary
                if statute.penalty:
                    hover_content.append("\n**Penalty:**")
                    if statute.penalty.imprisonment_max:
                        hover_content.append(f"- Imprisonment: up to {statute.penalty.imprisonment_max}")
                    if statute.penalty.fine_max:
                        hover_content.append(f"- Fine: up to {statute.penalty.fine_max}")
                break
    
    if not hover_content:
        return None
    
    return lsp.Hover(
        contents=lsp.MarkupContent(
            kind=lsp.MarkupKind.Markdown,
            value="\n".join(hover_content),
        )
    )
