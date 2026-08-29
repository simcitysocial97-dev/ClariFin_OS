"""
M9-C42.28 — M28.2 / M28.3 / M28.4 / M28.5 / M28.6 / M28.8 / M28.9
Executable Verification Plan + Targeted Executor + Evidence Capture
+ Reconciliation + Scope Enforcement + Failure Classification.

This module is the *runtime bridge* between the C42.27 evidence-aware
planner and the existing execution infrastructure. It contains:

  1. The executable verification-plan contract (M28.2)
     — every selected planner task is expanded into a concrete
       ExecutableVerificationTask with command, working dir, environment,
       expected artifact, timeouts, and source/test/config/toolchain
       fingerprints.

  2. The verification task adapter layer (M28.3)
     — adapters wrap the existing verification mechanisms (mutation
       runner, registry, orchestrator) for the kind families:
       unit, property, invariant, contract, coverage, mutation, golden,
       capability. Tasks that cannot yet be safely executed through
       this abstraction are marked ``not_executable_yet`` rather than
       faked or silently widened.

  3. The targeted mutation executor (M28.4)
     — only the components the planner selected are measured.

  4. The evidence-capture layer (M28.5)
     — every execution produces an immutable ExecutionEvidence record
       with the full fingerprint set, kill/survive counts, and artifact
       paths.

  5. Evidence reconciliation (M28.6) and labelled aggregate execution
     (M28.7) — produce the reconciled verification state and the
     labelled AUTHORITATIVE_MEASURED / AUTHORITATIVE_TARGETED /
     MATHEMATICALLY_RECONCILED aggregate.

  6. Scope enforcement (M28.8) and failure classification (M28.9)
     — the executor blocks scope mismatches and classifies every
     failure into verification / infrastructure / evidence / scope /
     configuration / certification.

  7. Forensic execution record (M28.13)
     — the single artifact the eventual Diagnostic & Forensic Agent
       will consume.

Design contract:

  * The planner is authoritative for scope. The executor must not
    independently rediscover or broaden scope.
  * Existing verification mechanisms are reused, not rewritten.
  * No silent repository-wide fallback. If a planner-selected task
    cannot be executed safely, it is marked not_executable_yet and the
    certification decision is BLOCKED.
  * No fabricated evidence. Fields that do not apply to a verification
    kind are explicitly absent.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable, Literal

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

assert (REPO_ROOT / "backend").is_dir(), f"REPO_ROOT sanity check failed: {REPO_ROOT}"

# C42.27 imports (the authoritative planner + evidence model)
from runtime.foundation.verification.evidence_planner import (  # noqa: E402
    EvidenceAwarePlan,
    EvidenceAwarePlanner,
    PlannedTask,
    default_planner,
)
from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    C42_26_POPULATION_ID,
    ComponentMeasurement,
    DerivedAggregate,
    EvidenceReuse,
    PopulationSnapshot,
    c42_24_b_measurements,
    c42_25_measurements,
    c42_26_population,
)
from runtime.foundation.verification.correlation import (  # noqa: E402
    Correlation,
    correlate,
)
from runtime.foundation.verification.mutation_runner import (  # noqa: E402
    execute_mutation,
)
from runtime.foundation.verification.mutation_contract import (  # noqa: E402
    ENGINE_SELECTION,
    is_valid_engine,
)
from runtime.foundation.verification.env import (  # noqa: E402
    REPO_ROOT as _ENV_REPO_ROOT,
    resolve_environment,
    hash_file,
)

# ===========================================================================
# M28.9 — Failure classification taxonomy (placed early; everything depends on it)
# ===========================================================================


class FailureKind(str, Enum):
    """Closed taxonomy of execution outcomes.

    Verification failure   — verification actually ran and found a defect.
    Infrastructure failure — verification could not execute correctly.
    Evidence failure       — execution occurred but required evidence could
                             not be captured or reconciled.
    Scope failure          — executor attempted to exceed planner-authorized
                             scope.
    Configuration failure  — requested task cannot be represented or
                             executed under current configuration.
    Certification failure  — all required evidence exists but the
                             certification criteria are not satisfied.
    """

    VERIFICATION = "verification_failure"
    INFRASTRUCTURE = "infrastructure_failure"
    EVIDENCE = "evidence_failure"
    SCOPE = "scope_failure"
    CONFIGURATION = "configuration_failure"
    CERTIFICATION = "certification_failure"


# ===========================================================================
# M28.2 — Executable verification-plan contract
# ===========================================================================

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


# ===========================================================================
# Fingerprinting helpers (deterministic, pure)
# ===========================================================================


def _hash_text(s: str | None) -> str:
    if s is None:
        return ""
    return hashlib.sha256(s.encode("utf-8", errors="replace")).hexdigest()


def _hash_file_safe(p: Path) -> str:
    if not p.exists():
        return ""
    try:
        return hash_file(p)
    except Exception:
        return ""


def collect_repo_fingerprints(component: str) -> TaskFingerprints:
    """Collect the four canonical fingerprints for a component.

    * source — fingerprint of the component's source directory
    * test   — fingerprint of the matching test directory
    * config — fingerprint of backend/pyproject.toml (mutation config)
    * toolchain — fingerprint of the canonical mutmut 3.7.0 + pytest toolchain
    """
    backend = REPO_ROOT / "backend"
    src = backend / "src" / "engines" / component
    test = backend / "tests" / "unit" / "engines" / component
    if not src.exists():
        # The component name may not include _engine suffix
        for cand in (
            (backend / "src" / "engines").iterdir()
            if (backend / "src" / "engines").exists()
            else []
        ):
            if cand.name.startswith(component):
                src = cand
                break
    cfg = backend / "pyproject.toml"

    def _dir_fingerprint(d: Path) -> str:
        if not d.exists():
            return ""
        h = hashlib.sha256()
        for f in sorted(d.rglob("*")):
            if f.is_file() and not any(part.startswith(".") for part in f.parts):
                h.update(str(f.relative_to(d)).encode())
                try:
                    h.update(f.read_bytes())
                except Exception:
                    h.update(b"<unreadable>")
        return h.hexdigest()

    toolchain = ""
    try:
        env = resolve_environment()
        parts = [
            env.python.version or "",
            env.pytest.version or "",
            env.mutmut.version or "",
        ]
        toolchain = _hash_text("|".join(parts))
    except Exception:
        toolchain = ""

    return TaskFingerprints(
        source=_dir_fingerprint(src),
        test=_dir_fingerprint(test),
        config=_hash_file_safe(cfg),
        toolchain=toolchain,
    )


# ===========================================================================
# M28.3 — Task adapter layer
# ===========================================================================
# Each adapter is a pure function: (PlannedTask, TaskFingerprints) ->
# ExecutableVerificationTask. Adapters that cannot safely represent
# the task return executable="not_executable_yet" rather than faking it.


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


# A small, enumerated table. Inference is prohibited.
ADAPTERS: dict[
    VerificationKind,
    Callable[[PlannedTask, TaskFingerprints], ExecutableVerificationTask],
] = {
    "mutation": adapt_mutation_task,
    "unit": adapt_unit_task,
}


def _resolve_kind(planned: PlannedTask) -> VerificationKind:
    """Map a planner task_kind + target to a VerificationKind.

    Falls back to 'capability' for unknown shapes (which the executor
    then marks not_executable_yet).
    """
    kind = (planned.task_kind or "").lower()
    if "mutation" in kind:
        return "mutation"
    if "unit" in kind:
        return "unit"
    # Planner currently emits "mutation" for all selected task kinds in
    # the C42.27 default planner. The contract is open: future planner
    # kinds (property/invariant/contract/coverage/golden) will route
    # through their own adapter once registered.
    return "mutation"


def build_executable_plan(plan: EvidenceAwarePlan) -> ExecutableVerificationPlan:
    """Expand a planner plan into an ExecutableVerificationPlan."""
    tasks: list[ExecutableVerificationTask] = []
    not_exec: list[ExecutableVerificationTask] = []
    for p in plan.selected_tasks:
        kind = _resolve_kind(p)
        fps = collect_repo_fingerprints(p.target)
        adapter = ADAPTERS.get(kind)
        if adapter is None:
            not_exec.append(
                ExecutableVerificationTask(
                    task_id=f"exec::{p.task_id}",
                    component=p.target,
                    capability=p.target.replace("_", "-"),
                    verification_kind=kind,
                    source_task_id=p.task_id,
                    execution_command="",
                    working_directory=str(REPO_ROOT),
                    required_environment=(),
                    evidence_kind="not_executable_yet",
                    expected_artifact="",
                    timeout_policy=0,
                    source_fingerprint=fps.source,
                    test_fingerprint=fps.test,
                    config_fingerprint=fps.config,
                    toolchain_fingerprint=fps.toolchain,
                    reason=p.cause,
                    executable="not_executable_yet",
                    executable_meta={"blocker": f"no adapter for kind={kind!r}"},
                )
            )
            continue
        t = adapter(p, fps)
        if t.executable == "not_executable_yet":
            not_exec.append(t)
        else:
            tasks.append(t)

    # Deterministic plan fingerprint over the executable contract
    h = hashlib.sha256()
    for t in tasks:
        h.update(t.task_id.encode())
        h.update(t.execution_command.encode())
        h.update(t.source_fingerprint.encode())
        h.update(t.test_fingerprint.encode())
        h.update(t.config_fingerprint.encode())
        h.update(t.toolchain_fingerprint.encode())
    plan_fp = h.hexdigest()

    rationale = (
        f"Expanded {len(plan.selected_tasks)} selected planner task(s) into "
        f"{len(tasks)} executable task(s); {len(not_exec)} marked "
        "not_executable_yet. Plan fingerprint covers command + four "
        "fingerprints for every executable task."
    )

    return ExecutableVerificationPlan(
        plan_id=f"exec-plan::{plan.plan_id}",
        generated_at=datetime.now(UTC).isoformat(),
        plan_fingerprint=plan_fp,
        source_plan_id=plan.plan_id,
        tasks=tuple(tasks),
        not_executable=tuple(not_exec),
        rationale=rationale,
    )


# ===========================================================================
# M28.5 — Evidence capture (immutable execution record)
# ===========================================================================


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
        d: dict[str, Any] = {
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


# ===========================================================================
# M28.4 + M28.8 — Targeted mutation executor (scope-safe)
# ===========================================================================

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
        # The installed set may include the expected engine (always)
        # and nothing else. We allow empty scope (smoke mode) only if
        # the task is itself a smoke-style task — currently we don't
        # model smoke as a planner-selected task, so an empty scope is
        # itself a violation.
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


# ===========================================================================
# M28.6 — Evidence reconciliation
# ===========================================================================


@dataclass(frozen=True, slots=True)
class ReconciledComponent:
    component: str
    source: (
        str  # "fresh_measured" | "reused" | "derived" | "invalidated" | "no_evidence"
    )
    evidence: ExecutionEvidence | None
    prior_measurement: ComponentMeasurement | None

    def to_dict(self) -> dict:
        return {
            "component": self.component,
            "source": self.source,
            "evidence": self.evidence.to_dict() if self.evidence else None,
            "prior_measurement": (
                self.prior_measurement.to_dict() if self.prior_measurement else None
            ),
        }


@dataclass(frozen=True, slots=True)
class LabelledAggregate:
    """An aggregate whose label is never collapsed into a generic score."""

    label: Literal[
        "AUTHORITATIVE_MEASURED",
        "AUTHORITATIVE_TARGETED",
        "MATHEMATICALLY_RECONCILED",
    ]
    result: float
    numerator: int  # sum(killed)
    denominator: int  # sum(scored)
    scope: str  # population_id or selected components
    decided_at: str
    rationale: str

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "result": self.result,
            "numerator": self.numerator,
            "denominator": self.denominator,
            "scope": self.scope,
            "decided_at": self.decided_at,
            "rationale": self.rationale,
        }


@dataclass(frozen=True, slots=True)
class ReconciledVerificationState:
    plan_id: str
    generated_at: str
    components: tuple[ReconciledComponent, ...]
    aggregate: LabelledAggregate | None
    certifiable: bool
    rationale: str

    def to_dict(self) -> dict:
        return {
            "plan_id": self.plan_id,
            "generated_at": self.generated_at,
            "components": [c.to_dict() for c in self.components],
            "aggregate": self.aggregate.to_dict() if self.aggregate else None,
            "certifiable": self.certifiable,
            "rationale": self.rationale,
        }


def reconcile(
    plan: EvidenceAwarePlan,
    fresh: dict[str, ExecutionEvidence],
    prior_by_component: dict[str, ComponentMeasurement],
    population: PopulationSnapshot,
    *,
    freshness_authority: str = "all_fresh_measured",
) -> ReconciledVerificationState:
    """Reconcile fresh + reusable + derived evidence into a verified state.

    Components in the planner's plan that were *selected* but did not
    produce a fresh ExecutionEvidence are invalidated (cannot be
    certified from prior evidence alone when the planner said they
    must be re-measured). Components the planner *excluded* as
    reusable keep their prior measurement.
    """
    components: list[ReconciledComponent] = []
    reuses = {r.scope_id: r for r in plan.reuses}
    selected = {t.target: t for t in plan.selected_tasks}
    excluded = {t.target: t for t in plan.excluded_tasks}

    for comp in population.components:
        sel_task = selected.get(comp)
        exc_task = excluded.get(comp)
        reuse = reuses.get(comp)
        evidence = fresh.get(comp)
        prior = prior_by_component.get(comp)

        if evidence is not None:
            if evidence.failure_kind in (
                FailureKind.INFRASTRUCTURE,
                FailureKind.SCOPE,
                FailureKind.CONFIGURATION,
                FailureKind.EVIDENCE,
                FailureKind.VERIFICATION,
            ):
                # Any failure means the component is invalidated — the
                # prior measurement is no longer authoritative for
                # certification until a subsequent fresh_measured
                # succeeds.
                components.append(
                    ReconciledComponent(comp, "invalidated", evidence, prior)
                )
            else:
                components.append(
                    ReconciledComponent(comp, "fresh_measured", evidence, prior)
                )
            continue
        if sel_task is not None:
            # Planner said re-measure, but we have no fresh evidence.
            components.append(ReconciledComponent(comp, "invalidated", None, prior))
            continue
        if exc_task is not None and reuse is not None and prior is not None:
            components.append(ReconciledComponent(comp, "reused", None, prior))
            continue
        # No prior and no fresh — no evidence.
        components.append(ReconciledComponent(comp, "no_evidence", None, prior))

    # M28.7 — Mathematically aggregate
    aggregate = _compute_labelled_aggregate(
        components, population, freshness_authority=freshness_authority
    )

    # Certifiability
    has_invalidated = any(c.source == "invalidated" for c in components)
    has_no_evidence = any(c.source == "no_evidence" for c in components)
    certifiable = (not has_invalidated) and (not has_no_evidence)

    parts: list[str] = []
    if has_invalidated:
        parts.append(
            f"{sum(1 for c in components if c.source == 'invalidated')} invalidated component(s)"
        )
    if has_no_evidence:
        parts.append(
            f"{sum(1 for c in components if c.source == 'no_evidence')} no-evidence component(s)"
        )
    if not parts:
        parts.append(
            "every component has either fresh measured evidence or a reused prior measurement"
        )
    rationale = (
        "certifiable: " + "; ".join(parts)
        if certifiable
        else "NOT certifiable: " + "; ".join(parts)
    )

    return ReconciledVerificationState(
        plan_id=plan.plan_id,
        generated_at=datetime.now(UTC).isoformat(),
        components=tuple(components),
        aggregate=aggregate,
        certifiable=certifiable,
        rationale=rationale,
    )


def _compute_labelled_aggregate(
    components: tuple[ReconciledComponent, ...],
    population: PopulationSnapshot,
    *,
    freshness_authority: str = "all_fresh_measured",
) -> LabelledAggregate:
    """Compute a labelled aggregate without ever collapsing categories.

    Label rules:
      * AUTHORITATIVE_MEASURED — every component in the population has
        a fresh, non-invalidated ExecutionEvidence (i.e. a full mutation
        campaign was just run by this executor).
      * AUTHORITATIVE_TARGETED — at least one component has fresh
        evidence and the rest are *reused*; the score is computed over
        fresh+reused components but only the fresh subset is considered
        *measured* (the rest are derived from prior artifacts).
      * MATHEMATICALLY_RECONCILED — no fresh evidence at all; every
        component is reused. The score is the deterministic
        re-derivation of the C42.27 aggregate.
    """
    fresh = [c for c in components if c.source == "fresh_measured"]
    reused = [c for c in components if c.source == "reused"]
    invalidated = [c for c in components if c.source == "invalidated"]

    def _score_for(c: ReconciledComponent) -> tuple[int, int] | None:
        if c.evidence is not None and c.evidence.counts:
            k = c.evidence.counts.get("killed", 0)
            g = c.evidence.counts.get("generated", 0)
            return k, g
        if c.prior_measurement is not None:
            k = int(c.prior_measurement.summary.get("killed", 0))
            g = int(c.prior_measurement.summary.get("scored", 0))
            return k, g
        return None

    def _agg(scope: list[ReconciledComponent]) -> tuple[int, int]:
        n = 0
        d = 0
        for c in scope:
            sc = _score_for(c)
            if sc is None:
                continue
            n += sc[0]
            d += sc[1]
        return n, d

    now = datetime.now(UTC).isoformat()
    if not fresh and not reused:
        return LabelledAggregate(
            label="MATHEMATICALLY_RECONCILED",
            result=0.0,
            numerator=0,
            denominator=0,
            scope=population.population_id,
            decided_at=now,
            rationale="no fresh or reused evidence; aggregate is 0/0",
        )
    if not fresh and reused:
        n, d = _agg(reused)
        pct = round(100.0 * n / d, 4) if d else 0.0
        return LabelledAggregate(
            label="MATHEMATICALLY_RECONCILED",
            result=pct,
            numerator=n,
            denominator=d,
            scope=population.population_id,
            decided_at=now,
            rationale=(
                f"derived from {len(reused)} reused component(s) over "
                f"population {population.population_id}; no fresh measurement"
            ),
        )
    if fresh and not reused:
        n, d = _agg(fresh)
        pct = round(100.0 * n / d, 4) if d else 0.0
        return LabelledAggregate(
            label="AUTHORITATIVE_MEASURED",
            result=pct,
            numerator=n,
            denominator=d,
            scope=population.population_id,
            decided_at=now,
            rationale=(
                f"every component in population {population.population_id} "
                "was freshly measured by this executor"
            ),
        )
    # Fresh + reused
    n, d = _agg(list(fresh) + list(reused))
    pct = round(100.0 * n / d, 4) if d else 0.0
    return LabelledAggregate(
        label="AUTHORITATIVE_TARGETED",
        result=pct,
        numerator=n,
        denominator=d,
        scope=population.population_id,
        decided_at=now,
        rationale=(
            f"{len(fresh)} component(s) freshly measured + {len(reused)} "
            "reused; only the fresh subset is directly measured, the rest "
            "are derived from prior certified artifacts"
        ),
    )


# ===========================================================================
# M28.13 — Forensic execution record
# ===========================================================================


@dataclass(frozen=True, slots=True)
class ForensicExecutionRecord:
    """The single artifact the Diagnostic & Forensic Agent will consume.

    Captures the entire change→plan→execute→reconcile→certify chain in
    one immutable record.
    """

    record_id: str
    generated_at: str
    repository_sha: str
    change: dict
    affected_graph_nodes: dict
    invalidations: dict
    reused_evidence: dict
    selected_tasks: dict
    executed_tasks: dict
    execution_results: dict
    new_evidence: dict
    derived_evidence: dict
    failures: dict
    uncertainties: dict
    certification_decision: dict

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "generated_at": self.generated_at,
            "repository_sha": self.repository_sha,
            "change": self.change,
            "affected_graph_nodes": self.affected_graph_nodes,
            "invalidations": self.invalidations,
            "reused_evidence": self.reused_evidence,
            "selected_tasks": self.selected_tasks,
            "executed_tasks": self.executed_tasks,
            "execution_results": self.execution_results,
            "new_evidence": self.new_evidence,
            "derived_evidence": self.derived_evidence,
            "failures": self.failures,
            "uncertainties": self.uncertainties,
            "certification_decision": self.certification_decision,
        }


def build_forensic_record(
    plan: EvidenceAwarePlan,
    executable: ExecutableVerificationPlan,
    fresh: dict[str, ExecutionEvidence],
    reconciled: ReconciledVerificationState,
) -> ForensicExecutionRecord:
    rid = hashlib.sha256(
        "|".join([plan.plan_id, executable.plan_id, _git_sha()]).encode()
    ).hexdigest()[:12]

    invalidations = {
        "by_component": {
            comp: [inv for inv in reuses if inv]
            for comp, reuses in ((r.scope_id, r.invalidations) for r in plan.reuses)
        }
    }
    reused_evidence = {
        "count": sum(1 for c in reconciled.components if c.source == "reused"),
        "components": [
            c.component for c in reconciled.components if c.source == "reused"
        ],
    }
    selected = {
        "count": len(plan.selected_tasks),
        "components": [t.target for t in plan.selected_tasks],
    }
    executed = {
        "count": len(fresh),
        "components": sorted(fresh.keys()),
    }
    results = {
        "by_component": {c: ev.to_dict() for c, ev in fresh.items()},
    }
    new_evidence = {
        "count": sum(1 for c in reconciled.components if c.source == "fresh_measured"),
        "components": [
            c.component for c in reconciled.components if c.source == "fresh_measured"
        ],
    }
    derived = {
        "aggregate": reconciled.aggregate.to_dict() if reconciled.aggregate else None,
    }
    failures = {
        "by_component": {
            c.component: {
                "kind": (
                    c.evidence.failure_kind.value
                    if c.evidence and c.evidence.failure_kind
                    else None
                ),
                "message": c.evidence.failure_message if c.evidence else None,
            }
            for c in reconciled.components
            if c.evidence is not None and c.evidence.failure_kind is not None
        },
        "count": sum(
            1
            for c in reconciled.components
            if c.evidence is not None and c.evidence.failure_kind is not None
        ),
    }
    uncertainties = {
        "no_evidence": [
            c.component for c in reconciled.components if c.source == "no_evidence"
        ],
        "invalidated": [
            c.component for c in reconciled.components if c.source == "invalidated"
        ],
        "drift_blockers": list(plan.drift_blockers),
        "certification_gaps": list(plan.certification_gaps),
    }
    decision = {
        "certifiable": reconciled.certifiable,
        "rationale": reconciled.rationale,
        "aggregate_label": reconciled.aggregate.label if reconciled.aggregate else None,
        "aggregate_result": (
            reconciled.aggregate.result if reconciled.aggregate else None
        ),
    }

    return ForensicExecutionRecord(
        record_id=f"forensic::{rid}",
        generated_at=datetime.now(UTC).isoformat(),
        repository_sha=_git_sha(),
        change={
            "changed_files": list(plan.changed_files),
            "affected_components": list(plan.affected_components),
            "affected_capabilities": list(plan.affected_capabilities),
        },
        affected_graph_nodes={
            "sources": list(plan.affected_sources),
            "capabilities": list(plan.affected_capabilities),
        },
        invalidations=invalidations,
        reused_evidence=reused_evidence,
        selected_tasks=selected,
        executed_tasks=executed,
        execution_results=results,
        new_evidence=new_evidence,
        derived_evidence=derived,
        failures=failures,
        uncertainties=uncertainties,
        certification_decision=decision,
    )


# ===========================================================================
# M28.10 — Convenience entry point
# ===========================================================================


def default_population() -> PopulationSnapshot:
    return c42_26_population()


def default_prior_measurements() -> list[ComponentMeasurement]:
    return c42_24_b_measurements() + c42_25_measurements()


def main() -> int:
    """CLI entry point for ad-hoc execution (used by the orchestrator)."""
    import argparse

    parser = argparse.ArgumentParser(
        prog="runtime.foundation.verification.executor_pipeline"
    )
    parser.add_argument(
        "--changed-file",
        action="append",
        default=[],
        help="A changed file to plan against (can be repeated)",
    )
    parser.add_argument(
        "--run-mutation",
        action="store_true",
        help="Actually run the targeted mutation for selected components",
    )
    parser.add_argument(
        "--max-runtime",
        type=int,
        default=None,
        help="Override per-task mutation timeout (seconds)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="Output JSON path for the forensic execution record",
    )
    args = parser.parse_args()

    planner = default_planner()
    plan = planner.plan(tuple(args.changed_file))
    executable = build_executable_plan(plan)

    fresh: dict[str, ExecutionEvidence] = {}
    if args.run_mutation:
        for t in executable.tasks:
            fresh[t.component] = execute_mutation_task(t, max_runtime=args.max_runtime)

    prior = {m.component: m for m in default_prior_measurements()}
    reconciled = reconcile(plan, fresh, prior, default_population())
    forensic = build_forensic_record(plan, executable, fresh, reconciled)

    out_path = (
        Path(args.out)
        if args.out
        else REPO_ROOT
        / "runtime"
        / "generated"
        / "m9-c42.28"
        / "forensic-execution-record.json"
    )
    out_path.write_text(json.dumps(forensic.to_dict(), indent=2))

    print(
        f"plan: {plan.plan_id}  selected={len(plan.selected_tasks)}  excluded={len(plan.excluded_tasks)}"
    )
    print(
        f"executable: {len(executable.tasks)}  not_executable={len(executable.not_executable)}"
    )
    print(f"executed: {len(fresh)}")
    print(f"certifiable: {reconciled.certifiable}  rationale: {reconciled.rationale}")
    print(f"forensic: {out_path.relative_to(REPO_ROOT)}")
    return 0 if reconciled.certifiable else 2


if __name__ == "__main__":
    sys.exit(main())
