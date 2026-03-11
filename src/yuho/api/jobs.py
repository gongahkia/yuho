"""Async job queue for long-running operations."""

import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class JobEvent:
    """A single event in a job's lifecycle."""
    stage: str
    message: str
    timestamp: float = field(default_factory=time.monotonic)
    progress: Optional[float] = None # 0.0-1.0


@dataclass
class Job:
    """An async job with event stream."""
    id: str
    status: JobStatus = JobStatus.PENDING
    events: List[JobEvent] = field(default_factory=list)
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.monotonic)

    def add_event(self, stage: str, message: str, progress: Optional[float] = None) -> None:
        self.events.append(JobEvent(stage=stage, message=message, progress=progress))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status.value,
            "events": [{"stage": e.stage, "message": e.message, "progress": e.progress} for e in self.events],
            "result": self.result,
            "error": self.error,
        }


class JobQueue:
    """In-memory job queue with background execution."""
    def __init__(self, max_jobs: int = 1000) -> None:
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()
        self._max_jobs = max_jobs

    def submit(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Job:
        """Submit a function for async execution. Returns the Job immediately."""
        job_id = uuid.uuid4().hex[:16]
        job = Job(id=job_id)
        with self._lock:
            if len(self._jobs) >= self._max_jobs:
                oldest = min(self._jobs.values(), key=lambda j: j.created_at)
                del self._jobs[oldest.id]
            self._jobs[job_id] = job
        def _run() -> None:
            job.status = JobStatus.RUNNING
            job.add_event("start", "Job started")
            try:
                job.result = fn(job, *args, **kwargs)
                job.status = JobStatus.COMPLETE
                job.add_event("complete", "Job finished", progress=1.0)
            except Exception as e:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.add_event("error", str(e))
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)


_global_queue: Optional[JobQueue] = None


def get_job_queue() -> JobQueue:
    global _global_queue
    if _global_queue is None:
        _global_queue = JobQueue()
    return _global_queue
