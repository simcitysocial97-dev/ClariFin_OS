"""M28.8 — Scope enforcement for targeted mutation execution.

Detects scope mismatches between the planner-expected engine and the
actually installed mutmut source_paths.
"""

from __future__ import annotations

import hashlib
import re
import traceback
from datetime import UTC, datetime

from runtime.foundation.verification.execution.classification import FailureKind
from runtime.foundation.verification.execution.evidence import ExecutionEvidence, _git_sha
from runtime.foundation.verification.execution.task import (
    DEFAULT_TASK_TIMEOUT,
    ExecutableVerificationTask,
)
from runtime.foundation.verification.mutation_runner import execute_mutation

REPO_ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent.parent.parent.parent

# Pattern that detects a scope-mismatch in the configured mutation
# source_paths. The C42.7 mutation contract installs a single engine's
# source_paths into backend/pyproject.toml before running mutmut. If
# that block references any other engine's source, the executor must
# BLOCK and emit a scope-mismatch evidence record.
_SCOPE_PATH_TOKEN_RE = re.compile(r"src/engines/(?P<eng>[a-z0-9_]+)")


def _read_installed_mutmut_scope() -> set[str]:
    """Read the source_paths that the canonical mutation contract
    installed into backend/pyproject.toml. Returns the set of engine
    names referenced. Empty set if the block is absent."""
    cfg = REPO_ROOT / "backend" / "pyproject.toml"
    if not cfg.exists():
        return set()
    text = cfg.read_text()
    # Only consider the [tool.mutmut] block, not the file as a whole.
    in_block = False
    block: list[str] = []
    for line in text.splitlines():
        if line.strip() == "[tool.mutmut]":
            in_block = True
            continue
        if in_block and line.strip().startswith("["):
            break
        if in_block:
            block.append(line)
    engines: set[str] = set()
    for line in block:
        for m in _SCOPE_PATH_TOKEN_RE.finditer(line):
            engines.add(m.group("eng"))
    return engines


def _scope_violation_message(expected: str, actual: set[str]) -> str:
    return (
        f"SCOPE MISMATCH: executor expected only {expected!r} in "
        f"installed mutmut scope, but discovered: {sorted(actual)}"
    )


def execute_mutation_task(
    task: ExecutableVerificationTask,
    *,
    max_runtime: int | None = None,
) -> ExecutionEvidence:
    """Execute a single mutation task, enforcing scope.

    Returns an ExecutionEvidence record regardless of outcome.
    """
    execution_id = f"exec-{hashlib.sha256(task.task_id.encode()).hexdigest()[:12]}"
    started = datetime.now(UTC)
    started_iso = started.isoformat()
    repo_sha = _git_sha()

    if task.executable != "executable":
        return ExecutionEvidence(
            execution_id=execution_id,
            task_id=task.task_id,
            component=task.component,
            capability=task.capability,
            verification_kind=task.verification_kind,
            started_at=started_iso,
            completed_at=datetime.now(UTC).isoformat(),
            duration_seconds=0.0,
            command=task.execution_command,
            exit_code=-2,
            failure_kind=FailureKind.CONFIGURATION,
            failure_message=f"task is not executable: {task.executable_meta}",
            source_fingerprint=task.source_fingerprint,
            test_fingerprint=task.test_fingerprint,
            config_fingerprint=task.config_fingerprint,
            toolchain_fingerprint=task.toolchain_fingerprint,
            repository_sha=repo_sha,
            notes="task adapter marked this as not_executable_yet",
        )

    # M28.8 — Scope enforcement: verify the command's expected engine
    # is the *only* engine present in the installed mutmut scope.
    expected_engine = task.executable_meta.get("expected_engine")
    if expected_engine:
        installed = _read_installed_mutmut_scope()
        if installed != {expected_engine}:
            return ExecutionEvidence(
                execution_id=execution_id,
                task_id=task.task_id,
                component=task.component,
                capability=task.capability,
                verification_kind=task.verification_kind,
                started_at=started_iso,
                completed_at=datetime.now(UTC).isoformat(),
                duration_seconds=0.0,
                command=task.execution_command,
                exit_code=-3,
                failure_kind=FailureKind.SCOPE,
                failure_message=_scope_violation_message(expected_engine, installed),
                source_fingerprint=task.source_fingerprint,
                test_fingerprint=task.test_fingerprint,
                config_fingerprint=task.config_fingerprint,
                toolchain_fingerprint=task.toolchain_fingerprint,
                repository_sha=repo_sha,
                notes=(
                    f"expected_engine={expected_engine}; installed_scope={sorted(installed)}"
                ),
            )

    # Invoke the canonical mutation runner. The runner already enforces
    # its own safety context; here we only capture the result.
    timeout = max_runtime or task.timeout_policy or DEFAULT_TASK_TIMEOUT
    try:
        result = execute_mutation(
            mode="target",
            target=task.component,
            max_runtime=timeout,
        )
    except Exception as exc:  # defensive
        return ExecutionEvidence(
            execution_id=execution_id,
            task_id=task.task_id,
            component=task.component,
            capability=task.capability,
            verification_kind=task.verification_kind,
            started_at=started_iso,
            completed_at=datetime.now(UTC).isoformat(),
            duration_seconds=(datetime.now(UTC) - started).total_seconds(),
            command=task.execution_command,
            exit_code=-1,
            failure_kind=FailureKind.INFRASTRUCTURE,
            failure_message=f"mutation runner raised: {exc}",
            source_fingerprint=task.source_fingerprint,
            test_fingerprint=task.test_fingerprint,
            config_fingerprint=task.config_fingerprint,
            toolchain_fingerprint=task.toolchain_fingerprint,
            repository_sha=repo_sha,
            notes=traceback.format_exc(limit=2),
        )

    completed = datetime.now(UTC).isoformat()
    duration = result.duration_seconds or 0
    # Classifier
    if result.execution_status != "PASS":
        fk = FailureKind.INFRASTRUCTURE
        msg = result.error or "mutation runner reported infrastructure failure"
    elif result.classification_status != "PASS" or not result.evidence_complete:
        fk = FailureKind.EVIDENCE
        msg = (
            "mutation evidence could not be reconciled "
            f"(classification_status={result.classification_status}, "
            f"complete={result.evidence_complete})"
        )
    elif result.mutation_score is None:
        fk = FailureKind.EVIDENCE
        msg = "mutation score was not evaluated"
    else:
        fk = None
        msg = ""

    return ExecutionEvidence(
        execution_id=execution_id,
        task_id=task.task_id,
        component=task.component,
        capability=task.capability,
        verification_kind=task.verification_kind,
        started_at=started_iso,
        completed_at=completed,
        duration_seconds=float(duration),
        command=task.execution_command,
        exit_code=result.mutmut_rc if result.mutmut_rc is not None else 0,
        failure_kind=fk,
        failure_message=msg,
        counts={
            "generated": result.mutants_generated,
            "killed": result.killed,
            "survived": result.survived,
            "no_tests": result.no_tests,
            "timeout": result.timeout,
            "suspicious": result.suspicious,
            "not_checked": result.not_checked,
        },
        source_fingerprint=task.source_fingerprint,
        test_fingerprint=task.test_fingerprint,
        config_fingerprint=result.config_hash or task.config_fingerprint,
        toolchain_fingerprint=task.toolchain_fingerprint,
        repository_sha=repo_sha,
        artifact_paths=(
            str(
                REPO_ROOT
                / "backend"
                / "tests"
                / "generated"
                / "mutation"
                / "mutation-summary.json"
            ),
        ),
        notes=(
            f"mode=target; run_id={result.run_id}; threshold={result.threshold_percent}%; "
            f"score={result.mutation_score}"
        ),
    )
