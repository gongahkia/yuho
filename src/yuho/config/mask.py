"""
Utilities for masking sensitive data in logs, errors, and output.

This module provides functions to redact sensitive information like
API keys, tokens, and passwords before they appear in logs or error messages.
"""

import re
from typing import Any, Dict, List, Optional, Set

# Sensitive field names that should always be masked
SENSITIVE_FIELDS: Set[str] = {
    "api_key",
    "apikey",
    "api-key",
    "auth_token",
    "authtoken",
    "auth-token",
    "token",
    "password",
    "secret",
    "credential",
    "openai_api_key",
    "anthropic_api_key",
    "authorization",
    "bearer",
}

# Patterns that look like secrets (for string scanning)
SECRET_PATTERNS = [
    # API keys (various formats)
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),  # OpenAI-style
    re.compile(r"sk-ant-[a-zA-Z0-9-]{20,}"),  # Anthropic-style
    re.compile(r"hf_[a-zA-Z0-9]{20,}"),  # HuggingFace-style
    # Bearer tokens in headers
    re.compile(r"Bearer\s+[a-zA-Z0-9._-]{20,}", re.IGNORECASE),
    # Generic long alphanumeric strings that look like tokens
    re.compile(r"[a-zA-Z0-9]{32,}"),
]


def mask_value(value: str, visible_chars: int = 4) -> str:
    """
    Mask a sensitive value, showing only the first few characters.

    Args:
        value: The sensitive value to mask
        visible_chars: Number of characters to show at the start

    Returns:
        Masked value like "sk-a***" or "***" if too short
    """
    if not value or len(value) <= visible_chars:
        return "***"
    return value[:visible_chars] + "***"


def is_sensitive_key(key: str) -> bool:
    """
    Check if a key name indicates sensitive data.

    Args:
        key: The key/field name to check

    Returns:
        True if the key appears to be sensitive
    """
    key_lower = key.lower().replace("_", "").replace("-", "")
    for sensitive in SENSITIVE_FIELDS:
        if sensitive.replace("_", "").replace("-", "") in key_lower:
            return True
    return False


def mask_dict(data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """
    Mask sensitive values in a dictionary.

    Args:
        data: Dictionary potentially containing sensitive values
        deep: Whether to recursively mask nested dictionaries

    Returns:
        New dictionary with sensitive values masked
    """
    result = {}
    for key, value in data.items():
        if is_sensitive_key(key):
            if isinstance(value, str) and value:
                result[key] = mask_value(value)
            elif value is not None:
                result[key] = "***"
            else:
                result[key] = None
        elif deep and isinstance(value, dict):
            result[key] = mask_dict(value, deep=True)
        elif deep and isinstance(value, list):
            result[key] = [
                mask_dict(v, deep=True) if isinstance(v, dict) else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def mask_string(text: str) -> str:
    """
    Scan a string and mask anything that looks like a secret.

    Args:
        text: Text that might contain secrets

    Returns:
        Text with secret-like patterns masked
    """
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub(lambda m: mask_value(m.group(0)), result)
    return result


def mask_error(error: Exception) -> str:
    """
    Get a safe string representation of an error, masking any secrets.

    Args:
        error: The exception to format

    Returns:
        Error message with potential secrets masked
    """
    return mask_string(str(error))


def mask_url(url: str) -> str:
    """
    Mask sensitive parts of a URL (query params with sensitive names).

    Args:
        url: URL that might contain sensitive query parameters

    Returns:
        URL with sensitive query parameters masked
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    try:
        parsed = urlparse(url)
        if not parsed.query:
            return url

        params = parse_qs(parsed.query, keep_blank_values=True)
        masked_params = {}

        for key, values in params.items():
            if is_sensitive_key(key):
                masked_params[key] = ["***" for _ in values]
            else:
                masked_params[key] = values

        # Rebuild URL with masked params
        masked_query = urlencode(masked_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            masked_query,
            parsed.fragment,
        ))
    except Exception:
        # If URL parsing fails, just return original
        return url


def safe_repr(obj: Any) -> str:
    """
    Get a safe string representation of any object, masking secrets.

    Args:
        obj: Object to represent

    Returns:
        Safe string representation
    """
    if isinstance(obj, dict):
        return str(mask_dict(obj))
    elif isinstance(obj, str):
        return mask_string(obj)
    elif isinstance(obj, Exception):
        return mask_error(obj)
    else:
        return mask_string(repr(obj))
