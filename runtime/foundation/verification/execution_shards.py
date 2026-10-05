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
from collections.abc import Sequence
from typing import Any

from runtime.foundation.verification.execution_orchestrator import (
    NON_PASS_STATES,
    PASSING_STATES,
    CompletionState,
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


def shard_wall_seconds(
    tasks: Sequence[ExecutionTaskSpec], cpu_budget: int | None = None
) -> int:
    """Wall-clock estimate for one shard, under the CPU budget it will really run with.

    M10-R3 (D). The matrix previously emitted ``sum(estimated_duration)`` as
    ``estimated_seconds``. That number describes a *serial* machine, so it was wrong in
    both directions at once: it ignored the concurrency the executor applies, and it
    ignored that some tasks fork their own worker pools (``-n auto`` in
    ``run_contract_tests.sh`` and ``run_fast_checks.sh``).

    For shard 6 of the reproduced plan it reported 1741 s — the serial sum — while the
    shard's real critical path was the max over its concurrent waves. A reader sizing a
    CI job from that figure, or an operator reasoning about why a shard timed out, was
    reasoning about a schedule that never ran.

    Now it is the critical path: sum over budget-admitted waves of the slowest task in
    each wave. ``estimated_seconds_serial`` is retained alongside it so the two can be
    compared rather than one silently replacing the other.
    """
    from runtime.foundation.verification.parallel_executor import (
        CpuBudget,
        estimate_wall_seconds,
    )

    budget = CpuBudget(cpu_budget)
    return int(round(estimate_wall_seconds(list(tasks), budget)))


def shard_cpu_peak(
    tasks: Sequence[ExecutionTaskSpec], cpu_budget: int | None = None
) -> int:
    """Peak simultaneous CPU demand this shard will reach, and its budget.

    Reported so a workflow sizing ``timeout-minutes`` can see the demand it is
    scheduling against instead of inferring it from a worker count.
    """
    from runtime.foundation.verification.parallel_executor import (
        CpuBudget,
        cpu_demand_for,
        schedule_within_budget,
    )

    budget = CpuBudget(cpu_budget)
    waves = schedule_within_budget(list(tasks), budget)
    return max(
        (sum(cpu_demand_for(t) for t in wave) for wave in waves),
        default=0,
    )


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


def shard_intended_termination_seconds(
    tasks: Sequence[ExecutionTaskSpec], cpu_budget: int | None = None
) -> int:
    """The longest this shard may legitimately run under the real schedule.

    M10-R3 (L1c). This is the shard's **contractual** wall clock, and it is the number
    the infrastructure backstop must exceed.

    It is the sum over CPU-budget-admitted waves of the slowest task's own
    ``timeout_seconds`` in that wave — not the maximum across the shard, because the CPU
    budget serialises the heavy tasks. A shard holding one 3600 s task and one 180 s task
    needs 3780 s of backstop on a 1-core budget, not 3600 s.

    Deriving this from the task budgets rather than from estimates is the point: the
    estimate is advisory, the budget is the obligation, and only the obligation may size
    an infrastructure timeout.
    """
    from runtime.foundation.verification.parallel_executor import (
        CpuBudget,
        schedule_within_budget,
    )

    budget = CpuBudget(cpu_budget)
    waves = schedule_within_budget(list(tasks), budget)
    return sum(
        max((int(t.timeout_seconds or 0) for t in wave), default=0) for wave in waves
    )


#: Headroom added on top of the contractual wall clock, in seconds.
#:
#: Covers process teardown, evidence flush and the aggregation tail. Not slack for a slow
#: task: a task that exceeds its own ``timeout_seconds`` is a defect and should be
#: reported as one, not absorbed by a bigger job timeout.
INFRA_BACKSTOP_MARGIN_SECONDS = 300


def required_backstop_minutes(
    tasks: Sequence[ExecutionTaskSpec], cpu_budget: int | None = None
) -> int:
    """The infrastructure backstop a shard leg must be given, in whole minutes.

    Published in the matrix so the workflow sizes its own ``timeout`` from the runtime's
    contract rather than a hand-maintained literal. Previously the reconcile workflow
    repeated the literal ``85m`` in **three** places (the GNU ``timeout`` call, a jq
    diagnostic, and an error message), so they could drift independently — and did once:
    the bare-number ``timeout 85`` bug capped every shard at 85 *seconds*.
    """
    contractual = shard_intended_termination_seconds(tasks, cpu_budget)
    total = contractual + INFRA_BACKSTOP_MARGIN_SECONDS
    return max(1, -(-total // 60))  # ceil, so a short shard still gets a whole minute


def validate_infra_backstop(
    tasks: Sequence[ExecutionTaskSpec],
    backstop_seconds: int,
    cpu_budget: int | None = None,
) -> str | None:
    """Reject a backstop that expires before the runtime's own termination path.

    M10-R3 (L1c). The mission requires this state be *mechanically rejected* rather than
    documented against. Without it, a workflow can pass a backstop shorter than the
    obligations it contains and the runner kills a leg that was still legitimately
    working — which is exactly the failure this milestone was chartered to end, and
    exactly what the ``timeout 85`` bug did.
    """
    intended = shard_intended_termination_seconds(tasks, cpu_budget)
    if backstop_seconds <= intended:
        return (
            f"infrastructure backstop {backstop_seconds}s expires at or before this "
            f"shard's contractual wall clock of {intended}s "
            f"(sum over CPU-budget waves of the slowest task budget). "
            f"Raise it to at least {required_backstop_minutes(tasks, cpu_budget)} minutes."
        )
    return None


def leg_environment(
    *,
    leg: str,
    plan_id: str = "",
    shard: int | None = None,
    repo_root: Path | None = None,
) -> dict[str, str]:
    """The per-leg environment the runtime requires, derived from its own provenance.

    M10-R3 (L1c). Both fan-out workflows declared this by hand:

        FINANCE_DB_PATH: .../backend/data/e2e-playwright-${{ matrix.shard }}.db
        PLAYWRIGHT_PROJECT: chromium
        CLARIFIN_PYTHON: .../.venv/bin/python

    with a *different* naming scheme in each file (``e2e-playwright-N`` vs ``e2e-`` +
    leg id). That is per-leg mutable state living in YAML, which is the mission's
    "the workflow must not know: environment variables" — and it is exactly the value
    that determines correctness, since two legs sharing a database is the cross-shard
    mutation the Playwright script documents as the cause of drifting screenshots.

    The runtime already knows all of it: ``REPO_ROOT`` is where it runs, and ``leg`` /
    ``shard`` identify the unit. So the declaration is derived rather than copied.

    Semantics for callers: these are **defaults**. A value already present in the
    environment is left alone, so an operator can still override deliberately. What is
    removed is the *obligation* to know any of it in YAML.

    The database name includes ``leg`` and ``plan_id`` so isolation survives a workflow
    restructure: two legs cannot collide because they cannot produce the same name unless
    they are the same leg.
    """
    from pathlib import Path as _Path

    root = (
        _Path(repo_root)
        if repo_root is not None
        else _Path(__file__).resolve().parents[3]
    )
    identity = leg or (f"shard-{shard}" if shard is not None else "local")
    token = f"{identity}-{plan_id}" if plan_id else identity
    return {
        # Per-leg isolated database: the single most correctness-relevant variable here.
        "FINANCE_DB_PATH": str(root / "backend" / "data" / f"e2e-{token}.db"),
        # The canonical interpreter. `AGENTS.md` makes the repository-root .venv the
        # single sanctioned environment; a workflow reproducing that path by hand was a
        # second place for it to drift.
        "CLARIFIN_PYTHON": str(root / ".venv" / "bin" / "python"),
    }


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
            # M10-R3 (D): the critical path under the real CPU budget, with the
            # serial sum retained for comparison. The old single figure was the
            # serial sum, which describes a schedule that never runs.
            "estimated_seconds": shard_wall_seconds(
                [t for t in assignment.shards[i] if not t.is_escalation]
            ),
            "estimated_seconds_serial": sum(
                _weight(t) for t in assignment.shards[i] if not t.is_escalation
            ),
            "cpu_peak": shard_cpu_peak(
                [t for t in assignment.shards[i] if not t.is_escalation]
            ),
            # L1c: the backstop this leg must be given. Reaches CI automatically now
            # that the workflow's matrix projection selects shape, not payload — the
            # two changes are complementary and neither works without the other.
            "required_timeout_minutes": required_backstop_minutes(
                [t for t in assignment.shards[i] if not t.is_escalation]
            ),
            "contractual_seconds": shard_intended_termination_seconds(
                [t for t in assignment.shards[i] if not t.is_escalation]
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


def _skipped_escalation_record(
    task: ExecutionTaskSpec, plan: ExecutionPlan
) -> TaskExecutionRecord:
    """The record an escalation task earns when sufficiency is met and it is skipped.

    Field-for-field what ``ExecutionOrchestrator.execute`` emits for the same
    condition, so a sharded run and a single-run plan produce the same record set and
    the same verdict. Written here rather than inline in the merge because it is a
    contract, not a convenience.
    """
    return TaskExecutionRecord(
        record_id=f"aggregate-escalation-{task.task_id}",
        plan_id=plan.plan_id,
        task_id=task.task_id,
        primary_capability=task.primary_capability,
        capabilities=list(task.capabilities),
        command=task.command,
        scope=task.scope,
        is_mandatory=task.is_mandatory,
        is_escalation=True,
        verification_kind=task.verification_kind,
        started_at="",
        completed_at="",
        duration_seconds=0.0,
        exit_code=0,
        completion_state=CompletionState.SKIPPED.value,
        stdout_path="",
        stderr_path="",
        artifacts=[],
        measurement_truth=None,
        diagnostic=None,
        next_action="",
        reason=(
            "stop-on-sufficiency: all mandatory tasks PASS or REUSED; escalation skipped"
        ),
        prerequisites_satisfied=True,
    )


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

    # M11-R4 — the escalation barrier the shards deliberately do not run.
    #
    # `run --shard` strips escalation tasks out of a shard's plan (see
    # control_plane_facade.run), because a shard holding a subset of the mandatory
    # tasks cannot decide stop-on-sufficiency on the global outcome. That decision
    # belongs here — but until now nothing actually made it, and the consequence was
    # a permanent deadlock:
    #
    #   * every shard omits them  ->  no SKIPPED record is ever produced;
    #   * this merge requires a record for every plan task  ->  `not_certifiable`
    #     with "missing 3 task(s)" on every single run.
    #
    # Reconciliation could therefore never certify any plan that contained an
    # escalation task, whatever the code under test did.
    #
    # So the aggregate owns the barrier, as the shard comment always assumed. It
    # decides exactly what `ExecutionOrchestrator.execute` decides, on exactly the
    # same evidence, and says so in the same words:
    #
    #   * sufficiency met (no mandatory task in a non-pass state) -> SKIPPED,
    #     "stop-on-sufficiency: all mandatory tasks PASS or REUSED; escalation skipped".
    #     This is the orchestrator's own outcome for that condition, so the merged
    #     record set is identical to a single-run plan's.
    #   * sufficiency NOT met -> the task is left missing. It genuinely did not run,
    #     and `not_certifiable` naming it is the truthful verdict. It is never
    #     auto-passed, auto-skipped or invented.
    non_pass = [
        r
        for r in records.values()
        if r.is_mandatory and r.completion_state not in PASSING_STATES
    ]
    if not non_pass:
        for task in plan.tasks:
            if task.is_escalation and task.task_id not in records:
                records[task.task_id] = _skipped_escalation_record(task, plan)
    missing = [t.task_id for t in plan.tasks if t.task_id not in records]

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
            "tasks_selected": len(plan.tasks),
            "tasks_total": len(plan.tasks),
            "tasks_executed": len(ordered),
            "tasks_reported": len(ordered),
            "tasks_passed": passed,
            "tasks_failed": failed,
            "tasks_missing": len(missing),
            "tasks_reused": sum(
                1 for r in ordered if str(r.completion_state).endswith("REUSED")
            ),
            "tasks_skipped": sum(
                1 for r in ordered if str(r.completion_state).endswith("SKIPPED")
            ),
            "tasks_authorization_required": sum(
                1
                for r in ordered
                if str(r.completion_state).endswith("AUTHORIZATION_REQUIRED")
            ),
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
