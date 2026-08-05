"""Immutable models for Engineering Workspace.

No execution logic. Data models only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class RepositoryStatus:
    """Repository status snapshot."""

    commit: str
    branch: str
    changed_files: int
    is_dirty: bool


@dataclass(frozen=True, slots=True)
class VerificationStatusInfo:
    """Verification status snapshot."""

    last_profile: str
    last_status: str
    last_timestamp: str | None
    passed: int
    failed: int
    skipped: int
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class PlannerStatus:
    """Planner status snapshot."""

    avg_duration_seconds: float
    runs: int
    last_plan_id: str | None


@dataclass(frozen=True, slots=True)
class CrossLayerStatus:
    """Cross-layer status snapshot."""

    total_files: int
    total_engines: int
    total_services: int
    total_endpoints: int
    total_capabilities: int


@dataclass(frozen=True, slots=True)
class EngineeringHealth:
    """Engineering health snapshot."""

    generated_at: str
    verification_success_rate: float
    local_success_rate: float
    ci_success_rate: float
    cache_hit_rate: float
    avg_duration_seconds: float


@dataclass(frozen=True, slots=True)
class RecentFailure:
    """Recent failure snapshot."""

    run_id: str
    timestamp: str
    profile: str
    failed: int
    environment: str


@dataclass(frozen=True, slots=True)
class VerificationCache:
    """Verification cache snapshot."""

    last_commit: str
    changed_files: list[str]
    executed_profiles: list[str]
    duration: float
    timestamp: str
    is_valid: bool


@dataclass(frozen=True, slots=True)
class RiskSummary:
    """Risk summary snapshot."""

    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int
    total_files: int


@dataclass(frozen=True, slots=True)
class StatusWorkspace:
    """Complete status workspace snapshot."""

    repository: RepositoryStatus
    verification: VerificationStatusInfo
    planner: PlannerStatus
    cross_layer: CrossLayerStatus
    health: EngineeringHealth
    recent_failures: list[RecentFailure]
    cache: VerificationCache
    risk: RiskSummary


@dataclass(frozen=True, slots=True)
class VerificationCounts:
    """Verification counts snapshot."""

    total_runs: int
    passed_runs: int
    failed_runs: int
    skipped_runs: int
    success_rate: float


@dataclass(frozen=True, slots=True)
class CacheMetrics:
    """Cache metrics snapshot."""

    hit_rate: float
    hits: int
    total: int


@dataclass(frozen=True, slots=True)
class DurationMetrics:
    """Duration metrics snapshot."""

    avg_seconds: float
    min_seconds: float
    max_seconds: float
    total_seconds: float


@dataclass(frozen=True, slots=True)
class FailureRate:
    """Failure rate snapshot."""

    local: float
    ci: float
    combined: float


@dataclass(frozen=True, slots=True)
class FlakyTestInfo:
    """Flaky test snapshot."""

    total_flaky: int
    flaky_tests: list[str]


@dataclass(frozen=True, slots=True)
class DependencyGrowth:
    """Dependency growth snapshot."""

    category: str
    current_count: int
    previous_count: int
    delta: int
    growth_rate: float


@dataclass(frozen=True, slots=True)
class RiskDistribution:
    """Risk distribution snapshot."""

    high: int
    medium: int
    low: int
    total: int


@dataclass(frozen=True, slots=True)
class MetricsWorkspace:
    """Complete metrics workspace snapshot."""

    verification: VerificationCounts
    local_verification: VerificationCounts
    ci_verification: VerificationCounts
    cache: CacheMetrics
    local_cache: CacheMetrics
    ci_cache: CacheMetrics
    duration: DurationMetrics
    local_duration: DurationMetrics
    ci_duration: DurationMetrics
    failure_rate: FailureRate
    flaky_tests: FlakyTestInfo
    dependency_growth: list[DependencyGrowth]
    risk_distribution: RiskDistribution


@dataclass(frozen=True, slots=True)
class HistoryEvent:
    """History event snapshot."""

    run_id: str
    timestamp: str
    environment: str
    profile: str
    status: str
    passed: int
    failed: int
    skipped: int
    duration_seconds: float


@dataclass(frozen=True, slots=True)
class VerificationHistory:
    """Verification history snapshot."""

    local: list[HistoryEvent]
    ci: list[HistoryEvent]
    combined: list[HistoryEvent]


@dataclass(frozen=True, slots=True)
class VerificationProfile:
    """Verification profile snapshot."""

    name: str
    status: str
    last_executed: str | None
    executed_count: int
    cache_usage: str


@dataclass(frozen=True, slots=True)
class ExecutionHistory:
    """Execution history snapshot."""

    profiles: list[VerificationProfile]
    recent_runs: list[HistoryEvent]


@dataclass(frozen=True, slots=True)
class PendingVerification:
    """Pending verification snapshot."""

    pending_count: int
    pending_profiles: list[str]


@dataclass(frozen=True, slots=True)
class VerificationWorkspace:
    """Complete verification workspace snapshot."""

    profiles: list[VerificationProfile]
    execution_history: ExecutionHistory
    pending: PendingVerification
    last_execution: HistoryEvent | None


@dataclass(frozen=True, slots=True)
class DependencyChain:
    """Dependency chain snapshot."""

    file_path: str
    engine: str | None
    services: list[str]
    routers: list[str]
    endpoints: list[str]
    capabilities: list[str]
    mappers: list[str]
    view_models: list[str]
    pages: list[str]
    workspaces: list[str]
    components: list[str]
    tests: list[str]
    graph_renderers: list[str]


@dataclass(frozen=True, slots=True)
class DependencyExplorerResult:
    """Dependency explorer result."""

    file_path: str
    chain: DependencyChain | None
    found: bool
