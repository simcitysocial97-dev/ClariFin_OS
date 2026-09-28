"""Core data model for the execution pipeline.

This module defines the immutable task contract and supporting types that are
shared between executor_pipeline.py and the per-kind adapters.  It is placed
at the root of the ``execution`` package so that adapters can import from it
without pulling in the heavy executor_pipeline machinery (which would create
a circular dependency).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

# ---------------------------------------------------------------------------
# Kinds / status literals
# ---------------------------------------------------------------------------

VerificationKind = Literal[
    "unit",
    "property",
    "invariant",
    "contract",
    "coverage",
    "mutation",
    "golden",
    "capability",
]

ExecutableStatus = Literal[
    "planned",
    "not_executable_yet",
    "executable",
    "blocked_by_scope",
    "blocked_by_config",
    "executed",
]

# Maximum wall-clock time the executor is allowed to spend on a single
# executable task. This is a hard safety bound — the planner is the
# authority on what *should* run; the executor is the authority on what
# *can* safely run.
DEFAULT_TASK_TIMEOUT = 600


# ---------------------------------------------------------------------------
# Fingerprints
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TaskFingerprints:
    """The four fingerprints that bound a task's validity."""

    source: str
    test: str
    config: str
    toolchain: str

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "test": self.test,
            "config": self.config,
            "toolchain": self.toolchain,
        }


# ---------------------------------------------------------------------------
# Executable task contract
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutableVerificationTask:
    """The execution contract for a single planner-selected task.

    Where a planner task answers "what should happen", an executable
    task answers "what command will be invoked, where, with which
    environment, producing which artifact, and how long may it run".
    """

    task_id: str
    component: str
    capability: str
    verification_kind: VerificationKind
    source_task_id: str  # the planner task_id this expands
    execution_command: str
    working_directory: str
    required_environment: tuple[str, ...]
    evidence_kind: str
    expected_artifact: str
    timeout_policy: int
    source_fingerprint: str
    test_fingerprint: str
    config_fingerprint: str
    toolchain_fingerprint: str
    reason: str
    executable: ExecutableStatus = "executable"
    executable_meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "component": self.component,
            "capability": self.capability,
            "verification_kind": self.verification_kind,
            "source_task_id": self.source_task_id,
            "execution_command": self.execution_command,
            "working_directory": self.working_directory,
            "required_environment": list(self.required_environment),
            "evidence_kind": self.evidence_kind,
            "expected_artifact": self.expected_artifact,
            "timeout_policy": self.timeout_policy,
            "fingerprints": {
                "source": self.source_fingerprint,
                "test": self.test_fingerprint,
                "config": self.config_fingerprint,
                "toolchain": self.toolchain_fingerprint,
            },
            "reason": self.reason,
            "executable": self.executable,
            "executable_meta": dict(self.executable_meta),
        }


@dataclass(frozen=True, slots=True)
class ExecutableVerificationPlan:
    """A planner plan expanded with executable contracts."""

    plan_id: str
    generated_at: str
    plan_fingerprint: str
    source_plan_id: str
    tasks: tuple[ExecutableVerificationTask, ...]
    not_executable: tuple[ExecutableVerificationTask, ...]
    rationale: str

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "plan_fingerprint": self.plan_fingerprint,
            "source_plan_id": self.source_plan_id,
            "tasks": [t.to_dict() for t in self.tasks],
            "not_executable": [t.to_dict() for t in self.not_executable],
            "rationale": self.rationale,
            "counts": {
                "tasks": len(self.tasks),
                "not_executable": len(self.not_executable),
            },
        }
