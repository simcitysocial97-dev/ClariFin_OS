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

import json
import sys
from pathlib import Path
import os
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Canonical imports — these are the ONLY internal modules the facade consumes.

from runtime.foundation.intelligence import (
    analyze,
    format_diagnostic,
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


def _collect_changed_files() -> list[str]:
    """Collect changed files via the canonical intelligence layer."""
    return _collect_changed_files_result().files


def _collect_changed_files_result() -> Any:
    """Return the full ``_ChangedFilesResult`` from the orchestrator layer, so
    callers can inspect the resolved boundary (source, base ref, file count).
    """
    from runtime.foundation.verification.orchestrator import (
        _collect_changed_files,
        _is_git_available,
    )

    if _is_git_available():
        return _collect_changed_files()
    from types import SimpleNamespace

    return SimpleNamespace(
        files=[], source="no-git", base=None, head=None, error="git unavailable"
    )


def _get_current_commit() -> str:
    from runtime.foundation.verification.orchestrator import _get_current_commit

    return _get_current_commit()


def _is_git_available() -> bool:
    from runtime.foundation.verification.orchestrator import _is_git_available

    return _is_git_available()


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

    # ── CANONICAL PUBLIC OPERATIONS ────────────────────────────────────────

    def check(self, changed_files: list[str] | None = None) -> int:
        """
        Primary verification entrypoint.

        Given the current repository state, determine what is affected,
        plan the required verification, execute it, and produce evidence.

        Returns 0 on certified, 1 on failed/blocked/interrupted.
        """
        import time

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

        max_warn = int(os.environ.get("VERIFY_MAX_CHANGED_FILES_WARN", 500))
        if len(changed_files) > max_warn:
            print(
                f"[check] WARNING: boundary has {len(changed_files)} files "
                f"(>{max_warn}); plan may be unbounded — set VERIFICATION_BASE_REF to narrow",
                file=sys.stderr,
            )

        if not changed_files and not _is_git_available():
            print("No changed files detected and git unavailable.", file=sys.stderr)
            return 1

        # 1. Repository state → Change detection
        # 2. Change detection → Capability graph → Affected capabilities
        control_plan: ControlPlanePlan = self.planner.plan(changed_files)

        # 3. Obligations (control plane's explicit obligation model)
        _obligations: ObligationSet = self._plan_to_obligations(
            control_plan, changed_files
        )

        # 4. Build executable execution plan using the canonical ExecutionOrchestrator
        execution_plan = self.orchestrator.build_execution_plan(changed_files)

        # 5. Execute, with an on_record hook so partial-progress is observable
        #    even if the run is interrupted.
        run_start = time.monotonic()
        executed_task_ids: list[str] = []

        def _capture_record(rec):
            executed_task_ids.append(rec.task_id)

        max_warn = int(os.environ.get("VERIFY_MAX_CHANGED_FILES_WARN", 500))
        if len(changed_files) > max_warn:
            print(
                f"[check] WARNING: boundary has {len(changed_files)} files "
                f"(>{max_warn}); plan may be unbounded — set VERIFICATION_BASE_REF to narrow",
                file=sys.stderr,
            )
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
            print("No changed files detected and git unavailable.", file=sys.stderr)
            return 1

        plan: ControlPlanePlan = self.planner.plan(changed_files)
        obligations: ObligationSet = self._plan_to_obligations(plan, changed_files)

        if json_out:
            print(json.dumps(obligations.to_dict(), indent=2, default=str))
        else:
            self._print_plan_obligations(obligations)

        return 0

    def run(self, *, plan_path: str | None = None, json_out: bool = False) -> int:
        """
        Execute an explicit or generated verification plan.

        The plan must be machine-readable (ControlPlanePlan JSON).
        """
        import time

        if plan_path:
            # Load plan from file
            plan_data = json.loads(Path(plan_path).read_text())
            # Reconstruct ControlPlanePlan from dict
            from runtime.foundation.verification.control_plane import (
                ControlPlanePlan as CPPlan,
            )

            plan = CPPlan.from_dict(plan_data) if hasattr(CPPlan, "from_dict") else None
            if plan is None:
                # Fallback: generate fresh plan
                changed_files = _collect_changed_files()
                plan = self.planner.plan(changed_files)
        else:
            changed_files = _collect_changed_files()
            if not changed_files and not _is_git_available():
                print("No changed files detected and git unavailable.", file=sys.stderr)
                return 1
            plan = self.planner.plan(changed_files)

        _obligations: ObligationSet = self._plan_to_obligations(plan, changed_files)
        execution_plan = self.orchestrator.build_execution_plan(changed_files)

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
            print("[run] INTERRUPTED (SIGINT/SIGTERM)", file=sys.stderr)
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
                bundle["change"], bundle["blast"], bundle["risk"], bundle["repair"]
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
            from runtime.foundation.verification.mutation_runner import run_mutation_cli

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
            from runtime.foundation.verification.help_resolver import cmd_help_resolve

            old_argv = sys.argv
            sys.argv = ["verify.py", "help-resolve", "workflows"] + sys.argv[1:]
            try:
                return cmd_help_resolve(sys.argv[1:])
            finally:
                sys.argv = old_argv
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

            return cmd_evidence_cleanup(sys.argv[2:] if len(sys.argv) > 2 else [])
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
        import os

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
        import os
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
        profile = _find_arg("--profile", args, default="runtime")
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
            plan_fingerprint,
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
        import os

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
        import os

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

                try:
                    local_results = _unit_results_from_any_evidence(local_evidence_path)
                except Exception:
                    pass
            if evidence_path:
                from runtime.foundation.verification.reconciliation import (
                    _unit_results_from_any_evidence,
                )

                try:
                    ci_results = _unit_results_from_any_evidence(evidence_path)
                except Exception:
                    pass
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

    def doctor(self) -> int:
        """
        Framework health/integrity diagnostics.

        This is for the verification framework itself rather than application verification.
        """
        # Delegates to health module which already exists
        from runtime.system.observability.health_report import EngineeringHealthReport

        report = EngineeringHealthReport()
        output = report.generate()
        print(output)
        return 0 if "FAIL" not in output else 1

    # ── INTERNAL HELPERS ────────────────────────────────────────────────────

    def _plan_to_obligations(
        self, plan: ControlPlanePlan, changed_files: list[str]
    ) -> ObligationSet:
        """
        Convert a ControlPlanePlan into a set of VerificationObligation instances.
        This is where the planner's output becomes explicit obligations.
        """

        obligations: list[VerificationObligation] = []
        for i, task in enumerate(plan.tasks):
            # Derive a change record (simplified — in reality would map file->symbol->capability)
            change = Change(
                path=changed_files[0] if changed_files else "unknown",
                change_type="modified",
                symbol=None,
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
                rationale=task.reason or "Inferred from change impact",
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
                reasons=(task.reason,),
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
    print(f"Command not available in canonical surface: {command}", file=sys.stderr)
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
    import os

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

    Returns the subprocess exit code (0 = success; non-zero mapped according
    to the canonical outcome vocabulary). On SIGINT/SIGTERM the process exits
    130/143 and an ``interrupted`` event is recorded. On per-task timeout a
    ``timeout_blocked`` event is recorded and the process exits 124.
    """
    import os
    import subprocess
    import time

    from runtime.foundation.verification.env import child_process_env
    from runtime.foundation.verification.profiles import get_profile
    from runtime.verify import _record_verification_event

    # Cache replay path — check before executing tasks.
    from runtime.foundation.verification.cache import VerificationCache

    cache = VerificationCache(
        REPO_ROOT / "runtime" / "generated" / "verification-cache.json",
        root=REPO_ROOT,
    )
    commit_sha = _get_current_commit()
    cf_result = _collect_changed_files_result()
    changed_files = sorted(getattr(cf_result, "files", []))

    try:
        profile = get_profile(operation)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    env = child_process_env()
    run_start = time.monotonic()
    passed = 0
    failed = 0
    task_ids_executed: list[str] = []
    interrupted_flag = False

    # Override is applied uniformly if the env-var is set (useful for tests /
    # bounded CI jobs); otherwise each task uses its declared estimate.
    timeout_override = _profile_task_timeout_seconds()

    # CACHE REPLAY: skip execution if a valid cached verdict exists.
    cache_result = cache.replay(commit_sha, changed_files, operation)
    if cache_result.reusable:
        print(
            f"[profile:{operation}] cache hit — replaying {cache_result.overall_status}",
            file=sys.stderr,
        )
        _record_verification_event(
            None,
            profile_name=operation,
            elapsed=0.0,
            cache_hit=True,
            status="passed" if cache_result.overall_status == "pass" else "failed",
            final_decision="cache_replay",
        )
        return cache_result.exit_code or 0

    for task in profile.tasks:
        task_timeout = timeout_override
        if task_timeout <= 0:
            task_timeout = max(600, 2 * task.estimated_duration_seconds)
        for cmd in task.commands:
            task_ids_executed.append(task.id)
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=str(REPO_ROOT),
                    env=env,
                    timeout=task_timeout,
                )
            except subprocess.TimeoutExpired:
                failed += 1
                elapsed = time.monotonic() - run_start
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
                print(
                    f"[profile:{operation}] task {task.id!r} timed out after {task_timeout}s",
                    file=sys.stderr,
                )
                return 124
            except KeyboardInterrupt:
                interrupted_flag = True
                break
            if result.returncode != 0:
                failed += 1
                elapsed = time.monotonic() - run_start
                # SIGINT (130) and SIGTERM (143) are interruption signals,
                # not task failures — record them as interrupted so the
                # operator knows the run was terminated rather than that a
                # verification asserted failed.
                if result.returncode in (130, 143):
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
                    return result.returncode
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
                print(
                    f"[profile:{operation}] task {task.id!r} failed (exit {result.returncode})",
                    file=sys.stderr,
                )
                return result.returncode
            passed += 1
        if interrupted_flag:
            break

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

    # CACHE SAVE: persist verdict only on full successful completion.
    from runtime.foundation.verification.cache import CachedVerdict

    cache.save(
        profile=operation,
        commit=commit_sha,
        changed_files=changed_files,
        verdict=CachedVerdict(
            overall_status="pass" if failed == 0 else "fail",
            passed=passed,
            failed=failed,
            skipped=0,
        ),
        duration=elapsed,
    )

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
        return cp.check()
    if operation == CanonicalOperation.PLAN.value:
        # Handle --json flag
        json_out = "--json" in args
        if json_out:
            args = [a for a in args if a != "--json"]
        return cp.plan(json_out=json_out)
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
        return cp.run(plan_path=plan_path, json_out=json_out)
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


if __name__ == "__main__":
    sys.exit(main())
