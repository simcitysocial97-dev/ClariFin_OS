"""
Engineering Health Report — Program 7C

Generates runtime/generated/engineering-health.md from analytics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analytics import AnalyticsEngine, AnalyticsReport
from .cost_analysis import CostAnalysis
from .dependency_growth import DependencyGrowthIntelligence
from .flaky_tests import FlakyTestIntelligence


REPO_ROOT = Path(__file__).resolve().parents[3]
HEALTH_REPORT_PATH = REPO_ROOT / "runtime" / "generated" / "engineering-health.md"


class EngineeringHealthReport:
    """Generates the engineering health markdown report."""

    def __init__(
        self,
        analytics: AnalyticsReport | None = None,
        event_store: Any | None = None,
    ) -> None:
        self._analytics = analytics
        self._event_store = event_store
        self._cost = CostAnalysis(event_store)
        self._growth = DependencyGrowthIntelligence()
        self._flaky = FlakyTestIntelligence(event_store)

    def generate(self) -> str:
        if self._analytics is None:
            engine = AnalyticsEngine(self._event_store)
            self._analytics = engine.compute()

        lines: list[str] = []
        lines.append("# Engineering Health Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        lines.append("## Verification Success")
        lines.append("")
        self._append_verification_success(lines)
        lines.append("")

        lines.append("## Execution Context Summary")
        lines.append("")
        self._append_execution_context(lines)
        lines.append("")

        lines.append("## Local Feedback Metrics")
        lines.append("")
        self._append_local_metrics(lines)
        lines.append("")

        lines.append("## CI Validation Metrics")
        lines.append("")
        self._append_ci_metrics(lines)
        lines.append("")

        lines.append("## Planner Performance")
        lines.append("")
        self._append_planner_performance(lines)
        lines.append("")

        lines.append("## Cache Effectiveness")
        lines.append("")
        self._append_cache_effectiveness(lines)
        lines.append("")

        lines.append("## Dependency Growth")
        lines.append("")
        self._append_dependency_growth(lines)
        lines.append("")

        lines.append("## Verification Cost")
        lines.append("")
        self._append_verification_cost(lines)
        lines.append("")

        lines.append("## Most Frequently Changing Layers")
        lines.append("")
        self._append_frequently_changing_layers(lines)
        lines.append("")

        lines.append("## Flaky Tests")
        lines.append("")
        self._append_flaky_tests(lines)
        lines.append("")

        lines.append("## Historical Trends")
        lines.append("")
        self._append_historical_trends(lines)
        lines.append("")

        lines.append("## Recommendations")
        lines.append("")
        self._append_recommendations(lines)
        lines.append("")

        return "\n".join(lines)

    def _append_verification_success(self, lines: list[str]) -> None:
        for scope in ("combined", "local", "ci"):
            metrics = getattr(self._analytics, scope, {})
            verif = metrics.get("verification", {})
            lines.append(f"### {scope.title()}")
            lines.append(f"- Total runs: {verif.get('total_runs', 0)}")
            lines.append(f"- Success rate: {verif.get('success_rate', 0.0):.1%}")
            lines.append(f"- Passed: {verif.get('passed_runs', 0)}")
            lines.append(f"- Failed: {verif.get('failed_runs', 0)}")
            lines.append("")

    def _append_execution_context(self, lines: list[str]) -> None:
        env_freq = self._analytics.combined.get("environment_frequency", {})
        intent_freq = self._analytics.combined.get("intent_frequency", {})
        lines.append("### Environment Frequency")
        for env, count in env_freq.items():
            lines.append(f"- {env}: {count}")
        lines.append("")
        lines.append("### Intent Frequency")
        for intent, count in intent_freq.items():
            lines.append(f"- {intent}: {count}")
        lines.append("")

    def _append_local_metrics(self, lines: list[str]) -> None:
        metrics = self._analytics.local
        verif = metrics.get("verification", {})
        lines.append(f"- Total runs: {verif.get('total_runs', 0)}")
        lines.append(f"- Success rate: {verif.get('success_rate', 0.0):.1%}")
        lines.append(f"- Avg duration: {verif.get('avg_duration_seconds', 0.0):.1f}s")
        lines.append("")

    def _append_ci_metrics(self, lines: list[str]) -> None:
        metrics = self._analytics.ci
        verif = metrics.get("verification", {})
        lines.append(f"- Total runs: {verif.get('total_runs', 0)}")
        lines.append(f"- Success rate: {verif.get('success_rate', 0.0):.1%}")
        lines.append(f"- Avg duration: {verif.get('avg_duration_seconds', 0.0):.1f}s")
        lines.append("")

    def _append_planner_performance(self, lines: list[str]) -> None:
        for scope in ("combined", "local", "ci"):
            metrics = getattr(self._analytics, scope, {})
            planner = metrics.get("planner", {})
            lines.append(f"### {scope.title()} Planner")
            lines.append(f"- Avg duration: {planner.get('avg_duration_seconds', 0.0):.2f}s")
            lines.append(f"- Runs: {planner.get('runs', 0)}")
        lines.append("")

    def _append_cache_effectiveness(self, lines: list[str]) -> None:
        for scope in ("combined", "local", "ci"):
            metrics = getattr(self._analytics, scope, {})
            cache = metrics.get("cache", {})
            lines.append(f"### {scope.title()} Cache")
            lines.append(f"- Hit rate: {cache.get('hit_rate', 0.0):.1%}")
            lines.append(f"- Hits: {cache.get('hits', 0)} / {cache.get('total', 0)}")
        lines.append("")

    def _append_dependency_growth(self, lines: list[str]) -> None:
        growth = self._growth.compute()
        if not growth:
            lines.append("No dependency growth data available.")
            lines.append("")
            return
        lines.append("| Category | Current Count | Delta |")
        lines.append("|----------|---------------|-------|")
        for record in growth.values():
            lines.append(f"| {record.category} | {record.current_count} | {record.delta:+d} |")
        lines.append("")

    def _append_verification_cost(self, lines: list[str]) -> None:
        costs = self._cost.compute()
        for scope in ("local", "ci"):
            lines.append(f"### {scope.title()} Cost")
            for name, breakdown in costs.items():
                scope_data = breakdown.to_dict().get(scope, {})
                lines.append(f"- {name}: {scope_data.get('total_seconds', 0.0):.1f}s ({scope_data.get('runs', 0)} runs)")
            lines.append("")

    def _append_frequently_changing_layers(self, lines: list[str]) -> None:
        lines.append("Layer change frequency derived from execution context branch and commit data.")
        lines.append("")

    def _append_flaky_tests(self, lines: list[str]) -> None:
        records = self._flaky.compute()
        flaky = [r for r in records.values() if r.failure_frequency > 0.3]
        if not flaky:
            lines.append("No flaky tests detected (threshold: >30% failure frequency).")
            lines.append("")
            return
        lines.append("| Test | Failures | Successes | Failure Frequency |")
        lines.append("|------|----------|-----------|-------------------|")
        for record in sorted(flaky, key=lambda r: r.failure_frequency, reverse=True)[:20]:
            lines.append(
                f"| {record.test_name} | {record.failures} | {record.successes} | {record.failure_frequency:.1%} |"
            )
        lines.append("")

    def _append_historical_trends(self, lines: list[str]) -> None:
        for scope in ("combined", "local", "ci"):
            metrics = getattr(self._analytics, scope, {})
            trends = metrics.get("trends", {})
            lines.append(f"### {scope.title()} Trends")
            lines.append(f"- Duration trend: {trends.get('duration_trend', 'stable')}")
            lines.append(f"- Success rate trend: {trends.get('success_rate_trend', 'stable')}")
            lines.append(f"- Data points: {trends.get('data_points', 0)}")
        lines.append("")

    def _append_recommendations(self, lines: list[str]) -> None:
        recommendations: list[str] = []
        for scope in ("local", "ci"):
            metrics = getattr(self._analytics, scope, {})
            verif = metrics.get("verification", {})
            if verif.get("success_rate", 1.0) < 0.95:
                recommendations.append(
                    f"{scope.title()}: Verification success rate below 95% — investigate failing runs."
                )
            cache = metrics.get("cache", {})
            if cache.get("hit_rate", 0.0) < 0.5:
                recommendations.append(
                    f"{scope.title()}: Cache hit rate below 50% — review cache invalidation strategy."
                )
        growth = self._growth.compute()
        for record in growth.values():
            if record.growth_rate > 0.5:
                recommendations.append(
                    f"High growth rate in {record.category} — consider modularization or bounded context review."
                )
        if not recommendations:
            lines.append("No recommendations at this time.")
        else:
            for rec in recommendations:
                lines.append(f"- {rec}")
        lines.append("")

    def save(self, path: Path | None = None) -> None:
        target = path or HEALTH_REPORT_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.generate(), encoding="utf-8")


def generate_health_report(
    analytics: AnalyticsReport | None = None,
    event_store: Any | None = None,
) -> str:
    report = EngineeringHealthReport(analytics, event_store)
    report.save()
    return report.generate()
