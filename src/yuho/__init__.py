"""
Yuho v5 - A domain-specific language for encoding legal statutes

This package provides:
- Parser: tree-sitter based parser for .yh files
- AST: Internal representation for semantic analysis
- Transpilers: JSON, English, LaTeX, Mermaid flowchart/mindmap, Alloy, DOCX, Akoma Ntoso
- LSP: Language Server Protocol implementation
- MCP: Model Context Protocol server
"""

__version__ = "5.1.0"

from yuho.parser import Parser, SourceLocation

__all__ = ["Parser", "SourceLocation", "__version__"]
