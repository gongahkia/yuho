"""
Yuho MCP Server implementation.

Provides MCP tools for parsing, transpiling, and analyzing Yuho code.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent, Resource
except ImportError:
    # Provide mock classes for when mcp is not installed
    class Server:
        def __init__(self, name: str):
            self.name = name

        def tool(self):
            def decorator(func):
                return func
            return decorator

        def resource(self, uri: str):
            def decorator(func):
                return func
            return decorator

    def stdio_server():
        raise ImportError("MCP dependencies not installed. Install with: pip install yuho[mcp]")


class YuhoMCPServer:
    """
    MCP Server exposing Yuho functionality.

    Tools:
    - yuho_check: Validate Yuho source
    - yuho_transpile: Convert to other formats
    - yuho_explain: Generate explanations
    - yuho_parse: Get AST representation
    - yuho_format: Format source code
    - yuho_complete: Get completions
    - yuho_hover: Get hover info
    - yuho_definition: Find definition

    Resources:
    - yuho://grammar: Tree-sitter grammar
    - yuho://types: Built-in types
    - yuho://library/{section}: Statute by section
    """

    def __init__(self):
        self.server = Server("yuho-mcp")
        self._register_tools()
        self._register_resources()

    def _register_tools(self):
        """Register MCP tools."""

        @self.server.tool()
        async def yuho_check(file_content: str) -> Dict[str, Any]:
            """
            Validate Yuho source code.

            Args:
                file_content: The Yuho source code to validate

            Returns:
                {valid: bool, errors: list of error dicts}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder

            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {
                    "valid": False,
                    "errors": [
                        {
                            "message": err.message,
                            "line": err.location.line,
                            "col": err.location.col,
                        }
                        for err in result.errors
                    ],
                }

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)
                return {
                    "valid": True,
                    "errors": [],
                    "stats": {
                        "statutes": len(ast.statutes),
                        "structs": len(ast.type_defs),
                        "functions": len(ast.function_defs),
                    },
                }
            except Exception as e:
                return {
                    "valid": False,
                    "errors": [{"message": str(e), "line": 1, "col": 1}],
                }

        @self.server.tool()
        async def yuho_transpile(file_content: str, target: str) -> Dict[str, Any]:
            """
            Transpile Yuho source to another format.

            Args:
                file_content: The Yuho source code
                target: Target format (json, jsonld, english, mermaid, alloy)

            Returns:
                {output: str} or {error: str}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder
            from yuho.transpile import TranspileTarget, get_transpiler

            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {"error": f"Parse error: {result.errors[0].message}"}

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)

                transpile_target = TranspileTarget.from_string(target)
                transpiler = get_transpiler(transpile_target)
                output = transpiler.transpile(ast)

                return {"output": output}
            except ValueError as e:
                return {"error": f"Invalid target: {e}"}
            except Exception as e:
                return {"error": str(e)}

        @self.server.tool()
        async def yuho_explain(file_content: str, section: Optional[str] = None) -> Dict[str, Any]:
            """
            Generate natural language explanation.

            Args:
                file_content: The Yuho source code
                section: Optional section number to explain

            Returns:
                {explanation: str} or {error: str}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder
            from yuho.transpile import EnglishTranspiler

            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {"error": f"Parse error: {result.errors[0].message}"}

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)

                # Filter to specific section if requested
                if section:
                    from yuho.ast.nodes import ModuleNode
                    matching = [s for s in ast.statutes if section in s.section_number]
                    if not matching:
                        return {"error": f"Section {section} not found"}
                    ast = ModuleNode(
                        imports=ast.imports,
                        type_defs=ast.type_defs,
                        function_defs=ast.function_defs,
                        statutes=tuple(matching),
                        variables=ast.variables,
                    )

                transpiler = EnglishTranspiler()
                explanation = transpiler.transpile(ast)

                return {"explanation": explanation}
            except Exception as e:
                return {"error": str(e)}

        @self.server.tool()
        async def yuho_parse(file_content: str) -> Dict[str, Any]:
            """
            Parse Yuho source and return AST.

            Args:
                file_content: The Yuho source code

            Returns:
                {ast: dict} or {error: str}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder
            from yuho.transpile import JSONTranspiler

            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {"error": f"Parse error: {result.errors[0].message}"}

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)

                # Use JSON transpiler to serialize AST
                json_transpiler = JSONTranspiler(include_locations=False)
                ast_json = json_transpiler.transpile(ast)

                return {"ast": json.loads(ast_json)}
            except Exception as e:
                return {"error": str(e)}

        @self.server.tool()
        async def yuho_format(file_content: str) -> Dict[str, Any]:
            """
            Format Yuho source code.

            Args:
                file_content: The Yuho source code

            Returns:
                {formatted: str} or {error: str}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder
            from yuho.cli.commands.fmt import _format_module

            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {"error": f"Parse error: {result.errors[0].message}"}

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)
                formatted = _format_module(ast)

                return {"formatted": formatted}
            except Exception as e:
                return {"error": str(e)}

        @self.server.tool()
        async def yuho_complete(file_content: str, line: int, col: int) -> Dict[str, Any]:
            """
            Get completions at position.

            Args:
                file_content: The Yuho source code
                line: Line number (1-indexed)
                col: Column number (1-indexed)

            Returns:
                {completions: list of completion items}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder

            completions = []

            # Keywords
            keywords = [
                "struct", "fn", "match", "case", "consequence", "pass", "return",
                "statute", "definitions", "elements", "penalty", "illustration",
                "import", "from", "TRUE", "FALSE",
            ]
            completions.extend({"label": kw, "kind": "keyword"} for kw in keywords)

            # Types
            types = ["int", "float", "bool", "string", "money", "percent", "date", "duration"]
            completions.extend({"label": t, "kind": "type"} for t in types)

            # Parse to get symbols
            parser = Parser()
            result = parser.parse(file_content)

            if result.is_valid:
                try:
                    builder = ASTBuilder(file_content)
                    ast = builder.build(result.root_node)

                    # Add struct names
                    for struct in ast.type_defs:
                        completions.append({"label": struct.name, "kind": "struct"})

                    # Add function names
                    for func in ast.function_defs:
                        completions.append({"label": func.name, "kind": "function"})

                except Exception:
                    pass

            return {"completions": completions}

        @self.server.tool()
        async def yuho_hover(file_content: str, line: int, col: int) -> Dict[str, Any]:
            """
            Get hover information at position.

            Args:
                file_content: The Yuho source code
                line: Line number (1-indexed)
                col: Column number (1-indexed)

            Returns:
                {info: str} or {info: null}
            """
            # TODO: Implement proper position lookup
            return {"info": None}

        @self.server.tool()
        async def yuho_definition(file_content: str, line: int, col: int) -> Dict[str, Any]:
            """
            Find definition location.

            Args:
                file_content: The Yuho source code
                line: Line number (1-indexed)
                col: Column number (1-indexed)

            Returns:
                {location: {line, col}} or {location: null}
            """
            # TODO: Implement proper definition lookup
            return {"location": None}

    def _register_resources(self):
        """Register MCP resources."""

        @self.server.resource("yuho://grammar")
        async def get_grammar() -> str:
            """Return the tree-sitter grammar source."""
            grammar_path = Path(__file__).parent.parent.parent / "tree-sitter-yuho" / "grammar.js"
            if grammar_path.exists():
                return grammar_path.read_text()
            return "// Grammar not found"

        @self.server.resource("yuho://types")
        async def get_types() -> str:
            """Return built-in type definitions."""
            return """
Yuho Built-in Types:

int       - Integer numbers (e.g., 42, -10)
float     - Floating point numbers (e.g., 3.14, -2.5)
bool      - Boolean values (TRUE, FALSE)
string    - Text strings (e.g., "hello")
money     - Monetary amounts with currency (e.g., $100.00, SGD1000)
percent   - Percentages 0-100 (e.g., 50%)
date      - ISO8601 dates (e.g., 2024-01-15)
duration  - Time periods (e.g., 3 years, 6 months)
void      - No value / null type
"""

        @self.server.resource("yuho://library/{section}")
        async def get_statute(section: str) -> str:
            """Return statute source by section number."""
            # TODO: Implement statute library lookup
            return f"// Statute {section} not found in library"

    def run_stdio(self):
        """Run the server using stdio transport."""
        import asyncio
        asyncio.run(self._run_stdio())

    async def _run_stdio(self):
        """Async stdio runner."""
        async with stdio_server() as streams:
            await self.server.run(
                streams[0],
                streams[1],
                self.server.create_initialization_options(),
            )

    def run_http(self, host: str = "127.0.0.1", port: int = 8080):
        """Run the server using HTTP transport."""
        import asyncio
        from aiohttp import web

        async def handle_mcp(request):
            # Simple HTTP handler for MCP
            data = await request.json()
            # Process MCP request...
            return web.json_response({"status": "ok"})

        app = web.Application()
        app.router.add_post("/mcp", handle_mcp)

        web.run_app(app, host=host, port=port)


def create_server() -> YuhoMCPServer:
    """Create and return a YuhoMCPServer instance."""
    return YuhoMCPServer()
