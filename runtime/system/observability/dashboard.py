"""
Unified Dashboard Data — Program 7C

Generates runtime/generated/dashboard.json with Local, CI, and Combined telemetry.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .analytics import AnalyticsEngine
from .cost_analysis import CostAnalysis
from .dependency_growth import DependencyGrowthIntelligence
from .event_store import EngineeringEventStore
from .flaky_tests import FlakyTestIntelligence

REPO_ROOT = Path(__file__).resolve().parents[3]
DASHBOARD_PATH = REPO_ROOT / "runtime" / "generated" / "dashboard.json"


class DashboardGenerator:
    """Generates unified dashboard data."""

    def __init__(self, event_store: EngineeringEventStore | None = None) -> None:
        self._event_store = event_store or EngineeringEventStore()
        self._analytics_engine = AnalyticsEngine(self._event_store)

    def generate(self) -> dict[str, Any]:
        analytics = self._analytics_engine.compute()
        cost = CostAnalysis(self._event_store)
        growth = DependencyGrowthIntelligence()
        flaky = FlakyTestIntelligence(self._event_store)

        cost_data = {
            name: breakdown.to_dict() for name, breakdown in cost.compute().items()
        }
        growth_data = {
            name: record.to_dict() for name, record in growth.compute().items()
        }
        flaky_data = {
            name: record.to_dict() for name, record in flaky.compute().items()
        }

        return {
            "local": {
                "verification": analytics.local.get("verification", {}),
                "analytics": {
                    k: v for k, v in analytics.local.items() if k != "verification"
                },
                "cost": {
                    phase: data.get("local", {}) for phase, data in cost_data.items()
                },
            },
            "ci": {
                "verification": analytics.ci.get("verification", {}),
                "analytics": {
                    k: v for k, v in analytics.ci.items() if k != "verification"
                },
                "cost": {
                    phase: data.get("ci", {}) for phase, data in cost_data.items()
                },
            },
            "combined": {
                "health": {
                    "verification": analytics.combined.get("verification", {}),
                    "trends": analytics.combined.get("trends", {}),
                    "rolling_averages": analytics.combined.get("rolling_averages", {}),
                    "intent_frequency": analytics.combined.get("intent_frequency", {}),
                    "environment_frequency": analytics.combined.get(
                        "environment_frequency", {}
                    ),
                    "profile_usage": analytics.combined.get("profile_usage", {}),
                    "blast_radius": analytics.combined.get("blast_radius", {}),
                },
                "growth": growth_data,
                "flaky_tests": flaky_data,
            },
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def save(self, path: Path | None = None) -> None:
        target = path or DASHBOARD_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(self.generate(), f, indent=2, default=str)


def generate_dashboard(
    event_store: EngineeringEventStore | None = None,
) -> dict[str, Any]:
    generator = DashboardGenerator(event_store)
    generator.save()
    return generator.generate()
