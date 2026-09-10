"""Mutation task adapter.

Extracted from executor_pipeline.py M28.3 — preserves the exact functional
signature: ``(PlannedTask, TaskFingerprints) -> ExecutableVerificationTask``.
"""

from __future__ import annotations

from pathlib import Path

from runtime.foundation.verification.evidence_planner import PlannedTask
from runtime.foundation.verification.execution.task import (
    DEFAULT_TASK_TIMEOUT,
    ExecutableVerificationTask,
    TaskFingerprints,
)
from runtime.foundation.verification.mutation_contract import (
    ENGINE_SELECTION,
    is_valid_engine,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def _engine_selection_for(component: str) -> dict | None:
    sel = ENGINE_SELECTION.get(component)
    if sel is not None:
        return {
            "test_selection": list(sel.test_selection),
            "source_paths": list(sel.source_paths),
        }
    return None


def adapt_mutation_task(
    planned: PlannedTask, fps: TaskFingerprints
) -> ExecutableVerificationTask:
    component = planned.target
    if not is_valid_engine(component):
        return ExecutableVerificationTask(
            task_id=f"exec::{planned.task_id}",
            component=component,
            capability=planned.target.replace("_", "-"),
            verification_kind="mutation",
            source_task_id=planned.task_id,
            execution_command="",
            working_directory=str(REPO_ROOT),
            required_environment=(".venv", "mutmut==3.7.0"),
            evidence_kind="mutation-summary",
            expected_artifact="backend/tests/generated/mutation/mutation-summary.json",
            timeout_policy=DEFAULT_TASK_TIMEOUT,
            source_fingerprint=fps.source,
            test_fingerprint=fps.test,
            config_fingerprint=fps.config,
            toolchain_fingerprint=fps.toolchain,
            reason=planned.cause,
            executable="not_executable_yet",
            executable_meta={
                "blocker": f"component {component!r} is not in ENGINE_SELECTION",
            },
        )
    sel = _engine_selection_for(component) or {}
    cmd = f".venv/bin/python runtime/verify.py mutation " f"--target {component} --json"
    return ExecutableVerificationTask(
        task_id=f"exec::{planned.task_id}",
        component=component,
        capability=planned.target.replace("_", "-"),
        verification_kind="mutation",
        source_task_id=planned.task_id,
        execution_command=cmd,
        working_directory=str(REPO_ROOT),
        required_environment=(".venv", "mutmut==3.7.0"),
        evidence_kind="mutation-summary",
        expected_artifact=f"backend/tests/generated/mutation/target-{component}-summary.json",
        timeout_policy=DEFAULT_TASK_TIMEOUT,
        source_fingerprint=fps.source,
        test_fingerprint=fps.test,
        config_fingerprint=fps.config,
        toolchain_fingerprint=fps.toolchain,
        reason=planned.cause,
        executable="executable",
        executable_meta={
            "engine_selection": sel,
            "expected_engine": component,
        },
    )
