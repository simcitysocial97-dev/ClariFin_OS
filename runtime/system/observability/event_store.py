"""
Event Store — Program 7C

Append-only JSONL event store for engineering telemetry.
One JSON object per line. Immutable events only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

REPO_ROOT = Path(__file__).resolve().parents[3]
EVENT_STORE_PATH = REPO_ROOT / "runtime" / "generated" / "engineering-events.jsonl"


@dataclass(frozen=True, slots=True)
class EngineeringEvent:
    """Immutable engineering telemetry event."""

    event_id: str
    event_type: str
    timestamp: datetime
    execution_context: dict[str, Any]
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "execution_context": self.execution_context,
            "payload": self.payload,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EngineeringEvent:
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            execution_context=data["execution_context"],
            payload=data["payload"],
            metadata=data.get("metadata", {}),
        )


class EngineeringEventStore:
    """Append-only event store backed by JSONL."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or EVENT_STORE_PATH
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, event: EngineeringEvent) -> None:
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), default=str) + "\n")

    def iter_events(self) -> Iterator[EngineeringEvent]:
        if not self._path.exists():
            return
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    yield EngineeringEvent.from_dict(data)
                except (json.JSONDecodeError, KeyError):
                    continue

    def load_events(self) -> list[EngineeringEvent]:
        return list(self.iter_events())

    def load_events_since(self, since: datetime) -> list[EngineeringEvent]:
        return [e for e in self.iter_events() if e.timestamp >= since]

    def load_events_by_type(self, event_type: str) -> list[EngineeringEvent]:
        return [e for e in self.iter_events() if e.event_type == event_type]

    def load_events_by_environment(self, environment: str) -> list[EngineeringEvent]:
        return [
            e
            for e in self.iter_events()
            if e.execution_context.get("environment") == environment
        ]

    def count(self) -> int:
        return sum(1 for _ in self.iter_events())

    def clear(self) -> None:
        if self._path.exists():
            self._path.unlink()


def create_event(
    event_type: str,
    execution_context: dict[str, Any],
    payload: dict[str, Any],
    event_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> EngineeringEvent:
    import uuid

    return EngineeringEvent(
        event_id=event_id or str(uuid.uuid4()),
        event_type=event_type,
        timestamp=datetime.now(timezone.utc),
        execution_context=execution_context,
        payload=payload,
        metadata=metadata or {},
    )
