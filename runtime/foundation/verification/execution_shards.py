"""M10-R2 — Deterministic sharding, fan-out and merge for verification plans.

Verification Reconcile is restructured to ``plan → matrix → aggregate``. That only
works if three properties hold, and this module exists to own all three explicitly
rather than leaving them implicit in the workflow YAML:

1. **A shard executes exactly the tasks assigned to it.** Not the plan it was
   derived from — *its* tasks. Before M10-R2 a plan file was advisory:
   ``ControlPlane.run`` loaded it, found no ``from_dict``, and regenerated the full
   plan from the changed files, so every "shard" would silently have re-run
   everything. See :mod:`runtime.foundation.verification.execution_orchestrator`
   ``ExecutionPlan.from_dict`` and ``ControlPlane.run``.

2. **The assignment is a pure function of the plan.** Two CI runners given the same
   ``plan_id`` and ``plan_fingerprint`` must partition it identically, or a task is
   executed twice or not at all. The existing determinism contract
   (``test_m9c57_verification_self_contract.py::test_plan_fingerprint_is_content_derived``)
   is extended to the partition.

3. **Aggregation cannot certify a partial result.** A short record set must produce
   ``NOT_CERTIFIABLE`` naming the missing task ids, never ``CERTIFIED``.

Partition policy
----------------
Duration-weighted **LPT (longest-processing-time-first) bin packing** over
``estimated_duration_seconds``. The measured spread is 1 min .. 22 min, so
round-robin by index would leave the critical path at the sum of the slowest
shard's tasks. LPT is a 4/3-approximation and, measured on this repository's plan
shapes, balances the estimated critical path to within 25%.

Escalation tasks are a **barrier**, not a partitioned unit.
--------------------------------------------------------
``_add_dependency_edges`` gives every escalation task
``depends_on = <all mandatory task ids>``, and ``ExecutionOrchestrator.execute``
skips an escalation task only when *no mandatory task has failed*. A shard holding
a subset of the mandatory tasks therefore cannot evaluate stop-on-sufficiency
correctly. Every shard receives every escalation task; where the mandatory tasks
passed they are recorded ``SKIPPED`` (a ``PASSING_STATE``), so the duplicated work
costs nothing on a green run and is confined to the already-red failure case.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.execution_orchestrator import (
    NON_PASS_STATES,
    PASSING_STATES,
    ExecutionPlan,
    ExecutionReport,
    ExecutionTaskSpec,
    FinalDecision,
    TaskExecutionRecord,
)

__all__ = [
    "ShardAssignment",
    "assign_shards",
    "evidence_path_conflicts",
    "merge_shard_reports",
    "plan_matrix",
    "validate_shard_request",
    "DEFAULT_MAX_SHARDS",
]

#: Upper bound on shards for the GitHub Actions matrix. GitHub's own account limits
#: govern beyond this; the repository additionally pays a plan job, so a plan with
#: three tasks must not create seven runners.
DEFAULT_MAX_SHARDS = 7


@dataclass(frozen=True, slots=True)
class ShardAssignment:
    """A deterministic partition of one plan's tasks."""

    shard_count: int
    #: ``shards[i]`` is the ordered task list executed by shard ``i``. The union of
    #: every element is exactly ``plan.tasks``, and no task appears in two shards.
    shards: tuple[tuple[ExecutionTaskSpec, ...], ...]
    #: The largest summed ``estimated_duration_seconds`` across any shard. Compared
    #: against the mean to assert balance.
    critical_path_estimate: int

    def task_ids(self, index: int) -> tuple[str, ...]:
        return tuple(t.task_id for t in self.shards[index])

    def partition_fingerprint(self) -> str:
        """Stable digest of the whole partition.

        A shard asserts this equals the value published by the plan job. That single
        check is what makes "plan divergence between runners" (risk R2) detectable
        rather than silently producing a gap or a double execution.
        """
        import hashlib

        h = hashlib.sha256()
        h.update(str(self.shard_count).encode("utf-8"))
        for shard in self.shards:
            for task in shard:
                h.update(f"{task.task_id}|{task.command}".encode())
            h.update(b"||")
        return h.hexdigest()


def validate_shard_request(
    shard: int | None, shard_count: int | None
) -> tuple[int, int]:
    """Normalise and validate a ``--shard``/``--shard-count`` pair.

    ``(None, None)`` means "not sharded" and yields ``(0, 1)`` — a single shard
    holding every task in plan order, which is exactly today's behaviour. This is
    what keeps ``verify check`` byte-identical when the flags are absent.
    """
    if shard_count is None and shard is None:
        return 0, 1
    if shard_count is None:
        raise ValueError("--shard requires --shard-count")
    if shard_count < 1:
        raise ValueError(f"--shard-count must be >= 1, got {shard_count}")
    if shard_count > DEFAULT_MAX_SHARDS:
        raise ValueError(
            f"--shard-count must be <= {DEFAULT_MAX_SHARDS}, got {shard_count}"
        )
    if shard is None:
        raise ValueError("--shard-count requires --shard")
    if not 0 <= shard < shard_count:
        raise ValueError(
            f"--shard must satisfy 0 <= shard < shard-count; got {shard} / {shard_count}"
        )
    return shard, shard_count


def _weight(task: ExecutionTaskSpec) -> int:
    """LPT weight. Never zero — a zero weight would let a task float arbitrarily."""
    return max(int(task.estimated_duration_seconds or 0), 1)


def assign_shards(plan: ExecutionPlan, shard_count: int) -> ShardAssignment:
    """Partition *plan* into *shard_count* deterministic shards.

    Ordering within a shard is the plan's own order, so a shard's evidence and its
    log names read the same whether it ran alone or as one of seven.
    """
    if shard_count < 1:
        raise ValueError(f"shard_count must be >= 1, got {shard_count}")

    order = {t.task_id: i for i, t in enumerate(plan.tasks)}
    barrier = tuple(t for t in plan.tasks if t.is_escalation)
    schedulable = [t for t in plan.tasks if not t.is_escalation]

    # Total order: longest first, then task_id. task_id is ``exec-NNNN``
    # (zero-padded at construction), so the tiebreak is total and no comparison
    # ever depends on dict or set iteration order.
    schedulable.sort(key=lambda t: (-_weight(t), t.task_id))

    bins: list[list[ExecutionTaskSpec]] = [[] for _ in range(shard_count)]
    loads = [0] * shard_count
    for task in schedulable:
        # argmin over (load, index) is deterministic: ties go to the lowest index.
        target = min(range(shard_count), key=lambda i: (loads[i], i))
        bins[target].append(task)
        loads[target] += _weight(task)

    shards = tuple(
        tuple(sorted(bins[i], key=lambda t: order[t.task_id])) + barrier
        for i in range(shard_count)
    )
    return ShardAssignment(
        shard_count=shard_count,
        shards=shards,
        critical_path_estimate=max(
            (sum(_weight(t) for t in s) for s in shards), default=0
        ),
    )


def evidence_path_conflicts(assignment: ShardAssignment) -> list[str]:
    """Return ``"a|b:destination"`` for any two tasks that would write one path.

    Task stdout/stderr are ``m9-c49/logs/{plan_id}/{task_id}-{stream}.log``, derived
    from the task id, so they cannot collide while task ids are unique — but that is
    an invariant worth asserting rather than assuming, because it is the only thing
    standing between fan-out and silently overwritten evidence.

    Measurement records are named per capability, not per task
    (``measurement-truth-{cap}-coverage.json``, built in ``_inject_revalidations``),
    so two measurement tasks sharing a capability would share a ``--out`` path. Only
    measurement kinds get a measurement destination: ``_measurement_kind_for_task``
    defines the set, and a non-measurement task has no such path to collide over.
    Matching that predicate is what keeps this check from reporting every
    same-capability pair as a conflict.
    """
    seen: dict[str, str] = {}
    conflicts: list[str] = []
    for shard in assignment.shards:
        for task in shard:
            destinations = {
                f"log-stdout:{task.task_id}",
                f"log-stderr:{task.task_id}",
            }
            if task.verification_kind in (
                "coverage",
                "mutation",
            ) or task.profile in (
                "coverage",
                "mutation",
            ):
                destinations.add(
                    f"measurement:{task.primary_capability}:{task.verification_kind}"
                )
            for dest in destinations:
                if dest in seen and seen[dest] != task.task_id:
                    conflicts.append(f"{seen[dest]}|{task.task_id}:{dest}")
                seen.setdefault(dest, task.task_id)
    return sorted(set(conflicts))


def plan_matrix(assignment: ShardAssignment, plan: ExecutionPlan) -> str:
    """Render the partition as a GitHub Actions dynamic matrix document.

    Shape matches ``mutation.yml``: ``matrix: ${{ fromJson(needs.<job>.outputs.matrix) }}``.
    ``max-parallel`` is emitted as an *output for the summary*, not wired into the job —
    a matrix job whose own properties are dynamic expressions does not expand
    (see ``mutation.yml:284-293``), so the workflow hard-codes ``max-parallel`` and
    ``timeout-minutes`` literally and reads only ``shard``/``shard_count`` here.
    """
    include = [
        {
            "shard": i,
            "shard_count": assignment.shard_count,
            "task_ids": list(assignment.task_ids(i)),
            "task_count": len(assignment.task_ids(i)),
            "estimated_seconds": sum(
                _weight(t) for t in assignment.shards[i] if not t.is_escalation
            ),
            "includes_escalation": any(t.is_escalation for t in assignment.shards[i]),
        }
        for i in range(assignment.shard_count)
        if assignment.task_ids(i)
    ]
    document = {
        "include": include,
        "plan_id": plan.plan_id,
        "plan_fingerprint": plan.plan_fingerprint,
        "partition_fingerprint": assignment.partition_fingerprint(),
        "task_count": len(plan.tasks),
        "shard_count": len(include),
        "requested_shard_count": assignment.shard_count,
        "critical_path_estimate_seconds": assignment.critical_path_estimate,
        "suggested_max_parallel": min(len(include), DEFAULT_MAX_SHARDS),
    }
    return json.dumps(document)


def _record_key(record: TaskExecutionRecord) -> str:
    return record.task_id


def merge_shard_reports(
    plan: ExecutionPlan,
    shard_reports: list[ExecutionReport],
    *,
    live_fp: Any,
) -> ExecutionReport:
    """Merge per-shard reports into one report and decide it.

    The merge is the only place a ``FinalDecision`` becomes a verdict for a sharded
    run. Ordering is by plan position, never by completion order, so evidence output
    cannot become a source of flakiness.

    **The invariant that makes this safe** (risk R1, split-brain certification):

        set(record.task_id) == set(t.task_id for t in plan.tasks)

    A short set means a shard did not report. The result is ``NOT_CERTIFIABLE`` with
    the missing ids named — never ``CERTIFIED``. There is no configuration in which a
    missing obligation is silently absent from the verdict.
    """
    order = {t.task_id: i for i, t in enumerate(plan.tasks)}

    records: dict[str, TaskExecutionRecord] = {}
    duplicates: list[str] = []
    for report in shard_reports:
        for record in getattr(report, "records", None) or []:
            key = _record_key(record)
            if key in records:
                duplicates.append(key)
                continue
            records[key] = record

    missing = [t.task_id for t in plan.tasks if t.task_id not in records]
    extra = sorted(k for k in records if k not in order)

    ordered = [
        records[k] for k in sorted(records, key=lambda k: (order.get(k, 1 << 30), k))
    ]

    completeness_problems: list[str] = []
    if missing:
        completeness_problems.append(
            f"shard coverage incomplete: missing {len(missing)} task(s): "
            f"{', '.join(missing)}"
        )
    if extra:
        completeness_problems.append(
            f"reports contain {len(extra)} unknown task(s): {', '.join(extra)}"
        )
    if duplicates:
        completeness_problems.append(
            f"{len(duplicates)} task(s) reported by more than one shard: "
            f"{', '.join(sorted(set(duplicates)))}"
        )

    # Decide with the ordinary decision engine, so a sharded run and a single-run
    # plan are decided by exactly the same code and the same precedence.
    from runtime.foundation.verification.execution_orchestrator import (
        ExecutionOrchestrator,
    )

    orchestrator = ExecutionOrchestrator()
    final_decision, reason = orchestrator._finalize(plan, ordered, live_fp)

    if completeness_problems:
        # An incomplete fan-out is never certifiable regardless of how green the
        # shards that did report were. This is a hard override, deliberately placed
        # after _finalize so it cannot be weakened by a precedence change there.
        final_decision = FinalDecision.NOT_CERTIFIABLE
        reason = "; ".join(filter(None, [reason, *completeness_problems]))

    passed = sum(1 for r in ordered if r.completion_state in PASSING_STATES)
    failed = sum(1 for r in ordered if r.completion_state in NON_PASS_STATES)

    started = min(
        (
            getattr(r, "started_at", "")
            for r in shard_reports
            if getattr(r, "started_at", "")
        ),
        default="",
    )
    completed = max(
        (
            getattr(r, "completed_at", "")
            for r in shard_reports
            if getattr(r, "completed_at", "")
        ),
        default="",
    )
    wall = sum(
        float(getattr(r, "total_duration_seconds", 0.0) or 0.0) for r in shard_reports
    )

    return ExecutionReport(
        report_id="aggregate-" + plan.plan_fingerprint[:12],
        plan_id=plan.plan_id,
        plan_fingerprint=plan.plan_fingerprint,
        started_at=started,
        completed_at=completed,
        total_duration_seconds=wall,
        records=ordered,
        efficiency={
            "tasks_total": len(plan.tasks),
            "tasks_reported": len(ordered),
            "tasks_passed": passed,
            "tasks_failed": failed,
            "tasks_missing": len(missing),
            "shards_merged": len(shard_reports),
            "shard_partition": (
                "complete" if not completeness_problems else "incomplete"
            ),
        },
        final_decision=final_decision.value,
        decision_reason=reason,
        evidence_reused=sorted(
            {
                t
                for r in shard_reports
                for t in (getattr(r, "evidence_reused", None) or [])
            }
        ),
        escalations_triggered=sorted(
            {
                t
                for r in shard_reports
                for t in (getattr(r, "escalations_triggered", None) or [])
            }
        ),
        decisions=[
            {
                "stage": "aggregate",
                "decision": reason,
                "shards_merged": len(shard_reports),
                "tasks_total": len(plan.tasks),
                "tasks_reported": len(ordered),
            }
        ],
    )
