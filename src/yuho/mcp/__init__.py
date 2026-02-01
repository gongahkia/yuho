"""
Yuho MCP (Model Context Protocol) module.

Exposes Yuho functionality to AI assistants and editors via MCP.
Provides tools for parsing, transpiling, and explaining legal statutes.
"""

from yuho.mcp.server import create_server, YuhoMCPServer

__all__ = ["create_server", "YuhoMCPServer"]
