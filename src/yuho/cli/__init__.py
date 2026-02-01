"""
Yuho CLI module - command-line interface for the Yuho language.

Provides commands for:
- check: Parse and validate .yh files
- transpile: Convert to JSON, English, Mermaid, etc.
- explain: LLM-powered explanations
- serve: Start MCP server
- contribute: Package statutes for sharing
"""

from yuho.cli.main import cli

__all__ = ["cli"]
