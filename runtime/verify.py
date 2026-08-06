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
import sys
from pathlib import Path

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

VERIFICATION_CACHE_PATH = REPO_ROOT / "runtime" / "generated" / "verification-cache.json"
VERIFICATION_REPORT_PATH = REPO_ROOT / "runtime" / "generated" / "verification-report.md"


def _load_cache() -> dict:
    if VERIFICATION_CACHE_PATH.exists():
        try:
            with open(VERIFICATION_CACHE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {
        "last_commit": "",
        "changed_files": [],
        "executed_profiles": [],
        "duration": 0,
        "timestamp": "",
    }


def _save_cache(data: dict) -> None:
    VERIFICATION_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(VERIFICATION_CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def _is_cache_valid(profile_name: str, changed_files: list[str], commit: str) -> bool:
    cache = _load_cache()
    return (
        cache.get("last_commit") == commit
        and cache.get("changed_files") == changed_files
        and profile_name in cache.get("executed_profiles", [])
    )


def _update_cache(profile_name: str, changed_files: list[str], commit: str, duration: float) -> None:
    cache = _load_cache()
    cache["last_commit"] = commit
    cache["changed_files"] = changed_files
    if "executed_profiles" not in cache:
        cache["executed_profiles"] = []
    if profile_name not in cache["executed_profiles"]:
        cache["executed_profiles"].append(profile_name)
    cache["duration"] = duration
    cache["timestamp"] = __import__("datetime").datetime.now(
        tz=__import__("datetime").timezone.utc
    ).isoformat()
    _save_cache(cache)


def _record_verification_event(report: Any, profile_name: str, elapsed: float) -> None:
    try:
        from runtime.system.observability.execution_context import create_context
        from runtime.system.observability.event_store import create_event, EngineeringEventStore
        from runtime.system.observability.repository import LocalMetricsRepository, RunRecord

        ctx = create_context()
        event_store = EngineeringEventStore()
        event = create_event(
            event_type="VerificationCompleted",
            execution_context=ctx.to_dict(),
            payload={
                "profile": profile_name,
                "status": report.summary.overall_status.value,
                "passed": report.summary.passed,
                "failed": report.summary.failed,
                "skipped": report.summary.skipped,
                "duration_seconds": elapsed,
                "blast_radius": report.blast_radius,
                "evidence_count": len(report.evidence_files),
                "cache_hit": False,
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
                status=report.summary.overall_status.value,
                passed=report.summary.passed,
                failed=report.summary.failed,
                skipped=report.summary.skipped,
                duration_seconds=elapsed,
                blast_radius=report.blast_radius,
                evidence_count=len(report.evidence_files),
                cache_hit=False,
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
    from runtime.system.observability.health_report import EngineeringHealthReport

    report = EngineeringHealthReport()
    output = report.generate()
    print(output)
    return 0


def cmd_diagnose() -> int:
    from runtime.foundation.intelligence.diagnostics import DeveloperDiagnostics
    from runtime.foundation.intelligence.formatter import format_diagnostic_report

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    diagnostics = DeveloperDiagnostics()
    report = diagnostics.diagnose(changed_files)
    output = format_diagnostic_report(report)
    print(output)
    return 0


def cmd_affected() -> int:
    from runtime.foundation.intelligence.affected import AffectedTestPlanner
    from runtime.foundation.intelligence.formatter import format_affected_test_plan

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    planner = AffectedTestPlanner()
    plan = planner.build_test_plan(changed_files)
    output = format_affected_test_plan(plan)
    print(output)
    return 0


def cmd_repair() -> int:
    from runtime.foundation.intelligence.diagnostics import DeveloperDiagnostics
    from runtime.foundation.intelligence.formatter import format_repair_suggestions

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    diagnostics = DeveloperDiagnostics()
    report = diagnostics.diagnose(changed_files)
    output = format_repair_suggestions(report.repair_suggestions)
    print(output)
    return 0


def cmd_risk() -> int:
    from runtime.foundation.intelligence.diagnostics import DeveloperDiagnostics
    from runtime.foundation.intelligence.formatter import format_risk_report
    from runtime.foundation.intelligence.risk import RiskAnalyzer

    changed_files = _collect_changed_files() if _is_git_available() else []
    if not changed_files:
        print("No changed files detected.", file=sys.stderr)
        return 1

    diagnostics = DeveloperDiagnostics()
    diagnostic_report = diagnostics.diagnose(changed_files)
    risk_report = RiskAnalyzer().analyze(diagnostic_report)
    output = format_risk_report(risk_report)
    print(output)
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
    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.query import query_endpoint
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge endpoint <path>", file=sys.stderr)
        return 1

    path = sys.argv[3]
    index = build_index()
    result = query_endpoint(path)
    if result is None:
        print(f"No endpoint found for path: {path}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_capability() -> int:
    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.query import query_capability
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge capability <name>", file=sys.stderr)
        return 1

    name = sys.argv[3]
    index = build_index()
    result = query_capability(name)
    if result is None:
        print(f"No capability found for name: {name}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_workspace() -> int:
    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.query import query_workspace
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge workspace <name>", file=sys.stderr)
        return 1

    name = sys.argv[3]
    index = build_index()
    result = query_workspace(name)
    if result is None:
        print(f"No workspace found for name: {name}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_rule() -> int:
    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.query import query_rule
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge rule <id>", file=sys.stderr)
        return 1

    rule_id = sys.argv[3]
    index = build_index()
    result = query_rule(rule_id)
    if result is None:
        print(f"No rule found for id: {rule_id}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_knowledge_component() -> int:
    from runtime.foundation.knowledge.indexer import build_index
    from runtime.foundation.knowledge.query import query_component
    from runtime.foundation.knowledge.formatter import format_query_result

    if len(sys.argv) < 4:
        print("Usage: python runtime/verify.py knowledge component <name>", file=sys.stderr)
        return 1

    name = sys.argv[3]
    index = build_index()
    result = query_component(name)
    if result is None:
        print(f"No component found for name: {name}", file=sys.stderr)
        return 1
    output = format_query_result(result)
    print(output)
    return 0


def cmd_dashboard() -> int:
    from runtime.system.observability.dashboard import DashboardGenerator

    generator = DashboardGenerator()
    dashboard = generator.generate()
    print(json.dumps(dashboard, indent=2, default=str))
    return 0


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
            "Commands: status, metrics, history, deps, verify-status, analytics, health, doctor, ci-doctor, diagnose, affected, repair, risk, integrity, knowledge, knowledge endpoint, knowledge capability, knowledge workspace, knowledge rule, knowledge component, dashboard, audit",
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
    if command == "audit":
        return cmd_audit()

    profile_name = command

    try:
        profile = get_profile(profile_name)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    commit = _get_current_commit()
    changed_files = _collect_changed_files() if _is_git_available() else []

    if not changed_files and profile_name not in ("full", "graph"):
        print(
            "No changed files detected and git is unavailable. "
            "Falling back to FULL verification profile.",
            file=sys.stderr,
        )
        profile = get_profile("full")

    if _is_cache_valid(profile_name, changed_files, commit):
        print(
            f"Cache hit for profile '{profile_name}' "
            f"(commit: {commit[:8]}). Reusing previous plan.",
            file=sys.stderr,
        )
    else:
        print(
            f"Running verification profile: {profile_name}",
            file=sys.stderr,
        )
        print(f"Changed files: {len(changed_files)}", file=sys.stderr)

    orchestrator = VerificationOrchestrator(profile=profile)

    import time

    start_time = time.monotonic()
    report = orchestrator.run(scope=profile.scope)
    elapsed = time.monotonic() - start_time

    report_path = VERIFICATION_REPORT_PATH
    report.save_markdown(report_path)

    _update_cache(profile_name, changed_files, commit, elapsed)
    _record_verification_event(report, profile_name, elapsed)

    print(f"\nVerification Report: {report_path}")
    print(f"Profile: {report.profile}")
    print(f"Passed: {report.summary.passed}")
    print(f"Failed: {report.summary.failed}")
    print(f"Skipped: {report.summary.skipped}")
    print(f"Duration: {elapsed:.1f}s")

    if report.summary.overall_status == VerificationStatus.FAILED:
        print("\nVerification FAILED", file=sys.stderr)
        return 1

    print("\nVerification PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())