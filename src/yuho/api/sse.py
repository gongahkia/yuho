"""Server-Sent Events (SSE) helpers for streaming job progress."""

import json
import time
from typing import Any, Dict, Generator

from yuho.api.jobs import Job, JobStatus


def format_sse_event(event: str, data: Any, event_id: str = "") -> str:
    """Format a single SSE message."""
    lines = []
    if event_id:
        lines.append(f"id: {event_id}")
    lines.append(f"event: {event}")
    payload = json.dumps(data) if not isinstance(data, str) else data
    for line in payload.split("\n"):
        lines.append(f"data: {line}")
    lines.append("")
    lines.append("")
    return "\n".join(lines)


def stream_job_events(job: Job, poll_interval: float = 0.5) -> Generator[str, None, None]:
    """Yield SSE events as a job progresses."""
    seen = 0
    while True:
        events = job.events[seen:]
        for evt in events:
            yield format_sse_event(
                event=evt.stage,
                data={"message": evt.message, "progress": evt.progress},
            )
            seen += 1
        if job.status in (JobStatus.COMPLETE, JobStatus.FAILED):
            yield format_sse_event(
                event="done",
                data={"status": job.status.value, "result": job.result, "error": job.error},
            )
            break
        time.sleep(poll_interval)
