"""M9-C50 — STOP GATE 2: Obligation ↔ Execution Reconciliation.

Proves that a successful verification cannot be produced while required
obligations are unsatisfied, and that obligation dispositions are derived from
the actual execution records (failed/auth/missing cannot close).
"""

from __future__ import annotations

from types import SimpleNamespace

from runtime.foundation.verification.obligation import (
    Capability,
    Change,
    Disposition,
    ObligationKind,
    ObligationSet,
    Requirement,
    VerificationObligation,
)
from runtime.foundation.verification.obligation_reconciliation import (
    reconcile_obligations,
)


def _ob(cap_id: str, kind: ObligationKind, disposition=Disposition.OPEN):
    change = Change(path="x.py", change_type="modified")
    cap = Capability(capability_id=cap_id, authority="Test")
    req = Requirement(
        requirement_id=f"r-{cap_id}",
        capability_id=cap_id,
        obligation_kind=kind,
        rationale="test",
        severity="required",
    )
    return VerificationObligation(
        obligation_id=f"obl-{cap_id}",
        change=change,
        capability=cap,
        requirement=req,
        disposition=disposition,
    )


def _rec(cap_id, kind, state):
    return SimpleNamespace(
        capabilities=[cap_id],
        primary_capability=cap_id,
        verification_kind=kind,
        completion_state=state,
    )


def test_passing_record_closes_obligation():
    res = reconcile_obligations(
        ObligationSet("s", (_ob("c1", ObligationKind.UNIT),)),
        [_rec("c1", "unit", "pass")],
    )
    assert res.complete
    assert res.obligations[0].disposition == Disposition.CLOSED


def test_failed_record_cannot_complete():
    res = reconcile_obligations(
        ObligationSet("s", (_ob("c1", ObligationKind.UNIT),)),
        [_rec("c1", "unit", "failed")],
    )
    assert not res.complete
    assert res.obligations[0].disposition == Disposition.FAILED


def test_missing_record_means_task_disappeared():
    res = reconcile_obligations(
        ObligationSet("s", (_ob("c1", ObligationKind.UNIT),)),
        [],
    )
    assert not res.complete
    assert res.obligations[0].disposition == Disposition.FAILED


def test_authorization_required_blocks_but_not_failed():
    res = reconcile_obligations(
        ObligationSet("s", (_ob("c1", ObligationKind.MUTATION),)),
        [_rec("c1", "mutation", "authorization_required")],
    )
    assert not res.complete
    assert res.obligations[0].disposition == Disposition.BLOCKED


def test_kind_and_capability_must_both_match():
    # record serves c2 not c1 -> obligation c1 unsatisfied
    res = reconcile_obligations(
        ObligationSet("s", (_ob("c1", ObligationKind.UNIT),)),
        [_rec("c2", "unit", "pass")],
    )
    assert not res.complete


def test_complete_requires_all_required_satisfied():
    res = reconcile_obligations(
        ObligationSet(
            "s",
            (
                _ob("c1", ObligationKind.UNIT),
                _ob("c2", ObligationKind.MUTATION),
            ),
        ),
        [_rec("c1", "unit", "pass"), _rec("c2", "mutation", "failed")],
    )
    assert not res.complete
    assert res.satisfied == 1
    assert res.total_required == 2
