"""WebSocket handler for live validation and JSON-RPC."""

import json
import logging
from typing import Any, Callable, Dict, Optional

from yuho.services.analysis import analyze_source

logger = logging.getLogger("yuho.api.ws")

# JSON-RPC method handlers
METHODS: Dict[str, Callable] = {}


def register_method(name: str) -> Callable:
    """Decorator to register a JSON-RPC method."""
    def decorator(fn: Callable) -> Callable:
        METHODS[name] = fn
        return fn
    return decorator


@register_method("parse")
def handle_parse(params: Dict[str, Any]) -> Dict[str, Any]:
    source = params.get("source", "")
    result = analyze_source(source, run_semantic=False)
    if result.parse_errors:
        return {"errors": [{"message": e.message, "line": e.location.line if e.location else None} for e in result.parse_errors]}
    summary = result.ast_summary
    return {"statutes": summary.statutes if summary else 0, "valid": True}


@register_method("validate")
def handle_validate(params: Dict[str, Any]) -> Dict[str, Any]:
    source = params.get("source", "")
    result = analyze_source(source)
    errors = []
    for e in result.parse_errors:
        errors.append({"message": e.message, "line": e.location.line if e.location else None, "type": "parse"})
    for e in result.errors:
        errors.append({"message": e.message, "line": e.location.line if e.location else None, "type": e.stage})
    return {"valid": len(errors) == 0, "errors": errors}


@register_method("transpile")
def handle_transpile(params: Dict[str, Any]) -> Dict[str, Any]:
    source = params.get("source", "")
    target = params.get("target", "json")
    from yuho.parser import get_parser
    from yuho.ast import ASTBuilder
    from yuho.transpile.base import TranspileTarget
    from yuho.transpile.registry import TranspilerRegistry
    parser = get_parser()
    result = parser.parse(source)
    if result.errors:
        return {"errors": [{"message": e.message} for e in result.errors]}
    builder = ASTBuilder(source, "<ws>")
    ast = builder.build(result.tree.root_node)
    t = TranspileTarget.from_string(target)
    transpiler = TranspilerRegistry.instance().get(t)
    output = transpiler.transpile(ast)
    return {"target": target, "output": output}


def process_jsonrpc(message: str) -> str:
    """Process a JSON-RPC 2.0 request, return JSON-RPC response."""
    try:
        req = json.loads(message)
    except json.JSONDecodeError:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")
    handler = METHODS.get(method)
    if not handler:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method not found: {method}"}, "id": req_id})
    try:
        result = handler(params)
        return json.dumps({"jsonrpc": "2.0", "result": result, "id": req_id})
    except Exception as e:
        logger.exception("WebSocket method error")
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32000, "message": str(e)}, "id": req_id})
