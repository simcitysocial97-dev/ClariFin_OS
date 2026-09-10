"""M50 S3 + S4 + S7 — Unified execution dispatcher.

Single execution boundary. Every supported kind flows through this
dispatcher, which:
  1. Validates the task.
  2. Resolves the adapter.
  3. Generates deterministic execution_id and evidence_id.
  4. Invokes the underlying mechanism via the existing Executor (real
     subprocess; no fake records).
  5. Captures start/end state, exit code, artifacts.
  6. Computes artifact SHA-256.
  7. Returns an ExecutionResult that satisfies the lineage contract.

The dispatcher is the only place that produces execution_id and
evidence_id. Downstream consumers MUST NOT construct these themselves.
"""

from __future__ import annotations

import sys
from pathlib import Path

from runtime.foundation.verification.env import hash_file
from runtime.foundation.verification.execution.classification import FailureKind
from runtime.foundation.verification.execution.evidence import ExecutionEvidence, _git_sha
from runtime.foundation.verification.execution.identity import (
    IdentityKind,
    compute_identity,
    evidence_identity,
    environment_identity,
)
from runtime.foundation.verification.execution.task import (
    DEFAULT_TASK_TIMEOUT,
    ExecutableVerificationTask,
)
from runtime.foundation.verification.executor import Executor as _SubprocessExecutor

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


class LineageViolationError(RuntimeError):
    """Raised when lineage invariants are violated (e.g. evidence without
    a valid execution identity, decision without reconciliation)."""


def _evidence_path_for(task: ExecutableVerificationTask) -> Path:
    """Resolve the canonical artifact path for a task."""
    if task.expected_artifact:
        return REPO_ROOT / task.expected_artifact
    return (
        REPO_ROOT
        / "runtime"
        / "generated"
        / "m9-c50.13"
        / f"artifact-{task.task_id.replace('::', '_')}.bin"
    )


def _artifact_sha256(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        return hash_file(path)
    except Exception:
        return ""


def execute_task(
    task: ExecutableVerificationTask,
    *,
    per_step_timeout: int | None = None,
    executor: _SubprocessExecutor | None = None,
) -> ExecutionEvidence:
    """Execute a single executable task end-to-end.

    Returns a fully-populated ExecutionEvidence with deterministic
    execution_id and evidence_id. Raises LineageViolationError if the
    task itself is not executable.

    This function is the single boundary between the executor pipeline
    and any subprocess. Every real verification kind flows through here.
    """
    if task.executable != "executable":
        raise LineageViolationError(
            f"task {task.task_id!r} is not executable "
            f"(status={task.executable}, blocker={task.executable_meta.get('blocker')!r})"
        )
    if not task.execution_command:
        raise LineageViolationError(f"task {task.task_id!r} has no execution_command")

    # Deterministic execution_id — never reused.
    execution_id = compute_identity(
        IdentityKind.EXECUTION,
        task.task_id,
        task.source_fingerprint,
        task.test_fingerprint,
        task.config_fingerprint,
        task.toolchain_fingerprint,
        _git_sha(),
        namespace="runtime.verification",
    )
    started = __import__("datetime").datetime.now(__import__("datetime").UTC).isoformat()
    started_dt = __import__("datetime").datetime.now(__import__("datetime").UTC)

    # Use the provided executor or instantiate one with task timeout.
    ex = executor or _SubprocessExecutor(
        repo_root=REPO_ROOT,
        per_step_timeout=per_step_timeout
        or task.timeout_policy
        or DEFAULT_TASK_TIMEOUT,
    )

    # Run the real command. No fake execution. No skip.
    result = ex.execute(task.execution_command, task_id=task.task_id)

    completed_dt = __import__("datetime").datetime.now(__import__("datetime").UTC)
    completed = completed_dt.isoformat()
    duration = (completed_dt - started_dt).total_seconds()

    artifact_path = _evidence_path_for(task)
    artifact_sha = _artifact_sha256(artifact_path)
    env_id = environment_identity(
        {
            "python": sys.executable,
            "cwd": str(REPO_ROOT),
            "fingerprint_toolchain": task.toolchain_fingerprint,
            "fingerprint_config": task.config_fingerprint,
        }
    )
    ev_id = evidence_identity(execution_id, artifact_sha, env_id, task.evidence_kind)

    # Classify the outcome. Failure is preserved; success is verified.
    if result.status.value == "passed":
        fk: FailureKind | None = None
        msg = ""
    else:
        fk = (
            FailureKind.INFRASTRUCTURE
            if result.exit_code == -1
            else FailureKind.VERIFICATION
        )
        msg = (result.error or "execution reported non-zero exit").strip()

    return ExecutionEvidence(
        execution_id=execution_id,
        task_id=task.task_id,
        component=task.component,
        capability=task.capability,
        verification_kind=task.verification_kind,
        started_at=started,
        completed_at=completed,
        duration_seconds=duration,
        command=task.execution_command,
        exit_code=result.exit_code,
        failure_kind=fk,
        failure_message=msg,
        counts={},
        coverage=None,
        test_count=None,
        source_fingerprint=task.source_fingerprint,
        test_fingerprint=task.test_fingerprint,
        config_fingerprint=task.config_fingerprint,
        toolchain_fingerprint=task.toolchain_fingerprint,
        repository_sha=_git_sha(),
        artifact_paths=(str(artifact_path),) if artifact_path.exists() else (),
        notes=(
            f"execution_id={execution_id}; evidence_id={ev_id}; "
            f"artifact_sha256={artifact_sha}; environment_identity={env_id}"
        ),
    )
