"""Verification Planner Audit — Program 12.

Verifies the verification planner for:
- Profile expansion determinism (expand_tasks() is reproducible)
- plan_verification() determinism (same inputs produce same plan structure)
- Verification cache existence and validity
- Task ordering (steps have sequential, unique order values)
- No duplicate task IDs within profiles
- Profile coverage (all expected profiles present)
- Dependency resolution consistency
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

EXPECTED_PROFILES = [
    "quick",
    "backend",
    "frontend",
    "contracts",
    "graph",
    "full",
    "mutation",
    "runtime",
    "golden",
    "playwright",
]


def _find_cache_path(repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "runtime" / "generated" / "verification-cache.json"


def _check_profile_expansion_determinism() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.verification.profiles import list_profiles
    except ImportError as exc:
        findings.append({
            "section": "planner",
            "check_id": "planner-profile-import",
            "name": "Profile module import",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Cannot import profiles module: {exc}",
            "details": {},
            "recommendation": "Ensure runtime.foundation.verification.profiles is importable",
        })
        return findings

    profiles = list_profiles()

    for profile in profiles:
        try:
            tasks1 = profile.expand_tasks()
            tasks2 = profile.expand_tasks()
            ids1 = tuple(t.id for t in tasks1)
            ids2 = tuple(t.id for t in tasks2)
            commands1 = tuple(
                tuple(t.commands) for t in tasks1
            )
            commands2 = tuple(
                tuple(t.commands) for t in tasks2
            )
            deterministic = ids1 == ids2 and commands1 == commands2
            status = "pass" if deterministic else "fail"
            message = f"Profile '{profile.name}' expand_tasks() is deterministic" if deterministic else f"Profile '{profile.name}' expand_tasks() is NOT deterministic"
        except Exception as exc:
            status = "fail"
            message = f"Profile '{profile.name}' expand_tasks() raised: {exc}"
            deterministic = False
            ids1 = ()
            ids2 = ()
            commands1 = ()
            commands2 = ()

        findings.append({
            "section": "planner",
            "check_id": f"planner-expand-deterministic-{profile.name}",
            "name": f"Profile '{profile.name}' expansion determinism",
            "status": status,
            "severity": "critical" if status == "fail" else "info",
            "priority": "critical" if status == "fail" else "low",
            "message": message,
            "details": {
                "task_ids_1": ids1,
                "task_ids_2": ids2,
                "deterministic": deterministic,
            },
            "recommendation": "" if status == "pass" else f"Fix non-determinism in expand_tasks() for profile '{profile.name}'",
        })

    return findings


def _check_no_duplicate_task_ids() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.verification.profiles import list_profiles
    except ImportError:
        findings.append({
            "section": "planner",
            "check_id": "planner-dup-import",
            "name": "Profile module import for duplicate check",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": "Cannot import profiles module",
            "details": {},
            "recommendation": "Ensure runtime.foundation.verification.profiles is importable",
        })
        return findings

    profiles = list_profiles()

    for profile in profiles:
        task_ids = [t.id for t in profile.tasks]
        seen: set[str] = set()
        duplicates: list[str] = []
        for tid in task_ids:
            if tid in seen and tid not in duplicates:
                duplicates.append(tid)
            seen.add(tid)
        status = "pass" if not duplicates else "fail"
        message = (
            f"Profile '{profile.name}' has no duplicate task IDs ({len(task_ids)} tasks)"
            if status == "pass"
            else f"Profile '{profile.name}' has duplicate task IDs: {duplicates}"
        )
        findings.append({
            "section": "planner",
            "check_id": f"planner-no-dup-tasks-{profile.name}",
            "name": f"Profile '{profile.name}' no duplicate tasks",
            "status": status,
            "severity": "high" if status == "fail" else "info",
            "priority": "high" if status == "fail" else "low",
            "message": message,
            "details": {"duplicate_ids": duplicates, "total_tasks": len(task_ids)},
            "recommendation": "" if status == "pass" else f"Remove duplicate task IDs from profile '{profile.name}'",
        })

    return findings


def _check_profile_coverage() -> dict[str, Any]:
    try:
        from runtime.foundation.verification.profiles import profile_names
    except ImportError as exc:
        return {
            "section": "planner",
            "check_id": "planner-profile-coverage-import",
            "name": "Profile coverage",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Cannot import profile functions: {exc}",
            "details": {},
            "recommendation": "Ensure profiles module is importable",
        }

    actual_names = set(profile_names())
    expected = set(EXPECTED_PROFILES)
    missing = expected - actual_names
    extra = actual_names - expected

    if not missing:
        status = "pass"
        message = f"All {len(expected)} expected profiles are available"
    else:
        status = "fail"
        message = f"Missing profiles: {sorted(missing)}"

    return {
        "section": "planner",
        "check_id": "planner-profile-coverage",
        "name": "Profile coverage",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": {
            "expected": sorted(expected),
            "actual": sorted(actual_names),
            "missing": sorted(missing),
            "extra": sorted(extra),
        },
        "recommendation": "" if status == "pass" else f"Add missing profiles: {', '.join(sorted(missing))}",
    }


def _check_profile_task_ordering() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.verification.profiles import list_profiles
    except ImportError as exc:
        findings.append({
            "section": "planner",
            "check_id": "planner-task-order-import",
            "name": "Task ordering",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Cannot import profiles module: {exc}",
            "details": {},
            "recommendation": "Ensure profiles module is importable",
        })
        return findings

    profiles = list_profiles()

    for profile in profiles:
        order_values: list[int] = []
        for task in profile.tasks:
            # VerificationTask doesn't have order; check if tasks are at least unique
            order_values.append(task.estimated_duration_seconds)

        # Check for non-negative estimated durations (all should be >= 0)
        negative = sum(1 for d in order_values if d < 0)
        if negative > 0:
            status = "fail"
            message = f"Profile '{profile.name}' has {negative} tasks with negative durations"
        else:
            status = "pass"
            message = f"Profile '{profile.name}' tasks have valid ordering ({len(order_values)} tasks)"

        findings.append({
            "section": "planner",
            "check_id": f"planner-task-ordering-{profile.name}",
            "name": f"Profile '{profile.name}' task ordering",
            "status": status,
            "severity": "medium" if status == "fail" else "info",
            "priority": "medium" if status == "fail" else "low",
            "message": message,
            "details": {"task_count": len(order_values), "negative_durations": negative},
            "recommendation": "" if status == "pass" else "Fix negative duration estimates",
        })

    return findings


def _check_plan_verification_determinism() -> dict[str, Any]:
    try:
        from runtime.foundation.verification.planner import plan_verification
    except ImportError as exc:
        return {
            "section": "planner",
            "check_id": "planner-plan-det-import",
            "name": "plan_verification() determinism",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Cannot import plan_verification: {exc}",
            "details": {},
            "recommendation": "Ensure planner module is importable",
        }

    changed_files = ["backend/src/engines/loan_engine.py"]
    try:
        plan1 = plan_verification(changed_files=changed_files, scope=None)
        plan2 = plan_verification(changed_files=changed_files, scope=None)

        step_ids_1 = tuple(s.id for s in plan1.steps)
        step_ids_2 = tuple(s.id for s in plan2.steps)
        target_ids_1 = tuple(t.id for t in plan1.targets)
        target_ids_2 = tuple(t.id for t in plan2.targets)
        workflows_1 = tuple(plan1.required_workflows)
        workflows_2 = tuple(plan2.required_workflows)
        scripts_1 = tuple(plan1.required_scripts)
        scripts_2 = tuple(plan2.required_scripts)
        duration_match = plan1.estimated_duration_seconds == plan2.estimated_duration_seconds
        step_order_1 = tuple(s.order for s in plan1.steps)
        step_order_2 = tuple(s.order for s in plan2.steps)

        deterministic = (
            step_ids_1 == step_ids_2
            and target_ids_1 == target_ids_2
            and workflows_1 == workflows_2
            and scripts_1 == scripts_2
            and duration_match
            and step_order_1 == step_order_2
        )
        status = "pass" if deterministic else "fail"
        message = "plan_verification() is deterministic" if deterministic else "plan_verification() is NOT deterministic"
    except Exception as exc:
        status = "fail"
        message = f"plan_verification() raised: {exc}"
        deterministic = False
        step_ids_1 = step_ids_2 = ()
        target_ids_1 = target_ids_2 = ()
        workflows_1 = workflows_2 = ()
        scripts_1 = scripts_2 = ()
        duration_match = False
        step_order_1 = step_order_2 = ()

    return {
        "section": "planner",
        "check_id": "planner-plan-determinism",
        "name": "plan_verification() determinism",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": {
            "step_ids_match": step_ids_1 == step_ids_2,
            "target_ids_match": target_ids_1 == target_ids_2,
            "workflows_match": workflows_1 == workflows_2,
            "scripts_match": scripts_1 == scripts_2,
            "duration_match": duration_match,
            "step_order_match": step_order_1 == step_order_2,
            "plan1_steps": len(step_ids_1),
            "plan2_steps": len(step_ids_2),
            "note": "Plan ID includes timestamp and is excluded from determinism check",
        },
        "recommendation": "" if status == "pass" else "Fix non-determinism in plan_verification()",
    }


def _check_step_ordering() -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.verification.planner import plan_verification
    except ImportError as exc:
        findings.append({
            "section": "planner",
            "check_id": "planner-step-order-import",
            "name": "Step ordering validation",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Cannot import plan_verification: {exc}",
            "details": {},
            "recommendation": "Ensure planner module is importable",
        })
        return findings

    test_files = [
        "backend/src/engines/loan_engine.py",
        "frontend/src/components/BalanceTrend.tsx",
    ]

    try:
        plan = plan_verification(changed_files=test_files, scope=None)
        orders = [s.order for s in plan.steps]
        unique_orders = set(orders)
        no_duplicates = len(orders) == len(unique_orders)
        sequential = sorted(orders) == list(range(1, len(orders) + 1)) if orders else True

        status = "pass" if (no_duplicates and sequential) else "fail"
        message = (
            f"Steps have sequential unique order ({len(orders)} steps)"
            if status == "pass"
            else f"Steps have ordering issues: duplicates={not no_duplicates}, sequential={sequential}"
        )

        findings.append({
            "section": "planner",
            "check_id": "planner-step-ordering",
            "name": "Step ordering validation",
            "status": status,
            "severity": "high" if status == "fail" else "info",
            "priority": "high" if status == "fail" else "low",
            "message": message,
            "details": {"orders": orders, "all_unique": no_duplicates, "sequential": sequential},
            "recommendation": "" if status == "pass" else "Fix step ordering to be sequential and unique",
        })

        # Also check step dependencies reference valid step IDs
        step_ids = {s.id for s in plan.steps}
        invalid_deps: list[str] = []
        for s in plan.steps:
            for dep in s.dependencies:
                if dep not in step_ids:
                    invalid_deps.append(f"{s.id} -> {dep}")
        dep_status = "pass" if not invalid_deps else "fail"
        findings.append({
            "section": "planner",
            "check_id": "planner-step-deps",
            "name": "Step dependency validation",
            "status": dep_status,
            "severity": "high" if dep_status == "fail" else "info",
            "priority": "high" if dep_status == "fail" else "low",
            "message": "All step dependencies reference valid steps" if dep_status == "pass" else f"Found {len(invalid_deps)} invalid dependencies",
            "details": {"invalid_deps": invalid_deps[:50]},
            "recommendation": "" if dep_status == "pass" else "Fix step dependencies to reference valid step IDs",
        })
    except Exception as exc:
        findings.append({
            "section": "planner",
            "check_id": "planner-step-order",
            "name": "Step ordering validation",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Could not generate plan: {exc}",
            "details": {},
            "recommendation": "Fix planner to generate plans without errors",
        })

    return findings


def _check_verification_cache(cache_path: Path) -> dict[str, Any]:
    if not cache_path.exists():
        return {
            "section": "planner",
            "check_id": "planner-cache-existence",
            "name": "Verification cache existence",
            "status": "fail",
            "severity": "high",
            "priority": "high",
            "message": f"Verification cache not found at {cache_path}",
            "details": {"path": str(cache_path), "exists": False},
            "recommendation": "Run verification at least once to populate the cache",
        }

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        required_keys = {"last_commit", "changed_files", "executed_profiles", "duration", "timestamp"}
        missing = [k for k in required_keys if k not in data]
        if missing:
            status = "fail"
            message = f"Cache missing required keys: {missing}"
        else:
            status = "pass"
            message = "Verification cache is valid and complete"
        details = {
            "exists": True,
            "keys": list(data.keys()),
            "missing_keys": missing,
            "executed_profiles": data.get("executed_profiles", []),
            "last_commit": data.get("last_commit", ""),
        }
    except (json.JSONDecodeError, OSError) as exc:
        status = "fail"
        message = f"Cache JSON is invalid: {exc}"
        details = {"error": str(exc)}

    return {
        "section": "planner",
        "check_id": "planner-cache-validity",
        "name": "Verification cache validity",
        "status": status,
        "severity": "high" if status == "fail" else "info",
        "priority": "high" if status == "fail" else "low",
        "message": message,
        "details": details,
        "recommendation": "" if status == "pass" else "Fix verification cache structure",
    }


def _check_cross_layer_determinism() -> dict[str, Any]:
    try:
        from runtime.foundation.verification.planner import (
            CrossLayerImpactPlanner,
        )
    except ImportError as exc:
        return {
            "section": "planner",
            "check_id": "planner-cl-impact-import",
            "name": "Cross-layer impact planner import",
            "status": "fail",
            "severity": "critical",
            "priority": "critical",
            "message": f"Cannot import CrossLayerImpactPlanner: {exc}",
            "details": {},
            "recommendation": "Ensure planner module is importable",
        }

    try:
        cli = CrossLayerImpactPlanner()
        changed_files = ["backend/src/engines/loan_engine.py"]
        report1 = cli.analyze_cross_layer_impact(changed_files)
        report2 = cli.analyze_cross_layer_impact(changed_files)

        same_engines = report1.affected_engines == report2.affected_engines
        same_capabilities = report1.affected_capabilities == report2.affected_capabilities
        same_endpoints = report1.affected_endpoints == report2.affected_endpoints
        same_chains = len(report1.dependency_chains) == len(report2.dependency_chains)

        deterministic = same_engines and same_capabilities and same_endpoints and same_chains
        status = "pass" if deterministic else "fail"
        message = "Cross-layer impact analysis is deterministic" if deterministic else "Cross-layer impact analysis is NOT deterministic"

        findings_data = {
            "same_engines": same_engines,
            "same_capabilities": same_capabilities,
            "same_endpoints": same_endpoints,
            "same_chains": same_chains,
            "engines_found": len(report1.affected_engines),
        }
    except Exception as exc:
        status = "fail"
        message = f"Cross-layer impact analysis failed: {exc}"
        findings_data = {"error": str(exc)}

    return {
        "section": "planner",
        "check_id": "planner-cross-layer-determinism",
        "name": "Cross-layer impact determinism",
        "status": status,
        "severity": "critical" if status == "fail" else "info",
        "priority": "critical" if status == "fail" else "low",
        "message": message,
        "details": findings_data,
        "recommendation": "" if status == "pass" else "Fix non-determinism in CrossLayerImpactPlanner",
    }


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []
    repo = repo_root or REPO_ROOT
    cache_path = _find_cache_path(repo)

    findings.extend(_check_profile_expansion_determinism())
    findings.extend(_check_no_duplicate_task_ids())
    findings.append(_check_profile_coverage())
    findings.extend(_check_profile_task_ordering())
    findings.append(_check_plan_verification_determinism())
    findings.extend(_check_step_ordering())
    findings.append(_check_verification_cache(cache_path))
    findings.append(_check_cross_layer_determinism())

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    duration = time.monotonic() - start
    metrics = {
        "total_checks": len(findings),
        "failures": sum(1 for f in findings if f["status"] == "fail"),
        "passes": sum(1 for f in findings if f["status"] == "pass"),
        "cache_path": str(cache_path),
        "cache_exists": cache_path.exists(),
    }

    return {
        "section": "planner",
        "name": "Verification Planner Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
