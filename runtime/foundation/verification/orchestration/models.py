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
import re
import subprocess
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent

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
    regression_info: dict = field(default_factory=dict)

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
            "regression_info": dict(self.regression_info),
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

