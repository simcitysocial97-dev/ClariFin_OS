"""
Engineering Observability Runtime — Program 7C

Tracks, analyzes, and reports the health of the engineering process.
"""

from __future__ import annotations

from .analytics import AnalyticsEngine, AnalyticsReport, generate_analytics
from .cost_analysis import CostAnalysis, generate_cost_analysis
from .dashboard import DashboardGenerator, generate_dashboard
from .dependency_growth import DependencyGrowthIntelligence, generate_dependency_growth
from .event_store import EngineeringEventStore, EngineeringEvent, create_event
from .execution_context import (
    ExecutionContext,
    ExecutionEnvironment,
    RunnerType,
    VerificationDepth,
    VerificationIntent,
    TriggerType,
    create_context,
    detect_environment,
    detect_intent,
)
from .flaky_tests import FlakyTestIntelligence, generate_flaky_tests
from .health_report import EngineeringHealthReport, generate_health_report
from .repository import (
    GitHubMetricsRepository,
    HybridHistory,
    LocalMetricsRepository,
    MetricsRepository,
    RunRecord,
)

__all__ = [
    "AnalyticsEngine",
    "AnalyticsReport",
    "CostAnalysis",
    "DashboardGenerator",
    "DependencyGrowthIntelligence",
    "EngineeringEvent",
    "EngineeringEventStore",
    "EngineeringHealthReport",
    "ExecutionContext",
    "ExecutionEnvironment",
    "GitHubMetricsRepository",
    "HybridHistory",
    "LocalMetricsRepository",
    "MetricsRepository",
    "RunnerType",
    "RunRecord",
    "TriggerType",
    "VerificationDepth",
    "VerificationIntent",
    "create_context",
    "create_event",
    "detect_environment",
    "detect_intent",
    "generate_analytics",
    "generate_cost_analysis",
    "generate_dashboard",
    "generate_dependency_growth",
    "generate_flaky_tests",
    "generate_health_report",
]
