"""Bounded, data-only persistence primitives for local caches.

This module intentionally has no dynamic imports or object deserialization.
Callers supply a fixed dataclass allowlist, so cache bytes can never select a
Python class or execute a constructor outside that allowlist.
"""

from __future__ import annotations

import json
import math
import os
import stat
import tempfile
from dataclasses import fields, is_dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


MAX_CACHE_BYTES = 32 * 1024 * 1024
MAX_CACHE_DEPTH = 256


def type_key(cls: type[Any]) -> str:
    """Return the stable cache identifier for an explicitly allowed class."""
    return f"{cls.__module__}:{cls.__qualname__}"


def encode(value: Any, allowed_types: Mapping[str, type[Any]]) -> Any:
    """Encode a finite tree of supported values without executable metadata."""
    return _encode(value, allowed_types, depth=0)


def decode(value: Any, allowed_types: Mapping[str, type[Any]]) -> Any:
    """Decode data produced by :func:`encode` using an explicit type allowlist."""
    return _decode(value, allowed_types, depth=0)


def read_json(path: Path) -> dict[str, Any] | None:
    """Read one regular, bounded, non-symlink JSON cache file."""
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError:
        return None
    try:
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_CACHE_BYTES:
                return None
            if hasattr(os, "getuid") and info.st_uid != os.getuid():
                return None
            raw = handle.read(MAX_CACHE_BYTES + 1)
    except OSError:
        return None
    if len(raw) > MAX_CACHE_BYTES:
        return None
    try:
        decoded = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return decoded if isinstance(decoded, dict) else None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically write bounded cache data with owner-only permissions."""
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    if len(encoded) > MAX_CACHE_BYTES:
        raise ValueError("cache payload exceeds the configured size limit")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    try:
        os.chmod(path.parent, 0o700)
    except OSError:
        pass
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as handle:
            temporary_name = handle.name
            os.fchmod(handle.fileno(), 0o600)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        os.chmod(path, 0o600)
    finally:
        if temporary_name:
            try:
                Path(temporary_name).unlink(missing_ok=True)
            except OSError:
                pass


def _encode(value: Any, allowed_types: Mapping[str, type[Any]], depth: int) -> Any:
    if depth > MAX_CACHE_DEPTH:
        raise ValueError("cache object exceeds the configured nesting depth")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("cache does not support non-finite floats")
        return value
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("cache does not support non-finite decimals")
        return {"$type": "decimal", "value": str(value)}
    if isinstance(value, datetime):
        return {"$type": "datetime", "value": value.isoformat()}
    if isinstance(value, date):
        return {"$type": "date", "value": value.isoformat()}
    if isinstance(value, timedelta):
        return {"$type": "timedelta", "microseconds": value.total_seconds() * 1_000_000}
    if isinstance(value, Enum):
        key = type_key(type(value))
        if key not in allowed_types:
            raise TypeError(f"cache type is not allowed: {key}")
        return {"$type": "enum", "class": key, "name": value.name}
    if isinstance(value, tuple):
        return {"$type": "tuple", "items": [_encode(item, allowed_types, depth + 1) for item in value]}
    if isinstance(value, list):
        return [_encode(item, allowed_types, depth + 1) for item in value]
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise TypeError("cache dictionaries must have string keys")
        return {key: _encode(item, allowed_types, depth + 1) for key, item in value.items()}
    if is_dataclass(value) and not isinstance(value, type):
        key = type_key(type(value))
        if key not in allowed_types:
            raise TypeError(f"cache type is not allowed: {key}")
        return {
            "$type": "dataclass",
            "class": key,
            "fields": {
                item.name: _encode(getattr(value, item.name), allowed_types, depth + 1)
                for item in fields(value)
            },
        }
    raise TypeError(f"unsupported cache value: {type(value).__name__}")


def _decode(value: Any, allowed_types: Mapping[str, type[Any]], depth: int) -> Any:
    if depth > MAX_CACHE_DEPTH:
        raise ValueError("cache object exceeds the configured nesting depth")
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("cache does not support non-finite floats")
        return value
    if isinstance(value, list):
        return [_decode(item, allowed_types, depth + 1) for item in value]
    if not isinstance(value, dict):
        raise TypeError("cache contains an unsupported JSON value")
    tag = value.get("$type")
    if tag is None:
        return {key: _decode(item, allowed_types, depth + 1) for key, item in value.items()}
    if tag == "decimal":
        raw = value.get("value")
        if not isinstance(raw, str):
            raise ValueError("invalid cached decimal")
        try:
            result = Decimal(raw)
        except InvalidOperation as exc:
            raise ValueError("invalid cached decimal") from exc
        if not result.is_finite():
            raise ValueError("cache does not support non-finite decimals")
        return result
    if tag == "datetime":
        raw = value.get("value")
        if not isinstance(raw, str):
            raise ValueError("invalid cached datetime")
        return datetime.fromisoformat(raw)
    if tag == "date":
        raw = value.get("value")
        if not isinstance(raw, str):
            raise ValueError("invalid cached date")
        return date.fromisoformat(raw)
    if tag == "timedelta":
        microseconds = value.get("microseconds")
        if not isinstance(microseconds, (int, float)) or not math.isfinite(microseconds):
            raise ValueError("invalid cached timedelta")
        return timedelta(microseconds=microseconds)
    if tag == "tuple":
        items = value.get("items")
        if not isinstance(items, list):
            raise ValueError("invalid cached tuple")
        return tuple(_decode(item, allowed_types, depth + 1) for item in items)
    if tag == "enum":
        cls = _allowed_type(value.get("class"), allowed_types, Enum)
        name = value.get("name")
        if not isinstance(name, str):
            raise ValueError("invalid cached enum")
        return cls[name]
    if tag == "dataclass":
        cls = _allowed_type(value.get("class"), allowed_types, object)
        encoded_fields = value.get("fields")
        if not isinstance(encoded_fields, dict):
            raise ValueError("invalid cached dataclass")
        expected = {item.name for item in fields(cls)}
        if set(encoded_fields) != expected:
            raise ValueError("cached dataclass fields do not match the current schema")
        return cls(
            **{
                name: _decode(encoded, allowed_types, depth + 1)
                for name, encoded in encoded_fields.items()
            }
        )
    raise ValueError(f"unsupported cache type tag: {tag!r}")


def _allowed_type(
    key: object, allowed_types: Mapping[str, type[Any]], required_base: type[Any]
) -> type[Any]:
    if not isinstance(key, str) or key not in allowed_types:
        raise ValueError("cache type is not allowed")
    cls = allowed_types[key]
    if required_base is not object and not issubclass(cls, required_base):
        raise ValueError("cache type has an invalid kind")
    return cls
