from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT: Path
EVENT_STORE_PATH: Path

@dataclass(frozen=True, slots=True)
class EngineeringEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    execution_context: dict[str, Any]
    payload: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EngineeringEvent: ...

class EngineeringEventStore:
    def __init__(self, path: Path | None = None) -> None: ...
    def append(self, event: EngineeringEvent) -> None: ...
    def iter_events(self) -> Iterator[EngineeringEvent]: ...
    def load_events(self) -> list[EngineeringEvent]: ...
    def load_events_since(self, since: datetime) -> list[EngineeringEvent]: ...
    def load_events_by_type(self, event_type: str) -> list[EngineeringEvent]: ...
    def load_events_by_environment(self, environment: str) -> list[EngineeringEvent]: ...
    def count(self) -> int: ...
    def clear(self) -> None: ...

def create_event(
    event_type: str,
    execution_context: dict[str, Any],
    payload: dict[str, Any],
    event_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> EngineeringEvent: ...
