"""
Yuho MCP Server implementation.

Provides MCP tools for parsing, transpiling, and analyzing Yuho code.
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass, field
import json
import logging
import time
import threading

# Configure MCP logger
logger = logging.getLogger("yuho.mcp")


class LogVerbosity(IntEnum):
    """Verbosity levels for MCP request logging."""
    QUIET = 0      # No logging
    MINIMAL = 1    # Log tool name only
    STANDARD = 2   # Log tool name and execution time
    VERBOSE = 3    # Log tool name, args summary, and execution time
    DEBUG = 4      # Log everything including full args and responses


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.1f}s")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    
    # Requests per second (token refill rate)
    requests_per_second: float = 10.0
    
    # Maximum burst size (bucket capacity)
    burst_size: int = 20
    
    # Per-client limits (by IP or client ID)
    per_client_rps: float = 5.0
    per_client_burst: int = 10
    
    # Enable/disable rate limiting
    enabled: bool = True
    
    # Exempt tool names (no rate limiting)
    exempt_tools: List[str] = field(default_factory=lambda: ["yuho_grammar", "yuho_types"])


class TokenBucket:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, rate: float, capacity: int):
        """
        Initialize token bucket.
        
        Args:
            rate: Token refill rate (tokens per second)
            capacity: Maximum bucket capacity
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()
    
    def _refill(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now
    
    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            
        Returns:
            True if tokens acquired, False if rate limited
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def time_until_available(self, tokens: int = 1) -> float:
        """
        Calculate time until tokens will be available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            Seconds until tokens available (0 if available now)
        """
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            deficit = tokens - self.tokens
            return deficit / self.rate


class RateLimiter:
    """Rate limiter for MCP server with per-client tracking."""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self._global_bucket = TokenBucket(config.requests_per_second, config.burst_size)
        self._client_buckets: Dict[str, TokenBucket] = {}
        self._client_buckets_lock = threading.Lock()
        self._stats = {
            "total_requests": 0,
            "rate_limited": 0,
            "by_tool": {},
        }
    
    def _get_client_bucket(self, client_id: str) -> TokenBucket:
        """Get or create a token bucket for a client."""
        with self._client_buckets_lock:
            if client_id not in self._client_buckets:
                self._client_buckets[client_id] = TokenBucket(
                    self.config.per_client_rps,
                    self.config.per_client_burst
                )
            return self._client_buckets[client_id]
    
    def check_rate_limit(
        self,
        tool_name: str,
        client_id: Optional[str] = None,
    ) -> None:
        """
        Check if request is rate limited.
        
        Args:
            tool_name: Name of the tool being called
            client_id: Optional client identifier
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        if not self.config.enabled:
            return
        
        # Track stats
        self._stats["total_requests"] += 1
        self._stats["by_tool"][tool_name] = self._stats["by_tool"].get(tool_name, 0) + 1
        
        # Check exempt tools
        if tool_name in self.config.exempt_tools:
            return
        
        # Check global rate limit
        if not self._global_bucket.acquire():
            self._stats["rate_limited"] += 1
            retry_after = self._global_bucket.time_until_available()
            logger.warning(f"Global rate limit exceeded for {tool_name}")
            raise RateLimitExceeded(retry_after)
        
        # Check per-client rate limit if client_id provided
        if client_id:
            client_bucket = self._get_client_bucket(client_id)
            if not client_bucket.acquire():
                self._stats["rate_limited"] += 1
                retry_after = client_bucket.time_until_available()
                logger.warning(f"Client rate limit exceeded for {client_id} on {tool_name}")
                raise RateLimitExceeded(retry_after)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return {
            **self._stats,
            "global_tokens": self._global_bucket.tokens,
            "active_clients": len(self._client_buckets),
        }
    
    def reset_stats(self) -> None:
        """Reset rate limiting statistics."""
        self._stats = {
            "total_requests": 0,
            "rate_limited": 0,
            "by_tool": {},
        }


class LogVerbosity(IntEnum):
    """Verbosity levels for MCP request logging."""
    QUIET = 0      # No logging
    MINIMAL = 1    # Log tool name only
    STANDARD = 2   # Log tool name and execution time
    VERBOSE = 3    # Log tool name, args summary, and execution time
    DEBUG = 4      # Log everything including full args and responses


class MCPRequestLogger:
    """Logger for MCP requests with configurable verbosity."""
    
    def __init__(self, verbosity: LogVerbosity = LogVerbosity.STANDARD):
        self.verbosity = verbosity
        
    def log_request(self, tool_name: str, args: Dict[str, Any]) -> float:
        """Log incoming request, return start time."""
        start = time.time()
        
        if self.verbosity >= LogVerbosity.MINIMAL:
            logger.info(f"MCP request: {tool_name}")
            
        if self.verbosity >= LogVerbosity.VERBOSE:
            args_summary = {k: f"{len(str(v))} chars" if len(str(v)) > 100 else v 
                          for k, v in args.items()}
            logger.info(f"  Args: {args_summary}")
            
        if self.verbosity >= LogVerbosity.DEBUG:
            logger.debug(f"  Full args: {args}")
            
        return start
    
    def log_response(self, tool_name: str, result: Any, start_time: float, error: Optional[Exception] = None) -> None:
        """Log response after tool execution."""
        elapsed = time.time() - start_time
        
        if error:
            logger.error(f"MCP error: {tool_name} failed after {elapsed:.3f}s - {error}")
            return
            
        if self.verbosity >= LogVerbosity.STANDARD:
            logger.info(f"MCP response: {tool_name} completed in {elapsed:.3f}s")
            
        if self.verbosity >= LogVerbosity.DEBUG:
            result_str = str(result)
            if len(result_str) > 500:
                result_str = result_str[:500] + "..."
            logger.debug(f"  Result: {result_str}")


try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Provide mock class for when mcp is not installed
    class FastMCP:
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

        def prompt(self, name: str = None):
            def decorator(func):
                return func
            return decorator
        
        def run(self, transport: str = "stdio"):
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

    def __init__(
        self,
        verbosity: LogVerbosity = LogVerbosity.STANDARD,
        rate_limit_config: Optional[RateLimitConfig] = None,
    ):
        self.server = FastMCP("yuho-mcp")
        self.request_logger = MCPRequestLogger(verbosity)
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def set_verbosity(self, verbosity: LogVerbosity) -> None:
        """Set the logging verbosity level."""
        self.request_logger.verbosity = verbosity
        logger.info(f"MCP logging verbosity set to: {verbosity.name}")

    def set_rate_limit_config(self, config: RateLimitConfig) -> None:
        """Update rate limiting configuration."""
        self.rate_limiter = RateLimiter(config)
        logger.info(f"MCP rate limiting updated: {config.requests_per_second} req/s, burst={config.burst_size}")

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return self.rate_limiter.get_stats()

    def _check_rate_limit(self, tool_name: str, client_id: Optional[str] = None) -> None:
        """Check rate limit and raise exception if exceeded."""
        self.rate_limiter.check_rate_limit(tool_name, client_id)

    def _register_tools(self):
        """Register MCP tools."""

        @self.server.tool()
        async def yuho_check(file_content: str, client_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Validate Yuho source code.

            Args:
                file_content: The Yuho source code to validate
                client_id: Optional client identifier for rate limiting

            Returns:
                {valid: bool, errors: list of error dicts}
            """
            try:
                self._check_rate_limit("yuho_check", client_id)
            except RateLimitExceeded as e:
                return {"error": str(e), "retry_after": e.retry_after}
            
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
        async def yuho_transpile(file_content: str, target: str, client_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Transpile Yuho source to another format.

            Args:
                file_content: The Yuho source code
                target: Target format (json, jsonld, english, mermaid, alloy)
                client_id: Optional client identifier for rate limiting

            Returns:
                {output: str} or {error: str}
            """
            try:
                self._check_rate_limit("yuho_transpile", client_id)
            except RateLimitExceeded as e:
                return {"error": str(e), "retry_after": e.retry_after}
            
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
        async def yuho_explain(file_content: str, section: Optional[str] = None, client_id: Optional[str] = None) -> Dict[str, Any]:
            """
            Generate natural language explanation.

            Args:
                file_content: The Yuho source code
                section: Optional section number to explain
                client_id: Optional client identifier for rate limiting

            Returns:
                {explanation: str} or {error: str}
            """
            try:
                self._check_rate_limit("yuho_explain", client_id)
            except RateLimitExceeded as e:
                return {"error": str(e), "retry_after": e.retry_after}
            
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
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder
            
            # Keywords and their docs
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
            
            # Get word at position
            lines = file_content.splitlines()
            if line < 1 or line > len(lines):
                return {"info": None}
            
            target_line = lines[line - 1]
            if col < 1 or col > len(target_line):
                return {"info": None}
            
            # Extract word at position
            start = col - 1
            end = col - 1
            while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == '_'):
                start -= 1
            while end < len(target_line) and (target_line[end].isalnum() or target_line[end] == '_'):
                end += 1
            
            if start == end:
                return {"info": None}
            
            word = target_line[start:end]
            
            # Check keywords
            if word in KEYWORD_DOCS:
                return {"info": f"**keyword** `{word}`\n\n{KEYWORD_DOCS[word]}"}
            
            # Check types
            if word in TYPE_DOCS:
                return {"info": f"**type** `{word}`\n\n{TYPE_DOCS[word]}"}
            
            # Parse for symbol info
            parser = Parser()
            result = parser.parse(file_content)
            
            if result.is_valid:
                try:
                    builder = ASTBuilder(file_content)
                    ast = builder.build(result.root_node)
                    
                    # Check structs
                    for struct in ast.type_defs:
                        if struct.name == word:
                            fields = ", ".join(f"{f.name}: {f.type_annotation}" for f in struct.fields)
                            return {"info": f"**struct** `{struct.name}`\n\n```yuho\nstruct {struct.name} {{ {fields} }}\n```"}
                    
                    # Check functions
                    for func in ast.function_defs:
                        if func.name == word:
                            params = ", ".join(f"{p.name}: {p.type_annotation}" for p in func.params)
                            ret = f" -> {func.return_type}" if func.return_type else ""
                            return {"info": f"**function** `{func.name}`\n\n```yuho\nfn {func.name}({params}){ret}\n```"}
                    
                    # Check statutes
                    for statute in ast.statutes:
                        if statute.section_number == word or f"S{statute.section_number}" == word:
                            title = statute.title.value if statute.title else "Untitled"
                            info = f"**Statute Section {statute.section_number}**: {title}"
                            if statute.elements:
                                info += "\n\n**Elements:**\n"
                                for elem in statute.elements:
                                    info += f"- {elem.element_type}: {elem.name}\n"
                            return {"info": info}
                            
                except Exception:
                    pass
            
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
            from yuho.parser import Parser
            from yuho.ast import ASTBuilder
            
            # Get word at position
            lines = file_content.splitlines()
            if line < 1 or line > len(lines):
                return {"location": None}
            
            target_line = lines[line - 1]
            if col < 1 or col > len(target_line):
                return {"location": None}
            
            # Extract word at position
            start = col - 1
            end = col - 1
            while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == '_'):
                start -= 1
            while end < len(target_line) and (target_line[end].isalnum() or target_line[end] == '_'):
                end += 1
            
            if start == end:
                return {"location": None}
            
            word = target_line[start:end]
            
            # Parse for symbol definitions
            parser = Parser()
            result = parser.parse(file_content)
            
            if result.is_valid:
                try:
                    builder = ASTBuilder(file_content)
                    ast = builder.build(result.root_node)
                    
                    # Check struct definitions
                    for struct in ast.type_defs:
                        if struct.name == word and struct.source_location:
                            return {
                                "location": {
                                    "line": struct.source_location.line,
                                    "col": struct.source_location.col,
                                }
                            }
                    
                    # Check function definitions
                    for func in ast.function_defs:
                        if func.name == word and func.source_location:
                            return {
                                "location": {
                                    "line": func.source_location.line,
                                    "col": func.source_location.col,
                                }
                            }
                    
                    # Check statute definitions (by section number)
                    for statute in ast.statutes:
                        if (statute.section_number == word or 
                            f"S{statute.section_number}" == word) and statute.source_location:
                            return {
                                "location": {
                                    "line": statute.source_location.line,
                                    "col": statute.source_location.col,
                                }
                            }
                            
                except Exception:
                    pass
            
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

            Uses a structured prompt to convert legal statute descriptions
            into valid Yuho DSL code with proper elements, penalties, and definitions.

            Args:
                natural_text: Natural language description of a statute

            Returns:
                {yuho_code: str, valid: bool, errors: list} or {error: str}
            """
            import asyncio

            try:
                from yuho.llm import get_provider, STATUTE_TO_YUHO_PROMPT
                from yuho.parser import Parser

                # Get LLM provider
                provider = get_provider()
                if not provider.is_available():
                    return {"error": "No LLM provider available. Configure Ollama or an API key."}

                # Build prompt using the specialized template
                prompt = STATUTE_TO_YUHO_PROMPT.format(statute_text=natural_text)

                # Run synchronous LLM call in executor to not block
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: provider.generate(prompt, max_tokens=2000)
                )

                # Extract code block if present
                yuho_code = response.strip()
                if "```" in yuho_code:
                    # Extract code from markdown code block
                    import re
                    code_match = re.search(r"```(?:yuho)?\s*\n(.*?)```", yuho_code, re.DOTALL)
                    if code_match:
                        yuho_code = code_match.group(1).strip()

                # Validate the generated code
                parser = Parser()
                result = parser.parse(yuho_code)

                if result.errors:
                    return {
                        "yuho_code": yuho_code,
                        "valid": False,
                        "errors": [
                            {
                                "message": err.message,
                                "line": err.location.line,
                                "col": err.location.col,
                            }
                            for err in result.errors
                        ],
                        "note": "LLM generated code with syntax errors. Manual correction may be needed.",
                    }

                return {
                    "yuho_code": yuho_code,
                    "valid": True,
                    "errors": [],
                }

            except ImportError as e:
                missing = str(e).split("'")[-2] if "'" in str(e) else "llm dependencies"
                return {"error": f"LLM provider not configured. Missing: {missing}. Install with: pip install yuho[llm]"}
            except Exception as e:
                return {"error": f"LLM generation failed: {str(e)}"}

        @self.server.tool()
        async def yuho_rate_limit_stats() -> Dict[str, Any]:
            """
            Get rate limiting statistics.

            Returns:
                Statistics about rate limiting including total requests,
                rate-limited requests, per-tool breakdown, and current token counts.
            """
            return self.rate_limiter.get_stats()

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
        if not MCP_AVAILABLE:
            raise ImportError("MCP dependencies not installed. Install with: pip install yuho[mcp]")
        self.server.run(transport="stdio")

    def run_http(self, host: str = "127.0.0.1", port: int = 8080):
        """Run the server using HTTP transport."""
        if not MCP_AVAILABLE:
            raise ImportError("MCP dependencies not installed. Install with: pip install yuho[mcp]")
        # FastMCP uses SSE transport for HTTP
        import os
        os.environ["MCP_HOST"] = host
        os.environ["MCP_PORT"] = str(port)
        self.server.run(transport="sse")
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
