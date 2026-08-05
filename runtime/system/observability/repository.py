"""
Metrics Repository — Program 7C

Abstraction for loading and saving hybrid metrics history.
LocalMetricsRepository reads/writes local history.
GitHubMetricsRepository reads/writes CI history.
No direct file access outside this module.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[3]
HISTORY_PATH = REPO_ROOT / "runtime" / "generated" / "engineering-history.json"


@dataclass(frozen=True, slots=True)
class RunRecord:
    """Single verification run record."""

    run_id: str
    timestamp: datetime
    environment: str
    runner: str
    verification_depth: str
    intent: str
    trigger: str
    commit_sha: str
    branch: str
    profile: str
    status: str
    passed: int
    failed: int
    skipped: int
    duration_seconds: float
    blast_radius: dict[str, Any] = field(default_factory=dict)
    evidence_count: int = 0
    cache_hit: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp.isoformat(),
            "environment": self.environment,
            "runner": self.runner,
            "verification_depth": self.verification_depth,
            "intent": self.intent,
            "trigger": self.trigger,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "profile": self.profile,
            "status": self.status,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "duration_seconds": self.duration_seconds,
            "blast_radius": self.blast_radius,
            "evidence_count": self.evidence_count,
            "cache_hit": self.cache_hit,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RunRecord:
        return cls(
            run_id=data["run_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            environment=data["environment"],
            runner=data["runner"],
            verification_depth=data["verification_depth"],
            intent=data["intent"],
            trigger=data["trigger"],
            commit_sha=data["commit_sha"],
            branch=data["branch"],
            profile=data["profile"],
            status=data["status"],
            passed=data["passed"],
            failed=data["failed"],
            skipped=data["skipped"],
            duration_seconds=data["duration_seconds"],
            blast_radius=data.get("blast_radius", {}),
            evidence_count=data.get("evidence_count", 0),
            cache_hit=data.get("cache_hit", False),
            metadata=data.get("metadata", {}),
        )


@dataclass(frozen=True, slots=True)
class HybridHistory:
    """Split history into local, CI, and combined."""

    local: list[RunRecord] = field(default_factory=list)
    ci: list[RunRecord] = field(default_factory=list)
    combined: list[RunRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "local": [r.to_dict() for r in self.local],
            "ci": [r.to_dict() for r in self.ci],
            "combined": [r.to_dict() for r in self.combined],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HybridHistory:
        return cls(
            local=[RunRecord.from_dict(r) for r in data.get("local", [])],
            ci=[RunRecord.from_dict(r) for r in data.get("ci", [])],
            combined=[RunRecord.from_dict(r) for r in data.get("combined", [])],
        )


class MetricsRepository(ABC):
    """Abstract metrics repository."""

    @abstractmethod
    def load(self) -> HybridHistory:
        """Load history from storage."""

    @abstractmethod
    def append(self, record: RunRecord) -> None:
        """Append a new run record."""

    @abstractmethod
    def save(self, history: HybridHistory) -> None:
        """Persist the full history."""


class LocalMetricsRepository(MetricsRepository):
    """Repository for local developer verification history."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or HISTORY_PATH

    def load(self) -> HybridHistory:
        if not self._path.exists():
            return HybridHistory()
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return HybridHistory.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return HybridHistory()

    def append(self, record: RunRecord) -> None:
        history = self.load()
        if record.environment == "ci":
            history.ci.append(record)
        else:
            history.local.append(record)
        history.combined.append(record)
        self.save(history)

    def save(self, history: HybridHistory) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(history.to_dict(), f, indent=2, default=str)


class GitHubMetricsRepository(MetricsRepository):
    """Repository for CI verification history (GitHub Actions)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or HISTORY_PATH

    def load(self) -> HybridHistory:
        if not self._path.exists():
            return HybridHistory()
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return HybridHistory.from_dict(data)
        except (json.JSONDecodeError, OSError):
            return HybridHistory()

    def append(self, record: RunRecord) -> None:
        history = self.load()
        history.ci.append(record)
        history.combined.append(record)
        self.save(history)

    def save(self, history: HybridHistory) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(history.to_dict(), f, indent=2, default=str)
