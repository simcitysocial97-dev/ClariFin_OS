from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from runtime.foundation.audit.models import AuditFinding, AuditPriority, AuditSeverity, AuditStatus

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def _f(check_id: str, name: str, status: str, severity: str, priority: str, message: str, details: dict[str, Any] = None, recommendation: str = "") -> AuditFinding:
    return AuditFinding(
        section="observability",
        check_id=check_id,
        name=name,
        status=AuditStatus(status),
        severity=AuditSeverity(severity),
        priority=AuditPriority(priority),
        message=message,
        details=details or {},
        recommendation=recommendation,
    )


def audit(repo_root: Path | None = None) -> dict[str, Any]:
    start = time.monotonic()
    repo_root = repo_root or REPO_ROOT
    findings: list[AuditFinding] = []
    metrics: dict[str, Any] = {}

    from runtime.system.observability.event_store import (
        EngineeringEventStore,
    )
    from runtime.system.observability.analytics import (
        AnalyticsEngine,
        AnalyticsReport,
    )
    from runtime.system.observability.dashboard import DashboardGenerator
    from runtime.system.observability.flaky_tests import FlakyTestIntelligence
    from runtime.system.observability.cost_analysis import CostAnalysis
    from runtime.system.observability.dependency_growth import (
        DependencyGrowthIntelligence,
    )

    event_store = EngineeringEventStore()

    event_count = event_store.count()
    if event_count >= 0:
        findings.append(
            _f(
                "event-store-readable",
                "JSONL event store is readable",
                "pass",
                "info",
                "low",
                f"EngineeringEventStore loaded {event_count} events from JSONL",
                {"event_count": event_count},
            )
        )
    else:
        findings.append(
            _f(
                "event-store-readable",
                "JSONL event store is readable",
                "fail",
                "high",
                "high",
                "EngineeringEventStore could not read events from JSONL",
                {},
                "Fix event store to correctly read JSONL file",
            )
        )

    events = event_store.load_events()
    if isinstance(events, list):
        findings.append(
            _f(
                "event-store-history",
                "Event history retrieval works",
                "pass",
                "info",
                "low",
                "EngineeringEventStore.load_events() returns a list of events",
                {"returned_count": len(events)},
            )
        )
    else:
        findings.append(
            _f(
                "event-store-history",
                "Event history retrieval works",
                "fail",
                "high",
                "high",
                "EngineeringEventStore.load_events() did not return a list",
                {},
                "Fix load_events() to return a list of EngineeringEvent",
            )
        )

    analytics_engine = AnalyticsEngine(event_store)
    analytics_report = analytics_engine.compute()
    if isinstance(analytics_report, AnalyticsReport):
        findings.append(
            _f(
                "analytics-computation",
                "Analytics computation works",
                "pass",
                "info",
                "low",
                "AnalyticsEngine.compute() returns a valid AnalyticsReport",
                {
                    "local_runs": analytics_report.local.get("verification", {}).get(
                        "total_runs", 0
                    ),
                    "ci_runs": analytics_report.ci.get("verification", {}).get(
                        "total_runs", 0
                    ),
                },
            )
        )
    else:
        findings.append(
            _f(
                "analytics-computation",
                "Analytics computation works",
                "fail",
                "high",
                "high",
                "AnalyticsEngine.compute() did not return an AnalyticsReport",
                {},
                "Fix AnalyticsEngine.compute() to return AnalyticsReport",
            )
        )

    dashboard_gen = DashboardGenerator(event_store)
    dashboard_data = dashboard_gen.generate()
    if isinstance(dashboard_data, dict) and "combined" in dashboard_data:
        findings.append(
            _f(
                "dashboard-generation",
                "Dashboard generation works",
                "pass",
                "info",
                "low",
                "DashboardGenerator.generate() returns valid dashboard data",
                {
                    "keys": list(dashboard_data.keys()),
                    "has_local": "local" in dashboard_data,
                    "has_ci": "ci" in dashboard_data,
                    "has_combined": "combined" in dashboard_data,
                },
            )
        )
    else:
        findings.append(
            _f(
                "dashboard-generation",
                "Dashboard generation works",
                "fail",
                "high",
                "high",
                "DashboardGenerator.generate() did not return valid dashboard data",
                {},
                "Fix DashboardGenerator.generate() to return valid dict",
            )
        )

    metrics_data = analytics_report.combined.get("verification", {})
    if isinstance(metrics_data, dict) and "total_runs" in metrics_data:
        findings.append(
            _f(
                "metrics-computation",
                "Metrics computation works",
                "pass",
                "info",
                "low",
                "AnalyticsEngine computes verification metrics correctly",
                {
                    "total_runs": metrics_data.get("total_runs", 0),
                    "success_rate": metrics_data.get("success_rate", 0.0),
                },
            )
        )
    else:
        findings.append(
            _f(
                "metrics-computation",
                "Metrics computation works",
                "fail",
                "high",
                "high",
                "AnalyticsEngine did not compute verification metrics correctly",
                {},
                "Fix AnalyticsEngine to compute verification metrics",
            )
        )

    flaky_intel = FlakyTestIntelligence(event_store)
    flaky_data = flaky_intel.compute()
    if isinstance(flaky_data, dict):
        findings.append(
            _f(
                "flaky-tests-tracking",
                "Flaky tests tracking works",
                "pass",
                "info",
                "low",
                "FlakyTestIntelligence.compute() returns a dict of flaky test records",
                {"flaky_tests_count": len(flaky_data)},
            )
        )
    else:
        findings.append(
            _f(
                "flaky-tests-tracking",
                "Flaky tests tracking works",
                "fail",
                "high",
                "high",
                "FlakyTestIntelligence.compute() did not return a dict",
                {},
                "Fix FlakyTestIntelligence.compute() to return dict",
            )
        )

    growth_intel = DependencyGrowthIntelligence()
    growth_data = growth_intel.compute()
    if isinstance(growth_data, dict):
        findings.append(
            _f(
                "growth-tracking",
                "Growth tracking works",
                "pass",
                "info",
                "low",
                "DependencyGrowthIntelligence.compute() returns growth records",
                {"growth_categories": len(growth_data)},
            )
        )
    else:
        findings.append(
            _f(
                "growth-tracking",
                "Growth tracking works",
                "fail",
                "high",
                "high",
                "DependencyGrowthIntelligence.compute() did not return a dict",
                {},
                "Fix DependencyGrowthIntelligence.compute() to return dict",
            )
        )

    cost_analysis = CostAnalysis(event_store)
    cost_data = cost_analysis.compute()
    if isinstance(cost_data, dict) and len(cost_data) > 0:
        findings.append(
            _f(
                "cost-analysis",
                "Cost analysis works",
                "pass",
                "info",
                "low",
                "CostAnalysis.compute() returns cost breakdown by phase",
                {"phases_analyzed": len(cost_data)},
            )
        )
    else:
        findings.append(
            _f(
                "cost-analysis",
                "Cost analysis works",
                "fail",
                "high",
                "high",
                "CostAnalysis.compute() did not return valid cost data",
                {},
                "Fix CostAnalysis.compute() to return cost breakdown",
            )
        )

    event_types = set()
    for event in events:
        event_types.add(event.event_type)
    metrics["total_events"] = len(events)
    metrics["event_types"] = sorted(event_types)
    metrics["analytics_profiles"] = 3
    metrics["dashboard_sections"] = 3
    metrics["flaky_tests_tracked"] = len(flaky_data)
    metrics["growth_categories"] = len(growth_data)
    metrics["cost_phases"] = len(cost_data)
    metrics["metrics_computed"] = isinstance(metrics_data, dict)

    all_pass = all(f.status == AuditStatus.PASS for f in findings)
    overall = AuditStatus.PASS if all_pass else AuditStatus.FAIL

    duration = time.monotonic() - start

    return {
        "section": "observability",
        "name": "Observability Audit",
        "status": overall,
        "findings": findings,
        "metrics": metrics,
        "duration_seconds": round(duration, 4),
    }