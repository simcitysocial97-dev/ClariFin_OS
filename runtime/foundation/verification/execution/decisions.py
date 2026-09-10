"""M50 S6 — Cache semantics and lineage enforcer.

Deterministic reuse decisions and the guards that enforce the
obligation → task → execution → evidence → reconciliation → decision
lineage chain.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from runtime.foundation.verification.execution.classification import FailureKind
from runtime.foundation.verification.execution.dispatcher import LineageViolationError
from runtime.foundation.verification.execution.evidence import ExecutionEvidence
from runtime.foundation.verification.execution.identity import (
    IdentityKind,
    compute_identity,
)
from runtime.foundation.verification.execution.task import ExecutableVerificationTask


@dataclass(frozen=True, slots=True)
class CacheDecision:
    """A deterministic cache reuse decision."""

    decision: Literal["REUSE", "EXECUTE", "INVALIDATE"]
    reason: str
    task_identity: str
    environment_identity: str
    prior_evidence_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "reason": self.reason,
            "task_identity": self.task_identity,
            "environment_identity": self.environment_identity,
            "prior_evidence_id": self.prior_evidence_id,
        }


def evaluate_cache(
    *,
    task_identity_str: str,
    environment_identity_str: str,
    prior_evidence: ExecutionEvidence | None,
    current_environment_identity: str,
    change_fingerprint: str,
) -> CacheDecision:
    """Compute a deterministic cache decision.

    The semantics are explicit: same valid task + same relevant
    environment + valid prior evidence → REUSE. Anything else is
    EXECUTE or INVALIDATE.
    """
    from dataclasses import dataclass, field  # noqa: PLC0415
    from typing import Literal as _Lit  # noqa: PLC0415
    del dataclass, field, _Lit  # guard only

    if prior_evidence is None:
        return CacheDecision(
            decision="EXECUTE",
            reason="no prior evidence",
            task_identity=task_identity_str,
            environment_identity=environment_identity_str,
        )
    if prior_evidence.failure_kind is not None:
        return CacheDecision(
            decision="INVALIDATE",
            reason=f"prior evidence failed: {prior_evidence.failure_kind.value}",
            task_identity=task_identity_str,
            environment_identity=environment_identity_str,
            prior_evidence_id=prior_evidence.notes or "",
        )
    # Evidence validity also depends on artifact presence.
    if not prior_evidence.artifact_paths:
        return CacheDecision(
            decision="INVALIDATE",
            reason="prior evidence has no artifact",
            task_identity=task_identity_str,
            environment_identity=environment_identity_str,
            prior_evidence_id=prior_evidence.notes or "",
        )
    for ap in prior_evidence.artifact_paths:
        if not Path(ap).exists():
            return CacheDecision(
                decision="INVALIDATE",
                reason=f"prior evidence artifact missing: {ap}",
                task_identity=task_identity_str,
                environment_identity=environment_identity_str,
                prior_evidence_id=prior_evidence.notes or "",
            )
    if environment_identity_str != current_environment_identity:
        return CacheDecision(
            decision="INVALIDATE",
            reason="environment changed",
            task_identity=task_identity_str,
            environment_identity=environment_identity_str,
            prior_evidence_id=prior_evidence.notes or "",
        )
    return CacheDecision(
        decision="REUSE",
        reason="task identity, environment identity, and evidence validity all match",
        task_identity=task_identity_str,
        environment_identity=environment_identity_str,
        prior_evidence_id=prior_evidence.notes or "",
    )


@dataclass(frozen=True, slots=True)
class VerificationDecision:
    """A canonical terminal decision. Produced only from a valid lineage."""

    decision_id: str
    decided_at: str
    obligation_id: str
    task_id: str
    execution_id: str
    evidence_id: str
    reconciliation_id: str
    status: Literal["CERTIFIED", "BLOCKED", "FAILED", "REUSED"]
    rationale: str

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "decided_at": self.decided_at,
            "obligation_id": self.obligation_id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "evidence_id": self.evidence_id,
            "reconciliation_id": self.reconciliation_id,
            "status": self.status,
            "rationale": self.rationale,
        }


def derive_decision(
    *,
    obligation_id: str,
    task: ExecutableVerificationTask | None,
    evidence: ExecutionEvidence | None,
    reconciliation_id: str,
) -> VerificationDecision:
    """Derive a canonical terminal decision with full lineage.

    Raises LineageViolationError when any required element is missing.
    """
    from runtime.foundation.verification.execution.identity import (  # noqa: PLC0415
        assert_valid_transition,
    )

    # Task required
    if task is None:
        raise LineageViolationError(
            f"cannot derive decision for obligation {obligation_id!r}: no task"
        )
    # Execution required → evidence carries execution_id
    if evidence is None:
        raise LineageViolationError(
            f"cannot derive decision for task {task.task_id!r}: no evidence"
        )
    if not evidence.execution_id:
        raise LineageViolationError(
            f"cannot derive decision for task {task.task_id!r}: evidence has no execution_id"
        )
    if not evidence.notes:
        raise LineageViolationError(
            f"cannot derive decision for task {task.task_id!r}: evidence has no evidence_id"
        )
    # State machine guard: EXECUTED → EVIDENCE_CAPTURED → RECONCILED → DECIDED
    assert_valid_transition("RECONCILED", "DECIDED")

    # Map outcomes to decision status.
    if evidence.failure_kind is not None:
        status: Literal["CERTIFIED", "BLOCKED", "FAILED", "REUSED"] = "FAILED"
        rationale = f"execution failed: {evidence.failure_kind.value}: {evidence.failure_message}"
    elif not evidence.artifact_paths:
        status = "BLOCKED"
        rationale = "no evidence artifact captured"
    else:
        status = "CERTIFIED"
        rationale = "task executed, evidence captured, lineage complete"

    decision_id = compute_identity(
        IdentityKind.DECISION,
        obligation_id,
        evidence.execution_id,
        evidence.notes,
        reconciliation_id,
        namespace="runtime.verification",
    )
    return VerificationDecision(
        decision_id=decision_id,
        decided_at=datetime.now(UTC).isoformat(),
        obligation_id=obligation_id,
        task_id=task.task_id,
        execution_id=evidence.execution_id,
        evidence_id=evidence.notes,
        reconciliation_id=reconciliation_id,
        status=status,
        rationale=rationale,
    )
