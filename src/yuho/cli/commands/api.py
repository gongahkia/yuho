"""
API server command - HTTP REST API for Yuho operations.

Provides a lightweight HTTP API for:
- Parsing and validating Yuho source code
- Transpiling to various formats
- Running lint checks
- Health checks
- Metrics (Prometheus)
"""

import sys
import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
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
from yuho.parser.wrapper import MAX_SOURCE_LENGTH
from yuho.services.analysis import analyze_source
from yuho.services.errors import (
    ASTBoundaryError,
    ParserBoundaryError,
    TranspileBoundaryError,
    run_ast_boundary,
    run_parser_boundary,
    run_transpile_boundary,
)
from yuho.middleware.auth import get_auth_token, verify_bearer_token, SKIP_AUTH_PATHS
from yuho.middleware.rate_limit import RateLimiter, RateLimitConfig, RateLimitExceeded
from yuho.middleware.metrics import get_metrics
from yuho.api.jobs import get_job_queue, Job, JobStatus
from yuho.api.sse import stream_job_events

logger = logging.getLogger("yuho.api")
MAX_REQUEST_BODY_BYTES = 1_048_576
API_VERSION = "v1"


class RequestBodyTooLargeError(Exception):
    """Raised when an API request body exceeds the configured limit."""


@dataclass
class APIError:
    """Structured API error."""
    code: str
    message: str
    details: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class APIResponse:
    """Standard API response structure."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Any] = None

    def to_json(self) -> str:
        result: Dict[str, Any] = {"success": self.success}
        if self.data is not None:
            result["data"] = self.data
        if self.error is not None:
            if isinstance(self.error, APIError):
                result["error"] = asdict(self.error)
            else:
                result["error"] = {"code": "UNKNOWN", "message": str(self.error)}
        return json.dumps(result, indent=2)


def _strip_version_prefix(path: str) -> str:
    """Strip /v1 prefix from path for routing."""
    if path.startswith(f"/{API_VERSION}/"):
        return path[len(f"/{API_VERSION}"):]
    return path


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
    
    def _get_cors_origin(self) -> str:
        """Get configured CORS origin."""
        if hasattr(self.server, 'cors_origins'):
            origins = self.server.cors_origins
            if origins and origins != ["*"]:
                req_origin = self.headers.get("Origin", "")
                if req_origin in origins:
                    return req_origin
                return origins[0]
        return "*"

    def _send_json_response(self, status: int, response: APIResponse) -> None:
        """Send a JSON response."""
        body = response.to_json().encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', self._get_cors_origin())
        self.send_header('X-API-Version', API_VERSION)
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
    
    def _check_auth(self, path: str) -> bool:
        """Check auth. Returns True if OK, sends 401 and returns False if not."""
        if path in SKIP_AUTH_PATHS:
            return True
        token = getattr(self.server, 'auth_token', None)
        if not verify_bearer_token(self.headers.get("Authorization"), token):
            self._send_json_response(401, APIResponse(
                success=False,
                error=APIError(code="UNAUTHORIZED", message="Missing or invalid Authorization header")
            ))
            return False
        return True

    def _check_rate_limit(self, path: str) -> bool:
        """Check rate limit. Returns True if OK."""
        limiter = getattr(self.server, 'rate_limiter', None)
        if not limiter:
            return True
        try:
            client_ip = self.client_address[0] if self.client_address else None
            limiter.check(path, client_id=client_ip)
            return True
        except RateLimitExceeded as e:
            self.send_response(429)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Retry-After', str(int(e.retry_after) + 1))
            body = APIResponse(success=False, error=APIError(code="RATE_LIMITED", message=str(e))).to_json().encode()
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            self._finish_request_log(429, False)
            return False

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        parsed = urlparse(self.path)
        path = parsed.path
        self._start_request_log("OPTIONS", path)
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', self._get_cors_origin())
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Request-ID')
        self.end_headers()
        self._finish_request_log(204, True)

    def do_GET(self) -> None:
        """Handle GET requests."""
        parsed = urlparse(self.path)
        raw_path = parsed.path
        path = _strip_version_prefix(raw_path)
        self._start_request_log("GET", path)
        metrics = get_metrics()
        metrics.inc_active()
        t0 = time.monotonic()
        try:
            if not self._check_auth(path):
                return
            if not self._check_rate_limit(path):
                return
            if path == '/health' or path == '/':
                self._handle_health()
            elif path == '/targets':
                self._handle_targets()
            elif path == '/rules':
                self._handle_rules()
            elif path == '/metrics':
                self._handle_metrics()
            elif path == '/docs':
                self._handle_docs()
            elif path.startswith('/jobs/') and path.endswith('/stream'):
                job_id = path.split('/')[2]
                self._handle_job_stream(job_id)
            elif path.startswith('/jobs/'):
                job_id = path.split('/')[2]
                self._handle_job_status(job_id)
            else:
                self._send_json_response(404, APIResponse(
                    success=False,
                    error=APIError(code="NOT_FOUND", message=f"Not found: {raw_path}")
                ))
        finally:
            metrics.dec_active()
            metrics.record_request(path, 200, time.monotonic() - t0)

    def do_POST(self) -> None:
        """Handle POST requests."""
        parsed = urlparse(self.path)
        raw_path = parsed.path
        path = _strip_version_prefix(raw_path)
        self._start_request_log("POST", path)
        metrics = get_metrics()
        metrics.inc_active()
        t0 = time.monotonic()
        try:
            if not self._check_auth(path):
                return
            if not self._check_rate_limit(path):
                return
            content_type = self.headers.get('Content-Type', '')
            if content_type and 'application/json' not in content_type:
                self._send_json_response(415, APIResponse(
                    success=False,
                    error=APIError(code="UNSUPPORTED_MEDIA", message="Content-Type must be application/json")
                ))
                return
            try:
                body = self._read_body()
                data = json.loads(body) if body else {}
            except RequestBodyTooLargeError as e:
                self._send_json_response(413, APIResponse(
                    success=False,
                    error=APIError(code="PAYLOAD_TOO_LARGE", message=str(e))
                ))
                return
            except json.JSONDecodeError as e:
                self._send_json_response(400, APIResponse(
                    success=False,
                    error=APIError(code="INVALID_JSON", message=f"Invalid JSON: {e}")
                ))
                return
            except ValueError as e:
                self._send_json_response(400, APIResponse(
                    success=False,
                    error=APIError(code="BAD_REQUEST", message=str(e))
                ))
                return
            schema_error = self._validate_post_payload(path, data)
            if schema_error:
                self._send_json_response(400, APIResponse(
                    success=False,
                    error=APIError(code="VALIDATION_ERROR", message=f"Invalid payload: {schema_error}")
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
            elif path == '/jobs/submit':
                self._handle_job_submit(data)
            else:
                self._send_json_response(404, APIResponse(
                    success=False,
                    error=APIError(code="NOT_FOUND", message=f"Not found: {raw_path}")
                ))
        finally:
            metrics.dec_active()
            metrics.record_request(path, 200, time.monotonic() - t0)
    
    def _handle_health(self) -> None:
        """Health check endpoint."""
        m = get_metrics()
        self._send_json_response(200, APIResponse(
            success=True,
            data={
                "status": "healthy",
                "version": __version__,
                "api_version": API_VERSION,
                "uptime_seconds": round(m.uptime_s, 1),
                "requests_served": m.total_requests,
                "parse_errors_total": m.total_parse_errors,
                "endpoints": [
                    "GET  /v1/health",
                    "GET  /v1/targets",
                    "GET  /v1/rules",
                    "GET  /v1/metrics",
                    "GET  /v1/docs",
                    "POST /v1/parse",
                    "POST /v1/validate",
                    "POST /v1/transpile",
                    "POST /v1/lint",
                    "POST /v1/jobs/submit",
                    "GET  /v1/jobs/{id}",
                    "GET  /v1/jobs/{id}/stream",
                ],
            }
        ))

    def _handle_metrics(self) -> None:
        """Prometheus metrics endpoint."""
        body = get_metrics().format_prometheus().encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; version=0.0.4; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self._finish_request_log(200, True)

    def _handle_docs(self) -> None:
        """Serve Swagger UI redirect."""
        html = f"""<!DOCTYPE html>
<html><head><title>Yuho API Docs</title>
<meta charset="utf-8">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css">
</head><body>
<div id="swagger-ui"></div>
<script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({{url:"/v1/openapi.yaml",dom_id:"#swagger-ui"}})</script>
</body></html>"""
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self._finish_request_log(200, True)
    
    def _paginate(self, items: list, params: dict) -> dict:
        """Apply offset/limit pagination to a list."""
        offset = max(int(params.get("offset", [0])[0]), 0)
        limit = min(max(int(params.get("limit", [50])[0]), 1), 200)
        page = items[offset:offset + limit]
        return {"items": page, "total": len(items), "offset": offset, "limit": limit}

    def _handle_targets(self) -> None:
        """List available transpile targets."""
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        targets = [
            {"name": t.name.lower(), "extension": t.file_extension}
            for t in TranspileTarget
        ]
        pg = self._paginate(targets, params)
        self._send_json_response(200, APIResponse(
            success=True,
            data={"targets": pg["items"], "total": pg["total"], "offset": pg["offset"], "limit": pg["limit"]}
        ))
    
    def _handle_rules(self) -> None:
        """List available lint rules."""
        from yuho.cli.commands.lint import ALL_RULES
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        rules = [
            {"id": r.id, "severity": r.severity.name.lower(), "description": r.description}
            for r in ALL_RULES
        ]
        pg = self._paginate(rules, params)
        self._send_json_response(200, APIResponse(
            success=True,
            data={"rules": pg["items"], "total": pg["total"], "offset": pg["offset"], "limit": pg["limit"]}
        ))
    
    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize user-provided filename for error messages only."""
        name = name.replace("\x00", "").replace("/", "_").replace("\\", "_")
        if len(name) > 255:
            name = name[:255]
        return name or "<api>"

    @staticmethod
    def _check_source_length(source: str) -> Optional[str]:
        """Return error string if source exceeds limit, else None."""
        if len(source) > MAX_SOURCE_LENGTH:
            return f"Source exceeds maximum length ({MAX_SOURCE_LENGTH} chars)"
        if "\x00" in source:
            return "Source contains null bytes"
        return None

    def _handle_parse(self, data: Dict[str, Any]) -> None:
        """Parse Yuho source code."""
        source = data.get('source', '')
        filename = self._sanitize_filename(data.get('filename', '<api>'))

        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        src_err = self._check_source_length(source)
        if src_err:
            self._send_json_response(400, APIResponse(success=False, error=src_err))
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
            self._send_json_response(422, APIResponse(
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
        filename = self._sanitize_filename(data.get('filename', '<api>'))
        include_metrics = bool(data.get('include_metrics', False))
        explain_errors = bool(data.get('explain_errors', False))
        
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        src_err = self._check_source_length(source)
        if src_err:
            self._send_json_response(400, APIResponse(success=False, error=src_err))
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

        status = 200 if len(errors) == 0 else 422
        self._send_json_response(status, APIResponse(
            success=len(errors) == 0,
            data=response_data
        ))
    
    def _handle_transpile(self, data: Dict[str, Any]) -> None:
        """Transpile Yuho source code."""
        source = data.get('source', '')
        target_name = data.get('target', 'json')
        filename = self._sanitize_filename(data.get('filename', '<api>'))
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        src_err = self._check_source_length(source)
        if src_err:
            self._send_json_response(400, APIResponse(success=False, error=src_err))
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
        rules = data.get('rules', None)
        filename = self._sanitize_filename(data.get('filename', '<api>'))
        if not source:
            self._send_json_response(400, APIResponse(
                success=False,
                error="Missing 'source' field"
            ))
            return
        src_err = self._check_source_length(source)
        if src_err:
            self._send_json_response(400, APIResponse(success=False, error=src_err))
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
    
    def _handle_job_submit(self, data: Dict[str, Any]) -> None:
        """Submit an async transpile job."""
        source = data.get('source', '')
        target_name = data.get('target', 'json')
        if not source:
            self._send_json_response(400, APIResponse(success=False, error="Missing 'source' field"))
            return
        def _run_transpile(job: Job) -> Dict[str, Any]:
            job.add_event("parse", "Parsing source", progress=0.2)
            result = run_parser_boundary(self.parser.parse, source, "<job>", message="Parse failed")
            if result.errors:
                raise ValueError("; ".join(e.message for e in result.errors))
            job.add_event("ast", "Building AST", progress=0.4)
            builder = ASTBuilder(source, "<job>")
            ast = run_ast_boundary(builder.build, result.tree.root_node, message="AST failed")
            job.add_event("transpile", f"Transpiling to {target_name}", progress=0.7)
            target = TranspileTarget.from_string(target_name)
            transpiler = self.registry.get(target)
            output = run_transpile_boundary(transpiler.transpile, ast, message="Transpile failed")
            return {"target": target_name, "output": output}
        queue = get_job_queue()
        job = queue.submit(_run_transpile)
        self._send_json_response(202, APIResponse(success=True, data={"job_id": job.id, "status": job.status.value}))

    def _handle_job_status(self, job_id: str) -> None:
        """Get job status."""
        job = get_job_queue().get(job_id)
        if not job:
            self._send_json_response(404, APIResponse(success=False, error=APIError(code="NOT_FOUND", message=f"Job {job_id} not found")))
            return
        self._send_json_response(200, APIResponse(success=True, data=job.to_dict()))

    def _handle_job_stream(self, job_id: str) -> None:
        """SSE stream for job events."""
        job = get_job_queue().get(job_id)
        if not job:
            self._send_json_response(404, APIResponse(success=False, error=APIError(code="NOT_FOUND", message=f"Job {job_id} not found")))
            return
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.send_header('Connection', 'keep-alive')
        self.send_header('Access-Control-Allow-Origin', self._get_cors_origin())
        self.end_headers()
        try:
            for chunk in stream_job_events(job):
                self.wfile.write(chunk.encode('utf-8'))
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        self._finish_request_log(200, True)

    def log_message(self, format: str, *args) -> None:
        """Override to use our logging."""
        if hasattr(self.server, 'verbose') and self.server.verbose:
            message = format % args
            click.echo(f"[API] {self.address_string()} - {message}")


class YuhoAPIServer(ThreadingHTTPServer):
    """Custom HTTP server with auth, rate limiting, and metrics."""

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        verbose: bool = False,
        auth_token: Optional[str] = None,
        cors_origins: Optional[List[str]] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ):
        super().__init__(server_address, RequestHandlerClass)
        self.verbose = verbose
        self.auth_token = auth_token
        self.cors_origins = cors_origins or ["*"]
        self.rate_limiter = rate_limiter


def run_api(
    host: Optional[str] = None,
    port: Optional[int] = None,
    verbose: bool = False,
    color: bool = True,
) -> None:
    """Start the Yuho API server."""
    from yuho.config.loader import get_config

    cfg = get_config()
    api_cfg = cfg.api
    resolved_host = host or api_cfg.host
    resolved_port = port if port is not None else api_cfg.port
    auth_token = get_auth_token()
    limiter = RateLimiter(RateLimitConfig(
        requests_per_second=api_cfg.rate_limit_rps,
        burst_size=api_cfg.rate_limit_burst,
        enabled=api_cfg.rate_limit_enabled,
    ))

    try:
        httpd = YuhoAPIServer(
            (resolved_host, resolved_port),
            YuhoAPIHandler,
            verbose=verbose,
            auth_token=auth_token,
            cors_origins=api_cfg.cors_origins,
            rate_limiter=limiter,
        )
    except OSError as e:
        click.echo(colorize(f"error: Could not start server: {e}", Colors.RED), err=True)
        sys.exit(1)

    url = f"http://{resolved_host}:{resolved_port}"
    click.echo(f"Yuho API {API_VERSION} at {colorize(url, Colors.CYAN) if color else url}")
    click.echo(f"Auth: {'enabled' if auth_token else 'disabled'}")
    click.echo("Endpoints:")
    click.echo("  GET  /v1/health    - Health check")
    click.echo("  GET  /v1/targets   - List transpile targets")
    click.echo("  GET  /v1/rules     - List lint rules")
    click.echo("  GET  /v1/metrics   - Prometheus metrics")
    click.echo("  GET  /v1/docs      - Swagger UI")
    click.echo("  POST /v1/parse     - Parse Yuho source")
    click.echo("  POST /v1/validate  - Validate Yuho source")
    click.echo("  POST /v1/transpile - Transpile to target format")
    click.echo("  POST /v1/lint      - Run lint checks")
    click.echo("\nPress Ctrl+C to stop")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        click.echo("\nShutting down...")
        httpd.shutdown()
