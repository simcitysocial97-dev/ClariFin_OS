"""Unit test adapter.

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

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def adapt_unit_task(
    planned: PlannedTask, fps: TaskFingerprints
) -> ExecutableVerificationTask:
    component = planned.target
    cap = planned.target.replace("_", "-")
    return ExecutableVerificationTask(
        task_id=f"exec::{planned.task_id}",
        component=component,
        capability=cap,
        verification_kind="unit",
        source_task_id=planned.task_id,
        execution_command=(
            f".venv/bin/python -m pytest backend/tests/unit/engines/{component} -q"
        ),
        working_directory=str(REPO_ROOT),
        required_environment=(".venv", "pytest"),
        evidence_kind="pytest-junit",
        expected_artifact=f"runtime/generated/m9-c42.28/junit-unit-{component}.xml",
        timeout_policy=DEFAULT_TASK_TIMEOUT,
        source_fingerprint=fps.source,
        test_fingerprint=fps.test,
        config_fingerprint=fps.config,
        toolchain_fingerprint=fps.toolchain,
        reason=planned.cause,
        executable="executable",
        executable_meta={"pytest_target": f"backend/tests/unit/engines/{component}"},
    )
