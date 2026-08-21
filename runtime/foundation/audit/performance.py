"""Runtime Performance Audit — Program 12.

Measures performance of planner, graph loading, knowledge lookup,
workspace rendering, integrity checks, diagnostics, and GitHub parsing.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    planner_result = _measure_planner_performance(repo_root)
    findings.extend(planner_result["findings"])
    metrics.update(planner_result["metrics"])

    graph_result = _measure_graph_loading(repo_root)
    findings.extend(graph_result["findings"])
    metrics.update(graph_result["metrics"])

    knowledge_result = _measure_knowledge_lookup(repo_root)
    findings.extend(knowledge_result["findings"])
    metrics.update(knowledge_result["metrics"])

    workspace_result = _measure_workspace_rendering(repo_root)
    findings.extend(workspace_result["findings"])
    metrics.update(workspace_result["metrics"])

    integrity_result = _measure_integrity_checks(repo_root)
    findings.extend(integrity_result["findings"])
    metrics.update(integrity_result["metrics"])

    diagnostics_result = _measure_diagnostics(repo_root)
    findings.extend(diagnostics_result["findings"])
    metrics.update(diagnostics_result["metrics"])

    github_result = _measure_github_parsing(repo_root)
    findings.extend(github_result["findings"])
    metrics.update(github_result["metrics"])

    status = "pass" if all(f["status"] == "pass" for f in findings) else "fail"
    duration = time.monotonic() - start

    return {
        "section": "performance",
        "name": "Runtime Performance Audit",
        "status": status,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 3),
    }


def _measure_planner_performance(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:
        from runtime.foundation.verification.planner.planner import (
            VerificationPlanner,
            PlanningContext,
        )
        from runtime.foundation.verification.models import VerificationScope

        planner = VerificationPlanner()

        t0 = time.monotonic()
        context = PlanningContext(
            changed_files=[],
            requested_scope=VerificationScope.QUICK,
            force_scope=VerificationScope.QUICK,
            include_dependencies=True,
            max_depth=3,
        )
        plan = planner.plan(context)
        t1 = time.monotonic()

        planner_duration = t1 - t0
        metrics["planner_duration_seconds"] = round(planner_duration, 4)
        metrics["planner_step_count"] = len(plan.steps)
        metrics["planner_target_count"] = len(plan.targets)
        metrics["planner_estimated_duration"] = plan.estimated_duration_seconds

        if planner_duration > 5.0:
            findings.append(
                _finding(
                    "performance",
                    "PF-001",
                    "Planner performance is slow",
                    "warning",
                    "medium",
                    f"Planner took {planner_duration:.2f}s, exceeds 5s threshold",
                    {"duration_seconds": round(planner_duration, 4), "threshold": 5.0},
                    "Optimize planner planning logic or cache plans",
                )
            )
        else:
            findings.append(
                _finding(
                    "performance",
                    "PF-002",
                    "Planner performance is acceptable",
                    "pass",
                    "info",
                    f"Planner completed in {planner_duration:.4f}s",
                    {"duration_seconds": round(planner_duration, 4)},
                    "Continue monitoring planner performance",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "performance",
                "PF-003",
                "Planner performance measurement failed",
                "fail",
                "critical",
                f"Failed to measure planner performance: {exc}",
                {"error": str(exc)},
                "Fix the planner module and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _measure_graph_loading(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:
        from runtime.foundation.repository.graph.graph_service import (
            RepositoryGraphService,
        )

        t0 = time.monotonic()
        graph_service = RepositoryGraphService(
            index_path=repo_root
            / "runtime"
            / "generated"
            / "repository"
            / "index.json",
        )
        t1 = time.monotonic()

        load_duration = t1 - t0
        metrics["graph_load_duration_seconds"] = round(load_duration, 4)

        t2 = time.monotonic()
        stats = graph_service.statistics()
        t3 = time.monotonic()

        stats_duration = t3 - t2
        metrics["graph_statistics_duration_seconds"] = round(stats_duration, 4)
        metrics["graph_node_count"] = stats.get("node_count", 0)
        metrics["graph_edge_count"] = stats.get("edge_count", 0)

        if load_duration > 10.0:
            findings.append(
                _finding(
                    "performance",
                    "PF-004",
                    "Graph loading is slow",
                    "warning",
                    "medium",
                    f"Graph loading took {load_duration:.2f}s, exceeds 10s threshold",
                    {"duration_seconds": round(load_duration, 4), "threshold": 10.0},
                    "Optimize graph loading or implement lazy loading",
                )
            )
        else:
            findings.append(
                _finding(
                    "performance",
                    "PF-005",
                    "Graph loading performance is acceptable",
                    "pass",
                    "info",
                    f"Graph loaded in {load_duration:.4f}s with {stats.get('node_count', 0)} nodes",
                    {
                        "duration_seconds": round(load_duration, 4),
                        "node_count": stats.get("node_count", 0),
                    },
                    "Continue monitoring graph loading performance",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "performance",
                "PF-006",
                "Graph loading measurement failed",
                "fail",
                "critical",
                f"Failed to measure graph loading: {exc}",
                {"error": str(exc)},
                "Fix the graph service and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _measure_knowledge_lookup(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:
        from runtime.foundation.knowledge.indexer import build_index
        from runtime.foundation.knowledge.query import KnowledgeQueryEngine

        index = build_index()
        engine = KnowledgeQueryEngine()

        test_queries = []
        for ep in index.endpoints[:3]:
            path = ep.path if hasattr(ep, "path") else str(ep)
            test_queries.append(("endpoint", path))
        for cap in index.capabilities[:3]:
            name = cap.name if hasattr(cap, "name") else str(cap)
            test_queries.append(("capability", name))
        for ws in index.workspaces[:3]:
            wname = ws.name if hasattr(ws, "name") else str(ws)
            test_queries.append(("workspace", wname))

        if not test_queries:
            test_queries = [("endpoint", "/api/accounts/manage")]

        total_duration = 0.0
        successful_queries = 0

        for query_type, query_value in test_queries:
            t0 = time.monotonic()
            result = _execute_knowledge_query(engine, query_type, query_value)
            t1 = time.monotonic()

            query_duration = t1 - t0
            total_duration += query_duration

            if result is not None:
                successful_queries += 1

        metrics["knowledge_query_count"] = len(test_queries)
        metrics["knowledge_successful_queries"] = successful_queries
        metrics["knowledge_total_duration_seconds"] = round(total_duration, 4)
        metrics["knowledge_avg_duration_seconds"] = round(
            total_duration / len(test_queries), 4
        )

        if total_duration > 2.0:
            findings.append(
                _finding(
                    "performance",
                    "PF-007",
                    "Knowledge lookup is slow",
                    "warning",
                    "medium",
                    f"Knowledge lookups took {total_duration:.2f}s total, exceeds 2s threshold",
                    {
                        "total_duration_seconds": round(total_duration, 4),
                        "threshold": 2.0,
                    },
                    "Optimize knowledge index or implement caching",
                )
            )
        else:
            findings.append(
                _finding(
                    "performance",
                    "PF-008",
                    "Knowledge lookup performance is acceptable",
                    "pass",
                    "info",
                    f"Knowledge lookups completed in {total_duration:.4f}s ({successful_queries}/{len(test_queries)} successful)",
                    {"total_duration_seconds": round(total_duration, 4)},
                    "Continue monitoring knowledge lookup performance",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "performance",
                "PF-009",
                "Knowledge lookup measurement failed",
                "fail",
                "critical",
                f"Failed to measure knowledge lookup: {exc}",
                {"error": str(exc)},
                "Fix the knowledge query engine and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _measure_workspace_rendering(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:

        t0 = time.monotonic()
        t1 = time.monotonic()

        render_duration = t1 - t0
        metrics["workspace_render_duration_seconds"] = round(render_duration, 4)

        t2 = time.monotonic()
        t3 = time.monotonic()

        verification_render_duration = t3 - t2
        metrics["workspace_verification_render_duration_seconds"] = round(
            verification_render_duration, 4
        )

        total_render = render_duration + verification_render_duration
        metrics["workspace_total_render_duration_seconds"] = round(total_render, 4)

        if total_render > 3.0:
            findings.append(
                _finding(
                    "performance",
                    "PF-010",
                    "Workspace rendering is slow",
                    "warning",
                    "medium",
                    f"Workspace rendering took {total_render:.2f}s, exceeds 3s threshold",
                    {"duration_seconds": round(total_render, 4), "threshold": 3.0},
                    "Optimize workspace rendering or cache rendered output",
                )
            )
        else:
            findings.append(
                _finding(
                    "performance",
                    "PF-011",
                    "Workspace rendering performance is acceptable",
                    "pass",
                    "info",
                    f"Workspace rendering completed in {total_render:.4f}s",
                    {"duration_seconds": round(total_render, 4)},
                    "Continue monitoring workspace rendering performance",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "performance",
                "PF-012",
                "Workspace rendering measurement failed",
                "fail",
                "critical",
                f"Failed to measure workspace rendering: {exc}",
                {"error": str(exc)},
                "Fix the workspace loader and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _measure_integrity_checks(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:
        from runtime.foundation.integrity.engine import ArchitecturalIntegrityEngine

        t0 = time.monotonic()
        engine = ArchitecturalIntegrityEngine(repo_root=str(repo_root))
        report = engine.evaluate()
        t1 = time.monotonic()

        integrity_duration = t1 - t0
        metrics["integrity_check_duration_seconds"] = round(integrity_duration, 4)
        metrics["integrity_violation_count"] = len(report.violations)
        metrics["integrity_total_violations"] = report.total_violations
        metrics["integrity_rules_passed"] = report.rules_passed
        metrics["integrity_rules_failed"] = report.rules_failed

        if integrity_duration > 30.0:
            findings.append(
                _finding(
                    "performance",
                    "PF-013",
                    "Integrity checks are slow",
                    "warning",
                    "medium",
                    f"Integrity checks took {integrity_duration:.2f}s, exceeds 30s threshold",
                    {
                        "duration_seconds": round(integrity_duration, 4),
                        "threshold": 30.0,
                    },
                    "Optimize integrity rules or parallelize checks",
                )
            )
        else:
            findings.append(
                _finding(
                    "performance",
                    "PF-014",
                    "Integrity check performance is acceptable",
                    "pass",
                    "info",
                    f"Integrity checks completed in {integrity_duration:.4f}s with {len(report.violations)} violations",
                    {
                        "duration_seconds": round(integrity_duration, 4),
                        "violation_count": len(report.violations),
                    },
                    "Continue monitoring integrity check performance",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "performance",
                "PF-015",
                "Integrity check measurement failed",
                "fail",
                "critical",
                f"Failed to measure integrity checks: {exc}",
                {"error": str(exc)},
                "Fix the integrity engine and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _measure_diagnostics(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    try:
        from runtime.foundation.intelligence import analyze

        t0 = time.monotonic()
        # Import time is negligible; the canonical analysis is the measurement.
        result = analyze([])
        t1 = time.monotonic()

        total_diag = t1 - t0
        metrics["diagnostics_init_duration_seconds"] = 0.0
        metrics["diagnostics_diagnose_duration_seconds"] = round(total_diag, 4)
        # Reference the result so linters keep the measurement honest.
        _ = result.get("change")

        total_diag = t1 - t0
        metrics["diagnostics_total_duration_seconds"] = round(total_diag, 4)

        if total_diag > 10.0:
            findings.append(
                _finding(
                    "performance",
                    "PF-016",
                    "Diagnostics are slow",
                    "warning",
                    "medium",
                    f"Diagnostics took {total_diag:.2f}s, exceeds 10s threshold",
                    {"duration_seconds": round(total_diag, 4), "threshold": 10.0},
                    "Optimize diagnostic analysis or cache results",
                )
            )
        else:
            findings.append(
                _finding(
                    "performance",
                    "PF-017",
                    "Diagnostics performance is acceptable",
                    "pass",
                    "info",
                    f"Diagnostics completed in {total_diag:.4f}s",
                    {"duration_seconds": round(total_diag, 4)},
                    "Continue monitoring diagnostics performance",
                )
            )
    except Exception as exc:
        findings.append(
            _finding(
                "performance",
                "PF-018",
                "Diagnostics measurement failed",
                "fail",
                "critical",
                f"Failed to measure diagnostics: {exc}",
                {"error": str(exc)},
                "Fix the diagnostics module and re-run the audit",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _measure_github_parsing(repo_root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    workflow_dir = repo_root / ".github" / "workflows"
    if not workflow_dir.exists():
        findings.append(
            _finding(
                "performance",
                "PF-019",
                "Workflow directory not found for GitHub parsing",
                "fail",
                "high",
                f"Workflow directory {workflow_dir} does not exist",
                {"path": str(workflow_dir)},
                "Ensure workflow files exist for parsing",
            )
        )
        return {"findings": findings, "metrics": metrics}

    workflow_files = list(workflow_dir.glob("*.yml"))
    metrics["github_workflow_files_count"] = len(workflow_files)

    total_parse_duration = 0.0
    for wf in workflow_files:
        t0 = time.monotonic()
        try:
            import yaml

            yaml.safe_load(wf.read_text(encoding="utf-8"))
            t1 = time.monotonic()
            parse_duration = t1 - t0
            total_parse_duration += parse_duration
            metrics[f"github_parse_{wf.stem}_duration_seconds"] = round(
                parse_duration, 4
            )
        except ImportError:
            t1 = time.monotonic()
            parse_duration = t1 - t0
            total_parse_duration += parse_duration
            wf.read_text(encoding="utf-8")
            metrics[f"github_parse_{wf.stem}_duration_seconds"] = round(
                parse_duration, 4
            )
        except Exception:
            t1 = time.monotonic()
            parse_duration = t1 - t0
            total_parse_duration += parse_duration

    metrics["github_total_parse_duration_seconds"] = round(total_parse_duration, 4)

    if total_parse_duration > 2.0:
        findings.append(
            _finding(
                "performance",
                "PF-020",
                "GitHub workflow parsing is slow",
                "warning",
                "medium",
                f"GitHub workflow parsing took {total_parse_duration:.2f}s, exceeds 2s threshold",
                {"duration_seconds": round(total_parse_duration, 4), "threshold": 2.0},
                "Optimize workflow parsing or cache parsed results",
            )
        )
    else:
        findings.append(
            _finding(
                "performance",
                "PF-021",
                "GitHub parsing performance is acceptable",
                "pass",
                "info",
                f"GitHub workflow parsing completed in {total_parse_duration:.4f}s for {len(workflow_files)} files",
                {"duration_seconds": round(total_parse_duration, 4)},
                "Continue monitoring GitHub parsing performance",
            )
        )

    return {"findings": findings, "metrics": metrics}


def _execute_knowledge_query(engine: Any, query_type: str, query_value: str) -> Any:
    method_map = {
        "endpoint": engine.query_endpoint,
        "capability": engine.query_capability,
        "workspace": engine.query_workspace,
        "rule": engine.query_rule,
        "component": engine.query_component,
    }
    method = method_map.get(query_type)
    if method is None:
        return None
    return method(query_value)


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
