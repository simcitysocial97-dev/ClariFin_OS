"""
Flaky Test Intelligence — Program 7C

Tracks per-test reliability metrics from event history.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .event_store import EngineeringEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]
FLAKY_TESTS_PATH = REPO_ROOT / "runtime" / "generated" / "flaky-tests.json"


@dataclass(frozen=True, slots=True)
class FlakyTestRecord:
    """Reliability record for a single test."""

    test_name: str
    failures: int = 0
    successes: int = 0
    failure_frequency: float = 0.0
    last_success: str | None = None
    last_failure: str | None = None
    affected_environment: str | None = None
    affected_profile: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_name": self.test_name,
            "failures": self.failures,
            "successes": self.successes,
            "failure_frequency": self.failure_frequency,
            "last_success": self.last_success,
            "last_failure": self.last_failure,
            "affected_environment": self.affected_environment,
            "affected_profile": self.affected_profile,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FlakyTestRecord:
        return cls(
            test_name=data["test_name"],
            failures=data["failures"],
            successes=data["successes"],
            failure_frequency=data["failure_frequency"],
            last_success=data.get("last_success"),
            last_failure=data.get("last_failure"),
            affected_environment=data.get("affected_environment"),
            affected_profile=data.get("affected_profile"),
            metadata=data.get("metadata", {}),
        )


class FlakyTestIntelligence:
    """Analyzes test reliability from events."""

    def __init__(self, event_store: EngineeringEventStore | None = None) -> None:
        self._event_store = event_store or EngineeringEventStore()

    def compute(self) -> dict[str, FlakyTestRecord]:
        events = self._event_store.load_events()
        test_records: dict[str, FlakyTestRecord] = {}

        for event in events:
            if event.event_type == "ExecutionFinished":
                payload = event.payload
                task_id = payload.get("task_id", "")
                status = payload.get("status", "unknown")
                timestamp = event.timestamp.isoformat()
                env = event.execution_context.get("environment", "unknown")
                profile = event.execution_context.get("metadata", {}).get("profile", "unknown")

                if task_id not in test_records:
                    test_records[task_id] = FlakyTestRecord(
                        test_name=task_id,
                        affected_environment=env,
                        affected_profile=profile,
                    )

                record = test_records[task_id]
                if status == "failed":
                    record.failures += 1
                    record.last_failure = timestamp
                elif status == "passed":
                    record.successes += 1
                    record.last_success = timestamp

                if record.affected_environment == "unknown":
                    record.affected_environment = env
                if record.affected_profile == "unknown":
                    record.affected_profile = profile

        for record in test_records.values():
            total = record.failures + record.successes
            record.failure_frequency = round(record.failures / total, 4) if total > 0 else 0.0

        return test_records

    def save(self, path: Path | None = None) -> None:
        target = path or FLAKY_TESTS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        records = self.compute()
        data = {name: record.to_dict() for name, record in records.items()}
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def generate_flaky_tests(event_store: EngineeringEventStore | None = None) -> dict[str, Any]:
    intelligence = FlakyTestIntelligence(event_store)
    intelligence.save()
    return {name: record.to_dict() for name, record in intelligence.compute().items()}
