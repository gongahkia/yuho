"""Event type definitions."""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EventType(Enum):
    STATUTE_CREATED = "statute.created"
    STATUTE_UPDATED = "statute.updated"
    STATUTE_DEPRECATED = "statute.deprecated"
    PACKAGE_PUBLISHED = "package.published"
    VERIFICATION_FAILED = "verification.failed"
    VALIDATION_ERROR = "validation.error"


@dataclass
class Event:
    """An event that can trigger webhooks."""
    type: EventType
    source: str # file path or package name
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            import uuid
            self.event_id = uuid.uuid4().hex[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
        }
