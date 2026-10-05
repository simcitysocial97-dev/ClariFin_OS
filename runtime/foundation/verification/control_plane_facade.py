"""
M9-C49 — Canonical Control Plane Facade.

This module is the SINGLE public command surface for the ClariFin_OS verification
runtime. Every operator/AI invocation maps to exactly one canonical operation
defined in cli_surface.CanonicalOperation.

The control plane owns:
  - ChangeDetector       (runtime.foundation.intelligence)
  - CapabilityResolver   (runtime.foundation.verification.capability_resolver)
  - EvidenceState        (runtime.foundation.verification.evidence_*)
  - ObligationEngine     (this module: obligation.py + planner integration)
  - TaskCompiler         (runtime.foundation.verification.executor_pipeline)
  - Executor             (runtime.foundation.verification.executor_pipeline + mutation_runner)
  - EvidenceCollector    (runtime.foundation.verification.executor_pipeline.evidence_capture)
  - VerdictEngine        (runtime.foundation.verification.certification)

The legacy surface (~97 tokens) is routed through this facade via
runtime.foundation.verification.canonical_control_plane.migration_map() and never
creates a second semantic authority.

Public API (exactly 9 top-level commands):

    verify check        — primary verification entrypoint
    verify plan         — plan-only mode (no execution)
    verify run          — execute an explicit plan
    verify diagnose     — failure/survivor diagnostic
    verify strengthen   — test-strengthening control plane
    verify inspect      — read-only inspection (capabilities/evidence/plan/...)
    verify certify      — certification (evidence-gated)
    verify ci           — CI orchestration/reconciliation
    verify doctor       — framework health/integrity

Internal implementation complexity is permitted; operator-facing complexity is not.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Canonical imports — these are the ONLY internal modules the facade consumes.
from runtime.foundation.intelligence import (
    analyze,
    format_diagnostic,
)
from runtime.foundation.verification.boundary_policy import (
    BoundaryEvidence,
    Strategy,
    build_evidence,
    classify_boundary_size,
    select_strategy,
)
from runtime.foundation.verification.canonical_control_plane import (
    CanonicalOperation,
    canonical_help,
    classification_for,
    migration_map,
)
from runtime.foundation.verification.certification import (
    main as certification_main,
)
from runtime.foundation.verification.control_plane import (
    ControlPlanePlan,
    ControlPlanePlanner,
)
from runtime.foundation.verification.evidence_planner import (
    default_planner,
)
from runtime.foundation.verification.execution_orchestrator import (
    CertificationRun,
    CompletionState,
    ExecutionOrchestrator,
    ExecutionPlan,
    ExecutionTaskSpec,
    FinalDecision,
)
from runtime.foundation.verification.execution_orchestrator import evidence_roots
from runtime.foundation.verification.execution_shards import (
    assign_shards,
    validate_infra_backstop,
)
from runtime.foundation.verification.parallel_executor import cpu_count
from runtime.foundation.verification.measurement_truth_integration import (
    get_measurement_truth_integrator,
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


def _collect_changed_files(*, fetch_remote: bool = True) -> list[str]:
    """Collect changed files via the canonical intelligence layer."""
    return _collect_changed_files_result(fetch_remote=fetch_remote).files


def _collect_changed_files_result(*, fetch_remote: bool = True) -> Any:
    """Return the full ``_ChangedFilesResult`` from the orchestrator layer, so
    callers can inspect the resolved boundary (source, base ref, file count).
    """
    from runtime.foundation.verification.orchestrator import (
        _collect_changed_files,
        _is_git_available,
    )

    if _is_git_available():
        return _collect_changed_files(fetch_remote=fetch_remote)
    from types import SimpleNamespace

    return SimpleNamespace(
        files=[],
        source="no-git",
        base=None,
        head=None,
        error="git unavailable",
    )


def _get_current_commit() -> str:
    from runtime.foundation.verification.orchestrator import (
        _get_current_commit,
    )

    return _get_current_commit()


def _is_git_available() -> bool:
    from runtime.foundation.verification.orchestrator import _is_git_available

    return _is_git_available()


def _summarise_capabilities(plan: ExecutionPlan) -> tuple[str, ...]:
    """Names of the capabilities a plan covers, with unmapped ones collapsed.

    Unmapped pseudo-capabilities are per-file ("unmapped:UNMAPPED:<path>"), so
    listing them individually turns the boundary evidence into a wall of paths —
    a 205-file boundary produced 30-odd of them and a single unreadable line.
    They are summarised as a count instead; the obligation itself still names
    every path.
    """

    real: set[str] = set()
    unmapped = 0
    for task in plan.tasks:
        for cap in task.capabilities or (task.primary_capability,):
            if not cap:
                continue
            if cap.startswith("unmapped:") and "UNMAPPED:" in cap:
                unmapped += 1
            else:
                real.add(cap)
    if unmapped:
        real.add(f"unmapped:{unmapped} change(s) awaiting review")
    return tuple(sorted(real))


class ControlPlane:
    """
    The canonical verification control plane.

    All operator/AI intent flows through exactly one of the nine public
    methods defined below. The control plane consumes internal services
    but exposes only intent — never implementation detail.
    """

    def __init__(self) -> None:
        self.planner = ControlPlanePlanner()
        self.orchestrator = ExecutionOrchestrator()
        self.integrator = get_measurement_truth_integrator()
        self._evidence_planner = default_planner()
        self._last_boundary_size = 0

    # ── CANONICAL PUBLIC OPERATIONS ────────────────────────────────────────

    def check(
        self,
        changed_files: list[str] | None = None,
        *,
        shard: tuple[int | None, int | None] = (None, None),
        json_out: bool = False,
    ) -> int:
        """
        Primary verification entrypoint.

        Given the current repository state, determine what is affected,
        plan the required verification, execute it, and produce evidence.

        M10-R2: *shard* is ``(shard, shard_count)``. ``(None, None)`` means not
        sharded, which is byte-identical to the pre-M10-R2 behaviour. When sharded,
        the full plan is still built and still validated — only the *execution* is
        narrowed to this shard's tasks, so the plan job and every shard agree on the
        plan fingerprint by construction.

        Returns 0 on certified, 1 on failed/blocked/interrupted.
        """
        import time

        from runtime.foundation.verification.execution_shards import (
            assign_shards,
            evidence_path_conflicts,
            plan_matrix,
            validate_shard_request,
        )

        cf_result = _collect_changed_files_result()
        changed_files = (
            cf_result.files if hasattr(cf_result, "files") else (changed_files or [])
        )
        source = getattr(cf_result, "source", "unknown")
        base_ref = getattr(cf_result, "base", None)

        # O-2 / G4 boundary transparency: print the resolved boundary BEFORE
        # planning so the operator knows what surface is being verified.
        print(f"[check] boundary={source}", end="", file=sys.stderr)
        if base_ref:
            print(f" base={base_ref[:8]}", end="", file=sys.stderr)
        print(f" files={len(changed_files)}", file=sys.stderr)

        if not changed_files and not _is_git_available():
            print(
                "No changed files detected and git unavailable.",
                file=sys.stderr,
            )
            return 1

        try:
            shard_index, shard_count = validate_shard_request(*shard)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2

        # 1. Repository state → Change detection
        # 2. Change detection → Capability graph → Affected capabilities
        control_plan: ControlPlanePlan = self.planner.plan(changed_files)

        # 3. Obligations (control plane's explicit obligation model)
        _obligations: ObligationSet = self._plan_to_obligations(
            control_plan, changed_files
        )

        # 4. Build executable execution plan using the canonical ExecutionOrchestrator
        execution_plan = self.orchestrator.build_execution_plan(changed_files)

        # 4b. Classify the boundary and select a strategy. An oversized boundary
        # does not get a warning followed by the same expanding plan; it gets a
        # deterministic bounded fallback. The decision is always recorded.
        boundary_class = classify_boundary_size(len(changed_files))
        strategy = select_strategy(boundary_class)
        self._last_boundary_size = len(changed_files)
        if strategy is Strategy.BOUNDED_FALLBACK:
            execution_plan.boundary_evidence = build_evidence(
                boundary_size=len(changed_files),
                strategy=strategy,
                incremental_task_count=len(execution_plan.tasks),
            )
            execution_plan = self._build_bounded_fallback_plan()
        print(
            (
                execution_plan.boundary_evidence.render()
                if execution_plan.boundary_evidence is not None
                else build_evidence(
                    boundary_size=len(changed_files),
                    strategy=strategy,
                    capabilities_covered=_summarise_capabilities(execution_plan),
                    incremental_task_count=len(execution_plan.tasks),
                ).render()
            ),
            file=sys.stderr,
        )

        # 5. Execute, with an on_record hook so partial-progress is observable
        #    even if the run is interrupted.
        if not execution_plan.tasks and not getattr(
            execution_plan, "mandatory_task_requirements", ()
        ):
            print("[check] NO_TASKS_FOR_CHANGE_SCOPE: certified no-op", file=sys.stderr)
            return 0

        # 4c. Shard narrowing (M10-R2). The plan above is always built whole, so the
        #     plan job and every shard derive an identical ``plan_fingerprint``.
        #     Only the task subset executed here differs. With ``shard_count == 1``
        #     this branch is inert and the run is byte-identical to pre-M10-R2.
        if shard_count > 1:
            from runtime.foundation.verification.execution_orchestrator import (
                ExecutionPlan,
            )

            assignment = assign_shards(execution_plan, shard_count)

            conflicts = evidence_path_conflicts(assignment)
            if conflicts:
                print(
                    "Refusing to fan out: concurrent tasks would share an evidence "
                    "destination: " + "; ".join(conflicts),
                    file=sys.stderr,
                )
                return 2

            matrix = plan_matrix(assignment, execution_plan)
            print(
                f"[check] plan={execution_plan.plan_id} "
                f"tasks={len(execution_plan.tasks)} "
                f"partition={assignment.partition_fingerprint()[:12]}",
                file=sys.stderr,
            )
            print(f"[check] MATRIX_JSON={matrix}", file=sys.stderr)

            kept = {t.task_id for t in assignment.shards[shard_index]}
            # Escalation tasks are EXCLUDED from shard execution, not merely
            # replicated. They are gated on the GLOBAL mandatory outcome
            # (`stop-on-sufficiency` runs them only when no mandatory task passed), and a
            # shard holding a subset of the mandatory tasks cannot decide that.
            # Replicating them would let each shard escalate on partial information.
            # The aggregate owns escalation, which is also why the shard's remaining
            # `depends_on` references no longer dangle once they are removed.
            kept -= {t.task_id for t in execution_plan.tasks if t.is_escalation}
            execution_plan = ExecutionPlan(
                plan_id=execution_plan.plan_id,
                source_plan_id=execution_plan.source_plan_id,
                repository_fingerprint=execution_plan.repository_fingerprint,
                changed_files=list(execution_plan.changed_files),
                affected_capabilities=list(execution_plan.affected_capabilities),
                affected_components=list(execution_plan.affected_components),
                invalidated_evidence=list(execution_plan.invalidated_evidence),
                reusable_evidence=list(execution_plan.reusable_evidence),
                tasks=[t for t in execution_plan.tasks if t.task_id in kept],
                escalation_conditions=list(execution_plan.escalation_conditions),
                measurement_requirements=list(execution_plan.measurement_requirements),
                certification_requirements=list(
                    execution_plan.certification_requirements
                ),
                rationale=execution_plan.rationale,
                plan_fingerprint=execution_plan.plan_fingerprint,
                generated_at=execution_plan.generated_at,
                revalidation_sources=list(execution_plan.revalidation_sources),
                reusable_measurements=list(execution_plan.reusable_measurements),
                boundary_evidence=execution_plan.boundary_evidence,
            )
            total_tasks = len(assignment.task_ids(0)) + sum(
                len(set(assignment.task_ids(i)) - set(assignment.task_ids(0)))
                for i in range(1, shard_count)
            )
            print(
                f"[check] shard {shard_index + 1}/{shard_count}: executing "
                f"{len(kept)}/{total_tasks} assigned task(s)",
                file=sys.stderr,
            )

        run_start = time.monotonic()
        executed_task_ids: list[str] = []

        def _capture_record(rec):
            executed_task_ids.append(rec.task_id)

        try:
            report = self.orchestrator.execute(
                execution_plan,
                authorize={t.task_id for t in execution_plan.tasks},
                dry_run=False,
                on_record=_capture_record,
            )
        except KeyboardInterrupt:
            elapsed = time.monotonic() - run_start
            from runtime.verify import _record_verification_event

            _record_verification_event(
                None,
                profile_name="check",
                elapsed=elapsed,
                status="interrupted",
                passed=0,
                failed=0,
                final_decision="interrupted",
                extra_metadata={"tasks_executed": executed_task_ids},
            )
            print("[check] INTERRUPTED (SIGINT/SIGTERM)", file=sys.stderr)
            return 130

        elapsed_total = time.monotonic() - run_start

        # 5b. Execution budget report (M9-C65)
        from runtime.foundation.verification.execution_budget import (
            ExecutionBudget,
            classify_boundary,
        )

        budget = ExecutionBudget()
        total_tasks = len(execution_plan.tasks) if execution_plan.tasks else 0
        completed_tasks = len(executed_task_ids)
        external_timeout = elapsed_total > budget.execution_budget_seconds
        decision_val = getattr(report, "final_decision", "unknown")
        is_fail = decision_val not in ("certified", "passed")
        boundary_report = classify_boundary(
            elapsed=elapsed_total,
            budget=budget,
            completed=completed_tasks,
            total=total_tasks,
            external_timeout=external_timeout,
            interrupted=False,
            failed=is_fail,
            current_task=executed_task_ids[-1] if executed_task_ids else None,
        )
        print(boundary_report.format_text(), file=sys.stderr)

        # 6. Record the canonical ExecutionReport through the event/RunRecord chain.
        from runtime.verify import record_execution_report

        record_execution_report("check", report, time.monotonic() - run_start)

        # 7. Print the compact per-task summary (truthful evidence of what ran).
        if json_out:
            # M10-R2. A reconcile shard runner pipes stdout to `shard-N.json`, and the
            # aggregate job parses it back into an ExecutionReport. That only works if
            # stdout is *machine-readable* on request; the human summary and the
            # verdict banner go to stderr instead so they still reach the log without
            # corrupting the JSON document.
            print(report.to_json())
            print(_format_task_summary(report), file=sys.stderr)
            decision = getattr(report, "final_decision", "unknown")
            print(
                (
                    "✓ Verification CERTIFIED"
                    if decision == "certified"
                    else f"✗ Verification FAILED: {getattr(report, 'decision_reason', 'unknown')}"
                ),
                file=sys.stderr,
            )
            return 0 if decision == "certified" else 1

        print(_format_task_summary(report))

        # 8. Evidence → Verdict (exit-code contract unchanged).
        decision = getattr(report, "final_decision", "unknown")
        if decision == "certified":
            print("✓ Verification CERTIFIED")
            return 0
        else:
            print("✗ Verification FAILED")
            reason = getattr(report, "decision_reason", "unknown")
            print(f"  Reason: {reason}", file=sys.stderr)
            return 1

    def plan(
        self,
        changed_files: list[str] | None = None,
        *,
        json_out: bool = False,
        shard_matrix: bool = False,
        shard_count: int | None = None,
        shard_plan_out: str | None = None,
        test_shards: bool = False,
        test_shard_with_counts: bool = False,
        profile_matrix_for: str | None = None,
    ) -> int:
        """
        Plan-only mode.

        Returns:
          - changed surfaces
          - affected symbols
          - affected capabilities
          - verification requirements
          - selected verification tasks
          - skipped/deferred tasks
          - reasons
          - evidence reuse decisions.

        M10-R2 adds two machine-readable modes for the reconcile
        ``plan -> matrix -> aggregate`` topology. They exist so the partition is
        produced by the same code that assigns shards, rather than by YAML or a
        second implementation:

        * ``shard_matrix`` prints the GitHub Actions dynamic-matrix document for
          ``shard_count`` shards and nothing else, so the plan job can publish it via
          ``$GITHUB_OUTPUT`` without parsing prose.
        * ``shard_plan_out`` writes the serialized ``ExecutionPlan`` to a file, so a
          shard runner is handed the plan it was assigned instead of re-deriving one.
        """
        if changed_files is None:
            changed_files = _collect_changed_files()
        if not changed_files and not _is_git_available():
            print(
                "No changed files detected and git unavailable.",
                file=sys.stderr,
            )
            return 1

        if test_shards or profile_matrix_for is not None:
            if profile_matrix_for is not None:
                from runtime.foundation.verification.profile_tasks import (
                    profile_matrix as build_profile_matrix,
                )

                try:
                    print(build_profile_matrix(profile_matrix_for))
                except ValueError as exc:
                    print(str(exc), file=sys.stderr)
                    return 2
                return 0

            from runtime.foundation.verification.runtime_shards import (
                DEFAULT_SHARD_COUNT,
                build_test_shards,
                runtime_test_files,
            )
            from runtime.foundation.verification.runtime_shards import (
                shard_matrix as build_shard_matrix,
            )

            files = runtime_test_files()
            if not files:
                print("no runtime test files found", file=sys.stderr)
                return 1
            plan = build_test_shards(
                files,
                shard_count or DEFAULT_SHARD_COUNT,
                _runtime_test_counts() if test_shard_with_counts else None,
            )
            print(build_shard_matrix(plan))
            return 0

        if shard_matrix or shard_plan_out is not None:
            from runtime.foundation.verification.execution_shards import (
                assign_shards,
                plan_matrix,
            )

            execution_plan = self.orchestrator.build_execution_plan(changed_files)
            if not execution_plan.tasks:
                print(
                    "No tasks for this boundary; nothing to shard.",
                    file=sys.stderr,
                )
                return 1

            if shard_plan_out is not None:
                out = Path(shard_plan_out)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_text(
                    json.dumps(execution_plan.to_dict(), indent=2, default=str),
                    encoding="utf-8",
                )
                print(
                    f"[plan] wrote {execution_plan.plan_id} "
                    f"({len(execution_plan.tasks)} task(s)) to {out}",
                    file=sys.stderr,
                )

            if shard_matrix:
                assignment = assign_shards(execution_plan, shard_count or 1)
                print(plan_matrix(assignment, execution_plan))
            return 0

        plan: ControlPlanePlan = self.planner.plan(changed_files)
        obligations: ObligationSet = self._plan_to_obligations(plan, changed_files)

        if json_out:
            print(json.dumps(obligations.to_dict(), indent=2, default=str))
        else:
            self._print_plan_obligations(obligations)

        return 0

    def run(
        self,
        *,
        plan_path: str | None = None,
        json_out: bool = False,
        shard: tuple[int, int] | None = None,
        aggregate: str | None = None,
        result_out: str | None = None,
        task_scope: list[str] | None = None,
    ) -> int:
        """
        Execute an explicit or generated verification plan.

        M10-R2: a supplied plan is now **authoritative**.

        Previously this method loaded ``plan_path``, looked for
        ``ControlPlanePlan.from_dict`` via ``hasattr``, found nothing, discarded the
        payload it had just parsed, and then rebuilt the full plan from the changed
        files. Every "explicit plan" therefore executed the entire boundary again,
        and a corrupt plan file exited 0. Both are now hard errors.

        The plan format is ``m9-c49-execution-plan/v1`` — the
        :class:`~runtime.foundation.verification.execution_orchestrator.ExecutionPlan`
        that the executor actually consumes, not the C48 ``ControlPlanePlan``. That
        is deliberate: the C48 plan is derived from the changed files and holds
        capability-level tasks, so it cannot express a shard, and
        ``CapabilityResolution`` has no faithful reverse mapping. Sharding operates
        on the C49 plan, so that is what a plan file carries.

        ``aggregate`` merges the reports of every shard run over one plan and is the
        single place a verdict is formed for a fanned-out run. This is deliberately a
        flag on ``run`` rather than a new canonical operation: the operation
        vocabulary is a governed surface, and aggregation is a mode of executing a
        supplied plan rather than a different kind of request.
        """
        import time

        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionPlan,
        )
        from runtime.foundation.verification.execution_shards import (
            assign_shards,
            validate_shard_request,
        )

        if aggregate is not None:
            return self._aggregate_shard_reports(aggregate, json_out=json_out)

        supplied: ExecutionPlan | None = None

        if plan_path:
            path = Path(plan_path)
            try:
                raw = path.read_text()
            except OSError as exc:
                print(
                    f"Cannot read plan file {plan_path}: {exc}",
                    file=sys.stderr,
                )
                return 2
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                print(
                    f"Plan file {plan_path} is not valid JSON: {exc}. "
                    "Refusing to regenerate a plan from the changed files: a "
                    "verification run must execute the plan it was given.",
                    file=sys.stderr,
                )
                return 2
            if not isinstance(payload, dict):
                print(
                    f"Plan file {plan_path} must contain a JSON object, got "
                    f"{type(payload).__name__}.",
                    file=sys.stderr,
                )
                return 2
            try:
                supplied = ExecutionPlan.from_dict(payload)
            except ValueError as exc:
                print(
                    f"Plan file {plan_path} is unusable: {exc}",
                    file=sys.stderr,
                )
                return 2

            validation_errors = supplied.validate()
            if validation_errors:
                print(
                    f"Plan file {plan_path} failed validation: "
                    + "; ".join(validation_errors),
                    file=sys.stderr,
                )
                return 2

        if supplied is not None:
            execution_plan = supplied
            changed_files = list(supplied.changed_files)
        else:
            changed_files = _collect_changed_files()
            if not changed_files and not _is_git_available():
                print(
                    "No changed files detected and git unavailable.",
                    file=sys.stderr,
                )
                return 1
            # M10-R2: `run` previously also built a C48 `ControlPlanePlan` here and
            # passed it to `_plan_to_obligations`, whose result was assigned to
            # `_obligations` and then never read. That was dead computation on a
            # plan format that cannot express a shard, so it is gone rather than
            # reintroduced. The obligation rollup that *is* used lives in `plan`.
            execution_plan = self.orchestrator.build_execution_plan(changed_files)

        if shard is not None:
            index, count = validate_shard_request(*shard)
            assignment = assign_shards(execution_plan, count)
            if count > 1:
                from runtime.foundation.verification.execution_shards import (
                    evidence_path_conflicts,
                )

                conflicts = evidence_path_conflicts(assignment)
                if conflicts:
                    print(
                        "Refusing to fan out: concurrent tasks would share an "
                        "evidence destination: " + "; ".join(conflicts),
                        file=sys.stderr,
                    )
                    return 2
                kept = {t.task_id for t in assignment.shards[index]}
                # Escalation tasks are EXCLUDED from shard execution, not merely
                # replicated. They are gated on the GLOBAL mandatory outcome
                # (`stop-on-sufficiency` runs them only when no mandatory task passed), and a
                # shard holding a subset of the mandatory tasks cannot decide that.
                # Replicating them would let each shard escalate on partial information.
                # The aggregate owns escalation, which is also why the shard's remaining
                # `depends_on` references no longer dangle once they are removed.
                kept -= {t.task_id for t in execution_plan.tasks if t.is_escalation}
                print(
                    f"[run] shard {index + 1}/{count} executing "
                    f"{len(kept)}/{len(execution_plan.tasks)} task(s); "
                    f"partition={assignment.partition_fingerprint()[:12]}",
                    file=sys.stderr,
                )
                execution_plan = ExecutionPlan(
                    plan_id=execution_plan.plan_id,
                    source_plan_id=execution_plan.source_plan_id,
                    repository_fingerprint=execution_plan.repository_fingerprint,
                    changed_files=list(execution_plan.changed_files),
                    affected_capabilities=list(execution_plan.affected_capabilities),
                    affected_components=list(execution_plan.affected_components),
                    invalidated_evidence=list(execution_plan.invalidated_evidence),
                    reusable_evidence=list(execution_plan.reusable_evidence),
                    tasks=[t for t in execution_plan.tasks if t.task_id in kept],
                    escalation_conditions=list(execution_plan.escalation_conditions),
                    measurement_requirements=list(
                        execution_plan.measurement_requirements
                    ),
                    certification_requirements=list(
                        execution_plan.certification_requirements
                    ),
                    rationale=execution_plan.rationale,
                    plan_fingerprint=execution_plan.plan_fingerprint,
                    generated_at=execution_plan.generated_at,
                    revalidation_sources=list(execution_plan.revalidation_sources),
                    reusable_measurements=list(execution_plan.reusable_measurements),
                    boundary_evidence=execution_plan.boundary_evidence,
                )

        # M10-R3 (D2) — scoped execution by task identity.
        #
        # `--shard` partitions, which is right for a matrix leg but wrong for
        # reproduction: to re-run one failing CI obligation you need that task and
        # nothing else, and re-deriving the whole partition to extract it is exactly the
        # "reconstruct the global plan" step the mission forbids.
        #
        # The narrowing is strict in both directions, and that is the point:
        #
        # * an unknown id is a hard error, never a silent no-op. `--task exec-9999`
        #   must not quietly execute the whole plan and report a green run for a task
        #   that does not exist — that would be the most dangerous possible response to
        #   a typo in a reproduction command.
        # * escalation tasks are dropped for the same reason `--shard` drops them: they
        #   are gated on the GLOBAL mandatory outcome, and a single-task run cannot
        #   decide that. Running one would execute work the plan never authorised.
        # M10-R3 (L1c): validate the infrastructure backstop BEFORE any spawn.
        #
        # A workflow used to wrap the leg in a hand-written `timeout 85m`. On this
        # repository that literal is *smaller than an obligation's own declared budget*:
        # reconcile shard 3 holds a single task with `timeout_seconds=5400` (90 min),
        # so the wrapper would kill it five minutes before its contractual expiry. The
        # runner would report a timeout for work that was still legitimately running —
        # the exact class of opaque failure this milestone exists to end, and the
        # mission requires this state be rejected rather than documented against.
        #
        # VERIFY_INFRA_BACKSTOP_SECONDS is what the wrapper is actually set to. Absent,
        # the check is skipped: a local run has no infrastructure backstop to violate.
        if shard is not None and shard[0] is not None and shard[1]:
            _backstop_raw = os.environ.get("VERIFY_INFRA_BACKSTOP_SECONDS")
            if _backstop_raw:
                try:
                    _backstop = int(_backstop_raw)
                except ValueError:
                    print(
                        f"VERIFY_INFRA_BACKSTOP_SECONDS={_backstop_raw!r} is not an "
                        f"integer number of seconds; the backstop cannot be validated.",
                        file=sys.stderr,
                    )
                    return 2
                _problem = validate_infra_backstop(
                    execution_plan.tasks, _backstop, cpu_count()
                )
                if _problem:
                    print(
                        f"[run] Refusing to execute shard {shard[0] + 1}/{shard[1]}: "
                        f"{_problem}",
                        file=sys.stderr,
                    )
                    return 2
                print(
                    f"[run] backstop { _backstop }s validated against a contractual "
                    f"wall clock for this shard",
                    file=sys.stderr,
                )

        # M10-R3 (L1c): the runtime supplies the per-leg environment it requires.
        #
        # Both fan-out workflows declared FINANCE_DB_PATH and CLARIFIN_PYTHON by hand,
        # under *different* naming schemes (`e2e-playwright-N` vs `e2e-<leg_id>`). That
        # is per-leg mutable state in YAML, and it is the value that determines
        # correctness: two legs sharing a database is the cross-shard mutation the
        # Playwright script itself documents as the cause of drifting screenshots.
        #
        # The runtime already knows the repository root and the leg's own identity, so
        # this is derived rather than copied. Anything already set in the environment is
        # left alone, so a deliberate override still wins — what is removed is the
        # *obligation* to know any of it in YAML.
        if shard is not None and shard[0] is not None:
            from runtime.foundation.verification.execution_shards import leg_environment

            for _key, _value in leg_environment(
                leg=f"reconcile-shard-{shard[0]}-of-{shard[1] or 1}",
                plan_id=execution_plan.plan_id,
            ).items():
                os.environ.setdefault(_key, _value)

        if task_scope:
            known = {t.task_id for t in execution_plan.tasks}
            unknown = [tid for tid in task_scope if tid not in known]
            if unknown:
                print(
                    f"Unknown task id(s): {', '.join(unknown)}. "
                    f"Plan {execution_plan.plan_id} contains "
                    f"{len(known)} task(s): {', '.join(sorted(known))}",
                    file=sys.stderr,
                )
                return 2
            kept = set(task_scope) - {
                t.task_id for t in execution_plan.tasks if t.is_escalation
            }
            if not kept:
                print(
                    "Refusing to run: the requested task(s) are escalation-gated and "
                    "cannot be decided from a scoped run: "
                    + ", ".join(sorted(task_scope)),
                    file=sys.stderr,
                )
                return 2
            print(
                f"[run] scoped execution of {len(kept)}/{len(execution_plan.tasks)} "
                f"task(s): {', '.join(sorted(kept))}",
                file=sys.stderr,
            )
            execution_plan = _plan_with_tasks(execution_plan, kept)

        # O-2 signal truth: record the run through the canonical event/RunRecord
        # chain even when the caller provided an explicit plan path.
        run_start = time.monotonic()
        executed_task_ids: list[str] = []

        def _capture_record(rec):
            executed_task_ids.append(rec.task_id)

        # M10-R2 closeout. Two changes, both about making a shard diagnosable:
        #
        # 1. Live per-task lifecycle logging. The reconcile leg previously printed one
        #    line (`shard 1/7 executing 1/11 task(s)`) and then went silent for the rest
        #    of the run, so a leg that died mid-task left no indication of what it was
        #    doing.
        # 2. A terminal result document, written on EVERY terminal path below, instead of
        #    a stdout redirect. A stdout redirect only produces content if the process
        #    survives to the end, which is why four of seven legs left 0-byte reports and
        #    the aggregate could not tell a killed leg from a failing one.
        prefix = None
        if shard is not None and shard[1] > 1:
            prefix = f"reconcile-shard {shard[0] + 1}/{shard[1]}"
        orchestrator = self.orchestrator
        if prefix and getattr(orchestrator, "_progress_prefix", None) is None:
            orchestrator = ExecutionOrchestrator(
                command_overrides=orchestrator._command_overrides,
                measurement_search_dirs=orchestrator._measurement_search_dirs,
                max_runtime_overrides=orchestrator._max_runtime_overrides,
                evidence_root=orchestrator._evidence_root,
                progress_prefix=prefix,
            )
            print(
                f"[{prefix}] plan={execution_plan.plan_id} "
                f"tasks={len(execution_plan.tasks)} "
                f"ids={','.join(t.task_id for t in execution_plan.tasks) or '-'}",
                file=sys.stderr,
                flush=True,
            )

        try:
            report = orchestrator.execute(
                execution_plan,
                authorize={t.task_id for t in execution_plan.tasks},
                dry_run=False,
                on_record=_capture_record,
            )
        except KeyboardInterrupt:
            elapsed = time.monotonic() - run_start
            _write_leg_result(
                result_out,
                leg_id=prefix or "run",
                shard_id=(f"reconcile-shard-{shard[0]}" if shard is not None else None),
                status="interrupted",
                final_decision="interrupted",
                exit_code=130,
                duration_seconds=elapsed,
                tasks=executed_task_ids,
            )
            from runtime.verify import _record_verification_event

            _record_verification_event(
                None,
                profile_name="run",
                elapsed=elapsed,
                status="interrupted",
                passed=0,
                failed=0,
                final_decision="interrupted",
                extra_metadata={"tasks_executed": executed_task_ids},
            )
            return 130

        _write_leg_result(
            result_out,
            leg_id=prefix or "run",
            shard_id=(f"reconcile-shard-{shard[0]}" if shard is not None else None),
            status="passed" if report.final_decision == "certified" else "failed",
            final_decision=report.final_decision,
            exit_code=0 if report.final_decision == "certified" else 1,
            duration_seconds=time.monotonic() - run_start,
            tasks=executed_task_ids,
            # M11-R4. This used to emit three keys per record — task_id,
            # completion_state, reason — while `_aggregate_shard_reports` rebuilds
            # them as `TaskExecutionRecord(**record)` against the full 23-field shape.
            # The two halves of one contract disagreed, so every reconcile aggregate
            # died with
            #     TypeError: TaskExecutionRecord.__init__() missing 20 required
            #                positional arguments
            # and the gate produced no verdict at all. It was masked for a long time
            # because the shards were independently red, so the crash was never the
            # first thing anyone saw.
            #
            # The fix is on the producer: a shard writes what a record IS, so the
            # aggregate gets the evidence — durations, exit codes, diagnostics,
            # measurement truth — instead of a summary it then has to guess at.
            records=[r.to_dict() for r in report.records],
        )

        from runtime.verify import record_execution_report

        record_execution_report("run", report, time.monotonic() - run_start)

        _publish_leg_certification(report, shard=shard, prefix=prefix)

        if json_out:
            print(report.to_json())
        else:
            self._print_execution_report(report)
            print(_format_task_summary(report))

        return 0 if report.final_decision == "certified" else 1

    def aggregate_playwright_legs(
        self,
        results_dir: str,
        *,
        shard_count: int | None = None,
        json_out: bool = False,
    ) -> int:
        """Aggregate the Playwright fan-out into one verdict (M10-R2).

        The gate is the authority. It refuses to certify unless every leg the plan
        declared reported exactly once and passed — functional shards *and* one visual
        leg per project. A missing leg means its tests never ran, which must never
        certify, and the visual legs are checked exactly like the functional ones so a
        dropped screenshot pass cannot pass unnoticed.
        """
        import time

        from runtime.foundation.verification.playwright_shards import (
            expected_leg_ids,
            read_leg_results,
            verify_legs,
        )

        started = time.monotonic()
        results, absent, malformed, rejected = read_leg_results(Path(results_dir))
        expected = expected_leg_ids(shard_count or 4)

        problems: list[str] = []
        # absent / malformed / rejected are three different failures with three
        # different owners; see read_shard_results for why they are never conflated.
        if absent:
            problems.append(
                "leg(s) produced NO TERMINAL RESULT (killed, cancelled or never "
                "started), so their tests are unreported: " + ", ".join(absent)
            )
        if malformed:
            problems.append(
                "leg result document(s) MALFORMED (producer bug): "
                + ", ".join(malformed)
            )
        if rejected:
            problems.append(
                "leg result document(s) REJECTED (unsupported schema): "
                + ", ".join(rejected)
            )
        problems.extend(verify_legs(expected, results))

        passed = sum(1 for r in results if r.ok)
        visual = [r for r in results if r.shard_id.endswith("-visual")]
        certified = not problems
        reason = (
            f"all {len(expected)} leg(s) passed ({len(visual)} visual, "
            f"{len(results) - len(visual)} functional)"
            if certified
            else "; ".join(problems)
        )

        if json_out:
            print(
                json.dumps(
                    {
                        "legs_expected": expected,
                        "legs_reported": len(results),
                        "legs_passed": passed,
                        "visual_legs": len(visual),
                        "leg_results": [r.to_dict() for r in results],
                        "final_decision": (
                            "certified" if certified else "not_certified"
                        ),
                        "decision_reason": reason,
                        "elapsed_seconds": round(time.monotonic() - started, 2),
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            print(
                f"[playwright-gate] "
                f"{'CERTIFIED' if certified else 'NOT CERTIFIED'}: {reason}"
            )

        return 0 if certified else 1

    def run_test_shards(
        self,
        *,
        shard_index: int | None = None,
        shard_count: int | None = None,
        result_out: str | None = None,
        verify_dir: str | None = None,
        json_out: bool = False,
    ) -> int:
        """Run one runtime test shard, or aggregate every shard (M10-R2).

        The gate is the authority. It refuses to certify unless every expected shard
        reported exactly once, every shard passed, and the independent integrity
        obligation passed. "The aggregate job succeeded" is never read as "every shard
        succeeded" — that is the whole reason this gate exists rather than letting the
        matrix job statuses speak for it.
        """
        import time

        from runtime.foundation.verification.runtime_shards import (
            DEFAULT_SHARD_COUNT,
            expected_shard_ids,
            read_shard_results,
            run_test_shard,
            summarise_shards,
            verify_shards,
        )

        if shard_index is not None:
            if not result_out:
                print(
                    "--shard requires --result-out <path> so the gate can read the "
                    "shard's outcome",
                    file=sys.stderr,
                )
                return 2
            try:
                shard = run_test_shard(
                    shard_index,
                    shard_count or DEFAULT_SHARD_COUNT,
                    result_out=Path(result_out),
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(
                f"[runtime-shard] {shard.shard_id} {shard.status} "
                f"files={shard.file_count} passed={shard.passed} "
                f"failed={shard.failed} ({shard.duration_seconds:.1f}s)",
                file=sys.stderr,
            )
            return 0 if shard.ok else 1

        if not verify_dir:
            print(
                "run --profile runtime needs --shard N (a leg) or "
                "--verify-shards <dir> (the gate)",
                file=sys.stderr,
            )
            return 2

        started = time.monotonic()
        results, absent, malformed, rejected = read_shard_results(Path(verify_dir))
        # The integrity obligation runs here, after the shards: it is a distinct
        # canonical operation (`runtime.verify integrity`) that the monolithic
        # self-test used to run sequentially. Running it in the gate keeps it a real
        # obligation rather than folding it into the last shard.
        print(
            f"[runtime-gate] {len(results)} shard result(s) read; "
            f"absent={len(absent)} malformed={len(malformed)} rejected={len(rejected)}"
        )
        summary = summarise_shards(results)
        if summary:
            print(summary)

        # The integrity obligation is a distinct canonical operation
        # (`runtime.verify integrity`) that the monolithic self-test used to run
        # sequentially after the suite. It runs here, in the gate, as a real
        # obligation rather than being folded into whichever shard happened to be
        # last — otherwise a green suite could mask a red integrity scan.
        integrity_ok: bool | None = None
        if not (absent or malformed or rejected) and all(r.ok for r in results):
            integrity_ok = _run_runtime_integrity(Path(verify_dir))

        problems: list[str] = []
        # Three distinct failure buckets, never conflated. A leg with no file never
        # reached a terminal result (infrastructure); a malformed or rejected file is a
        # producer bug. Collapsing them into one "unreadable" list is what made the
        # earlier reconcile failure undiagnosable.
        if absent:
            problems.append(
                "shard(s) produced NO TERMINAL RESULT (killed, cancelled or never "
                "started), so their tests are unreported: " + ", ".join(absent)
            )
        if malformed:
            problems.append(
                "shard result document(s) MALFORMED (producer bug): "
                + ", ".join(malformed)
            )
        if rejected:
            problems.append(
                "shard result document(s) REJECTED (unsupported schema): "
                + ", ".join(rejected)
            )
        problems.extend(
            verify_shards(
                shard_count or len(results),
                results,
                integrity_ok=integrity_ok,
            )
        )

        certified = not problems
        reason = (
            f"all {len(results)} shard(s) passed across "
            f"{sum(r.file_count for r in results)} file(s); "
            f"{sum(r.passed for r in results)} test(s) passed"
            if certified
            else "; ".join(problems)
        )

        if json_out:
            print(
                json.dumps(
                    {
                        "shards_expected": expected_shard_ids(
                            shard_count or len(results)
                        ),
                        "shards_reported": len(results),
                        "shard_results": [r.to_dict() for r in results],
                        "tests_passed": sum(r.passed for r in results),
                        "files_covered": sum(r.file_count for r in results),
                        "final_decision": (
                            "certified" if certified else "not_certified"
                        ),
                        "decision_reason": reason,
                        "elapsed_seconds": round(time.monotonic() - started, 2),
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            print(
                f"[runtime-gate] {'CERTIFIED' if certified else 'NOT CERTIFIED'}: "
                f"{reason}"
            )

        return 0 if certified else 1

    def run_profile_fanout(
        self,
        profile_op: str,
        *,
        task: str | None = None,
        result_out: str | None = None,
        verify_legs: str | None = None,
        json_out: bool = False,
    ) -> int:
        """Run one obligation of a profile, or aggregate a profile's legs (M10-R2).

        Three modes on one surface:

        * ``task=<id>`` — execute exactly that canonical obligation on this runner and
          write a result document. This is the matrix leg. The command comes from the
          profile's own task list and runs through the shared worker, so a leg *is* the
          obligation rather than a re-implementation of it.
        * ``verify_legs=<dir>`` — the gate. Reads every leg result and refuses to
          certify unless every canonical obligation reported and passed, then runs the
          profile's evidence-rollup task(s) and exits with the profile's verdict.

        The gate is the authority. A missing obligation, a duplicate report, an unknown
        task id, or any non-passing leg all block certification — the same split-brain
        discipline the reconcile shard merge uses. There is no path by which a red or
        absent leg yields a green required check.
        """
        import time

        from runtime.foundation.verification.profile_tasks import (
            aggregate_tasks,
            expected_obligation_ids,
            read_leg_results,
            run_obligation_leg,
            summarise_legs,
        )
        from runtime.foundation.verification.profile_tasks import (
            verify_legs as verify_leg_results,
        )

        if task:
            if not result_out:
                print(
                    "--task requires --result-out <path> so the gate can read the "
                    "leg's outcome",
                    file=sys.stderr,
                )
                return 2
            try:
                result = run_obligation_leg(
                    profile_op,
                    task,
                    result_out=Path(result_out),
                    timeout_seconds=_profile_task_timeout_seconds(),
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            print(
                f"[profile-leg:{profile_op}] {result.task_id} {result.status} "
                f"({result.duration_seconds:.1f}s)",
                file=sys.stderr,
            )
            return 0 if result.ok else 1

        if not verify_legs:
            print(
                "run --profile needs either --task <id> (a leg) or "
                "--verify-legs <dir> (the gate)",
                file=sys.stderr,
            )
            return 2

        started = time.monotonic()
        results, absent, malformed, rejected = read_leg_results(Path(verify_legs))
        problems: list[str] = []
        if absent:
            problems.append(
                "obligation leg(s) produced NO TERMINAL RESULT (killed, cancelled or "
                "never started), so their obligations are unreported: "
                + ", ".join(absent)
            )
        if malformed:
            problems.append(
                "obligation result document(s) MALFORMED (producer bug): "
                + ", ".join(malformed)
            )
        if rejected:
            problems.append(
                "obligation result document(s) REJECTED (unsupported schema): "
                + ", ".join(rejected)
            )
        problems.extend(verify_leg_results(profile_op, results))

        print(f"[profile-gate:{profile_op}] {len(results)} leg result(s) read")
        summary = summarise_legs(results)
        if summary:
            print(summary)

        # The evidence rollup runs only once every obligation has reported, because it
        # reads what they produced. That is a genuine data dependency and therefore a
        # real barrier, not an ordering preference.
        rollups = aggregate_tasks(profile_op)
        if not problems:
            for rollup in rollups:
                outcome = run_obligation_leg(
                    profile_op,
                    rollup.id,
                    result_out=Path(verify_legs) / f"aggregate-{rollup.id}.json",
                    timeout_seconds=_profile_task_timeout_seconds(),
                )
                if not outcome.ok:
                    problems.append(
                        f"{rollup.id} {outcome.status} exit={outcome.exit_code}"
                    )

        elapsed = time.monotonic() - started
        passed = sum(1 for r in results if r.ok)
        expected = expected_obligation_ids(profile_op)
        certified = not problems
        reason = (
            f"all {len(expected)} obligation(s) passed; "
            f"evidence rollup {len(rollups)} task(s) passed"
            if certified
            else "; ".join(problems)
        )

        if json_out:
            print(
                json.dumps(
                    {
                        "profile": profile_op,
                        "obligations_expected": expected,
                        "legs_reported": len(results),
                        "legs_passed": passed,
                        "rollups": len(rollups),
                        "final_decision": (
                            "certified" if certified else "not_certified"
                        ),
                        "decision_reason": reason,
                        "elapsed_seconds": round(elapsed, 2),
                    },
                    indent=2,
                    default=str,
                )
            )
        else:
            print(
                f"[profile-gate:{profile_op}] "
                f"{'CERTIFIED' if certified else 'NOT CERTIFIED'}: {reason}"
            )

        return 0 if certified else 1

    def _aggregate_shard_reports(
        self, shard_dir: str, *, json_out: bool = False
    ) -> int:
        """Merge every shard's report over one plan and form the single verdict.

        This is the M10-R2 reconcile aggregate step. The property that makes it safe
        is asserted in ``execution_shards.merge_shard_reports`` and re-stated here
        because it is the whole reason this step exists: a set of records that does
        not cover every task in the plan can only produce ``NOT_CERTIFIABLE``, with
        the missing ids named. There is no configuration in which a shard that
        silently failed to report leaves the run certifiable.
        """

        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionPlan,
            ExecutionReport,
            TaskExecutionRecord,
        )
        from runtime.foundation.verification.execution_shards import (
            merge_shard_reports,
        )
        from runtime.foundation.verification.runtime_shards import (
            expected_shard_ids,
        )

        root = Path(shard_dir)
        plan_file = root / "plan.json"
        if not plan_file.exists():
            print(
                f"[aggregate] no plan.json in {shard_dir}; the aggregate job must "
                "receive the plan artifact alongside the shard reports",
                file=sys.stderr,
            )
            return 2
        try:
            plan = ExecutionPlan.from_dict(json.loads(plan_file.read_text()))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"[aggregate] unreadable plan {plan_file}: {exc}", file=sys.stderr)
            return 2

        # A shard whose process was killed leaves no file at all. That is an
        # infrastructure event and the gate must be able to NAME it, so the shard count
        # is compared against how many files actually arrived rather than the gate
        # discovering it as "0 of N tasks missing".
        shard_files = sorted(root.glob("shard-*.json"))
        expected_shards = len(expected_shard_ids(len(shard_files) or 1))
        if not shard_files:
            print(
                f"[aggregate] no shard-*.json reports in {shard_dir}; a gate that "
                "aggregates zero shards would certify nothing and must not report "
                "success",
                file=sys.stderr,
            )
            return 2
        if len(shard_files) != expected_shards:
            print(
                f"[aggregate] TRANSPORT: expected {expected_shards} shard result(s), "
                f"{len(shard_files)} arrived. At least one leg produced NO TERMINAL "
                "RESULT (killed, cancelled, or never started).",
                file=sys.stderr,
            )

        reports: list[ExecutionReport] = []
        unreadable: list[str] = []
        for path in shard_files:
            try:
                payload = json.loads(path.read_text())
            except (OSError, json.JSONDecodeError) as exc:
                # A shard that died mid-flight — wrapper timeout, OOM, cancellation —
                # leaves no readable report. That is not a reason for the gate to
                # produce no verdict at all: it is exactly the "shard coverage
                # incomplete" case, and it must be decided NOT_CERTIFIABLE with the
                # offending file named, never as an opaque exit 2 with nothing to act
                # on. Its tasks then simply never appear in the record set, which is
                # what the missing-task guard is for.
                print(
                    f"[aggregate] shard report {path.name} is unreadable "
                    f"({type(exc).__name__}); its tasks count as unreported: {exc}",
                    file=sys.stderr,
                )
                unreadable.append(path.name)
                continue
            if payload.get("plan_id") not in (None, plan.plan_id):
                print(
                    f"[aggregate] {path.name} reports plan_id={payload['plan_id']} but "
                    f"the aggregate plan is {plan.plan_id}; the shards did not agree "
                    "on the plan",
                    file=sys.stderr,
                )
                return 2
            records = []
            for index, record in enumerate(payload.get("records") or []):
                record["completion_state"] = _as_state(record.get("completion_state"))
                try:
                    records.append(TaskExecutionRecord(**record))
                except TypeError as exc:
                    # M11-R4. A record the producer truncated is a PRODUCER BUG, and
                    # the aggregator's own contract says such a document is reported,
                    # never coerced into a verdict and never allowed to abort the run.
                    # This loop used to raise straight through, so one malformed record
                    # cost the operator the entire gate verdict — the opposite of what
                    # the absent/unreadable handling above is for.
                    print(
                        f"[aggregate] {path.name} record #{index} is MALFORMED "
                        f"(producer bug): {exc}",
                        file=sys.stderr,
                    )
                    unreadable.append(f"{path.name}#{index}")
                    continue
            if not records and payload.get("records"):
                # Every record in this shard was unusable, so the shard contributed
                # nothing. Its tasks must count as unreported, not as passing.
                continue
            reports.append(
                ExecutionReport(
                    report_id=payload.get("report_id", path.stem),
                    plan_id=payload.get("plan_id", plan.plan_id),
                    plan_fingerprint=payload.get(
                        "plan_fingerprint", plan.plan_fingerprint
                    ),
                    started_at=payload.get("started_at", ""),
                    completed_at=payload.get("completed_at", ""),
                    total_duration_seconds=payload.get("total_duration_seconds", 0.0),
                    records=records,
                    efficiency=payload.get("efficiency") or {},
                    final_decision=payload.get("final_decision", "unknown"),
                    decision_reason=payload.get("decision_reason", ""),
                    evidence_reused=payload.get("evidence_reused") or [],
                    escalations_triggered=payload.get("escalations_triggered") or [],
                    decisions=payload.get("decisions") or [],
                )
            )

        print(
            f"[aggregate] plan={plan.plan_id} tasks={len(plan.tasks)} "
            f"shards={len(reports)} unreadable={len(unreadable)}",
            file=sys.stderr,
        )
        report = merge_shard_reports(plan, reports, live_fp=plan.repository_fingerprint)

        if unreadable:
            report.final_decision = "not_certifiable"
            report.decision_reason = (
                f"{report.decision_reason} | shard report(s) unreadable, so their "
                f"tasks are unreported: {', '.join(unreadable)}"
            )
            report.efficiency["unreadable_shard_reports"] = len(unreadable)

        from runtime.verify import record_execution_report

        record_execution_report("run", report, 0.0)

        if json_out:
            print(report.to_json())
        else:
            self._print_execution_report(report)
            print(_format_task_summary(report))

        if report.final_decision != "certified":
            print(
                f"[aggregate] {report.final_decision}: {report.decision_reason}",
                file=sys.stderr,
            )
        return 0 if report.final_decision == "certified" else 1

    def diagnose(self, changed_files: list[str] | None = None) -> int:
        """
        Failure/survivor diagnostic control-plane entrypoint.

        Automatically selects the appropriate internal diagnostic capabilities.
        """
        if changed_files is None:
            changed_files = _collect_changed_files()
        if not changed_files:
            print("No changed files detected.", file=sys.stderr)
            return 1

        # Delegate to intelligence layer for change/risk/blast analysis
        bundle = analyze(changed_files=changed_files)
        print(
            format_diagnostic(
                bundle["change"],
                bundle["blast"],
                bundle["risk"],
                bundle["repair"],
            )
        )
        return 0

    def strengthen(
        self,
        *,
        plan_path: str | None = None,
        json_out: bool = False,
        args: list[str] | None = None,
    ) -> int:
        """
        Test-strengthening control-plane entrypoint.

        Automatically routes:
          * survivor diagnosis;
          * candidate discovery;
          * candidate generation;
          * validation;
          * mutant re-execution;
          * regression verification;
          * evidence promotion.
        """
        args = list(args or [])
        # Support --capability flag for explicit capability targeting
        capability_id = None
        remaining_args = list(args)
        for i, arg in enumerate(args):
            if arg == "--capability" and i + 1 < len(args):
                capability_id = args[i + 1]
                remaining_args = list(args[:i]) + list(args[i + 2 :])
                break

        if capability_id:
            # Run strengthening pipeline for specific capability
            from runtime.foundation.verification.strengthening_pipeline import (
                format_strengthening_report,
                run_capability_aware_strengthening_pipeline,
            )

            report = run_capability_aware_strengthening_pipeline(
                capability_id=capability_id
            )
            output = (
                json.dumps(report.to_dict(), indent=2, default=str)
                if json_out
                else format_strengthening_report(report)
            )
            print(output)
            return 0
        else:
            # No capability specified: run mutation smoke test as default behavior
            from runtime.foundation.verification.mutation_runner import (
                run_mutation_cli,
            )

            old_argv = sys.argv
            sys.argv = ["verify.py", "mutation"] + remaining_args
            try:
                return run_mutation_cli(remaining_args)
            finally:
                sys.argv = old_argv

    def inspect(self, query: str | None = None, *, json_out: bool = False) -> int:
        """
        Read-only inspection/query entrypoint.

        Examples:
          verify inspect capabilities
          verify inspect evidence
          verify inspect plan
          verify inspect mutation
          verify inspect workflows
          verify inspect health
        """
        if query is None:
            print(
                "Missing inspect subquery. Use: capabilities, evidence, plan, mutation, workflows, health",
                file=sys.stderr,
            )
            return 1

        q = query.lower()
        if q == "capabilities":
            from runtime.foundation.verification.capability_catalog import (
                cmd_capabilities,
            )

            old_argv = sys.argv
            sys.argv = ["verify.py", "capabilities"]
            try:
                return cmd_capabilities([])
            finally:
                sys.argv = old_argv
        elif q == "evidence":
            # Show current obligations / open evidence gaps
            changed_files = _collect_changed_files()
            plan = self.planner.plan(changed_files)
            obligations: ObligationSet = self._plan_to_obligations(plan, changed_files)
            if json_out:
                print(json.dumps(obligations.to_dict(), indent=2, default=str))
            else:
                print(f"Total obligations: {len(obligations.obligations)}")
                print(
                    f"Open: {len([o for o in obligations.obligations if o.disposition == 'open'])}"
                )
                print(
                    f"Closed: {len([o for o in obligations.obligations if o.disposition == 'closed'])}"
                )
                for o in obligations.obligations:
                    if o.disposition == "open":
                        print(
                            f"  - {o.obligation_id}: {o.capability.capability_id} ({o.requirement.obligation_kind.value})"
                        )
        elif q == "plan":
            changed_files = _collect_changed_files()
            plan = self.planner.plan(changed_files)
            if json_out:
                print(json.dumps(plan.to_dict(), indent=2, default=str))
            else:
                print(f"Plan ID: {plan.plan_id}")
                caps = list(plan.capability_resolution.directly_affected_capabilities)
                print(f"Capabilities: {caps}")
                print(f"Tasks: {len(plan.tasks)}")
        elif q == "mutation":
            from runtime.foundation.verification.measurement_truth_integration import (
                format_measurement_truth_report,
                get_measurement_truth_integrator,
            )

            integrator = get_measurement_truth_integrator()
            report = integrator.evaluate_all_capabilities()
            print(format_measurement_truth_report(report))
            return 0
        elif q == "workflows":
            from runtime.foundation.verification.workflow_inspection import (
                cmd_inspect_workflows,
            )

            # Build clean argv for the workflow command: only flags like --json, --out
            workflow_args = [a for a in sys.argv[2:] if a.startswith("--")]
            return cmd_inspect_workflows(workflow_args)
        elif q == "health":
            from runtime.system.observability.health_report import (
                EngineeringHealthReport,
            )

            health_report = EngineeringHealthReport()
            print(health_report.generate())
            return 0
        elif q == "evidence-cleanup":
            from runtime.foundation.verification.evidence_retention import (
                cmd_evidence_cleanup,
            )

            old_argv = sys.argv
            sys.argv = ["verify.py", "evidence-cleanup"] + sys.argv[2:]
            try:
                return cmd_evidence_cleanup(sys.argv[2:])
            finally:
                sys.argv = old_argv
        elif q == "frontend-backend-sync":
            from runtime.foundation.verification.frontend_backend_gate import (
                run_gate as _run_frontend_backend_gate,
            )

            return _run_frontend_backend_gate()
        else:
            print(f"Unknown inspect subquery: {query}", file=sys.stderr)
            return 1
        return 0

    def certify(self) -> int:
        """
        Certification should be the only explicit certification-oriented public entrypoint.
        It must remain evidence-gated.
        """
        # Delegates to the certification module which enforces evidence gates
        return certification_main()

    def ci(self, args: list[str] | None = None) -> int:
        """
        CI-specific orchestration/reconciliation entrypoint where needed.

        Accepts the same CLI flags as the legacy ``reconcile`` / ``exec-evidence``
        commands so that both direct invocation and migration-route invocation
        honor the same argument contract. This is required because the
        legacy→canonical migration must preserve the operator-visible interface.
        """

        raw = args or sys.argv[2:]

        # Detect exec-evidence mode vs reconcile mode.
        has_out = "--out" in raw or any(a.startswith("--out=") for a in raw)
        has_profile = "--profile" in raw or any(a.startswith("--profile=") for a in raw)
        if has_out or has_profile:
            return self._run_exec_evidence_cli(raw)
        return self._run_reconcile_cli_from_args(raw)

    def _run_exec_evidence_cli(self, args: list[str]) -> int:
        """Create an execution-evidence artifact (M5-C / M6-A).

        Extracted from the legacy ``exec-evidence`` command. Produces a
        ``vea5-execution-evidence/v2`` artifact with one unit record per selected
        unit in the plan, stamped with the caller-supplied status/exit/duration.
        """
        from datetime import UTC, datetime

        from runtime.foundation.verification.evidence_contract import (
            ExecutionAttempt,
            ExecutionEvidenceV2,
            UnitExecutionRecord,
            save_execution_evidence_v2,
        )
        from runtime.foundation.verification.reconciliation import (
            _load_plan_from_manifest,
            plan_fingerprint,
        )

        plan_path = _find_arg("--plan", args, default=None)
        status = _find_arg("--status", args, default="pass")
        exit_code_str = _find_arg("--exit", args, default="0")
        duration_str = _find_arg("--duration", args, default="0.0")
        commit_sha = _find_arg("--commit", args, default=None)
        out_path = _find_arg("--out", args, default=None)

        plan_path = plan_path or os.environ.get("CI_PLAN_PATH")
        commit_sha = commit_sha or os.environ.get("GITHUB_SHA", _get_current_commit())
        out_path = out_path or os.environ.get(
            "CI_EVIDENCE_PATH", "runtime/generated/vea5-execution.pr.json"
        )

        if not plan_path:
            print("--plan is required for exec-evidence", file=sys.stderr)
            return 1
        if not out_path:
            print("--out is required for exec-evidence", file=sys.stderr)
            return 1

        try:
            plan = _load_plan_from_manifest(plan_path)
        except Exception as exc:
            print(f"Failed to load plan: {exc}", file=sys.stderr)
            return 1

        try:
            exit_code = int(exit_code_str)
        except ValueError:
            exit_code = 0
        try:
            duration = float(duration_str)
        except ValueError:
            duration = 0.0

        records: dict[str, UnitExecutionRecord] = {}
        for sel in plan.selected:
            records[sel.unit_id] = UnitExecutionRecord(
                unit_id=sel.unit_id,
                provenance={
                    "category": sel.category,
                    "source": sel.source,
                    "capabilities": list(sel.capabilities),
                    "impact_kinds": list(sel.impact_kinds),
                },
                attempts=(
                    ExecutionAttempt(
                        attempt_index=0,
                        command=sel.command,
                        started_at=None,
                        ended_at=None,
                        duration_seconds=duration,
                        exit_code=exit_code,
                        status=status,
                        stdout_ref=None,
                        stderr_ref=None,
                        artifacts=(),
                    ),
                ),
            )

        from runtime.foundation.verification.reconciliation import (
            _load_plan_from_manifest,
        )

        fp = plan_fingerprint(plan)
        evidence = ExecutionEvidenceV2(
            tier=plan.tier,
            plan_fingerprint=fp.digest(),
            commit=commit_sha or "",
            units=tuple(records[u.unit_id] for u in plan.selected),
            generated_at=datetime.now(UTC).isoformat(),
        )
        save_execution_evidence_v2(evidence, out_path)
        print(f"Wrote execution evidence to {out_path}")
        return 0

    def _run_reconcile_cli_from_args(self, args: list[str]) -> int:
        """Reconciliation gate with explicit CLI-arg resolution (M5-D / M5-E)."""

        plan_path = _find_arg("--plan", args, default=None)
        evidence_path = _find_arg("--evidence", args, default=None)
        report_path = _find_arg("--report", args, default=None)
        commit_sha = _find_arg("--commit", args, default=None)
        local_plan_path = _find_arg("--local", args, default=None)
        local_evidence_path = _find_arg("--local-evidence", args, default=None)

        plan_path = plan_path or os.environ.get(
            "CI_PLAN_PATH", "runtime/generated/vea5-tier-plan.pr.json"
        )
        evidence_path = evidence_path or os.environ.get(
            "CI_EVIDENCE_PATH", "runtime/generated/vea5-execution.pr.json"
        )
        report_path = report_path or os.environ.get(
            "CI_REPORT_PATH", "runtime/generated/vea5-reconciliation.pr.json"
        )
        commit_sha = commit_sha or os.environ.get("GITHUB_SHA", _get_current_commit())

        # For LOCAL-vs-CI reconciliation mode, also surface the local-side paths.
        local_plan_path = local_plan_path or os.environ.get("LOCAL_PLAN_PATH")
        local_evidence_path = local_evidence_path or os.environ.get(
            "LOCAL_EVIDENCE_PATH"
        )

        return self._run_reconcile_cli(
            plan_path=plan_path,
            evidence_path=evidence_path,
            report_path=report_path,
            commit_sha=commit_sha,
            local_plan_path=local_plan_path,
            local_evidence_path=local_evidence_path,
        )

    def _run_reconcile_cli(
        self,
        plan_path: str | None = None,
        evidence_path: str | None = None,
        report_path: str | None = None,
        commit_sha: str | None = None,
        local_plan_path: str | None = None,
        local_evidence_path: str | None = None,
    ) -> int:
        """Run the existing reconcile CLI with explicitly supplied paths.

        When called through the canonical ``ci`` entrypoint the paths come from
        parsed CLI args / env vars. When called through the legacy ``reconcile``
        migration path they fall back to the historic env-var defaults.

        Two modes are supported:
          * CI-only (``--evidence`` present, no ``--local``): validates a CI
            plan against its own persisted execution evidence (M5-A).
          * LOCAL-vs-CI (``--local`` present): compares a local plan against a CI
            plan for structural equivalence (M4 / M5-B).
        """

        from runtime.foundation.verification.reconciliation import (
            ReconciliationStatus,
            reconcile,
            save_reconciliation_report,
            validate_ci_artifacts,
        )
        from runtime.foundation.verification.reconciliation import (
            _load_plan_from_manifest as _load_plan,
        )

        plan_path = plan_path or os.environ.get(
            "CI_PLAN_PATH", "runtime/generated/vea5-tier-plan.pr.json"
        )
        evidence_path = evidence_path or os.environ.get(
            "CI_EVIDENCE_PATH", "runtime/generated/vea5-execution.pr.json"
        )
        report_path = report_path or os.environ.get(
            "CI_REPORT_PATH", "runtime/generated/vea5-reconciliation.pr.json"
        )
        commit_sha = commit_sha or os.environ.get("GITHUB_SHA", _get_current_commit())

        # For LOCAL-vs-CI reconciliation mode, also surface the local-side paths.
        local_plan_path = local_plan_path or os.environ.get("LOCAL_PLAN_PATH")
        local_evidence_path = local_evidence_path or os.environ.get(
            "LOCAL_EVIDENCE_PATH"
        )

        # LOCAL-vs-CI mode: compare two plans structurally.
        if local_plan_path:
            try:
                local_plan = _load_plan(local_plan_path)
                ci_plan = _load_plan(plan_path)
            except Exception as e:
                print(f"Failed to load plan(s): {e}", file=sys.stderr)
                return 2
            local_results: dict[str, Any] = {}
            ci_results: dict[str, Any] = {}
            if local_evidence_path:
                from runtime.foundation.verification.reconciliation import (
                    _unit_results_from_any_evidence,
                )

                with contextlib.suppress(Exception):
                    local_results = _unit_results_from_any_evidence(local_evidence_path)
            if evidence_path:
                from runtime.foundation.verification.reconciliation import (
                    _unit_results_from_any_evidence,
                )

                with contextlib.suppress(Exception):
                    ci_results = _unit_results_from_any_evidence(evidence_path)
            report = reconcile(
                local_plan,
                ci_plan,
                local_results=local_results,
                ci_results=ci_results,
                commit=commit_sha,
            )
            if report_path:
                save_reconciliation_report(report, report_path)
            print(json.dumps(report.to_dict(), indent=2, default=str))
            status = report.classification.status
            if status == ReconciliationStatus.PLANNING_DIVERGENCE.value:
                return 2
            if status == ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value:
                return 1
            return 0

        # CI-only mode: validate plan against its own execution evidence.
        try:
            report = validate_ci_artifacts(
                ci_plan_path=plan_path,
                ci_evidence_path=evidence_path,
                commit=commit_sha,
            )
        except FileNotFoundError as e:
            print(f"CI artifacts not found: {e}", file=sys.stderr)
            return 1

        if report_path:
            save_reconciliation_report(report, report_path)

        print(json.dumps(report.to_dict(), indent=2, default=str))

        status = report.classification.status
        if status == ReconciliationStatus.PLANNING_DIVERGENCE.value:
            return 2
        if status == ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value:
            return 1
        return 0

    def _diagnose_framework(self) -> Any:
        """Return FrameworkIntegrityResult for the verification framework."""
        from runtime.foundation.verification.authority_drift_detector import (
            run_authority_drift_detection,
        )
        from runtime.foundation.verification.framework_integrity import (
            FrameworkIntegrityResult,
            FrameworkSelfTests,
        )

        drift = run_authority_drift_detection()
        integrity = FrameworkIntegrityResult.from_drift_report(
            drift,
            artifact_summary={"detector": "authority_drift_detector"},
        )
        self_tests = FrameworkSelfTests()
        test_result = self_tests.run_all()
        all_findings = list(integrity.findings) + list(test_result.findings)
        return FrameworkIntegrityResult(
            health=integrity.health,
            critical_count=integrity.critical_count + test_result.critical_count,
            high_count=integrity.high_count + test_result.high_count,
            medium_count=integrity.medium_count + test_result.medium_count,
            low_count=integrity.low_count + test_result.low_count,
            info_count=integrity.info_count + test_result.info_count,
            total_findings=len(all_findings),
            findings=all_findings,
            artifact_summary={"detector": "authority_drift_detector"},
            diagnostic={
                "self_tests": test_result.diagnostic.get("self_tests", {}),
                "passed": test_result.diagnostic.get("passed", 0),
                "total": test_result.diagnostic.get("total", 0),
            },
        )

    def doctor(self) -> int:
        """
        Framework health/integrity diagnostics.

        This is for the verification framework itself rather than application verification.
        Includes authority drift detection from the authority_drift_detector module.
        Returns FrameworkIntegrityResult via diagnose(); int for CLI compatibility.
        """
        from runtime.system.observability.health_report import (
            EngineeringHealthReport,
        )

        report = EngineeringHealthReport()
        output = report.generate()
        print(output)

        integrity = self._diagnose_framework()
        if integrity.healthy:
            print("\nFramework authority integrity: HEALTHY")
        else:
            print("\nFramework authority integrity: DEGRADED")
            for f in integrity.findings:
                print(
                    f"  [{f.severity.upper()}] {f.check_name}: {f.detected_component}"
                )
                print(f"    Expected: {f.expected_authority}")
                print(f"    Actual:   {f.actual_authority}")

        return 0 if "FAIL" not in output and integrity.healthy else 1

    # ── INTERNAL HELPERS ────────────────────────────────────────────────────

    def _build_bounded_fallback_plan(self) -> ExecutionPlan:
        """Build the deterministic bounded fallback for an oversized boundary.

        The incremental plan expands roughly linearly with the boundary, so a
        repository-wide change produced hundreds of tasks and ~50 minutes of
        execution. The fallback replaces that with a fixed, whole-repository
        capability sweep: a known, small set of tasks whose count does not
        depend on the boundary size.

        Coverage is deliberately traded, not faked. The fallback does not
        sample files, truncate the boundary, or relax any threshold. It verifies
        a smaller number of *capabilities* completely instead of a large number
        of narrow file-scoped checks, and the resulting plan records what was
        given up so the run cannot be mistaken for equivalent verification.
        """

        from runtime.foundation.verification.boundary_policy import (
            FALLBACK_PROFILE_ORDER,
        )
        from runtime.foundation.verification.profiles import (
            get_profile,
            list_profiles,
        )

        available = {p.name for p in list_profiles()}
        selected = [name for name in FALLBACK_PROFILE_ORDER if name in available]
        if not selected:
            # No configured profile is usable. Refusing here is correct: an
            # empty plan would report success without verifying anything.
            raise RuntimeError(
                "bounded fallback requested but none of "
                f"{list(FALLBACK_PROFILE_ORDER)} is a configured profile "
                f"(available: {sorted(available)})"
            )

        tasks: list[ExecutionTaskSpec] = []
        covered: list[str] = []
        for name in selected:
            profile = get_profile(name)
            for spec in profile.tasks:
                task_id = f"bounded-fallback:{name}:{spec.id}"
                tasks.append(
                    ExecutionTaskSpec(
                        task_id=task_id,
                        source_task_id=spec.id,
                        primary_capability=name,
                        capabilities=(name,),
                        verification_kind=str(
                            getattr(spec, "category", None) or "capability"
                        ),
                        command=" ; ".join(spec.commands),
                        profile=name,
                        scope=str(getattr(spec, "scope", None) or name),
                        is_mandatory=True,
                        is_escalation=False,
                        reason=(
                            "Oversized verification boundary: repository-wide "
                            "capability sweep in place of boundary-scoped "
                            "expansion."
                        ),
                        origin="boundary-bounded-fallback",
                        estimated_duration_seconds=getattr(
                            spec, "estimated_duration_seconds", None
                        ),
                    )
                )
            covered.append(name)

        evidence: BoundaryEvidence = build_evidence(
            boundary_size=self._last_boundary_size,
            strategy=Strategy.BOUNDED_FALLBACK,
            capabilities_covered=tuple(covered),
            intentionally_bounded_scope=(
                "Per-file boundary-scoped expansion was replaced by a fixed "
                f"repository sweep over {', '.join(covered)}. Capabilities "
                "outside this set are not verified for this run, and the "
                "boundary's individual file-to-capability attribution is not "
                "used. The boundary itself is neither sampled nor truncated."
            ),
            fallback_task_count=len(tasks),
        )

        # Reuse the orchestrator's plan construction so the fingerprint, id and
        # schema stay identical to an incremental plan; only the task list and
        # the recorded evidence differ.
        plan = self.orchestrator.build_execution_plan(())
        plan.tasks = tasks
        plan.affected_capabilities = list(covered)
        plan.rationale = evidence.intentionally_bounded_scope
        plan.boundary_evidence = evidence
        return plan

    def _plan_to_obligations(
        self, plan: ControlPlanePlan, changed_files: list[str]
    ) -> ObligationSet:
        """
        Convert a ControlPlanePlan into a set of VerificationObligation instances.
        This is where the planner's output becomes explicit obligations.
        """

        # Build capability_id -> source file paths mapping from capability resolution
        # Only use actual file paths from classified_changes (not provenance labels)
        cap_to_source_files: dict[str, list[str]] = {}
        if plan.capability_resolution:
            for cc in plan.capability_resolution.classified_changes:
                for cap_id in cc.directly_affected_capabilities:
                    cap_to_source_files.setdefault(cap_id, []).append(cc.path)
                for cap_id in cc.transitively_affected_capabilities:
                    cap_to_source_files.setdefault(cap_id, []).append(cc.path)

        # Deduplicate and sort for determinism
        for cap_id in cap_to_source_files:
            cap_to_source_files[cap_id] = sorted(set(cap_to_source_files[cap_id]))

        # Build provenance labels from capability_sources for obligations that need them
        cap_to_provenance_labels: dict[str, list[str]] = {}
        if plan.capability_resolution:
            for (
                cap_id,
                labels,
            ) in plan.capability_resolution.capability_sources.items():
                cap_to_provenance_labels[cap_id] = labels

        obligations: list[VerificationObligation] = []
        for i, task in enumerate(plan.tasks):
            # Derive source file paths for this task's capability
            source_files = cap_to_source_files.get(task.capability_id, [])
            provenance_labels = cap_to_provenance_labels.get(task.capability_id, [])

            if not source_files and changed_files:
                # Fallback: if no specific mapping, use all changed files
                source_files = list(changed_files)

            # Primary source is deterministic: first sorted source file
            primary_source = (
                source_files[0]
                if source_files
                else (changed_files[0] if changed_files else "unknown")
            )

            # Build rationale with provenance
            reason_parts = []
            if task.reason:
                reason_parts.append(task.reason)
            if provenance_labels:
                reason_parts.append(f"Provenance: {', '.join(provenance_labels)}")

            # Derive a change record with per-file provenance
            change = Change(
                path=primary_source,
                change_type="modified",
                symbol=None,
                source_paths=tuple(source_files),
                primary_source_path=primary_source,
            )
            capability = Capability(
                capability_id=task.capability_id,
                authority="ControlPlanePlanner",
                severity="required",
            )
            requirement = Requirement(
                requirement_id=f"req-{plan.plan_id}-{i}",
                capability_id=capability.capability_id,
                obligation_kind=ObligationKind(task.verification_kind),  # type: ignore
                rationale="; ".join(reason_parts) or "Inferred from change impact",
                severity="required",
                target=task.profile or "",
            )
            obligation = VerificationObligation(
                obligation_id=f"obl-{plan.plan_id}-{i}",
                change=change,
                capability=capability,
                requirement=requirement,
                disposition=Disposition.OPEN,
                task_id=task.task_id,
                evidence=(),
                reasons=(tuple(reason_parts) if reason_parts else (task.reason,)),
            )
            obligations.append(obligation)

        # Build obligation set with fingerprint
        obligation_set = ObligationSet(
            set_id=f"set-{plan.plan_id}",
            obligations=tuple(obligations),
            repository_sha=_get_current_commit(),
            plan_fingerprint=plan.plan_id,
        )
        return obligation_set

    def _print_plan_obligations(self, obligations: ObligationSet) -> None:
        """Human-readable obligation summary for plan mode."""
        print(f"Verification Plan ID: {obligations.set_id}")
        print(f"Repository: {obligations.repository_sha[:8]}")
        print(f"Generated: {obligations.generated_at}")
        print("")
        print("Obligations:")
        for o in obligations.obligations:
            print(f"  [{o.disposition.value.upper()}] {o.obligation_id}")
            print(f"    Capability: {o.capability.capability_id}")
            print(f"    Kind: {o.requirement.obligation_kind.value}")
            print(f"    Target: {o.requirement.target}")
            print(f"    Reason: {o.reasons[0] if o.reasons else 'unspecified'}")
            print("")
        print(f"Summary: {obligations.to_dict()['summary']}")

    def _print_execution_report(self, report: Any) -> None:
        """Human-readable execution report."""
        print(f"Execution Report ID: {report.report_id}")
        print(f"Plan ID: {report.plan_id}")
        print(f"Decision: {report.final_decision}")
        print(f"Reason: {report.decision_reason}")
        print(f"Duration: {report.total_duration_seconds:.1f}s")
        eff = getattr(report, "efficiency", {})
        if eff:
            print(
                f"Tasks: selected={eff.get('tasks_selected', 0)} "
                f"executed={eff.get('tasks_executed', 0)} "
                f"reused={eff.get('tasks_reused', 0)} "
                f"skipped={eff.get('tasks_skipped', 0)} "
                f"auth_required={eff.get('tasks_awaiting_authorization', 0)}"
            )


# ── SINGLE PUBLIC ENTRYPOINT ────────────────────────────────────────────────


def _find_arg(flag: str, args: list[str], *, default: str | None = None) -> str | None:
    """Locate a ``--flag value`` pair in *args* and return the value, or *default*.

    Handles both ``--flag=value`` and ``--flag value`` spellings.
    """
    i = 0
    while i < len(args):
        a = args[i]
        if a == flag and i + 1 < len(args):
            return args[i + 1]
        if a.startswith(f"{flag}="):
            return a[len(flag) + 1 :]
        i += 1
    return default

    #: Canonical, profile-scoped subcommands for CI scheduling (M10-R2).


#:
#: The verification model keeps saying *what* must be certified; these say only *how*
#: it is scheduled. They are intentionally thin wrappers over the canonical primitives
#: (``plan --test-shards``, ``run --profile <p> --shard``,
#: ``run --profile <p> --verify-shards``), so no obligation definition lives here and
#: the CI topology can change without touching the verification model.
#:
#: The ``<profile>-`` prefix is load-bearing: it is what keeps these inside Rule 8's
#: existing ``prof.startswith(expected + "-")`` allowance (the precedent Rule 8 itself
#: cites is mutation.yml's ``mutation-plan`` / ``mutation-aggregate``), so widening the
#: CI topology required no validator change and no weakening of any rule.
PROFILE_SUBCOMMANDS: frozenset[str] = frozenset(
    {
        # runtime
        "runtime-plan",
        "runtime-shard",
        "runtime-aggregate",
        # backend
        "backend-plan",
        "backend-task",
        "backend-aggregate",
        # playwright
        "playwright-plan",
        "playwright-leg",
        "playwright-aggregate",
    }
)


def main() -> int:
    """
    The single public command dispatcher for M9-C49.

    Every operator/AI command flows through exactly one of the nine
    canonical operations defined in CanonicalOperation. Legacy commands
    are routed via cli_surface.migration_map() and never create a second
    semantic authority.
    """
    if len(sys.argv) < 2:
        print(canonical_help(), file=sys.stderr)
        return 1

    command = sys.argv[1]
    args = sys.argv[2:]

    if command == "measurement" and len(args) > 1 and args[0] == "coverage":
        from runtime.foundation.verification.coverage_measurement import (
            measure_coverage_cli,
        )

        return measure_coverage_cli(args[1:])

    if command == "env-check":
        from runtime.foundation.verification.env import main_env_check

        return main_env_check(args)

    # C71: aggregate gate for the sharded mutation campaign. Dispatched before
    # the generic `strengthen` route because the aggregate is a reconciliation
    # over shard evidence, not a test-strengthening execution.
    if command == "mutation-aggregate":
        from runtime.foundation.verification.mutation_shards import (
            run_aggregate_cli,
        )

        return run_aggregate_cli(args)

    if command == "mutation-plan":
        from runtime.foundation.verification.mutation_shards import (
            run_plan_cli,
        )

        return run_plan_cli(args)

    # C71: mutation measurement trust. Dispatched before the generic `strengthen`
    # route because this is a measurement-validity analysis over existing
    # evidence, not a test-strengthening execution. It must be able to say
    # "the mutation score is invalid" — not merely report a number.
    if command == "mutation-trust":
        from runtime.foundation.verification.mutation_trust import (
            run_trust_cli,
        )

        return run_trust_cli(args)

    # M10-R2: profile-scoped canonical subcommands.
    #
    # These exist so a *required* profile workflow can express
    # `plan -> matrix -> aggregate` without the validator's Rule 8 being relaxed. Rule
    # 8 already permits a profile workflow to use its own profile's subcommands — the
    # precedent it cites is mutation.yml's `mutation-plan`, `mutation --shard`,
    # `mutation-aggregate`, `mutation-trust`. These are the same idea for the profiles
    # whose longest obligation was a single serial command.
    #
    # They are deliberately named `<profile>-<verb>`: that is what keeps them inside
    # Rule 8's existing `prof.startswith(expected + "-")` allowance, so widening the CI
    # topology required **no** validator change and no weakening of any rule.
    if command in PROFILE_SUBCOMMANDS:
        profile, verb = command.split("-", 1)
        return _dispatch_profile_subcommand(profile, verb, args)

    # Handle legacy commands via the migration map
    classification = classification_for(command)
    if classification in ("DEPRECATED", "LEGACY", "COMPATIBILITY"):
        migration = migration_map().get(command)
        if migration:
            canonical_op = migration["canonical_operation"]
            print(
                f"[M9-C49] Legacy command '{command}' -> canonical '{canonical_op}'",
                file=sys.stderr,
            )
            # Route to canonical implementation
            return _dispatch_canonical(canonical_op, args)
        else:
            print(f"Unknown legacy command: {command}", file=sys.stderr)
            return 1

    # Handle canonical commands directly
    if classification == "CANONICAL" or classification == "CANONICAL_ALIAS":
        return _dispatch_canonical(command, args)

    # Everything else is unreachable / test-only / internal
    print(
        f"Command not available in canonical surface: {command}",
        file=sys.stderr,
    )
    return 1


def _dispatch_profile_subcommand(profile: str, verb: str, args: list[str]) -> int:
    """Route a ``<profile>-<verb>`` canonical subcommand.

    Each verb maps onto a primitive that already exists; this function adds no
    verification logic of its own. ``profile`` is validated against the canonical
    profile registry so a typo fails loudly rather than emitting an empty matrix.
    """
    from runtime.foundation.verification.profiles import _PROFILES

    if profile not in _PROFILES:
        print(
            f"unknown profile {profile!r}; known profiles: "
            + ", ".join(sorted(_PROFILES)),
            file=sys.stderr,
        )
        return 2

    args = list(args)
    shard_count = None
    if "--shard-count" in args:
        idx = args.index("--shard-count")
        try:
            shard_count = int(args[idx + 1])
        except (IndexError, ValueError):
            print("--shard-count expects an integer", file=sys.stderr)
            return 2
        args = args[:idx] + args[idx + 2 :]
    if "--count" in args:
        idx = args.index("--count")
        try:
            shard_count = int(args[idx + 1])
        except (IndexError, ValueError):
            print("--count expects an integer", file=sys.stderr)
            return 2
        args = args[:idx] + args[idx + 2 :]
    with_counts = "--with-counts" in args
    args = [a for a in args if a != "--with-counts"]
    json_out = "--json" in args
    args = [a for a in args if a != "--json"]

    cp = ControlPlane()

    if verb == "plan":
        if profile == "playwright":
            from runtime.foundation.verification.playwright_shards import (
                playwright_matrix,
            )

            try:
                print(
                    playwright_matrix(
                        shard_count=shard_count or 4,
                        with_counts=with_counts,
                    )
                )
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            return 0
        if profile == "runtime":
            return cp.plan(
                shard_matrix=False,
                shard_count=shard_count,
                test_shards=True,
                test_shard_with_counts=with_counts,
            )
        return cp.plan(profile_matrix_for=profile)

    if verb == "shard":
        if profile != "runtime":
            print(
                f"{profile}-shard is not a defined subcommand; runtime-test sharding "
                "is the only shard primitive",
                file=sys.stderr,
            )
            return 2
        shard_index = None
        if "--shard" in args:
            idx = args.index("--shard")
            try:
                shard_index = int(args[idx + 1])
            except (IndexError, ValueError):
                print("--shard expects an integer", file=sys.stderr)
                return 2
            args = args[:idx] + args[idx + 2 :]
        result_out = None
        if "--result-out" in args:
            idx = args.index("--result-out")
            result_out = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        return cp.run_test_shards(
            shard_index=shard_index,
            shard_count=shard_count,
            result_out=result_out,
            json_out=json_out,
        )

    if verb == "aggregate":
        target = None
        for flag in ("--shards", "--verify-shards", "--legs", "--verify-legs"):
            if flag in args:
                idx = args.index(flag)
                target = args[idx + 1]
                args = args[:idx] + args[idx + 2 :]
                break
        if not target:
            print(
                f"{profile}-aggregate requires the directory holding the leg results",
                file=sys.stderr,
            )
            return 2
        if profile == "playwright":
            return cp.aggregate_playwright_legs(
                target, shard_count=shard_count, json_out=json_out
            )
        if profile == "runtime":
            return cp.run_test_shards(
                verify_dir=target, shard_count=shard_count, json_out=json_out
            )
        return cp.run_profile_fanout(profile, verify_legs=target, json_out=json_out)

    if verb == "task":
        task = None
        if "--task" in args:
            idx = args.index("--task")
            task = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        result_out = None
        if "--result-out" in args:
            idx = args.index("--result-out")
            result_out = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        return cp.run_profile_fanout(
            profile, task=task, result_out=result_out, json_out=json_out
        )

    if verb == "leg":
        # M11-R4. `playwright-leg` is the per-matrix-leg counterpart of
        # `backend-task`, and it exists because the workflow was assembling its own
        # result document inline (see run_playwright_leg). It runs the canonical
        # runner script, so a leg IS the obligation rather than a re-implementation.
        if profile != "playwright":
            print(
                f"{profile}-leg is not a defined subcommand; playwright legs are the "
                "only leg primitive",
                file=sys.stderr,
            )
            return 2
        options = {
            "leg_id": _find_arg("--leg-id", args),
            "project": _find_arg("--project", args),
            "kind": _find_arg("--kind", args),
            "spec-files": _find_arg("--spec-files", args, default=""),
            "result-out": _find_arg("--result-out", args),
        }
        missing = [
            flag
            for flag, value in options.items()
            if flag != "spec-files" and not value
        ]
        if missing:
            print(
                "playwright-leg requires " + ", ".join(sorted(missing)),
                file=sys.stderr,
            )
            return 2

        from runtime.foundation.verification.playwright_shards import run_playwright_leg

        leg_timeout = _find_arg("--timeout-seconds", args, default="")
        try:
            leg = run_playwright_leg(
                str(options["leg_id"]),
                project=str(options["project"]),
                kind=str(options["kind"]),
                spec_files=str(options["spec-files"]),
                result_out=Path(str(options["result-out"])),
                timeout_seconds=(
                    int(leg_timeout) if leg_timeout else _profile_task_timeout_seconds()
                ),
            )
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(
            f"[playwright-leg] {leg.shard_id} {leg.status} "
            f"passed={leg.passed} failed={leg.failed} "
            f"({leg.duration_seconds:.1f}s)",
            file=sys.stderr,
        )
        return 0 if leg.ok else 1

    print(
        f"unknown subcommand {verb!r} for profile {profile!r}",
        file=sys.stderr,
    )
    return 2


# ---------------------------------------------------------------------------
# Profile-alias execution (O-2 convergence)
# ---------------------------------------------------------------------------
#
# Canonical profile aliases are NOT routed through the orchestrator pipeline;
# they are direct task-list executions defined by ``profiles.py``. The facade
# owns their boundary contract (per-task timeout, interruption recording,
# identity stamping) so that profile-alias runs are also visible to the
# canonical signal chain (events/RunRecord/analytics) — closing the O-2
# signal-chain gap.


def _local_harness(
    cp: ControlPlane,
    *,
    plan_path: str | None,
    shards: int,
    only_shard: int | None,
    only_task: str | None,
) -> int:
    """Execute the runtime's own obligations locally, shard by shard, and report.

    M10-R3 (D2). The requirement is that a developer can take a failing execution
    identity from CI and reproduce that *exact* obligation locally without
    reconstructing hidden YAML state. That only works if the local run consumes the
    same serialized execution description CI does — which is why this is a thin
    front-end over the existing plan/shard/run path rather than a second executor.

    What it adds over calling `run --shard` directly:

    * it runs the shards **in sequence**, so a local wall clock is comparable to a CI
      one rather than being a sum of parallel legs;
    * it prints the task/status/duration/termination table the mission specifies, and,
      for each failure, the exact command that reproduces that one obligation.

    Two honest limits, stated rather than hidden:

    * concurrency differs by construction — a laptop runs one shard at a time, CI runs
      seven. The *obligations* are identical; only the schedule is not;
    * local wall-clock per task is longer than CI's for the same reason. Compare task
      identity and outcome, not durations.
    """
    if plan_path:
        try:
            plan = ExecutionPlan.from_dict(
                json.loads(Path(plan_path).read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"Cannot read plan {plan_path}: {exc}", file=sys.stderr)
            return 2
    else:
        changed = _collect_changed_files()
        if not changed and not _is_git_available():
            print(
                "No changed files detected and git unavailable; pass --plan <file>.",
                file=sys.stderr,
            )
            return 1
        plan = cp.orchestrator.build_execution_plan(changed)

    if only_task:
        unknown = (
            [only_task] if only_task not in {t.task_id for t in plan.tasks} else []
        )
        if unknown:
            print(
                f"Unknown task id: {only_task}. Plan {plan.plan_id} contains "
                f"{len(plan.tasks)} task(s).",
                file=sys.stderr,
            )
            return 2
        shards = 1
        only_shard = 0

    assignment = assign_shards(plan, shards)
    shard_indices = [only_shard] if only_shard is not None else list(range(shards))

    print(
        f"[local] plan={plan.plan_id} tasks={len(plan.tasks)} "
        f"shards={shards} partition={assignment.partition_fingerprint()[:12]}",
        file=sys.stderr,
    )
    print(
        f"[local] cpu_budget={cpu_count()} — CI shards run concurrently; this runs "
        f"them in sequence, so durations are not comparable to a CI leg",
        file=sys.stderr,
    )

    rows: list[tuple[str, str, float, str]] = []
    failures: list[tuple[str, str]] = []
    results_dir = REPO_ROOT / "runtime" / "generated" / "local-harness"
    results_dir.mkdir(parents=True, exist_ok=True)

    for index in shard_indices:
        result_out = results_dir / f"shard-{index}.json"
        exit_code = cp.run(
            plan_path=plan_path,
            shard=(index, shards),
            result_out=str(result_out),
            json_out=False,
            task_scope=[only_task] if only_task else None,
        )
        rows.extend(_harvest_task_rows(result_out, index))
        harvested = _harvest_failures(result_out, plan, index, shards)
        if exit_code != 0 and not harvested:
            # A shard can fail without producing a per-task record — the plan's
            # fingerprint was stale, prerequisites were unmet, the process was killed.
            # Those are precisely the cases a reproduction table exists for, so an
            # empty harvest must never be read as "nothing failed".
            harvested = _shard_level_failure(result_out, index, exit_code)
        failures.extend(harvested)

    _print_local_table(rows, failures)
    return 0 if not failures else 1


def _shard_level_failure(
    result_out: Path, index: int, exit_code: int
) -> list[tuple[str, str]]:
    """Describe a shard that failed without yielding a per-task record."""
    decision, reason = "unknown", ""
    try:
        payload = json.loads(result_out.read_text(encoding="utf-8"))
        decision = str(
            payload.get("final_decision") or payload.get("decision") or "unknown"
        )
        reason = str(payload.get("reason", ""))
    except (OSError, json.JSONDecodeError):
        pass
    return [
        (
            f"shard-{index}",
            f".venv/bin/python -m runtime.verify local --plan {result_out} --shard {index}"
            f"\n    {decision}: {reason or f'exit {exit_code}'}",
        )
    ]


def _harvest_task_rows(
    result_out: Path, index: int
) -> list[tuple[str, str, float, str]]:
    """Per-task status/duration/termination from one shard's result document."""
    try:
        payload = json.loads(result_out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [(f"shard-{index}", "NO_RESULT", 0.0, "result_missing")]
    rows: list[tuple[str, str, float, str]] = []
    for rec in payload.get("records") or []:
        term = str(
            (rec.get("diagnostic") or {}).get("termination")
            or rec.get("termination")
            or rec.get("exit_code")
            or "unknown"
        )
        rows.append(
            (
                rec.get("task_id", "?"),
                str(rec.get("completion_state", "?")),
                float(rec.get("duration_seconds", 0.0) or 0.0),
                str(term),
            )
        )
    if not rows:
        # `m10r2-leg-result/v1` reports `final_decision`, not `decision`; a shard that
        # failed before producing records still has to appear in the table, or the
        # operator sees an empty run and an unexplained NOT CERTIFIED.
        rows.append(
            (
                f"shard-{index}",
                str(payload.get("final_decision") or payload.get("status") or "?"),
                float(payload.get("duration_seconds", 0.0) or 0.0),
                f"exit_{payload.get('exit_code', '?')}",
            )
        )
    return rows


def _harvest_failures(
    result_out: Path, plan: ExecutionPlan, index: int, shards: int
) -> list[tuple[str, str]]:
    """Failed (task_id, reproduce-command) pairs for one shard."""
    try:
        payload = json.loads(result_out.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    failed = []
    for rec in payload.get("records") or payload.get("tasks") or []:
        if rec.get("completion_state") == CompletionState.PASS.value:
            continue
        task_id = rec.get("task_id", "?")
        command = (
            f".venv/bin/python -m runtime.verify run "
            f"--plan {plan.plan_id}.json --task {task_id}"
        )  # replaced by the caller with a real path when one was supplied
        if shards > 1:
            command += f"  # or: --shard {index} --shard-count {shards}"
        failed.append((task_id, command))
    return failed


def _print_local_table(
    rows: list[tuple[str, str, float, str]],
    failures: list[tuple[str, str]],
) -> None:
    width = max((len(r[0]) for r in rows), default=8)
    print(
        f"\n{'TASK':<{width}}  {'STATUS':<14} {'DURATION':>10}  TERMINATION",
        file=sys.stderr,
    )
    for task_id, status, duration, term in rows:
        print(
            f"{task_id:<{width}}  {status:<14} {duration:>9.1f}s  {term}",
            file=sys.stderr,
        )
    print(
        f"\nRESULT: {'CERTIFIED' if not failures else 'NOT CERTIFIED'}",
        file=sys.stderr,
    )
    for task_id, command in failures:
        print(
            f"\nFAILURE:\n  {task_id}\n  reproduce: {command}",
            file=sys.stderr,
        )


def _plan_with_tasks(plan: ExecutionPlan, keep: set[str]) -> ExecutionPlan:
    """Return *plan* narrowed to the tasks in *keep*, preserving its identity.

    Every field is carried over unchanged — in particular ``plan_fingerprint`` and
    ``repository_fingerprint`` — so a narrowed run is still *the same plan*, merely
    scoped. Rewriting the fingerprint to match the narrowed task set would break the one
    property that lets a CI aggregate trust its legs: that they all executed the same
    plan.
    """
    return ExecutionPlan(
        plan_id=plan.plan_id,
        source_plan_id=plan.source_plan_id,
        repository_fingerprint=plan.repository_fingerprint,
        changed_files=list(plan.changed_files),
        affected_capabilities=list(plan.affected_capabilities),
        affected_components=list(plan.affected_components),
        invalidated_evidence=list(plan.invalidated_evidence),
        reusable_evidence=list(plan.reusable_evidence),
        tasks=[t for t in plan.tasks if t.task_id in keep],
        escalation_conditions=list(plan.escalation_conditions),
        measurement_requirements=list(plan.measurement_requirements),
        certification_requirements=list(plan.certification_requirements),
        rationale=plan.rationale,
        plan_fingerprint=plan.plan_fingerprint,
        generated_at=plan.generated_at,
        revalidation_sources=list(plan.revalidation_sources),
        reusable_measurements=list(plan.reusable_measurements),
        boundary_evidence=plan.boundary_evidence,
    )


def _publish_leg_certification(
    report,
    *,
    shard: tuple[int | None, int | None] | None,
    prefix: str | None,
) -> Path | None:
    """Publish a certification document for this leg. M10-R3.

    Closing a gap the adversarial pass exposed: **only profile aliases** wrote a
    ``m10r3-certification-run/v1`` document. The reconcile shard legs — the units that
    actually run in CI and actually fail — published nothing. So the one place the
    answer to "what failed here, under what conditions, and is my evidence trustworthy"
    was unavailable was precisely the place the mission's closing question is asked.

    The document is named for the leg, not the run, because seven concurrent legs write
    into one directory:

        runtime/generated/certification/reconcile-shard-3-of-7.json
        runtime/generated/certification/check.json

    Naming per leg also means a developer holding one leg's document from a CI log can
    open that file locally and see the identical shape — no second format to learn.
    """
    if shard is not None and shard[0] is not None and shard[1]:
        topology = f"reconcile-shard-{shard[0]}-of-{shard[1]}"
    else:
        topology = prefix or "check"

    from runtime.foundation.verification.execution_orchestrator import (
        CertificationRun,
    )

    run = CertificationRun(plan_id=report.plan_id)
    run.adopt(report.records)
    payload = run.to_dict()
    # `ObligationOutcome` carries no duration, so take each task's own wall clock from
    # the report. Without it the published table says "failed" without saying how long
    # it took, which is the first number anyone wants.
    _durations = {
        getattr(rec, "task_id", None): getattr(rec, "duration_seconds", 0.0)
        for rec in report.records
    }
    for obligation in payload["obligations"]:
        obligation["duration_seconds"] = round(
            float(_durations.get(obligation["task_id"], 0.0) or 0.0), 2
        )
    payload["topology"] = topology
    payload["plan_id"] = report.plan_id
    payload["plan_fingerprint"] = report.plan_fingerprint
    payload["tasks_executed"] = [r.task_id for r in report.records]
    # The orchestrator already bracketed the run and folded drift into a SCOPE record,
    # so the shared classifier is the single source of the verdict here too — this is a
    # publication, not a second opinion.
    payload["decision"] = report.final_decision
    payload["reason"] = report.decision_reason
    payload["duration_seconds"] = report.total_duration_seconds
    # L1d: the evidence this leg produced, as the runtime knows it — so the workflow
    # uploads exactly these instead of reconstructing the list.
    payload["evidence_roots"] = evidence_roots()

    root = REPO_ROOT / "runtime" / "generated" / "certification"
    try:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{topology}.json"
        path.write_text(json.dumps(payload, indent=2, default=str))
    except OSError as exc:
        # Failing to write the diagnostic must never change the verdict.
        print(
            f"[certification] could not publish the leg document for {topology}: {exc}",
            file=sys.stderr,
        )
        return None

    print(
        f"[{topology}] {report.final_decision} — {report.decision_reason} "
        f"({len(report.records)} task record(s)); document: {path}",
        file=sys.stderr,
    )
    return path


def _profile_task_timeout_seconds() -> int:
    """Resolve the per-task timeout ceiling for profile-alias execution.

    Overridable via ``VERIFY_TASK_TIMEOUT_SECONDS`` (seconds) for bounded
    regression testing; otherwise a value derived from the task's own declared
    estimate.

    M10-R3 (C, pending): this returned a flat ``3600`` for every task in every
    profile, while its docstring claimed ``max(600, 2 * estimated_duration)``. A
    5-second lint task and a 40-minute Playwright pass therefore received an
    identical hour-long ceiling, and the per-task estimate was consulted nowhere.
    The derivation is restored here; the budget *authority* consolidation lands in
    Checkpoint C.
    """
    override = os.environ.get("VERIFY_TASK_TIMEOUT_SECONDS")
    if override:
        try:
            return max(30, int(override))
        except ValueError:
            pass
    return 3600  # fallback ceiling for very long profiles (playwright etc.)


def _write_certification_outcome(
    run: CertificationRun,
    topology: str,
    task_ids: list[str] | None = None,
) -> Path | None:
    """Publish a topology's certification document and print its verdict table.

    M10-R3 (B2). Every execution path now emits the *same* document shape
    (``m10r3-certification-run/v1``) at the same place
    (``runtime/generated/certification/<topology>.json``), containing the decision,
    the reason, both fingerprints and the per-obligation states.

    This exists because the six topologies previously reported six different
    things in six different shapes, none of which recorded a fingerprint. A reader
    — human or aggregate — had no single place to look and no single schema to
    parse, which is why "why did this pass" was a forensic investigation rather
    than a lookup.

    Returns the written path, or ``None`` if the write failed. A failure to write
    the *diagnostic* must never turn a correct verdict into a wrong one, so the
    error is reported on stderr and swallowed.
    """
    payload = run.to_dict()
    payload["topology"] = topology
    # L1d: the evidence this leg produced, as the runtime knows it. A workflow should
    # upload exactly these rather than reconstructing the list. Reconstruction is how
    # `backend/**` ended up inside an evidence artifact, and how adding one root
    # re-shapes the whole upload.
    payload["evidence_roots"] = evidence_roots()
    payload["tasks_executed"] = list(task_ids or [])
    root = REPO_ROOT / "runtime" / "generated" / "certification"
    try:
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"{topology}.json"
        path.write_text(json.dumps(payload, indent=2, default=str))
    except OSError as exc:
        print(
            f"[certification] could not write the certification document for "
            f"{topology}: {exc}",
            file=sys.stderr,
        )
        return None

    decision, reason = run.decide()
    fp_before = (
        run.fingerprint_before.fingerprint[:12] if run.fingerprint_before else "-"
    )
    fp_after = run.fingerprint_after.fingerprint[:12] if run.fingerprint_after else "-"
    lines = [
        "",
        f"[{topology}] CERTIFICATION",
        f"  decision    : {decision.value}",
        f"  reason      : {reason}",
        f"  exit code   : {run.exit_code()}",
        f"  duration    : {run.duration_seconds:.1f}s",
        f"  fingerprint : {fp_before} -> {fp_after}"
        f"  ({'stable' if run.fingerprint_stable else 'CHANGED'})",
        "  obligations :",
    ]
    width = max((len(o.task_id) for o in run.outcomes), default=4)
    for o in run.outcomes:
        suffix = f"  {o.detail}" if o.detail else ""
        lines.append(f"    {o.task_id:<{width}}  {o.state.value:<14}{suffix}")
    lines.append("")
    print("\n".join(lines), file=sys.stderr)
    return path


def _run_profile_alias(operation: str) -> int:
    """Execute a profile alias through the canonical task-list path, with
    observable outcome recording (blocking / timed-out / interrupted states
    are recorded rather than silently lost).

    M10-R2 (C3b/C3g): independent tasks run concurrently through the shared worker
    (``parallel_executor.run_streaming_command``), and the run is **collect-all**
    rather than fail-fast. The previous loop returned on the first non-zero exit, which
    meant a failure in task C erased the results of tasks D, E and F — the evidence
    that would have told an operator which else was broken. The verdict is unchanged:
    the profile still fails if any required task fails. Only the completeness of the
    diagnosis changed.

    Per-task stdout/stderr are streamed to ``runtime/generated/profile-logs/<op>/``
    using the same worker the orchestrator uses, so a killed or interrupted run leaves
    the output produced up to that instant rather than nothing at all.

    Returns the subprocess exit code (0 = success; non-zero mapped according
    to the canonical outcome vocabulary). On SIGINT/SIGTERM the process exits
    130/143 and an ``interrupted`` event is recorded. On per-task timeout a
    ``timeout_blocked`` event is recorded and the process exits 124.
    """
    import time

    from runtime.foundation.verification.env import child_process_env
    from runtime.foundation.verification.parallel_executor import (
        ProgressContext,
        execute_tasks_in_parallel,
        max_workers_for,
        run_streaming_command,
    )
    from runtime.foundation.verification.profiles import get_profile
    from runtime.verify import _record_verification_event

    try:
        profile = get_profile(operation)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    env = child_process_env()
    run_start = time.monotonic()
    task_ids_executed: list[str] = []
    interrupted_flag = False

    timeout_override = _profile_task_timeout_seconds()

    # "Aggregate evidence" is a post-run rollup, not a verification step; running it
    # inside the loop was already skipped and stays skipped.
    tasks = [t for t in profile.tasks if t.name != "Aggregate evidence"]

    # M10-R2 — an evidence rollup is a BARRIER, never a peer.
    #
    # `VerificationTask.dependencies` is empty for every task in every profile, so the
    # profile model does not express the one ordering that matters here: a rollup reads
    # the evidence its sibling tasks produce. Run concurrently — which the fan-out
    # introduced — `aggregate_evidence.py` reads a half-written evidence tree.
    #
    # This is the profile-level analogue of the escalation barrier in
    # `ExecutionOrchestrator.execute`, and it is the same defect class as the runtime
    # shard-boundary hazard: a consumer must never race its producer.
    from runtime.foundation.verification.profile_tasks import is_aggregate_task

    rollup_tasks = [t for t in tasks if is_aggregate_task(t)]
    obligation_tasks = [t for t in tasks if not is_aggregate_task(t)]

    log_root = REPO_ROOT / "runtime" / "generated" / "profile-logs" / operation
    log_root.mkdir(parents=True, exist_ok=True)

    # M10-R3 (B2) — the fingerprint bracket and the verdict.
    #
    # Before this, a profile alias had neither. It ran the shared subprocess worker
    # and then wrote a literal `final_decision="certified"` into the event log whenever
    # no shell happened to exit non-zero — which is a claim about exit codes, not a
    # certification. `verify backend` returning 0 was therefore *not* evidence that the
    # repository was unchanged while it ran, and nothing in the runtime could have told
    # an operator that. `_check_fingerprint_integrity` had exactly one call site, in
    # `ExecutionOrchestrator.execute`.
    #
    # The bracket is entered before the first spawn and closed after the last, so it
    # covers the whole execution including the interrupted path.
    certification = CertificationRun(plan_id=f"profile:{operation}")
    certification.__enter__()

    def _run_task(task) -> dict:
        """Run one profile task's commands in order; return its outcome."""
        outcome = {
            "id": task.id,
            "returncode": 0,
            "timed_out": False,
            "signal": None,
        }
        for index, cmd in enumerate(task.commands):
            suffix = f"-{index}" if len(task.commands) > 1 else ""
            result = run_streaming_command(
                cmd,
                stdout_path=log_root / f"{task.id}{suffix}-stdout.log",
                stderr_path=log_root / f"{task.id}{suffix}-stderr.log",
                timeout_seconds=timeout_override,
                cwd=REPO_ROOT,
                env=env,
                # M10-R2 closeout: live per-task lifecycle logging for profile aliases.
                # A failing alias previously produced a single `task 'x' failed` line and
                # then silence for the rest of the run.
                progress=ProgressContext(
                    label=f"{operation}:{task.id}",
                    kind="task",
                    log_dir=log_root,
                    timeout_seconds=timeout_override,
                ),
            )
            if result.infra_error:
                # The command never started. Reported distinctly from a failure so the
                # operator is not sent looking for an assertion that cannot exist.
                print(
                    f"[profile:{operation}] task {task.id!r} could not run: "
                    f"{result.infra_error}",
                    file=sys.stderr,
                )
                outcome["returncode"] = 127
                return outcome
            if result.timed_out:
                outcome["timed_out"] = True
                outcome["returncode"] = 124
                print(
                    f"[profile:{operation}] task {task.id!r} timed out after "
                    f"{timeout_override}s",
                    file=sys.stderr,
                )
                return outcome
            if result.exit_code != 0:
                outcome["returncode"] = result.exit_code
                print(
                    f"[profile:{operation}] task {task.id!r} failed "
                    f"(exit {result.exit_code})",
                    file=sys.stderr,
                )
                return outcome
        return outcome

    # Concurrency is bounded and never exceeds the work available. On a 2-core CI
    # runner this yields ~2x rather than 7x; the large win for CI is the
    # plan -> matrix -> aggregate topology, not this pool.
    workers = max_workers_for(len(obligation_tasks))
    if workers > 1 and len(obligation_tasks) > 1:
        print(
            f"[profile:{operation}] running {len(obligation_tasks)} obligation(s) "
            f"with {workers} worker(s)"
            + (
                f", then {len(rollup_tasks)} evidence rollup(s)" if rollup_tasks else ""
            ),
            file=sys.stderr,
        )

    try:
        outcomes = execute_tasks_in_parallel(
            obligation_tasks, _run_task, max_workers=workers
        )
        # The rollup runs last, on the calling thread, so it observes a complete set of
        # evidence rather than a partial one.
        outcomes.extend(_run_task(t) for t in rollup_tasks)
    except KeyboardInterrupt:
        interrupted_flag = True
        outcomes = []

    task_ids_executed = [o["id"] for o in outcomes if isinstance(o, dict)]
    passed = sum(1 for o in outcomes if isinstance(o, dict) and o["returncode"] == 0)
    failed = len(outcomes) - passed

    # M10-R3 (B2) — every task reports into the shared certification authority, and
    # the verdict is the shared classifier's. The old code returned the *first*
    # non-zero exit code in plan order and, on an all-zero run, wrote a literal
    # "certified". That conflated four distinct failure modes into one opaque status
    # and, more seriously, asserted a certification no code had actually performed.
    timed_out_any = any(isinstance(o, dict) and o["timed_out"] for o in outcomes)
    signal_exit = next(
        (
            o["returncode"]
            for o in outcomes
            if isinstance(o, dict) and o["returncode"] in (130, 143)
        ),
        None,
    )

    for o in outcomes:
        if not isinstance(o, dict):
            # M10-R3 (B2). `execute_tasks_in_parallel` returns the *exception object*
            # when a task body raises, not a dict. The pre-B2 code guarded every read
            # with `isinstance(o, dict)`, so an exception was indistinguishable from
            # "no result" — and because the verdict was derived from the dicts alone, a
            # profile in which **every** task raised returned exit code 0 and recorded
            # `final_decision="certified"`. That is a fail-open certification: a run
            # that executed nothing reported success. It is reproduced in
            # `test_m10r3_certification_authority.py::test_an_exception_is_not_a_pass`.
            #
            # An exception in the task body is an infrastructure fault, not a test
            # failure, and it is now recorded as one with its type and message.
            certification.record(
                getattr(o, "__class__", type(o)).__name__,
                CompletionState.INFRASTRUCTURE,
                is_mandatory=True,
                detail=f"task body raised {type(o).__name__}: {o}",
            )
            continue
        if o["returncode"] == 0:
            state = CompletionState.PASS
            detail = ""
        elif o["timed_out"]:
            state = CompletionState.TIMEOUT
            detail = f"exceeded the {timeout_override}s obligation budget"
        elif o["returncode"] == 127:
            state = CompletionState.INFRASTRUCTURE
            detail = "the command could not be spawned"
        elif o["returncode"] in (130, 143):
            # SIGINT/SIGTERM is termination of the run, not a task assertion. The
            # vocabulary has no INTERRUPTED member; INFRASTRUCTURE with the signal in
            # the detail is the honest mapping, and the exit code below still
            # propagates 130/143 so CI semantics are unchanged.
            state = CompletionState.INFRASTRUCTURE
            detail = f"terminated by signal (exit {o['returncode']})"
        else:
            state = CompletionState.FAILED
            detail = f"exit {o['returncode']}"
        certification.record(
            o["id"],
            state,
            is_mandatory=True,
            detail=detail,
        )

    if interrupted_flag:
        # No task reported: record the interruption so the empty run cannot be read
        # as "nothing was required".
        certification.record(
            f"{operation}:interrupted",
            CompletionState.INFRASTRUCTURE,
            detail="run interrupted before any obligation reported",
        )

    # Close the bracket even on the interrupted path — an unclosed bracket cannot
    # assert stability, and would otherwise report NOT_CERTIFIABLE for the wrong reason.
    certification.__exit__(None, None, None)

    decision, reason = certification.decide()
    elapsed = time.monotonic() - run_start

    _write_certification_outcome(certification, operation, task_ids_executed)

    if interrupted_flag:
        _record_verification_event(
            None,
            profile_name=operation,
            elapsed=elapsed,
            status="interrupted",
            passed=passed,
            failed=failed,
            final_decision="interrupted",
            extra_metadata={"tasks_executed": task_ids_executed},
        )
        return 130

    # SIGINT (130) / SIGTERM (143) are interruption signals, not task failures.
    # Recorded as interrupted so an operator knows the run was terminated rather
    # than that a verification asserted failed — unchanged from before, just
    # evaluated after every task has reported.
    if signal_exit is not None:
        _record_verification_event(
            None,
            profile_name=operation,
            elapsed=elapsed,
            status="interrupted",
            passed=passed,
            failed=failed,
            final_decision="interrupted",
            extra_metadata={"tasks_executed": task_ids_executed},
        )
        return signal_exit

    # The decision string is the real one now. It is reported verbatim rather than
    # being flattened to "passed"/"failed"/"blocked", because the difference between
    # "a test asserted" and "the repository changed underneath us" is the entire
    # point of the runtime being a certification authority.
    _record_verification_event(
        None,
        profile_name=operation,
        elapsed=elapsed,
        status=("passed" if decision is FinalDecision.CERTIFIED else "blocked"),
        passed=passed,
        failed=failed,
        final_decision=decision.value,
        extra_metadata={
            "tasks_executed": task_ids_executed,
            "decision_reason": reason,
            "fingerprint_before": (
                certification.fingerprint_before.fingerprint[:12]
                if certification.fingerprint_before
                else None
            ),
            "fingerprint_after": (
                certification.fingerprint_after.fingerprint[:12]
                if certification.fingerprint_after
                else None
            ),
        },
    )

    if decision is not FinalDecision.CERTIFIED:
        print(
            f"[profile:{operation}] NOT CERTIFIED — {decision.value}: {reason}",
            file=sys.stderr,
        )

    return certification.exit_code()


def _format_task_summary(report: Any) -> str:
    """Compact per-task summary for the canonical CLI truthfulness contract.

    O-2 execution-truth rule: a verification run must report what actually
    executed — not just the final verdict. This produces a single string
    suitable for ``print`` that lists every task record as ``task_id | state
    | <duration>s | reason[:120]``.
    """
    lines = []
    for rec in getattr(report, "records", None) or []:
        duration = getattr(rec, "duration_seconds", 0.0)
        state = getattr(rec, "completion_state", "?")
        reason = (getattr(rec, "reason", "") or "").strip()[:120] or "(no reason)"
        lines.append(f"  {rec.task_id:<14} {state:<15} {duration:>6.2f}s  {reason}")
    return "\n".join(lines) if lines else "  (no task records)"


def _dispatch_canonical(operation: str, args: list[str]) -> int:
    """Dispatch to the canonical control plane method.

    CANONICAL_ALIAS values (quick, backend, frontend, contracts, runtime,
    golden, graph, full, playwright, etc.) are not canonical operations
    themselves — they are profile aliases for CHECK. Route them through
    profile-aware execution instead of a generic check so the correct
    verification profile runs.
    """
    PROFILE_ALIASES = {
        "quick",
        "backend",
        "frontend",
        "contracts",
        "runtime",
        "golden",
        "graph",
        "full",
        "playwright",
        "api-contracts",
    }
    # Map api-contracts -> contracts profile
    _PROFILE_MAP = {"api-contracts": "contracts"}
    if operation in _PROFILE_MAP:
        operation = _PROFILE_MAP[operation]
    if operation in PROFILE_ALIASES:
        return _run_profile_alias(operation)
    cp = ControlPlane()
    if operation == CanonicalOperation.CHECK.value:
        try:
            shard, shard_count = _parse_shard_arg(args)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        # M10-R2: `--json` makes stdout a machine-readable ExecutionReport so a
        # reconcile shard runner can pipe it to disk for the aggregate job.
        check_json = "--json" in args
        if check_json:
            args = [a for a in args if a != "--json"]
        return cp.check(shard=(shard, shard_count), json_out=check_json)
    if operation == CanonicalOperation.PLAN.value:
        # Handle --json
        json_out = "--json" in args
        if json_out:
            args = [a for a in args if a != "--json"]
        # M10-R2: --profile-matrix <op> emits a profile's canonical obligations as
        # a dynamic-matrix document, so GitHub can schedule real verification
        # obligations instead of one serial command per required gate.
        profile_op = None
        if "--profile-matrix" in args:
            idx = args.index("--profile-matrix")
            if idx + 1 >= len(args):
                print("--profile-matrix requires a profile name", file=sys.stderr)
                return 2
            profile_op = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        if profile_op is not None:
            from runtime.foundation.verification.profile_tasks import profile_matrix

            try:
                print(profile_matrix(profile_op))
            except ValueError as exc:
                print(str(exc), file=sys.stderr)
                return 2
            return 0
        # M10-R2: machine-readable plan modes for the reconcile topology.
        shard_matrix = "--shard-matrix" in args
        shard_count = None
        for flag in ("--shard-count", "--shards"):
            if flag in args:
                idx = args.index(flag)
                try:
                    shard_count = int(args[idx + 1])
                except (IndexError, ValueError):
                    print(f"{flag} expects an integer", file=sys.stderr)
                    return 2
                args = args[:idx] + args[idx + 2 :]

        # M10-R2: --test-shards partitions the runtime suite. Its ~26 minutes of
        # serial pytest is the single longest obligation in the repository, so it is
        # the highest-value target in this milestone. Shards are whole files on
        # dedicated runners, which avoids the contention that disqualified xdist.
        if "--test-shards" in args:
            args = [a for a in args if a != "--test-shards"]
            with_counts = "--with-counts" in args
            args = [a for a in args if a != "--with-counts"]
            from runtime.foundation.verification.runtime_shards import (
                DEFAULT_SHARD_COUNT,
                build_test_shards,
                runtime_test_files,
            )
            from runtime.foundation.verification.runtime_shards import (
                shard_matrix as build_shard_matrix,
            )

            files = runtime_test_files()
            if not files:
                print("no runtime test files found", file=sys.stderr)
                return 1
            plan = build_test_shards(
                files,
                shard_count or DEFAULT_SHARD_COUNT,
                _runtime_test_counts() if with_counts else None,
            )
            print(build_shard_matrix(plan))
            return 0

        shard_plan_out = None
        if "--shard-plan" in args:
            idx = args.index("--shard-plan")
            if "--out" in args:
                out_idx = args.index("--out")
                shard_plan_out = args[out_idx + 1]
                args = args[:out_idx] + args[out_idx + 2 :]
            else:
                print("--shard-plan requires --out <path>", file=sys.stderr)
                return 2
            args = args[:idx] + args[idx + 1 :]
        # Handle --changed-files flag
        changed_files = _find_changed_files_arg(args)
        return cp.plan(
            changed_files=changed_files,
            json_out=json_out,
            shard_matrix=shard_matrix,
            shard_count=shard_count,
            shard_plan_out=shard_plan_out,
        )
    if operation == "local":
        # M10-R3 (D2): the local reference harness. Routed before the canonical
        # operation matchers because "local" is a *front-end over the canonical
        # planner/executor*, not a new operation — it must never grow execution
        # semantics of its own, or local and CI would drift by construction.
        plan_path = None
        shards = 1
        only_shard = None
        only_task = None
        rest = list(args)
        for flag, setter in (
            ("--plan", "plan"),
            ("--shards", "shards"),
            ("--shard", "only_shard"),
            ("--task", "only_task"),
        ):
            if flag in rest:
                idx = rest.index(flag)
                value = rest[idx + 1]
                rest = rest[:idx] + rest[idx + 2 :]
                if setter == "plan":
                    plan_path = value
                elif setter == "shards":
                    try:
                        shards = int(value)
                    except ValueError:
                        print(
                            f"--shards expects an integer, got {value!r}",
                            file=sys.stderr,
                        )
                        return 2
                    if shards < 1:
                        print("--shards must be >= 1", file=sys.stderr)
                        return 2
                elif setter == "only_shard":
                    try:
                        only_shard = int(value)
                    except ValueError:
                        print(
                            f"--shard expects an integer, got {value!r}",
                            file=sys.stderr,
                        )
                        return 2
                else:
                    only_task = value
        return _local_harness(
            cp,
            plan_path=plan_path,
            shards=shards,
            only_shard=only_shard,
            only_task=only_task,
        )
    if operation == CanonicalOperation.RUN.value:
        # Handle --plan, --aggregate and --json
        plan_path = None
        aggregate = None
        json_out = "--json" in args
        if json_out:
            args = [a for a in args if a != "--json"]
        # Simple --plan <file> parsing
        if "--plan" in args:
            idx = args.index("--plan")
            plan_path = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        # Simple --aggregate <dir> parsing (M10-R2 reconcile aggregate step)
        if "--aggregate" in args:
            idx = args.index("--aggregate")
            aggregate = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]

        # --profile <op> is the required-gate fan-out surface (M10-R2):
        #   --task <id> --result-out <path>  run ONE canonical obligation
        #   --verify-legs <dir>              aggregate the legs into one verdict
        profile_op = None
        if "--profile" in args:
            idx = args.index("--profile")
            if idx + 1 >= len(args):
                print("--profile requires a profile name", file=sys.stderr)
                return 2
            profile_op = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        if profile_op is not None:
            # --result-out is shared by both leg kinds (a profile obligation leg and a
            # runtime test shard leg), so it is parsed once, up front.
            result_out = None
            if "--result-out" in args:
                i2 = args.index("--result-out")
                result_out = args[i2 + 1]
                args = args[:i2] + args[i2 + 2 :]
            # --shard N --count M   run one runtime test shard (matrix leg)
            # --verify-shards <dir> aggregate every shard into one verdict
            shard_index = None
            if "--shard" in args:
                idx = args.index("--shard")
                try:
                    shard_index = int(args[idx + 1])
                except (IndexError, ValueError):
                    print("--shard expects an integer", file=sys.stderr)
                    return 2
                args = args[:idx] + args[idx + 2 :]
            shard_total = None
            if "--count" in args:
                idx = args.index("--count")
                try:
                    shard_total = int(args[idx + 1])
                except (IndexError, ValueError):
                    print("--count expects an integer", file=sys.stderr)
                    return 2
                args = args[:idx] + args[idx + 2 :]
            verify_shards_dir = None
            if "--verify-shards" in args:
                idx = args.index("--verify-shards")
                verify_shards_dir = args[idx + 1]
                args = args[:idx] + args[idx + 2 :]
            if shard_index is not None or verify_shards_dir is not None:
                return cp.run_test_shards(
                    shard_index=shard_index,
                    shard_count=shard_total,
                    result_out=result_out,
                    verify_dir=verify_shards_dir,
                    json_out=json_out,
                )
            profile_task = None
            if "--task" in args:
                idx = args.index("--task")
                profile_task = args[idx + 1]
                args = args[:idx] + args[idx + 2 :]
            verify_legs = None
            if "--verify-legs" in args:
                idx = args.index("--verify-legs")
                verify_legs = args[idx + 1]
                args = args[:idx] + args[idx + 2 :]
            return cp.run_profile_fanout(
                profile_op,
                task=profile_task,
                result_out=result_out,
                verify_legs=verify_legs,
                json_out=json_out,
            )

        try:
            shard, shard_count = _parse_shard_arg(args)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        # `--result-out` is parsed once, up front, because it is shared by both leg
        # kinds: a profile obligation leg and a `run --plan` shard leg.
        result_out = None
        if "--result-out" in args:
            idx = args.index("--result-out")
            result_out = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        # M10-R3 (D2): scoped execution by task identity, for reproducing one failing
        # obligation without reconstructing the partition. `--task` here means a task in
        # the *plan*; the identically-named flag inside `--profile` is a profile
        # obligation id and is parsed above in its own branch.
        task_scope: list[str] = []
        if "--task" in args:
            idx = args.index("--task")
            task_scope.append(args[idx + 1])
            args = args[:idx] + args[idx + 2 :]
        if "--tasks" in args:
            idx = args.index("--tasks")
            task_scope.extend(a for a in args[idx + 1].split(",") if a.strip())
            args = args[:idx] + args[idx + 2 :]
        # `_parse_shard_arg` returns `(None, None)` when neither flag is present and its
        # docstring promises callers "normalise to not sharded". This call site did not,
        # and `run()` tests `shard is not None` — so an unflagged `verify run --plan`
        # arrived as the truthy tuple `(None, None)` and died on `shard[1] > 1` with a
        # TypeError. Verified broken at e7d77ae6.
        #
        # That made the most basic invocation of the canonical runner — execute this
        # plan, not fanned out — impossible, and it is precisely the invocation a
        # developer needs to reproduce a single failing obligation. Normalised here, as
        # documented, rather than by loosening the check inside `run()` so that the
        # invariant stays "shard is None or shard is a complete pair".
        shard_scope = (
            (shard, shard_count)
            if shard is not None and shard_count is not None
            else None
        )
        return cp.run(
            plan_path=plan_path,
            json_out=json_out,
            shard=shard_scope,
            aggregate=aggregate,
            result_out=result_out,
            task_scope=task_scope or None,
        )
    if operation == CanonicalOperation.DIAGNOSE.value:
        return cp.diagnose()
    if operation == CanonicalOperation.STRENGTHEN.value:
        return cp.strengthen(args=args)
    if operation == CanonicalOperation.INSPECT.value:
        # inspect takes a subquery as first arg
        query = args[0] if args else None
        json_out = "--json" in args
        if json_out:
            args = [a for a in args if a != "--json"]
        return cp.inspect(query, json_out=json_out)
    if operation == CanonicalOperation.CERTIFY.value:
        return cp.certify()
    if operation == CanonicalOperation.CI.value:
        return cp.ci()
    if operation == CanonicalOperation.DOCTOR.value:
        return cp.doctor()
    print(f"Unknown canonical operation: {operation}", file=sys.stderr)
    return 1


def _runtime_test_counts() -> dict[str, int] | None:
    """Per-file test counts for the runtime suite, or None if unavailable.

    Used only to *balance* shards. Coverage correctness never depends on it: the shard
    partition asserts union(shards) == all files independently, so a failure to collect
    counts degrades balance and nothing else.
    """
    import collections
    import subprocess

    try:
        completed = subprocess.run(
            [
                ".venv/bin/python",
                "-m",
                "pytest",
                "runtime/tests/",
                "-q",
                "--no-header",
                "-p",
                "no:cacheprovider",
                "--collect-only",
            ],
            capture_output=True,
            text=True,
            timeout=300,
            cwd=str(REPO_ROOT),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    counter: collections.Counter[str] = collections.Counter(
        line.split("::", 1)[0] for line in completed.stdout.splitlines() if "::" in line
    )
    return dict(counter) or None


#: Schema for a matrix leg's terminal result. The aggregate distinguishes three states
#: from this and its ABSENCE:
#:
#:   no file      the leg never reached a terminal result (killed, cancelled, never
#:                started) -- an infrastructure event
#:   status=failed the leg ran and failed a verification obligation
#:   status=passed the leg completed
#:
#: An externally killed process cannot write anything, and that is not a defect to paper
#: over -- it is a state the gate must be able to name. What IS a defect, and what this
#: schema exists to remove, is the previous shape where a *normal* failed execution left a
#: 0-byte stdout redirect and was therefore indistinguishable from a kill.
LEG_RESULT_SCHEMA = "m10r2-leg-result/v1"


def _write_leg_result(
    result_out: str | None,
    *,
    leg_id: str,
    status: str,
    final_decision: str | None,
    exit_code: int,
    duration_seconds: float,
    tasks: list[str],
    records: list[dict] | None = None,
    shard_id: str | None = None,
) -> None:
    """Write a leg's terminal result. Never raises; a write failure is reported."""
    import contextlib

    if not result_out:
        return
    payload = {
        "schema": LEG_RESULT_SCHEMA,
        # `leg_id` is the human label a reader sees in the log ("reconcile-shard 2/3");
        # `shard_id` is the stable machine key the shared reader matches on. Both are
        # emitted so ONE result contract serves all four fan-out workflows rather than
        # each growing its own shape.
        "leg_id": leg_id,
        "shard_id": shard_id or leg_id,
        "outcome": "terminal",
        "status": status,
        "final_decision": final_decision,
        "exit_code": exit_code,
        "duration_seconds": round(float(duration_seconds), 2),
        "tasks": list(tasks),
        "records": records or [],
    }
    try:
        path = Path(result_out)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        print(
            f"[{leg_id}] report={path} bytes={path.stat().st_size} "
            f"status={status} outcome=terminal",
            file=sys.stderr,
            flush=True,
        )
    except Exception as exc:  # noqa: BLE001 - reporting must not fail the run
        with contextlib.suppress(Exception):
            print(
                f"[{leg_id}] could not write terminal result: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
                flush=True,
            )


def _as_state(value: Any) -> Any:
    """Coerce a serialised completion state back into the enum member.

    Shard reports cross a process boundary, so ``CompletionState.PASS`` arrives as a
    string. Two shapes reach us and both must work:

    * ``"pass"`` — the enum's value, which is what a report stores when the value was
      serialised explicitly.
    * ``"CompletionState.PASS"`` — ``str()`` of the member. ``CompletionState`` is a
      ``str``-mixin enum, so ``str(member)`` is the qualified name rather than the
      value, and ``json.dumps(..., default=str)`` writes exactly that.

    Rejecting the second form would silently downgrade every task to INFRASTRUCTURE
    and fail the whole reconciliation, so both are accepted. An unrecognised value is
    never coerced to a passing state.
    """
    from runtime.foundation.verification.execution_orchestrator import CompletionState

    if isinstance(value, CompletionState):
        return value
    text = str(value)
    if "." in text and text.rsplit(".", 1)[0].endswith("CompletionState"):
        text = text.rsplit(".", 1)[1]
    try:
        return CompletionState(text)
    except ValueError:
        return CompletionState.INFRASTRUCTURE


def _parse_shard_arg(args: list[str]) -> tuple[int | None, int | None]:
    """Parse ``--shard N`` / ``--shard-count M`` out of *args*.

    Returns ``(None, None)`` when neither flag is present, which the callers
    normalise to "not sharded" — so an unflagged ``verify check`` takes exactly the
    code path it took before M10-R2.
    """
    shard: int | None = None
    shard_count: int | None = None

    def _int(raw: str, flag: str) -> int:
        try:
            return int(raw)
        except ValueError:
            raise ValueError(f"{flag} expects an integer, got {raw!r}") from None

    i = 0
    while i < len(args):
        a = args[i]
        if a == "--shard" and i + 1 < len(args):
            shard = _int(args[i + 1], "--shard")
            i += 2
            continue
        if a.startswith("--shard="):
            shard = _int(a.split("=", 1)[1], "--shard")
            i += 1
            continue
        if a == "--shard-count" and i + 1 < len(args):
            shard_count = _int(args[i + 1], "--shard-count")
            i += 2
            continue
        if a.startswith("--shard-count="):
            shard_count = _int(a.split("=", 1)[1], "--shard-count")
            i += 1
            continue
        i += 1
    return shard, shard_count


def _find_changed_files_arg(args: list[str]) -> list[str] | None:
    """Extract --changed-files arguments from args list.

    Handles both --changed-files=file1,file2 and --changed-files file1 file2 spellings.
    Returns list of files or None if not specified.
    """
    files = []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--changed-files":
            # Collect subsequent non-flag arguments as files
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                files.append(args[i])
                i += 1
            continue
        if a.startswith("--changed-files="):
            # Comma-separated list
            val = a[len("--changed-files=") :]
            files.extend(val.split(","))
            i += 1
            continue
        i += 1
    return files if files else None


if __name__ == "__main__":
    sys.exit(main())


def _run_runtime_integrity(result_dir: Path) -> bool:
    """Run the canonical integrity scan as its own obligation, and record the result.

    ``run_runtime_verification.sh`` runs this sequentially after the test suite and
    tracks it in its own ``FAILED_CHECKS`` list, so it has always been a *separate*
    obligation that merely happened to share a shell script. Sharding the suite makes
    that separation structural: integrity is the gate's own step, so it cannot be
    skipped by a shard, and a red scan cannot be hidden by a green suite.
    """
    from runtime.foundation.verification.env import child_process_env
    from runtime.foundation.verification.parallel_executor import run_streaming_command

    result_dir.mkdir(parents=True, exist_ok=True)
    from runtime.foundation.verification.parallel_executor import ProgressContext

    result = run_streaming_command(
        ".venv/bin/python -m runtime.verify integrity",
        stdout_path=result_dir / "integrity-stdout.log",
        stderr_path=result_dir / "integrity-stderr.log",
        timeout_seconds=_profile_task_timeout_seconds(),
        env=child_process_env(),
        # Live logging: the integrity scan is the gate's own obligation, so its progress
        # and termination kind belong in the job log next to the shard summaries.
        progress=ProgressContext(
            label="runtime:integrity",
            kind="integrity",
            log_dir=result_dir,
            timeout_seconds=_profile_task_timeout_seconds(),
        ),
    )
    ok = result.exit_code == 0 and not result.timed_out and not result.infra_error
    (result_dir / "integrity.json").write_text(
        json.dumps(
            {
                "obligation": "runtime-integrity",
                "status": "passed" if ok else "failed",
                "exit_code": result.exit_code,
                "duration_seconds": round(result.duration_seconds, 2),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        f"[runtime-gate] runtime-integrity {'passed' if ok else 'FAILED'} "
        f"({result.duration_seconds:.1f}s)",
        file=sys.stderr,
    )
    return ok
