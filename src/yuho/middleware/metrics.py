"""Prometheus-compatible metrics collector."""

import threading
import time
from collections import defaultdict
from typing import Dict, Optional


class MetricsCollector:
    """Collects request metrics for /metrics endpoint."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._started_at = time.monotonic()
        self._request_count: Dict[str, int] = defaultdict(int) # key: "endpoint:status"
        self._request_duration: Dict[str, list] = defaultdict(list) # key: endpoint
        self._parse_errors: int = 0
        self._active: int = 0

    def record_request(self, endpoint: str, status: int, duration_s: float) -> None:
        with self._lock:
            self._request_count[f"{endpoint}:{status}"] += 1
            bucket = self._request_duration[endpoint]
            bucket.append(duration_s)
            if len(bucket) > 10000: # cap memory
                bucket[:] = bucket[-5000:]

    def record_parse_error(self) -> None:
        with self._lock:
            self._parse_errors += 1

    def inc_active(self) -> None:
        with self._lock:
            self._active += 1

    def dec_active(self) -> None:
        with self._lock:
            self._active -= 1

    def format_prometheus(self) -> str:
        """Render metrics in Prometheus text exposition format."""
        lines = []
        with self._lock:
            lines.append("# HELP yuho_requests_total Total HTTP requests")
            lines.append("# TYPE yuho_requests_total counter")
            for key, count in sorted(self._request_count.items()):
                endpoint, status = key.rsplit(":", 1)
                lines.append(f'yuho_requests_total{{endpoint="{endpoint}",status="{status}"}} {count}')
            lines.append("# HELP yuho_request_duration_seconds Request duration histogram")
            lines.append("# TYPE yuho_request_duration_seconds summary")
            for endpoint, durations in sorted(self._request_duration.items()):
                if durations:
                    s = sorted(durations)
                    lines.append(f'yuho_request_duration_seconds{{endpoint="{endpoint}",quantile="0.5"}} {s[len(s)//2]:.6f}')
                    lines.append(f'yuho_request_duration_seconds{{endpoint="{endpoint}",quantile="0.99"}} {s[int(len(s)*0.99)]:.6f}')
                    lines.append(f'yuho_request_duration_seconds_count{{endpoint="{endpoint}"}} {len(s)}')
                    lines.append(f'yuho_request_duration_seconds_sum{{endpoint="{endpoint}"}} {sum(s):.6f}')
            lines.append("# HELP yuho_parse_errors_total Total parse errors")
            lines.append("# TYPE yuho_parse_errors_total counter")
            lines.append(f"yuho_parse_errors_total {self._parse_errors}")
            lines.append("# HELP yuho_active_connections Current active connections")
            lines.append("# TYPE yuho_active_connections gauge")
            lines.append(f"yuho_active_connections {self._active}")
            uptime = time.monotonic() - self._started_at
            lines.append("# HELP yuho_uptime_seconds Server uptime")
            lines.append("# TYPE yuho_uptime_seconds gauge")
            lines.append(f"yuho_uptime_seconds {uptime:.1f}")
        return "\n".join(lines) + "\n"


_global_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = MetricsCollector()
    return _global_metrics
