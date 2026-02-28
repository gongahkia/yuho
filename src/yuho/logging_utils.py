"""Structured logging helpers for request-scoped events."""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Optional
from uuid import uuid4


@dataclass(frozen=True)
class RequestLogContext:
    """Request-scoped logging context with start time."""

    request_id: str
    started_at: float


def new_request_id(prefix: Optional[str] = None) -> str:
    """Generate a short request identifier."""
    rid = uuid4().hex[:12]
    if prefix:
        return f"{prefix}-{rid}"
    return rid


def log_structured(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    request_id: Optional[str] = None,
    duration_ms: Optional[float] = None,
    **fields: Any,
) -> None:
    """Emit a structured JSON log line."""
    payload: Dict[str, Any] = {"event": event}
    if request_id is not None:
        payload["request_id"] = request_id
    if duration_ms is not None:
        payload["duration_ms"] = round(duration_ms, 3)

    for key, value in fields.items():
        if value is not None:
            payload[key] = _normalize_value(value)

    logger.log(level, json.dumps(payload, sort_keys=True))


def start_request(
    logger: logging.Logger,
    event: str,
    *,
    request_id: Optional[str] = None,
    level: int = logging.INFO,
    **fields: Any,
) -> RequestLogContext:
    """Log request start and return its timing context."""
    rid = request_id or new_request_id()
    log_structured(
        logger,
        event,
        level=level,
        request_id=rid,
        **fields,
    )
    return RequestLogContext(request_id=rid, started_at=perf_counter())


def finish_request(
    logger: logging.Logger,
    context: RequestLogContext,
    event: str,
    *,
    status: str,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Log request completion with status and duration."""
    duration_ms = (perf_counter() - context.started_at) * 1000.0
    log_structured(
        logger,
        event,
        level=level,
        request_id=context.request_id,
        duration_ms=duration_ms,
        status=status,
        **fields,
    )


def _normalize_value(value: Any) -> Any:
    """Convert non-JSON values into safe structured representations."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value]
    if isinstance(value, dict):
        return {str(k): _normalize_value(v) for k, v in value.items()}
    return repr(value)
