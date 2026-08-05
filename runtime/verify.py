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


def main() -> int:
    if len(sys.argv) < 2:
        print(
            "Usage: python runtime/verify.py <profile>",
            file=sys.stderr,
        )
        print(
            "Profiles: quick, backend, frontend, contracts, graph, full",
            file=sys.stderr,
        )
        return 1

    profile_name = sys.argv[1]

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
            "Commands: status, metrics, history, deps, verify-status, analytics, health, diagnose, affected, repair, risk, integrity, knowledge, knowledge endpoint, knowledge capability, knowledge workspace, knowledge rule, knowledge component",
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