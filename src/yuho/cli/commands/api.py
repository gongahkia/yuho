"""
API server command - HTTP REST API for Yuho operations.

Provides a lightweight HTTP API for:
- Parsing and validating Yuho source code
- Transpiling to various formats
- Running lint checks
- Health checks
"""

import sys
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

import click

from yuho import __version__
from yuho.parser import get_parser
from yuho.ast import ASTBuilder
from yuho.transpile.base import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry
from yuho.cli.error_formatter import Colors, colorize
from yuho.cli.commands.check import get_error_explanation
from yuho.logging_utils import RequestLogContext, finish_request, start_request
from yuho.services.analysis import analyze_source
from yuho.services.errors import (
    ASTBoundaryError,
    ParserBoundaryError,
    TranspileBoundaryError,
    run_ast_boundary,
    run_parser_boundary,
    run_transpile_boundary,
)

logger = logging.getLogger("yuho.api")
MAX_REQUEST_BODY_BYTES = 1_048_576


class RequestBodyTooLargeError(Exception):
    """Raised when an API request body exceeds the configured limit."""


@dataclass
class APIResponse:
    """Standard API response structure."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)


class YuhoAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Yuho API."""
    
    # Class-level parser and registry (shared across requests)
    parser = get_parser()
    registry = TranspilerRegistry.instance()
    _request_context: Optional[RequestLogContext] = None
    _request_method: str = ""
    _request_path: str = ""

    def _start_request_log(self, method: str, path: str) -> None:
        """Start request logging context for this HTTP request."""
        request_id = self.headers.get("X-Request-ID")
        client_ip = self.client_address[0] if self.client_address else None
        self._request_method = method
        self._request_path = path
        self._request_context = start_request(
            logger,
            "api.request.start",
            request_id=request_id,
            method=method,
            path=path,
            client_ip=client_ip,
        )

    def _finish_request_log(self, status_code: int, success: bool) -> None:
        """Finish request logging context with status metadata."""
        if self._request_context is None:
            return

        finish_request(
            logger,
            self._request_context,
            "api.request.complete",
            status="success" if success else "error",
            method=self._request_method or self.command,
            path=self._request_path or self.path,
            status_code=status_code,
            success=success,
        )
        self._request_context = None
    
    def _send_json_response(self, status: int, response: APIResponse) -> None:
        """Send a JSON response."""
        body = response.to_json().encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        if self._request_context is not None:
            self.send_header('X-Request-ID', self._request_context.request_id)
        self.end_headers()
        self.wfile.write(body)
        self._finish_request_log(status, response.success)

    def _validate_post_payload(self, path: str, data: Dict[str, Any]) -> Optional[str]:
        """Validate endpoint payload shape before execution."""
        if path == '/parse':
            if not isinstance(data.get('source', ''), str):
                return "'source' must be a string"
            if 'filename' in data and not isinstance(data['filename'], str):
                return "'filename' must be a string"
            return None

        if path == '/validate':
            if not isinstance(data.get('source', ''), str):
                return "'source' must be a string"
            if 'filename' in data and not isinstance(data['filename'], str):
                return "'filename' must be a string"
            if 'include_metrics' in data and not isinstance(data['include_metrics'], bool):
                return "'include_metrics' must be a boolean"
            if 'explain_errors' in data and not isinstance(data['explain_errors'], bool):
                return "'explain_errors' must be a boolean"
            return None

        if path == '/transpile':
            if not isinstance(data.get('source', ''), str):
                return "'source' must be a string"
            if 'target' in data and not isinstance(data['target'], str):
                return "'target' must be a string"
            if 'filename' in data and not isinstance(data['filename'], str):
                return "'filename' must be a string"
            return None

        if path == '/lint':
            if not isinstance(data.get('source', ''), str):
                return "'source' must be a string"
            if 'filename' in data and not isinstance(data['filename'], str):
                return "'filename' must be a string"
            if 'rules' in data:
                rules = data['rules']
                if not isinstance(rules, list) or any(not isinstance(r, str) for r in rules):
                    return "'rules' must be a list of strings"
            return None

        return None
    
    def _read_body(self) -> bytes:
        """Read request body."""
        content_length_header = self.headers.get('Content-Length', '0')
        try:
            content_length = int(content_length_header)
        except ValueError as exc:
            raise ValueError("Invalid Content-Length header") from exc

        if content_length < 0:
            raise ValueError("Invalid Content-Length header")
        if content_length > MAX_REQUEST_BODY_BYTES:
            raise RequestBodyTooLargeError(
                f"Request body too large (max {MAX_REQUEST_BODY_BYTES} bytes)"
            )

        return self.rfile.read(content_length)
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        self._start_request_log("OPTIONS", path)

        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self._finish_request_log(204, True)
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        self._start_request_log("GET", path)
        
        if path == '/health' or path == '/':
            self._handle_health()
        elif path == '/targets':
            self._handle_targets()
        elif path == '/rules':
            self._handle_rules()
        else:
            self._send_json_response(404, APIResponse(
                success=False,
                error=f"Not found: {path}"
            ))
    
    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        self._start_request_log("POST", path)
        
        try:
            body = self._read_body()
            data = json.loads(body) if body else {}
        except RequestBodyTooLargeError as e:
            self._send_json_response(413, APIResponse(
                success=False,
                error=str(e)
            ))
            return
        except json.JSONDecodeError as e:
            self._send_json_response(400, APIResponse(
                success=False,
                error=f"Invalid JSON: {e}"
            ))
            return
        except ValueError as e:
            self._send_json_response(400, APIResponse(
                success=False,
                error=str(e)
            ))
            return

        schema_error = self._validate_post_payload(path, data)
        if schema_error:
            self._send_json_response(400, APIResponse(
                success=False,
                error=f"Invalid payload: {schema_error}"
            ))
            return
        
        if path == '/parse':
            self._handle_parse(data)
        elif path == '/validate':
            self._handle_validate(data)
        elif path == '/transpile':
            self._handle_transpile(data)
        elif path == '/lint':
            self._handle_lint(data)
        else:
            self._send_json_response(404, APIResponse(
                success=False,
                error=f"Not found: {path}"
            ))
    
    def _handle_health(self) -> None:
        """Health check endpoint."""
        self._send_json_response(200, APIResponse(
            success=True,
            data={
                "status": "healthy",
                "version": __version__,
                "endpoints": [
                    "GET /health",
                    "GET /targets",
                    "GET /rules",
                    "POST /parse",
                    "POST /validate",
                    "POST /transpile",
                    "POST /lint",
                ]
            }
        ))
    
    def _handle_targets(self) -> None:
        """List available transpile targets."""
        targets = [
            {
                "name": t.name.lower(),
                "extension": t.file_extension,
            }
            for t in TranspileTarget
        ]
        self._send_json_response(200, APIResponse(
            success=True,
            data={"targets": targets}
        ))
    
    def _handle_rules(self) -> None:
        """List available lint rules."""
        from yuho.cli.commands.lint import ALL_RULES
        rules = [
            {
                "id": r.id,
                "severity": r.severity.name.lower(),
                "description": r.description,
            }
            for r in ALL_RULES
        ]
        self._send_json_response(200, APIResponse(
            success=True,
            data={"rules": rules}
        ))
    
    def _handle_parse(self, data: Dict[str, Any]) -> None:
        """Parse Yuho source code."""
        source = data.get('source', '')
        filename = data.get('filename', '<api>')
        
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        
        analysis = analyze_source(source, file=filename, run_semantic=False)

        if analysis.parse_errors:
            errors = [
                {
                    "message": e.message,
                    "line": e.location.line if e.location else None,
                    "column": e.location.col if e.location else None,
                }
                for e in analysis.parse_errors
            ]
            self._send_json_response(200, APIResponse(
                success=False,
                data={"errors": errors}
            ))
            return

        if analysis.errors and not analysis.parse_errors:
            self._send_json_response(500, APIResponse(
                success=False,
                error=analysis.errors[0].message
            ))
            return

        ast = analysis.ast
        summary = analysis.ast_summary
        if ast is None or summary is None:
            self._send_json_response(500, APIResponse(
                success=False,
                error="AST build error: Unknown error"
            ))
            return

        # Return AST summary
        self._send_json_response(200, APIResponse(
            success=True,
            data={
                "statutes": summary.statutes,
                "types": summary.structs,
                "functions": summary.functions,
                "imports": summary.imports,
                "statute_sections": [s.section_number for s in ast.statutes],
            }
        ))
    
    def _handle_validate(self, data: Dict[str, Any]) -> None:
        """Validate Yuho source code."""
        source = data.get('source', '')
        filename = data.get('filename', '<api>')
        include_metrics = bool(data.get('include_metrics', False))
        explain_errors = bool(data.get('explain_errors', False))
        
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        
        errors = []
        analysis = analyze_source(source, file=filename, run_semantic=False)

        if analysis.parse_errors:
            errors = [
                {
                    "type": "parse",
                    "message": e.message,
                    "line": e.location.line if e.location else None,
                    "column": e.location.col if e.location else None,
                    "node_type": e.node_type,
                    "explanation": (
                        get_error_explanation(e.message, e.node_type) if explain_errors else None
                    ),
                }
                for e in analysis.parse_errors
            ]

        if analysis.errors and not analysis.parse_errors:
            errors.extend(
                {
                    "type": error.stage,
                    "message": error.message,
                    "line": error.location.line if error.location else None,
                    "column": error.location.col if error.location else None,
                }
                for error in analysis.errors
            )
        
        response_data: Dict[str, Any] = {
            "valid": len(errors) == 0,
            "errors": errors,
        }
        if include_metrics:
            response_data["code_scale"] = (
                analysis.code_scale.to_dict() if analysis.code_scale else None
            )
            response_data["clock_load_scale"] = (
                analysis.clock_load_scale.to_dict() if analysis.clock_load_scale else None
            )

        self._send_json_response(200, APIResponse(
            success=len(errors) == 0,
            data=response_data
        ))
    
    def _handle_transpile(self, data: Dict[str, Any]) -> None:
        """Transpile Yuho source code."""
        source = data.get('source', '')
        target_name = data.get('target', 'json')
        filename = data.get('filename', '<api>')
        
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        
        # Parse
        try:
            result = run_parser_boundary(
                self.parser.parse,
                source,
                filename,
                message="Failed to parse source",
            )
        except ParserBoundaryError as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=str(e)
            ))
            return
        
        if result.errors:
            errors = [{"message": e.message} for e in result.errors]
            self._send_json_response(200, APIResponse(
                success=False,
                data={"errors": errors}
            ))
            return
        
        # Build AST
        try:
            builder = ASTBuilder(source, filename)
            ast = run_ast_boundary(
                builder.build,
                result.tree.root_node,
                message="Failed to build AST",
            )
        except ASTBoundaryError as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=str(e)
            ))
            return

        # Transpile
        try:
            target = TranspileTarget.from_string(target_name)
            transpiler = self.registry.get(target)
            output = run_transpile_boundary(
                transpiler.transpile,
                ast,
                message="Transpilation failed",
            )
            
            self._send_json_response(200, APIResponse(
                success=True,
                data={
                    "target": target.name.lower(),
                    "output": output,
                }
            ))
        except ValueError as e:
            self._send_json_response(400, APIResponse(
                success=False,
                error=f"Invalid target: {target_name}"
            ))
        except TranspileBoundaryError as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=str(e)
            ))
    
    def _handle_lint(self, data: Dict[str, Any]) -> None:
        """Run lint checks on Yuho source code."""
        source = data.get('source', '')
        rules = data.get('rules', None)  # Optional rule filter
        filename = data.get('filename', '<api>')
        
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        
        # Parse
        try:
            result = run_parser_boundary(
                self.parser.parse,
                source,
                filename,
                message="Failed to parse source",
            )
        except ParserBoundaryError as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=str(e)
            ))
            return
        
        if result.errors:
            errors = [{"message": e.message} for e in result.errors]
            self._send_json_response(200, APIResponse(
                success=False,
                data={"parse_errors": errors}
            ))
            return
        
        # Build AST
        try:
            builder = ASTBuilder(source, filename)
            ast = run_ast_boundary(
                builder.build,
                result.tree.root_node,
                message="Failed to build AST",
            )
        except ASTBoundaryError as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=str(e)
            ))
            return

        # Run lint
        from yuho.cli.commands.lint import ALL_RULES, Severity
        
        active_rules = ALL_RULES
        if rules:
            active_rules = [r for r in ALL_RULES if r.id in rules]
        
        all_issues = []
        for rule in active_rules:
            issues = rule.check(ast, source)
            for issue in issues:
                all_issues.append({
                    "rule": issue.rule,
                    "severity": issue.severity.name.lower(),
                    "message": issue.message,
                    "line": issue.line,
                    "suggestion": issue.suggestion,
                })
        
        self._send_json_response(200, APIResponse(
            success=True,
            data={
                "issues": all_issues,
                "summary": {
                    "errors": len([i for i in all_issues if i["severity"] == "error"]),
                    "warnings": len([i for i in all_issues if i["severity"] == "warning"]),
                    "infos": len([i for i in all_issues if i["severity"] == "info"]),
                    "hints": len([i for i in all_issues if i["severity"] == "hint"]),
                }
            }
        ))
    
    def log_message(self, format: str, *args) -> None:
        """Override to use our logging."""
        if hasattr(self.server, 'verbose') and self.server.verbose:
            message = format % args
            click.echo(f"[API] {self.address_string()} - {message}")


class YuhoAPIServer(ThreadingHTTPServer):
    """Custom HTTP server with additional configuration."""
    
    def __init__(self, server_address, RequestHandlerClass, verbose: bool = False):
        super().__init__(server_address, RequestHandlerClass)
        self.verbose = verbose


def run_api(
    host: Optional[str] = None,
    port: Optional[int] = None,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Start the Yuho API server.
    
    Args:
        host: Host to bind to (defaults to config mcp.host)
        port: Port to listen on (defaults to config mcp.port)
        verbose: Enable verbose output
        color: Use colored output
    """
    from yuho.config.loader import get_config

    mcp_config = get_config().mcp
    resolved_host = host or mcp_config.host
    resolved_port = port if port is not None else mcp_config.port

    server_address = (resolved_host, resolved_port)
    
    try:
        httpd = YuhoAPIServer(server_address, YuhoAPIHandler, verbose=verbose)
    except OSError as e:
        click.echo(colorize(f"error: Could not start server: {e}", Colors.RED), err=True)
        sys.exit(1)
    
    url = f"http://{resolved_host}:{resolved_port}"
    click.echo(f"Starting Yuho API server at {colorize(url, Colors.CYAN) if color else url}")
    click.echo("Endpoints:")
    click.echo("  GET  /health    - Health check")
    click.echo("  GET  /targets   - List transpile targets")
    click.echo("  GET  /rules     - List lint rules")
    click.echo("  POST /parse     - Parse Yuho source")
    click.echo("  POST /validate  - Validate Yuho source")
    click.echo("  POST /transpile - Transpile to target format")
    click.echo("  POST /lint      - Run lint checks")
    click.echo("")
    click.echo("Press Ctrl+C to stop")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
        httpd.shutdown()
