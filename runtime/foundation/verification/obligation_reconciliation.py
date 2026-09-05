"""M9-C50 — Obligation ↔ Execution Reconciliation (STOP GATE 2).

Closes the Phase-2 obligation-integrity gap: the obligation set that the
control plane derives from a plan was previously NOT consulted by the verdict
path, so a run could be CERTIFIED while required obligations remained OPEN.

This module reconciles each obligation's disposition against the executed
execution records, then provides a completeness check that the control plane
uses to refuse success when required obligations are unsatisfied.

No new authority is created here — this is a projection over the canonical
obligation model (``runtime.foundation.verification.obligation``) and the
canonical execution report (``ExecutionReport.records``).
"""

from __future__ import annotations

from dataclasses import replace

from runtime.foundation.verification.obligation import (
    Disposition,
    ObligationSet,
    VerificationObligation,
)

# CompletionState values from execution_orchestrator (kept as literals to avoid
# a hard import cycle into the facade layer; source of truth remains the enum).
_PASSING_STATES = {"pass", "reused", "skipped"}
_BLOCKING_STATES = {
    "authorization_required",
    "infrastructure",
    "timeout",
    "scope",
    "configuration",
    "certification",
    "evidence",
}


def reconcile_obligations(
    obligation_set: ObligationSet,
    records: list,
) -> ObAnalyzeResult:
    """Map each obligation to a satisfying execution record and derive a new
    disposition, then report completeness.

    Matching rule: an execution record satisfies an obligation when its
    ``capabilities`` includes the obligation's capability_id AND its
    ``verification_kind`` equals the obligation's obligation_kind. Records that
    have a matching capability are examined for the first non-blocking PASSING
    state; if none passing, the obligation is FAILED (or BLOCKED for
    authorization/infrastructure with no pass).

    Returns the reconciled obligation tuples plus a completeness summary.
    """

    out: list[VerificationObligation] = []
    satisfied = 0
    total_required = 0
    failed_obligations: list[str] = []

    for ob in obligation_set.obligations:
        if ob.disposition == Disposition.NOT_APPLICABLE:
            out.append(ob)
            continue
        total_required += 1

        cap = ob.capability.capability_id
        kind = ob.requirement.obligation_kind.value

        candidate_states: list[str] = []
        for rec in records:
            caps = getattr(rec, "capabilities", None) or [getattr(rec, "primary_capability", "")]
            rkind = getattr(rec, "verification_kind", "")
            if cap in caps and rkind == kind:
                candidate_states.append(str(getattr(rec, "completion_state", "")))

        if not candidate_states:
            # No execution record served this requirement — task disappeared.
            out.append(
                replace(ob, disposition=Disposition.FAILED)
            )
            failed_obligations.append(ob.obligation_id)
            continue

        if any(s in _PASSING_STATES for s in candidate_states):
            if ob.disposition == Disposition.REUSED:
                out.append(ob)
                satisfied += 1
            else:
                out.append(replace(ob, disposition=Disposition.CLOSED))
                satisfied += 1
        elif any(s == "reused" for s in candidate_states):
            out.append(replace(ob, disposition=Disposition.REUSED))
            satisfied += 1
        elif any(s in _BLOCKING_STATES for s in candidate_states):
            out.append(replace(ob, disposition=Disposition.BLOCKED))
        else:
            out.append(replace(ob, disposition=Disposition.FAILED))
            failed_obligations.append(ob.obligation_id)

    return ObAnalyzeResult(
        obligations=tuple(out),
        satisfied=satisfied,
        total_required=total_required,
        failed_obligations=failed_obligations,
        complete=(satisfied == total_required and total_required > 0),
    )


class ObAnalyzeResult:
    """Outcome of reconciling an obligation set against execution records."""

    __slots__ = (
        "obligations",
        "satisfied",
        "total_required",
        "failed_obligations",
        "complete",
    )

    def __init__(
        self,
        *,
        obligations: tuple,
        satisfied: int,
        total_required: int,
        failed_obligations: list,
        complete: bool,
    ) -> None:
        self.obligations = obligations
        self.satisfied = satisfied
        self.total_required = total_required
        self.failed_obligations = failed_obligations
        self.complete = complete
