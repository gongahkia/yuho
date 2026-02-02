"""
Yuho transpilation module - multi-target code generation.

Supports transpilation to:
- JSON: Structured AST representation
- JSON-LD: Linked data with legal ontology
- English: Controlled natural language
- LaTeX: Legal document formatting
- Mermaid: Decision tree flowcharts
- Alloy: Formal verification models
"""

from yuho.transpile.base import TranspileTarget, TranspilerBase
from yuho.transpile.json_transpiler import JSONTranspiler
from yuho.transpile.jsonld_transpiler import JSONLDTranspiler
from yuho.transpile.english_transpiler import EnglishTranspiler
from yuho.transpile.mermaid_transpiler import MermaidTranspiler
from yuho.transpile.alloy_transpiler import AlloyTranspiler
from yuho.transpile.latex_transpiler import LaTeXTranspiler, compile_to_pdf
from yuho.transpile.registry import TranspilerRegistry

__all__ = [
    "TranspileTarget",
    "TranspilerBase",
    "TranspilerRegistry",
    "JSONTranspiler",
    "JSONLDTranspiler",
    "EnglishTranspiler",
    "LaTeXTranspiler",
    "compile_to_pdf",
    "MermaidTranspiler",
    "AlloyTranspiler",
    "get_transpiler",
]


def get_transpiler(target: TranspileTarget) -> TranspilerBase:
    """
    Get a transpiler instance for the given target.

    This is a convenience function that uses the TranspilerRegistry singleton.

    Args:
        target: The transpilation target

    Returns:
        A transpiler instance for the target

    Raises:
        KeyError: If no transpiler is registered for the target
    """
    return TranspilerRegistry.instance().get(target)
