"""Shared token-bucket rate limiter extracted from MCP server."""

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    def __init__(self, retry_after: float):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.1f}s")


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_second: float = 10.0
    burst_size: int = 20
    per_client_rps: float = 5.0
    per_client_burst: int = 10
    enabled: bool = True
    exempt_paths: List[str] = field(default_factory=lambda: ["/health", "/v1/health"])


class TokenBucket:
    """Token bucket rate limiter."""
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_refill = now

    def acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def time_until_available(self, tokens: int = 1) -> float:
        with self._lock:
            self._refill()
            if self.tokens >= tokens:
                return 0.0
            return (tokens - self.tokens) / self.rate


class RateLimiter:
    """Rate limiter with global and per-client buckets."""
    def __init__(self, config: Optional[RateLimitConfig] = None):
        self.config = config or RateLimitConfig()
        self._global = TokenBucket(self.config.requests_per_second, self.config.burst_size)
        self._clients: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_client_bucket(self, client_id: str) -> TokenBucket:
        with self._lock:
            if client_id not in self._clients:
                self._clients[client_id] = TokenBucket(self.config.per_client_rps, self.config.per_client_burst)
            return self._clients[client_id]

    def check(self, path: str, client_id: Optional[str] = None) -> None:
        """Raise RateLimitExceeded if over limit."""
        if not self.config.enabled:
            return
        if path in self.config.exempt_paths:
            return
        if not self._global.acquire():
            raise RateLimitExceeded(self._global.time_until_available())
        if client_id:
            bucket = self._get_client_bucket(client_id)
            if not bucket.acquire():
                raise RateLimitExceeded(bucket.time_until_available())
