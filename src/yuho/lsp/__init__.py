"""
Yuho LSP (Language Server Protocol) module.

Provides IDE features for .yh files:
- Syntax error diagnostics
- Code completion
- Hover information
- Go to definition
- Find references
"""

from yuho.lsp.server import YuhoLanguageServer

__all__ = ["YuhoLanguageServer"]
