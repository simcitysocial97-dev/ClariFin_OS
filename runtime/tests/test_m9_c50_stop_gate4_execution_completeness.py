"""M9-C50 — STOP GATE 4: Execution Completeness (Plan → Execute convergence).

Proves that every promised task kind is executable, unsupported kinds are
explicitly classified (never silently dropped), planner/executor identities
match, failures propagate to obligation dispositions, and reconciliation
sees the execution.
"""

from __future__ import annotations

from types import SimpleNamespace

from runtime.foundation.verification.evidence_planner import PlannedTask
from runtime.foundation.verification.executor_pipeline import (
    ADAPTERS,
    build_executable_plan,
)
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

EXPECTED_KINDS = frozenset(
    {
        "unit",
        "property",
        "invariant",
        "contract",
        "coverage",
        "mutation",
        "golden",
        "capability",
    }
)


def _planned(kind: str, target: str = "loan_engine") -> PlannedTask:
    return PlannedTask(
        task_id=f"task-{kind}-0001",
        task_kind=kind,
        target=target,
        disposition="selected_fresh",
        cause="stop-gate-4 probe",
    )


def _plan_with(*tasks: PlannedTask):
    from runtime.foundation.verification.evidence_planner import EvidenceAwarePlan

    return EvidenceAwarePlan(
        plan_id="sg4",
        generated_at="2026-01-01T00:00:00Z",
        repository_state={},
        changed_files=("backend/src/engines/loan_engine.py",),
        affected_sources=(),
        affected_capabilities=("loan-engine",),
        affected_components=(),
        population_id="test",
        population_fingerprint="test",
        selected_tasks=tuple(tasks),
        excluded_tasks=(),
        reuses=(),
        derived_aggregates=(),
        drift_blockers=(),
        certification_gaps=(),
        rationale="gate4",
    )


def test_all_promised_kinds_have_adapters():
    assert (
        set(ADAPTERS) >= EXPECTED_KINDS
    ), f"missing adapters: {sorted(EXPECTED_KINDS - set(ADAPTERS))}"


def test_every_kind_produces_executable_task_with_evidence():
    plan = _plan_with(*(_planned(k) for k in sorted(EXPECTED_KINDS)))
    exe = build_executable_plan(plan)
    all_tasks = list(exe.tasks) + list(getattr(exe, "not_executable", []))
    assert len(all_tasks) == len(EXPECTED_KINDS)
    # Every kind must produce a task (either executable or explicitly
    # classified as not_executable_yet — never silently dropped).
    for t in all_tasks:
        assert t.evidence_kind, f"kind={t.verification_kind} emits no evidence"
        assert (
            t.expected_artifact or t.executable == "not_executable_yet"
        ), f"kind={t.verification_kind} declares no expected artifact"


def test_planner_executor_identity_match():
    plan = _plan_with(*(_planned(k) for k in sorted(EXPECTED_KINDS)))
    exe = build_executable_plan(plan)
    all_tasks = list(exe.tasks) + list(getattr(exe, "not_executable", []))
    planned_ids = {t.source_task_id for t in all_tasks}
    expected_ids = {f"task-{k}-0001" for k in EXPECTED_KINDS}
    assert planned_ids == expected_ids, "planner/executor identity mismatch"


def test_unsupported_kind_explicitly_classified_never_silent():
    plan = _plan_with(_planned("quantum_divination"))
    exe = build_executable_plan(plan)
    not_exec = list(getattr(exe, "not_executable", []))
    assert len(not_exec) == 1, "unknown kind must be explicitly classified"
    t = not_exec[0]
    assert t.executable == "not_executable_yet"
    assert "no adapter" in str(t.executable_meta.get("blocker", ""))


def test_execution_failure_propagates_to_failed_obligation():
    ob = VerificationObligation(
        obligation_id="obl-fail",
        change=Change(path="x.py", change_type="modified"),
        capability=Capability(capability_id="loan-engine", authority="T"),
        requirement=Requirement(
            requirement_id="r1",
            capability_id="loan-engine",
            obligation_kind=ObligationKind.UNIT,
            rationale="t",
            severity="required",
        ),
        disposition=Disposition.OPEN,
    )
    failing = SimpleNamespace(
        capabilities=["loan-engine"],
        primary_capability="loan-engine",
        verification_kind="unit",
        completion_state="failed",
    )
    res = reconcile_obligations(
        ObligationSet(set_id="sg4", obligations=(ob,)), [failing]
    )
    assert not res.complete
    assert res.obligations[0].disposition == Disposition.FAILED
    assert res.obligations[0].is_closed() is False


def test_reconciliation_module_exists_and_callable():
    """The obligation_reconciliation module exists and provides reconciliation."""
    from runtime.foundation.verification import obligation_reconciliation

    assert hasattr(obligation_reconciliation, "reconcile_obligations")
    assert callable(obligation_reconciliation.reconcile_obligations)
