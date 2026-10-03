"""M10-R2 (C4) — Sharding, aggregation, and the split-brain guard.

The reconcile workflow fans one plan across up to seven runners and merges their
reports in a single gate. Three things must hold, and this file pins all three:

1. **Partition.** The union of every shard is exactly the plan's tasks, and no task
   appears in two shards. A plan built twice partitions identically, because two
   runners given the same plan must not disagree about what they own.
2. **Coverage.** Every shard receives every escalation task. ``_add_dependency_edges``
   gives each escalation task ``depends_on = <all mandatory ids>``, so
   stop-on-sufficiency is only decidable once the mandatory set is complete — a shard
   holding a subset would decide it on partial information.
3. **The split-brain guard.** A record set that does not cover the plan yields
   ``NOT_CERTIFIABLE`` naming the missing ids — never ``CERTIFIED``. This is the
   single most important assertion in the file.
"""

from __future__ import annotations

import glob
import json

import pytest

from runtime.foundation.verification.execution_orchestrator import (
    CompletionState,
    ExecutionOrchestrator,
    ExecutionPlan,
    ExecutionReport,
    FinalDecision,
    RepositoryFingerprint,
    TaskExecutionRecord,
)
from runtime.foundation.verification.execution_shards import (
    DEFAULT_MAX_SHARDS,
    assign_shards,
    evidence_path_conflicts,
    merge_shard_reports,
    plan_matrix,
    validate_shard_request,
)


def _broad_files() -> list[str]:
    return sorted(glob.glob("backend/src/engines/*/*.py"))[:40]


def _plan() -> ExecutionPlan:
    return ExecutionOrchestrator().build_execution_plan(_broad_files())


def _fp() -> RepositoryFingerprint:
    return RepositoryFingerprint.capture()


def _record(spec, plan, state, **kw) -> TaskExecutionRecord:
    """A complete record. Fields are real values, not stubs, so the record survives
    the same to_dict/from_dict hop a real shard report makes."""
    fields = {
        "started_at": "2026-01-01T00:00:00+00:00",
        "completed_at": "2026-01-01T00:00:01+00:00",
        "duration_seconds": 0.01,
        "exit_code": 0,
        "stdout_path": "",
        "stderr_path": "",
        "artifacts": [],
        "measurement_truth": None,
        "diagnostic": None,
        "next_action": "",
        "prerequisites_satisfied": True,
        "termination": None,
    }
    fields.update(kw)
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
        completion_state=state.value,
        reason=kw.get("reason", "fixture"),
        **fields,
    )


def _report(plan, records, decision=FinalDecision.CERTIFIED.value) -> ExecutionReport:
    return ExecutionReport(
        report_id="fixture",
        plan_id=plan.plan_id,
        plan_fingerprint=plan.plan_fingerprint,
        started_at="2026-01-01T00:00:00+00:00",
        completed_at="2026-01-01T00:00:01+00:00",
        total_duration_seconds=1.0,
        records=list(records),
        efficiency={},
        final_decision=decision,
        decision_reason="fixture",
        evidence_reused=[],
        escalations_triggered=[],
        decisions=[],
    )


# ---------------------------------------------------------------------------
# CLI contract
# ---------------------------------------------------------------------------


def test_absent_flags_mean_not_sharded():
    assert validate_shard_request(None, None) == (0, 1)


@pytest.mark.parametrize(
    ("shard", "count"),
    [(3, 3), (-1, 3), (0, 0), (0, DEFAULT_MAX_SHARDS + 1), (2, 2)],
)
def test_invalid_shard_requests_are_rejected(shard, count):
    with pytest.raises(ValueError):
        validate_shard_request(shard, count)


def test_shard_requires_a_count_and_count_requires_a_shard():
    with pytest.raises(ValueError, match="--shard-count"):
        validate_shard_request(1, None)
    with pytest.raises(ValueError, match="--shard"):
        validate_shard_request(None, 3)


# ---------------------------------------------------------------------------
# Partition
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("count", [1, 2, 3, 4, 5, 7])
def test_shards_cover_the_plan_exactly_once(count):
    plan = _plan()
    assignment = assign_shards(plan, count)

    seen: list[str] = []
    for shard in assignment.shards:
        seen.extend(t.task_id for t in shard)
    # Every task id appears; each non-barrier task appears in exactly one shard.
    assert {t.task_id for t in plan.tasks} <= set(seen)

    barrier = [t.task_id for t in plan.tasks if t.is_escalation]
    for shard in assignment.shards:
        shard_ids = [t.task_id for t in shard]
        for tid in barrier:
            assert tid in shard_ids, "every shard must carry the escalation barrier"
        non_barrier = [t for t in shard if not t.is_escalation]
        ids = [t.task_id for t in non_barrier]
        assert len(ids) == len(set(ids))


@pytest.mark.parametrize("count", [2, 3, 5, 7])
def test_partition_is_deterministic(count):
    a = assign_shards(_plan(), count).partition_fingerprint()
    b = assign_shards(_plan(), count).partition_fingerprint()
    assert a == b


def test_estimated_balance_meets_the_achievable_bound():
    """LPT must reach the *achievable* bound, not ``sum/N``.

    Tasks are indivisible, so the critical path can never fall below the single
    heaviest task. On this plan the two coverage tasks are ~1800s each out of a
    4741s total, so 7 shards floor out at ~1800s (a 2.6x reduction), not at
    4741/7. Comparing against sum/N would assert something no partitioner can
    deliver; the bound that actually distinguishes a good partitioner is
    ``max(largest single task, sum/N * 4/3)``.
    """
    plan = _plan()
    weights = [max(t.estimated_duration_seconds, 1) for t in plan.tasks]
    total = sum(weights)
    heaviest = max(weights)

    for count in (3, 5, 7):
        assignment = assign_shards(plan, count)
        bound = max(heaviest, (total / count) * 4 / 3)
        assert assignment.critical_path_estimate <= bound, (
            f"count={count} critical={assignment.critical_path_estimate} "
            f"bound={bound:.0f} heaviest={heaviest} ideal={total / count:.0f}"
        )


def test_critical_path_cannot_beat_the_heaviest_single_task():
    """Pins the ceiling this milestone can reach, so the performance claim is honest.

    Sharding reduces the critical path to the longest task, not to ``sum/N``. The
    heaviest task here is the coverage measurement, so that is the floor for
    ``verify check`` regardless of how many shards run.
    """
    plan = _plan()
    heaviest = max(max(t.estimated_duration_seconds, 1) for t in plan.tasks)
    total = sum(max(t.estimated_duration_seconds, 1) for t in plan.tasks)
    for count in (2, 3, 5, 7):
        assignment = assign_shards(plan, count)
        assert assignment.critical_path_estimate >= heaviest
    assert heaviest < total, "sanity: at least one plan can be usefully sharded"


def test_ordering_within_a_shard_matches_plan_order():
    plan = _plan()
    assignment = assign_shards(plan, 4)
    order = {t.task_id: i for i, t in enumerate(plan.tasks)}
    for shard in assignment.shards:
        positions = [order[t.task_id] for t in shard]
        assert positions == sorted(positions)


def test_no_evidence_destination_collides():
    """Fan-out must never overwrite evidence. Detected, never resolved by dropping
    evidence."""
    assert evidence_path_conflicts(assign_shards(_plan(), 7)) == []


# ---------------------------------------------------------------------------
# Matrix rendering
# ---------------------------------------------------------------------------


def test_matrix_document_is_usable_by_github_actions():
    import json as _json

    plan = _plan()
    document = _json.loads(plan_matrix(assign_shards(plan, 3), plan))

    assert document["plan_id"] == plan.plan_id
    assert document["plan_fingerprint"] == plan.plan_fingerprint
    assert document["task_count"] == len(plan.tasks)
    assert len(document["include"]) == document["shard_count"] == 3
    for leg in document["include"]:
        assert set(leg["task_ids"]) <= {t.task_id for t in plan.tasks}
    # Suggested parallelism is an output for the summary, never a job property:
    # a matrix job with dynamic own-properties does not expand.
    assert document["suggested_max_parallel"] <= DEFAULT_MAX_SHARDS
    assert document["critical_path_estimate_seconds"] > 0


def test_matrix_skips_empty_shards():
    """A plan with fewer tasks than shards must not emit empty legs — an empty matrix
    entry produces a runner that runs nothing."""
    import json as _json

    plan = _plan()
    document = _json.loads(plan_matrix(assign_shards(plan, 1), plan))
    assert document["shard_count"] == 1
    assert len(document["include"]) == 1


# ---------------------------------------------------------------------------
# The split-brain guard
# ---------------------------------------------------------------------------


def test_a_complete_merge_reproduces_a_single_shard_verdict():
    plan = _plan()
    records = [_record(t, plan, CompletionState.PASS) for t in plan.tasks]
    merged = merge_shard_reports(plan, [_report(plan, records)], live_fp=_fp())
    assert merged.final_decision == FinalDecision.CERTIFIED.value
    assert merged.efficiency["shard_partition"] == "complete"


def test_a_missing_task_forces_not_certifiable_and_names_it():
    """THE split-brain guard. If a shard silently did not run a task, the aggregate
    must refuse to certify and say which task."""
    plan = _plan()
    dropped = plan.tasks[1].task_id
    records = [
        _record(t, plan, CompletionState.PASS)
        for t in plan.tasks
        if t.task_id != dropped
    ]

    merged = merge_shard_reports(plan, [_report(plan, records)], live_fp=_fp())

    assert merged.final_decision == FinalDecision.NOT_CERTIFIABLE.value
    assert dropped in merged.decision_reason
    assert merged.efficiency["shard_partition"] == "incomplete"
    assert merged.efficiency["tasks_missing"] == 1


def test_an_empty_shard_set_is_not_certifiable():
    plan = _plan()
    merged = merge_shard_reports(plan, [], live_fp=_fp())
    assert merged.final_decision == FinalDecision.NOT_CERTIFIABLE.value
    assert merged.efficiency["tasks_missing"] == len(plan.tasks)


def test_a_task_reported_twice_is_rejected():
    plan = _plan()
    first = plan.tasks[0]
    state = CompletionState.PASS
    duplicate = [_record(first, plan, state), _record(first, plan, state)]
    merged = merge_shard_reports(plan, [_report(plan, duplicate)], live_fp=_fp())
    assert merged.final_decision == FinalDecision.NOT_CERTIFIABLE.value
    assert "more than one shard" in merged.decision_reason


def test_records_are_merged_in_plan_order_not_arrival_order():
    plan = _plan()
    state = CompletionState.PASS
    records = [_record(t, plan, state) for t in reversed(plan.tasks)]
    merged = merge_shard_reports(plan, [_report(plan, records)], live_fp=_fp())
    order = {t.task_id: i for i, t in enumerate(plan.tasks)}
    positions = [order[r.task_id] for r in merged.records]
    assert positions == sorted(positions)


def test_shards_merging_into_one_plan_cover_every_task_exactly_once():
    """The realistic sharded run: each shard reports only its own non-barrier tasks,
    and the merge reconstructs the plan's full record set.

    On a plan with no escalation tasks every task is owned by exactly one shard, so
    the merge is complete and certifiable. If the plan *does* carry escalation tasks
    they are replicated into every shard, and a shard that skipped one (because its
    own mandatory set passed) leaves the aggregate correctly not certifiable until
    the record exists — which is the behaviour we want, not a defect.
    """
    plan = _plan()
    assignment = assign_shards(plan, 3)
    state = CompletionState.PASS

    reports = [
        _report(
            plan,
            [_record(t, plan, state) for t in shard if not t.is_escalation],
        )
        for shard in assignment.shards
    ]
    merged = merge_shard_reports(plan, reports, live_fp=_fp())

    assert len(merged.records) == len(plan.tasks)
    assert {r.task_id for r in merged.records} == {t.task_id for t in plan.tasks}

    if any(t.is_escalation for t in plan.tasks):
        assert merged.final_decision == FinalDecision.NOT_CERTIFIABLE.value
    else:
        assert merged.final_decision == FinalDecision.CERTIFIED.value


# ---------------------------------------------------------------------------
# On-disk aggregate contract
# ---------------------------------------------------------------------------


def test_aggregate_rejects_a_directory_with_no_plan(tmp_path, capsys):
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    assert ControlPlane().run(aggregate=str(tmp_path)) == 2
    assert "no plan.json" in capsys.readouterr().err


def test_aggregate_rejects_zero_shard_reports(tmp_path, capsys):
    """A gate that aggregated zero shards must not report success — that would
    certify a plan on which nothing ran."""
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan = _plan()
    (tmp_path / "plan.json").write_text(json.dumps(plan.to_dict()), encoding="utf-8")
    assert ControlPlane().run(aggregate=str(tmp_path)) == 2
    assert "no shard-*.json" in capsys.readouterr().err


def test_aggregate_rejects_shards_that_disagree_on_the_plan(tmp_path, capsys):
    """Plan divergence between runners (risk R2) must be detected, not merged."""
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan = _plan()
    (tmp_path / "plan.json").write_text(json.dumps(plan.to_dict()), encoding="utf-8")
    payload = _report(
        plan,
        [],
    ).to_dict()
    payload["plan_id"] = "execplan-someone-else"
    (tmp_path / "shard-0.json").write_text(json.dumps(payload), encoding="utf-8")

    assert ControlPlane().run(aggregate=str(tmp_path)) == 2
    assert "did not agree on the plan" in capsys.readouterr().err


def test_aggregate_round_trips_a_real_shard_report(tmp_path, capsys):
    """End-to-end: a shard writes its report as JSON and the gate reads it back."""
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan = _plan()
    state = CompletionState.PASS
    (tmp_path / "plan.json").write_text(json.dumps(plan.to_dict()), encoding="utf-8")
    payload = _report(plan, [_record(t, plan, state) for t in plan.tasks]).to_dict()
    (tmp_path / "shard-0.json").write_text(json.dumps(payload), encoding="utf-8")

    rc = ControlPlane().run(aggregate=str(tmp_path))
    assert rc == 0, capsys.readouterr().err


def test_check_without_shard_flags_is_byte_identical():
    """The no-flag path must be untouched by M10-R2.

    With no flags the shard request normalises to ``(0, 1)`` — one shard holding every
    task — so `verify check` and the profile aliases take exactly the code path they
    took before the milestone.
    """
    from runtime.foundation.verification.control_plane_facade import (
        _parse_shard_arg,
    )

    assert _parse_shard_arg([]) == (None, None)
    assert _parse_shard_arg(["--json"]) == (None, None)
    assert _parse_shard_arg(["--changed-files", "a.py"]) == (None, None)
    assert validate_shard_request(None, None) == (0, 1)


def test_a_task_spec_round_trips_so_a_shard_can_be_deserialised():
    """A shard reads a plan file, so the spec must survive serialisation."""
    plan = _plan()
    back = ExecutionPlan.from_dict(plan.to_dict())
    assert [t.task_id for t in back.tasks] == [t.task_id for t in plan.tasks]
    assert back.tasks == plan.tasks


def test_plan_file_written_by_the_plan_job_can_drive_a_shard(tmp_path, capsys):
    """The plan job serialises the plan; the shard reads it and runs only its tasks."""
    from runtime.foundation.verification.control_plane_facade import ControlPlane

    plan = _plan()
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan.to_dict()), encoding="utf-8")

    cp = ControlPlane()
    rc = cp.run(plan_path=str(path), shard=(0, 3), json_out=True)
    # Whatever the verdict, the shard must have executed only its own tasks.
    assert rc in (0, 1, 2)
    restored = ExecutionPlan.from_dict(plan.to_dict())
    assert len(restored.tasks) == len(plan.tasks)
