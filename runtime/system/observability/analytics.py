"""
Analytics Engine — Program 7C

Computes metrics independently for local, CI, and combined scopes.
All metrics derived from events, never from runtime state.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .event_store import EngineeringEventStore, create_event
from .repository import HybridHistory, RunRecord


REPO_ROOT = Path(__file__).resolve().parents[3]
ANALYTICS_PATH = REPO_ROOT / "runtime" / "generated" / "engineering-analytics.json"


@dataclass(frozen=True, slots=True)
class VerificationMetrics:
    """Per-scope verification metrics."""

    total_runs: int = 0
    passed_runs: int = 0
    failed_runs: int = 0
    success_rate: float = 0.0
    avg_duration_seconds: float = 0.0
    min_duration_seconds: float = 0.0
    max_duration_seconds: float = 0.0
    rolling_avg_duration_30: float = 0.0
    trend_direction: str = "stable"
    cache_hit_rate: float = 0.0


@dataclass(frozen=True, slots=True)
class AnalyticsReport:
    """Full analytics report split by environment."""

    local: dict[str, Any] = field(default_factory=dict)
    ci: dict[str, Any] = field(default_factory=dict)
    combined: dict[str, Any] = field(default_factory=dict)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "local": self.local,
            "ci": self.ci,
            "combined": self.combined,
            "generated_at": self.generated_at,
        }

    def save(self, path: Path | None = None) -> None:
        target = path or ANALYTICS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)


class AnalyticsEngine:
    """Computes analytics from event history."""

    def __init__(self, event_store: EngineeringEventStore | None = None) -> None:
        self._event_store = event_store or EngineeringEventStore()

    def compute(self) -> AnalyticsReport:
        events = self._event_store.load_events()
        local_events = [e for e in events if e.execution_context.get("environment") == "local"]
        ci_events = [e for e in events if e.execution_context.get("environment") == "ci"]

        local_metrics = self._compute_for_events(local_events)
        ci_metrics = self._compute_for_events(ci_events)
        combined_metrics = self._compute_for_events(events)

        return AnalyticsReport(
            local=local_metrics,
            ci=ci_metrics,
            combined=combined_metrics,
        )

    def _compute_for_events(self, events: list[Any]) -> dict[str, Any]:
        run_records = self._extract_run_records(events)
        verification = self._compute_verification_metrics(run_records)
        planner = self._compute_planner_metrics(events)
        execution = self._compute_execution_metrics(events)
        aggregation = self._compute_aggregation_metrics(events)
        cache_metrics = self._compute_cache_metrics(events)
        intent_frequency = self._compute_intent_frequency(events)
        environment_frequency = self._compute_environment_frequency(events)
        profile_usage = self._compute_profile_usage(events)
        blast_radius = self._compute_blast_radius(run_records)
        rolling = self._compute_rolling_averages(run_records)
        trends = self._compute_trends(run_records)

        return {
            "verification": verification,
            "planner": planner,
            "execution": execution,
            "aggregation": aggregation,
            "cache": cache_metrics,
            "intent_frequency": intent_frequency,
            "environment_frequency": environment_frequency,
            "profile_usage": profile_usage,
            "blast_radius": blast_radius,
            "rolling_averages": rolling,
            "trends": trends,
        }

    def _extract_run_records(self, events: list[Any]) -> list[RunRecord]:
        records: list[RunRecord] = []
        for event in events:
            if event.event_type == "VerificationCompleted":
                payload = event.payload
                ctx = event.execution_context
                records.append(
                    RunRecord(
                        run_id=event.event_id,
                        timestamp=event.timestamp,
                        environment=ctx.get("environment", "unknown"),
                        runner=ctx.get("runner", "unknown"),
                        verification_depth=ctx.get("verification_depth", "unknown"),
                        intent=ctx.get("intent", "unknown"),
                        trigger=ctx.get("trigger", "unknown"),
                        commit_sha=ctx.get("commit_sha", "unknown"),
                        branch=ctx.get("branch", "unknown"),
                        profile=payload.get("profile", "unknown"),
                        status=payload.get("status", "unknown"),
                        passed=payload.get("passed", 0),
                        failed=payload.get("failed", 0),
                        skipped=payload.get("skipped", 0),
                        duration_seconds=payload.get("duration_seconds", 0.0),
                        blast_radius=payload.get("blast_radius", {}),
                        evidence_count=payload.get("evidence_count", 0),
                        cache_hit=payload.get("cache_hit", False),
                        metadata=payload.get("metadata", {}),
                    )
                )
        return records

    def _compute_verification_metrics(self, records: list[RunRecord]) -> dict[str, Any]:
        if not records:
            return {"total_runs": 0, "success_rate": 0.0}
        passed = sum(1 for r in records if r.status == "passed")
        failed = sum(1 for r in records if r.status == "failed")
        durations = [r.duration_seconds for r in records if r.duration_seconds > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        return {
            "total_runs": len(records),
            "passed_runs": passed,
            "failed_runs": failed,
            "success_rate": round(passed / len(records), 4) if records else 0.0,
            "avg_duration_seconds": round(avg_duration, 2),
            "min_duration_seconds": round(min(durations), 2) if durations else 0.0,
            "max_duration_seconds": round(max(durations), 2) if durations else 0.0,
        }

    def _compute_planner_metrics(self, events: list[Any]) -> dict[str, Any]:
        durations = []
        for event in events:
            if event.event_type == "PlanningCompleted":
                durations.append(event.payload.get("duration_seconds", 0.0))
        if not durations:
            return {"avg_duration_seconds": 0.0, "runs": 0}
        return {
            "avg_duration_seconds": round(sum(durations) / len(durations), 2),
            "runs": len(durations),
        }

    def _compute_execution_metrics(self, events: list[Any]) -> dict[str, Any]:
        durations = []
        for event in events:
            if event.event_type == "ExecutionFinished":
                durations.append(event.payload.get("duration_seconds", 0.0))
        if not durations:
            return {"avg_duration_seconds": 0.0, "runs": 0}
        return {
            "avg_duration_seconds": round(sum(durations) / len(durations), 2),
            "runs": len(durations),
        }

    def _compute_aggregation_metrics(self, events: list[Any]) -> dict[str, Any]:
        durations = []
        for event in events:
            if event.event_type == "EvidenceGenerated":
                durations.append(event.payload.get("duration_seconds", 0.0))
        if not durations:
            return {"avg_duration_seconds": 0.0, "runs": 0}
        return {
            "avg_duration_seconds": round(sum(durations) / len(durations), 2),
            "runs": len(durations),
        }

    def _compute_cache_metrics(self, events: list[Any]) -> dict[str, Any]:
        hits = 0
        total = 0
        for event in events:
            if event.event_type == "VerificationCompleted":
                total += 1
                if event.payload.get("cache_hit"):
                    hits += 1
        if total == 0:
            return {"hit_rate": 0.0, "hits": 0, "total": 0}
        return {
            "hit_rate": round(hits / total, 4),
            "hits": hits,
            "total": total,
        }

    def _compute_intent_frequency(self, events: list[Any]) -> dict[str, int]:
        freq: dict[str, int] = defaultdict(int)
        for event in events:
            intent = event.execution_context.get("intent", "unknown")
            freq[intent] += 1
        return dict(freq)

    def _compute_environment_frequency(self, events: list[Any]) -> dict[str, int]:
        freq: dict[str, int] = defaultdict(int)
        for event in events:
            env = event.execution_context.get("environment", "unknown")
            freq[env] += 1
        return dict(freq)

    def _compute_profile_usage(self, events: list[Any]) -> dict[str, int]:
        freq: dict[str, int] = defaultdict(int)
        for event in events:
            if event.event_type == "VerificationCompleted":
                profile = event.payload.get("profile", "unknown")
                freq[profile] += 1
        return dict(freq)

    def _compute_blast_radius(self, records: list[RunRecord]) -> dict[str, Any]:
        if not records:
            return {"avg_engines": 0, "avg_services": 0, "avg_endpoints": 0, "avg_components": 0}
        total_engines = 0
        total_services = 0
        total_endpoints = 0
        total_components = 0
        count = 0
        for r in records:
            br = r.blast_radius
            if br:
                total_engines += len(br.get("affected_engines", []))
                total_services += len(br.get("affected_services", []))
                total_endpoints += len(br.get("affected_endpoints", []))
                total_components += len(br.get("affected_components", []))
                count += 1
        if count == 0:
            return {"avg_engines": 0, "avg_services": 0, "avg_endpoints": 0, "avg_components": 0}
        return {
            "avg_engines": round(total_engines / count, 2),
            "avg_services": round(total_services / count, 2),
            "avg_endpoints": round(total_endpoints / count, 2),
            "avg_components": round(total_components / count, 2),
        }

    def _compute_rolling_averages(self, records: list[RunRecord]) -> dict[str, Any]:
        if not records:
            return {"rolling_avg_30": 0.0, "window": 30}
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        window = min(30, len(sorted_records))
        recent = sorted_records[-window:]
        durations = [r.duration_seconds for r in recent if r.duration_seconds > 0]
        avg = sum(durations) / len(durations) if durations else 0.0
        return {"rolling_avg_30": round(avg, 2), "window": window}

    def _compute_trends(self, records: list[RunRecord]) -> dict[str, Any]:
        if len(records) < 2:
            return {"duration_trend": "stable", "success_rate_trend": "stable", "data_points": len(records)}
        sorted_records = sorted(records, key=lambda r: r.timestamp)
        mid = len(sorted_records) // 2
        first_half = sorted_records[:mid]
        second_half = sorted_records[mid:]
        first_durations = [r.duration_seconds for r in first_half if r.duration_seconds > 0]
        second_durations = [r.duration_seconds for r in second_half if r.duration_seconds > 0]
        first_avg = sum(first_durations) / len(first_durations) if first_durations else 0.0
        second_avg = sum(second_durations) / len(second_durations) if second_durations else 0.0
        duration_trend = "increasing" if second_avg > first_avg * 1.1 else "decreasing" if second_avg < first_avg * 0.9 else "stable"
        first_pass_rate = sum(1 for r in first_half if r.status == "passed") / len(first_half) if first_half else 0.0
        second_pass_rate = sum(1 for r in second_half if r.status == "passed") / len(second_half) if second_half else 0.0
        success_trend = "improving" if second_pass_rate > first_pass_rate else "degrading" if second_pass_rate < first_pass_rate else "stable"
        return {
            "duration_trend": duration_trend,
            "success_rate_trend": success_trend,
            "data_points": len(records),
        }


def generate_analytics(event_store: EngineeringEventStore | None = None) -> AnalyticsReport:
    engine = AnalyticsEngine(event_store)
    report = engine.compute()
    report.save()
    return report
