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
        self._register_prompts()

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

        @self.server.tool()
        async def yuho_references(file_content: str, line: int, col: int) -> Dict[str, Any]:
            """
            Find all references to symbol at position.

            Args:
                file_content: The Yuho source code
                line: Line number (1-indexed)
                col: Column number (1-indexed)

            Returns:
                {locations: list of {line, col, end_line, end_col}}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder

            # Get word at position
            lines = file_content.splitlines()
            if line < 1 or line > len(lines):
                return {"locations": []}

            target_line = lines[line - 1]
            if col < 1 or col > len(target_line):
                return {"locations": []}

            # Extract word at position
            start = col - 1
            end = col - 1
            while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == '_'):
                start -= 1
            while end < len(target_line) and (target_line[end].isalnum() or target_line[end] == '_'):
                end += 1

            if start == end:
                return {"locations": []}

            word = target_line[start:end]

            # Find all occurrences
            locations = []
            for i, ln in enumerate(lines, 1):
                c = 0
                while True:
                    pos = ln.find(word, c)
                    if pos == -1:
                        break
                    before_ok = pos == 0 or not (ln[pos - 1].isalnum() or ln[pos - 1] == '_')
                    after_pos = pos + len(word)
                    after_ok = after_pos >= len(ln) or not (ln[after_pos].isalnum() or ln[after_pos] == '_')
                    if before_ok and after_ok:
                        locations.append({
                            "line": i,
                            "col": pos + 1,
                            "end_line": i,
                            "end_col": after_pos + 1,
                        })
                    c = after_pos

            return {"locations": locations}

        @self.server.tool()
        async def yuho_symbols(file_content: str) -> Dict[str, Any]:
            """
            Get all symbols in the document.

            Args:
                file_content: The Yuho source code

            Returns:
                {symbols: list of {name, kind, line, col}}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder

            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {"symbols": [], "error": result.errors[0].message}

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)

                symbols = []

                # Structs
                for struct in ast.type_defs:
                    loc = struct.source_location
                    symbols.append({
                        "name": struct.name,
                        "kind": "struct",
                        "line": loc.line if loc else 0,
                        "col": loc.col if loc else 0,
                    })

                # Functions
                for func in ast.function_defs:
                    loc = func.source_location
                    symbols.append({
                        "name": func.name,
                        "kind": "function",
                        "line": loc.line if loc else 0,
                        "col": loc.col if loc else 0,
                    })

                # Statutes
                for statute in ast.statutes:
                    loc = statute.source_location
                    title = statute.title.value if statute.title else ""
                    symbols.append({
                        "name": f"S{statute.section_number}: {title}",
                        "kind": "statute",
                        "line": loc.line if loc else 0,
                        "col": loc.col if loc else 0,
                    })

                return {"symbols": symbols}
            except Exception as e:
                return {"symbols": [], "error": str(e)}

        @self.server.tool()
        async def yuho_diagnostics(file_content: str) -> Dict[str, Any]:
            """
            Get diagnostics (errors, warnings) for the document.

            Args:
                file_content: The Yuho source code

            Returns:
                {diagnostics: list of {message, severity, line, col}}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder

            diagnostics = []
            parser = Parser()
            result = parser.parse(file_content)

            # Parse errors
            for err in result.errors:
                diagnostics.append({
                    "message": err.message,
                    "severity": "error",
                    "line": err.location.line,
                    "col": err.location.col,
                })

            # Try AST build for more diagnostics
            if result.is_valid:
                try:
                    builder = ASTBuilder(file_content)
                    ast = builder.build(result.root_node)

                    # TODO: Run semantic analysis for more diagnostics
                except Exception as e:
                    diagnostics.append({
                        "message": str(e),
                        "severity": "error",
                        "line": 1,
                        "col": 1,
                    })

            return {"diagnostics": diagnostics}

        @self.server.tool()
        async def yuho_validate_contribution(file_content: str, tests: List[str] = None) -> Dict[str, Any]:
            """
            Validate a statute file for contribution to the library.

            Args:
                file_content: The Yuho source code
                tests: Optional list of test file contents

            Returns:
                {valid: bool, results: list}
            """
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder

            tests = tests or []
            results = []

            # Check parsing
            parser = Parser()
            result = parser.parse(file_content)

            if result.errors:
                return {
                    "valid": False,
                    "results": [{
                        "check": "parse",
                        "passed": False,
                        "message": result.errors[0].message,
                    }],
                }

            results.append({"check": "parse", "passed": True, "message": "Parses successfully"})

            # Check AST build
            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)
                results.append({"check": "ast", "passed": True, "message": "AST builds successfully"})
            except Exception as e:
                return {
                    "valid": False,
                    "results": results + [{
                        "check": "ast",
                        "passed": False,
                        "message": str(e),
                    }],
                }

            # Check has statutes
            if not ast.statutes:
                results.append({
                    "check": "statute",
                    "passed": False,
                    "message": "No statutes defined",
                })
            else:
                results.append({
                    "check": "statute",
                    "passed": True,
                    "message": f"Contains {len(ast.statutes)} statute(s)",
                })

            # Check tests exist
            if not tests:
                results.append({
                    "check": "tests",
                    "passed": False,
                    "message": "No test files provided",
                })
            else:
                results.append({
                    "check": "tests",
                    "passed": True,
                    "message": f"{len(tests)} test file(s) provided",
                })

            valid = all(r["passed"] for r in results)
            return {"valid": valid, "results": results}

        @self.server.tool()
        async def yuho_library_search(query: str) -> Dict[str, Any]:
            """
            Search statute library by section number, title, or jurisdiction.

            Args:
                query: Search query string

            Returns:
                {statutes: list of {section, title, jurisdiction, path}}
            """
            # TODO: Implement proper library search using library index
            library_path = Path(__file__).parent.parent.parent.parent / "library"
            results = []

            query_lower = query.lower()

            if library_path.exists():
                for yh_file in library_path.glob("**/*.yh"):
                    try:
                        content = yh_file.read_text()
                        # Simple search in content
                        if query_lower in content.lower():
                            results.append({
                                "section": yh_file.stem,
                                "title": yh_file.stem,  # Simplified
                                "jurisdiction": "unknown",
                                "path": str(yh_file),
                            })
                    except Exception:
                        continue

            return {"statutes": results[:20]}  # Limit results

        @self.server.tool()
        async def yuho_library_get(section: str) -> Dict[str, Any]:
            """
            Get a statute from the library by section number.

            Args:
                section: Section number (e.g., "299")

            Returns:
                {statute: {section, title, content}} or {error: str}
            """
            library_path = Path(__file__).parent.parent.parent.parent / "library"

            if library_path.exists():
                # Search for matching section
                for yh_file in library_path.glob("**/*.yh"):
                    if section in yh_file.stem:
                        try:
                            content = yh_file.read_text()
                            return {
                                "statute": {
                                    "section": section,
                                    "title": yh_file.stem,
                                    "content": content,
                                }
                            }
                        except Exception as e:
                            return {"error": str(e)}

            return {"error": f"Section {section} not found in library"}

        @self.server.tool()
        async def yuho_statute_to_yuho(natural_text: str) -> Dict[str, Any]:
            """
            Convert natural language statute text to Yuho code using LLM.

            Args:
                natural_text: Natural language description of a statute

            Returns:
                {yuho_code: str} or {error: str}
            """
            try:
                from yuho.llm import get_provider

                provider = get_provider()

                prompt = f"""Convert the following legal statute text into Yuho DSL code.

Statute text:
{natural_text}

Please generate valid Yuho code with:
- Proper statute declaration with section number
- Elements (actus_reus, mens_rea, circumstance)
- Penalty section if applicable
- Definitions if needed

Yuho code:"""

                response = await provider.generate_async(prompt)
                return {"yuho_code": response}
            except ImportError:
                return {"error": "LLM provider not configured"}
            except Exception as e:
                return {"error": str(e)}

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
            library_path = Path(__file__).parent.parent.parent.parent / "library"
            if library_path.exists():
                for yh_file in library_path.glob("**/*.yh"):
                    if section in yh_file.stem:
                        try:
                            return yh_file.read_text()
                        except Exception:
                            pass
            return f"// Statute {section} not found in library"

        @self.server.resource("yuho://docs/{topic}")
        async def get_docs(topic: str) -> str:
            """Return reference documentation for a topic."""
            docs = {
                "overview": """
# Yuho Language Overview

Yuho is a domain-specific language for encoding legal statutes in a machine-readable format.

## Key Features
- Structured statute representation
- Elements: actus_reus, mens_rea, circumstance
- Penalty specifications
- Pattern matching
- Type system

## File Extension
.yh files
""",
                "syntax": """
# Yuho Syntax Reference

## Statute Declaration
```
statute "Section.Number" {
    title: "Statute Title"
    
    elements {
        actus_reus element_name: condition_expr
        mens_rea intent_name: intent_type
        circumstance circ_name: circ_expr
    }
    
    penalty {
        imprisonment { max: 10 years }
        fine { max: $10000 SGD }
    }
}
```

## Struct Definition
```
struct PersonInfo {
    name: string
    age: int
}
```

## Function Definition
```
fn is_adult(age: int) -> bool {
    return age >= 18
}
```
""",
                "types": """
# Yuho Type System

## Primitive Types
- int: Integer numbers
- float: Floating point
- bool: TRUE or FALSE
- string: Text strings

## Legal Domain Types
- money: Currency amounts ($100.00 SGD)
- percent: Percentages (50%)
- date: ISO dates (2024-01-15)
- duration: Time periods (3 years)

## Composite Types
- struct: Named record types
- optional: Type? for nullable
- array: [Type] for lists
""",
                "elements": """
# Statute Elements

## actus_reus (Guilty Act)
The physical or conduct element of an offense.
```
actus_reus caused_death: victim.died && defendant.action.caused(victim.death)
```

## mens_rea (Guilty Mind)
The mental element - intent or knowledge required.
```
mens_rea intent_to_kill: intent.purpose || intent.knowledge
```

## circumstance
Additional circumstances that must exist.
```
circumstance victim_human: victim.is_human
```
""",
                "penalty": """
# Penalty Specification

## Imprisonment
```
imprisonment {
    min: 2 years
    max: 20 years
}
```

## Fine
```
fine {
    max: $500000 SGD
}
```

## Supplementary
Additional penalties like caning, disqualification, etc.
```
supplementary {
    caning: true
    disqualification: "driving"
}
```
""",
            }
            return docs.get(topic.lower(), f"# Topic '{topic}' not found\n\nAvailable topics: {', '.join(docs.keys())}")

    def _register_prompts(self):
        """Register MCP prompts."""

        @self.server.prompt("explain_statute")
        async def explain_statute_prompt(file_content: str) -> str:
            """Prompt for explaining a statute in plain English."""
            return f"""You are a legal expert explaining a statute encoded in Yuho.

Analyze the following Yuho code and explain:
1. What offense it defines
2. What elements must be proven
3. What penalties apply

Yuho code:
```yuho
{file_content}
```

Provide a clear, structured explanation suitable for legal professionals."""

        @self.server.prompt("convert_to_yuho")
        async def convert_to_yuho_prompt(natural_text: str) -> str:
            """Prompt for converting natural language statute to Yuho."""
            return f"""You are an expert in legal DSLs, specifically Yuho.

Convert the following legal statute text into valid Yuho code.

Statute text:
{natural_text}

Requirements:
1. Use proper statute declaration syntax
2. Identify and encode all elements (actus_reus, mens_rea, circumstance)
3. Include penalty section if mentioned
4. Add definitions section for legal terms
5. Use appropriate types (money, duration, percent)

Output only valid Yuho code with comments explaining design decisions."""

        @self.server.prompt("analyze_coverage")
        async def analyze_coverage_prompt(file_content: str) -> str:
            """Prompt for analyzing test coverage of a statute."""
            return f"""You are a legal testing expert.

Analyze the following Yuho statute and identify:
1. All condition branches that need testing
2. Edge cases for each element
3. Suggested test scenarios

Yuho code:
```yuho
{file_content}
```

Provide a comprehensive test plan with specific values for each test case."""

    def health_check(self) -> Dict[str, Any]:
        """Return server health status."""
        return {
            "status": "healthy",
            "name": "yuho-mcp",
            "version": "5.0.0",
            "tools_registered": True,
            "resources_registered": True,
        }

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

        async def handle_health(request):
            """Health check endpoint."""
            return web.json_response(self.health_check())

        app = web.Application()
        app.router.add_post("/mcp", handle_mcp)
        app.router.add_get("/health", handle_health)

        web.run_app(app, host=host, port=port)


def create_server() -> YuhoMCPServer:
    """Create and return a YuhoMCPServer instance."""
    return YuhoMCPServer()
