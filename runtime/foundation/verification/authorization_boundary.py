# runtime/foundation/verification/authorization_boundary.py
#
# M9-C53 — Human Authorization Boundary.
#
# Preserves the C42/C48/C52 authorization boundary. The system may:
#   - discover gaps, classify gaps, propose tests, generate candidate tests,
#     execute candidate validation, produce evidence, recommend acceptance.
# The system must NOT silently promote a generated test into the authoritative
# repository test suite when the existing authorization contract requires
# human approval.
#
# Authorization states (closed):
#   PROPOSED                  — candidate generated, not yet validated
#   VALIDATED                 — candidate passed validation
#   AWAITING_HUMAN_AUTHORIZATION — validated, waiting for human decision
#   AUTHORIZED                — human authorized the candidate
#   REJECTED                  — human rejected the candidate
#   EXPIRED                   — authorization window expired

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class AuthorizationState(str):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    AWAITING_HUMAN_AUTHORIZATION = "AWAITING_HUMAN_AUTHORIZATION"
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


VALID_TRANSITIONS: dict[str, tuple[str, ...]] = {
    AuthorizationState.PROPOSED: (
        AuthorizationState.VALIDATED,
        AuthorizationState.REJECTED,
    ),
    AuthorizationState.VALIDATED: (
        AuthorizationState.AWAITING_HUMAN_AUTHORIZATION,
        AuthorizationState.REJECTED,
    ),
    AuthorizationState.AWAITING_HUMAN_AUTHORIZATION: (
        AuthorizationState.AUTHORIZED,
        AuthorizationState.REJECTED,
        AuthorizationState.EXPIRED,
    ),
    AuthorizationState.AUTHORIZED: (),  # terminal
    AuthorizationState.REJECTED: (),  # terminal
    AuthorizationState.EXPIRED: (),  # terminal
}


@dataclass(frozen=True, slots=True)
class AuthorizationRecord:
    """One authorization decision record."""

    record_id: str
    candidate_id: str
    generation_id: str
    state: str
    previous_state: str
    decided_at: str
    actor: str  # "system" | "human:<id>" | "authorization-boundary"
    reason: str
    conditions: tuple[str, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "candidate_id": self.candidate_id,
            "generation_id": self.generation_id,
            "state": self.state,
            "previous_state": self.previous_state,
            "decided_at": self.decided_at,
            "actor": self.actor,
            "reason": self.reason,
            "conditions": list(self.conditions),
            "evidence": self.evidence,
        }


@dataclass(frozen=True, slots=True)
class AuthorizationBoundaryReport:
    """Complete authorization boundary report."""

    schema: str = "m9-c53-authorization-boundary/v1"
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    records: list[AuthorizationRecord] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "records": [r.to_dict() for r in self.records],
            "summary": self.summary,
        }


def _id(*parts: str) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:12]


def create_proposed_state(
    candidate_id: str,
    generation_id: str,
    *,
    evidence: dict[str, Any] | None = None,
) -> AuthorizationRecord:
    """Create the initial PROPOSED state for a candidate."""
    return AuthorizationRecord(
        record_id=f"auth::{_id(candidate_id, generation_id, 'proposed')}",
        candidate_id=candidate_id,
        generation_id=generation_id,
        state=AuthorizationState.PROPOSED,
        previous_state="",
        decided_at=datetime.now(UTC).isoformat(),
        actor="system",
        reason="candidate test generated from evidence",
        evidence=evidence or {},
    )


def transition_state(
    current: AuthorizationRecord,
    new_state: str,
    *,
    actor: str,
    reason: str,
    conditions: tuple[str, ...] = (),
    evidence: dict[str, Any] | None = None,
) -> AuthorizationRecord:
    """Transition an authorization record to a new state.

    Enforces valid state transitions. Invalid transitions raise ValueError.
    """
    if new_state not in VALID_TRANSITIONS.get(current.state, ()):
        raise ValueError(
            f"invalid state transition: {current.state} -> {new_state}. "
            f"Valid transitions from {current.state}: {VALID_TRANSITIONS.get(current.state, ())}"
        )

    return AuthorizationRecord(
        record_id=f"auth::{_id(current.candidate_id, current.generation_id, new_state)}",
        candidate_id=current.candidate_id,
        generation_id=current.generation_id,
        state=new_state,
        previous_state=current.state,
        decided_at=datetime.now(UTC).isoformat(),
        actor=actor,
        reason=reason,
        conditions=conditions,
        evidence=evidence or {},
    )


def evaluate_authorization(
    candidate_id: str,
    generation_id: str,
    *,
    validation_passed: bool,
    gap_class: str,
    authorization_required: bool,
    evidence: dict[str, Any] | None = None,
) -> list[AuthorizationRecord]:
    """Evaluate the full authorization path for a candidate.

    Returns the chain of authorization records from PROPOSED through
    the appropriate terminal state (AWAITING_HUMAN_AUTHORIZATION for
    candidates that require human approval).
    """
    records: list[AuthorizationRecord] = []

    # 1. PROPOSED
    proposed = create_proposed_state(candidate_id, generation_id, evidence=evidence)
    records.append(proposed)

    # If validation failed, reject immediately
    if not validation_passed:
        records.append(
            transition_state(
                proposed,
                AuthorizationState.REJECTED,
                actor="authorization-boundary",
                reason="candidate failed validation; rejected before authorization",
                evidence=evidence,
            )
        )
        return records

    # 2. VALIDATED
    validated = transition_state(
        proposed,
        AuthorizationState.VALIDATED,
        actor="system",
        reason="candidate passed all 8 validation dimensions",
        evidence=evidence,
    )
    records.append(validated)

    # 3. If authorization is required, transition to AWAITING_HUMAN_AUTHORIZATION
    if authorization_required:
        awaiting = transition_state(
            validated,
            AuthorizationState.AWAITING_HUMAN_AUTHORIZATION,
            actor="authorization-boundary",
            reason=(
                "human authorization required: the system may propose and "
                "validate candidate tests but must NOT silently promote a "
                "generated test into the authoritative repository test suite"
            ),
            conditions=(
                "human must review candidate test",
                "human must verify behavioral justification",
                "human must authorize acceptance or rejection",
            ),
            evidence=evidence,
        )
        records.append(awaiting)
    else:
        # Auto-authorize: no human authorization required
        # Transition through AWAITING_HUMAN_AUTHORIZATION → AUTHORIZED
        awaiting = transition_state(
            validated,
            AuthorizationState.AWAITING_HUMAN_AUTHORIZATION,
            actor="authorization-boundary",
            reason="auto-authorization path: no human authorization required",
            evidence=evidence,
        )
        records.append(awaiting)
        authorized = transition_state(
            awaiting,
            AuthorizationState.AUTHORIZED,
            actor="authorization-boundary",
            reason="auto-authorized: authorization_required=False",
            evidence=evidence,
        )
        records.append(authorized)

    return records


def build_authorization_report(
    records: list[AuthorizationRecord],
) -> AuthorizationBoundaryReport:
    """Build the authorization boundary report from records."""
    summary: dict[str, int] = {}
    for r in records:
        summary[r.state] = summary.get(r.state, 0) + 1

    return AuthorizationBoundaryReport(
        records=records,
        summary=summary,
    )


def persist_authorization_records(
    records: list[AuthorizationRecord],
    out_path: Path,
) -> dict[str, Any]:
    """Persist authorization records to a JSON artifact."""
    artifact = {
        "schema": "m9-c53-authorization-boundary/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "boundary": {
            "self_approval": "FORBIDDEN — the system must NOT silently promote "
            "a generated test into the authoritative repository test suite",
            "promotion_authority": "human authorization gate",
            "valid_states": list(
                set(AuthorizationState.PROPOSED, AuthorizationState.VALIDATED)
                | {AuthorizationState.AWAITING_HUMAN_AUTHORIZATION}
                | {
                    AuthorizationState.AUTHORIZED,
                    AuthorizationState.REJECTED,
                    AuthorizationState.EXPIRED,
                }
            ),
            "valid_transitions": {k: list(v) for k, v in VALID_TRANSITIONS.items()},
        },
        "records": [r.to_dict() for r in records],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2))
    return artifact


__all__ = [
    "AuthorizationState",
    "VALID_TRANSITIONS",
    "AuthorizationRecord",
    "AuthorizationBoundaryReport",
    "create_proposed_state",
    "transition_state",
    "evaluate_authorization",
    "build_authorization_report",
    "persist_authorization_records",
]
