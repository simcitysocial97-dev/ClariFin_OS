"""Verification Profiles Audit — Program 12.

Audits verification profiles for expected vs actual tests,
missed tests, unexpected tests, duration estimates, cache behavior,
planner correctness, and artifacts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    from runtime.foundation.verification.profiles import list_profiles

    profiles = list_profiles()
    metrics["total_profiles"] = len(profiles)

    expected_tests = _build_expected_tests()
    actual_tests = _collect_actual_tests(profiles)

    missed = _find_missed_tests(expected_tests, actual_tests)
    unexpected = _find_unexpected_tests(expected_tests, actual_tests)

    for test_id in missed:
        findings.append(
            _finding(
                "verification_profiles",
                "VP-001",
                f"Missed test: {test_id}",
                "fail",
                "high",
                f"Expected test {test_id} is not present in any profile",
                {"test_id": test_id, "expected_in": expected_tests[test_id].get("profile", "unknown")},
                f"Add {test_id} to the appropriate verification profile",
            )
        )

    for test_id in unexpected:
        findings.append(
            _finding(
                "verification_profiles",
                "VP-002",
                f"Unexpected test: {test_id}",
                "warning",
                "medium",
                f"Test {test_id} exists but is not in the expected test set",
                {"test_id": test_id, "actual_profile": actual_tests[test_id].get("profile", "unknown")},
                "Review whether this test should be in the expected set or remove it",
            )
        )

    duration_check = _check_duration_estimates(profiles)
    findings.extend(duration_check["findings"])
    metrics.update(duration_check["metrics"])

    cache_check = _check_cache_behavior(repo_root)
    findings.extend(cache_check["findings"])
    metrics.update(cache_check["metrics"])

    planner_check = _check_planner_correctness(repo_root)
    findings.extend(planner_check["findings"])
    metrics.update(planner_check["metrics"])

    artifact_check = _check_profile_artifacts(repo_root)
    findings.extend(artifact_check["findings"])
    metrics.update(artifact_check["metrics"])

    duplicate_check = _check_duplicate_tasks(profiles)
    findings.extend(duplicate_check["findings"])
    metrics.update(duplicate_check["metrics"])

    status = "pass" if all(f["status"] == "pass" for f in findings) else "fail"
    duration = time.monotonic() - start

    return {
        "section": "verification_profiles",
        "name": "Verification Profiles Audit",
        "status": status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 3),
    }


def _build_expected_tests() -> dict[str, dict[str, Any]]:
    return {
        "quick-ruff": {"profile": "quick", "category": "capability"},
        "quick-mypy": {"profile": "quick", "category": "capability"},
        "quick-unit": {"profile": "quick", "category": "capability"},
        "backend-ruff": {"profile": "backend", "category": "capability"},
        "backend-mypy": {"profile": "backend", "category": "capability"},
        "backend-unit": {"profile": "backend", "category": "capability"},
        "backend-integration": {"profile": "backend", "category": "integration"},
        "backend-schemathesis": {"profile": "backend", "category": "contract"},
        "backend-aggregate": {"profile": "backend", "category": "capability"},
        "frontend-lint": {"profile": "frontend", "category": "capability"},
        "frontend-typecheck": {"profile": "frontend", "category": "capability"},
        "frontend-unit": {"profile": "frontend", "category": "capability"},
        "frontend-build": {"profile": "frontend", "category": "capability"},
        "frontend-aggregate": {"profile": "frontend", "category": "capability"},
        "contracts-schemathesis": {"profile": "contracts", "category": "contract"},
        "contracts-backend-unit": {"profile": "contracts", "category": "contract"},
        "contracts-aggregate": {"profile": "contracts", "category": "capability"},
        "graph-integrity": {"profile": "graph", "category": "architectural"},
        "graph-cross-layer": {"profile": "graph", "category": "architectural"},
        "graph-aggregate": {"profile": "graph", "category": "capability"},
        "full-ruff": {"profile": "full", "category": "capability"},
        "full-mypy": {"profile": "full", "category": "capability"},
        "full-backend-unit": {"profile": "full", "category": "capability"},
        "full-backend-integration": {"profile": "full", "category": "integration"},
        "full-schemathesis": {"profile": "full", "category": "contract"},
        "full-frontend-lint": {"profile": "full", "category": "capability"},
        "full-frontend-typecheck": {"profile": "full", "category": "capability"},
        "full-frontend-unit": {"profile": "full", "category": "capability"},
        "full-frontend-build": {"profile": "full", "category": "capability"},
        "full-graph": {"profile": "full", "category": "architectural"},
        "full-aggregate": {"profile": "full", "category": "capability"},
        "mutation-run": {"profile": "mutation", "category": "mutation"},
        "mutation-aggregate": {"profile": "mutation", "category": "mutation"},
        "runtime-self-test": {"profile": "runtime", "category": "architectural"},
        "runtime-aggregate": {"profile": "runtime", "category": "architectural"},
        "golden-regression": {"profile": "golden", "category": "capability"},
        "golden-aggregate": {"profile": "golden", "category": "capability"},
        "playwright-e2e": {"profile": "playwright", "category": "integration"},
        "playwright-aggregate": {"profile": "playwright", "category": "integration"},
    }


def _collect_actual_tests(profiles: tuple[Any, ...]) -> dict[str, dict[str, Any]]:
    actual: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        for task in profile.tasks:
            actual[task.id] = {
                "profile": profile.name,
                "name": task.name,
                "category": task.category.value,
                "command_count": len(task.commands),
                "estimated_duration_seconds": task.estimated_duration_seconds,
            }
    return actual


def _find_missed_tests(
    expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
) -> list[str]:
    return [tid for tid in expected if tid not in actual]


def _find_unexpected_tests(
    expected: dict[str, dict[str, Any]], actual: dict[str, dict[str, Any]]
) -> list[str]:
    return [tid for tid in actual if tid not in expected]


def _check_duration_estimates(profiles: tuple[Any, ...]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    total_estimated = 0

    for profile in profiles:
        profile_total = 0
        for task in profile.tasks:
            est = task.estimated_duration_seconds
            total_estimated += est
            profile_total += est
            if est <= 0:
                findings.append(
                    _finding(
                        "verification_profiles",
                        "VP-003",
                        f"Task {task.id} has invalid duration estimate",
                        "fail",
                        "medium",
                        f"Task {task.id} in profile {profile.name} has estimated_duration_seconds={est}, expected > 0",
                        {"task_id": task.id, "profile": profile.name, "estimated_duration_seconds": est},
                        f"Set a positive estimated duration for {task.id}",
                    )
                )
        metrics[f"{profile.name}_total_estimated_seconds"] = profile_total

    metrics["total_estimated_seconds_all_profiles"] = total_estimated

    if not findings:
        findings.append(
            _finding(
                "verification_profiles",
                "VP-004",
                "All duration estimates are valid",
                "pass",
                "info",
                f"All {sum(len(p.tasks) for p in profiles)} tasks across {len(profiles)} profiles have positive duration estimates",
                {},
                "Review duration estimates periodically as tasks evolve",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_cache_behavior(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    cache_path = repo_root / "runtime" / "generated" / "verification-cache.json"
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            metrics["cache_last_commit"] = data.get("last_commit", "")[:8]
            metrics["cache_changed_files_count"] = len(data.get("changed_files", []))
            metrics["cache_executed_profiles"] = data.get("executed_profiles", [])
            metrics["cache_has_data"] = True
        except Exception:
            metrics["cache_has_data"] = False
            findings.append(
                _finding(
                    "verification_profiles",
                    "VP-005",
                    "Verification cache is corrupted",
                    "fail",
                    "medium",
                    "The verification-cache.json file exists but cannot be parsed",
                    {"path": str(cache_path)},
                    "Regenerate the verification cache by running a fresh verification",
                )
            )
    else:
        metrics["cache_has_data"] = False
        findings.append(
            _finding(
                "verification_profiles",
                "VP-006",
                "Verification cache does not exist",
                "warning",
                "low",
                "No verification-cache.json found; caching is not active",
                {"path": str(cache_path)},
                "Ensure verification cache is generated during CI runs",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_planner_correctness(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:
        from runtime.foundation.verification.planner.planner import VerificationPlanner
        from runtime.foundation.verification.planner.planner import PlanningContext
        from runtime.foundation.verification.models import VerificationScope

        planner = VerificationPlanner()
        context = PlanningContext(
            changed_files=[],
            requested_scope=VerificationScope.QUICK,
            force_scope=VerificationScope.QUICK,
            include_dependencies=True,
            max_depth=3,
        )

        plan = planner.plan(context)
        metrics["planner_generated_plan_id"] = plan.id
        metrics["planner_scope"] = plan.scope.value
        metrics["planner_target_count"] = len(plan.targets)
        metrics["planner_step_count"] = len(plan.steps)
        metrics["planner_estimated_duration"] = plan.estimated_duration_seconds

        if len(plan.steps) == 0:
            findings.append(
                _finding(
                    "verification_profiles",
                    "VP-007",
                    "Planner produced zero steps",
                    "fail",
                    "critical",
                    "The verification planner generated a plan with no execution steps",
                    {"plan_id": plan.id, "scope": plan.scope.value},
                    "Investigate why the planner produced no steps for the quick scope",
                )
            )

        if plan.estimated_duration_seconds < 0:
            findings.append(
                _finding(
                    "verification_profiles",
                    "VP-008",
                    "Planner produced negative duration estimate",
                    "fail",
                    "high",
                    f"Planner estimated duration is {plan.estimated_duration_seconds}s, expected non-negative",
                    {"estimated_duration_seconds": plan.estimated_duration_seconds},
                    "Fix duration calculation in the planner",
                )
            )

        if not findings:
            findings.append(
                _finding(
                    "verification_profiles",
                    "VP-009",
                    "Planner correctness verified",
                    "pass",
                    "info",
                    f"Planner generated a valid plan with {len(plan.steps)} steps and {len(plan.targets)} targets",
                    {"plan_id": plan.id, "step_count": len(plan.steps), "target_count": len(plan.targets)},
                    "Continue monitoring planner output for correctness",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "verification_profiles",
                "VP-010",
                "Planner correctness check failed",
                "fail",
                "critical",
                f"Failed to run planner correctness check: {exc}",
                {"error": str(exc)},
                "Fix the planner module and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_profile_artifacts(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    artifact_files = [
        "cross-layer-map.json",
        "knowledge-index.json",
        "verification-cache.json",
        "engineering-history.json",
        "verification-report.md",
        "dashboard.json",
    ]

    for artifact in artifact_files:
        path = repo_root / "runtime" / "generated" / artifact
        exists = path.exists()
        metrics[f"artifact_{artifact}_exists"] = exists
        if not exists:
            findings.append(
                _finding(
                    "verification_profiles",
                    "VP-011",
                    f"Expected artifact missing: {artifact}",
                    "warning",
                    "medium",
                    f"Expected artifact {artifact} does not exist in runtime/generated/",
                    {"artifact": artifact, "path": str(path)},
                    f"Ensure {artifact} is generated during verification runs",
                )
            )

    if not any(f["check_id"] == "VP-011" for f in findings):
        findings.append(
            _finding(
                "verification_profiles",
                "VP-012",
                "All expected profile artifacts present",
                "pass",
                "info",
                f"All {len(artifact_files)} expected artifacts exist in runtime/generated/",
                {},
                "Continue generating all expected artifacts during verification",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _check_duplicate_tasks(profiles: tuple[Any, ...]) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    seen_ids: dict[str, str] = {}
    duplicates: list[str] = []

    for profile in profiles:
        for task in profile.tasks:
            if task.id in seen_ids:
                duplicates.append(task.id)
                findings.append(
                    _finding(
                        "verification_profiles",
                        "VP-013",
                        f"Duplicate task ID: {task.id}",
                        "fail",
                        "high",
                        f"Task ID {task.id} appears in both profile {seen_ids[task.id]} and profile {profile.name}",
                        {"task_id": task.id, "profile_1": seen_ids[task.id], "profile_2": profile.name},
                        f"Remove or rename the duplicate task {task.id}",
                    )
                )
            else:
                seen_ids[task.id] = profile.name

    metrics["unique_task_ids"] = len(seen_ids)
    metrics["duplicate_task_ids"] = len(duplicates)

    if not duplicates:
        findings.append(
            _finding(
                "verification_profiles",
                "VP-014",
                "No duplicate task IDs found",
                "pass",
                "info",
                f"All {len(seen_ids)} task IDs across {len(profiles)} profiles are unique",
                {},
                "Continue ensuring task ID uniqueness across profiles",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _finding(
    section: str,
    check_id: str,
    name: str,
    status: str,
    severity: str,
    message: str,
    details: dict[str, Any],
    recommendation: str,
) -> dict[str, Any]:
    return {
        "section": section,
        "check_id": check_id,
        "name": name,
        "status": status,
        "severity": severity,
        "priority": _severity_to_priority(severity),
        "message": message,
        "details": details,
        "recommendation": recommendation,
    }


def _severity_to_priority(severity: str) -> str:
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low",
    }
    return mapping.get(severity, "low")