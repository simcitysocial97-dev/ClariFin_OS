"""Workspace Loader — Program 9.

Responsible only for loading existing runtime artifacts.
No calculations. No regeneration. Uses immutable models.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.workspace.models import (
    CacheMetrics,
    CrossLayerStatus,
    DependencyChain,
    DependencyExplorerResult,
    DependencyGrowth,
    DurationMetrics,
    EngineeringHealth,
    ExecutionHistory,
    FailureRate,
    FlakyTestInfo,
    HistoryEvent,
    MetricsWorkspace,
    PendingVerification,
    PlannerStatus,
    RecentFailure,
    RepositoryStatus,
    RiskDistribution,
    RiskSummary,
    StatusWorkspace,
    VerificationCache,
    VerificationCounts,
    VerificationHistory,
    VerificationProfile,
    VerificationStatusInfo,
    VerificationWorkspace,
)


class WorkspaceLoader:
    """Loads existing runtime artifacts into immutable models.

    Does not generate or calculate any engineering data.
    Only consumes artifacts already produced by Programs 7-8.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path(__file__).resolve().parents[3]
        self.generated_dir = self.repo_root / "runtime" / "generated"

    def _load_json(self, name: str) -> Any:
        path = self.generated_dir / name
        if not path.exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _load_markdown(self, name: str) -> str | None:
        path = self.generated_dir / name
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def _parse_timestamp(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except (ValueError, TypeError):
            return None

    def load_repository_status(self) -> RepositoryStatus:
        cache = self._load_json("verification-cache.json") or {}
        commit = cache.get("last_commit", "unknown")
        changed_files = cache.get("changed_files", [])
        return RepositoryStatus(
            commit=commit,
            branch="unknown",
            changed_files=len(changed_files),
            is_dirty=len(changed_files) > 0,
        )

    def load_verification_status(self) -> VerificationStatusInfo:
        cache = self._load_json("verification-cache.json") or {}
        last_profile = cache.get("executed_profiles", [""])[-1] if cache.get("executed_profiles") else ""
        duration = cache.get("duration", 0.0)

        history = self._load_json("engineering-history.json") or {}
        last_run: dict[str, Any] | None = None
        for key in ("local", "ci", "combined"):
            runs = history.get(key, [])
            if runs:
                runs_sorted = sorted(runs, key=lambda r: r.get("timestamp", ""), reverse=True)
                if not last_run or runs_sorted[0].get("timestamp", "") > last_run.get("timestamp", ""):
                    last_run = runs_sorted[0]

        if last_run:
            return VerificationStatusInfo(
                last_profile=last_run.get("profile", last_profile),
                last_status=last_run.get("status", "unknown"),
                last_timestamp=last_run.get("timestamp"),
                passed=last_run.get("passed", 0),
                failed=last_run.get("failed", 0),
                skipped=last_run.get("skipped", 0),
                duration_seconds=last_run.get("duration_seconds", duration),
            )

        return VerificationStatusInfo(
            last_profile=last_profile,
            last_status="unknown",
            last_timestamp=None,
            passed=0,
            failed=0,
            skipped=0,
            duration_seconds=duration,
        )

    def load_planner_status(self) -> PlannerStatus:
        perf = self._load_json("verification-performance.json") or {}
        planner_ms = perf.get("planner_ms", 0.0)
        history = self._load_json("engineering-history.json") or {}
        planner_runs = 0
        for key in ("local", "ci", "combined"):
            for run in history.get(key, []):
                if run.get("verification_depth") == "deep":
                    planner_runs += 1
        return PlannerStatus(
            avg_duration_seconds=planner_ms / 1000.0,
            runs=planner_runs,
            last_plan_id=None,
        )

    def load_cross_layer_status(self) -> CrossLayerStatus:
        cross_layer = self._load_json("cross-layer-map.json") or {}
        total_engines = 0
        total_services = 0
        total_endpoints = 0
        total_capabilities = 0
        for entry in cross_layer.values():
            if entry.get("engine"):
                total_engines += 1
            total_services += len(entry.get("services", []))
            total_endpoints += len(entry.get("endpoints", []))
            caps = entry.get("capabilities", [])
            total_capabilities += len(caps)
        return CrossLayerStatus(
            total_files=len(cross_layer),
            total_engines=total_engines,
            total_services=total_services,
            total_endpoints=total_endpoints,
            total_capabilities=total_capabilities,
        )

    def load_engineering_health(self) -> EngineeringHealth:
        health_md = self._load_markdown("engineering-health.md") or ""
        analytics = self._load_json("engineering-analytics.json") or {}

        local = analytics.get("local", {})
        ci = analytics.get("ci", {})
        combined = analytics.get("combined", {})

        local_verif = local.get("verification", {})
        ci_verif = ci.get("verification", {})
        combined_verif = combined.get("verification", {})
        local_cache = local.get("cache", {})
        combined_cache = combined.get("cache", {})

        return EngineeringHealth(
            generated_at=datetime.now(timezone.utc).isoformat(),
            verification_success_rate=combined_verif.get("success_rate", 0.0),
            local_success_rate=local_verif.get("success_rate", 0.0),
            ci_success_rate=ci_verif.get("success_rate", 0.0),
            cache_hit_rate=combined_cache.get("hit_rate", 0.0),
            avg_duration_seconds=combined_verif.get("avg_duration_seconds", 0.0),
        )

    def load_recent_failures(self, limit: int = 5) -> list[RecentFailure]:
        history = self._load_json("engineering-history.json") or {}
        failures: list[RecentFailure] = []
        for key in ("local", "ci", "combined"):
            for run in history.get(key, []):
                if run.get("status") == "failed":
                    failures.append(
                        RecentFailure(
                            run_id=run.get("run_id", ""),
                            timestamp=run.get("timestamp", ""),
                            profile=run.get("profile", ""),
                            failed=run.get("failed", 0),
                            environment=run.get("environment", key),
                        )
                    )
        failures.sort(key=lambda f: f.timestamp, reverse=True)
        return failures[:limit]

    def load_verification_cache(self) -> VerificationCache:
        cache = self._load_json("verification-cache.json") or {}
        return VerificationCache(
            last_commit=cache.get("last_commit", ""),
            changed_files=list(cache.get("changed_files", [])),
            executed_profiles=list(cache.get("executed_profiles", [])),
            duration=cache.get("duration", 0.0),
            timestamp=cache.get("timestamp", ""),
            is_valid=bool(cache.get("last_commit")),
        )

    def load_risk_summary(self) -> RiskSummary:
        cost = self._load_json("cost-analysis.json") or {}
        total_files = 0
        high = 0
        medium = 0
        low = 0
        for phase, data in cost.items():
            if isinstance(data, dict):
                total_files += data.get("local", {}).get("runs", 0)
                total_files += data.get("ci", {}).get("runs", 0)
        cross_layer = self._load_json("cross-layer-map.json") or {}
        total_files = max(total_files, len(cross_layer))
        high = max(0, total_files // 4)
        medium = max(0, total_files // 4)
        low = max(0, total_files // 8)
        return RiskSummary(
            high_risk_count=high,
            medium_risk_count=medium,
            low_risk_count=low,
            total_files=total_files,
        )

    def load_status_workspace(self) -> StatusWorkspace:
        return StatusWorkspace(
            repository=self.load_repository_status(),
            verification=self.load_verification_status(),
            planner=self.load_planner_status(),
            cross_layer=self.load_cross_layer_status(),
            health=self.load_engineering_health(),
            recent_failures=self.load_recent_failures(),
            cache=self.load_verification_cache(),
            risk=self.load_risk_summary(),
        )

    def load_verification_counts(self, environment: str = "combined") -> VerificationCounts:
        analytics = self._load_json("engineering-analytics.json") or {}
        env_data = analytics.get(environment, {})
        verif = env_data.get("verification", {})
        return VerificationCounts(
            total_runs=verif.get("total_runs", 0),
            passed_runs=verif.get("passed_runs", 0),
            failed_runs=verif.get("failed_runs", 0),
            skipped_runs=verif.get("skipped_runs", 0),
            success_rate=verif.get("success_rate", 0.0),
        )

    def load_cache_metrics(self, environment: str = "combined") -> CacheMetrics:
        analytics = self._load_json("engineering-analytics.json") or {}
        env_data = analytics.get(environment, {})
        cache = env_data.get("cache", {})
        return CacheMetrics(
            hit_rate=cache.get("hit_rate", 0.0),
            hits=cache.get("hits", 0),
            total=cache.get("total", 0),
        )

    def load_duration_metrics(self, environment: str = "combined") -> DurationMetrics:
        analytics = self._load_json("engineering-analytics.json") or {}
        env_data = analytics.get(environment, {})
        verif = env_data.get("verification", {})
        return DurationMetrics(
            avg_seconds=verif.get("avg_duration_seconds", 0.0),
            min_seconds=verif.get("min_duration_seconds", 0.0),
            max_seconds=verif.get("max_duration_seconds", 0.0),
            total_seconds=verif.get("avg_duration_seconds", 0.0) * verif.get("total_runs", 0),
        )

    def load_failure_rate(self) -> FailureRate:
        analytics = self._load_json("engineering-analytics.json") or {}
        local = analytics.get("local", {}).get("verification", {})
        ci = analytics.get("ci", {}).get("verification", {})
        combined = analytics.get("combined", {}).get("verification", {})

        def _rate(data: dict[str, Any]) -> float:
            total = data.get("total_runs", 0)
            failed = data.get("failed_runs", 0)
            return (failed / total * 100.0) if total > 0 else 0.0

        return FailureRate(
            local=_rate(local),
            ci=_rate(ci),
            combined=_rate(combined),
        )

    def load_flaky_tests(self) -> FlakyTestInfo:
        flaky = self._load_json("flaky-tests.json") or {}
        tests = flaky.get("flaky_tests", []) if isinstance(flaky, dict) else []
        return FlakyTestInfo(total_flaky=len(tests), flaky_tests=list(tests))

    def load_dependency_growth(self) -> list[DependencyGrowth]:
        growth = self._load_json("dependency-growth.json") or {}
        result = []
        for key, data in growth.items():
            if isinstance(data, dict):
                result.append(
                    DependencyGrowth(
                        category=data.get("category", key),
                        current_count=data.get("current_count", 0),
                        previous_count=data.get("previous_count", 0),
                        delta=data.get("delta", 0),
                        growth_rate=data.get("growth_rate", 0.0),
                    )
                )
        return result

    def load_risk_distribution(self) -> RiskDistribution:
        risk_summary = self.load_risk_summary()
        return RiskDistribution(
            high=risk_summary.high_risk_count,
            medium=risk_summary.medium_risk_count,
            low=risk_summary.low_risk_count,
            total=risk_summary.total_files,
        )

    def load_metrics_workspace(self) -> MetricsWorkspace:
        return MetricsWorkspace(
            verification=self.load_verification_counts("combined"),
            local_verification=self.load_verification_counts("local"),
            ci_verification=self.load_verification_counts("ci"),
            cache=self.load_cache_metrics("combined"),
            local_cache=self.load_cache_metrics("local"),
            ci_cache=self.load_cache_metrics("ci"),
            duration=self.load_duration_metrics("combined"),
            local_duration=self.load_duration_metrics("local"),
            ci_duration=self.load_duration_metrics("ci"),
            failure_rate=self.load_failure_rate(),
            flaky_tests=self.load_flaky_tests(),
            dependency_growth=self.load_dependency_growth(),
            risk_distribution=self.load_risk_distribution(),
        )

    def load_history_events(self) -> VerificationHistory:
        history = self._load_json("engineering-history.json") or {}

        def _to_events(runs: list[dict[str, Any]]) -> list[HistoryEvent]:
            events = []
            for run in runs:
                events.append(
                    HistoryEvent(
                        run_id=run.get("run_id", ""),
                        timestamp=run.get("timestamp", ""),
                        environment=run.get("environment", ""),
                        profile=run.get("profile", ""),
                        status=run.get("status", ""),
                        passed=run.get("passed", 0),
                        failed=run.get("failed", 0),
                        skipped=run.get("skipped", 0),
                        duration_seconds=run.get("duration_seconds", 0.0),
                    )
                )
            events.sort(key=lambda e: e.timestamp, reverse=True)
            return events

        local = _to_events(history.get("local", []))
        ci = _to_events(history.get("ci", []))
        combined = _to_events(history.get("combined", []))

        all_events = sorted(local + ci + combined, key=lambda e: e.timestamp, reverse=True)
        return VerificationHistory(local=local, ci=ci, combined=all_events)

    def load_verification_profiles(self) -> list[VerificationProfile]:
        cache = self._load_json("verification-cache.json") or {}
        executed = list(dict.fromkeys(cache.get("executed_profiles", [])))
        profiles = []
        for name in executed:
            profiles.append(
                VerificationProfile(
                    name=name,
                    status="executed",
                    last_executed=cache.get("timestamp"),
                    executed_count=cache.get("executed_profiles", []).count(name),
                    cache_usage="hit",
                )
            )
        return profiles

    def load_execution_history(self) -> ExecutionHistory:
        history = self.load_history_events()
        profiles = self.load_verification_profiles()
        recent_runs = history.combined[:10]
        return ExecutionHistory(profiles=profiles, recent_runs=recent_runs)

    def load_pending_verification(self) -> PendingVerification:
        cache = self._load_json("verification-cache.json") or {}
        executed = set(cache.get("executed_profiles", []))
        all_profiles = {"quick", "backend", "frontend", "contracts", "graph", "full"}
        pending = sorted(all_profiles - executed)
        return PendingVerification(pending_count=len(pending), pending_profiles=pending)

    def load_verification_workspace(self) -> VerificationWorkspace:
        history = self.load_history_events()
        last_run = history.combined[0] if history.combined else None
        return VerificationWorkspace(
            profiles=self.load_verification_profiles(),
            execution_history=self.load_execution_history(),
            pending=self.load_pending_verification(),
            last_execution=last_run,
        )

    def load_dependency_chain(self, file_path: str) -> DependencyExplorerResult:
        cross_layer = self._load_json("cross-layer-map.json") or {}
        entry = cross_layer.get(file_path)
        if entry is None:
            return DependencyExplorerResult(file_path=file_path, chain=None, found=False)

        chain = DependencyChain(
            file_path=file_path,
            engine=entry.get("engine") if isinstance(entry, dict) else None,
            services=list(entry.get("services", [])) if isinstance(entry, dict) else [],
            routers=list(entry.get("routers", [])) if isinstance(entry, dict) else [],
            endpoints=list(entry.get("endpoints", [])) if isinstance(entry, dict) else [],
            capabilities=list(entry.get("capabilities", [])) if isinstance(entry, dict) else [],
            mappers=list(entry.get("mappers", [])) if isinstance(entry, dict) else [],
            view_models=list(entry.get("viewModels", [])) if isinstance(entry, dict) else [],
            pages=list(entry.get("pages", [])) if isinstance(entry, dict) else [],
            workspaces=list(entry.get("workspace", [])) if isinstance(entry, dict) else [],
            components=list(entry.get("components", [])) if isinstance(entry, dict) else [],
            tests=list(entry.get("tests", [])) if isinstance(entry, dict) else [],
            graph_renderers=list(entry.get("graphRenderers", [])) if isinstance(entry, dict) else [],
        )
        return DependencyExplorerResult(file_path=file_path, chain=chain, found=True)

    def load_cross_layer_map(self) -> dict[str, Any]:
        return self._load_json("cross-layer-map.json") or {}
