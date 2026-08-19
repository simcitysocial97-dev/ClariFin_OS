#!/usr/bin/env python3
"""
ClariFin OS — Autonomous Verification Runtime (Program 7B)

CLI entry point for deterministic verification.

Usage:
    python runtime/verify.py quick
    python runtime/verify.py backend
    python runtime/verify.py frontend
    python runtime/verify.py contracts
    python runtime/verify.py graph
    python runtime/verify.py full
    python runtime/verify.py knowledge
    python runtime/verify.py knowledge endpoint <path>
    python runtime/verify.py knowledge capability <name>
    python runtime/verify.py knowledge workspace <name>
    python runtime/verify.py knowledge rule <id>
    python runtime/verify.py knowledge component <name>

The runtime automatically:
1. Collects changed files (git diff)
2. Analyzes cross-layer impact (Program 7A)
3. Plans verification deterministically
4. Executes verification tasks
5. Aggregates evidence
6. Generates a unified report
7. Exits non-zero on failures
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.models import (  # noqa: E402
    VerificationStatus,
)
from runtime.foundation.verification.orchestrator import (  # noqa: E402
    VerificationOrchestrator,
    _collect_changed_files,
    _get_current_commit,
    _is_git_available,
)
from runtime.foundation.verification.profiles import get_profile  # noqa: E402
from runtime.foundation.verification.failure_report import (  # noqa: E402
    build_failure_report,
)

VERIFICATION_CACHE_PATH = REPO_ROOT / "runtime" / "generated" / "verification-cache.json"
VERIFICATION_REPORT_PATH = REPO_ROOT / "runtime" / "generated" / "verification-report.md"


def _log_changed_files_boundary(cf_result: Any) -> None:
    """Log the resolved changed-file boundary and the resulting scope count.

    M9-C3: proving *which* PR base/head boundary drove the verification scope is
    part of trustworthy CI. When the boundary could not be resolved, this prints
    the actionable error so a misleading scope is never silently selected.
    """
    base = getattr(cf_result, "base", None)
    head = getattr(cf_result, "head", None)
    source = getattr(cf_result, "source", "unknown")
    error = getattr(cf_result, "error", None)
    count = len(getattr(cf_result, "files", []) or [])
    if error:
        print(f"Changed-file boundary ERROR: {error}", file=sys.stderr)
        return
    scope = f"{base}..{head}" if head else (f"merge-base({base})" if base else "local")
    print(
        f"Changed files: {count} (boundary: {scope}, source: {source})",
        file=sys.stderr,
    )


def _record_verification_event(
    report: Any | None,
    profile_name: str,
    elapsed: float,
    *,
    cache_hit: bool = False,
    status: str | None = None,
) -> None:
    try:
        from runtime.system.observability.execution_context import create_context
        from runtime.system.observability.event_store import create_event, EngineeringEventStore
        from runtime.system.observability.repository import LocalMetricsRepository, RunRecord

        if report is not None:
            _status = report.summary.overall_status.value
            _passed = report.summary.passed
            _failed = report.summary.failed
            _skipped = report.summary.skipped
            _blast = report.blast_radius
            _evidence = len(report.evidence_files)
        else:
            # Cache-replay path: no fresh report exists; use the recorded verdict.
            _status = status or "unknown"
            _passed = 0
            _failed = 0
            _skipped = 0
            _blast = 0
            _evidence = 0

        ctx = create_context()
        event_store = EngineeringEventStore()
        event = create_event(
            event_type="VerificationCompleted",
            execution_context=ctx.to_dict(),
            payload={
                "profile": profile_name,
                "status": _status,
                "passed": _passed,
                "failed": _failed,
                "skipped": _skipped,
                "duration_seconds": elapsed,
                "blast_radius": _blast,
                "evidence_count": _evidence,
                "cache_hit": cache_hit,
                "metadata": {},
            },
        )
        event_store.append(event)

        repo = LocalMetricsRepository()
        repo.append(
            RunRecord(
                run_id=event.event_id,
                timestamp=event.timestamp,
                environment=ctx.environment.value,
                runner=ctx.runner.value,
                verification_depth=ctx.verification_depth.value,
                intent=ctx.intent.value,
                trigger=ctx.trigger.value,
                commit_sha=ctx.commit_sha,
                branch=ctx.branch,
                profile=profile_name,
                status=_status,
                passed=_passed,
                failed=_failed,
                skipped=_skipped,
                duration_seconds=elapsed,
                blast_radius=_blast,
                evidence_count=_evidence,
                cache_hit=cache_hit,
            )
        )
    except Exception:
        pass


def cmd_status() -> int:
    from runtime.foundation.workspace.status import cmd_status as _cmd_status
    return _cmd_status()


def cmd_history() -> int:
    from runtime.foundation.workspace.history import cmd_history as _cmd_history
    return _cmd_history()


def cmd_deps() -> int:
    from runtime.foundation.workspace.dependencies import cmd_deps as _cmd_deps
    file_path = sys.argv[2] if len(sys.argv) > 2 else None
    return _cmd_deps(file_path)


def cmd_verify_status() -> int:
    from runtime.foundation.workspace.verification import cmd_verify_status as _cmd_verify_status
    return _cmd_verify_status()


def cmd_metrics() -> int:
    from runtime.foundation.workspace.metrics import cmd_metrics as _cmd_metrics
    return _cmd_metrics()


def cmd_analytics() -> int:
    from runtime.system.observability.analytics import AnalyticsEngine

    engine = AnalyticsEngine()
    report = engine.compute()
    print(json.dumps(report.to_dict(), indent=2, default=str))
    return 0


def cmd_health() -> int:
    from runtime.system.observability.health_report import EngineeringHealthReport

    report = EngineeringHealthReport()
    output = report.generate()
    print(output)
    return 0


def cmd_doctor() -> int:
    return cmd_health()


def cmd_ci_doctor() -> int:
    import subprocess
    import sys as _sys

    script_path = REPO_ROOT / ".github" / "scripts" / "validate_actions.py"
    result = subprocess.run(
        [_sys.executable, str(script_path)],
        capture_output=True,
        text=True,
    )
    print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=_sys.stderr, end="")
    return result.returncode


def cmd_diagnose() -> int:
    from runtime.foundation.intelligence import (
        analyze,
        format_diagnostic,
    )

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    bundle = analyze(changed_files=changed_files)
    print(format_diagnostic(
        bundle["change"], bundle["blast"], bundle["risk"], bundle["repair"]
    ))
    return 0


def cmd_diagnose_failures() -> int:
    """VEA-2 Phase 2, M6 — attribute real pipeline failures to the blast radius.

    Replaces the Phase 1.5 hand-fed-log diagnostic. Failures are read from the
    M5 evidence (``unit_id`` already joined to the M3 manifest), never parsed out
    of raw logs. Zero manual log parsing.
    """
    from runtime.foundation.intelligence.platform.blast import compute_blast_radius
    from runtime.foundation.intelligence.platform.change import analyze_changes
    from runtime.foundation.intelligence.platform.optimizer import optimize_verification
    from runtime.foundation.intelligence.platform.attribution import (
        attribute_failures,
        build_observed_failures,
    )
    from runtime.foundation.intelligence.platform.cli_format import (
        format_cross_layer_failure,
    )
    from runtime.system.evidence.aggregator import EvidenceAggregator

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    change = analyze_changes(paths=changed_files)
    blast = compute_blast_radius(change)
    plan = optimize_verification(blast)

    evidence_dir = REPO_ROOT / "runtime" / "generated" / "evidence"
    if not evidence_dir.exists():
        # Explicit "no evidence" state. We do NOT fabricate a green verdict or
        # claim the change is clean — there is simply nothing to diagnose.
        print(
            "No verification evidence was collected for this run "
            f"({evidence_dir.relative_to(REPO_ROOT)} does not exist)."
        )
        print("Run a verification profile first, then re-run diagnose-failures.")
        return 0

    summary = EvidenceAggregator(REPO_ROOT).aggregate(evidence_dir)
    failures = build_observed_failures(summary.unit_failures)

    if not failures:
        print(
            "No observed failures in this run's evidence. "
            "Verification is green for this change, or no failure evidence "
            "was captured."
        )
        return 0

    report = attribute_failures(blast, failures, plan.selected)
    print(format_cross_layer_failure(change, blast, plan, report))

    # Exit non-zero only when the change is actually implicated in a failure,
    # mirroring the Phase 1.5 intent: an unrelated red pipeline is not a failure
    # of this command's diagnostic.
    return 1 if report.change_is_implicated else 0


def cmd_affected() -> int:
    from runtime.foundation.intelligence import (
        blast_radius,
        verification_plan,
        format_affected,
    )

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    blast = blast_radius(changed_files)
    plan = verification_plan(changed_files)
    print(format_affected(blast, plan))
    return 0


def cmd_repair() -> int:
    from runtime.foundation.intelligence import repair_plan, format_repair

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    repair = repair_plan(changed_files=changed_files)
    print(format_repair(repair))
    return 0


def cmd_risk() -> int:
    from runtime.foundation.intelligence import engineering_risk, format_risk

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    risk = engineering_risk(changed_files)
    print(format_risk(risk))
    return 0


def cmd_integrity() -> int:
    from runtime.foundation.integrity.engine import evaluate_integrity
    from runtime.foundation.integrity.formatter import format_integrity_report

    report = evaluate_integrity()
    output = format_integrity_report(report)
    print(output)

    if not report.passed:
        return 1
    return 0


def cmd_knowledge() -> int:
    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.formatter import format_knowledge_report

    index = build_index()
    output = format_knowledge_report(index)
    print(output)
    return 0


def cmd_knowledge_endpoint() -> int:
    from runtime.foundation.knowledge.query import query_endpoint
    from runtime.foundation.knowledge.indexer import build_index
    build_index()  # noqa: F841 - warm knowledge cache
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge endpoint <path>", file=sys.stderr)
        return 1

    path = sys.argv[3]
    result = query_endpoint(path)
    if result is None:
        print(f"No endpoint found for path: {path}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_capability() -> int:
    from runtime.foundation.knowledge.query import query_capability
    from runtime.foundation.knowledge.indexer import build_index
    build_index()  # noqa: F841 - warm knowledge cache
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge capability <name>", file=sys.stderr)
        return 1

    name = sys.argv[3]
    result = query_capability(name)
    if result is None:
        print(f"No capability found for name: {name}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_workspace() -> int:
    from runtime.foundation.knowledge.query import query_workspace
    from runtime.foundation.knowledge.indexer import build_index
    build_index()  # noqa: F841 - warm knowledge cache
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge workspace <name>", file=sys.stderr)
        return 1

    name = sys.argv[3]
    result = query_workspace(name)
    if result is None:
        print(f"No workspace found for name: {name}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_rule() -> int:
    from runtime.foundation.knowledge.query import query_rule
    from runtime.foundation.knowledge.indexer import build_index
    build_index()  # noqa: F841 - warm knowledge cache
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge rule <id>", file=sys.stderr)
        return 1

    rule_id = sys.argv[3]
    result = query_rule(rule_id)
    if result is None:
        print(f"No rule found for id: {rule_id}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_component() -> int:
    from runtime.foundation.knowledge.query import query_component
    from runtime.foundation.knowledge.indexer import build_index
    build_index()  # noqa: F841 - warm knowledge cache
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge component <name>", file=sys.stderr)
        return 1

    name = sys.argv[3]
    result = query_component(name)
    if result is None:
        print(f"No component found for name: {name}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_plan() -> int:
    """VEA-5 M2 — emit a tier-aware verification plan manifest.

    Usage:
        python runtime/verify.py plan --tier local
        python runtime/verify.py plan --tier pr --base main
        python runtime/verify.py plan --tier deep
        python runtime/verify.py plan --tier local --changed backend/src/engines/loan_engine/amortization.py

    Writes runtime/generated/vea5-tier-plan.json and prints it. This is the
    inspectable evidence artifact required by the M2 acceptance gates; it does
    not execute any verification unit.
    """
    import argparse

    parser = argparse.ArgumentParser(prog="verify.py plan", add_help=False)
    parser.add_argument("--tier", required=True, choices=["local", "pr", "deep"])
    parser.add_argument("--base", default=None, help="explicit PR base ref")
    parser.add_argument(
        "--changed", nargs="*", default=None,
        help="explicit changed files (bypass git; for CI override / tests)",
    )
    parser.add_argument("--head", default=None, help="explicit head ref")
    parser.add_argument("--no-write", action="store_true", help="do not write the manifest file")
    args, _ = parser.parse_known_args(sys.argv[2:])

    # M5-A — PR base correctness. For a PR the base ref must be the PR base
    # (GITHUB_BASE_REF) or an explicit equivalent. It must NEVER silently fall
    # back to origin/main when a PR base is available.
    pr_base = args.base or os.environ.get("GITHUB_BASE_REF")
    if args.tier == "pr" and not pr_base:
        print(
            "ERROR: --tier pr requires an explicit base (--base) or "
            "GITHUB_BASE_REF. Refusing to fall back to origin/main.",
            file=sys.stderr,
        )
        return 1

    from runtime.foundation.verification.tier import (
        MANIFEST_PATH,
        plan_for_tier,
    )

    plan = plan_for_tier(
        args.tier,
        changed_files=args.changed,
        explicit_base=pr_base,
        pr_base=pr_base,
        head_ref=args.head,
    )

    if not args.no_write:
        plan.write(MANIFEST_PATH)

    print(json.dumps(plan.to_dict(), indent=2, default=str))
    return 0


def cmd_reconcile() -> int:
    """VEA-5 M4/M5 — plan reconciliation & CI reconciliation gate.

    Two distinct modes:

    (A) CI gate (Option A, used by .github/workflows/verification-reconcile.yml).
        When only --plan (+ --evidence) is supplied and --local is ABSENT, the CI
        plan is validated against its OWN persisted execution evidence. A valid
        fully-passing execution yields same-plan (exit 0). It must NOT classify
        as environment-divergence merely because a LOCAL side was omitted.

        python runtime/verify.py reconcile \\
            --plan runtime/generated/vea5-tier-plan.pr.json \\
            --evidence runtime/generated/vea5-execution.pr.json \\
            --report runtime/generated/vea5-reconciliation.pr.json \\
            --commit "$GITHUB_SHA"

    (B) LOCAL-vs-CI comparison. When --local (and optionally --local-evidence) is
        supplied alongside --plan, the two sides are reconciled structurally.

        python runtime/verify.py reconcile --local local.json --plan ci.json \\
            --local-evidence local-ev.json --evidence ci-ev.json

    M5 exit contract:
        same-plan                  -> 0
        expected-tier-difference   -> 0
        environment-divergence     -> 1  (execution/evidence diverged; NOT a planning defect)
        planning-divergence        -> 2  (architectural failure: unexplained unit change)

    The environment-vs-planning distinction is preserved in the persisted report
    even though both fail the gate.
    """
    import argparse

    from runtime.foundation.verification.reconciliation import (
        ReconciliationStatus,
        reconcile,
        reconcile_from_artifacts,
        save_reconciliation_report,
        validate_ci_artifacts,
    )
    from runtime.foundation.verification.tier import (
        TierPlan,
        plan_for_tier,
    )

    parser = argparse.ArgumentParser(prog="verify.py reconcile", add_help=False)
    # Generate-and-compare mode (legacy / dev).
    parser.add_argument("--local", default=None, help="path to a LOCAL plan manifest (JSON)")
    parser.add_argument("--ci", default=None, help="path to a CI/PR plan manifest (JSON)")
    parser.add_argument("--tier", default="local", choices=["local", "pr", "deep"])
    parser.add_argument("--pr-tier", default="pr", choices=["local", "pr", "deep"])
    parser.add_argument("--base", default=None, help="explicit PR base ref")
    parser.add_argument(
        "--changed", nargs="*", default=None,
        help="explicit changed files (when generating both plans)",
    )
    parser.add_argument("--head", default=None, help="explicit head ref")
    # M5 persisted-artifact mode (CI gate).
    parser.add_argument("--plan", default=None, help="path to the CI/PR plan manifest (JSON)")
    parser.add_argument("--evidence", default=None, help="path to CI/PR execution-evidence artifact (JSON)")
    parser.add_argument("--local-evidence", default=None, help="path to a LOCAL execution-evidence artifact (JSON)")
    parser.add_argument("--report", default=None, help="path to write the persisted reconciliation report (JSON)")
    parser.add_argument("--commit", default=None, help="commit sha for the evidence identity spine")
    args, _ = parser.parse_known_args(sys.argv[2:])

    if args.plan is not None:
        if args.local is not None:
            # Option B — true LOCAL-vs-CI reconciliation from persisted artifacts.
            report = reconcile_from_artifacts(
                local_plan_path=args.local,
                ci_plan_path=args.plan,
                local_evidence_path=args.local_evidence,
                ci_evidence_path=args.evidence,
                commit=args.commit,
            )
        else:
            # Option A — M5 CI gate: validate the CI plan against its OWN
            # execution evidence. It must NOT classify as environment-divergence
            # merely because --local was omitted. (See validate_ci_artifacts.)
            report = validate_ci_artifacts(
                ci_plan_path=args.plan,
                ci_evidence_path=args.evidence,
                commit=args.commit,
            )
    else:
        def _load_or_generate(path: str | None, tier: str) -> TierPlan:
            if path:
                data = json.loads(Path(path).read_text(encoding="utf-8"))
                return TierPlan(
                    tier=data["tier"],
                    base_ref=data.get("base_ref"),
                    head_ref=data["head_ref"],
                    changed_files=tuple(data["changed_files"]),
                    selected=tuple(
                        __import__(
                            "runtime.foundation.verification.tier", fromlist=["SelectedUnit"]
                        ).SelectedUnit(**s) for s in data["selected"]
                    ),
                    excluded=tuple(
                        __import__(
                            "runtime.foundation.verification.tier", fromlist=["ExcludedUnit"]
                        ).ExcludedUnit(**e) for e in data["excluded"]
                    ),
                    estimated_seconds=data["estimated_seconds"],
                    planner_version=data["planner_version"],
                    framework_version=data["framework_version"],
                )
            return plan_for_tier(
                tier,
                changed_files=args.changed,
                explicit_base=args.base,
                pr_base=args.base,
                head_ref=args.head,
            )

        local_plan = _load_or_generate(args.local, args.tier)
        ci_plan = _load_or_generate(args.ci, args.pr_tier)
        report = reconcile(local_plan, ci_plan)

    if args.report is not None:
        save_reconciliation_report(report, args.report)

    print(json.dumps(report.to_dict(), indent=2, default=str))

    status = report.classification.status
    # M5 exit contract.
    if status == ReconciliationStatus.PLANNING_DIVERGENCE.value:
        return 2  # architectural failure
    if status == ReconciliationStatus.ENVIRONMENT_DIVERGENCE.value:
        return 1  # execution/evidence differed, not a planning defect
    return 0


def cmd_exec_evidence() -> int:
    """VEA-5 M5-C / M6-A — emit the persisted execution-evidence artifact.

    Reads a plan manifest (M5-B) and the recorded outcome of the profile that
    executed it, then writes the execution-evidence artifact. By default it emits
    the **M6-A v2 schema** (``vea5-execution-evidence/v2``): per selected unit, an
    *execution record* with one or more *attempts*, each carrying command,
    start/end, duration, exit code and evidence-artifact references. This is the
    unambiguous ``unit_id -> attempt -> artifact`` path required by M6. Use
    ``--v1`` to emit the legacy M5 v1 schema (still loadable by reconcile).

    This artifact is the deterministic input to ``verify.py reconcile`` —
    reconciliation never reconstructs execution state from the live job.

    Usage (M6-A v2):
        python runtime/verify.py exec-evidence \\
            --plan runtime/generated/vea5-tier-plan.pr.json \\
            --profile runtime \\
            --report runtime/generated/verification-report.md \\
            --status pass --exit 0 --duration 42.0 \\
            --out runtime/generated/vea5-execution.pr.json

    M6-A note: when richer per-unit detail is available (command, timing,
    stdout/stderr, coverage/mutation artifact refs), pass them per unit. Until
    that instrumentation exists, the per-unit status is derived from the
    executed profile's overall outcome — the v2 *shape* is fully satisfied and
    the gate remains deterministic.
    """
    import argparse

    from runtime.foundation.verification.evidence_contract import (
        ExecutionEvidenceV2,
        build_unit_execution_record,
        execution_evidence_v2_from_plan,
        save_execution_evidence_v2,
    )
    from runtime.foundation.verification.reconciliation import (
        execution_evidence_from_units,
        plan_fingerprint,
        save_execution_evidence,
    )
    from runtime.foundation.verification.tier import TierPlan

    parser = argparse.ArgumentParser(prog="verify.py exec-evidence", add_help=False)
    parser.add_argument("--plan", required=True, help="path to the plan manifest (JSON)")
    parser.add_argument("--profile", default="runtime", help="profile that executed the plan")
    parser.add_argument(
        "--report", default="runtime/generated/verification-report.md",
        help="evidence location for the executed profile",
    )
    parser.add_argument("--status", required=True, choices=["pass", "fail", "skipped"])
    parser.add_argument("--exit", type=int, required=True, dest="exit_code")
    parser.add_argument("--duration", type=float, default=0.0)
    parser.add_argument("--commit", default=None)
    parser.add_argument(
        "--out", default="runtime/generated/vea5-execution.json",
        help="path to write the execution-evidence artifact",
    )
    parser.add_argument("--v1", action="store_true", help="emit legacy M5 v1 schema")
    args, _ = parser.parse_known_args(sys.argv[2:])

    data = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    plan = TierPlan(
        tier=data["tier"],
        base_ref=data.get("base_ref"),
        head_ref=data["head_ref"],
        changed_files=tuple(data["changed_files"]),
        selected=tuple(
            __import__(
                "runtime.foundation.verification.tier", fromlist=["SelectedUnit"]
            ).SelectedUnit(**s) for s in data["selected"]
        ),
        excluded=tuple(
            __import__(
                "runtime.foundation.verification.tier", fromlist=["ExcludedUnit"]
            ).ExcludedUnit(**e) for e in data["excluded"]
        ),
        estimated_seconds=data["estimated_seconds"],
        planner_version=data["planner_version"],
        framework_version=data["framework_version"],
    )

    if args.v1:
        from runtime.foundation.verification.reconciliation import UnitExecution

        units = [
            UnitExecution(
                unit_id=s.unit_id,
                status=args.status,
                exit_code=args.exit_code,
                evidence_ref=args.report,
            )
            for s in plan.selected
        ]
        v1_artifact = execution_evidence_from_units(
            tier=plan.tier,
            plan_fingerprint_digest=plan_fingerprint(plan).digest(),
            commit=args.commit or plan.head_ref,
            units=units,
        )
        save_execution_evidence(v1_artifact, args.out)
        print(json.dumps(v1_artifact.to_dict(), indent=2))
        return 0

    # M6-A v2: per-unit record with a single attempt.
    records = {}
    for s in plan.selected:
        provenance = {
            "category": s.category,
            "source": s.source,
            "capabilities": list(s.capabilities),
            "impact_kinds": list(s.impact_kinds),
            "command": s.command,
            "reason": s.reason,
        }
        records[s.unit_id] = build_unit_execution_record(
            unit_id=s.unit_id,
            provenance=provenance,
            command=s.command,
            status=args.status,
            exit_code=args.exit_code,
            duration_seconds=args.duration,
            artifacts=[
                __import__(
                    "runtime.foundation.verification.evidence_contract",
                    fromlist=["EvidenceArtifactRef"],
                ).EvidenceArtifactRef(
                    kind="report",
                    ref=args.report,
                )
            ],
        )
    artifact: ExecutionEvidenceV2 = execution_evidence_v2_from_plan(
        plan=plan,
        commit=args.commit or plan.head_ref,
        records=records,
    )
    save_execution_evidence_v2(artifact, args.out)
    print(json.dumps(artifact.to_dict(), indent=2))
    return 0


def cmd_deep_contract() -> int:
    """VEA-5 M6-B — emit the Deep tier ownership contract.

    Prints (and optionally writes) the machine-readable DEEP contract: the
    explicit, categorized ownership of functional / regression / test-effectiveness
    / UI / performance / security verification surfaces. DEEP answers
    "is the entire system still healthy?" — the complement of PR's
    "what does this change require?".

    Usage:
        python runtime/verify.py deep-contract
        python runtime/verify.py deep-contract --out runtime/generated/vea5-deep-contract.json
    """
    import argparse

    from runtime.foundation.verification.evidence_contract import (
        deep_contract_manifest,
    )

    parser = argparse.ArgumentParser(prog="verify.py deep-contract", add_help=False)
    parser.add_argument("--out", default=None, help="path to write the contract manifest")
    args, _ = parser.parse_known_args(sys.argv[2:])

    manifest = deep_contract_manifest()
    if args.out:
        p = Path(args.out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


def cmd_local_gate() -> int:
    """VEA-5 M8.3 — developer-side LOCAL plan artifact (pre-push closure).

    Emits the LOCAL TierPlan manifest from the developer's working-tree delta
    (staged + unstaged + untracked). It deliberately NEVER consults origin/main
    / merge-base (M2 invariant), so it cannot reintroduce branch-divergence
    contamination, regardless of how many unrelated files have diverged. It runs
    no verification and adds no CI cost — it is
    a cheap, inspectable artifact a developer can generate before push to see
    exactly what the PR gate will be required to verify.

    Usage:
        python runtime/verify.py local-gate
        python runtime/verify.py local-gate --out runtime/generated/vea5-tier-plan.local.json
    """
    import argparse

    from runtime.foundation.verification.tier import (
        MANIFEST_PATH,
        VerificationTier,
        plan_for_tier,
    )

    parser = argparse.ArgumentParser(prog="verify.py local-gate", add_help=False)
    parser.add_argument(
        "--out",
        default=str(MANIFEST_PATH).replace("vea5-tier-plan.json", "vea5-tier-plan.local.json"),
        help="path to write the LOCAL plan manifest",
    )
    parser.add_argument(
        "--changed", nargs="*", default=None,
        help="explicit changed files (bypass git; for tests)",
    )
    args, _ = parser.parse_known_args(sys.argv[2:])

    # M2 invariant: LOCAL never adopts a base ref, even if one is provided
    # incidentally. We pass explicit_base=None to guarantee no origin/main use.
    plan = plan_for_tier(
        VerificationTier.LOCAL,
        changed_files=args.changed,
        explicit_base=None,
        pr_base=None,
    )
    assert plan.base_ref is None, "LOCAL gate must never adopt a base ref"
    plan.write(Path(args.out))
    print(json.dumps(plan.to_dict(), indent=2, default=str))
    return 0


def cmd_dashboard() -> int:
    from runtime.system.observability.dashboard import DashboardGenerator

    generator = DashboardGenerator()
    dashboard = generator.generate()
    print(json.dumps(dashboard, indent=2, default=str))
    return 0


def cmd_intelligence() -> int:
    """Program 14.0 — run the Engineering Intelligence Layer."""
    from runtime.foundation.intelligence.platform.pipeline import run_intelligence

    allow_logs = "--logs" in sys.argv
    collect_ci = "--no-ci" not in sys.argv

    run = run_intelligence(collect_ci=collect_ci, allow_logs=allow_logs)

    print("Engineering Intelligence Layer")
    print(f"  Changed files:      {len(run.change.changeset.files)}")
    print(f"  Direct impact:      {len(run.blast.direct)}")
    print(f"  Indirect impact:    {len(run.blast.indirect)}")
    print(f"  Risk:               {run.risk.overall_level} "
          f"(score {run.risk.overall_score}, confidence {run.risk.confidence})")
    print(f"  Verification units: {len(run.plan.selected)} selected, "
          f"{len(run.plan.skipped)} skipped")
    print(f"  Estimated cost:     {run.plan.estimated_seconds}s "
          f"(baseline {run.plan.baseline_seconds}s)")
    print("\nArtifacts:")
    for path in run.written:
        print(f"  {path.relative_to(REPO_ROOT)}")
    return 0


def cmd_certify_v4() -> int:
    """Program 14.0 — Phase 10 production certification."""
    from runtime.foundation.intelligence.platform import certification

    result = certification.certify()
    output_json = REPO_ROOT / "runtime" / "generated" / "engineering-platform-audit-v4.json"
    output_md = REPO_ROOT / "runtime" / "generated" / "program14-certification.md"
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(result.to_dict(), indent=2, default=str) + "\n", encoding="utf-8"
    )
    output_md.write_text(certification.render_markdown(result), encoding="utf-8")

    for check in result.checks:
        print(f"  {check.id} {check.name}: {check.status.upper()}")
        if check.status != "pass":
            print(f"      {check.detail}")

    print(f"\nRuntime audit: {result.audit_status}")
    print(f"Program 14 certification: "
          f"{'CERTIFIED' if result.passed else 'NOT CERTIFIED'}")
    print(f"  {output_json.relative_to(REPO_ROOT)}")
    print(f"  {output_md.relative_to(REPO_ROOT)}")
    return 0 if result.passed else 1


def cmd_certify_v5() -> int:
    """Program 14.1 — eliminate legacy intelligence & complete migration."""
    from runtime.foundation.intelligence.platform import certification

    result = certification.certify_v5()

    for check in result["intelligence_checks"]:
        mark = "PASS" if check["status"] == "pass" else "FAIL"
        print(f"  {check['id']} {check['name']}: {mark}")
        if check["status"] != "pass":
            print(f"      {check['detail']}")

    print(f"\nRuntime audit: {result['runtime_audit']['certification_status']}")
    print(
        f"Program 14.1 certification: {result['certification_status']}"
    )
    print(f"  {REPO_ROOT / 'runtime/generated/engineering-platform-audit-v5.json'}")
    print(f"  {REPO_ROOT / 'runtime/generated/program14.1-certification.md'}")
    return 0 if result["certification_status"] == "CERTIFIED" else 1


def cmd_intelligence_audit() -> int:
    """Generate the Program 14.1 migration report artifacts."""
    from runtime.foundation.intelligence.platform.migration import (
        generate_migration_artifacts,
    )

    artifacts = generate_migration_artifacts()
    print("Program 14.1 migration reports generated:")
    for name in artifacts:
        path = REPO_ROOT / "runtime/generated" / name
        print(f"  {path.relative_to(REPO_ROOT)}")
    return 0


def cmd_api_contracts() -> int:
    """M9-C27 — API Contract Integrity & Drift-Proofing gate.

    Runs the canonical ``api-contracts`` capability: STRUCTURAL freshness,
    GENERATED-type reproducibility, CONSUMER integrity, and WIRE validation.
    Emits a machine-readable evidence artifact and exits non-zero on drift.
    """
    import json as _json

    from runtime.foundation.verification.api_contracts.gate import ApiContractGate

    gate = ApiContractGate()
    report = gate.run()

    evidence_path = (
        REPO_ROOT
        / "runtime"
        / "generated"
        / "api-contract-evidence.json"
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(
        _json.dumps(report.to_dict(), indent=2, default=str), encoding="utf-8"
    )

    # Human-readable summary
    print("=" * 72)
    print("  M9-C27 — API CONTRACT INTEGRITY GATE")
    print("=" * 72)
    print(f"  Run ID:              {report.run_id}")
    print(f"  Repo revision:      {report.repository_revision}")
    print(f"  OpenAPI hash:        {report.openapi_hash[:16]}")
    print(f"  Inventory hash:      {report.inventory.contract_inventory_hash}")
    print(f"  Backend operations:  {report.inventory.backend_operations}")
    print(f"  Frontend consumers:  {report.inventory.frontend_consumers}")
    print(f"  Runtime schemas:     {report.inventory.runtime_schemas}")
    print("-" * 72)
    for dim in report.dimensions:
        status = dim.status.upper()
        nfail = len(dim.failures)
        print(f"  {dim.name:<22} {status:<8} ({nfail} failures)")
    print("-" * 72)

    if report.failures:
        print(f"  TOTAL FAILURES: {len(report.failures)}")
        for f in report.failures[:20]:
            print(
                f"  [{f.classification.value}] {f.operation}\n"
                f"      expected: {f.expected}\n"
                f"      actual:   {f.actual}"
            )
    else:
        print("  ALL CONTRACT CHECKS PASSED")

    print("=" * 72)
    print(f"  Evidence: {evidence_path.relative_to(REPO_ROOT)}")
    print("=" * 72)

    return 0 if report.passed else 1


def cmd_contract_governance() -> int:
    """M9-C30 — Contract Governance & Enforcement Certification.

    Forensic certification that proves no reasonable future mutation can
    silently bypass the API contract gate. Covers:
      - Exhaustive mutation surface inventory
      - Gate attack with mutation matrix
      - Semantic blind spot analysis
      - Authority policy establishment
      - Artifact reproducibility verification
      - CI enforcement verification
    """
    from runtime.foundation.verification.api_contracts.c30_certification import main
    return main()


def cmd_audit() -> int:
    from runtime.foundation.audit.runner import AuditRunner
    from runtime.foundation.audit.reporter import AuditReporter
    from runtime.foundation.audit.repository import audit as _audit_repository
    from runtime.foundation.audit.cross_layer import audit as _audit_cross_layer
    from runtime.foundation.audit.dependency_graph import audit as _audit_dependency_graph
    from runtime.foundation.audit.planner import audit as _audit_planner
    from runtime.foundation.audit.executor import audit as _audit_executor
    from runtime.foundation.audit.evidence import audit as _audit_evidence
    from runtime.foundation.audit.observability import audit as _audit_observability
    from runtime.foundation.audit.knowledge import audit as _audit_knowledge
    from runtime.foundation.audit.workspace import audit as _audit_workspace
    from runtime.foundation.audit.integrity import audit as _audit_integrity
    from runtime.foundation.audit.github_actions import audit as _audit_github_actions
    from runtime.foundation.audit.runtime_cli import audit as _audit_runtime_cli
    from runtime.foundation.audit.github_runtime import audit as _audit_github_runtime
    from runtime.foundation.audit.verification_profiles import audit as _audit_verification_profiles
    from runtime.foundation.audit.artifact_ownership import audit as _audit_artifact_ownership
    from runtime.foundation.audit.performance import audit as _audit_performance
    from runtime.foundation.audit.failure_injection import audit as _audit_failure_injection
    from runtime.foundation.audit.pipeline import audit as _audit_pipeline
    from runtime.foundation.audit.roi import audit as _audit_roi

    runner = AuditRunner()

    runner.register("repository", lambda: _audit_repository())
    runner.register("cross_layer", lambda: _audit_cross_layer())
    runner.register("dependency_graph", lambda: _audit_dependency_graph())
    runner.register("planner", lambda: _audit_planner())
    runner.register("executor", lambda: _audit_executor())
    runner.register("evidence", lambda: _audit_evidence())
    runner.register("observability", lambda: _audit_observability())
    runner.register("knowledge", lambda: _audit_knowledge())
    runner.register("workspace", lambda: _audit_workspace())
    runner.register("integrity", lambda: _audit_integrity())
    runner.register("github_actions", lambda: _audit_github_actions())
    runner.register("runtime_cli", lambda: _audit_runtime_cli())
    runner.register("github_runtime", lambda: _audit_github_runtime())
    runner.register("verification_profiles", lambda: _audit_verification_profiles())
    runner.register("artifact_ownership", lambda: _audit_artifact_ownership())
    runner.register("performance", lambda: _audit_performance())
    runner.register("failure_injection", lambda: _audit_failure_injection())
    runner.register("pipeline", lambda: _audit_pipeline())
    runner.register("roi", lambda: _audit_roi())

    print("Running Engineering Platform Certification Audit...", file=sys.stderr)
    report = runner.run()
    reporter = AuditReporter(report)
    paths = reporter.save_all(REPO_ROOT)

    print(f"\nAudit Report: {paths['markdown']}")
    print(f"Certification: {report.certification_status}")
    print(f"Overall Status: {report.overall_status.value}")
    print(f"Duration: {report.total_duration_seconds:.2f}s")
    print(f"Critical Issues: {len(report.critical_issues)}")
    print(f"High Priority Issues: {len(report.high_priority_issues)}")
    print(f"Medium Priority Issues: {len(report.medium_priority_issues)}")
    print(f"Low Priority Issues: {len(report.low_priority_issues)}")

    for s in report.sections:
        print(f"  {s.name}: {s.status.value.upper()} ({s.duration_seconds:.2f}s)")

    if report.overall_status.value == "fail":
        print("\nAudit FAILED", file=sys.stderr)
        return 1

    if report.certification_status == "CERTIFIED":
        print("\nCertification achieved: CERTIFIED")
        return 0

    print("\nAudit PASSED with warnings")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: python runtime/verify.py <profile|command>",
            file=sys.stderr,
        )
        print(
            "Profiles: quick, backend, frontend, contracts, graph, full, runtime, golden, mutation, playwright",
            file=sys.stderr,
        )
        print(
            "Commands: status, metrics, history, deps, verify-status, analytics, health, doctor, ci-doctor, diagnose, diagnose-failures, plan, reconcile, exec-evidence, deep-contract, local-gate, affected, repair, risk, integrity, knowledge, knowledge endpoint, knowledge capability, knowledge workspace, knowledge rule, knowledge component, dashboard, intelligence, intelligence-audit, certify-v4, certify-v5, audit, api-contracts, contract-governance",
            file=sys.stderr,
        )
        return 1

    command = sys.argv[1]

    if command == "status":
        return cmd_status()
    if command == "metrics":
        return cmd_metrics()
    if command == "history":
        return cmd_history()
    if command == "deps":
        return cmd_deps()
    if command == "verify-status":
        return cmd_verify_status()
    if command == "analytics":
        return cmd_analytics()
    if command == "health":
        return cmd_health()
    if command == "doctor":
        return cmd_doctor()
    if command == "ci-doctor":
        return cmd_ci_doctor()
    if command == "diagnose":
        return cmd_diagnose()
    if command == "diagnose-failures":
        return cmd_diagnose_failures()
    if command == "plan":
        return cmd_plan()
    if command == "reconcile":
        return cmd_reconcile()
    if command == "exec-evidence":
        return cmd_exec_evidence()
    if command == "deep-contract":
        return cmd_deep_contract()
    if command == "local-gate":
        return cmd_local_gate()
    if command == "affected":
        return cmd_affected()
    if command == "repair":
        return cmd_repair()
    if command == "risk":
        return cmd_risk()
    if command == "integrity":
        return cmd_integrity()
    if command == "knowledge":
        sub_command = sys.argv[2] if len(sys.argv) > 2 else None
        if sub_command == "endpoint":
            return cmd_knowledge_endpoint()
        if sub_command == "capability":
            return cmd_knowledge_capability()
        if sub_command == "workspace":
            return cmd_knowledge_workspace()
        if sub_command == "rule":
            return cmd_knowledge_rule()
        if sub_command == "component":
            return cmd_knowledge_component()
        return cmd_knowledge()
    if command == "dashboard":
        return cmd_dashboard()
    if command == "intelligence":
        return cmd_intelligence()
    if command == "certify-v4":
        return cmd_certify_v4()
    if command == "certify-v5":
        return cmd_certify_v5()
    if command == "intelligence-audit":
        return cmd_intelligence_audit()
    if command == "audit":
        return cmd_audit()
    if command == "api-contracts":
        return cmd_api_contracts()
    if command == "contract-governance":
        return cmd_contract_governance()

    profile_name = command

    try:
        profile = get_profile(profile_name)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    commit = _get_current_commit()
    if _is_git_available():
        _cf_result = _collect_changed_files()
        changed_files = _cf_result.files
        _log_changed_files_boundary(_cf_result)
    else:
        changed_files = []

    if not changed_files and profile_name not in ("full", "graph"):
        import os
        in_ci = os.environ.get("CI") == "true" or os.environ.get("GITHUB_ACTIONS") == "true"
        if in_ci:
            print(
                "No changed files detected and git is unavailable in CI. "
                "Falling back to full verification profile.",
                file=sys.stderr,
            )
            profile_name = "full"
            profile = get_profile(profile_name)
        else:
            print(
                "No changed files detected and git is unavailable. "
                "Cannot run selective verification without a git working tree. "
                "Use 'full' or 'graph' profile for comprehensive verification, "
                "or run from a git repository.",
                file=sys.stderr,
            )
            return 1

    from runtime.foundation.verification.cache import (
        CachedVerdict,
        ReplayResult,
        VerificationCache,
    )

    cache = VerificationCache(VERIFICATION_CACHE_PATH)
    replay: ReplayResult = cache.replay(commit, changed_files, profile_name)

    if replay.reusable:
        verdict_status = replay.overall_status or "unknown"
        print(
            f"Cache hit for profile '{profile_name}' "
            f"(commit: {commit[:8]}). Replaying stored verdict: "
            f"{verdict_status.upper()}",
            file=sys.stderr,
        )
        # Record the cache-hit observation (D-05): cache_hit=true is persisted in
        # the event/metrics store even though no fresh verification was executed.
        _record_verification_event(
            None,
            profile_name,
            0.0,
            cache_hit=True,
            status=verdict_status,
        )
        if verdict_status == "fail":
            print("\nVerification FAILED (cached)", file=sys.stderr)
            return 1
        print("\nVerification PASSED (cached)")
        return 0

    print(
        f"Running verification profile: {profile_name}",
        file=sys.stderr,
    )
    print(f"Changed files: {len(changed_files)}", file=sys.stderr)

    # M9-C8 (observable logs): stream every subprocess output line to stdout so
    # the CI log shows Playwright progress in real time instead of appearing
    # hung. The Executor tees each line through this callback as it is produced.
    def _stream_log(line: str) -> None:
        print(line, end="", flush=True)

    # M9-C8 (bounded runtime): the per-project Playwright job is sharded across a
    # matrix, so each bash step may run one full project (232 tests). Give the
    # step a 90-minute ceiling that matches the GitHub job window so a long but
    # legitimate run is never killed prematurely by the executor.
    orchestrator = VerificationOrchestrator(
        profile=profile,
        log_callback=_stream_log,
        per_step_timeout=5400,
    )

    import time

    start_time = time.monotonic()
    try:
        report = orchestrator.run(scope=profile.scope)
    except RuntimeError as exc:
        # M9-C3: a boundary that could not be resolved (e.g. PR event without
        # SHAs) must fail loudly, never fall back to a misleading scope.
        print(f"\nVerification ABORTED: {exc}", file=sys.stderr)
        return 2
    elapsed = time.monotonic() - start_time

    report_path = VERIFICATION_REPORT_PATH
    report.save_markdown(report_path)

    overall = (
        "pass"
        if report.summary.overall_status == VerificationStatus.PASSED
        else "fail"
    )
    unit_statuses = tuple(
        (r.unit_id or "UNMAPPED", r.status.value)
        for r in report.results
        if r.unit_id
    )
    verdict = CachedVerdict(
        overall_status=overall,
        passed=report.summary.passed,
        failed=report.summary.failed,
        skipped=report.summary.skipped,
        unit_statuses=unit_statuses,
    )
    cache.save(profile_name, commit, changed_files, verdict, elapsed)
    _record_verification_event(report, profile_name, elapsed, cache_hit=False)

    print(f"\nVerification Report: {report_path}")
    print(f"Profile: {report.profile}")
    print(f"Passed: {report.summary.passed}")
    print(f"Failed: {report.summary.failed}")
    print(f"Skipped: {report.summary.skipped}")
    print(f"Duration: {elapsed:.1f}s")

    # P2-1 / M9-C3: surface an actionable failure summary on the console (in
    # addition to the markdown report) so the failed unit, classification, exit
    # code, test result, root failure and evidence location are visible without
    # opening the artifact files. Aggregate counts are preserved above.
    failed_results = [r for r in report.results if r.status.value == "failed"]
    if failed_results:
        print("\nFailed tasks:")
        for r in failed_results:
            try:
                fr = build_failure_report(r)
            except Exception:
                # Reporting must never convert a verification failure into a pass.
                fr = None
            if fr is None:
                raw_error = r.error
                reason_str = (
                    "(none)"
                    if raw_error is None
                    else ("[empty stderr]" if raw_error == "" else raw_error.replace("\n", " ").strip()[:300])
                )
                print(f"  - {r.task_id}: exit={r.exit_code} reason={reason_str}")
                if r.stderr_path:
                    print(f"      stderr: {r.stderr_path}")
                continue
            print(f"  - {r.task_id}")
            if fr.unit_id:
                print(f"      unit:   {fr.unit_id}")
            print(f"      classification: {fr.classification.value}")
            print(f"      exit:   {fr.exit_code}")
            if fr.failure_summary:
                print(f"      result: {fr.failure_summary}")
            if fr.root_failure:
                print(f"      failure:{fr.root_failure}")
            if fr.diagnostic:
                diag = fr.diagnostic.replace("\n", " ").strip()
                if len(diag) > 300:
                    diag = diag[:297] + "..."
                print(f"      reason: {diag}")
            print(f"      evidence: {fr.evidence_path}")

    if report.summary.overall_status == VerificationStatus.FAILED:
        print("\nVerification FAILED", file=sys.stderr)
        return 1

    print("\nVerification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())