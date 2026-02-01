"""
Yuho v5 - A domain-specific language for encoding legal statutes

This package provides:
- Parser: tree-sitter based parser for .yh files
- AST: Internal representation for semantic analysis
- Transpilers: Code generation to JSON, JSON-LD, English, LaTeX, Mermaid, Alloy
- LSP: Language Server Protocol implementation
- MCP: Model Context Protocol server
"""

__version__ = "5.0.0"

from yuho.parser import Parser, SourceLocation

__all__ = ["Parser", "SourceLocation", "__version__"]
