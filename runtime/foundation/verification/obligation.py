"""
M9-C49 — Verification Obligation Model.

The control plane reasons in terms of *obligations*, not files or commands:

    Change
       ↓
    Capability
       ↓
    Requirement
       ↓
    Verification Obligation
       ↓
    Task
       ↓
    Evidence
       ↓
    Disposition

An obligation is closed only when the required evidence exists, is current,
and is valid. The disposition vocabulary is closed:

    CLOSED          — required evidence exists and is valid
    EXECUTED        — task ran, evidence captured (still needs disposition)
    OPEN            — task not yet run; no evidence
    BLOCKED         — task cannot run (scope, config, infra)
    INVALIDATED     — prior evidence was invalidated; needs re-execution
    REUSED          — valid prior evidence; obligation closed without execution
    NOT_APPLICABLE  — obligation does not apply for this change
    FAILED          — task ran; required evidence not produced

This module is pure: no I/O. The control plane facade is the only writer.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


class Disposition(str, Enum):
    """Closed disposition vocabulary for verification obligations."""

    CLOSED = "closed"
    EXECUTED = "executed"
    OPEN = "open"
    BLOCKED = "blocked"
    INVALIDATED = "invalidated"
    REUSED = "reused"
    NOT_APPLICABLE = "not_applicable"
    FAILED = "failed"


class ObligationKind(str, Enum):
    """Closed vocabulary for the *kind* of verification an obligation
    represents. Mirrors the executor's VerificationKind."""

    UNIT = "unit"
    PROPERTY = "property"
    INVARIANT = "invariant"
    CONTRACT = "contract"
    COVERAGE = "coverage"
    MUTATION = "mutation"
    GOLDEN = "golden"
    CAPABILITY = "capability"


@dataclass(frozen=True, slots=True)
class Change:
    """The minimal change record the control plane reasons about."""

    path: str
    change_type: str  # "added" | "modified" | "deleted" | "renamed"
    symbol: str | None = None
    old_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "change_type": self.change_type,
            "symbol": self.symbol,
            "old_path": self.old_path,
        }


@dataclass(frozen=True, slots=True)
class Capability:
    """A canonical capability identity."""

    capability_id: str
    authority: str  # which authority declared it
    severity: str = "required"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "authority": self.authority,
            "severity": self.severity,
            "description": self.description,
        }


@dataclass(frozen=True, slots=True)
class Requirement:
    """A single verification requirement derived from a capability."""

    requirement_id: str
    capability_id: str
    obligation_kind: ObligationKind
    rationale: str
    severity: str = "required"  # blocking | required | prioritized | optional
    target: str = ""  # engine / module / file the obligation applies to

    def to_dict(self) -> dict[str, Any]:
        return {
            "requirement_id": self.requirement_id,
            "capability_id": self.capability_id,
            "obligation_kind": self.obligation_kind.value,
            "rationale": self.rationale,
            "severity": self.severity,
            "target": self.target,
        }


@dataclass(frozen=True, slots=True)
class EvidenceRef:
    """Reference to an evidence artifact produced by (or reusable for) an
    obligation."""

    evidence_id: str
    kind: str  # "pytest-junit" | "mutation-summary" | "coverage-truth" | ...
    artifact_path: str
    produced_at: str
    fingerprint: str
    is_fresh: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "kind": self.kind,
            "artifact_path": self.artifact_path,
            "produced_at": self.produced_at,
            "fingerprint": self.fingerprint,
            "is_fresh": self.is_fresh,
        }


@dataclass(frozen=True, slots=True)
class VerificationObligation:
    """A single verification obligation in the control plane.

    An obligation is closed only when the required evidence exists and is
    valid. The control plane owns the full lifecycle.
    """

    obligation_id: str
    change: Change
    capability: Capability
    requirement: Requirement
    disposition: Disposition = Disposition.OPEN
    task_id: str | None = None
    evidence: tuple[EvidenceRef, ...] = ()
    reasons: tuple[str, ...] = ()
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    closed_at: str | None = None

    def is_closed(self) -> bool:
        return self.disposition == Disposition.CLOSED

    def fingerprint(self) -> str:
        h = hashlib.sha256()
        h.update(self.obligation_id.encode())
        h.update(self.change.path.encode())
        h.update(self.capability.capability_id.encode())
        h.update(self.requirement.obligation_kind.value.encode())
        h.update(self.disposition.value.encode())
        h.update(str(len(self.evidence)).encode())
        return h.hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "obligation_id": self.obligation_id,
            "change": self.change.to_dict(),
            "capability": self.capability.to_dict(),
            "requirement": self.requirement.to_dict(),
            "disposition": self.disposition.value,
            "task_id": self.task_id,
            "evidence": [e.to_dict() for e in self.evidence],
            "reasons": list(self.reasons),
            "created_at": self.created_at,
            "closed_at": self.closed_at,
            "fingerprint": self.fingerprint(),
        }


@dataclass(frozen=True, slots=True)
class ObligationSet:
    """A complete set of obligations for one control-plane invocation."""

    set_id: str
    obligations: tuple[VerificationObligation, ...]
    generated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    repository_sha: str = "unknown"
    plan_fingerprint: str = ""

    def closed(self) -> tuple[VerificationObligation, ...]:
        return tuple(o for o in self.obligations if o.is_closed())

    def open(self) -> tuple[VerificationObligation, ...]:
        return tuple(o for o in self.obligations if not o.is_closed())

    def blocked(self) -> tuple[VerificationObligation, ...]:
        return tuple(
            o for o in self.obligations if o.disposition == Disposition.BLOCKED
        )

    def failed(self) -> tuple[VerificationObligation, ...]:
        return tuple(o for o in self.obligations if o.disposition == Disposition.FAILED)

    def reuse_count(self) -> int:
        return sum(1 for o in self.obligations if o.disposition == Disposition.REUSED)

    def invalidate_count(self) -> int:
        return sum(
            1 for o in self.obligations if o.disposition == Disposition.INVALIDATED
        )

    def fingerprint(self) -> str:
        h = hashlib.sha256()
        for o in self.obligations:
            h.update(o.fingerprint().encode())
        return h.hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "set_id": self.set_id,
            "obligations": [o.to_dict() for o in self.obligations],
            "generated_at": self.generated_at,
            "repository_sha": self.repository_sha,
            "plan_fingerprint": self.plan_fingerprint,
            "set_fingerprint": self.fingerprint(),
            "summary": {
                "total": len(self.obligations),
                "closed": len(self.closed()),
                "open": len(self.open()),
                "blocked": len(self.blocked()),
                "failed": len(self.failed()),
                "reused": self.reuse_count(),
                "invalidated": self.invalidate_count(),
            },
        }


def serialize_obligation_set(obligation_set: ObligationSet) -> str:
    """JSON serialization for ledger persistence."""
    return json.dumps(obligation_set.to_dict(), indent=2, default=str)


def obligations_from_dict(data: dict[str, Any]) -> ObligationSet:
    """Rehydrate an obligation set from its JSON form. Used by ledger round-trips
    and by the planner↔executor handoff."""

    obligations: list[VerificationObligation] = []
    for od in data.get("obligations", []):
        change = Change(
            path=od["change"]["path"],
            change_type=od["change"]["change_type"],
            symbol=od["change"].get("symbol"),
            old_path=od["change"].get("old_path"),
        )
        cap = Capability(
            capability_id=od["capability"]["capability_id"],
            authority=od["capability"]["authority"],
            severity=od["capability"].get("severity", "required"),
            description=od["capability"].get("description", ""),
        )
        req = Requirement(
            requirement_id=od["requirement"]["requirement_id"],
            capability_id=od["requirement"]["capability_id"],
            obligation_kind=ObligationKind(od["requirement"]["obligation_kind"]),
            rationale=od["requirement"].get("rationale", ""),
            severity=od["requirement"].get("severity", "required"),
            target=od["requirement"].get("target", ""),
        )
        evidence = tuple(
            EvidenceRef(
                evidence_id=ed["evidence_id"],
                kind=ed["kind"],
                artifact_path=ed["artifact_path"],
                produced_at=ed["produced_at"],
                fingerprint=ed["fingerprint"],
                is_fresh=ed.get("is_fresh", True),
            )
            for ed in od.get("evidence", [])
        )
        obligations.append(
            VerificationObligation(
                obligation_id=od["obligation_id"],
                change=change,
                capability=cap,
                requirement=req,
                disposition=Disposition(od["disposition"]),
                task_id=od.get("task_id"),
                evidence=evidence,
                reasons=tuple(od.get("reasons", [])),
                created_at=od.get("created_at", ""),
                closed_at=od.get("closed_at"),
            )
        )
    return ObligationSet(
        set_id=data["set_id"],
        obligations=tuple(obligations),
        generated_at=data.get("generated_at", ""),
        repository_sha=data.get("repository_sha", "unknown"),
        plan_fingerprint=data.get("plan_fingerprint", ""),
    )
