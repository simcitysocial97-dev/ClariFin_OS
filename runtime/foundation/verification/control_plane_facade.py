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
    ExecutionOrchestrator,
    ExecutionPlan,
    ExecutionTaskSpec,
)
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
        print(f"[check] boundary={source}", end="")
        if base_ref:
            print(f" base={base_ref[:8]}", end="")
        print(f" files={len(changed_files)}")

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
            print("[check] NO_TASKS_FOR_CHANGE_SCOPE: certified no-op")
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
        self, changed_files: list[str] | None = None, *, json_out: bool = False
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
        """
        if changed_files is None:
            changed_files = _collect_changed_files()
        if not changed_files and not _is_git_available():
            print(
                "No changed files detected and git unavailable.",
                file=sys.stderr,
            )
            return 1

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
        """
        import time

        from runtime.foundation.verification.execution_orchestrator import (
            ExecutionPlan,
        )
        from runtime.foundation.verification.execution_shards import (
            assign_shards,
            validate_shard_request,
        )

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

        # O-2 signal truth: record the run through the canonical event/RunRecord
        # chain even when the caller provided an explicit plan path.
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
                profile_name="run",
                elapsed=elapsed,
                status="interrupted",
                passed=0,
                failed=0,
                final_decision="interrupted",
                extra_metadata={"tasks_executed": executed_task_ids},
            )
            return 130

        from runtime.verify import record_execution_report

        record_execution_report("run", report, time.monotonic() - run_start)

        if json_out:
            print(json.dumps(report.to_json(), indent=2, default=str))
        else:
            self._print_execution_report(report)
            print(_format_task_summary(report))

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


def _profile_task_timeout_seconds() -> int:
    """Resolve the per-task timeout ceiling for profile-alias execution.

    Overridable via ``VERIFY_TASK_TIMEOUT_SECONDS`` (seconds) for bounded
    regression testing; otherwise ``max(600, 2 * task.estimated_duration)``.
    """

    override = os.environ.get("VERIFY_TASK_TIMEOUT_SECONDS")
    if override:
        try:
            return max(30, int(override))
        except ValueError:
            pass
    return 3600  # fallback ceiling for very long profiles (playwright etc.)


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

    log_root = REPO_ROOT / "runtime" / "generated" / "profile-logs" / operation
    log_root.mkdir(parents=True, exist_ok=True)

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
    workers = max_workers_for(len(tasks))
    if workers > 1 and len(tasks) > 1:
        print(
            f"[profile:{operation}] running {len(tasks)} task(s) with "
            f"{workers} worker(s)",
            file=sys.stderr,
        )

    try:
        outcomes = execute_tasks_in_parallel(tasks, _run_task, max_workers=workers)
    except KeyboardInterrupt:
        interrupted_flag = True
        outcomes = []

    task_ids_executed = [o["id"] for o in outcomes if isinstance(o, dict)]
    passed = sum(1 for o in outcomes if isinstance(o, dict) and o["returncode"] == 0)
    failed = len(outcomes) - passed

    # Collect-all verdict: fail if any required task failed, but only after every
    # independent task has reported.
    timed_out_any = any(isinstance(o, dict) and o["timed_out"] for o in outcomes)
    signal_exit = next(
        (
            o["returncode"]
            for o in outcomes
            if isinstance(o, dict) and o["returncode"] in (130, 143)
        ),
        None,
    )
    first_failure = next(
        (
            o["returncode"]
            for o in outcomes
            if isinstance(o, dict) and o["returncode"] != 0
        ),
        0,
    )

    elapsed = time.monotonic() - run_start
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

    if timed_out_any:
        _record_verification_event(
            None,
            profile_name=operation,
            elapsed=elapsed,
            status="blocked",
            passed=passed,
            failed=failed,
            final_decision="timeout_blocked",
            extra_metadata={"tasks_executed": task_ids_executed},
        )
        return 124

    if first_failure != 0:
        # Every independent task has now run and reported; only now is the verdict
        # formed. The exit code is the first non-zero in plan order, matching the
        # pre-M10-R2 contract exactly.
        _record_verification_event(
            None,
            profile_name=operation,
            elapsed=elapsed,
            status="failed",
            passed=passed,
            failed=failed,
            final_decision="failed",
            extra_metadata={"tasks_executed": task_ids_executed},
        )
        return first_failure

    _record_verification_event(
        None,
        profile_name=operation,
        elapsed=elapsed,
        status="passed",
        passed=passed,
        failed=failed,
        final_decision="certified",
        extra_metadata={"tasks_executed": task_ids_executed},
    )
    return 0


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
        return cp.check(shard=(shard, shard_count))
    if operation == CanonicalOperation.PLAN.value:
        # Handle --json flag
        json_out = "--json" in args
        if json_out:
            args = [a for a in args if a != "--json"]
        # Handle --changed-files flag
        changed_files = _find_changed_files_arg(args)
        return cp.plan(changed_files=changed_files, json_out=json_out)
    if operation == CanonicalOperation.RUN.value:
        # Handle --plan and --json
        plan_path = None
        json_out = "--json" in args
        if json_out:
            args = [a for a in args if a != "--json"]
        # Simple --plan <file> parsing
        if "--plan" in args:
            idx = args.index("--plan")
            plan_path = args[idx + 1]
            args = args[:idx] + args[idx + 2 :]
        try:
            shard, shard_count = _parse_shard_arg(args)
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return cp.run(
            plan_path=plan_path,
            json_out=json_out,
            shard=(shard, shard_count),
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
