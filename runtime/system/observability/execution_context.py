"""
Execution Context Model — Program 7C

Immutable dataclasses that describe the environment and intent
surrounding every verification run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ExecutionEnvironment(str, Enum):
    """Where the verification run executes."""

    LOCAL = "local"
    CI = "ci"


class RunnerType(str, Enum):
    """Which runner executes the verification."""

    DEVELOPER_WORKSTATION = "developer-workstation"
    GITHUB_ACTIONS = "github-actions"


class VerificationDepth(str, Enum):
    """How deep the verification runs."""

    FAST = "fast"
    DEEP = "deep"


class VerificationIntent(str, Enum):
    """Why the verification is running."""

    DEVELOPER_FEEDBACK = "developer-feedback"
    ENGINEERING_VALIDATION = "engineering-validation"
    RELEASE_VALIDATION = "release-validation"


class TriggerType(str, Enum):
    """What triggered the verification."""

    MANUAL = "manual"
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    SCHEDULED = "scheduled"


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """Mandatory context for every verification run."""

    environment: ExecutionEnvironment
    runner: RunnerType
    verification_depth: VerificationDepth
    intent: VerificationIntent
    trigger: TriggerType
    commit_sha: str
    branch: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment.value,
            "runner": self.runner.value,
            "verification_depth": self.verification_depth.value,
            "intent": self.intent.value,
            "trigger": self.trigger.value,
            "commit_sha": self.commit_sha,
            "branch": self.branch,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionContext:
        return cls(
            environment=ExecutionEnvironment(data["environment"]),
            runner=RunnerType(data["runner"]),
            verification_depth=VerificationDepth(data["verification_depth"]),
            intent=VerificationIntent(data["intent"]),
            trigger=TriggerType(data["trigger"]),
            commit_sha=data["commit_sha"],
            branch=data["branch"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


def detect_environment() -> ExecutionEnvironment:
    """Detect whether running in CI or locally."""
    import os

    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        return ExecutionEnvironment.CI
    return ExecutionEnvironment.LOCAL


def detect_runner() -> RunnerType:
    """Detect the runner type."""
    import os

    if os.environ.get("GITHUB_ACTIONS"):
        return RunnerType.GITHUB_ACTIONS
    return RunnerType.DEVELOPER_WORKSTATION


def detect_trigger() -> TriggerType:
    """Detect what triggered the run."""
    import os

    if os.environ.get("GITHUB_EVENT_NAME"):
        event = os.environ["GITHUB_EVENT_NAME"]
        if event == "push":
            return TriggerType.PUSH
        if event == "pull_request":
            return TriggerType.PULL_REQUEST
        if event == "schedule":
            return TriggerType.SCHEDULED
        return TriggerType.MANUAL
    return TriggerType.MANUAL


def detect_depth() -> VerificationDepth:
    """Detect verification depth from environment."""
    if detect_environment() == ExecutionEnvironment.CI:
        return VerificationDepth.DEEP
    return VerificationDepth.FAST


def detect_intent() -> VerificationIntent:
    """Detect verification intent from environment."""
    if detect_environment() == ExecutionEnvironment.CI:
        return VerificationIntent.ENGINEERING_VALIDATION
    return VerificationIntent.DEVELOPER_FEEDBACK


def create_context(
    commit_sha: str = "unknown",
    branch: str = "unknown",
    intent: VerificationIntent | None = None,
    depth: VerificationDepth | None = None,
) -> ExecutionContext:
    """Create a fully populated execution context from environment detection."""
    return ExecutionContext(
        environment=detect_environment(),
        runner=detect_runner(),
        verification_depth=depth or detect_depth(),
        intent=intent or detect_intent(),
        trigger=detect_trigger(),
        commit_sha=commit_sha,
        branch=branch,
    )
