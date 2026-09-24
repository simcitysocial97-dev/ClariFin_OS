"""
Event Store — Program 7C

Append-only JSONL event store for engineering telemetry.
One JSON object per line. Immutable events only.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
        if self._path.exists():
            existing_ids: set[str] = set()
            with open(self._path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        existing_ids.add(json.loads(line).get("event_id"))
                    except (json.JSONDecodeError, KeyError):
                        continue
            if event.event_id in existing_ids:
                return
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), default=str) + "\n")

    def iter_events(self) -> Iterator[EngineeringEvent]:
        if not self._path.exists():
            return
        with open(self._path, encoding="utf-8") as f:
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
        timestamp=datetime.now(UTC),
        execution_context=execution_context,
        payload=payload,
        metadata=metadata or {},
    )


def record_verification_event(
    report: Any,
    profile: str,
    duration: float,
    *,
    cache_hit: bool = False,
    status: str = "pass",
) -> None:
    """Record a verification run event to the engineering event store and metrics repository.

    This is the canonical function for persisting verification telemetry.
    It writes both an EngineeringEvent (to the JSONL event store) and a
    RunRecord (to the hybrid metrics history).

    Args:
        report: The verification report (or None for cache-only events).
        profile: The verification profile name (e.g. "backend", "runtime").
        duration: Execution duration in seconds.
        cache_hit: Whether this was a cache-hit observation.
        status: The verification status ("pass" or "fail").
    """
    import uuid as _uuid

    from runtime.system.observability.repository import (
        LocalMetricsRepository,
        RunRecord,
    )

    # Build payload
    payload: dict[str, Any] = {
        "profile": profile,
        "cache_hit": cache_hit,
        "status": status,
        "duration": duration,
    }
    if report is not None:
        payload["passed"] = getattr(report.summary, "passed", 0) if hasattr(report, "summary") else 0
        payload["failed"] = getattr(report.summary, "failed", 0) if hasattr(report, "summary") else 0
        payload["skipped"] = getattr(report.summary, "skipped", 0) if hasattr(report, "summary") else 0
        payload["evidence_count"] = len(getattr(report, "evidence_files", [])) if hasattr(report, "evidence_files") else 0
        payload["blast_radius"] = getattr(report, "blast_radius", {}) if hasattr(report, "blast_radius") else {}

    # Write to event store
    event = create_event(
        event_type="verification_run",
        execution_context={"environment": "local"},
        payload=payload,
        event_id=str(_uuid.uuid4()),
    )
    store = EngineeringEventStore()
    store.append(event)

    # Write to metrics repository
    repo = LocalMetricsRepository()
    run_record = RunRecord(
        run_id=str(_uuid.uuid4()),
        timestamp=datetime.now(UTC),
        environment="local",
        runner="verify.py",
        verification_depth="profile",
        intent="developer-feedback",
        trigger="manual",
        commit_sha="unknown",
        branch="unknown",
        profile=profile,
        status=status,
        passed=payload.get("passed", 0),
        failed=payload.get("failed", 0),
        skipped=payload.get("skipped", 0),
        duration_seconds=duration,
        blast_radius=payload.get("blast_radius", {}),
        evidence_count=payload.get("evidence_count", 0),
        cache_hit=cache_hit,
    )
    repo.append(run_record)


# Backward-compatible private alias
_record_verification_event = record_verification_event
