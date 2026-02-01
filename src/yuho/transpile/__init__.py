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

__all__ = [
    "TranspileTarget",
    "TranspilerBase",
    "JSONTranspiler",
    "JSONLDTranspiler",
    "EnglishTranspiler",
    "MermaidTranspiler",
    "AlloyTranspiler",
]


def get_transpiler(target: TranspileTarget) -> TranspilerBase:
    """
    Get a transpiler instance for the given target.

    Args:
        target: The transpilation target

    Returns:
        A transpiler instance for the target
    """
    transpilers = {
        TranspileTarget.JSON: JSONTranspiler,
        TranspileTarget.JSON_LD: JSONLDTranspiler,
        TranspileTarget.ENGLISH: EnglishTranspiler,
        TranspileTarget.MERMAID: MermaidTranspiler,
        TranspileTarget.ALLOY: AlloyTranspiler,
    }

    transpiler_cls = transpilers.get(target)
    if not transpiler_cls:
        raise ValueError(f"No transpiler registered for target: {target}")

    return transpiler_cls()
