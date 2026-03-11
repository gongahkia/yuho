"""Bearer token authentication middleware."""

import hmac
import os
from typing import Optional


def get_auth_token() -> Optional[str]:
    """Get configured auth token from env or config."""
    token = os.environ.get("YUHO_API_AUTH_TOKEN")
    if token:
        return token
    try:
        from yuho.config.loader import get_config
        return get_config().api.auth_token
    except Exception:
        return None


def verify_bearer_token(authorization: Optional[str], expected: Optional[str]) -> bool:
    """Verify Authorization header against expected token. Returns True if no token configured."""
    if not expected:
        return True # no auth configured
    if not authorization:
        return False
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    return hmac.compare_digest(parts[1], expected)


SKIP_AUTH_PATHS = frozenset(["/health", "/v1/health", "/"])
