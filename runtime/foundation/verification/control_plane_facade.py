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
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Canonical imports — these are the ONLY internal modules the facade consumes.
from runtime.foundation.verification.canonical_control_plane import (
    CanonicalOperation,
    canonical_tree,
    migration_map,
    classification_for,
    canonical_help,
)
from runtime.foundation.verification.obligation import (
    VerificationObligation,
    ObligationSet,
    Disposition,
    ObligationKind,
    Change,
    Capability,
    Requirement,
    EvidenceRef,
)
from runtime.foundation.verification.control_plane import (
    ControlPlanePlanner,
    ControlPlanePlan,
)
from runtime.foundation.verification.executor_pipeline import (
    ExecutionEvidence,
)
from runtime.foundation.verification.execution_orchestrator import (
    ExecutionOrchestrator,
)
from runtime.foundation.verification.certification import (
    main as certification_main,
)
from runtime.foundation.verification.mutation_runner import (
    execute_mutation,
)
from runtime.foundation.intelligence import (
    blast_radius,
    format_affected,
    verification_plan,
    analyze,
    format_diagnostic,
)
from runtime.foundation.verification.strengthening_pipeline import (
    cmd_strengthen_capability,
    cmd_strengthen_survivor,
)
from runtime.foundation.verification.measurement_truth_integration import (
    format_measurement_truth_report,
    get_measurement_truth_integrator,
)
from runtime.foundation.verification.help_resolver import (
    cmd_help_resolve,
    cmd_what_should_i_run,
)
from runtime.foundation.verification.configuration_authority import (
    cmd_config_authority,
)
from runtime.foundation.verification.configuration_authority_enforcement import (
    main as config_authority_verify_main,
)
from runtime.foundation.verification.control_plane_efficiency import (
    main as efficiency_main,
)
from runtime.foundation.verification.evidence_planner import (
    EvidenceAwarePlanner,
    default_planner,
)


def _collect_changed_files() -> list[str]:
    """Collect changed files via the canonical intelligence layer."""
    from runtime.foundation.verification.orchestrator import _collect_changed_files, _is_git_available
    if _is_git_available():
        cf_result = _collect_changed_files()
        return cf_result.files
    return []


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

        Returns 0 on certified, 1 on failed/blocked.
        """
        if changed_files is None:
            changed_files = _collect_changed_files()
        if not changed_files and not _is_git_available():
            print("No changed files detected and git unavailable.", file=sys.stderr)
            return 1

        # 1. Repository state → Change detection
        # 2. Change detection → Capability graph → Affected capabilities
        control_plan: ControlPlanePlan = self.planner.plan(changed_files)

        # 3. Obligations (control plane's explicit obligation model)
        obligations: ObligationSet = self._plan_to_obligations(control_plan, changed_files)

        # 4. Build executable execution plan using the canonical ExecutionOrchestrator
        execution_plan = self.orchestrator.build_execution_plan(changed_files)

        # 5. Execution → Evidence (authorize all planned tasks for canonical path)
        report = self.orchestrator.execute(
            execution_plan,
            authorize={t.task_id for t in execution_plan.tasks},
            dry_run=False,
        )

        # 6. Evidence → Verdict
        decision = getattr(report, "final_decision", "unknown")
        if decision == "certified":
            print("✓ Verification CERTIFIED")
            return 0
        else:
            print("✗ Verification FAILED")
            reason = getattr(report, "decision_reason", "unknown")
            print(f"  Reason: {reason}", file=sys.stderr)
            return 1

    def plan(self, changed_files: list[str] | None = None, *, json_out: bool = False) -> int:
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
        if plan_path:
            # Load plan from file
            plan_data = json.loads(Path(plan_path).read_text())
            # Reconstruct ControlPlanePlan from dict
            from runtime.foundation.verification.control_plane import (
                ControlPlanePlan as CPPlan,
            )
            plan = CPPlan.from_dict(plan_data) if hasattr(CPPlan, 'from_dict') else None
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

        obligations: ObligationSet = self._plan_to_obligations(plan, _collect_changed_files())
        execution_plan = self.orchestrator.build_execution_plan(changed_files)
        report = self.orchestrator.execute(
            execution_plan,
            authorize={t.task_id for t in execution_plan.tasks},
            dry_run=False,
        )

        if json_out:
            print(json.dumps(report.to_json(), indent=2, default=str))
        else:
            self._print_execution_report(report)

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

    def strengthen(self, *, plan_path: str | None = None, json_out: bool = False, args: list[str] | None = None) -> int:
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
                remaining_args = list(args[:i]) + list(args[i + 2:])
                break

        if capability_id:
            # Run strengthening pipeline for specific capability
            from runtime.foundation.verification.strengthening_pipeline import (
                run_capability_aware_strengthening_pipeline,
                format_strengthening_report,
            )
            report = run_capability_aware_strengthening_pipeline(capability_id=capability_id)
            output = json.dumps(report.to_dict(), indent=2, default=str) if json_out else format_strengthening_report(report)
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
            print("Missing inspect subquery. Use: capabilities, evidence, plan, mutation, workflows, health", file=sys.stderr)
            return 1

        q = query.lower()
        if q == "capabilities":
            from runtime.foundation.verification.capability_catalog import cmd_capabilities
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
                print(f"Open: {len([o for o in obligations.obligations if o.disposition == 'open'])}")
                print(f"Closed: {len([o for o in obligations.obligations if o.disposition == 'closed'])}")
                for o in obligations.obligations:
                    if o.disposition == "open":
                        print(f"  - {o.obligation_id}: {o.capability.capability_id} ({o.requirement.obligation_kind.value})")
        elif q == "plan":
            changed_files = _collect_changed_files()
            plan = self.planner.plan(changed_files)
            if json_out:
                print(json.dumps(plan.to_dict(), indent=2, default=str))
            else:
                print(f"Plan ID: {plan.plan_id}")
                print(f"Capabilities: {[c.capability_id for c in plan.affected_capabilities]}")
                print(f"Tasks: {len(plan.evidence_aware_plan.selected_tasks)}")
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
            from runtime.system.observability.health_report import EngineeringHealthReport
            report = EngineeringHealthReport()
            print(report.generate())
            return 0
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

    def ci(self) -> int:
        """
        CI-specific orchestration/reconciliation entrypoint where needed.
        """
        # Standard CI reconciliation gate (mirrors verification-reconcile.yml)
        import os

        plan_path = os.environ.get(
            "CI_PLAN_PATH", "runtime/generated/vea5-tier-plan.pr.json"
        )
        evidence_path = os.environ.get(
            "CI_EVIDENCE_PATH", "runtime/generated/vea5-execution.pr.json"
        )
        report_path = os.environ.get(
            "CI_REPORT_PATH", "runtime/generated/vea5-reconciliation.pr.json"
        )
        commit_sha = os.environ.get("GITHUB_SHA", _get_current_commit())

        # For now delegate to existing CLI reconcile
        old_argv = sys.argv
        sys.argv = ["verify.py", "reconcile"]
        try:
            from runtime.foundation.verification.reconciliation import (
                validate_ci_artifacts,
            )
            # The existing reconcile command does the right thing
            return self._run_reconcile_cli()
        finally:
            sys.argv = old_argv

    def _run_reconcile_cli(self) -> int:
        """Run the existing reconcile CLI."""
        import sys as _sys
        from runtime.foundation.verification.reconciliation import (
            ReconciliationStatus,
            reconcile_from_artifacts,
            save_reconciliation_report,
            validate_ci_artifacts,
        )
        from runtime.foundation.verification.tier import (
            TierPlan,
            plan_for_tier,
        )

        import os

        plan_path = os.environ.get(
            "CI_PLAN_PATH", "runtime/generated/vea5-tier-plan.pr.json"
        )
        evidence_path = os.environ.get(
            "CI_EVIDENCE_PATH", "runtime/generated/vea5-execution.pr.json"
        )
        report_path = os.environ.get(
            "CI_REPORT_PATH", "runtime/generated/vea5-reconciliation.pr.json"
        )
        commit_sha = os.environ.get("GITHUB_SHA", _get_current_commit())

        # M5 CI gate: validate the CI plan against its OWN execution evidence
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
        import hashlib

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
            canonical_op, internal_route = migration["canonical_operation"], migration["internal_route"]
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


def _dispatch_canonical(operation: str, args: list[str]) -> int:
    """Dispatch to the canonical control plane method."""
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