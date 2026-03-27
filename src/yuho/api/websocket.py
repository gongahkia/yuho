"""WebSocket handler for live validation and JSON-RPC."""

import json
import logging
from typing import Any, Callable, Dict

from yuho.services.analysis import analyze_source

logger = logging.getLogger("yuho.api.ws")

# JSON-RPC method handlers
MethodHandler = Callable[[Dict[str, Any]], Dict[str, Any]]
METHODS: Dict[str, MethodHandler] = {}


def register_method(name: str) -> Callable[[MethodHandler], MethodHandler]:
    """Decorator to register a JSON-RPC method."""

    def decorator(fn: MethodHandler) -> MethodHandler:
        METHODS[name] = fn
        return fn

    return decorator


@register_method("parse")
def handle_parse(params: Dict[str, Any]) -> Dict[str, Any]:
    source = params.get("source", "")
    result = analyze_source(source, run_semantic=False)
    payload = result.validation_payload()
    payload["valid"] = bool(payload["parse_valid"] and payload["ast_valid"])
    if result.ast is not None:
        payload["statute_sections"] = [s.section_number for s in result.ast.statutes]
    return payload


@register_method("validate")
def handle_validate(params: Dict[str, Any]) -> Dict[str, Any]:
    source = params.get("source", "")
    result = analyze_source(source)
    return result.validation_payload()


@register_method("transpile")
def handle_transpile(params: Dict[str, Any]) -> Dict[str, Any]:
    source = params.get("source", "")
    target = params.get("target", "json")
    from yuho.transpile.base import TranspileTarget
    from yuho.transpile.registry import TranspilerRegistry

    analysis = analyze_source(source, file="<ws>", run_semantic=False)
    if not analysis.parse_valid or not analysis.ast_valid or analysis.ast is None:
        return analysis.validation_payload()

    t = TranspileTarget.from_string(target)
    transpiler = TranspilerRegistry.instance().get(t)
    output = transpiler.transpile(analysis.ast)
    return {
        "target": target,
        "output": output,
        "parse_valid": analysis.parse_valid,
        "ast_valid": analysis.ast_valid,
    }


def process_jsonrpc(message: str) -> str:
    """Process a JSON-RPC 2.0 request, return JSON-RPC response."""
    try:
        req = json.loads(message)
    except json.JSONDecodeError:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32700, "message": "Parse error"},
                "id": None,
            }
        )
    method = req.get("method", "")
    params = req.get("params", {})
    req_id = req.get("id")
    handler = METHODS.get(method)
    if not handler:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32601, "message": f"Method not found: {method}"},
                "id": req_id,
            }
        )
    try:
        result = handler(params)
        return json.dumps({"jsonrpc": "2.0", "result": result, "id": req_id})
    except Exception as e:
        logger.exception("WebSocket method error")
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "error": {"code": -32000, "message": str(e)},
                "id": req_id,
            }
        )
