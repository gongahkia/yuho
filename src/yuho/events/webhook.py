"""Webhook delivery with HMAC-SHA256 signatures."""

import hashlib
import hmac
import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from urllib.request import Request, urlopen
from urllib.error import URLError

from yuho.events.model import Event, EventType

logger = logging.getLogger("yuho.events.webhook")


@dataclass
class WebhookEndpoint:
    """A registered webhook endpoint."""

    id: str
    url: str
    secret: str
    events: List[str] = field(default_factory=lambda: ["*"])  # event types to subscribe
    enabled: bool = True
    max_retries: int = 3


class WebhookManager:
    """Manages webhook registrations and delivery."""

    def __init__(self) -> None:
        self._endpoints: Dict[str, WebhookEndpoint] = {}
        self._lock = threading.Lock()

    def register(self, endpoint: WebhookEndpoint) -> None:
        with self._lock:
            self._endpoints[endpoint.id] = endpoint

    def unregister(self, endpoint_id: str) -> bool:
        with self._lock:
            return self._endpoints.pop(endpoint_id, None) is not None

    def list_endpoints(self) -> List[WebhookEndpoint]:
        with self._lock:
            return list(self._endpoints.values())

    def _matches(self, endpoint: WebhookEndpoint, event: Event) -> bool:
        if "*" in endpoint.events:
            return True
        return event.type.value in endpoint.events

    def _sign(self, payload: bytes, secret: str) -> str:
        return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    def _deliver(self, endpoint: WebhookEndpoint, event: Event) -> bool:
        payload = json.dumps(event.to_dict()).encode("utf-8")
        signature = self._sign(payload, endpoint.secret)
        for attempt in range(endpoint.max_retries):
            try:
                req = Request(
                    endpoint.url,
                    data=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Yuho-Signature": f"sha256={signature}",
                        "X-Yuho-Event": event.type.value,
                        "X-Yuho-Event-ID": event.event_id,
                    },
                    method="POST",
                )
                resp = urlopen(req, timeout=10)
                if 200 <= resp.status < 300:
                    return True
            except (URLError, OSError) as e:
                wait = 2**attempt  # exponential backoff
                logger.warning(
                    f"Webhook delivery failed (attempt {attempt+1}): {e}, retrying in {wait}s"
                )
                time.sleep(wait)
        logger.error(f"Webhook delivery exhausted retries for {endpoint.url}")
        return False

    def dispatch(self, event: Event) -> None:
        """Dispatch event to all matching endpoints (async)."""
        with self._lock:
            targets = [
                ep for ep in self._endpoints.values() if ep.enabled and self._matches(ep, event)
            ]
        for ep in targets:
            t = threading.Thread(target=self._deliver, args=(ep, event), daemon=True)
            t.start()


_global_manager: Optional[WebhookManager] = None


def get_webhook_manager() -> WebhookManager:
    global _global_manager
    if _global_manager is None:
        _global_manager = WebhookManager()
    return _global_manager
