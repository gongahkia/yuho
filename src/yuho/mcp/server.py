"""
Yuho MCP Server implementation.

Provides MCP tools for parsing, transpiling, and analyzing Yuho code.
"""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, TypedDict
from pathlib import Path
from enum import IntEnum
from dataclasses import dataclass, field
from functools import wraps
import json
import logging
import time
import threading

from yuho import __version__
from yuho.cli.commands.check import get_error_explanation
from yuho.config.loader import get_config
from yuho.config.mask import mask_error
from yuho.services.analysis import analyze_source
from yuho.services.errors import (
    ASTBoundaryError,
    ParserBoundaryError,
    TranspileBoundaryError,
    run_ast_boundary,
    run_parser_boundary,
    run_transpile_boundary,
)

# Configure MCP logger
logger = logging.getLogger("yuho.mcp")

if TYPE_CHECKING:
    from yuho.ast import nodes


class RateLimitStats(TypedDict):
    total_requests: int
    rate_limited: int
    by_tool: Dict[str, int]
    error_counts: Dict[str, int]
    latency_histograms_ms: Dict[str, Dict[str, int]]


def _iter_leaf_elements(
    elements: (
        tuple["nodes.ElementNode | nodes.ElementGroupNode", ...]
        | list["nodes.ElementNode | nodes.ElementGroupNode"]
    ),
) -> Iterator["nodes.ElementNode"]:
    from yuho.ast import nodes

    for elem in elements:
        if isinstance(elem, nodes.ElementNode):
            yield elem
            continue
        yield from _iter_leaf_elements(list(elem.members))


class LogVerbosity(IntEnum):
    """Verbosity levels for MCP request logging."""

    QUIET = 0  # No logging
    MINIMAL = 1  # Log tool name only
    STANDARD = 2  # Log tool name and execution time
    VERBOSE = 3  # Log tool name, args summary, and execution time
    DEBUG = 4  # Log everything including full args and responses


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

    # Per-tool rate-limit overrides. Tools not in this map fall back to the
    # global limit. Long-running tools (subprocess dispatchers, full-corpus
    # walks) get a much lower rate so they can't accidentally swamp the
    # process. Fast tools (parse, format, hover) get a higher rate so an
    # IDE / AI client polling them doesn't get throttled.
    #
    # Each value is a (rps, burst) tuple.
    per_tool_overrides: Dict[str, tuple] = field(default_factory=lambda: {
        # Long-running: subprocess dispatchers / full-library scans.
        "yuho_run_l3_review":         (0.1,  2),   # ~6 calls per minute
        "yuho_apply_flag_fix":        (0.1,  2),
        "yuho_propose_encoding_skeleton": (0.5, 3),
        "yuho_simulate_fact_pattern": (1.0,  4),
        "yuho_verify_grounded":       (1.0,  4),
        "yuho_section_references":    (2.0,  5),   # corpus walk + graph build
        "yuho_validate_contribution": (1.0,  3),
        # Mid-cost.
        "yuho_section_pair":          (5.0, 10),
        "yuho_library_list":          (5.0, 10),
        "yuho_library_search":        (5.0, 10),
        "yuho_transpile":             (5.0, 10),
        # Cheap, latency-sensitive: bumped above the global default.
        "yuho_check":                 (30.0, 60),
        "yuho_parse":                 (30.0, 60),
        "yuho_hover":                 (30.0, 60),
        "yuho_complete":              (30.0, 60),
        "yuho_diagnostics":           (30.0, 60),
        "yuho_format":                (30.0, 60),
        "yuho_definition":            (30.0, 60),
        "yuho_references":            (30.0, 60),
        "yuho_symbols":               (30.0, 60),
    })


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
        # Per-tool buckets: built lazily on first call.
        self._tool_buckets: Dict[str, TokenBucket] = {}
        self._tool_buckets_lock = threading.Lock()
        self._stats_lock = threading.Lock()
        self._stats: RateLimitStats = {
            "total_requests": 0,
            "rate_limited": 0,
            "by_tool": {},
            "error_counts": {},
            "latency_histograms_ms": {},
        }

    def _get_client_bucket(self, client_id: str) -> TokenBucket:
        """Get or create a token bucket for a client."""
        with self._client_buckets_lock:
            if client_id not in self._client_buckets:
                self._client_buckets[client_id] = TokenBucket(
                    self.config.per_client_rps, self.config.per_client_burst
                )
            return self._client_buckets[client_id]

    def _get_tool_bucket(self, tool_name: str) -> Optional[TokenBucket]:
        """Get or create a per-tool token bucket if the tool has an override.

        Returns None if no override applies (fall back to the global bucket).
        """
        override = self.config.per_tool_overrides.get(tool_name)
        if override is None:
            return None
        rps, burst = override
        with self._tool_buckets_lock:
            if tool_name not in self._tool_buckets:
                self._tool_buckets[tool_name] = TokenBucket(rps, burst)
            return self._tool_buckets[tool_name]

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
        with self._stats_lock:
            self._stats["total_requests"] += 1
            self._stats["by_tool"][tool_name] = self._stats["by_tool"].get(tool_name, 0) + 1

        # Check exempt tools
        if tool_name in self.config.exempt_tools:
            return

        # Per-tool override: if this tool has a custom rate, the per-tool
        # bucket is the binding constraint, not the global bucket. Falling
        # back to the global bucket only when no override is set keeps
        # high-frequency tools (yuho_check) from being throttled by the
        # default global rate.
        tool_bucket = self._get_tool_bucket(tool_name)
        if tool_bucket is not None:
            if not tool_bucket.acquire():
                with self._stats_lock:
                    self._stats["rate_limited"] += 1
                retry_after = tool_bucket.time_until_available()
                logger.warning(f"Per-tool rate limit exceeded for {tool_name}")
                raise RateLimitExceeded(retry_after)
        else:
            # Check global rate limit
            if not self._global_bucket.acquire():
                with self._stats_lock:
                    self._stats["rate_limited"] += 1
                retry_after = self._global_bucket.time_until_available()
                logger.warning(f"Global rate limit exceeded for {tool_name}")
                raise RateLimitExceeded(retry_after)

        # Check per-client rate limit if client_id provided
        if client_id:
            client_bucket = self._get_client_bucket(client_id)
            if not client_bucket.acquire():
                with self._stats_lock:
                    self._stats["rate_limited"] += 1
                retry_after = client_bucket.time_until_available()
                logger.warning(f"Client rate limit exceeded for {client_id} on {tool_name}")
                raise RateLimitExceeded(retry_after)

    def record_tool_result(self, tool_name: str, elapsed_seconds: float, had_error: bool) -> None:
        """Record per-tool latency and error statistics."""
        elapsed_ms = max(0.0, elapsed_seconds * 1000.0)
        bucket = self._latency_bucket_label(elapsed_ms)

        with self._stats_lock:
            histograms = self._stats["latency_histograms_ms"]
            tool_histogram = histograms.setdefault(tool_name, {})
            tool_histogram[bucket] = tool_histogram.get(bucket, 0) + 1

            if had_error:
                error_counts = self._stats["error_counts"]
                error_counts[tool_name] = error_counts.get(tool_name, 0) + 1

    def _latency_bucket_label(self, elapsed_ms: float) -> str:
        """Return histogram bucket label for elapsed milliseconds."""
        if elapsed_ms <= 10:
            return "le_10ms"
        if elapsed_ms <= 25:
            return "le_25ms"
        if elapsed_ms <= 50:
            return "le_50ms"
        if elapsed_ms <= 100:
            return "le_100ms"
        if elapsed_ms <= 250:
            return "le_250ms"
        if elapsed_ms <= 500:
            return "le_500ms"
        if elapsed_ms <= 1000:
            return "le_1000ms"
        return "gt_1000ms"

    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        with self._stats_lock:
            stats_snapshot = {
                "total_requests": self._stats["total_requests"],
                "rate_limited": self._stats["rate_limited"],
                "by_tool": dict(self._stats["by_tool"]),
                "error_counts": dict(self._stats["error_counts"]),
                "latency_histograms_ms": {
                    tool: dict(hist) for tool, hist in self._stats["latency_histograms_ms"].items()
                },
            }

        return {
            **stats_snapshot,
            "global_tokens": self._global_bucket.tokens,
            "active_clients": len(self._client_buckets),
        }

    def reset_stats(self) -> None:
        """Reset rate limiting statistics."""
        with self._stats_lock:
            self._stats = {
                "total_requests": 0,
                "rate_limited": 0,
                "by_tool": {},
                "error_counts": {},
                "latency_histograms_ms": {},
            }


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
            args_summary = {
                k: f"{len(str(v))} chars" if len(str(v)) > 100 else v for k, v in args.items()
            }
            logger.info(f"  Args: {args_summary}")

        if self.verbosity >= LogVerbosity.DEBUG:
            logger.debug(f"  Full args: {args}")

        return start

    def log_response(
        self, tool_name: str, result: Any, start_time: float, error: Optional[Exception] = None
    ) -> None:
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
    from mcp.server.fastmcp import FastMCP as _FastMCPImpl

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

    # Provide mock class for when mcp is not installed
    class _FallbackFastMCP:
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

        def prompt(self, name: Optional[str] = None):
            def decorator(func):
                return func

            return decorator

        def run(self, transport: str = "stdio"):
            raise ImportError("MCP dependencies not installed. Install with: pip install yuho[mcp]")

    _FastMCPImpl = _FallbackFastMCP


def mcp_error(
    code: str,
    message: str,
    *,
    retry: bool = False,
    retry_after_seconds: Optional[float] = None,
    **extra: Any,
) -> Dict[str, Any]:
    """Construct the canonical error envelope for MCP tool returns.

    Standard shape:

        {
          "ok": false,
          "error_code": "<machine-readable identifier>",
          "message": "<human-readable explanation>",
          "retry": true | false,
          "retry_after_seconds": <number or null>,
          ...extra fields a specific tool wants to surface...
        }

    Use error_code values that map onto a small fixed vocabulary:
    'parse_error', 'not_found', 'invalid_argument', 'rate_limited',
    'timeout', 'subprocess_failed', 'unavailable', 'internal_error'.
    Tools may extend the vocabulary but should keep codes stable across
    versions for client error-handling.
    """
    payload: Dict[str, Any] = {
        "ok": False,
        "error_code": code,
        "message": message,
        "retry": retry,
        "retry_after_seconds": retry_after_seconds,
    }
    payload.update(extra)
    return payload


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
        self.server = _FastMCPImpl("yuho-mcp")
        self.request_logger = MCPRequestLogger(verbosity)
        self.rate_limiter = RateLimiter(rate_limit_config or RateLimitConfig())

        # ----------------------------------------------------------------
        # In-process caches.
        # ----------------------------------------------------------------
        # 1. Reference graph (G10): expensive to build (~150ms for the
        #    SG Penal Code), invariant across many tool calls. Cache the
        #    built graph once per process lifetime.
        self._reference_graph_cache = None
        self._reference_graph_lock = threading.Lock()

        # 2. Per-section corpus records: read once, hand out the same
        #    dict to every consumer. Keyed by section number.
        self._corpus_section_cache: Dict[str, Any] = {}
        self._corpus_section_cache_lock = threading.Lock()

        # 3. Generic TTL cache for tool results. Keyed by
        #    (tool_name, frozen_args). Bounded by entry count.
        self._tool_result_cache: Dict[tuple, tuple] = {}  # value: (expires_at, result)
        self._tool_result_cache_lock = threading.Lock()
        self._tool_result_cache_max = 256
        self._tool_result_cache_ttl = 30.0  # seconds

        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def get_reference_graph(self):
        """Return the cached G10 reference graph, building it on first call."""
        from yuho.library.reference_graph import build_reference_graph
        from pathlib import Path
        with self._reference_graph_lock:
            if self._reference_graph_cache is None:
                penal = Path("library/penal_code")
                if not penal.exists():
                    return None
                try:
                    self._reference_graph_cache = build_reference_graph(penal)
                except Exception:
                    self._reference_graph_cache = None
            return self._reference_graph_cache

    def invalidate_reference_graph(self) -> None:
        """Drop the cached reference graph (call after edits to library/)."""
        with self._reference_graph_lock:
            self._reference_graph_cache = None

    def get_corpus_section(self, section: str) -> Optional[dict]:
        """Return the cached `_corpus/sections/s{N}.json` record for a section."""
        from pathlib import Path
        with self._corpus_section_cache_lock:
            if section in self._corpus_section_cache:
                return self._corpus_section_cache[section]
            path = Path("library/penal_code/_corpus/sections") / f"s{section}.json"
            if not path.exists():
                self._corpus_section_cache[section] = None
                return None
            try:
                with path.open("r", encoding="utf-8") as f:
                    record = json.load(f)
                self._corpus_section_cache[section] = record
                return record
            except Exception:
                self._corpus_section_cache[section] = None
                return None

    def cache_get(self, key: tuple) -> Optional[Any]:
        """Look up a cached tool result. Returns None on miss or expired."""
        with self._tool_result_cache_lock:
            entry = self._tool_result_cache.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() >= expires_at:
                self._tool_result_cache.pop(key, None)
                return None
            return value

    def cache_put(self, key: tuple, value: Any, ttl: Optional[float] = None) -> None:
        """Store a tool result with TTL. Evicts oldest entries when full."""
        ttl = ttl if ttl is not None else self._tool_result_cache_ttl
        expires_at = time.monotonic() + ttl
        with self._tool_result_cache_lock:
            self._tool_result_cache[key] = (expires_at, value)
            # Bounded eviction: drop the oldest entry if over capacity.
            if len(self._tool_result_cache) > self._tool_result_cache_max:
                # Pop the entry with the smallest expires_at (closest to expiry).
                oldest_key = min(self._tool_result_cache,
                                 key=lambda k: self._tool_result_cache[k][0])
                self._tool_result_cache.pop(oldest_key, None)

    def set_verbosity(self, verbosity: LogVerbosity) -> None:
        """Set the logging verbosity level."""
        self.request_logger.verbosity = verbosity
        logger.info(f"MCP logging verbosity set to: {verbosity.name}")

    def set_rate_limit_config(self, config: RateLimitConfig) -> None:
        """Update rate limiting configuration."""
        self.rate_limiter = RateLimiter(config)
        logger.info(
            f"MCP rate limiting updated: {config.requests_per_second} req/s, burst={config.burst_size}"
        )

    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return self.rate_limiter.get_stats()

    def _check_rate_limit(self, tool_name: str, client_id: Optional[str] = None) -> None:
        """Check rate limit and raise exception if exceeded."""
        self.rate_limiter.check_rate_limit(tool_name, client_id)

    def _register_tools(self):
        """Register MCP tools."""

        def tool_with_structured_logging():
            """Wrap MCP tools with structured request/response logging."""

            def decorator(func):
                tool_name = func.__name__

                @self.server.tool()
                @wraps(func)
                async def wrapped(*args, **kwargs):
                    start_time = self.request_logger.log_request(tool_name, kwargs)
                    try:
                        result = await func(*args, **kwargs)
                        result_error = result.get("error") if isinstance(result, dict) else None
                        response_error = RuntimeError(str(result_error)) if result_error else None
                        self.rate_limiter.record_tool_result(
                            tool_name,
                            time.time() - start_time,
                            had_error=response_error is not None,
                        )
                        self.request_logger.log_response(
                            tool_name,
                            result,
                            start_time,
                            error=response_error,
                        )
                        return result
                    except Exception as exc:
                        self.rate_limiter.record_tool_result(
                            tool_name,
                            time.time() - start_time,
                            had_error=True,
                        )
                        self.request_logger.log_response(
                            tool_name,
                            None,
                            start_time,
                            error=exc,
                        )
                        raise

                return wrapped

            return decorator

        @tool_with_structured_logging()
        async def yuho_check(
            file_content: str,
            include_metrics: bool = False,
            explain_errors: bool = False,
            client_id: Optional[str] = None,
        ) -> Dict[str, Any]:
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
                return mcp_error("rate_limited", str(e), retry=True, retry_after_seconds=e.retry_after)

            analysis = analyze_source(file_content, file="<mcp>", run_semantic=True)
            payload = analysis.validation_payload(include_metrics=include_metrics)
            if explain_errors:
                for item in payload["errors"]:
                    if item["stage"] != "parse":
                        continue
                    item["explanation"] = get_error_explanation(
                        item["message"],
                        item.get("node_type"),
                    )
            return payload

        @tool_with_structured_logging()
        async def yuho_transpile(
            file_content: str, target: str, client_id: Optional[str] = None
        ) -> Dict[str, Any]:
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
                return mcp_error("rate_limited", str(e), retry=True, retry_after_seconds=e.retry_after)

            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder
            from yuho.transpile import TranspileTarget, get_transpiler

            parser = get_parser()
            try:
                result = run_parser_boundary(
                    parser.parse,
                    file_content,
                    message="Failed to parse source",
                )
            except ParserBoundaryError as e:
                return mcp_error("internal_error", str(e))

            if result.errors:
                return mcp_error("parse_error", result.errors[0].message)

            try:
                builder = ASTBuilder(file_content)
                ast = run_ast_boundary(
                    builder.build,
                    result.root_node,
                    message="Failed to build AST",
                )
            except ASTBoundaryError as e:
                return mcp_error("internal_error", str(e))

            try:
                transpile_target = TranspileTarget.from_string(target)
                transpiler = get_transpiler(transpile_target)
                output = run_transpile_boundary(
                    transpiler.transpile,
                    ast,
                    message="Transpilation failed",
                )

                return {"output": output}
            except ValueError as e:
                return mcp_error("invalid_argument", f"Invalid target: {e}")
            except TranspileBoundaryError as e:
                return mcp_error("internal_error", str(e))

        @tool_with_structured_logging()
        async def yuho_explain(
            file_content: str, section: Optional[str] = None, client_id: Optional[str] = None
        ) -> Dict[str, Any]:
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
                return mcp_error("rate_limited", str(e), retry=True, retry_after_seconds=e.retry_after)

            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder
            from yuho.transpile import EnglishTranspiler

            parser = get_parser()
            try:
                result = run_parser_boundary(
                    parser.parse,
                    file_content,
                    message="Failed to parse source",
                )
            except ParserBoundaryError as e:
                return mcp_error("internal_error", str(e))

            if result.errors:
                return mcp_error("parse_error", result.errors[0].message)

            try:
                builder = ASTBuilder(file_content)
                ast = run_ast_boundary(
                    builder.build,
                    result.root_node,
                    message="Failed to build AST",
                )
            except ASTBoundaryError as e:
                return mcp_error("internal_error", str(e))

            # Filter to specific section if requested
            if section:
                from yuho.ast.nodes import ModuleNode

                matching = [s for s in ast.statutes if section in s.section_number]
                if not matching:
                    return mcp_error("not_found", f"Section {section} not found", section=section)
                ast = ModuleNode(
                    imports=ast.imports,
                    type_defs=ast.type_defs,
                    function_defs=ast.function_defs,
                    statutes=tuple(matching),
                    variables=ast.variables,
                )

            try:
                transpiler = EnglishTranspiler()
                explanation = run_transpile_boundary(
                    transpiler.transpile,
                    ast,
                    message="Failed to generate explanation",
                )
                return {"explanation": explanation}
            except TranspileBoundaryError as e:
                return mcp_error("internal_error", str(e))

        @tool_with_structured_logging()
        async def yuho_parse(file_content: str) -> Dict[str, Any]:
            """
            Parse Yuho source and return AST.

            Args:
                file_content: The Yuho source code

            Returns:
                {ast: dict} or {error: str}
            """
            from yuho.transpile import JSONTranspiler

            analysis = analyze_source(file_content, file="<mcp>", run_semantic=False)
            if not analysis.parse_valid or not analysis.ast_valid or analysis.ast is None:
                payload = analysis.validation_payload()
                first_error = (
                    payload["errors"][0]
                    if payload["errors"]
                    else {
                        "message": "Failed to build AST",
                    }
                )
                return mcp_error("invalid_argument", first_error["message"], validation=payload)

            # Use JSON transpiler to serialize AST
            json_transpiler = JSONTranspiler(include_locations=False)
            ast_json = json_transpiler.transpile(analysis.ast)

            return {"ast": json.loads(ast_json)}

        @tool_with_structured_logging()
        async def yuho_format(file_content: str) -> Dict[str, Any]:
            """
            Format Yuho source code.

            Args:
                file_content: The Yuho source code

            Returns:
                {formatted: str} or {error: str}
            """
            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder
            from yuho.cli.commands.fmt import _format_module

            parser = get_parser()
            try:
                result = run_parser_boundary(
                    parser.parse,
                    file_content,
                    message="Failed to parse source",
                )
            except ParserBoundaryError as e:
                return mcp_error("internal_error", str(e))

            if result.errors:
                return mcp_error("parse_error", result.errors[0].message)

            try:
                builder = ASTBuilder(file_content)
                ast = run_ast_boundary(
                    builder.build,
                    result.root_node,
                    message="Failed to build AST",
                )
            except ASTBoundaryError as e:
                return mcp_error("internal_error", str(e))

            try:
                formatted = _format_module(ast)
                return {"formatted": formatted}
            except (TypeError, ValueError, AttributeError, RuntimeError) as e:
                return mcp_error("internal_error", str(e))

        @tool_with_structured_logging()
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
            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder

            completions: List[Dict[str, str]] = []

            # Keywords
            keywords = [
                "struct",
                "fn",
                "match",
                "case",
                "consequence",
                "pass",
                "return",
                "statute",
                "definitions",
                "elements",
                "penalty",
                "illustration",
                "import",
                "from",
                "TRUE",
                "FALSE",
            ]
            completions.extend({"label": kw, "kind": "keyword"} for kw in keywords)

            # Types
            types = ["int", "float", "bool", "string", "money", "percent", "date", "duration"]
            completions.extend({"label": t, "kind": "type"} for t in types)

            # Parse to get symbols
            parser = get_parser()
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

                except Exception as exc:
                    logger.warning(
                        "MCP tool yuho_complete symbol enrichment failed: %s",
                        mask_error(exc),
                    )

            return {"completions": completions}

        @tool_with_structured_logging()
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
            from yuho.parser import get_parser
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
            while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == "_"):
                start -= 1
            while end < len(target_line) and (
                target_line[end].isalnum() or target_line[end] == "_"
            ):
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
            parser = get_parser()
            result = parser.parse(file_content)

            if result.is_valid:
                try:
                    builder = ASTBuilder(file_content)
                    ast = builder.build(result.root_node)

                    # Check structs
                    for struct in ast.type_defs:
                        if struct.name == word:
                            fields = ", ".join(
                                f"{f.name}: {f.type_annotation}" for f in struct.fields
                            )
                            return {
                                "info": f"**struct** `{struct.name}`\n\n```yuho\nstruct {struct.name} {{ {fields} }}\n```"
                            }

                    # Check functions
                    for func in ast.function_defs:
                        if func.name == word:
                            params = ", ".join(
                                f"{p.name}: {p.type_annotation}" for p in func.params
                            )
                            ret = f" -> {func.return_type}" if func.return_type else ""
                            return {
                                "info": f"**function** `{func.name}`\n\n```yuho\nfn {func.name}({params}){ret}\n```"
                            }

                    # Check statutes
                    for statute in ast.statutes:
                        if statute.section_number == word or f"S{statute.section_number}" == word:
                            title = statute.title.value if statute.title else "Untitled"
                            info = f"**Statute Section {statute.section_number}**: {title}"
                            if statute.elements:
                                info += "\n\n**Elements:**\n"
                                for elem in _iter_leaf_elements(list(statute.elements)):
                                    info += f"- {elem.element_type}: {elem.name}\n"
                            return {"info": info}

                except Exception as exc:
                    logger.warning(
                        "MCP tool yuho_hover symbol inspection failed: %s",
                        mask_error(exc),
                    )

            return {"info": None}

        @tool_with_structured_logging()
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
            from yuho.parser import get_parser
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
            while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == "_"):
                start -= 1
            while end < len(target_line) and (
                target_line[end].isalnum() or target_line[end] == "_"
            ):
                end += 1

            if start == end:
                return {"location": None}

            word = target_line[start:end]

            # Parse for symbol definitions
            parser = get_parser()
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
                        if (
                            statute.section_number == word or f"S{statute.section_number}" == word
                        ) and statute.source_location:
                            return {
                                "location": {
                                    "line": statute.source_location.line,
                                    "col": statute.source_location.col,
                                }
                            }

                except Exception as exc:
                    logger.warning(
                        "MCP tool yuho_definition symbol lookup failed: %s",
                        mask_error(exc),
                    )

            return {"location": None}

        @tool_with_structured_logging()
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
            from yuho.parser import get_parser
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
            while start > 0 and (target_line[start - 1].isalnum() or target_line[start - 1] == "_"):
                start -= 1
            while end < len(target_line) and (
                target_line[end].isalnum() or target_line[end] == "_"
            ):
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
                    before_ok = pos == 0 or not (ln[pos - 1].isalnum() or ln[pos - 1] == "_")
                    after_pos = pos + len(word)
                    after_ok = after_pos >= len(ln) or not (
                        ln[after_pos].isalnum() or ln[after_pos] == "_"
                    )
                    if before_ok and after_ok:
                        locations.append(
                            {
                                "line": i,
                                "col": pos + 1,
                                "end_line": i,
                                "end_col": after_pos + 1,
                            }
                        )
                    c = after_pos

            return {"locations": locations}

        @tool_with_structured_logging()
        async def yuho_symbols(file_content: str) -> Dict[str, Any]:
            """
            Get all symbols in the document.

            Args:
                file_content: The Yuho source code

            Returns:
                {symbols: list of {name, kind, line, col}}
            """
            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder

            parser = get_parser()
            result = parser.parse(file_content)

            if result.errors:
                return mcp_error("parse_error", result.errors[0].message, symbols=[])

            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)

                symbols = []

                # Structs
                for struct in ast.type_defs:
                    loc = struct.source_location
                    symbols.append(
                        {
                            "name": struct.name,
                            "kind": "struct",
                            "line": loc.line if loc else 0,
                            "col": loc.col if loc else 0,
                        }
                    )

                # Functions
                for func in ast.function_defs:
                    loc = func.source_location
                    symbols.append(
                        {
                            "name": func.name,
                            "kind": "function",
                            "line": loc.line if loc else 0,
                            "col": loc.col if loc else 0,
                        }
                    )

                # Statutes
                for statute in ast.statutes:
                    loc = statute.source_location
                    title = statute.title.value if statute.title else ""
                    symbols.append(
                        {
                            "name": f"S{statute.section_number}: {title}",
                            "kind": "statute",
                            "line": loc.line if loc else 0,
                            "col": loc.col if loc else 0,
                        }
                    )

                return {"symbols": symbols}
            except Exception as e:
                return mcp_error("internal_error", str(e), symbols=[])

        @tool_with_structured_logging()
        async def yuho_diagnostics(file_content: str) -> Dict[str, Any]:
            """
            Get diagnostics (errors, warnings) for the document.

            Args:
                file_content: The Yuho source code

            Returns:
                {diagnostics: list of {message, severity, line, col}}
            """
            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder
            from yuho.ast.type_inference import TypeInferenceVisitor
            from yuho.ast.type_check import TypeCheckVisitor

            diagnostics = []
            parser = get_parser()
            result = parser.parse(file_content)

            # Parse errors
            for parse_error in result.errors:
                diagnostics.append(
                    {
                        "message": parse_error.message,
                        "severity": "error",
                        "line": parse_error.location.line,
                        "col": parse_error.location.col,
                    }
                )

            # Try AST build for more diagnostics
            if result.is_valid:
                try:
                    builder = ASTBuilder(file_content)
                    ast = builder.build(result.root_node)

                    # Run semantic analysis (type inference + type checking)
                    try:
                        infer_visitor = TypeInferenceVisitor()
                        ast.accept(infer_visitor)
                        check_visitor = TypeCheckVisitor(infer_visitor.result)
                        ast.accept(check_visitor)
                        for type_error in check_visitor.result.errors:
                            diagnostics.append(
                                {
                                    "message": type_error.message,
                                    "severity": "error",
                                    "line": type_error.line,
                                    "col": type_error.column,
                                }
                            )
                        for warning in check_visitor.result.warnings:
                            diagnostics.append(
                                {
                                    "message": warning.message,
                                    "severity": "warning",
                                    "line": warning.line,
                                    "col": warning.column,
                                }
                            )
                    except Exception as e:
                        logger.warning(f"Semantic analysis failed: {e}")
                except Exception as e:
                    diagnostics.append(
                        {
                            "message": str(e),
                            "severity": "error",
                            "line": 1,
                            "col": 1,
                        }
                    )

            return {"diagnostics": diagnostics}

        @tool_with_structured_logging()
        async def yuho_validate_contribution(
            file_content: str, tests: Optional[List[str]] = None
        ) -> Dict[str, Any]:
            """
            Validate a statute file for contribution to the library.

            Args:
                file_content: The Yuho source code
                tests: Optional list of test file contents

            Returns:
                {valid: bool, results: list}
            """
            from yuho.parser import get_parser
            from yuho.ast import ASTBuilder

            tests = tests or []
            results = []

            # Check parsing
            parser = get_parser()
            result = parser.parse(file_content)

            if result.errors:
                return {
                    "valid": False,
                    "results": [
                        {
                            "check": "parse",
                            "passed": False,
                            "message": result.errors[0].message,
                        }
                    ],
                }

            results.append({"check": "parse", "passed": True, "message": "Parses successfully"})

            # Check AST build
            try:
                builder = ASTBuilder(file_content)
                ast = builder.build(result.root_node)
                results.append(
                    {"check": "ast", "passed": True, "message": "AST builds successfully"}
                )
            except Exception as e:
                return {
                    "valid": False,
                    "results": results
                    + [
                        {
                            "check": "ast",
                            "passed": False,
                            "message": str(e),
                        }
                    ],
                }

            # Check has statutes
            if not ast.statutes:
                results.append(
                    {
                        "check": "statute",
                        "passed": False,
                        "message": "No statutes defined",
                    }
                )
            else:
                results.append(
                    {
                        "check": "statute",
                        "passed": True,
                        "message": f"Contains {len(ast.statutes)} statute(s)",
                    }
                )

            # Check tests exist
            if not tests:
                results.append(
                    {
                        "check": "tests",
                        "passed": False,
                        "message": "No test files provided",
                    }
                )
            else:
                results.append(
                    {
                        "check": "tests",
                        "passed": True,
                        "message": f"{len(tests)} test file(s) provided",
                    }
                )

            valid = all(r["passed"] for r in results)
            return {"valid": valid, "results": results}

        @tool_with_structured_logging()
        async def yuho_library_search(query: str) -> Dict[str, Any]:
            """
            Search statute library by section number, title, or jurisdiction.

            Args:
                query: Search query string

            Returns:
                {statutes: list of {section, title, jurisdiction, path}}
            """
            import tomllib

            library_path = Path(__file__).parent.parent.parent.parent / "library"
            results = []

            query_lower = query.lower()

            if library_path.exists():
                for meta_file in library_path.glob("**/metadata.toml"):
                    try:
                        with open(meta_file, "rb") as f:
                            meta = tomllib.load(f)
                        statute = meta.get("statute", {})
                        description = meta.get("description", {})
                        section = statute.get("section_number", "")
                        title = statute.get("title", "")
                        jurisdiction = statute.get("jurisdiction", "")
                        summary = description.get("summary", "")

                        searchable = f"{section} {title} {jurisdiction} {summary}".lower()
                        if query_lower in searchable:
                            statute_dir = meta_file.parent
                            yh_files = list(statute_dir.glob("statute.yh"))
                            path = str(yh_files[0]) if yh_files else str(statute_dir)
                            results.append(
                                {
                                    "section": section,
                                    "title": title,
                                    "jurisdiction": jurisdiction,
                                    "path": path,
                                }
                            )
                    except Exception:
                        continue

            return {"statutes": results[:20]}

        @tool_with_structured_logging()
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
                            return mcp_error("internal_error", str(e))

            return mcp_error("not_found", f"Section {section} not found", section=section)

        # (yuho_statute_to_yuho was cut in the Phase D endpoint trim.
        # MCP clients own the LLM; they can construct Yuho code themselves
        # using the schema and examples exposed by other MCP resources.)

        # ====================================================================
        # Phase D expansion — workflow + library-nav tools
        # ====================================================================

        @tool_with_structured_logging()
        async def yuho_find_by_anchor(anchor: str) -> Dict[str, Any]:
            """
            Resolve an SSO provision anchor (e.g. `pr415-`) to its encoded
            section in the library.

            Args:
                anchor: SSO anchor id. Leading `pr` and trailing `-` optional.

            Returns:
                {section, title, path} or {error}.
            """
            import re, tomllib
            # normalise to bare section number
            a = anchor.strip()
            m = re.match(r"^(?:pr)?(\d+[A-Za-z]*)-?$", a)
            if not m: return mcp_error("invalid_argument", f"anchor not recognised: {anchor!r}", anchor=anchor)
            section = m.group(1)
            library_path = Path(__file__).parent.parent.parent.parent / "library"
            for meta_file in library_path.glob("**/metadata.toml"):
                try:
                    with open(meta_file, "rb") as f: meta = tomllib.load(f)
                    if meta.get("statute", {}).get("section_number", "") == section:
                        yh = meta_file.parent / "statute.yh"
                        return {
                            "section": section,
                            "title": meta.get("statute", {}).get("title", ""),
                            "path": str(yh) if yh.exists() else str(meta_file.parent),
                            "sso_url": meta.get("verification", {}).get("sso_url", ""),
                        }
                except Exception: continue
            return mcp_error("not_found", f"section {section} not found", section=section)

        @tool_with_structured_logging()
        async def yuho_find_citations_to(section: str) -> Dict[str, Any]:
            """
            List sections in the library whose encoded `.yh` text references a
            given section — useful for "what extends s415?" queries.

            Args:
                section: Section number (e.g., "415").

            Returns:
                {citers: list of {section, title, path, snippet}}.
            """
            import re, tomllib
            library_path = Path(__file__).parent.parent.parent.parent / "library"
            # match "s<num>", "section <num>", and bare `referencing … s<num>` patterns
            pat = re.compile(rf"(?<![A-Za-z0-9]){re.escape(section)}(?![A-Za-z0-9])")
            citers: list[Dict[str, Any]] = []
            for yh in library_path.glob("**/statute.yh"):
                # skip self-references
                m = re.match(r"s(\d+[A-Z]*)_", yh.parent.name)
                if m and m.group(1) == section: continue
                try:
                    text = yh.read_text()
                except Exception: continue
                if pat.search(text):
                    # best-effort snippet
                    snip_m = pat.search(text)
                    lo = max(0, snip_m.start() - 40)
                    hi = min(len(text), snip_m.end() + 40)
                    meta_file = yh.parent / "metadata.toml"
                    title = ""
                    if meta_file.exists():
                        try:
                            with open(meta_file, "rb") as f:
                                title = tomllib.load(f).get("statute", {}).get("title", "")
                        except Exception: pass
                    citers.append({
                        "section": m.group(1) if m else yh.parent.name,
                        "title": title,
                        "path": str(yh),
                        "snippet": text[lo:hi].replace("\n", " "),
                    })
            return {"citers": citers[:50], "count": len(citers)}

        @tool_with_structured_logging()
        async def yuho_section_pair(section: str, include_ast: bool = False) -> Dict[str, Any]:
            """
            Return canonical raw SSO text + encoded `.yh` source side by side
            for a given PC section. The primary tool for fidelity review — an
            MCP client uses this to decide STAMP vs FLAG.

            Args:
                section: Section number (e.g., "415").
                include_ast: if True, also parse the encoded file and return a
                    JSON-serialised AST summary (saves a separate yuho_parse
                    round-trip for structural reasoning).

            Returns:
                {section, marginal_note, canonical: {text, sub_items, amendments},
                 encoded: {path, source, metadata_toml, ast?}} or {error}.
            """
            import json as _j, re, tomllib
            repo = Path(__file__).parent.parent.parent.parent
            raw_path = repo / "library" / "penal_code" / "_raw" / "act.json"
            if not raw_path.is_file():
                return mcp_error("not_found", "_raw/act.json missing — run scripts/scrape_sso.py")
            raw = _j.loads(raw_path.read_text())
            by_num = {s["number"]: s for s in raw.get("sections", []) if s.get("number")}
            sec = by_num.get(section)
            if not sec: return mcp_error("not_found", f"section {section} not in canonical corpus", section=section)
            # find encoded dir
            encoded = {"path": None, "source": None, "metadata_toml": None}
            for p in (repo / "library" / "penal_code").iterdir():
                if p.is_dir() and re.match(rf"s{section}_", p.name):
                    yh = p / "statute.yh"
                    meta = p / "metadata.toml"
                    encoded["path"] = str(yh) if yh.exists() else str(p)
                    if yh.exists(): encoded["source"] = yh.read_text()
                    if meta.exists(): encoded["metadata_toml"] = meta.read_text()
                    break
            # optional AST payload
            if include_ast and encoded.get("source"):
                try:
                    from yuho.services.analysis import analyze_source
                    ar = analyze_source(encoded["source"], file="section.yh")
                    if ar.ast is not None:
                        encoded["ast_summary"] = {
                            "statute_count": len(ar.ast.statutes),
                            "statutes": [
                                {
                                    "section_number": s.section_number,
                                    "title": s.title.value if s.title else None,
                                    "definition_count": len(s.definitions),
                                    "element_count": sum(1 for _ in s.elements),
                                    "illustration_count": len(s.illustrations),
                                    "exception_count": len(s.exceptions),
                                    "subsection_count": len(s.subsections),
                                    "has_penalty": bool(s.penalty),
                                    "effective_dates": list(s.effective_dates or (
                                        (s.effective_date,) if s.effective_date else ())),
                                }
                                for s in ar.ast.statutes
                            ],
                        }
                except Exception as exc:
                    encoded["ast_error"] = mask_error(exc)
            return {
                "section": section,
                "marginal_note": sec.get("marginal_note", ""),
                "canonical": {
                    "text": sec.get("text", ""),
                    "sub_items": sec.get("sub_items", []),
                    "amendments": sec.get("amendments", []),
                    "anchor_id": sec.get("anchor_id", ""),
                },
                "encoded": encoded,
            }

        @tool_with_structured_logging()
        async def yuho_coverage_status() -> Dict[str, Any]:
            """
            Return the current L1 / L2 / L3 coverage summary for the Penal Code
            library, plus which sections are still unencoded.

            Returns:
                {totals, l3_pct, unencoded: list of section numbers,
                 flagged: list of section numbers with open L3 flags}.
            """
            import json as _j
            repo = Path(__file__).parent.parent.parent.parent
            cov_path = repo / "library" / "penal_code" / "_coverage" / "coverage.json"
            if not cov_path.is_file():
                return mcp_error("not_found", "coverage.json missing — run scripts/coverage_report.py")
            cov = _j.loads(cov_path.read_text())
            totals = cov.get("totals", {})
            unencoded = [
                r["number"] for r in cov.get("sections", [])
                if not r.get("encoded_path") and r.get("number")
            ]
            flagged: list[str] = []
            for flag_file in (repo / "library" / "penal_code").glob("s*/_L3_FLAG.md"):
                import re
                m = re.match(r"s(\d+[A-Z]*)_", flag_file.parent.name)
                if m: flagged.append(m.group(1))
            return {
                "totals": totals,
                "unencoded": unencoded[:50],
                "unencoded_count": len(unencoded),
                "flagged": flagged,
                "flagged_count": len(flagged),
            }

        @tool_with_structured_logging()
        async def yuho_propose_encoding_skeleton(
            section: str, shape: str = "auto"
        ) -> Dict[str, Any]:
            """
            Return a skeleton `.yh` file for a given canonical PC section —
            boilerplate headers, `statute {N} "<marginal>" effective …`,
            pre-filled with the canonical text as comments. The MCP client's
            LLM then fills in the semantics.

            Args:
                section: Section number (e.g., "415").
                shape: One of `auto | offence | punishment | interpretation |
                       scope | defence`. `auto` leaves it to the client.

            Returns:
                {section, slug, skeleton_yh} or {error}.
            """
            import json as _j, re
            repo = Path(__file__).parent.parent.parent.parent
            raw_path = repo / "library" / "penal_code" / "_raw" / "act.json"
            if not raw_path.is_file(): return mcp_error("not_found", "_raw/act.json missing — run scripts/scrape_sso.py")
            raw = _j.loads(raw_path.read_text())
            by_num = {s["number"]: s for s in raw.get("sections", []) if s.get("number")}
            sec = by_num.get(section)
            if not sec: return mcp_error("not_found", f"section {section} not in canonical corpus", section=section)
            marginal = sec.get("marginal_note", f"Section {section}")
            anchor = sec.get("anchor_id", f"pr{section}-")
            # slug: snake-case from marginal, dropping stopwords
            stop = {"of","and","the","in","for","to","with","by","on","or","a","an"}
            words = re.findall(r"[A-Za-z0-9]+", marginal.lower())
            slug = "_".join(w for w in words if w not in stop)[:45]
            amendments = sec.get("amendments", [])
            amend_lines = "\n".join(f"/// @amendment {a.get('marker','')}" for a in amendments)
            canonical_excerpt = (sec.get("text", "")[:500] + "…") if sec.get("text") else ""

            skeleton = f'''/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds={anchor}#{anchor}
{amend_lines}

// Canonical text (for reference during encoding; do not treat as Yuho source):
//   {canonical_excerpt}

statute {section} "{marginal}" effective 1872-01-01 {{
    // TODO: fill in based on `shape` ({shape}).
    // - offence: elements {{ all_of {{ actus_reus …; mens_rea …; }} }} + penalty
    // - punishment: penalty only, cross-ref target offence in a doc comment
    // - interpretation: definitions {{ term := "…"; }}
    // - scope: minimal body; provision text in definitions or doc comment
    // - defence: encode as a function returning a bool, or exception block

    definitions {{
    }}
}}
'''
            return {
                "section": section,
                "slug": slug,
                "dir_hint": f"library/penal_code/s{section}_{slug}/",
                "skeleton_yh": skeleton,
                "canonical_sub_item_count": len(sec.get("sub_items", [])),
                "hint_shape": shape,
            }

        @tool_with_structured_logging()
        async def yuho_run_l3_review(section: str) -> Dict[str, Any]:
            """
            Run the Phase-D 11-point L3 checklist on a section and return a
            structured STAMP/FLAG decision. Unlike the `recommend_l3` prompt
            (which instructs an LLM to audit), this tool does the mechanical
            parts directly — illustration count, penalty-clause sanity, date
            sanity, placeholder-text grep — and returns the results as data.

            The client still has to make the final judgement call on
            semantic items (all_of vs any_of matching English, etc.); this
            tool surfaces the evidence.

            Args:
                section: Section number (e.g., "415").

            Returns:
                {section, checklist: [{item, passed, detail}],
                 mechanical_decision: "STAMP_CANDIDATE" | "FLAG",
                 encoded_exists, canonical_exists}
            """
            import json as _j, re as _re, tomllib
            repo = Path(__file__).parent.parent.parent.parent
            raw_path = repo / "library" / "penal_code" / "_raw" / "act.json"
            if not raw_path.is_file():
                return mcp_error("not_found", "_raw/act.json missing — run scripts/scrape_sso.py")
            raw = _j.loads(raw_path.read_text())
            by_num = {s["number"]: s for s in raw.get("sections", []) if s.get("number")}
            sec = by_num.get(section)
            if not sec:
                return mcp_error("not_found", f"section {section} not in canonical corpus", section=section)

            d = None
            for p in (repo / "library" / "penal_code").iterdir():
                if p.is_dir() and _re.match(rf"s{section}_", p.name):
                    d = p; break
            if not d or not (d / "statute.yh").exists():
                return mcp_error("not_found", f"no encoded statute.yh for s{section}", section=section)
            source = (d / "statute.yh").read_text()

            checklist: list[Dict[str, Any]] = []
            def _rec(item: int, name: str, passed: bool, detail: str = "") -> None:
                checklist.append({"item": item, "name": name, "passed": passed, "detail": detail})

            # 1 — section number matches
            m = _re.search(r"statute\s+(\d+[A-Za-z]*)", source)
            _rec(1, "section number matches", m is not None and m.group(1) == section,
                 f"found `statute {m.group(1) if m else '?'}`")

            # 2 — marginal note present (we can't do verbatim without fuzzy match)
            marginal = sec.get("marginal_note", "")
            _rec(2, "marginal note present", marginal.split()[0] in source if marginal else True,
                 f"marginal: {marginal[:60]}")

            # 3 — illustration count match
            canonical_ills = sum(1 for it in sec.get("sub_items", [])
                                 if it.get("kind") == "illustration"
                                 or (it.get("kind") == "item" and _re.match(r"^\s*\([a-z]\)", it.get("text","").strip())))
            encoded_ills = len(_re.findall(r"^\s*illustration\s+\w+\s*\{", source, _re.MULTILINE))
            _rec(3, "illustration count ≥ canonical", encoded_ills >= canonical_ills,
                 f"encoded={encoded_ills}, canonical≈{canonical_ills}")

            # 4 — explanations preserved
            canonical_expls = sum(1 for it in sec.get("sub_items", []) if it.get("kind") == "explanation")
            # check presence as doc comment, refinement, or definitions entry
            encoded_expls = len(_re.findall(r"Explanation\s*\d*", source))
            _rec(4, "explanations preserved", (canonical_expls == 0) or (encoded_expls >= canonical_expls),
                 f"encoded={encoded_expls}, canonical={canonical_expls}")

            # 5 — exceptions preserved
            canonical_excs = sum(1 for it in sec.get("sub_items", []) if it.get("kind") == "exception")
            encoded_excs = len(_re.findall(r"^\s*exception\s", source, _re.MULTILINE))
            _rec(5, "exceptions preserved", canonical_excs == 0 or encoded_excs >= canonical_excs,
                 f"encoded={encoded_excs}, canonical={canonical_excs}")

            # 6 — subsections preserved
            canonical_subs = sum(1 for it in sec.get("sub_items", []) if it.get("kind") == "subsection")
            encoded_subs = len(_re.findall(r"^\s*subsection\s+\(", source, _re.MULTILINE))
            _rec(6, "subsections preserved (if canonical has any)",
                 canonical_subs == 0 or encoded_subs >= canonical_subs,
                 f"encoded={encoded_subs}, canonical={canonical_subs}")

            # 7 — no fabricated caning stroke range
            canonical_text = sec.get("text", "")
            # only check statutes that DO mention caning
            has_caning_liability = "liable to caning" in canonical_text or "caning" in canonical_text
            # canonical gives explicit number?
            canonical_has_stroke_num = bool(_re.search(r"(not less than|at least|up to|may extend to)?\s*\d+\s*strokes", canonical_text))
            # encoding uses a fabricated 0 .. N caning range
            fabricated = bool(_re.search(r"caning\s*:=\s*0\s*\.\.\s*\d+\s*strokes", source))
            _rec(7, "no fabricated caning range",
                 (not fabricated) or canonical_has_stroke_num,
                 f"has_caning_liability={has_caning_liability}, canonical_has_number={canonical_has_stroke_num}, encoding_fabricates={fabricated}")

            # 8 — no fabricated fine cap
            canonical_has_fine_number = bool(_re.search(r"\$[0-9,]+", canonical_text) or
                                              _re.search(r"fine\s+(of|which may extend to)\s+[^\.]+\d", canonical_text))
            has_fine_clause = bool(_re.search(r"^\s*fine\s*:=", source, _re.MULTILINE))
            uses_numeric_fine = bool(_re.search(r"fine\s*:=\s*\$[^\.]+\.\.\s*\$", source))
            _rec(8, "no fabricated fine cap",
                 (not uses_numeric_fine) or canonical_has_fine_number,
                 f"canonical_has_number={canonical_has_fine_number}, uses_numeric={uses_numeric_fine}")

            # 9 — no placeholder text
            has_placeholder = bool(_re.search(r"\b(TODO|lorem|placeholder|xxx|FIXME)\b", source, _re.IGNORECASE))
            _rec(9, "no placeholder text", not has_placeholder,
                 f"has_placeholder={has_placeholder}")

            # 10 — effective date sane (if amendment present, need multi-effective)
            has_amendment = bool(sec.get("amendments"))
            effective_count = len(_re.findall(r"effective\s+\d{4}-\d{2}-\d{2}", source))
            _rec(10, "effective date count matches amendment presence",
                 (effective_count >= 2) if has_amendment else (effective_count >= 1),
                 f"has_amendment={has_amendment}, effective_count={effective_count}")

            # 11 — yuho check passes
            check_ok = False
            try:
                import subprocess as _sp
                r = _sp.run(
                    [str(repo / ".venv-scrape" / "bin" / "yuho"),
                     "check", "--format", "json", str(d / "statute.yh")],
                    capture_output=True, text=True, timeout=60,
                )
                check_ok = _j.loads(r.stdout).get("valid", False) if r.stdout else False
            except Exception: check_ok = False
            _rec(11, "yuho check passes", check_ok, "")

            mechanical_decision = "STAMP_CANDIDATE" if all(c["passed"] for c in checklist) else "FLAG"
            return {
                "section": section,
                "checklist": checklist,
                "mechanical_decision": mechanical_decision,
                "encoded_exists": True,
                "canonical_exists": True,
                "note": (
                    "Mechanical-only: items 1-3,5-11 are regex/count-based. "
                    "Items 4 (explanations structure), 8 (fabricated caps that are structurally fine), "
                    "and semantic all_of/any_of matching still need LLM judgement."
                ),
            }

        @tool_with_structured_logging()
        async def yuho_apply_flag_fix(
            section: str, failed: str, reason: str, suggested_fix: str = "",
            ctx: Optional[Any] = None,
        ) -> Dict[str, Any]:
            """
            Trigger the minimum-edit flag-fix workflow on a section. Writes
            a transient `_L3_FLAG.md` in the section's dir, invokes the
            same script (`scripts/phase_d_flag_fix.py`) used in Phase D
            to patch the encoding, runs `yuho check`, and returns the
            outcome.

            Streams progress via `ctx.report_progress(...)` while the
            dispatcher runs so the AI client can show "still working"
            instead of appearing hung. The `ctx` parameter is injected
            by FastMCP when called from a session that supports it.

            NOTE: this tool requires `codex` to be on PATH (uses Codex
            for the actual edit). Returns an ERROR outcome if codex is
            not available.

            Args:
                section: Section number.
                failed: checklist items that fail (e.g. "7" or "7, 8").
                reason: one-sentence explanation.
                suggested_fix: optional one-sentence fix direction.

            Returns:
                {section, outcome: "FIXED" | "PARTIAL" | "UNCHANGED" | "BROKEN" | "ERROR",
                 error?, yuho_check?, flag_deleted?}
            """
            import subprocess as _sp, re as _re, json as _j, time as _time
            repo = Path(__file__).parent.parent.parent.parent
            d = None
            for p in (repo / "library" / "penal_code").iterdir():
                if p.is_dir() and _re.match(rf"s{section}_", p.name): d = p; break
            if not d:
                return mcp_error(
                    "not_found",
                    f"no directory found for section s{section}",
                    section=section,
                    outcome="ERROR",
                )
            # seed the flag file
            flag_body = (
                f"# s{section} — L3 flag\n\n"
                f"- failed: {failed}\n"
                f"- reason: {reason}\n"
            )
            if suggested_fix:
                flag_body += f"- suggested fix: {suggested_fix}\n"
            (d / "_L3_FLAG.md").write_text(flag_body)

            async def _report(progress: float, message: str) -> None:
                """Best-effort progress notification to the client."""
                if ctx is None:
                    return
                try:
                    await ctx.report_progress(progress=progress, total=1.0, message=message)
                except Exception:
                    # Older clients / clients without progress support.
                    pass

            await _report(0.05, "writing _L3_FLAG.md and dispatching codex agent")

            # Run the dispatcher with Popen so we can stream progress lines.
            try:
                proc = _sp.Popen(
                    [str(repo / ".venv-scrape" / "bin" / "python"),
                     str(repo / "scripts" / "phase_d_flag_fix.py"),
                     section, "--dispatch", "--parallel", "1",
                     "--timeout", "600", "--model", "gpt-5.4",
                     "--reasoning", "high"],
                    stdout=_sp.PIPE,
                    stderr=_sp.STDOUT,
                    text=True,
                )
            except FileNotFoundError:
                return mcp_error(
                    "unavailable",
                    "codex CLI or python venv not available; install codex and create .venv-scrape",
                    section=section,
                    outcome="ERROR",
                )

            stdout_lines: List[str] = []
            start = _time.time()
            timeout_s = 900
            # Pump stdout: report each non-blank line as a progress message.
            # We don't have a known total, so we ramp progress from 0.05 → 0.9
            # as the dispatcher runs, leaving the last 10% for the post-run
            # yuho-check. Yields to the asyncio loop on every iteration so
            # MCP cancellation (CancelledError) lands here promptly; on
            # cancellation we terminate the subprocess and return a
            # structured cancelled-outcome envelope.
            import asyncio as _asyncio
            try:
                while True:
                    # Cooperative cancellation point.
                    await _asyncio.sleep(0)

                    if _time.time() - start > timeout_s:
                        proc.terminate()
                        return mcp_error(
                            "timeout",
                            f"flag-fix dispatcher exceeded {timeout_s}s timeout",
                            section=section,
                            outcome="ERROR",
                            partial_stdout="".join(stdout_lines)[-400:],
                        )
                    line = proc.stdout.readline() if proc.stdout else ""
                    if not line:
                        if proc.poll() is not None:
                            break
                        # Brief sleep so the loop doesn't busy-spin and so
                        # cancellation latency stays bounded (10ms here).
                        await _asyncio.sleep(0.01)
                        continue
                    stdout_lines.append(line)
                    # Heuristic progress: ramp toward 0.9 with each line.
                    elapsed = _time.time() - start
                    progress = min(0.9, 0.1 + (elapsed / timeout_s) * 0.8)
                    msg = line.strip()[:120]
                    if msg:
                        await _report(progress, msg)
                proc.wait()
            except _asyncio.CancelledError:
                # Client requested cancellation. Tear down the dispatcher
                # cleanly and surface a structured "cancelled" envelope so
                # callers can distinguish from genuine errors.
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                # Drop the half-written flag file; the user's previous
                # state is preserved on the .yh file (we never edited it).
                try:
                    (d / "_L3_FLAG.md").unlink(missing_ok=True)
                except Exception:
                    pass
                return mcp_error(
                    "cancelled",
                    "flag-fix cancelled by client request",
                    section=section,
                    outcome="CANCELLED",
                    partial_stdout="".join(stdout_lines)[-400:],
                    retry=True,
                )
            except Exception as e:
                return mcp_error(
                    "subprocess_failed",
                    f"flag-fix dispatcher raised {type(e).__name__}: {e}",
                    section=section,
                    outcome="ERROR",
                    partial_stdout="".join(stdout_lines)[-400:],
                )

            class _Result:
                stdout = "".join(stdout_lines)
            r = _Result()
            await _report(0.95, "running yuho check on patched encoding")
            # determine outcome
            flag_still_there = (d / "_L3_FLAG.md").exists()
            check_ok = False
            try:
                rc = _sp.run(
                    [str(repo / ".venv-scrape" / "bin" / "yuho"),
                     "check", "--format", "json", str(d / "statute.yh")],
                    capture_output=True, text=True, timeout=60,
                )
                check_ok = _j.loads(rc.stdout).get("valid", False) if rc.stdout else False
            except Exception: pass
            if not flag_still_there and check_ok: outcome = "FIXED"
            elif not flag_still_there and not check_ok: outcome = "BROKEN"
            elif flag_still_there and check_ok: outcome = "PARTIAL"
            else: outcome = "UNCHANGED"
            return {
                "section": section,
                "outcome": outcome,
                "yuho_check": check_ok,
                "flag_deleted": not flag_still_there,
                "dispatcher_stdout_tail": r.stdout[-400:] if r.stdout else "",
            }

        @tool_with_structured_logging()
        async def yuho_library_list(
            include_marginal: bool = True,
            include_sso: bool = False,
            limit: int = 0,
            offset: int = 0,
        ) -> Dict[str, Any]:
            """
            List all encoded sections in the Penal Code library with coverage
            badges. Complements `yuho://library/index` for clients that prefer
            a structured tool response over markdown.

            Args:
                include_marginal: include the marginal note per section.
                include_sso: include the SSO deep-link URL per section.
                limit: max sections to return (0 = no cap).
                offset: skip this many sections (for pagination).

            Returns:
                {total, shown, sections: [{number, title, L1, L2, L3, path, sso_url?}]}
            """
            import json as _j
            repo = Path(__file__).parent.parent.parent.parent
            cov_path = repo / "library" / "penal_code" / "_coverage" / "coverage.json"
            if not cov_path.is_file():
                return mcp_error("not_found", "coverage.json missing — run scripts/coverage_report.py")
            cov = _j.loads(cov_path.read_text())
            rows = cov.get("sections", [])
            total = len(rows)
            sliced = rows[offset:(offset + limit) if limit else None]
            items: list[dict] = []
            for r in sliced:
                item: dict = {
                    "number": r.get("number", ""),
                    "L1": bool(r.get("L1")),
                    "L2": bool(r.get("L2")),
                    "L3": bool(r.get("L3")),
                    "encoded_path": r.get("encoded_path"),
                }
                if include_marginal:
                    item["marginal_note"] = r.get("marginal_note", "")
                if include_sso:
                    item["sso_url"] = r.get("sso_url", "")
                items.append(item)
            return {"total": total, "shown": len(items), "sections": items}

        @tool_with_structured_logging()
        async def yuho_grammar_example(primitive: str) -> Dict[str, Any]:
            """
            Return a worked example for a Yuho grammar primitive. Tool-form
            wrapper over the `yuho://examples/{primitive}` resource so clients
            that prefer tool-calls over resource reads get equal access.

            Known primitives: subsection, effective, fine_unlimited,
            caning_unspecified, penalty_or_both, penalty_when, nested_penalty,
            exception_priority, doc_comment_on_group, section_suffix,
            illustration, element_group.

            Args:
                primitive: name of the primitive.

            Returns:
                {primitive, example, known_primitives} — `example` is missing
                if the primitive is unknown.
            """
            # reuse the same map as the examples resource — duplicated for
            # callability, kept small so drift is tolerable.
            examples = {
                "subsection": "G5 — see `yuho://examples/subsection` for full example.",
                "effective": "G6 — see `yuho://examples/effective`.",
                "fine_unlimited": "G8 — see `yuho://examples/fine_unlimited`.",
                "caning_unspecified": "G14 — see `yuho://examples/caning_unspecified`.",
                "penalty_or_both": "G8 — see `yuho://examples/penalty_or_both`.",
                "penalty_when": "G9 — see `yuho://examples/penalty_when`.",
                "nested_penalty": "G12 — see `yuho://examples/nested_penalty`.",
                "exception_priority": "G13 — see `yuho://examples/exception_priority`.",
                "doc_comment_on_group": "G1 — see `yuho://examples/doc_comment_on_group`.",
                "section_suffix": "G3 — see `yuho://examples/section_suffix`.",
                "illustration": "Illustrations — see `yuho://examples/illustration`.",
                "element_group": "Elements — see `yuho://examples/element_group`.",
            }
            known = sorted(examples)
            if primitive not in examples:
                return mcp_error("invalid_argument", "unknown primitive",
                                 primitive=primitive, known_primitives=known)
            # resolve the actual body by calling the resource getter (we have
            # it in this scope under _register_resources; to keep things
            # decoupled we re-read the map from the examples resource body).
            return {"primitive": primitive, "pointer": examples[primitive],
                    "fetch_resource": f"yuho://examples/{primitive}",
                    "known_primitives": known}

        @tool_with_structured_logging()
        async def yuho_rate_limit_stats() -> Dict[str, Any]:
            """
            Get rate limiting statistics.

            Returns:
                Statistics about rate limiting including total requests,
                rate-limited requests, per-tool breakdown, and current token counts.
            """
            return self.rate_limiter.get_stats()

        # ----------------------------------------------------------------
        # G10 — cross-section reference graph
        # ----------------------------------------------------------------

        @tool_with_structured_logging()
        async def yuho_section_references(
            section: str,
            direction: str = "both",
            kind: Optional[str] = None,
            transitive: bool = False,
        ) -> Dict[str, Any]:
            """
            Walk the cross-section reference graph for a Penal Code section (G10).

            Returns the typed edges leaving and/or entering the section. Edge
            kinds are 'subsumes', 'amends', 'implicit'. Implicit edges are
            mentions like 's415' or 'Section 415' inside element descriptions,
            doc comments, or case-law holdings.

            Args:
                section: section number (e.g. '415', '376AA').
                direction: 'out', 'in', or 'both' (default).
                kind: optional filter ('subsumes' | 'amends' | 'implicit').
                transitive: follow edges transitively (BFS closure).

            Returns:
                {section, direction, outgoing?, incoming?} — outgoing/incoming
                are lists of edges or section numbers depending on `transitive`.
            """
            section = section.lstrip("sS").strip()
            kinds = [kind] if kind else None
            cache_key = ("yuho_section_references", section, direction, kind, transitive)
            cached = self.cache_get(cache_key)
            if cached is not None:
                return cached
            graph = self.get_reference_graph()
            if graph is None:
                return mcp_error(
                    "unavailable",
                    "Reference graph could not be built (is library/penal_code present?)",
                    section=section,
                )

            result: Dict[str, Any] = {"section": section, "direction": direction}
            if direction in ("out", "both"):
                if transitive:
                    result["outgoing"] = sorted(graph.reachable_from(section, kinds))
                else:
                    result["outgoing"] = [
                        {"dst": e.dst, "kind": e.kind, "snippet": e.snippet}
                        for e in graph.outgoing(section, kinds)
                    ]
            if direction in ("in", "both"):
                if transitive:
                    result["incoming"] = sorted(graph.reachable_to(section, kinds))
                else:
                    result["incoming"] = [
                        {"src": e.src, "kind": e.kind, "snippet": e.snippet}
                        for e in graph.incoming(section, kinds)
                    ]
            self.cache_put(cache_key, result, ttl=120.0)
            return result

        # ----------------------------------------------------------------
        # Simulator — fact-pattern → element-trace
        # ----------------------------------------------------------------

        @tool_with_structured_logging()
        async def yuho_simulate_fact_pattern(facts: Dict[str, Any]) -> Dict[str, Any]:
            """
            Run the Yuho fact-pattern simulator.

            Takes a structured fact pattern (see `simulator/schema.md`) and
            returns a per-element trace: which elements the facts satisfy,
            contradict, or leave unresolved. Does NOT predict case outcomes
            or provide legal advice; it is a structural trace over the
            encoded section's elements and exceptions.

            Args:
                facts: a dict matching the fact-pattern schema. Required keys:
                    `section` (the encoded section number),
                    optional: `name`, `acts`, `mental_states`, `circumstances`,
                    `outcomes`, `asserted_exceptions`, `fact_facts`.

            Returns:
                The simulator's structural trace with verdict, satisfied /
                contradicted / suggested / unresolved element lists, and
                exception-match info.
            """
            try:
                import sys
                from pathlib import Path
                sim_path = Path(__file__).resolve().parent.parent.parent.parent / "simulator"
                if str(sim_path) not in sys.path:
                    sys.path.insert(0, str(sim_path))
                import simulator as sim_mod  # type: ignore
                return sim_mod.evaluate(facts)
            except Exception as e:
                return mcp_error("unavailable", f"simulator could not be loaded: {e}")

        # ----------------------------------------------------------------
        # Grounded answer verifier
        # ----------------------------------------------------------------

        @tool_with_structured_logging()
        async def yuho_verify_grounded(answer: Dict[str, Any]) -> Dict[str, Any]:
            """
            Verify that every claim in a model answer is grounded in the
            encoded corpus.

            Takes a JSON answer document with explicit citations and checks
            each citation's span against the named artefact (`raw`, `yh`,
            or `english`). Reports orphan claims and spurious citations.

            See `scripts/verify_grounded.py` for the input schema.

            Args:
                answer: dict with optional `question`, `answer`, and a list
                    of `claims`, where each claim has `text` and `citations`.

            Returns:
                Verification report: per-claim results, spurious citation list,
                grounded fraction, verdict.
            """
            try:
                import sys
                from pathlib import Path
                root = Path(__file__).resolve().parent.parent.parent.parent
                scripts_path = root / "scripts"
                if str(scripts_path) not in sys.path:
                    sys.path.insert(0, str(scripts_path))
                import verify_grounded as vg  # type: ignore

                # Re-route the verifier's per-section loader through the
                # server's cache so multiple claims citing the same section
                # don't each re-read the section JSON from disk.
                if hasattr(vg, "_load_section"):
                    server_self = self
                    original_load = vg._load_section

                    def cached_load(section: str):
                        rec = server_self.get_corpus_section(section)
                        if rec is not None:
                            return rec
                        return original_load(section)
                    vg._load_section = cached_load
                    try:
                        return vg.verify_answer(answer)
                    finally:
                        vg._load_section = original_load
                return vg.verify_answer(answer)
            except Exception as e:
                return mcp_error("unavailable", f"verifier could not be loaded: {e}")

        # ----------------------------------------------------------------
        # Benchmark task fetcher
        # ----------------------------------------------------------------

        @tool_with_structured_logging()
        async def yuho_benchmark_task(
            task_type: str,
            n: int = 1,
            offset: int = 0,
        ) -> Dict[str, Any]:
            """
            Fetch tasks from the Yuho benchmark pack.

            Task types: 'citation_grounding', 'penalty_extraction',
            'element_classification', 'cross_reference', 'illustration_recognition'.

            Args:
                task_type: one of the five task types.
                n: number of tasks to return (default 1).
                offset: skip this many tasks before returning n.

            Returns:
                {task_type, n_total, n_returned, tasks: [...]}.
            """
            from pathlib import Path
            import json as _json

            valid_types = {
                "citation_grounding", "penalty_extraction", "element_classification",
                "cross_reference", "illustration_recognition",
            }
            if task_type not in valid_types:
                return mcp_error(
                    "invalid_argument",
                    f"unknown task_type {task_type!r}",
                    valid_types=sorted(valid_types),
                )

            path = Path("benchmarks/tasks") / f"{task_type}.jsonl"
            if not path.exists():
                return mcp_error(
                    "not_found",
                    "benchmark task file does not exist; run `python3 benchmarks/build_benchmarks.py`",
                    task_type=task_type,
                    expected_path=str(path),
                )

            tasks = []
            n_total = 0
            with path.open("r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    n_total += 1
                    if i < offset:
                        continue
                    if len(tasks) < n:
                        tasks.append(_json.loads(line))
            return {
                "task_type": task_type,
                "n_total": n_total,
                "n_returned": len(tasks),
                "tasks": tasks,
            }

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
                        except Exception as exc:
                            logger.warning(
                                "MCP resource yuho://library/{section} read failed: %s",
                                mask_error(exc),
                            )
            return f"// Statute {section} not found in library"

        @self.server.resource("yuho://grammar/summary")
        async def get_grammar_summary() -> str:
            """Condensed plain-English summary of the statute-level grammar
            primitives. Designed for AI clients — smaller + easier to reason
            about than the full 850-line tree-sitter grammar."""
            return """# Yuho grammar — statute-body primitives

Full grammar at `yuho://grammar`. Worked examples per primitive at
`yuho://examples/{primitive}`. Gap log at `yuho://gaps`.

## Top-level shape

```yh
/// @jurisdiction singapore
/// @meta act=Penal Code 1871
/// @meta source=https://sso.agc.gov.sg/Act/PC1871?ProvIds=prN-#prN-
/// @amendment [15/2019]

statute N "Title"
    effective 1872-01-01
    effective 2020-01-01          // G6: multiple effective dates allowed
{
    definitions   { ... }
    elements      { ... }
    penalty ...   { ... }
    illustration <label> { "..." }
    exception <label> { ... }
    subsection (N) { ... }        // G5: nested subsections
    caselaw ... { ... }
    parties { ... }
}
```

## `definitions`

Flat list of named term/string pairs.

```yh
definitions {
    deceive := "to cause a person to believe something that is false";
    fraudulently := "with intent to defraud another person";
}
```

## `elements` + `all_of` / `any_of`

Supports `actus_reus`, `mens_rea`, `circumstance`, plus deontic triple
`obligation` / `prohibition` / `permission`. Groups can nest; doc
comments (`///`) can precede groups (G1).

```yh
elements {
    /// conjunctive criteria for cheating
    all_of {
        actus_reus deception := "deceiving any person";
        any_of {
            mens_rea fraud := "fraudulently";
            mens_rea dish := "dishonestly";
        }
    }
}
```

Element-entry attributes: `caused_by <ident>`, `burden prosecution|defence [beyond_reasonable_doubt|balance_of_probabilities|prima_facie]`, `actor <ident>`, `patient <ident>`.

## `penalty` (G8 + G9 + G12 + G14)

Outer combinator: `cumulative` (default — all apply together), `alternative` (exactly one), `or_both` (any / both, the typical PC pattern). `when <ident>` branches penalties by named condition (G9). Nested combinator (G12): one level of sub-block for "imprisonment AND ALSO fine or caning" patterns.

```yh
// G8: the standard X years, or fine, or both
penalty or_both {
    imprisonment := 0 years .. 3 years;
    fine := unlimited;           // G8 sentinel — no numeric cap
}

// G9: conditional branches
penalty or_both when rash_act {
    imprisonment := 0 years .. 5 years;
    fine := unlimited;
}
penalty or_both when negligent_act {
    imprisonment := 0 years .. 2 years;
    fine := unlimited;
}

// G12 + G14: "imprisonment AND ALSO liable to fine or caning or both"
penalty cumulative {
    imprisonment := 0 years .. 10 years;
    or_both {
        fine := unlimited;
        caning := unspecified;   // G14 sentinel — liable to caning, no stroke count
    }
}
```

Penalty clause forms:
- `imprisonment := <duration>` or `<duration> .. <duration>`
- `fine := <money>` or `<money> .. <money>` or `unlimited`
- `caning := <int> strokes`, `<int> .. <int> strokes`, or `unspecified`
- `death := TRUE`
- `supplementary := "..."`
- `minimum imprisonment := <duration>` / `minimum fine := <money>`

## `exception` (G13 — prioritised)

```yh
exception grave_provocation {
    "Culpable homicide is not murder if the offender ..."
    when provoked_and_lost_control
    priority 1
    defeats <other_label>
}
```

Lower `priority` integer = higher precedence. `defeats <label>` explicit
override. Z3 encoder emits priority-aware firing (G13 semantic).

## `subsection` (G5)

Arbitrary-depth nesting of subsection blocks, accepting the same member
types as a statute.

```yh
statute 377BO "Child abuse material extraterritoriality" {
    subsection (1) { definitions { ... } elements { ... } }
    subsection (2) { definitions { ... } }
    subsection (3) { ... }
}
```

Subsection labels accept `(1)`, `(2A)`, `(a)`, `(iii)`, or bare numerics.

## Section suffix (G3)

Multi-letter suffixes on section numbers: `376AA`, `377BO`, `377CA`, etc.
Grammar accepts `[0-9]+[A-Za-z]*`.

## Value qualifiers (defeasible logic)

Variable declarations accept `fact`, `conclusion`, `presumed` qualifiers
and a trailing `unless <expr>` rebuttal clause.

## Legal-native types

`int`, `float`, `bool`, `string`, `money` (`$10,000.00`, `SGD1000`),
`percent` (`50%`), `date` (ISO-8601), `duration` (`3 years`, `6 months`,
combinations like `1 year .. 7 years`), `void`.

## Statute-level clauses

`subsumes <section>`, `amends <section>` — declare lifecycle
relationships. Doc comments `///` accept arbitrary text including colons.
"""

        @self.server.resource("yuho://library/index")
        async def get_library_index() -> str:
            """Full browseable library index with coverage badges + SSO links.

            Intended as the primary entry point for AI clients discovering
            Yuho's statute library. Rendered as a markdown table sorted by
            section number.
            """
            import json as _j, tomllib, re
            repo = Path(__file__).parent.parent.parent.parent
            cov_path = repo / "library" / "penal_code" / "_coverage" / "coverage.json"
            if not cov_path.is_file():
                return "# Library index\n\n_No coverage.json found; run scripts/coverage_report.py._\n"
            cov = _j.loads(cov_path.read_text())
            totals = cov.get("totals", {})
            header = (
                "# Yuho — Singapore Penal Code library\n\n"
                f"Coverage: raw={totals.get('raw_sections',0)} · "
                f"L1={totals.get('L1_pass',0)} · "
                f"L2={totals.get('L2_pass',0)} · "
                f"L3={totals.get('L3_pass',0)}\n\n"
                "| § | Marginal note | L1 | L2 | L3 | Verified | SSO |\n"
                "|---|---|:-:|:-:|:-:|---|---|\n"
            )
            lines = [header]
            def tick(b): return "✓" if b else "·"
            for r in cov.get("sections", []):
                n = r.get("number", "")
                if not n: continue
                ver = f"{r.get('L3_verified_on','')} {r.get('L3_verified_by','')}".strip() or "—"
                sso = f"[↗]({r['sso_url']})" if r.get("sso_url") else ""
                marginal = (r.get("marginal_note") or "")[:60]
                lines.append(
                    f"| s{n} | {marginal} | {tick(r.get('L1'))} | "
                    f"{tick(r.get('L2'))} | {tick(r.get('L3'))} | {ver} | {sso} |"
                )
            return "\n".join(lines) + "\n"

        @self.server.resource("yuho://raw/{section}")
        async def get_raw_canonical(section: str) -> str:
            """Return the canonical SSO text for a PC section (raw/act.json)."""
            import json as _j
            repo = Path(__file__).parent.parent.parent.parent
            raw_path = repo / "library" / "penal_code" / "_raw" / "act.json"
            if not raw_path.is_file():
                return f"// canonical act.json missing"
            raw = _j.loads(raw_path.read_text())
            for s in raw.get("sections", []):
                if s.get("number") == section:
                    out: list[str] = [
                        f"# s{section} — {s.get('marginal_note','')}",
                        "",
                        f"**SSO anchor:** `{s.get('anchor_id','')}`",
                        "",
                        "## Text",
                        "",
                        s.get("text", ""),
                    ]
                    if s.get("sub_items"):
                        out += ["", f"## Sub-items ({len(s['sub_items'])})", ""]
                        for it in s["sub_items"]:
                            out.append(f"- **[{it.get('kind','')}:{it.get('label','')}]** {it.get('text','')}")
                    if s.get("amendments"):
                        out += ["", f"## Amendments ({len(s['amendments'])})", ""]
                        for a in s["amendments"]:
                            out.append(f"- `{a.get('marker','')}`")
                    return "\n".join(out) + "\n"
            return f"// section {section} not in canonical corpus"

        @self.server.resource("yuho://examples/{primitive}")
        async def get_grammar_example(primitive: str) -> str:
            """Return a worked example for a named grammar primitive.

            Primitives covered: subsection, effective, fine_unlimited,
            caning_unspecified, penalty_or_both, penalty_when, nested_penalty,
            exception_priority, doc_comment_on_group, section_suffix,
            illustration, explanation, element_group.
            """
            examples = {
                "subsection": (
                    "G5 — subsection nesting (s377BO / s511 shape):\n\n"
                    "```yh\n"
                    "statute 511 \"Attempt to commit offence\" {\n"
                    "  subsection (1) {\n"
                    "    definitions { substantial_step := \"...\"; }\n"
                    "    elements { all_of { actus_reus a := \"takes a substantial step\"; } }\n"
                    "  }\n"
                    "  subsection (2) {\n"
                    "    definitions { factual_impossibility := \"...\"; }\n"
                    "  }\n"
                    "}\n"
                    "```\n"
                ),
                "effective": (
                    "G6 — multiple effective dates (amendment-introduced sections):\n\n"
                    "```yh\n"
                    "statute 377BO \"Child abuse material extraterritoriality\"\n"
                    "    effective 1872-01-01\n"
                    "    effective 2020-01-01\n"
                    "{ /* ... */ }\n"
                    "```\n"
                    "The first date is the act's original commencement, the second is the\n"
                    "amendment that introduced this specific section.\n"
                ),
                "fine_unlimited": (
                    "G8 — fine without a numeric cap (statute says \"with fine\" alone):\n\n"
                    "```yh\n"
                    "penalty or_both {\n"
                    "  imprisonment := 0 days .. 1 year;\n"
                    "  fine := unlimited;\n"
                    "}\n"
                    "```\n"
                    "NEVER invent a dollar cap. If the statute doesn't name one, use `unlimited`.\n"
                ),
                "caning_unspecified": (
                    "G14 — caning liability without stroke count (\"liable to caning\"):\n\n"
                    "```yh\n"
                    "penalty cumulative {\n"
                    "  imprisonment := 0 years .. 10 years;\n"
                    "  or_both {\n"
                    "    fine := unlimited;\n"
                    "    caning := unspecified;\n"
                    "  }\n"
                    "}\n"
                    "```\n"
                    "Never write `caning := 0 .. 0 strokes` or any invented range — that's\n"
                    "fabrication. `unspecified` encodes \"liable to caning, quantum set by\n"
                    "sentencing court.\"\n"
                ),
                "penalty_or_both": (
                    "G8 — typical SG PC penalty pattern: X years, or fine, or both:\n\n"
                    "```yh\n"
                    "penalty or_both {\n"
                    "  imprisonment := 0 years .. 3 years;\n"
                    "  fine := unlimited;\n"
                    "}\n"
                    "```\n"
                ),
                "penalty_when": (
                    "G9 — conditional penalty branches (s304A rash vs negligent):\n\n"
                    "```yh\n"
                    "penalty or_both when rash_act {\n"
                    "  imprisonment := 0 years .. 5 years;\n"
                    "  fine := unlimited;\n"
                    "}\n"
                    "penalty or_both when negligent_act {\n"
                    "  imprisonment := 0 years .. 2 years;\n"
                    "  fine := unlimited;\n"
                    "}\n"
                    "```\n"
                ),
                "nested_penalty": (
                    "G12 — nested combinator (\"imprisonment AND ALSO liable to fine or caning or both\"):\n\n"
                    "```yh\n"
                    "penalty cumulative {\n"
                    "  imprisonment := 0 years .. 10 years;\n"
                    "  or_both {\n"
                    "    fine := unlimited;\n"
                    "    caning := unspecified;\n"
                    "  }\n"
                    "}\n"
                    "```\n"
                    "Outer `cumulative` = imprisonment always applies. Inner `or_both` = fine\n"
                    "OR caning OR both, at sentencing court's discretion.\n"
                ),
                "exception_priority": (
                    "G13 — prioritised exceptions (Catala default-logic, s300 Murder shape):\n\n"
                    "```yh\n"
                    "exception grave_provocation {\n"
                    "  \"Culpable homicide is not murder if the offender ...\"\n"
                    "  when provoked_and_lost_control\n"
                    "  priority 1\n"
                    "}\n"
                    "exception self_defence_excess {\n"
                    "  \"...\"\n"
                    "  priority 2\n"
                    "  defeats grave_provocation\n"
                    "}\n"
                    "```\n"
                    "`defeats <label>` or lower `priority` integer = higher precedence.\n"
                    "Z3 encoder emits priority-aware firing so only the dominant exception\n"
                    "negates conviction when multiple guards are satisfied.\n"
                ),
                "doc_comment_on_group": (
                    "G1 — doc comments on all_of / any_of groups:\n\n"
                    "```yh\n"
                    "elements {\n"
                    "  /// conjunctive criteria for cheating\n"
                    "  all_of {\n"
                    "    actus_reus deception := \"deceiving any person\";\n"
                    "    /// alternative mens rea branches — fraudulent OR dishonest\n"
                    "    any_of {\n"
                    "      mens_rea fraud := \"fraudulently\";\n"
                    "      mens_rea dish := \"dishonestly\";\n"
                    "    }\n"
                    "  }\n"
                    "}\n"
                    "```\n"
                ),
                "section_suffix": (
                    "G3 — multi-letter section suffix (376AA, 377BO, 377CA …):\n\n"
                    "```yh\n"
                    "statute 376AA \"Exploitative sexual penetration of minor ...\"\n"
                    "    effective 1872-01-01\n"
                    "    effective 2020-01-01\n"
                    "{ /* ... */ }\n"
                    "```\n"
                    "Direct — no decimal workaround. Grammar accepts `[0-9]+[A-Za-z]*`.\n"
                ),
                "illustration": (
                    "Illustrations — preserve verbatim from canonical text:\n\n"
                    "```yh\n"
                    "illustration illustration_a {\n"
                    "  \"( a ) A shoots Z with the intention of killing him. Z dies in consequence. A commits murder.\"\n"
                    "}\n"
                    "```\n"
                    "Quote text verbatim from `_raw/act.json`. Never paraphrase.\n"
                ),
                "element_group": (
                    "Elements — offence shape (actus reus + mens rea + circumstance):\n\n"
                    "```yh\n"
                    "elements {\n"
                    "  all_of {\n"
                    "    actus_reus doing_act := \"does any act\";\n"
                    "    mens_rea intent := \"with intent to …\" caused_by doing_act;\n"
                    "    circumstance harm_caused := \"causes harm\";\n"
                    "  }\n"
                    "}\n"
                    "```\n"
                ),
            }
            if primitive in examples: return examples[primitive]
            keys = ", ".join(sorted(examples))
            return f"// no example for primitive '{primitive}'. Known primitives: {keys}\n"

        @self.server.resource("yuho://prompts/phase-d-reencoding")
        async def get_phase_d_reencoding_prompt() -> str:
            """Strict re-encoding prompt used during Phase D."""
            p = Path(__file__).parent.parent.parent.parent / "doc" / "PHASE_D_REENCODING_PROMPT.md"
            return p.read_text() if p.exists() else "// Phase D re-encoding prompt not found"

        @self.server.resource("yuho://prompts/phase-d-l3-review")
        async def get_phase_d_l3_prompt() -> str:
            """11-point L3 audit checklist used by the automated reviewer."""
            p = Path(__file__).parent.parent.parent.parent / "doc" / "PHASE_D_L3_REVIEW_PROMPT.md"
            return p.read_text() if p.exists() else "// Phase D L3 review prompt not found"

        @self.server.resource("yuho://prompts/phase-d-flag-fix")
        async def get_phase_d_flag_fix_prompt() -> str:
            """Minimum-edit flag-fix prompt used to patch flagged sections."""
            p = Path(__file__).parent.parent.parent.parent / "doc" / "PHASE_D_FLAG_FIX_PROMPT.md"
            return p.read_text() if p.exists() else "// Phase D flag-fix prompt not found"

        @self.server.resource("yuho://coverage")
        async def get_coverage() -> str:
            """Current L1/L2/L3 coverage dashboard (coverage.json)."""
            p = Path(__file__).parent.parent.parent.parent / "library" / "penal_code" / "_coverage" / "coverage.json"
            return p.read_text() if p.exists() else "{\"error\": \"coverage.json missing\"}"

        @self.server.resource("yuho://flags")
        async def get_flags() -> str:
            """Aggregated list of currently flagged sections awaiting human review."""
            p = Path(__file__).parent.parent.parent.parent / "library" / "penal_code" / "_L3_flags.md"
            return p.read_text() if p.exists() else "# No flags currently open\n"

        @self.server.resource("yuho://gaps")
        async def get_gaps() -> str:
            """The Phase C/D grammar gap log (G1-G14)."""
            p = Path(__file__).parent.parent.parent.parent / "doc" / "PHASE_C_GAPS.md"
            return p.read_text() if p.exists() else "// Gap log not found"

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
            return docs.get(
                topic.lower(),
                f"# Topic '{topic}' not found\n\nAvailable topics: {', '.join(docs.keys())}",
            )

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

        @self.server.prompt("find_fidelity_issues")
        async def find_fidelity_issues_prompt(section: str) -> str:
            """Prompt for auditing an encoded section against canonical SSO text.

            Expects the client to pair this with a `yuho_section_pair` call so
            both sides are on the table.
            """
            return f"""You are auditing the encoded Yuho file for Singapore Penal Code 1871 section {section} against the canonical statute text.

Do these in order:
1. Call the `yuho_section_pair` tool with section="{section}". That returns canonical (raw SSO text + sub_items + amendments) alongside the encoded .yh source.
2. Walk the 11-point fidelity checklist at `yuho://prompts/phase-d-l3-review`: section number match, marginal note verbatim, all canonical illustrations present, explanations preserved, exceptions preserved, subsections not flattened, no fabricated penalty values (no invented fine caps, no invented caning strokes, no penalty on definition-only sections), all_of vs any_of matches English connectives, effective date sane, no placeholder text, yuho check still passes.
3. For each item that fails, report: (a) what canonical says vs what the encoding says; (b) which of the existing grammar primitives (G1-G14 — see `yuho://gaps`) should fix it; (c) the minimum edit needed.

If every item passes, report "STAMP candidate" and recommend the L3 metadata stamp."""

        @self.server.prompt("recommend_l3")
        async def recommend_l3_prompt(section: str) -> str:
            """Prompt for a quick STAMP/FLAG decision with concise reasoning."""
            return f"""Decide whether Singapore Penal Code 1871 section {section} should be L3-stamped now.

Use these tools in order:
1. `yuho_section_pair` with section="{section}" — get canonical + encoded side by side.
2. `yuho_check_encoding` (if available) or read the encoded source to confirm it parses.
3. Spot-check: illustration count match, no fabricated fine/caning values, subsections present if canonical has them, all_of/any_of matches English.

Respond in at most 6 lines:
```
decision: STAMP | FLAG
checklist: <which of the 11 points fail, if any>
edit_if_flagged: <one-sentence minimum fix>
confidence: high | medium | low
```

Do not rewrite the encoding. If you'd stamp, just say so — the human will actually set metadata.toml."""

        @self.server.prompt("encode_new_section")
        async def encode_new_section_prompt(section: str) -> str:
            """Prompt for encoding a fresh, unencoded PC section from canonical text."""
            # use plain concat, not an f-string — the prompt body contains
            # literal `{` / `}` braces from Yuho syntax examples that would
            # otherwise be interpreted as f-string placeholders.
            return (
                "You are encoding Singapore Penal Code 1871 section "
                + section
                + " into Yuho from scratch.\n\n"
                "Do these:\n"
                '1. Call `yuho_propose_encoding_skeleton` with section="'
                + section
                + '" to get the boilerplate header, the right directory slug, and canonical excerpt as a reference comment.\n'
                "2. Read `yuho://prompts/phase-d-reencoding` for the strict encoding rules — no fabricated fine caps, illustration preservation, use of new grammar primitives (G1-G14), etc.\n"
                "3. Read `yuho://grammar` for exact syntax.\n"
                "4. Fill the skeleton. Every claim must be supported by the canonical text returned by `yuho_section_pair` — if something isn't in canonical, don't invent it.\n"
                "5. Call `yuho_check` to verify the encoding parses + type-checks. Iterate until it passes.\n\n"
                "Grammar primitives you may need: `subsection (N) { ... }`, `effective <date>` (multiple allowed), `fine := unlimited`, `caning := unspecified`, `penalty or_both / alternative / cumulative`, `penalty when <ident>`, nested combinators (`penalty cumulative { imprisonment; or_both { fine; caning } }`), `exception { priority N defeats <label> }`.\n\n"
                "Report the final .yh + metadata.toml contents in fenced code blocks keyed by the target file path (e.g. `library/penal_code/s"
                + section
                + "_<slug>/statute.yh`)."
            )

    def health_check(self) -> Dict[str, Any]:
        """Return server health status."""
        return {
            "status": "healthy",
            "name": "yuho-mcp",
            "version": __version__,
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
        # FastMCP uses SSE transport for HTTP.
        run_kwargs: Dict[str, Any] = {"transport": "sse"}
        auth_token = get_config().mcp.auth_token

        try:
            import inspect

            run_signature = inspect.signature(self.server.run)
            if "host" in run_signature.parameters:
                run_kwargs["host"] = host
            if "port" in run_signature.parameters:
                run_kwargs["port"] = port
            if auth_token:
                if "auth_token" in run_signature.parameters:
                    run_kwargs["auth_token"] = auth_token
                elif "token" in run_signature.parameters:
                    run_kwargs["token"] = auth_token
                elif "bearer_token" in run_signature.parameters:
                    run_kwargs["bearer_token"] = auth_token
                elif "headers" in run_signature.parameters:
                    run_kwargs["headers"] = {"Authorization": f"Bearer {auth_token}"}
                else:
                    raise RuntimeError(
                        "mcp.auth_token is set but FastMCP.run() has no supported auth option; refusing insecure HTTP startup."
                    )
        except (ValueError, TypeError):
            # Fallback to transport-only call if signature introspection fails.
            if auth_token:
                raise RuntimeError(
                    "mcp.auth_token is set but FastMCP.run() signature could not be inspected; refusing insecure HTTP startup."
                )

        self.server.run(**run_kwargs)


def create_server() -> YuhoMCPServer:
    """Create and return a YuhoMCPServer instance."""
    return YuhoMCPServer()
