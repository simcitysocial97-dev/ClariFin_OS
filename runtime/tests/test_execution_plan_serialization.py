"""M10-R2 (C1) — Plan serialization is real, and a supplied plan is authoritative.

Before M10-R2 a plan *file* was decorative. ``ControlPlane.run`` read it, looked for
``ControlPlanePlan.from_dict`` with ``hasattr``, found nothing, discarded the payload
it had just parsed, and rebuilt the whole plan from the changed files. A corrupt plan
file exited 0. Every one of those is now a hard error, because ``check --shard``
depends on a shard executing *only* what it was handed.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from runtime.foundation.verification.control_plane_facade import ControlPlane
from runtime.foundation.verification.execution_orchestrator import (
    ExecutionOrchestrator,
    ExecutionPlan,
    ExecutionTaskSpec,
    RepositoryFingerprint,
)

CHANGED = ["backend/src/engines/loan_engine/amortization.py"]


def _plan() -> ExecutionPlan:
    return ExecutionOrchestrator().build_execution_plan(CHANGED)


# ---------------------------------------------------------------------------
# Round trip
# ---------------------------------------------------------------------------


def test_task_spec_round_trips_field_for_field():
    """Every declared field must survive. This is the test that would have caught
    the four ``ExecutionTaskSpec(**spec.to_dict())`` rebuild sites silently turning
    the eight ``tuple[str, ...]`` fields into lists."""
    spec = _plan().tasks[0]
    back = ExecutionTaskSpec.from_dict(spec.to_dict())
    assert back == spec
    for f in dataclasses.fields(spec):
        assert getattr(back, f.name) == getattr(spec, f.name), f.name


def test_plan_round_trips_field_for_field():
    plan = _plan()
    back = ExecutionPlan.from_dict(plan.to_dict())
    assert back.plan_id == plan.plan_id
    assert back.plan_fingerprint == plan.plan_fingerprint
    assert back.tasks == plan.tasks
    for f in dataclasses.fields(ExecutionPlan):
        if f.name in ("tasks", "repository_fingerprint"):
            continue
        assert getattr(back, f.name) == getattr(plan, f.name), f.name


def test_tuple_fields_survive_the_round_trip_as_tuples():
    plan = _plan()
    for spec in plan.tasks:
        for name in (
            "capabilities",
            "prerequisites",
            "depends_on",
            "expected_evidence",
            "measurement_required",
            "escalation_conditions",
            "evidence_reused",
            "evidence_invalidated",
        ):
            assert isinstance(getattr(spec, name), tuple), (spec.task_id, name)


def test_plan_fingerprint_is_stable_across_a_round_trip():
    """The fingerprint is what every shard asserts against the plan job, so a
    round-trip that changed it would make every shard look divergent."""
    plan = _plan()
    assert (
        ExecutionPlan.from_dict(plan.to_dict()).plan_fingerprint
        == plan.plan_fingerprint
    )


def test_building_the_plan_twice_is_still_deterministic():
    a, b = _plan(), _plan()
    assert a.plan_fingerprint == b.plan_fingerprint
    assert [t.task_id for t in a.tasks] == [t.task_id for t in b.tasks]
    assert a.tasks == b.tasks


def test_fingerprint_round_trips():
    plan = _plan()
    back = ExecutionPlan.from_dict(plan.to_dict())
    assert back.repository_fingerprint == plan.repository_fingerprint
    assert (
        back.repository_fingerprint.fingerprint
        == plan.repository_fingerprint.fingerprint
    )


# ---------------------------------------------------------------------------
# Tolerance and rejection
# ---------------------------------------------------------------------------


def test_unknown_keys_are_tolerated():
    """A newer producer writing to an older consumer must not be a hard failure."""
    payload = dict(_plan().to_dict())
    payload["a_field_from_the_future"] = {"nested": [1, 2, 3]}
    assert ExecutionPlan.from_dict(payload).plan_id == _plan().plan_id


def test_missing_optional_fields_fall_back_to_dataclass_defaults():
    payload = _plan().tasks[0].to_dict()
    for defaulted in (
        "prerequisites",
        "depends_on",
        "expected_evidence",
        "measurement_required",
        "escalation_conditions",
        "authorization_required",
        "timeout_seconds",
        "failure_policy",
        "evidence_reused",
        "evidence_invalidated",
        "estimated_duration_seconds",
        "mutation_target",
    ):
        payload.pop(defaulted, None)
    rebuilt = ExecutionTaskSpec.from_dict(payload)
    assert rebuilt.timeout_seconds == 600
    assert rebuilt.depends_on == ()
    assert rebuilt.authorization_required is False


def test_correct_schema_is_accepted_and_a_foreign_one_is_rejected():
    plan = _plan()
    assert ExecutionPlan.SCHEMA in plan.to_dict()["schema"]
    payload = dict(plan.to_dict())
    payload["schema"] = "m9-c49-execution-plan/v99"
    with pytest.raises(ValueError, match="unsupported execution plan schema"):
        ExecutionPlan.from_dict(payload)


def test_a_payload_without_a_schema_key_is_accepted():
    """Tolerates a hand-written plan; only an unrecognised schema is fatal."""
    payload = dict(_plan().to_dict())
    payload.pop("schema")
    assert ExecutionPlan.from_dict(payload).plan_id == _plan().plan_id


def test_spec_reconstruction_requires_the_non_default_fields():
    """A spec missing ``command`` must not silently become an empty-command task:
    ``ExecutionPlan.validate`` reports empty commands, but only if construction got
    far enough to produce one."""
    with pytest.raises(TypeError):
        ExecutionTaskSpec.from_dict({"task_id": "exec-0001"})


# ---------------------------------------------------------------------------
# run --plan is authoritative  (the F7 regression)
# ---------------------------------------------------------------------------


def test_run_executes_exactly_the_tasks_in_the_supplied_plan(tmp_path, monkeypatch):
    """The core regression. A one-task plan must execute one task, even though the
    live boundary would expand to eight."""
    plan = _plan()
    single = ExecutionPlan(
        plan_id=plan.plan_id,
        source_plan_id=plan.source_plan_id,
        repository_fingerprint=plan.repository_fingerprint,
        changed_files=list(plan.changed_files),
        affected_capabilities=list(plan.affected_capabilities),
        affected_components=list(plan.affected_components),
        invalidated_evidence=list(plan.invalidated_evidence),
        reusable_evidence=list(plan.reusable_evidence),
        tasks=[plan.tasks[0]],
        escalation_conditions=list(plan.escalation_conditions),
        measurement_requirements=list(plan.measurement_requirements),
        certification_requirements=list(plan.certification_requirements),
        rationale="single-task plan",
        plan_fingerprint=plan.plan_fingerprint,
        generated_at=plan.generated_at,
        revalidation_sources=list(plan.revalidation_sources),
        reusable_measurements=list(plan.reusable_measurements),
    )
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(single.to_dict()), encoding="utf-8")

    seen: list[str] = []

    def _fake_shell(spec, _plan, *_a, **_k):
        from runtime.foundation.verification.execution_orchestrator import (
            CompletionState,
        )

        seen.append(spec.task_id)
        return _ok_record(spec, single, CompletionState.PASS)

    monkeypatch.setattr(
        ExecutionOrchestrator, "_execute_shell_task", staticmethod(_fake_shell)
    )
    ControlPlane().run(plan_path=str(path))

    assert seen == [single.tasks[0].task_id]


def test_run_rejects_a_corrupt_plan_file_instead_of_regenerating(tmp_path, capsys):
    """Before M10-R2 this exited 0 after silently regenerating the whole plan."""
    path = tmp_path / "broken.json"
    path.write_text("{ not json", encoding="utf-8")
    assert ControlPlane().run(plan_path=str(path)) == 2
    assert "not valid JSON" in capsys.readouterr().err


def test_run_rejects_a_missing_plan_file(tmp_path, capsys):
    assert ControlPlane().run(plan_path=str(tmp_path / "absent.json")) == 2
    assert "Cannot read plan file" in capsys.readouterr().err


def test_run_rejects_a_foreign_schema(tmp_path, capsys):
    payload = dict(_plan().to_dict())
    payload["schema"] = "something-else/v1"
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert ControlPlane().run(plan_path=str(path)) == 2
    assert "unsupported execution plan schema" in capsys.readouterr().err


def test_run_rejects_an_internally_invalid_plan(tmp_path, capsys):
    """A plan with a duplicate task id must not be executed — it would make the
    record set ambiguous and mask a double execution."""
    plan = _plan()
    payload = plan.to_dict()
    payload["tasks"] = [plan.tasks[0].to_dict(), plan.tasks[0].to_dict()]
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert ControlPlane().run(plan_path=str(path)) == 2
    assert "failed validation" in capsys.readouterr().err


def test_run_rejects_a_non_object_payload(tmp_path, capsys):
    path = tmp_path / "plan.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    assert ControlPlane().run(plan_path=str(path)) == 2
    assert "must contain a JSON object" in capsys.readouterr().err


def _ok_record(spec, plan, state):
    from datetime import UTC, datetime

    from runtime.foundation.verification.execution_orchestrator import (
        TaskExecutionRecord,
    )

    now = datetime.now(UTC).isoformat()
    return TaskExecutionRecord(
        record_id=f"rec-{spec.task_id}",
        plan_id=plan.plan_id,
        task_id=spec.task_id,
        primary_capability=spec.primary_capability,
        capabilities=list(spec.capabilities),
        command=spec.command,
        scope=spec.scope,
        is_mandatory=spec.is_mandatory,
        is_escalation=spec.is_escalation,
        verification_kind=spec.verification_kind,
        started_at=now,
        completed_at=now,
        duration_seconds=0.0,
        exit_code=0,
        completion_state=state.value if hasattr(state, "value") else str(state),
        stdout_path="",
        stderr_path="",
        artifacts=[],
        measurement_truth=None,
        diagnostic=None,
        next_action="",
        reason="stub",
        prerequisites_satisfied=True,
        termination=None,
    )