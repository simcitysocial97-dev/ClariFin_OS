"""M50 S1 + S5 — Canonical execution contract identities and state machine.

Single source of truth for verification lifecycle identities and the
state machine that gates every transition. These types are the contract
between the planner, the executor, the reconciliation layer, and any
downstream consumer (CI, governance, self-verification).

Lineage requirement (enforced at every transition):
  obligation → task → execution → evidence → reconciliation → decision

No element may be constructed without its predecessor. The contract is
therefore derivable from preceding valid states only.
"""

from __future__ import annotations

import hashlib


# Stable identity vocabulary. These prefixes are part of the public API;
# changing them requires explicit architectural review.
class IdentityKind:
    OBLIGATION = "obl"
    TASK = "task"
    EXECUTION = "exec"
    EVIDENCE = "ev"
    RECONCILIATION = "rec"
    DECISION = "dec"
    RUN = "run"


# Lifecycle states. Transitions are validated by the state machine.
VALID_STATES = frozenset(
    {
        "PLANNED",
        "DISPATCHED",
        "EXECUTING",
        "EXECUTED",
        "FAILED",
        "BLOCKED",
        "EVIDENCE_CAPTURED",
        "RECONCILED",
        "REUSED",
        "INVALIDATED",
        "DECIDED",
    }
)

# Transition graph: from -> {to_set}
_TRANSITIONS: dict[str, frozenset[str]] = {
    "PLANNED": frozenset({"DISPATCHED", "BLOCKED"}),
    "DISPATCHED": frozenset({"EXECUTING", "BLOCKED"}),
    "EXECUTING": frozenset({"EXECUTED", "FAILED"}),
    "EXECUTED": frozenset({"EVIDENCE_CAPTURED", "FAILED"}),
    "EVIDENCE_CAPTURED": frozenset({"RECONCILED", "INVALIDATED"}),
    "RECONCILED": frozenset({"DECIDED"}),
    "REUSED": frozenset({"RECONCILED"}),
    "INVALIDATED": frozenset({"DISPATCHED"}),  # re-execute
    "FAILED": frozenset({"DECIDED", "BLOCKED"}),
    "BLOCKED": frozenset({"DECIDED"}),
    "DECIDED": frozenset(),  # terminal
}


def is_valid_transition(from_state: str, to_state: str) -> bool:
    """Return True if the lifecycle transition is permitted."""
    if from_state not in VALID_STATES or to_state not in VALID_STATES:
        return False
    return to_state in _TRANSITIONS.get(from_state, frozenset())


def assert_valid_transition(from_state: str, to_state: str) -> None:
    """Raise ValueError if the transition is not permitted.

    The runtime NEVER manufactures a CERTIFIED or DECIDED state without
    passing through the canonical pipeline. Examples of forbidden
    transitions that this guard rejects:
        PLANNED -> DECIDED
        EXECUTING -> CERTIFIED
        FAILED -> CERTIFIED
    """
    if not is_valid_transition(from_state, to_state):
        raise ValueError(f"forbidden lifecycle transition: {from_state} -> {to_state}")


# ===========================================================================
# M50 S5 — Deterministic identity model
#
# Each identity is a sha256 over the semantic inputs that determine its
# validity. Same inputs always produce the same identity. Different
# inputs always produce different identities.
# ===========================================================================


def compute_identity(
    kind: str,
    *inputs: str,
    namespace: str | None = None,
) -> str:
    """Return a deterministic identity of the form '<kind>::<prefix>:<sha>'.

    ``inputs`` are concatenated with ``|`` separators in the order given.
    ``namespace`` is an optional prefix to avoid cross-purpose collisions.
    """
    h = hashlib.sha256()
    if namespace:
        h.update(namespace.encode())
    h.update(b"\x00")
    h.update("|".join(inputs).encode())
    digest = h.hexdigest()[:16]
    prefix = f"{namespace}::{kind}" if namespace else kind
    return f"{prefix}::{digest}"


def task_identity(
    change_identity: str,
    capability_identity: str,
    verification_kind: str,
    target: str,
    verification_policy: str,
) -> str:
    """Semantic task identity. A change in any input changes the identity."""
    return compute_identity(
        IdentityKind.TASK,
        change_identity,
        capability_identity,
        verification_kind,
        target,
        verification_policy,
        namespace="runtime.verification",
    )


def evidence_identity(
    execution_id: str,
    artifact_sha256: str,
    environment_identity: str,
    evidence_kind: str,
) -> str:
    """Evidence identity depends on execution, artifact, environment, kind.

    Stale evidence (mismatched environment) cannot satisfy this identity
    without re-execution.
    """
    return compute_identity(
        IdentityKind.EVIDENCE,
        execution_id,
        artifact_sha256,
        environment_identity,
        evidence_kind,
        namespace="runtime.verification",
    )


def environment_identity(parts: dict[str, str]) -> str:
    """Deterministic environment identity over ordered key=value parts."""
    return compute_identity(
        "env",
        *(f"{k}={parts[k]}" for k in sorted(parts)),
        namespace="runtime.verification",
    )
