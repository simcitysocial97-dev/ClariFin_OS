"""Integrity Engine Audit — Program 12.

Verifies all 28 constitutional rules, severity assignments, categories,
messages, and determinism of the Architectural Integrity Engine.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _load_registry() -> dict[str, Any]:
    from runtime.foundation.integrity.registry import get_constitution

    registry = get_constitution()
    rules = registry.all_rules()
    return {
        "total_count": registry.total_count,
        "rule_ids": registry.rule_ids,
        "rules": rules,
    }


def _run_all_rules() -> dict[str, Any]:
    from runtime.foundation.integrity.engine import evaluate_integrity

    report = evaluate_integrity()
    return {
        "rules_evaluated": report.rules_evaluated,
        "rules_passed": report.rules_passed,
        "rules_failed": report.rules_failed,
        "total_violations": report.total_violations,
        "severity_counts": report.severity_counts,
        "passed": report.passed,
        "files_scanned": report.files_scanned,
        "cross_layer_entries": report.cross_layer_entries,
    }


def _verify_rule_count(expected: int = 28) -> dict[str, Any]:
    registry_info = _load_registry()
    actual = registry_info["total_count"]
    status = "pass" if actual == expected else "fail"
    return {
        "section": "integrity",
        "check_id": "int-rule-count",
        "name": f"All {expected} rules present",
        "status": status,
        "severity": "info",
        "priority": "low",
        "message": f"Expected {expected} rules, found {actual}",
        "details": {
            "expected": expected,
            "actual": actual,
            "rule_ids": registry_info["rule_ids"],
        },
        "recommendation": (
            "" if status == "pass" else f"Add missing rules to reach {expected}"
        ),
    }


def _verify_severity_assignments() -> dict[str, Any]:
    registry_info = _load_registry()
    findings: list[dict[str, Any]] = []
    expected_severities: dict[str, str] = {
        "ARCH-001": "HIGH",
        "ARCH-002": "HIGH",
        "ARCH-003": "LOW",
        "ARCH-004": "HIGH",
        "ARCH-005": "HIGH",
        "ARCH-006": "MEDIUM",
        "ARCH-007": "MEDIUM",
        "ARCH-008": "HIGH",
        "ARCH-009": "CRITICAL",
        "ARCH-010": "HIGH",
        "ARCH-011": "HIGH",
        "ARCH-012": "MEDIUM",
        "ARCH-013": "MEDIUM",
        "ARCH-014": "LOW",
        "ARCH-015": "MEDIUM",
        "ARCH-016": "HIGH",
        "ARCH-017": "MEDIUM",
        "ARCH-018": "MEDIUM",
        "ARCH-019": "MEDIUM",
        "ARCH-020": "LOW",
        "ARCH-021": "MEDIUM",
        "ARCH-022": "LOW",
        "ARCH-023": "MEDIUM",
        "ARCH-024": "LOW",
        "ARCH-025": "MEDIUM",
        "ARCH-026": "MEDIUM",
        "ARCH-027": "LOW",
        "ARCH-028": "LOW",
    }

    for rule in registry_info["rules"]:
        expected_sev = expected_severities.get(rule.id)
        actual_sev = rule.severity.value
        if expected_sev and actual_sev != expected_sev:
            findings.append(
                {
                    "section": "integrity",
                    "check_id": f"int-severity-{rule.id}",
                    "name": f"{rule.id} severity assignment",
                    "status": "fail",
                    "severity": "critical",
                    "priority": "critical",
                    "message": f"{rule.id} has severity '{actual_sev}', expected '{expected_sev}'",
                    "details": {
                        "rule_id": rule.id,
                        "actual": actual_sev,
                        "expected": expected_sev,
                    },
                    "recommendation": f"Update {rule.id} severity to {expected_sev}",
                }
            )
        else:
            findings.append(
                {
                    "section": "integrity",
                    "check_id": f"int-severity-{rule.id}",
                    "name": f"{rule.id} severity assignment",
                    "status": "pass",
                    "severity": "info",
                    "priority": "low",
                    "message": f"{rule.id} severity '{actual_sev}' is correct",
                    "details": {"rule_id": rule.id, "severity": actual_sev},
                    "recommendation": "",
                }
            )

    all_pass = all(f["status"] == "pass" for f in findings)
    return {
        "section": "integrity",
        "name": "Severity assignments",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": {
            "rules_checked": len(findings),
            "failures": sum(1 for f in findings if f["status"] == "fail"),
        },
        "duration_seconds": 0.0,
    }


def _verify_categories() -> dict[str, Any]:
    registry_info = _load_registry()
    findings: list[dict[str, Any]] = []
    valid_categories = {"structural", "ownership", "evolution"}

    for rule in registry_info["rules"]:
        cat = rule.category.value
        status = "pass" if cat in valid_categories else "fail"
        findings.append(
            {
                "section": "integrity",
                "check_id": f"int-category-{rule.id}",
                "name": f"{rule.id} category validity",
                "status": status,
                "severity": "critical" if status == "fail" else "info",
                "priority": "critical" if status == "fail" else "low",
                "message": f"{rule.id} category is '{cat}'"
                + (" (valid)" if status == "pass" else " (invalid)"),
                "details": {
                    "rule_id": rule.id,
                    "category": cat,
                    "valid": cat in valid_categories,
                },
                "recommendation": (
                    "" if status == "pass" else f"Fix category for {rule.id}"
                ),
            }
        )

    all_pass = all(f["status"] == "pass" for f in findings)
    return {
        "section": "integrity",
        "name": "Category assignments",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": {
            "rules_checked": len(findings),
            "failures": sum(1 for f in findings if f["status"] == "fail"),
        },
        "duration_seconds": 0.0,
    }


def _verify_messages() -> dict[str, Any]:
    registry_info = _load_registry()
    findings: list[dict[str, Any]] = []

    for rule in registry_info["rules"]:
        has_name = bool(rule.name.strip())
        has_description = bool(rule.description.strip())
        has_examples = len(rule.examples) > 0
        has_check = bool(rule.check.strip())

        all_ok = has_name and has_description and has_examples and has_check
        findings.append(
            {
                "section": "integrity",
                "check_id": f"int-message-{rule.id}",
                "name": f"{rule.id} message completeness",
                "status": "pass" if all_ok else "fail",
                "severity": "critical" if not all_ok else "info",
                "priority": "critical" if not all_ok else "low",
                "message": f"{rule.id}: name={'yes' if has_name else 'no'}, desc={'yes' if has_description else 'no'}, examples={len(rule.examples)}, check={'yes' if has_check else 'no'}",
                "details": {
                    "rule_id": rule.id,
                    "has_name": has_name,
                    "has_description": has_description,
                    "has_examples": has_examples,
                    "has_check": has_check,
                },
                "recommendation": "" if all_ok else f"Add missing fields to {rule.id}",
            }
        )

    all_pass = all(f["status"] == "pass" for f in findings)
    return {
        "section": "integrity",
        "name": "Message completeness",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": {
            "rules_checked": len(findings),
            "failures": sum(1 for f in findings if f["status"] == "fail"),
        },
        "duration_seconds": 0.0,
    }


def _inject_and_verify_violations() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.integrity.models import ArchitectureLayer
        from runtime.foundation.integrity.scanner import (
            ArchitecturalGraph,
            ScannedFile,
            ImportRecord,
        )
        from runtime.foundation.integrity.rules import (
            check_router_not_import_engine,
            check_component_not_api_direct,
            check_mapper_not_react,
            check_workspace_not_fetch,
        )
    except ImportError as exc:
        findings.append(
            {
                "section": "integrity",
                "check_id": "int-inject-import",
                "name": "Violation injection imports",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"Cannot import integrity models/rules for injection test: {exc}",
                "details": {},
                "recommendation": "Ensure integrity engine modules are importable",
            }
        )
        return {
            "section": "integrity",
            "name": "Violation injection and detection",
            "status": "fail",
            "findings": findings,
            "metrics": {"duration_seconds": 0.0},
            "duration_seconds": 0.0,
        }

    router_file = ScannedFile(
        path="backend/src/routers/bad_router.py",
        layer=ArchitectureLayer.BACKEND_ROUTER.value,
        file_type="python",
        imports=(
            ImportRecord(
                module="backend.src.engines.loan_engine",
                line_number=10,
                resolved_path="backend/src/engines/loan_engine.py",
                layer=ArchitectureLayer.BACKEND_ENGINE.value,
            ),
        ),
        fetch_call_lines=(),
        has_workspace_registration=False,
        class_names=(),
        function_names=(),
    )

    violations = check_router_not_import_engine(
        ArchitecturalGraph(
            files=(router_file,),
            cross_layer_map={},
            graph_nodes=(),
            graph_edges=(),
            files_scanned=1,
            repo_root=str(REPO_ROOT),
        )
    )
    found_router_violation = any(v.rule_id == "ARCH-001" for v in violations)
    findings.append(
        {
            "section": "integrity",
            "check_id": "int-inject-ARCH-001",
            "name": "ARCH-001 violation injection (Router imports Engine)",
            "status": "pass" if found_router_violation else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"ARCH-001 detected injected router→engine violation: {found_router_violation}",
            "details": {"violations_found": len(violations), "rule_id": "ARCH-001"},
            "recommendation": (
                "" if found_router_violation else "Fix ARCH-001 rule detection"
            ),
        }
    )

    component_file = ScannedFile(
        path="frontend/components/bad_component.tsx",
        layer=ArchitectureLayer.FRONTEND_COMPONENT.value,
        file_type="typescript",
        imports=(
            ImportRecord(
                module="frontend/lib/api/client",
                line_number=5,
                resolved_path="frontend/lib/api/client.ts",
                layer=ArchitectureLayer.FRONTEND_API.value,
            ),
        ),
        fetch_call_lines=(12,),
        has_workspace_registration=False,
        class_names=(),
        function_names=(),
    )

    violations = check_component_not_api_direct(
        ArchitecturalGraph(
            files=(component_file,),
            cross_layer_map={},
            graph_nodes=(),
            graph_edges=(),
            files_scanned=1,
            repo_root=str(REPO_ROOT),
        )
    )
    found_comp_violation = any(v.rule_id == "ARCH-002" for v in violations)
    findings.append(
        {
            "section": "integrity",
            "check_id": "int-inject-ARCH-002",
            "name": "ARCH-002 violation injection (Component calls API directly)",
            "status": "pass" if found_comp_violation else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"ARCH-002 detected injected component→API violation: {found_comp_violation}",
            "details": {"violations_found": len(violations), "rule_id": "ARCH-002"},
            "recommendation": (
                "" if found_comp_violation else "Fix ARCH-002 rule detection"
            ),
        }
    )

    mapper_file = ScannedFile(
        path="frontend/lib/mappers/bad_mapper.ts",
        layer=ArchitectureLayer.FRONTEND_MAPPER.value,
        file_type="typescript",
        imports=(
            ImportRecord(
                module="react",
                line_number=3,
                resolved_path=None,
                layer=ArchitectureLayer.UNKNOWN.value,
            ),
        ),
        fetch_call_lines=(),
        has_workspace_registration=False,
        class_names=(),
        function_names=(),
    )

    violations = check_mapper_not_react(
        ArchitecturalGraph(
            files=(mapper_file,),
            cross_layer_map={},
            graph_nodes=(),
            graph_edges=(),
            files_scanned=1,
            repo_root=str(REPO_ROOT),
        )
    )
    found_mapper_violation = any(v.rule_id == "ARCH-003" for v in violations)
    findings.append(
        {
            "section": "integrity",
            "check_id": "int-inject-ARCH-003",
            "name": "ARCH-003 violation injection (Mapper imports React)",
            "status": "pass" if found_mapper_violation else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"ARCH-003 detected injected mapper→React violation: {found_mapper_violation}",
            "details": {"violations_found": len(violations), "rule_id": "ARCH-003"},
            "recommendation": (
                "" if found_mapper_violation else "Fix ARCH-003 rule detection"
            ),
        }
    )

    workspace_file = ScannedFile(
        path="frontend/lib/workspace/bad_workspace.ts",
        layer=ArchitectureLayer.FRONTEND_WORKSPACE.value,
        file_type="typescript",
        imports=(),
        fetch_call_lines=(42,),
        has_workspace_registration=False,
        class_names=(),
        function_names=(),
    )

    violations = check_workspace_not_fetch(
        ArchitecturalGraph(
            files=(workspace_file,),
            cross_layer_map={},
            graph_nodes=(),
            graph_edges=(),
            files_scanned=1,
            repo_root=str(REPO_ROOT),
        )
    )
    found_ws_violation = any(v.rule_id == "ARCH-004" for v in violations)
    findings.append(
        {
            "section": "integrity",
            "check_id": "int-inject-ARCH-004",
            "name": "ARCH-004 violation injection (Workspace performs fetch)",
            "status": "pass" if found_ws_violation else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"ARCH-004 detected injected workspace→fetch violation: {found_ws_violation}",
            "details": {"violations_found": len(violations), "rule_id": "ARCH-004"},
            "recommendation": (
                "" if found_ws_violation else "Fix ARCH-004 rule detection"
            ),
        }
    )

    all_pass = all(f["status"] == "pass" for f in findings)
    return {
        "section": "integrity",
        "name": "Violation injection and detection",
        "status": "pass" if all_pass else "fail",
        "findings": findings,
        "metrics": {
            "violations_injected": 4,
            "detected": sum(1 for f in findings if f["status"] == "pass"),
        },
        "duration_seconds": 0.0,
    }


def _verify_determinism() -> dict[str, Any]:
    findings: list[dict[str, Any]] = []

    try:
        from runtime.foundation.integrity.engine import evaluate_integrity
    except ImportError as exc:
        findings.append(
            {
                "section": "integrity",
                "check_id": "int-determinism-import",
                "name": "Integrity engine import for determinism test",
                "status": "fail",
                "severity": "critical",
                "priority": "critical",
                "message": f"Cannot import integrity engine: {exc}",
                "details": {},
                "recommendation": "Ensure integrity engine is importable",
            }
        )
        return {
            "section": "integrity",
            "name": "Determinism",
            "status": "fail",
            "findings": findings,
            "metrics": {"duration_seconds": 0.0},
            "duration_seconds": 0.0,
        }

    report1 = evaluate_integrity()
    report2 = evaluate_integrity()

    same_violations = report1.total_violations == report2.total_violations
    same_rules_evaluated = report1.rules_evaluated == report2.rules_evaluated
    same_files_scanned = report1.files_scanned == report2.files_scanned
    same_cross_layer = report1.cross_layer_entries == report2.cross_layer_entries

    all_deterministic = (
        same_violations
        and same_rules_evaluated
        and same_files_scanned
        and same_cross_layer
    )

    findings.append(
        {
            "section": "integrity",
            "check_id": "int-determinism-run",
            "name": "Deterministic evaluation",
            "status": "pass" if all_deterministic else "fail",
            "severity": "info",
            "priority": "low",
            "message": f"Two consecutive runs produced identical results: {all_deterministic}",
            "details": {
                "run1_violations": report1.total_violations,
                "run2_violations": report2.total_violations,
                "run1_rules": report1.rules_evaluated,
                "run2_rules": report2.rules_evaluated,
                "run1_files": report1.files_scanned,
                "run2_files": report2.files_scanned,
                "run1_cross_layer": report1.cross_layer_entries,
                "run2_cross_layer": report2.cross_layer_entries,
            },
            "recommendation": (
                ""
                if all_deterministic
                else "Investigate non-deterministic behavior in the integrity engine"
            ),
        }
    )

    status = "pass" if all_deterministic else "fail"
    return {
        "section": "integrity",
        "name": "Determinism",
        "status": status,
        "findings": findings,
        "metrics": {"deterministic": all_deterministic},
        "duration_seconds": 0.0,
    }


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    findings: list[dict[str, Any]] = []

    count_result = _verify_rule_count()
    findings.append(count_result)

    severity_result = _verify_severity_assignments()
    findings.extend(severity_result["findings"])

    category_result = _verify_categories()
    findings.extend(category_result["findings"])

    message_result = _verify_messages()
    findings.extend(message_result["findings"])

    injection_result = _inject_and_verify_violations()
    findings.extend(injection_result["findings"])

    determinism_result = _verify_determinism()
    findings.extend(determinism_result["findings"])

    try:
        runtime_result = _run_all_rules()
        metrics = {
            "rules_evaluated": runtime_result["rules_evaluated"],
            "rules_passed": runtime_result["rules_passed"],
            "rules_failed": runtime_result["rules_failed"],
            "total_violations": runtime_result["total_violations"],
            "severity_counts": runtime_result["severity_counts"],
            "files_scanned": runtime_result["files_scanned"],
            "cross_layer_entries": runtime_result["cross_layer_entries"],
        }
    except Exception:
        metrics = {"rules_evaluated": 0, "rules_passed": 0, "rules_failed": 0}

    all_pass = all(f["status"] == "pass" for f in findings)
    overall_status = "pass" if all_pass else "fail"

    duration = time.monotonic() - start
    return {
        "section": "integrity",
        "name": "Integrity Engine Audit",
        "status": overall_status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": duration,
    }
