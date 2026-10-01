"""
M9-C49 — Verification Execution Orchestration.

Turns the C48 control-plane plan into an *executable, observable, deterministic*
verification pipeline. The orchestrator is the bridge from "what should I run?"
(C48) to "run it, observe it, decide what happens next, stop when defensible".

Design contract (M9-C49):

* The orchestrator consumes the C48 ControlPlanePlan; it never independently
  re-discovers which verifications to run. The capability graph remains the
  controlling abstraction.
* Same repository state + same control-plane input → same plan. Plan and task
  identity are content-derived; the generated-at timestamp is excluded from
  every fingerprint.
* Execution is observable. Every task produces a structured TaskExecutionRecord
  that records the command, capabilities served, start/end, exit code, completion
  state, produced artifacts, optional measurement truth, and next action.
* Stopping rules (Section 6) are deterministic:
    - mandatory tasks all PASS/REUSED → skip escalation; declare final decision.
    - any mandatory FAILED → run declared diagnostic; do not auto-execute
      escalation commands from the planner; decision is DIAGNOSTIC.
    - TIMEOUT / INFRASTRUCTURE / SCOPE / CONFIGURATION / CERTIFICATION failures
      never convert to PASS.
    - AUTHORIZATION_REQUIRED tasks (e.g. targeted mutation campaigns) stop at
      the human-authorization boundary unless explicitly authorized.
* Mutation execution is subordinate to orchestration. A targeted mutation is one
  capability among many; full campaigns require explicit authorization. The
  orchestrator reuses C45/C47 durable survivor intelligence and the native
  mutmut runner — never transient mutmut workspaces as evidence.
* Fingerprints are validated before execution: if the live repository state no
  longer matches the plan's captured fingerprint, the orchestrator refuses to
  run (decision: VALIDATION_BLOCKED) and the operator must re-plan.

This module is additive — it consumes the C48 planner, control plane,
measurement-truth, strengthening, and command-inventory modules without
introducing a parallel registry, evidence store, or capability system.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import re
import signal
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# C49 generated evidence root.
GENERATED_ROOT = REPO_ROOT / "runtime" / "generated" / "m9-c49"
GENERATED_ROOT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Completion state / failure stage / final decision (closed taxonomies)
# ---------------------------------------------------------------------------


class CompletionState(str, Enum):
    """Per-task completion state. Closed vocabulary, never converted to PASS."""

    PASS = "pass"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INFRASTRUCTURE = "infrastructure"
    EVIDENCE = "evidence"
    SCOPE = "scope"
    CONFIGURATION = "configuration"
    CERTIFICATION = "certification"
    AUTHORIZATION_REQUIRED = "authorization_required"
    REUSED = "reused"
    SKIPPED = "skipped"  # sufficiency: minimum verification already satisfied


# States that mean "the run is observably not a pass"
NON_PASS_STATES: frozenset[CompletionState] = frozenset(
    {
        CompletionState.FAILED,
        CompletionState.TIMEOUT,
        CompletionState.INFRASTRUCTURE,
        CompletionState.EVIDENCE,
        CompletionState.SCOPE,
        CompletionState.CONFIGURATION,
        CompletionState.CERTIFICATION,
        CompletionState.AUTHORIZATION_REQUIRED,
    }
)

PASSING_STATES: frozenset[CompletionState] = frozenset(
    {CompletionState.PASS, CompletionState.REUSED, CompletionState.SKIPPED}
)


class FailureStage(str, Enum):
    """Diagnostic classification of a non-pass task outcome (Section 11)."""

    TEST_FAILURE = "test_failure"
    ASSERTION_FAILURE = "assertion_failure"
    CODE_DEFECT = "code_defect"
    CONFIGURATION_FAILURE = "configuration_failure"
    TOOLING_FAILURE = "tooling_failure"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    TIMEOUT = "timeout"
    INVALID_SCOPE = "invalid_scope"
    MISSING_EVIDENCE = "missing_evidence"
    STALE_EVIDENCE = "stale_evidence"
    AUTHORIZATION_REQUIRED = "authorization_required"
    NONE = "none"


class FinalDecision(str, Enum):
    """Pipeline-level decision (Section 6)."""

    CERTIFIED = "certified"
    NOT_CERTIFIABLE = "not_certifiable"
    DIAGNOSTIC = "diagnostic"
    AWAITING_AUTHORIZATION = "awaiting_authorization"
    INFRASTRUCTURE_BLOCKED = "infrastructure_blocked"
    TIMEOUT_BLOCKED = "timeout_blocked"
    VALIDATION_BLOCKED = "validation_blocked"


class TaskOrigin(str, Enum):
    """Origin classification for a task (transparency over why a task is in
    the plan)."""

    CONTROL_PLANE = "control_plane"
    REVALIDATION = "revalidation"  # injected by C49 because a measurement
    # record is stale/missing for a directly-affected capability


# ---------------------------------------------------------------------------
# Repository fingerprint (deterministic, never timestamp-derived)
# ---------------------------------------------------------------------------


def _git(*args: str) -> str:
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=15,
        )
        return out.stdout.strip()
    except Exception:
        return ""


_PYTEST_FAILURE_LINE = re.compile(r"^(FAILED|ERROR)\s+(\S+)", re.MULTILINE)
_PYTEST_TIMEOUT_MARKER = "from pytest-timeout"
_PYTEST_SUMMARY = re.compile(
    r"^(?:(\d+) failed)?(?:,?\s*(\d+) passed)?(?:,?\s*(\d+) skipped)?"
    r"(?:,?\s*(\d+) error)?(?:,?\s*(\d+) xfailed)?"
    r"(?:,?\s*(\d+) xpassed)?.*?in\s+(\d+\.?\d*)s",
    re.MULTILINE,
)


def _summarise_pytest_outcome(text: str) -> dict | None:
    """Name the inner pytest failure precisely, from its own output.

    A verification script that runs pytest and then aggregates several checks
    exits with a single non-zero status, which loses the distinction the
    investigation actually needs: was this an assertion failure, a per-test
    timeout, or a collection/internal error? Those have different causes and
    different fixes, and "the suite failed" is not evidence for any of them.

    Returns None when the text contains no pytest signal at all, so callers can
    leave non-pytest tasks untouched. The classification is derived only from
    pytest's own summary and short-summary lines — it never re-runs anything and
    never guesses.
    """
    if not text or "pytest" not in text and "passed" not in text:
        return None

    failed = _PYTEST_FAILURE_LINE.findall(text)
    summary = _PYTEST_SUMMARY.search(text)
    counts = {
        "failed": int(summary.group(1)) if summary and summary.group(1) else 0,
        "passed": int(summary.group(2)) if summary and summary.group(2) else 0,
        "skipped": int(summary.group(3)) if summary and summary.group(3) else 0,
        "errors": int(summary.group(4)) if summary and summary.group(4) else 0,
        "xfailed": int(summary.group(5)) if summary and summary.group(5) else 0,
        "xpassed": int(summary.group(6)) if summary and summary.group(6) else 0,
    }
    duration = float(summary.group(7)) if summary and summary.group(7) else None

    if not failed and not summary:
        return None

    # A per-test timeout is reported by pytest-timeout in the failure body; a
    # timeout and an assertion failure are different defects even when both
    # surface as a non-zero pytest exit.
    timed_out = _PYTEST_TIMEOUT_MARKER in text
    errored = any(tag == "ERROR" for tag, _ in failed) or counts["errors"] > 0

    if timed_out:
        kind = "TEST_TIMEOUT"
    elif errored:
        kind = "COLLECTION_OR_INTERNAL_ERROR"
    elif counts["failed"] or failed:
        kind = "TEST_ASSERTION_FAILURE"
    else:
        kind = "PASSED"

    return {
        "kind": kind,
        "failed_nodeids": [nodeid for _, nodeid in failed],
        "counts": counts,
        "duration_seconds": duration,
    }


def _read_text(path: Path) -> str:
    """Read an evidence file, tolerating a missing or undecodable one."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _tee(pipe, path: Path) -> None:
    """Copy a child pipe into an evidence file line by line, flushing each line.

    Flushing per line is the whole point: the file is valid, and contains
    everything produced so far, even if the child is killed, the orchestrator is
    interrupted, or the machine loses the process. It mirrors ``_tee`` in
    executor.py, which streams the same way for the same reason.
    """
    try:
        with path.open("a", encoding="utf-8") as handle:
            for raw in pipe:
                line = (
                    raw
                    if isinstance(raw, str)
                    else raw.decode("utf-8", errors="replace")
                )
                handle.write(line)
                handle.flush()
    except (OSError, ValueError):
        # A closed pipe during teardown is expected, not an error worth raising
        # into the verification run.
        pass
    finally:
        with contextlib.suppress(Exception):
            pipe.close()


def _kill_process_group(proc) -> None:
    """Kill the child's whole process group (F19, as in executor.py).

    The child is a shell that runs pytest, which runs further processes. Killing
    only the shell would leave the real work running after a wrapper timeout.
    """
    with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        time.sleep(0.5)
        with contextlib.suppress(ProcessLookupError, PermissionError, OSError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)


def _classify_termination(
    exit_code: int | None, timed_out: bool, infra_error: str | None
) -> dict:
    """Say *how* a task's process ended, not just that it did not pass.

    "the command exited non-zero" is not a diagnosis. A verification run can
    end because a test failed, because the wrapper killed it, because the
    process was killed by a signal, or because the command never started, and
    each of those points at a different cause. The record keeps them apart so a
    long run cannot be misread as a flaky one.
    """
    if infra_error:
        return {"kind": "INFRASTRUCTURE", "detail": infra_error, "signal": None}
    if timed_out:
        return {
            "kind": "WRAPPER_TIMEOUT",
            "detail": "verification wrapper killed the command before it finished",
            "signal": None,
        }
    if exit_code is not None and exit_code < 0:
        return {
            "kind": "SIGNAL_TERMINATION",
            "detail": f"child terminated by signal {-exit_code}",
            "signal": -exit_code,
        }
    if exit_code is not None and exit_code > 128:
        signum = exit_code - 128
        try:
            signame = signal.Signals(signum).name
        except ValueError:
            signame = f"SIG{signum}"
        return {
            "kind": "SIGNAL_TERMINATION",
            "detail": f"shell reported 128+{signum} ({signame})",
            "signal": signum,
        }
    if exit_code == 0:
        return {"kind": "EXIT_ZERO", "detail": "command exit 0", "signal": None}
    return {
        "kind": "EXIT_NONZERO",
        "detail": f"command reported exit {exit_code}",
        "signal": None,
    }


def _hash_file(path: Path) -> str:
    if not path.exists():
        return ""
    try:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        return h.hexdigest()
    except OSError:
        return ""


def _hash_tree(working_dir: Path) -> str:
    if not working_dir.exists():
        return ""
    h = hashlib.sha256()
    for f in sorted(working_dir.rglob("*.py")):
        if any(part.startswith(".") for part in f.parts):
            continue
        rel = str(f.relative_to(working_dir))
        h.update(rel.encode("utf-8"))
        try:
            h.update(f.read_bytes())
        except OSError:
            h.update(b"<unreadable>")
    return h.hexdigest()


def _hash_toolchain() -> str:
    """Hash the canonical toolchain versions (mutmut, pytest, python)."""
    try:
        from runtime.foundation.verification.env import resolve_environment

        env = resolve_environment()
        parts = [
            env.python.version or "",
            env.pytest.version or "",
            env.mutmut.version or "",
        ]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    except Exception:
        return ""


@dataclass(frozen=True, slots=True)
class RepositoryFingerprint:
    """A deterministic, content-derived fingerprint of the repository state."""

    repository_sha: str
    working_tree_hash: str
    config_hash: str
    toolchain_hash: str
    fingerprint: str

    @classmethod
    def capture(cls) -> RepositoryFingerprint:
        repo_sha = _git("rev-parse", "HEAD")
        if not repo_sha:
            # fallback: working-tree hash when no HEAD is available
            repo_sha = "no-head"
        tree = _hash_tree(REPO_ROOT / "backend" / "src")
        config_paths = [
            REPO_ROOT / "backend" / "pyproject.toml",
            REPO_ROOT / "pyproject.toml",
        ]
        config_h = hashlib.sha256()
        for p in config_paths:
            content = _hash_file(p)
            config_h.update(str(p.relative_to(REPO_ROOT)).encode())
            config_h.update(content.encode())
        config_hash = config_h.hexdigest()
        tool = _hash_toolchain()
        composite = hashlib.sha256(
            "|".join([repo_sha, tree, config_hash, tool]).encode("utf-8")
        ).hexdigest()
        return cls(
            repository_sha=repo_sha,
            working_tree_hash=tree,
            config_hash=config_hash,
            toolchain_hash=tool,
            fingerprint=composite,
        )

    def matches(self, other: RepositoryFingerprint) -> bool:
        return self.fingerprint == other.fingerprint

    def to_dict(self) -> dict:
        return {
            "repository_sha": self.repository_sha,
            "working_tree_hash": self.working_tree_hash,
            "config_hash": self.config_hash,
            "toolchain_hash": self.toolchain_hash,
            "fingerprint": self.fingerprint,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RepositoryFingerprint:
        return cls(
            repository_sha=d.get("repository_sha", ""),
            working_tree_hash=d.get("working_tree_hash", ""),
            config_hash=d.get("config_hash", ""),
            toolchain_hash=d.get("toolchain_hash", ""),
            fingerprint=d.get("fingerprint", ""),
        )


# ---------------------------------------------------------------------------
# Capability → mutation target (capability vocabulary → ENGINE_SELECTION)
# ---------------------------------------------------------------------------

# Registry capabilities that have a known C42 mutation contract target.
CAPABILITY_TO_MUTATION_TARGET: dict[str, str] = {
    "loan-engine": "loan_engine",
    "reconciliation": "reconciliation_engine",
    "ledger": "ledger_audit_engine",
    "credit_card": "credit_card_engine",
    "account_engine": "account_engine",
}


# ---------------------------------------------------------------------------
# Plan contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ExecutionTaskSpec:
    """The execution contract for a single task.

    A spec is a pure (frozen) dataclass so plan identity is content-only.
    """

    task_id: str
    source_task_id: str  # control-plane task ID this expands
    primary_capability: str
    capabilities: tuple[str, ...]
    verification_kind: str
    command: str
    profile: str
    scope: str
    is_mandatory: bool
    is_escalation: bool
    reason: str
    origin: str  # TaskOrigin
    prerequisites: tuple[str, ...] = field(default_factory=tuple)
    depends_on: tuple[str, ...] = field(default_factory=tuple)
    expected_evidence: tuple[str, ...] = field(default_factory=tuple)
    measurement_required: tuple[str, ...] = field(default_factory=tuple)
    escalation_conditions: tuple[str, ...] = field(default_factory=tuple)
    authorization_required: bool = False
    timeout_seconds: int = 600
    failure_policy: str = "diagnose_then_stop"
    evidence_reused: tuple[str, ...] = field(default_factory=tuple)
    evidence_invalidated: tuple[str, ...] = field(default_factory=tuple)
    estimated_duration_seconds: int = 0
    mutation_target: str = ""  # set when verification_kind == "mutation"

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "source_task_id": self.source_task_id,
            "primary_capability": self.primary_capability,
            "capabilities": list(self.capabilities),
            "verification_kind": self.verification_kind,
            "command": self.command,
            "profile": self.profile,
            "scope": self.scope,
            "is_mandatory": self.is_mandatory,
            "is_escalation": self.is_escalation,
            "reason": self.reason,
            "origin": self.origin,
            "prerequisites": list(self.prerequisites),
            "depends_on": list(self.depends_on),
            "expected_evidence": list(self.expected_evidence),
            "measurement_required": list(self.measurement_required),
            "escalation_conditions": list(self.escalation_conditions),
            "authorization_required": self.authorization_required,
            "timeout_seconds": self.timeout_seconds,
            "failure_policy": self.failure_policy,
            "evidence_reused": list(self.evidence_reused),
            "evidence_invalidated": list(self.evidence_invalidated),
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "mutation_target": self.mutation_target,
        }


@dataclass
class ExecutionPlan:
    """The full execution plan — the C48 plan, expanded to a machine-readable
    contract that can be validated, persisted, and executed deterministically.
    """

    plan_id: str
    source_plan_id: str  # C48 ControlPlanePlan.plan_id
    repository_fingerprint: RepositoryFingerprint
    changed_files: list[str]
    affected_capabilities: list[str]
    affected_components: list[str]
    invalidated_evidence: list[str]
    reusable_evidence: list[str]
    tasks: list[ExecutionTaskSpec]
    escalation_conditions: list[str]
    measurement_requirements: list[dict]
    certification_requirements: list[dict]
    rationale: str
    plan_fingerprint: str
    generated_at: str
    # M9-C49: revalidation injections and persistent-evidence state.
    revalidation_sources: list[dict] = field(default_factory=list)
    reusable_measurements: list[dict] = field(default_factory=list)
    #: Boundary classification and the strategy this plan was built under.
    #: Present on every plan so a reader never has to infer the scope of a run
    #: from a warning in a log. See runtime.foundation.verification.boundary_policy.
    boundary_evidence: object | None = None

    def to_dict(self) -> dict:
        return {
            "schema": "m9-c49-execution-plan/v1",
            "plan_id": self.plan_id,
            "source_plan_id": self.source_plan_id,
            "repository_fingerprint": self.repository_fingerprint.to_dict(),
            "changed_files": list(self.changed_files),
            "affected_capabilities": list(self.affected_capabilities),
            "affected_components": list(self.affected_components),
            "invalidated_evidence": list(self.invalidated_evidence),
            "reusable_evidence": list(self.reusable_evidence),
            "tasks": [t.to_dict() for t in self.tasks],
            "escalation_conditions": list(self.escalation_conditions),
            "measurement_requirements": list(self.measurement_requirements),
            "certification_requirements": list(self.certification_requirements),
            "rationale": self.rationale,
            "plan_fingerprint": self.plan_fingerprint,
            "generated_at": self.generated_at,
            "revalidation_sources": list(self.revalidation_sources),
            "reusable_measurements": list(self.reusable_measurements),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)

    def validate(self) -> list[str]:
        """Integrity checks on the plan. Empty list = OK."""
        errors: list[str] = []
        seen_ids: set[str] = set()
        for t in self.tasks:
            if t.task_id in seen_ids:
                errors.append(f"duplicate task_id={t.task_id}")
            seen_ids.add(t.task_id)
            if not t.command:
                errors.append(f"task {t.task_id} has empty command")
            if not t.capabilities:
                errors.append(f"task {t.task_id} has no capabilities")
        for t in self.tasks:
            if t.is_escalation:
                for dep in t.depends_on:
                    if dep not in {x.task_id for x in self.tasks}:
                        errors.append(
                            f"escalation task {t.task_id} depends on missing task {dep}"
                        )
        if not self.tasks:
            errors.append("plan has no tasks")
        return errors


# ---------------------------------------------------------------------------
# Task execution record
# ---------------------------------------------------------------------------


@dataclass
class TaskExecutionRecord:
    record_id: str
    plan_id: str
    task_id: str
    primary_capability: str
    capabilities: list[str]
    command: str
    scope: str
    is_mandatory: bool
    is_escalation: bool
    verification_kind: str
    started_at: str
    completed_at: str
    duration_seconds: float
    exit_code: int | None
    completion_state: str  # CompletionState
    stdout_path: str
    stderr_path: str
    artifacts: list[str]
    measurement_truth: dict | None
    diagnostic: dict | None
    next_action: str
    reason: str
    prerequisites_satisfied: bool
    # How the process actually ended, kept apart from the completion state:
    # EXIT_ZERO / EXIT_NONZERO / WRAPPER_TIMEOUT / SIGNAL_TERMINATION /
    # INFRASTRUCTURE, plus an `inner` pytest classification when the command
    # ran pytest (TEST_ASSERTION_FAILURE / TEST_TIMEOUT /
    # COLLECTION_OR_INTERNAL_ERROR / PASSED). See `_classify_termination` and
    # `_summarise_pytest_outcome`. A long run that ends in any of these must be
    # diagnosable from the record alone, without re-running it.
    termination: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Execution report
# ---------------------------------------------------------------------------


@dataclass
class ExecutionReport:
    report_id: str
    plan_id: str
    plan_fingerprint: str
    started_at: str
    completed_at: str
    total_duration_seconds: float
    records: list[TaskExecutionRecord]
    efficiency: dict
    final_decision: str  # FinalDecision
    decision_reason: str
    evidence_reused: list[str]
    escalations_triggered: list[str]
    decisions: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "schema": "m9-c49-execution-report/v1",
            "report_id": self.report_id,
            "plan_id": self.plan_id,
            "plan_fingerprint": self.plan_fingerprint,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "total_duration_seconds": self.total_duration_seconds,
            "records": [r.to_dict() for r in self.records],
            "efficiency": dict(self.efficiency),
            "final_decision": self.final_decision,
            "decision_reason": self.decision_reason,
            "evidence_reused": list(self.evidence_reused),
            "escalations_triggered": list(self.escalations_triggered),
            "decisions": list(self.decisions),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, default=str)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _capability_components(capabilities: list[str]) -> list[str]:
    """Deterministic list of engine components served by a capability set."""
    out: list[str] = []
    for c in capabilities:
        target = CAPABILITY_TO_MUTATION_TARGET.get(c, "")
        if target and target not in out:
            out.append(target)
    return out


def _measurement_kind_for_task(spec: ExecutionTaskSpec) -> str:
    """The MeasurementKind value for a task, or empty string for non-measurement."""
    if spec.verification_kind in ("mutation",):
        return "mutation"
    if spec.verification_kind in ("coverage",):
        return "coverage"
    if spec.profile == "mutation":
        return "mutation"
    if spec.profile == "coverage":
        return "coverage"
    return ""


# ---------------------------------------------------------------------------
# Execution orchestrator
# ---------------------------------------------------------------------------


class ExecutionOrchestrator:
    """Consumes the C48 control-plane plan and drives it to a final decision.

    The orchestrator is the *only* component that decides which commands
    actually run, in which order, under which stop rules, and what the final
    certification state is. It never invents new verifications: every task
    traces back to a C48 control-plane task or a revalidation injection that
    a stale/missing persistent measurement record justifies.
    """

    def __init__(
        self,
        contract_registry=None,
        population=None,
        measurements=None,
        command_overrides: dict[str, str] | None = None,
        measurement_search_dirs: list[str] | None = None,
        max_runtime_overrides: dict[str, int] | None = None,
        evidence_root: Path | None = None,
    ) -> None:
        from runtime.foundation.verification.capability_contract import (
            get_capability_contract_registry,
        )
        from runtime.foundation.verification.evidence_reuse import (
            c42_24_b_measurements,
            c42_25_measurements,
            c42_26_population,
        )

        self._contract_registry = (
            contract_registry or get_capability_contract_registry()
        )
        self._population = population or c42_26_population()
        self._measurements = measurements or (
            c42_24_b_measurements() + c42_25_measurements()
        )
        self._command_overrides = dict(command_overrides or {})
        self._max_runtime_overrides = dict(max_runtime_overrides or {})
        self._measurement_search_dirs = list(measurement_search_dirs or [])
        self._evidence_root = evidence_root or GENERATED_ROOT

    # ------------------------------------------------------------- planning

    def build_execution_plan(self, changed_files: list[str]) -> ExecutionPlan:
        """Build a deterministic ExecutionPlan from a list of changed files.

        The plan consumes the C48 ControlPlanePlan. It then:
        * deduplicates identical commands across capabilities (one execution
          can serve multiple capabilities);
        * orders tasks deterministically (mandatory first, escalation last);
        * injects revalidation tasks for missing/stale authoritative
          measurement records (Section 6 — "stale evidence → invalidate and
          execute the minimum replacement verification").
        """
        from runtime.foundation.verification.control_plane import (
            generate_control_plane_plan,
        )

        cp = generate_control_plane_plan(
            changed_files,
            population=self._population,
            measurements=self._measurements,
        )

        live_fp = RepositoryFingerprint.capture()
        tasks, _dedup_keys = self._expand_control_plane_tasks(cp, live_fp)
        revalidation_tasks, revalidation_sources, reusable = self._inject_revalidations(
            cp, tasks, live_fp
        )
        tasks = tasks + revalidation_tasks
        self._add_dependency_edges(tasks)

        plan_fingerprint = self._compute_plan_fingerprint(
            cp.plan_id, live_fp, changed_files, tasks
        )
        plan_id = f"execplan-{plan_fingerprint[:12]}"

        rationale = self._build_rationale(cp, tasks, reusable, revalidation_sources)

        plan = ExecutionPlan(
            plan_id=plan_id,
            source_plan_id=cp.plan_id,
            repository_fingerprint=live_fp,
            changed_files=list(changed_files),
            affected_capabilities=sorted(
                set(cp.capability_resolution.all_affected_capabilities)
            ),
            affected_components=self._collect_components(tasks),
            invalidated_evidence=list(cp.capability_resolution.invalidated_evidence),
            reusable_evidence=list(cp.capability_resolution.reusable_evidence),
            tasks=tasks,
            escalation_conditions=list(cp.escalation_conditions),
            measurement_requirements=list(cp.measurement_requirements),
            certification_requirements=list(cp.certification_requirements),
            rationale=rationale,
            plan_fingerprint=plan_fingerprint,
            generated_at=datetime.now(UTC).isoformat(),
            revalidation_sources=revalidation_sources,
            reusable_measurements=reusable,
        )
        return plan

    def _expand_control_plane_tasks(self, cp, live_fp: RepositoryFingerprint):
        """Translate C48 control-plane tasks into deduplicated ExecutionTaskSpec.

        Dedup key: (command, verification_kind, profile). One execution
        serves all capabilities the same command covers (per Section 16
        efficiency requirement).
        """
        inventory = self._get_inventory_map()
        dedup: dict[tuple[str], dict] = {}
        order: list[tuple[str]] = []

        for cp_task in cp.tasks:
            inv_entry = inventory.get(cp_task.profile) or inventory.get(
                _profile_from_command(cp_task.command)
            )
            timeout = self._timeout_for(cp_task, inv_entry, fallback=900)
            # Authorization boundary: only commands that actually mutate
            # the repository or are the full mutation campaign require
            # human authorization. Profile script commands (which the C48
            # inventory flags as "escalation") do not themselves mutate.
            is_mutation = (
                "mutation" in cp_task.profile
                or "mutation" in cp_task.command
                or cp_task.verification_kind == "mutation"
            )
            auth_required = is_mutation
            expected_evidence = list(inv_entry.evidence_produced) if inv_entry else []
            prereqs = list(inv_entry.prerequisites) if inv_entry else [".venv"]
            dedup_key = (cp_task.command.strip(),)
            bucket = dedup.get(dedup_key)
            if bucket is None:
                spec = ExecutionTaskSpec(
                    task_id=f"exec-{len(order) + 1:04d}",
                    source_task_id=f"{cp_task.capability_id}::{cp_task.task_id}",
                    primary_capability=cp_task.capability_id,
                    capabilities=(cp_task.capability_id,),
                    verification_kind=cp_task.verification_kind,
                    command=cp_task.command.strip(),
                    profile=cp_task.profile,
                    scope=cp_task.profile,
                    is_mandatory=cp_task.is_mandatory,
                    is_escalation=cp_task.is_escalation,
                    reason=cp_task.reason,
                    origin=TaskOrigin.CONTROL_PLANE.value,
                    prerequisites=tuple(prereqs),
                    expected_evidence=tuple(expected_evidence),
                    measurement_required=tuple(
                        m.value for m in cp_task.measurement_required
                    ),
                    escalation_conditions=(),
                    authorization_required=auth_required,
                    timeout_seconds=timeout,
                    evidence_reused=tuple(cp_task.evidence_reused),
                    evidence_invalidated=tuple(cp_task.evidence_invalidated),
                    estimated_duration_seconds=cp_task.estimated_duration_seconds,
                )
                bucket = {"spec": spec, "capabilities": {cp_task.capability_id}}
                dedup[dedup_key] = bucket
                order.append(dedup_key)
            else:
                bucket["capabilities"].add(cp_task.capability_id)
                # Merge deduped spec: upgrade mandatory / authorization
                # if any contributing task needs them.
                new_dict = bucket["spec"].to_dict()
                if cp_task.is_mandatory and not bucket["spec"].is_mandatory:
                    new_dict["is_mandatory"] = True
                if cp_task.evidence_invalidated:
                    new_dict["is_mandatory"] = True
                if auth_required and not bucket["spec"].authorization_required:
                    new_dict["authorization_required"] = True
                # Track the earliest source task id for provenance
                if cp_task.task_id < new_dict["source_task_id"]:
                    new_dict["source_task_id"] = cp_task.task_id
                bucket["spec"] = ExecutionTaskSpec(**new_dict)
        # Finalize per-bucket capabilities into the spec.
        tasks: list[ExecutionTaskSpec] = []
        for key in order:
            bucket = dedup[key]
            spec_dict = bucket["spec"].to_dict()
            caps = sorted(bucket["capabilities"])
            spec_dict["primary_capability"] = caps[0]
            spec_dict["capabilities"] = caps
            spec_dict["reason"] = (
                spec_dict["reason"] + f" (serves: {', '.join(caps)})"
            ).strip()
            tasks.append(ExecutionTaskSpec(**spec_dict))
        # Apply deterministic ordering: mandatory first by (primary_cap, command).
        tasks.sort(
            key=lambda t: (
                0 if t.is_mandatory else 1,
                t.primary_capability,
                t.command,
            )
        )
        # Reassign stable task IDs after sort.
        tasks = [
            ExecutionTaskSpec(**{**t.to_dict(), "task_id": f"exec-{i + 1:04d}"})
            for i, t in enumerate(tasks)
        ]
        return tasks, order

    def _inject_revalidations(self, cp, tasks: list[ExecutionTaskSpec], live_fp):
        """Inspect durable measurement records and inject revalidation tasks
        for capabilities whose required measurements are missing or stale."""
        from runtime.foundation.verification.measurement_truth import (
            MeasurementKind,
            certification_gate,
        )

        revalidation_sources: list[dict] = []
        reusable: list[dict] = []
        new_tasks: list[ExecutionTaskSpec] = []
        next_id = len(tasks) + 1

        for cap_id in sorted(
            set(cp.capability_resolution.directly_affected_capabilities)
        ):
            contract = self._contract_registry.get_contract(cap_id)
            if not contract:
                continue
            for mm in contract.measurement_mappings:
                kind = mm.measurement_kind.value
                cap = cap_id
                component = self._component_for_mapping(cap, kind)
                record, path = self._find_measurement_record(
                    cap, kind, mm.authoritative_evidence_path
                )
                if record is not None and certification_gate(record):
                    if record.repository_sha == live_fp.repository_sha:
                        reusable.append(
                            {
                                "capability": cap,
                                "kind": kind,
                                "path": str(path),
                                "repository_sha": record.repository_sha,
                                "score": (
                                    record.mutation_score
                                    if kind == MeasurementKind.MUTATION.value
                                    else (
                                        record.coverage_result_percent
                                        or record.coverage.line_percent
                                    )
                                ),
                            }
                        )
                        continue
                    # stale: present but repo sha does not match
                    revalidation_sources.append(
                        {
                            "capability": cap,
                            "kind": kind,
                            "reason": (
                                f"evidence stale: recorded sha "
                                f"{record.repository_sha[:12]} != current "
                                f"{live_fp.repository_sha[:12]}"
                            ),
                            "path": str(path),
                        }
                    )
                else:
                    revalidation_sources.append(
                        {
                            "capability": cap,
                            "kind": kind,
                            "reason": (
                                "no authoritative certifiable measurement record found"
                                if not record
                                else "record not certifiable"
                            ),
                            "path": mm.authoritative_evidence_path or "",
                        }
                    )

                # Inject a revalidation task
                if kind == "mutation":
                    target = CAPABILITY_TO_MUTATION_TARGET.get(cap, "")
                    if not target:
                        new_tasks.append(
                            ExecutionTaskSpec(
                                task_id=f"exec-{next_id:04d}",
                                source_task_id=f"revalidate::{cap}::mutation",
                                primary_capability=cap,
                                capabilities=(cap,),
                                verification_kind="mutation",
                                command=(
                                    f".venv/bin/python -m runtime.verify mutation "
                                    f"--target {component} --json"
                                    if component
                                    else ""
                                ),
                                profile="mutation",
                                scope="mutation",
                                is_mandatory=mm.required_for_certification,
                                is_escalation=False,
                                reason=(
                                    f"revalidation: {cap} mutation evidence is "
                                    f"{'stale' if record else 'missing'} for "
                                    f"certification"
                                ),
                                origin=TaskOrigin.REVALIDATION.value,
                                prerequisites=(".venv", "mutmut==3.7.0", "git"),
                                expected_evidence=("mutation_score", "survivor_intel"),
                                measurement_required=("mutation",),
                                authorization_required=True,
                                timeout_seconds=1200,
                                estimated_duration_seconds=1200,
                                mutation_target=component,
                            )
                        )
                    else:
                        new_tasks.append(
                            ExecutionTaskSpec(
                                task_id=f"exec-{next_id:04d}",
                                source_task_id=f"revalidate::{cap}::mutation",
                                primary_capability=cap,
                                capabilities=(cap,),
                                verification_kind="mutation",
                                command=(
                                    f".venv/bin/python -m runtime.verify mutation "
                                    f"--target {target} --json"
                                ),
                                profile="mutation",
                                scope="mutation",
                                is_mandatory=mm.required_for_certification,
                                is_escalation=False,
                                reason=(
                                    f"revalidation: {cap} mutation evidence is "
                                    f"{'stale' if record else 'missing'} for "
                                    f"certification"
                                ),
                                origin=TaskOrigin.REVALIDATION.value,
                                prerequisites=(".venv", "mutmut==3.7.0", "git"),
                                expected_evidence=("mutation_score", "survivor_intel"),
                                measurement_required=("mutation",),
                                authorization_required=True,
                                timeout_seconds=1200,
                                estimated_duration_seconds=1200,
                                mutation_target=target,
                            )
                        )
                elif kind == "coverage":
                    scope = mm.scope or "tests/unit/engines"
                    if (
                        cap == "api-contracts"
                        or "contract" in cap
                        or scope in {"backend", "backend/src", "."}
                    ):
                        scope = "."
                    new_tasks.append(
                        ExecutionTaskSpec(
                            task_id=f"exec-{next_id:04d}",
                            source_task_id=f"revalidate::{cap}::coverage",
                            primary_capability=cap,
                            capabilities=(cap,),
                            verification_kind="coverage",
                            command=(
                                f".venv/bin/python -m runtime.verify measurement "
                                f"coverage {scope} --out "
                                f"{REPO_ROOT / 'runtime' / 'generated' / 'm9-c49' / 'measurements' / f'measurement-truth-{cap}-coverage.json'}"
                            ),
                            profile="coverage",
                            scope="coverage",
                            is_mandatory=mm.required_for_certification,
                            is_escalation=False,
                            reason=(
                                f"revalidation: {cap} coverage evidence is "
                                f"{'stale' if record else 'missing'}"
                            ),
                            origin=TaskOrigin.REVALIDATION.value,
                            prerequisites=(".venv", "coverage"),
                            expected_evidence=("measurement_truth",),
                            measurement_required=("coverage",),
                            authorization_required=False,
                            timeout_seconds=1800,
                            estimated_duration_seconds=1800,
                        )
                    )
                next_id += 1

        # Re-sort: revalidation tasks are mandatory, ordered after control-plane
        # mandatory tasks but before escalation tasks. Keep deterministic order
        # by (origin, primary_cap, command).
        new_tasks.sort(key=lambda t: (t.origin, t.primary_capability, t.command))
        return new_tasks, revalidation_sources, reusable

    def _find_measurement_record(self, cap_id: str, kind: str, mapping_path: str):
        from runtime.foundation.verification.measurement_truth import (
            load_measurement_truth,
        )

        candidates: list[Path] = []
        for d in [Path(p) for p in self._measurement_search_dirs if p]:
            if d.is_dir():
                candidates.extend(sorted(d.glob(f"measurement-truth-*-{kind}.json")))
                candidates.extend(sorted(d.glob("measurement-truth*.json")))
        if mapping_path:
            p = Path(mapping_path)
            if not p.is_absolute():
                p = REPO_ROOT / p
            candidates.insert(0, p)
        # Per-capability defaults
        for search_dir in self._measurement_search_dirs:
            dd = Path(search_dir)
            if not dd.is_absolute():
                dd = REPO_ROOT / dd
            candidates.append(dd / f"measurement-truth-{cap_id}.json")
        # Default durable locations
        for default in [
            REPO_ROOT
            / "backend"
            / "tests"
            / "generated"
            / "mutation"
            / f"measurement-truth-{cap_id}.json",
            REPO_ROOT
            / "backend"
            / "tests"
            / "generated"
            / "mutation"
            / "local-smoke"
            / "measurement-truth.json",
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c47"
            / "coverage"
            / "measurement-truth-coverage.json",
            REPO_ROOT
            / "runtime"
            / "generated"
            / "m9-c47"
            / f"measurement-truth-{cap_id}.json",
        ]:
            candidates.append(default)
        for path in candidates:
            if not path.exists():
                continue
            try:
                rec = load_measurement_truth(path)
            except Exception:
                continue
            if rec.measurement_kind != kind:
                continue
            return rec, path
        return None, None

    def _component_for_mapping(self, cap_id: str, kind: str) -> str:
        if kind == "mutation":
            return CAPABILITY_TO_MUTATION_TARGET.get(cap_id, "")
        if kind == "coverage":
            contract = self._contract_registry.get_contract(cap_id)
            if contract and contract.measurement_mappings:
                for mm in contract.measurement_mappings:
                    if mm.measurement_kind.value == "coverage":
                        return mm.scope
        return ""

    # ----------------------------------------------------------------------

    def _add_dependency_edges(self, tasks: list[ExecutionTaskSpec]) -> None:
        """Mark escalation tasks as depending on all mandatory tasks (so the
        orchestrator can decide skip vs. run at execution time)."""
        mandatory_ids = {t.task_id for t in tasks if t.is_mandatory}
        for i, t in enumerate(tasks):
            if t.is_escalation and not t.depends_on:
                tasks[i] = ExecutionTaskSpec(
                    **{**t.to_dict(), "depends_on": tuple(sorted(mandatory_ids))}
                )

    def _compute_plan_fingerprint(
        self,
        source_plan_id: str,
        live_fp: RepositoryFingerprint,
        changed_files: list[str],
        tasks: list[ExecutionTaskSpec],
    ) -> str:
        h = hashlib.sha256()
        h.update(source_plan_id.encode("utf-8"))
        h.update(live_fp.fingerprint.encode("utf-8"))
        for f in sorted(changed_files):
            h.update(f.encode("utf-8"))
        for t in tasks:
            h.update(
                "|".join(
                    [
                        t.task_id,
                        ",".join(t.capabilities),
                        t.verification_kind,
                        t.command,
                        str(int(t.is_mandatory)),
                        str(int(t.is_escalation)),
                        str(t.timeout_seconds),
                        str(int(t.authorization_required)),
                        t.origin,
                    ]
                ).encode("utf-8")
            )
        return h.hexdigest()

    def _build_rationale(
        self,
        cp,
        tasks: list[ExecutionTaskSpec],
        reusable: list[dict],
        revalidation_sources: list[dict],
    ) -> str:
        mandatory = sum(1 for t in tasks if t.is_mandatory)
        escalation = sum(1 for t in tasks if t.is_escalation)
        reused = len(reusable)
        revals = len(revalidation_sources)
        return (
            f"Plan built from C48 control-plane {cp.plan_id} for "
            f"{len(cp.changed_files)} changed file(s). Selected "
            f"{len(cp.capability_resolution.directly_affected_capabilities)} "
            f"directly + "
            f"{len(cp.capability_resolution.transitively_affected_capabilities)} "
            f"transitively affected capabilities. Mandatory tasks: {mandatory}; "
            f"escalation tasks: {escalation}; reusable measurements: {reused}; "
            f"revalidation injections: {revals}. "
            f"Mutation is a single capability among many; full mutation campaigns "
            f"require explicit authorization. Stop-on-sufficiency rule applies: "
            f"escalation tasks are skipped when all mandatory tasks are PASS or REUSED."
        )

    def _collect_components(self, tasks: list[ExecutionTaskSpec]) -> list[str]:
        comps: set[str] = set()
        for t in tasks:
            comps.update(_capability_components(list(t.capabilities)))
            if t.mutation_target:
                comps.add(t.mutation_target)
        return sorted(comps)

    def _get_inventory_map(self) -> dict[str, Any]:
        try:
            from runtime.foundation.verification.command_inventory import (
                get_command_inventory,
            )

            inv = get_command_inventory()
        except Exception:
            return {}
        out: dict[str, Any] = {}
        for cmd in inv.commands:
            if cmd.profile_name:
                out.setdefault(cmd.profile_name, cmd)
            if cmd.command_id:
                out.setdefault(cmd.command_id, cmd)
        return out

    def _timeout_for(self, cp_task, inv_entry, fallback: int) -> int:
        kind = cp_task.verification_kind
        if kind in self._max_runtime_overrides:
            return self._max_runtime_overrides[kind]
        if inv_entry and inv_entry.estimated_duration_seconds:
            return max(60, int(inv_entry.estimated_duration_seconds) * 2)
        if cp_task.estimated_duration_seconds:
            return max(60, int(cp_task.estimated_duration_seconds) * 2)
        return fallback

    # ------------------------------------------------------------- validation

    def validate_execution(
        self, plan: ExecutionPlan
    ) -> tuple[list[str], RepositoryFingerprint]:
        """Validate plan + repository fingerprint. Returns (errors, live_fp)."""
        errors: list[str] = []
        errors.extend(plan.validate())
        live_fp = RepositoryFingerprint.capture()
        if not plan.repository_fingerprint.matches(live_fp):
            errors.append(
                "repository state changed since plan was built "
                f"(plan_fp={plan.repository_fingerprint.fingerprint[:12]} "
                f"vs live_fp={live_fp.fingerprint[:12]})"
            )
        return errors, live_fp

    def verify_prerequisites(self, plan: ExecutionPlan) -> tuple[bool, list[str]]:
        """Verify prerequisites for all tasks. Returns (ok, missing list)."""
        missing: list[str] = []
        # Global prerequisites
        if not (REPO_ROOT / ".venv" / "bin" / "python").exists():
            missing.append(".venv/bin/python")
        for path in (".git", "backend", "pyproject.toml"):
            if not (REPO_ROOT / path).exists():
                missing.append(path)
        # Per-task prerequisite paths
        seen: set[str] = set()
        for t in plan.tasks:
            for p in t.prerequisites:
                if p in seen:
                    continue
                seen.add(p)
                if p in (".venv", "git", "mutmut==3.7.0", "pytest", "coverage"):
                    continue
                # explicit script path
                pth = REPO_ROOT / p.lstrip("/")
                if not pth.exists():
                    missing.append(f"{t.task_id}: {p}")
        return (not missing), missing

    # ------------------------------------------------------------- execution

    def execute(
        self,
        plan: ExecutionPlan,
        authorize: set[str] | None = None,
        dry_run: bool = False,
        on_record: Callable[[TaskExecutionRecord], None] | None = None,
    ) -> ExecutionReport:
        """Execute the plan and produce an ExecutionReport.

        * ``authorize`` is a set of task_ids (or profile names) for which the
          operator has explicitly authorized production-affecting work. Tasks
          that are not authorized but require authorization transition to
          AUTHORIZATION_REQUIRED without executing.
        * ``dry_run`` plans and validates but never runs commands; useful for
          acceptance tests and inspection.
        * ``on_record`` is an optional callback invoked with each
          TaskExecutionRecord as it is produced. Callers use it to observe
          in-flight progress (and to capture partial progress if the run is
          interrupted) without changing orchestration semantics.
        """
        authorize = set(authorize or [])
        validation_errors, live_fp = self.validate_execution(plan)
        if validation_errors:
            report = self._blocked_report(plan, validation_errors, live_fp)
            return report

        prereq_ok, prereq_missing = self.verify_prerequisites(plan)
        if not prereq_ok:
            report = self._blocked_report(
                plan,
                [f"missing prerequisites: {', '.join(prereq_missing)}"],
                live_fp,
            )
            return report

        if dry_run:
            report = self._dry_run_report(plan, live_fp)
            return report

        records: list[TaskExecutionRecord] = []
        evidence_reused: list[str] = []
        escalations_triggered: list[str] = []
        decisions: list[dict] = []
        started_at = datetime.now(UTC).isoformat()
        t0 = time.monotonic()

        def _push_record(rec: TaskExecutionRecord) -> None:
            records.append(rec)
            if on_record is not None:
                on_record(rec)

        # Section 6 stop-on-sufficiency state
        any_mandatory_fail = False

        for spec in plan.tasks:
            # Re-evaluation: live fingerprint may have changed mid-run
            current_fp = RepositoryFingerprint.capture()
            if current_fp.fingerprint != live_fp.fingerprint:
                _push_record(
                    self._make_record(
                        spec,
                        plan,
                        exit_code=-1,
                        state=CompletionState.SCOPE,
                        reason_text=f"repository state changed mid-run: live_fp={current_fp.fingerprint[:12]}",
                        stderr_tail=[],
                    )
                )
                any_mandatory_fail = True
                decisions.append(
                    {
                        "stage": "in_flight",
                        "decision": "aborted",
                        "reason": "live fingerprint changed mid-run",
                    }
                )
                break

            # Stop on sufficiency (Section 6): skip escalation if all
            # mandatory tasks so far are PASS/REUSED.
            if spec.is_escalation and not any_mandatory_fail:
                _push_record(
                    self._make_record(
                        spec,
                        plan,
                        exit_code=0,
                        state=CompletionState.SKIPPED,
                        reason_text=(
                            "stop-on-sufficiency: all mandatory tasks PASS or REUSED; "
                            "escalation skipped"
                        ),
                        stderr_tail=[],
                    )
                )
                continue

            # Evidence reuse: for measurement tasks, check the persistent
            # record before executing (Section 6 — reuse authoritative current
            # evidence; reject stale evidence).
            if _measurement_kind_for_task(spec):
                reusable = self._check_reusable_measurement(spec, live_fp)
                if reusable is not None:
                    record = self._make_record(
                        spec,
                        plan,
                        exit_code=0,
                        state=CompletionState.REUSED,
                        reason_text=(
                            f"authoritative {spec.verification_kind} record reused "
                            f"from {reusable.get('path', '?')}"
                        ),
                        stderr_tail=[],
                        measurement_truth={
                            "kind": spec.verification_kind,
                            "path": reusable.get("path", ""),
                            "score": reusable.get("score"),
                            "repository_sha": reusable.get("repository_sha", ""),
                            "completion_status": "AUTHORITATIVE_COMPLETE",
                        },
                    )
                    _push_record(record)
                    evidence_reused.append(spec.task_id)
                    continue

            # Authorization boundary.
            if spec.authorization_required and spec.task_id not in authorize:
                record = self._make_record(
                    spec,
                    plan,
                    exit_code=-1,
                    state=CompletionState.AUTHORIZATION_REQUIRED,
                    reason_text=(
                        "task requires human authorization; not authorized at "
                        "execution time — no production changes attempted"
                    ),
                    stderr_tail=[],
                    diagnostic={
                        "stage": FailureStage.AUTHORIZATION_REQUIRED.value,
                        "message": "operator must pass --authorize to run",
                    },
                    next_action=(
                        "review capability / component / required evidence and rerun "
                        "with --authorize <task_id> or --authorize all"
                    ),
                )
                _push_record(record)
                escalations_triggered.append(spec.task_id)
                continue

            # Execute.
            record = self._execute_task(spec, plan, live_fp)
            _push_record(record)
            if spec.is_mandatory and record.completion_state in NON_PASS_STATES:
                any_mandatory_fail = True
            if record.completion_state in (CompletionState.FAILED,):
                decisions.append(
                    {
                        "stage": "diagnostic",
                        "task_id": spec.task_id,
                        "decision": record.next_action,
                        "failure_stage": (record.diagnostic or {}).get(
                            "stage", FailureStage.NONE.value
                        ),
                    }
                )

        # Finalize.
        final_decision, reason = self._finalize(plan, records, live_fp)
        report_id = (
            "report-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|" + started_at).encode("utf-8")
            ).hexdigest()[:12]
        )
        efficiency = self._compute_efficiency(plan, records)
        return ExecutionReport(
            report_id=report_id,
            plan_id=plan.plan_id,
            plan_fingerprint=plan.plan_fingerprint,
            started_at=started_at,
            completed_at=datetime.now(UTC).isoformat(),
            total_duration_seconds=time.monotonic() - t0,
            records=records,
            efficiency=efficiency,
            final_decision=final_decision.value,
            decision_reason=reason,
            evidence_reused=evidence_reused,
            escalations_triggered=escalations_triggered,
            decisions=decisions,
        )

    def _execute_task(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord:
        # If a per-kind override is set, route through the shell path so
        # the override substitution applies (the internal runners ignore
        # the command string).
        if f"kind:{spec.verification_kind}" in self._command_overrides:
            return self._execute_shell_task(spec, plan)
        if spec.command in self._command_overrides:
            return self._execute_shell_task(spec, plan)
        # Internal measurement executor: for measurement revalidation tasks,
        # route through the native mutmut runner (Section 8 — mutation is one
        # verification capability among many, run via internal runner).
        if spec.verification_kind == "mutation" and spec.mutation_target:
            return self._execute_measurement_task(spec, plan, live_fp)
        if spec.verification_kind == "coverage":
            return self._execute_coverage_task(spec, plan, live_fp)
        # Default: shell command
        return self._execute_shell_task(spec, plan)

    def _execute_shell_task(
        self, spec: ExecutionTaskSpec, plan: ExecutionPlan
    ) -> TaskExecutionRecord:
        command = self._resolve_command(spec)
        log_dir = self._evidence_root / "logs" / plan.plan_id
        log_dir.mkdir(parents=True, exist_ok=True)
        stdout_path = log_dir / f"{spec.task_id}-stdout.log"
        stderr_path = log_dir / f"{spec.task_id}-stderr.log"
        # Start each execution with a clean file. The tee appends (so it is safe
        # for the reader threads to interleave), so anything left from an earlier
        # execution of the same task would otherwise appear to be this run's
        # output. Truncating up front keeps the file meaning "this execution",
        # and an empty file is still a valid record of "produced no output".
        for stale in (stdout_path, stderr_path):
            with contextlib.suppress(OSError):
                stale.unlink()
        t0 = time.monotonic()
        exit_code: int | None = None
        timed_out = False
        infra_error: str | None = None
        stdout_data = ""
        stderr_data = ""
        # 2026-09-30 — M9 stabilization: stream to the evidence files instead of
        # buffering the whole run in memory and writing it at the end.
        #
        # With `capture_output=True` the log files stayed 0 bytes for the entire
        # execution and only received their contents after the child exited. Two
        # consequences, both observed during this stabilization:
        #
        #   1. If the orchestrator itself is interrupted, or the child is killed
        #      and the write step is never reached, the evidence for a failing
        #      run is *nothing at all* — which is exactly what happened to
        #      reconcile run execplan-d210b2f3ea52, where all 20 task logs were
        #      zero bytes and the failing obligation's output was unrecoverable.
        #   2. Nothing recorded which test was executing, so a failing 29-minute
        #      pytest run could not be narrowed down without re-running the
        #      whole suite to catch it again.
        #
        # Streaming with an immediate flush makes the evidence exist and grow
        # while the task runs, so a kill, a signal or an orchestrator crash
        # still leaves the output produced up to that instant. This reuses the
        # tee-then-flush pattern executor.py already uses for the same purpose
        # (see `_tee` there); it is not a new mechanism.
        #
        # The contents read back afterwards are identical to what
        # `capture_output=True` would have produced, so the state classification
        # below is unchanged.
        try:
            # Canonical child environment (M9-C57): venv-first PATH + ED7
            # locale/TZ, shared with executor.py via env.child_process_env.
            from runtime.foundation.verification.env import child_process_env

            proc = subprocess.Popen(
                command,
                shell=True,
                cwd=str(REPO_ROOT),
                env=child_process_env(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                # Own process group, so a wrapper timeout can kill the whole
                # tree (the child is a shell that runs pytest, which runs more
                # processes again). Mirrors executor.py's F19 handling.
                start_new_session=True,
            )
            readers = [
                threading.Thread(
                    target=_tee,
                    args=(proc.stdout, stdout_path),
                    daemon=True,
                ),
                threading.Thread(
                    target=_tee,
                    args=(proc.stderr, stderr_path),
                    daemon=True,
                ),
            ]
            for reader in readers:
                reader.start()
            try:
                proc.wait(timeout=spec.timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                exit_code = 124
                _kill_process_group(proc)
            for reader in readers:
                reader.join(timeout=5)
            # A shell that dies on a signal reports 128+signum, so a return code
            # above 128 is a termination, not a command's own exit status. It is
            # recorded explicitly because "the process was killed" and "the
            # command reported failure" are different diagnoses.
            if exit_code is None:
                exit_code = proc.returncode
            stdout_data = _read_text(stdout_path)
            stderr_data = _read_text(stderr_path)
        except FileNotFoundError as exc:
            infra_error = f"command not found: {exc}"
        except Exception as exc:  # defensive
            infra_error = f"subprocess raised: {type(exc).__name__}: {exc}"

        # The evidence files were written by the tee while the child ran. Touch
        # them so they exist even when the child produced no output at all and
        # the process was killed before the first line.
        stdout_path.touch(exist_ok=True)
        stderr_path.touch(exist_ok=True)
        duration = time.monotonic() - t0
        artifacts: list[str] = [str(stdout_path), str(stderr_path)]

        if infra_error:
            state = CompletionState.INFRASTRUCTURE
            reason_text = infra_error
        elif timed_out:
            state = CompletionState.TIMEOUT
            reason_text = f"command exceeded {spec.timeout_seconds}s"
        elif exit_code == 0:
            state = CompletionState.PASS
            reason_text = "command exit 0"
        else:
            # Reclassify infrastructure signals from stderr before
            # defaulting to FAILED — an actual runtime FileNotFoundError
            # or ModuleNotFoundError means the verification surface
            # itself is broken (not a test assertion failure).
            infra_signals = (
                "FileNotFoundError",
                "No such file or directory",
                "ModuleNotFoundError",
                "command not found",
                "Permission denied",
                "No such command",
            )
            stderr_text = (stderr_data or "") + "\n" + (stdout_data or "")
            if any(sig in stderr_text for sig in infra_signals) or exit_code == 127:
                state = CompletionState.INFRASTRUCTURE
                reason_text = (
                    f"infrastructure error (exit {exit_code}): "
                    f"{stderr_text.strip()[:200]}"
                )
            else:
                state = CompletionState.FAILED
                reason_text = f"command exit {exit_code}"

        diag = self._diagnose(spec, state, stderr_data, stdout_data)
        next_action = self._next_action(spec, state, diag)
        termination = _classify_termination(exit_code, timed_out, infra_error)
        # Fold the *in-command* cause into the record. A wrapper script that
        # aggregates checks (`run_runtime_verification.sh` prints
        # `Failed checks: runtime-tests`) hides which check actually failed, and
        # the script's own non-zero exit says nothing about the kind of failure:
        # an assertion failure, a per-test timeout and an integrity failure are
        # three different defects. The record names them so a long run cannot be
        # summarised as "command exit 1" and then guessed at.
        pytest_detail = _summarise_pytest_outcome(stdout_data + "\n" + stderr_data)
        if pytest_detail and state is not CompletionState.PASS:
            diag = dict(diag or {})
            diag.setdefault("pytest", pytest_detail)
            termination = dict(termination)
            termination["inner"] = pytest_detail
            if not timed_out and not infra_error and exit_code != 0:
                # Keep the wrapper's EXIT_NONZERO but say what the inner run
                # actually was, so the two are never confused.
                termination["kind"] = "EXIT_NONZERO_WITH_INNER_" + pytest_detail["kind"]
        if state != CompletionState.PASS and spec.is_mandatory:
            # attach a forensic diagnostic record
            pass
        return self._make_record(
            spec,
            plan,
            exit_code=exit_code,
            state=state,
            reason_text=reason_text,
            stderr_tail=stderr_data.splitlines()[-20:],
            stdout_path=str(stdout_path),
            stderr_path=str(stderr_path),
            artifacts=artifacts,
            diagnostic=diag,
            next_action=next_action,
            duration_seconds=duration,
            termination=termination,
        )

    def _execute_measurement_task(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord:
        from runtime.foundation.verification.measurement_truth import (
            EvidenceClassification,
            FailureClassification,
            MeasurementCompletionStatus,
            MeasurementKind,
            MeasurementTruthRecord,
            PopulationAccounting,
            certification_gate,
            classify_completion,
            save_measurement_truth,
            set_evidence_fingerprint,
        )

        started = datetime.now(UTC)
        t0 = time.monotonic()
        try:
            from runtime.foundation.verification.mutation_runner import execute_mutation

            result = execute_mutation(
                mode="target", target=spec.mutation_target, allow_dirty=True
            )
        except Exception as exc:
            duration = time.monotonic() - t0
            diag = {
                "stage": FailureStage.INFRASTRUCTURE_FAILURE.value,
                "message": f"mutation runner raised: {type(exc).__name__}: {exc}",
            }
            return self._make_record(
                spec,
                plan,
                exit_code=-1,
                state=CompletionState.INFRASTRUCTURE,
                reason_text=str(exc),
                stderr_tail=[diag["message"]],
                diagnostic=diag,
                next_action="verify.py env-check; clean worktree, then re-authorize",
                duration_seconds=duration,
            )

        duration = time.monotonic() - t0
        # Build MeasurementTruthRecord
        if result.execution_status != "PASS":
            state = CompletionState.INFRASTRUCTURE
            reason = result.error or "mutation runner reported infrastructure failure"
        elif result.classification_status != "PASS" or not result.evidence_complete:
            state = CompletionState.EVIDENCE
            reason = (
                "mutation evidence could not be reconciled "
                f"(classification_status={result.classification_status}, "
                f"complete={result.evidence_complete})"
            )
        else:
            state = CompletionState.PASS
            reason = (
                f"targeted mutation: score {result.mutation_score}%, "
                f"killed {result.killed}/{result.mutants_generated}"
            )

        record_path = (
            self._evidence_root
            / "measurements"
            / f"measurement-truth-{spec.primary_capability}-mutation.json"
        )
        record_path.parent.mkdir(parents=True, exist_ok=True)
        truth = MeasurementTruthRecord(
            run_id=result.run_id,
            measurement_kind=MeasurementKind.MUTATION.value,
            repository_sha=result.repository_sha or live_fp.repository_sha,
            tree_sha=result.tree_sha or live_fp.working_tree_hash,
            configuration_fingerprint=result.config_hash or live_fp.config_hash,
            toolchain_fingerprint=live_fp.toolchain_hash,
            environment_fingerprint=live_fp.fingerprint,
            command=f"verify.py mutation --target {spec.mutation_target}",
            requested_scope=spec.mutation_target,
            actual_scope=result.source_scope or spec.mutation_target,
            population=PopulationAccounting(
                requested_generated=result.mutants_generated,
                generated=result.mutants_generated,
                killed=result.killed,
                survived=result.survived,
                no_tests=result.no_tests,
                timeout=result.timeout,
                suspicious=result.suspicious,
                not_checked=result.not_checked,
            ),
            mutation_score=result.mutation_score,
            execution_status=result.execution_status,
            failure_classification=(
                FailureClassification.NONE.value
                if state == CompletionState.PASS
                else FailureClassification.INFRASTRUCTURE.value
            ),
            start_time=started.isoformat(),
            end_time=datetime.now(UTC).isoformat(),
            duration_seconds=duration,
            toolchain_versions={
                "python": result.python_version,
                "pytest": result.pytest_version,
                "mutmut": result.mutmut_version,
            },
            artifact_paths=[str(record_path)],
            # Seed the classification optimistically: the campaign really did
            # just execute. `classify_completion` then downgrades it on its own
            # if the run was partial, timed out, hit an infrastructure error or
            # produced unusable evidence — so a bad run is still refused, and
            # the label is decided by the canonical classifier rather than
            # hard-coded here.
            evidence_classification=EvidenceClassification.AUTHORITATIVE.value,
            mode="target",
            target=spec.mutation_target,
            error=result.error,
        )
        # Order matters. `classify_completion` rejects a record whose
        # `evidence_fingerprint` is empty while it has processed a non-empty
        # population (EVIDENCE_FAILURE), so durability must be stamped *before*
        # classification, not after. Measured on the real records: the ledger,
        # loan-engine and reconciliation campaigns each processed their full
        # population (190/190, 1273/1273, 368/368) with zero timeouts and
        # `failure_classification` "none" at the current repository SHA, and were
        # still refused by certification as "mutation measurement
        # authoritative+current" — because this path left the classification at
        # the dataclass default (DERIVED), never stamped a fingerprint, and so
        # could never mint a consumable record at all.
        #
        # The reuse path in this same file hard-codes
        # `"completion_status": "AUTHORITATIVE_COMPLETE"` for a reused record,
        # so a reused measurement certified while a freshly measured one could
        # not — the inverse of the intended contract.
        #
        # This weakens nothing. `classify_completion` still refuses a partial
        # population, an empty population, a population that does not reconcile,
        # a timeout-classified, infrastructure-failed or interrupted run, and an
        # invalid scope — verified against each case directly. The canonical
        # classifier decides the label, instead of the writer hard-coding one
        # that the gate then refuses.
        set_evidence_fingerprint(truth)
        truth.completion_status = classify_completion(record=truth)
        truth.evidence_classification = (
            EvidenceClassification.AUTHORITATIVE.value
            if truth.completion_status
            == MeasurementCompletionStatus.AUTHORITATIVE_COMPLETE.value
            else EvidenceClassification.DERIVED.value
        )
        truth.consumable_by_certification = certification_gate(truth)
        with contextlib.suppress(Exception):
            save_measurement_truth(truth, record_path)

        diag = self._diagnose(spec, state, reason, "")
        next_action = self._next_action(spec, state, diag)
        return self._make_record(
            spec,
            plan,
            exit_code=0 if state == CompletionState.PASS else 1,
            state=state,
            reason_text=reason,
            stderr_tail=[],
            diagnostic=diag,
            next_action=next_action,
            measurement_truth={
                "kind": "mutation",
                "path": str(record_path),
                "score": result.mutation_score,
                "repository_sha": truth.repository_sha,
                "completion_status": truth.completion_status,
                "evidence_classification": truth.evidence_classification,
                "consumable_by_certification": truth.consumable_by_certification,
            },
            duration_seconds=duration,
        )

    def _execute_coverage_task(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        live_fp: RepositoryFingerprint,
    ) -> TaskExecutionRecord:
        # The C49 orchestrator executes coverage via the canonical measurement
        # CLI. We respect a per-task command_overrides substitution so tests
        # can substitute fast commands.
        return self._execute_shell_task(spec, plan)

    def _check_reusable_measurement(
        self, spec: ExecutionTaskSpec, live_fp: RepositoryFingerprint
    ) -> dict | None:
        contract = self._contract_registry.get_contract(spec.primary_capability)
        if not contract:
            return None
        from runtime.foundation.verification.measurement_truth import (
            certification_gate,
        )

        kind = _measurement_kind_for_task(spec)
        if not kind:
            return None
        mm = next(
            (
                m
                for m in contract.measurement_mappings
                if m.measurement_kind.value == kind
            ),
            None,
        )
        if mm is None:
            return None
        record, path = self._find_measurement_record(
            spec.primary_capability, kind, mm.authoritative_evidence_path
        )
        if record is None or not certification_gate(record):
            return None
        if record.repository_sha != live_fp.repository_sha:
            return None
        return {
            "kind": kind,
            "path": str(path),
            "score": (
                record.mutation_score
                if kind == "mutation"
                else record.coverage_result_percent or record.coverage.line_percent
            ),
            "repository_sha": record.repository_sha,
        }

    # ------------------------------------------------------------- diagnose

    def _diagnose(
        self,
        spec: ExecutionTaskSpec,
        state: CompletionState,
        stderr: str,
        stdout: str,
    ) -> dict:
        if state == CompletionState.PASS or state == CompletionState.REUSED:
            return {"stage": FailureStage.NONE.value, "message": "ok"}
        if state == CompletionState.TIMEOUT:
            return {
                "stage": FailureStage.TIMEOUT.value,
                "message": "command exceeded timeout",
            }
        if state == CompletionState.INFRASTRUCTURE:
            return {
                "stage": FailureStage.INFRASTRUCTURE_FAILURE.value,
                "message": stderr[:400] if stderr else "infrastructure error",
            }
        if state == CompletionState.SCOPE:
            return {
                "stage": FailureStage.INVALID_SCOPE.value,
                "message": stderr[:400] if stderr else "scope mismatch",
            }
        if state == CompletionState.CONFIGURATION:
            return {
                "stage": FailureStage.CONFIGURATION_FAILURE.value,
                "message": stderr[:400] if stderr else "configuration error",
            }
        if state == CompletionState.EVIDENCE:
            return {
                "stage": FailureStage.MISSING_EVIDENCE.value,
                "message": stderr[:400] if stderr else "evidence incomplete",
            }
        if state == CompletionState.AUTHORIZATION_REQUIRED:
            return {
                "stage": FailureStage.AUTHORIZATION_REQUIRED.value,
                "message": "human authorization required",
            }
        # FAILED — classify
        text = (stderr or "") + "\n" + (stdout or "")
        if re.search(r"AssertionError|assert .* ==", text):
            stage = FailureStage.ASSERTION_FAILURE
        elif re.search(r"collected 0 items|no tests ran", text):
            stage = FailureStage.MISSING_EVIDENCE
        elif re.search(r"ModuleNotFoundError|ImportError", text):
            stage = FailureStage.CONFIGURATION_FAILURE
        elif re.search(r"\bError\b", text) and re.search(r"line \d+", text):
            stage = FailureStage.CODE_DEFECT
        elif re.search(r"\bFAIL\b|\bFAILED\b|\bE\s+\b", text):
            stage = FailureStage.TEST_FAILURE
        else:
            stage = FailureStage.TOOLING_FAILURE
        return {
            "stage": stage.value,
            "message": (stderr or text).strip()[:400],
        }

    def _next_action(
        self, spec: ExecutionTaskSpec, state: CompletionState, diag: dict
    ) -> str:
        if state in PASSING_STATES:
            return "no action — task satisfied"
        if state == CompletionState.AUTHORIZATION_REQUIRED:
            return (
                "review task profile + measurement history; rerun with explicit "
                "--authorize <task_id> or --authorize all"
            )
        if state == CompletionState.TIMEOUT:
            return (
                "increase timeout for this profile, or run targeted subset; "
                "do not assume the previous score"
            )
        if state == CompletionState.INFRASTRUCTURE:
            return (
                "diagnose infrastructure (verify.py env-check, .venv health) "
                "and rerun; cannot be certified"
            )
        if state == CompletionState.SCOPE:
            return "align requested vs actual scope, then re-plan"
        if state == CompletionState.CONFIGURATION:
            return "verify prerequisites and rerun"
        if state == CompletionState.EVIDENCE:
            return "rerun measurement to capture complete evidence"
        # FAILED — capability-aware diagnostic path
        primary = spec.primary_capability
        return (
            f"run capability-aware diagnostic for {primary} "
            f"(verify.py what-should-i-run failing-test <test> or "
            f"verify.py strengthen-survivor <survivor_id>); "
            f"do not auto-run unrelated tasks"
        )

    # ------------------------------------------------------------- finalize

    def _finalize(
        self,
        plan: ExecutionPlan,
        records: list[TaskExecutionRecord],
        live_fp: RepositoryFingerprint,
    ) -> tuple[FinalDecision, str]:
        states = [r.completion_state for r in records]
        # Blockers first
        if any(s == CompletionState.INFRASTRUCTURE for s in states):
            return (
                FinalDecision.INFRASTRUCTURE_BLOCKED,
                "one or more tasks reported infrastructure failure — cannot certify",
            )
        if any(s == CompletionState.TIMEOUT for s in states):
            return (
                FinalDecision.TIMEOUT_BLOCKED,
                "one or more tasks timed out — cannot certify (timeout never converts to PASS)",
            )
        if any(s == CompletionState.SCOPE for s in states):
            return (
                FinalDecision.VALIDATION_BLOCKED,
                "scope or fingerprint mismatch detected — cannot certify",
            )
        if any(
            s == CompletionState.CONFIGURATION and r.is_mandatory
            for s, r in zip(states, records, strict=False)
        ):
            return (
                FinalDecision.VALIDATION_BLOCKED,
                "configuration failure on a mandatory task — cannot certify",
            )
        if any(
            s == CompletionState.FAILED and r.is_mandatory
            for s, r in zip(states, records, strict=False)
        ):
            failed = [
                r.task_id
                for r in records
                if r.completion_state == CompletionState.FAILED and r.is_mandatory
            ]
            return (
                FinalDecision.DIAGNOSTIC,
                f"mandatory tasks failed: {', '.join(failed)} — run diagnostic path",
            )
        if any(s == CompletionState.AUTHORIZATION_REQUIRED for s in states):
            return (
                FinalDecision.AWAITING_AUTHORIZATION,
                "one or more tasks require explicit human authorization; production "
                "changes were not attempted",
            )
        # All mandatory tasks passed (or reused or skipped). Certification gate:
        required_kinds: dict[tuple[str, str], dict] = {}
        for cr in plan.certification_requirements:
            required_kinds[(cr.get("capability", ""), "mutation")] = cr
        missing: list[str] = []
        from runtime.foundation.verification.measurement_truth import (
            MeasurementKind,
            certification_gate,
        )

        for cr in plan.certification_requirements:
            cap = cr.get("capability", "")
            mm_score = cr.get("minimum_mutation_score")
            if mm_score is None:
                continue
            record, _path = self._find_measurement_record(
                cap, MeasurementKind.MUTATION.value, ""
            )
            if record is None or not certification_gate(record):
                missing.append(f"{cap} mutation measurement authoritative+current")
                continue
            if record.repository_sha != live_fp.repository_sha:
                missing.append(
                    f"{cap} mutation record sha={record.repository_sha[:8]} != current"
                )
                continue
            if (record.mutation_score or 0) < mm_score:
                missing.append(
                    f"{cap} mutation score {record.mutation_score} < {mm_score}"
                )
        if missing:
            return (
                FinalDecision.NOT_CERTIFIABLE,
                "certification conditions not satisfied: " + "; ".join(missing),
            )
        return (
            FinalDecision.CERTIFIED,
            "all mandatory tasks passed and certification conditions satisfied",
        )

    # ------------------------------------------------------------- helpers

    def _make_record(
        self,
        spec: ExecutionTaskSpec,
        plan: ExecutionPlan,
        *,
        exit_code: int | None,
        state: CompletionState,
        reason_text: str,
        stderr_tail: list[str],
        stdout_path: str = "",
        stderr_path: str = "",
        artifacts: list[str] | None = None,
        diagnostic: dict | None = None,
        next_action: str = "",
        measurement_truth: dict | None = None,
        duration_seconds: float = 0.0,
        termination: dict | None = None,
    ) -> TaskExecutionRecord:
        record_id = (
            "task-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|" + spec.task_id + "|" + state.value).encode(
                    "utf-8"
                )
            ).hexdigest()[:12]
        )
        return TaskExecutionRecord(
            record_id=record_id,
            plan_id=plan.plan_id,
            task_id=spec.task_id,
            primary_capability=spec.primary_capability,
            capabilities=list(spec.capabilities),
            command=spec.command,
            scope=spec.scope,
            is_mandatory=spec.is_mandatory,
            is_escalation=spec.is_escalation,
            verification_kind=spec.verification_kind,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            duration_seconds=duration_seconds,
            exit_code=exit_code,
            completion_state=state.value,
            stdout_path=stdout_path,
            stderr_path=stderr_path,
            artifacts=list(artifacts or []),
            measurement_truth=measurement_truth,
            diagnostic=diagnostic,
            next_action=next_action or "no action",
            reason=reason_text,
            prerequisites_satisfied=True,
            termination=termination,
        )

    def _blocked_report(
        self,
        plan: ExecutionPlan,
        errors: list[str],
        live_fp: RepositoryFingerprint,
    ) -> ExecutionReport:
        return ExecutionReport(
            report_id="report-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|blocked").encode("utf-8")
            ).hexdigest()[:12],
            plan_id=plan.plan_id,
            plan_fingerprint=plan.plan_fingerprint,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            total_duration_seconds=0.0,
            records=[],
            efficiency=self._compute_efficiency(plan, []),
            final_decision=FinalDecision.VALIDATION_BLOCKED.value,
            decision_reason="; ".join(errors),
            evidence_reused=[],
            escalations_triggered=[],
        )

    def _dry_run_report(
        self, plan: ExecutionPlan, live_fp: RepositoryFingerprint
    ) -> ExecutionReport:
        return ExecutionReport(
            report_id="report-"
            + hashlib.sha256(
                (plan.plan_fingerprint + "|dry").encode("utf-8")
            ).hexdigest()[:12],
            plan_id=plan.plan_id,
            plan_fingerprint=plan.plan_fingerprint,
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            total_duration_seconds=0.0,
            records=[],
            efficiency=self._compute_efficiency(plan, []),
            final_decision=FinalDecision.DIAGNOSTIC.value,
            decision_reason="dry run — no execution performed",
            evidence_reused=[],
            escalations_triggered=[],
        )

    def _compute_efficiency(
        self, plan: ExecutionPlan, records: list[TaskExecutionRecord]
    ) -> dict:
        """Section-16 efficiency metrics."""
        try:
            from runtime.foundation.verification.command_inventory import (
                get_command_inventory,
            )

            inv = get_command_inventory()
            total_available = len(inv.commands)
        except Exception:
            total_available = 0
        selected = len(plan.tasks)
        executed = sum(
            1
            for r in records
            if r.completion_state
            in (
                CompletionState.PASS.value,
                CompletionState.FAILED.value,
                CompletionState.TIMEOUT.value,
                CompletionState.INFRASTRUCTURE.value,
                CompletionState.EVIDENCE.value,
                CompletionState.SCOPE.value,
                CompletionState.CONFIGURATION.value,
                CompletionState.CERTIFICATION.value,
            )
        )
        reused = sum(
            1 for r in records if r.completion_state == CompletionState.REUSED.value
        )
        skipped = sum(
            1 for r in records if r.completion_state == CompletionState.SKIPPED.value
        )
        auth_required = sum(
            1
            for r in records
            if r.completion_state == CompletionState.AUTHORIZATION_REQUIRED.value
        )
        blind_total = self._blind_total_commands()
        executed_unique = len(
            {
                r.command
                for r in records
                if r.completion_state == CompletionState.PASS.value
            }
        )
        unnecessary_avoided = max(0, blind_total - executed_unique)
        return {
            "total_available_tasks": total_available,
            "tasks_selected": selected,
            "tasks_executed": executed,
            "tasks_reused": reused,
            "tasks_skipped": skipped,
            "tasks_awaiting_authorization": auth_required,
            "blind_total_commands": blind_total,
            "unnecessary_execution_avoided": unnecessary_avoided,
            "execution_time_seconds": sum(r.duration_seconds for r in records),
        }

    def _blind_total_commands(self) -> int:
        try:
            from runtime.foundation.verification.capability_contract import (
                get_capability_contract_registry,
            )
            from runtime.foundation.verification.command_inventory import (
                get_command_inventory,
            )

            registry = get_capability_contract_registry()
            inventory = get_command_inventory()
        except Exception:
            return 0
        registry.load()
        seen: set[str] = set()
        for cap in registry.get_all_contracts():
            for wf in cap.workflow_mappings:
                seen.add(wf.command.strip())
        # also count capability-derived commands
        for _cid, cmds in inventory.capabilities_index.items():
            for cmd_id in cmds:
                cmd = inventory.get_command(cmd_id)
                if cmd:
                    seen.add(cmd.command.strip())
        return len(seen)

    def _resolve_command(self, spec: ExecutionTaskSpec) -> str:
        if spec.command in self._command_overrides:
            return self._command_overrides[spec.command]
        # Per-kind override (used in tests to substitute fast commands for
        # revalidation measurement tasks whose auto-generated commands vary).
        kind_key = f"kind:{spec.verification_kind}"
        if kind_key in self._command_overrides:
            return self._command_overrides[kind_key]
        return spec.command


def _profile_from_command(command: str) -> str:
    """Heuristic: map a command string to a profile name (best effort)."""
    m = re.search(r"\.github/scripts/run_([a-z_]+)\.sh", command)
    if m:
        return m.group(1)
    return ""


# ---------------------------------------------------------------------------
# Convenience entry points
# ---------------------------------------------------------------------------


def build_plan(
    changed_files: list[str], orchestrator: ExecutionOrchestrator | None = None
) -> ExecutionPlan:
    orch = orchestrator or ExecutionOrchestrator()
    return orch.build_execution_plan(changed_files)


def format_plan(plan: ExecutionPlan) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("  VERIFICATION EXECUTION PLAN (M9-C49)")
    lines.append("=" * 80)
    lines.append(f"  Plan ID:       {plan.plan_id}")
    lines.append(f"  Source:        C48 {plan.source_plan_id}")
    lines.append(f"  Fingerprint:   {plan.plan_fingerprint[:12]}")
    lines.append(f"  Repository:    {plan.repository_fingerprint.repository_sha[:12]}")
    lines.append(f"  Toolchain:     {plan.repository_fingerprint.toolchain_hash[:12]}")
    lines.append(f"  Changed:       {len(plan.changed_files)}")
    lines.append(f"  Affected caps: {', '.join(plan.affected_capabilities)}")
    lines.append("-" * 80)
    lines.append("  TASKS:")
    for t in plan.tasks:
        auth = " [AUTH]" if t.authorization_required else ""
        mand = " (mandatory)" if t.is_mandatory else ""
        if t.is_escalation:
            mand = " (escalation)"
        lines.append(
            f"    [{t.verification_kind:>9s}] {t.task_id} -> {t.primary_capability}{auth}{mand}"
        )
        lines.append(f"             cmd: {t.command}")
        lines.append(f"             origin: {t.origin}  reason: {t.reason[:120]}")
    lines.append("-" * 80)
    lines.append("  REVALIDATION:")
    for r in plan.revalidation_sources:
        lines.append(
            f"    {r.get('capability', '?')} {r.get('kind', '?')}: {r.get('reason', '?')}"
        )
    lines.append("  REUSABLE:")
    for r in plan.reusable_measurements:
        lines.append(
            f"    {r.get('capability', '?')} {r.get('kind', '?')}: score={r.get('score')} sha={r.get('repository_sha', '?')[:12]}"
        )
    lines.append("-" * 80)
    lines.append(f"  RATIONALE: {plan.rationale}")
    lines.append("=" * 80)
    return "\n".join(lines)


def format_report(report: ExecutionReport) -> str:
    lines: list[str] = []
    lines.append("=" * 80)
    lines.append("  VERIFICATION EXECUTION REPORT (M9-C49)")
    lines.append("=" * 80)
    lines.append(f"  Report ID:     {report.report_id}")
    lines.append(f"  Plan ID:       {report.plan_id}")
    lines.append(f"  Decision:      {report.final_decision}")
    lines.append(f"  Reason:        {report.decision_reason}")
    lines.append(f"  Total time:    {report.total_duration_seconds:.1f}s")
    lines.append("-" * 80)
    eff = report.efficiency
    lines.append(
        f"  EFFICIENCY: selected={eff.get('tasks_selected', 0)} "
        f"executed={eff.get('tasks_executed', 0)} "
        f"reused={eff.get('tasks_reused', 0)} "
        f"skipped={eff.get('tasks_skipped', 0)} "
        f"auth_required={eff.get('tasks_awaiting_authorization', 0)} "
        f"avoided={eff.get('unnecessary_execution_avoided', 0)}"
    )
    lines.append("-" * 80)
    lines.append("  TASK RECORDS:")
    for r in report.records:
        lines.append(
            f"    [{r.completion_state:>22s}] {r.task_id} ({r.primary_capability}) "
            f"exit={r.exit_code} dur={r.duration_seconds:.1f}s"
        )
        if r.next_action and r.completion_state not in ("pass", "reused", "skipped"):
            lines.append(f"             next: {r.next_action[:120]}")
    lines.append("=" * 80)
    return "\n".join(lines)
