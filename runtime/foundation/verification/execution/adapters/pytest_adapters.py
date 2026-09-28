"""Pytest-bound adapter factory.

Extracted from executor_pipeline.py M50 S2 — the factory that produces
adapters for property, invariant, contract, coverage, golden, and
capability kinds.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from runtime.foundation.verification.evidence_planner import PlannedTask
from runtime.foundation.verification.execution.task import (
    ExecutableVerificationTask,
    TaskFingerprints,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

# Each canonical pytest target was discovered by direct inspection of
# backend/tests/. Adding a new target here requires a corresponding
# canonical test directory to exist.
CANONICAL_PYTEST_TARGETS: dict[str, tuple[str, str, int]] = {
    # kind -> (pytest_target_relative_to_repo_root, evidence_kind, timeout_seconds)
    "property": ("backend/tests/properties", "hypothesis-report", 600),
    "invariant": ("backend/tests/invariants", "pytest-junit", 900),
    "contract": ("backend/tests/contract", "contract-validation", 600),
    "coverage": ("backend/tests", "coverage-summary", 1800),
    "golden": ("backend/tests/golden", "golden-snapshot", 600),
    "capability": ("backend/tests/capability", "pytest-junit", 600),
}


def build_pytest_adapter(
    kind: str,
) -> Callable[[PlannedTask, TaskFingerprints], ExecutableVerificationTask]:
    """Construct a real pytest-bound adapter for the given kind."""
    pytest_target, evidence_kind, timeout = CANONICAL_PYTEST_TARGETS[kind]

    def adapter(
        planned: PlannedTask, fps: TaskFingerprints
    ) -> ExecutableVerificationTask:
        component = planned.target
        cap = planned.target.replace("_", "-")
        # Refine pytest target when a specific component is targeted and a
        # component-named test directory exists.
        refined = pytest_target
        if component:
            cand = REPO_ROOT / pytest_target / component.replace("-", "_")
            if cand.is_dir():
                refined = str(cand.relative_to(REPO_ROOT))
        junit_artifact = (
            f"runtime/generated/m9-c50.13/junit-{kind}-" f"{component or 'all'}.xml"
        )
        cmd = (
            f".venv/bin/python -m pytest {refined} -q " f"--junit-xml={junit_artifact}"
        )
        return ExecutableVerificationTask(
            task_id=f"exec::{planned.task_id}",
            component=component,
            capability=cap,
            verification_kind=kind,
            source_task_id=planned.task_id,
            execution_command=cmd,
            working_directory=str(REPO_ROOT),
            required_environment=(".venv", "pytest"),
            evidence_kind=evidence_kind,
            expected_artifact=junit_artifact,
            timeout_policy=timeout,
            source_fingerprint=fps.source,
            test_fingerprint=fps.test,
            config_fingerprint=fps.config,
            toolchain_fingerprint=fps.toolchain,
            reason=planned.cause,
            executable="executable",
            executable_meta={
                "canonical_pytest_target": refined,
                "adapter_kind": kind,
            },
        )

    return adapter
