"""
Event Store — Program 7C

Append-only JSONL event store for engineering telemetry.
One JSON object per line. Immutable events only.
"""

from __future__ import annotations

import json
import logging
import subprocess
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


def _normalize_status(status: str) -> str:
    if status in {"pass", "passed"}:
        return "passed"
    if status in {"fail", "failed"}:
        return "failed"
    return status


_DECISION_TO_STATUS = {
    "certified": "passed",
    "diagnostic": "failed",
    "not_certifiable": "failed",
    "infrastructure_blocked": "blocked",
    "timeout_blocked": "blocked",
    "validation_blocked": "blocked",
    "awaiting_authorization": "blocked",
    "interrupted": "interrupted",
}


def decision_to_status(final_decision: str | None) -> str:
    return _DECISION_TO_STATUS.get(final_decision or "unknown", "unknown")


def _resolve_repository_identity() -> tuple[str, str]:
    try:
        commit_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        branch_result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        commit_sha = (getattr(commit_result, "stdout", "") or "").strip()
        branch = (getattr(branch_result, "stdout", "") or "").strip()
    except (OSError, subprocess.SubprocessError):
        return "", ""
    return commit_sha, branch


def record_verification_event(
    report: Any | None,
    profile_name: str | None = None,
    elapsed: float = 0.0,
    *,
    profile: str | None = None,
    duration: float | None = None,
    cache_hit: bool = False,
    status: str | None = None,
    passed: int | None = None,
    failed: int | None = None,
    skipped: int | None = None,
    evidence_count: int | None = None,
    plan_id: str | None = None,
    report_id: str | None = None,
    final_decision: str | None = None,
    extra_metadata: dict[str, Any] | None = None,
) -> None:
    resolved_profile = profile_name or profile
    if not resolved_profile:
        raise ValueError("profile_name is required")
    resolved_duration = elapsed if duration is None else duration
    try:
        from runtime.system.observability.execution_context import create_context
        from runtime.system.observability.repository import (
            LocalMetricsRepository,
            RunRecord,
        )

        summary = getattr(report, "summary", None)
        if summary is not None:
            overall_status = getattr(summary, "overall_status", "unknown")
            raw_status = getattr(overall_status, "value", overall_status)
            normalized_status = _normalize_status(str(raw_status))
            normalized_passed = int(getattr(summary, "passed", 0))
            normalized_failed = int(getattr(summary, "failed", 0))
            normalized_skipped = int(getattr(summary, "skipped", 0))
            normalized_evidence = len(getattr(report, "evidence_files", []) or [])
        else:
            normalized_status = _normalize_status(
                status or decision_to_status(final_decision)
            )
            normalized_passed = int(passed or 0)
            normalized_failed = int(failed or 0)
            normalized_skipped = int(skipped or 0)
            normalized_evidence = int(evidence_count or 0)

        commit_sha, branch = _resolve_repository_identity()
        context = create_context(commit_sha=commit_sha, branch=branch)
        metadata = dict(extra_metadata or {})
        if plan_id:
            metadata["plan_id"] = plan_id
        if report_id:
            metadata["report_id"] = report_id

        event_payload = {
            "profile": resolved_profile,
            "status": normalized_status,
            "passed": normalized_passed,
            "failed": normalized_failed,
            "skipped": normalized_skipped,
            "duration_seconds": resolved_duration,
            "evidence_count": normalized_evidence,
            "cache_hit": cache_hit,
        }
        completed_payload = {
            **event_payload,
            "final_decision": final_decision
            or ("certified" if normalized_status == "passed" else normalized_status),
        }
        event_store = EngineeringEventStore()
        record_event = create_event(
            "verification_record",
            context.to_dict(),
            event_payload,
            metadata=metadata,
        )
        event_store.append(record_event)
        completed_event = create_event(
            "VerificationCompleted",
            context.to_dict(),
            completed_payload,
            metadata=metadata,
        )
        event_store.append(completed_event)

        LocalMetricsRepository().append(
            RunRecord(
                run_id=record_event.event_id,
                timestamp=record_event.timestamp,
                environment=context.environment.value,
                runner=context.runner.value,
                verification_depth=context.verification_depth.value,
                intent=context.intent.value,
                trigger=context.trigger.value,
                commit_sha=commit_sha,
                branch=branch,
                profile=resolved_profile,
                status=normalized_status,
                passed=normalized_passed,
                failed=normalized_failed,
                skipped=normalized_skipped,
                duration_seconds=resolved_duration,
                evidence_count=normalized_evidence,
                cache_hit=cache_hit,
                metadata=metadata,
            )
        )
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Failed to record verification event: %s", exc
        )


def record_execution_report(
    profile_name: str,
    report: Any,
    elapsed: float,
) -> None:
    decision = getattr(report, "final_decision", None) or "unknown"
    status = decision_to_status(decision)
    records = getattr(report, "records", None) or []
    passed = 0
    failed = 0
    skipped = 0
    states: dict[str, int] = {}
    artifacts: set[str] = set()

    for task_record in records:
        state = getattr(task_record, "completion_state", "unknown")
        states[state] = states.get(state, 0) + 1
        if state in {"pass", "reused"}:
            passed += 1
        elif state == "failed":
            failed += 1
        elif state == "skipped":
            skipped += 1
        artifacts.update(getattr(task_record, "artifacts", None) or [])

    record_verification_event(
        None,
        profile_name,
        elapsed,
        status=status,
        passed=passed,
        failed=failed,
        skipped=skipped,
        evidence_count=sum(1 for artifact in artifacts if Path(artifact).exists()),
        plan_id=getattr(report, "plan_id", None),
        report_id=getattr(report, "report_id", None),
        final_decision=decision,
        extra_metadata={"task_states": states} if states else None,
    )


_record_verification_event = record_verification_event
