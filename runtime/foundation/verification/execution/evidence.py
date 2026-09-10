"""M28.5 — Evidence capture.

Every execution produces an immutable ExecutionEvidence record with the
full fingerprint set, kill/survive counts, and artifact paths.
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from runtime.foundation.verification.env import hash_file
from runtime.foundation.verification.execution.classification import FailureKind

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


@dataclass(frozen=True, slots=True)
class ExecutionEvidence:
    """An immutable record of a single executable task's execution.

    For verification kinds where mutation metrics do not apply, the
    corresponding fields are explicitly absent (the dataclass does not
    initialise them — see ``to_dict``).
    """

    execution_id: str
    task_id: str
    component: str
    capability: str
    verification_kind: str
    started_at: str
    completed_at: str
    duration_seconds: float
    command: str
    exit_code: int
    failure_kind: FailureKind | None
    failure_message: str
    counts: dict[str, int] = field(default_factory=dict)
    coverage: float | None = None
    test_count: int | None = None
    source_fingerprint: str = ""
    test_fingerprint: str = ""
    config_fingerprint: str = ""
    toolchain_fingerprint: str = ""
    artifact_paths: tuple[str, ...] = ()
    repository_sha: str = ""
    notes: str = ""

    def to_dict(self) -> dict:
        d: dict[str, object] = {
            "execution_id": self.execution_id,
            "task_id": self.task_id,
            "component": self.component,
            "capability": self.capability,
            "verification_kind": self.verification_kind,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_seconds": self.duration_seconds,
            "command": self.command,
            "exit_code": self.exit_code,
            "failure_kind": self.failure_kind.value if self.failure_kind else None,
            "failure_message": self.failure_message,
            "source_fingerprint": self.source_fingerprint,
            "test_fingerprint": self.test_fingerprint,
            "config_fingerprint": self.config_fingerprint,
            "toolchain_fingerprint": self.toolchain_fingerprint,
            "repository_sha": self.repository_sha,
            "artifact_paths": list(self.artifact_paths),
            "notes": self.notes,
        }
        # Mutation-specific metrics (only present when the kind recorded
        # them). For non-mutation kinds, these keys are explicitly
        # absent — not zero, not None.
        if self.counts:
            d["counts"] = dict(self.counts)
        if self.coverage is not None:
            d["coverage"] = self.coverage
        if self.test_count is not None:
            d["test_count"] = self.test_count
        return d


def _git_sha() -> str:
    try:
        return (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout.strip()
            or "unknown"
        )
    except Exception:
        return "unknown"
