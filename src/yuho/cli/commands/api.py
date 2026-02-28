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
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

import click

from yuho.parser import Parser
from yuho.ast import ASTBuilder
from yuho.transpile.base import TranspileTarget
from yuho.transpile.registry import TranspilerRegistry
from yuho.cli.error_formatter import Colors, colorize
from yuho.cli.commands.check import get_error_explanation
from yuho.services.analysis import analyze_source


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
    parser = Parser()
    registry = TranspilerRegistry.instance()
    
    def _send_json_response(self, status: int, response: APIResponse) -> None:
        """Send a JSON response."""
        body = response.to_json().encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)
    
    def _read_body(self) -> bytes:
        """Read request body."""
        content_length = int(self.headers.get('Content-Length', 0))
        return self.rfile.read(content_length)
    
    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        
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
        
        try:
            body = self._read_body()
            data = json.loads(body) if body else {}
        except json.JSONDecodeError as e:
            self._send_json_response(400, APIResponse(
                success=False,
                error=f"Invalid JSON: {e}"
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
                "version": "5.0.0",
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
        result = self.parser.parse(source, filename)
        
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
            ast = builder.build(result.tree.root_node)
        except Exception as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=f"AST build error: {e}"
            ))
            return

        # Transpile
        try:
            target = TranspileTarget.from_string(target_name)
            transpiler = self.registry.get(target)
            output = transpiler.transpile(ast)
            
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
        except Exception as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=f"Transpilation error: {e}"
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
        result = self.parser.parse(source, filename)
        
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
            ast = builder.build(result.tree.root_node)
        except Exception as e:
            self._send_json_response(500, APIResponse(
                success=False,
                error=f"AST build error: {e}"
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


class YuhoAPIServer(HTTPServer):
    """Custom HTTP server with additional configuration."""
    
    def __init__(self, server_address, RequestHandlerClass, verbose: bool = False):
        super().__init__(server_address, RequestHandlerClass)
        self.verbose = verbose


def run_api(
    host: str = "127.0.0.1",
    port: int = 8080,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """
    Start the Yuho API server.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        verbose: Enable verbose output
        color: Use colored output
    """
    server_address = (host, port)
    
    try:
        httpd = YuhoAPIServer(server_address, YuhoAPIHandler, verbose=verbose)
    except OSError as e:
        click.echo(colorize(f"error: Could not start server: {e}", Colors.RED), err=True)
        sys.exit(1)
    
    url = f"http://{host}:{port}"
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
