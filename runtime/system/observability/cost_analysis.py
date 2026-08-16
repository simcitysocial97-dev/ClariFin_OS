"""
Cost Analysis — Program 7C

Separate cost tracking for local and CI runs.
Never combines fast local runs with deep CI runs.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .event_store import EngineeringEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]
COST_ANALYSIS_PATH = REPO_ROOT / "runtime" / "generated" / "cost-analysis.json"


@dataclass
class CostBreakdown:
    """Cost breakdown for a specific phase."""

    phase: str
    local_total_seconds: float = 0.0
    local_runs: int = 0
    ci_total_seconds: float = 0.0
    ci_runs: int = 0
    combined_total_seconds: float = 0.0
    combined_runs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "local": {
                "total_seconds": round(self.local_total_seconds, 2),
                "runs": self.local_runs,
                "avg_seconds": round(self.local_total_seconds / self.local_runs, 2) if self.local_runs else 0.0,
            },
            "ci": {
                "total_seconds": round(self.ci_total_seconds, 2),
                "runs": self.ci_runs,
                "avg_seconds": round(self.ci_total_seconds / self.ci_runs, 2) if self.ci_runs else 0.0,
            },
            "combined": {
                "total_seconds": round(self.combined_total_seconds, 2),
                "runs": self.combined_runs,
                "avg_seconds": round(self.combined_total_seconds / self.combined_runs, 2) if self.combined_runs else 0.0,
            },
        }


class CostAnalysis:
    """Computes cost analysis from events."""

    PHASE_EVENT_MAP = {
        "Planning": "PlanningCompleted",
        "Execution": "ExecutionFinished",
        "Aggregation": "EvidenceGenerated",
        "Report generation": "VerificationCompleted",
        "Cache lookup": "VerificationCompleted",
        "Evidence generation": "EvidenceGenerated",
        "Cross-layer analysis": "PlanningCompleted",
    }

    def __init__(self, event_store: EngineeringEventStore | None = None) -> None:
        self._event_store = event_store or EngineeringEventStore()

    def compute(self) -> dict[str, CostBreakdown]:
        events = self._event_store.load_events()
        breakdowns: dict[str, CostBreakdown] = {
            phase: CostBreakdown(phase=phase)
            for phase in self.PHASE_EVENT_MAP
        }

        for event in events:
            env = event.execution_context.get("environment", "unknown")
            duration = event.payload.get("duration_seconds", 0.0)
            phase = self._resolve_phase(event.event_type)

            if phase and phase in breakdowns:
                if env == "local":
                    breakdowns[phase].local_total_seconds += duration
                    breakdowns[phase].local_runs += 1
                elif env == "ci":
                    breakdowns[phase].ci_total_seconds += duration
                    breakdowns[phase].ci_runs += 1
                breakdowns[phase].combined_total_seconds += duration
                breakdowns[phase].combined_runs += 1

        return breakdowns

    def _resolve_phase(self, event_type: str) -> str | None:
        for phase, mapped_event in self.PHASE_EVENT_MAP.items():
            if mapped_event == event_type:
                return phase
        return None

    def save(self, path: Path | None = None) -> None:
        target = path or COST_ANALYSIS_PATH
        target.parent.mkdir(parents=True, exist_ok=True)
        data = {name: breakdown.to_dict() for name, breakdown in self.compute().items()}
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)


def generate_cost_analysis(event_store: EngineeringEventStore | None = None) -> dict[str, Any]:
    analysis = CostAnalysis(event_store)
    analysis.save()
    return {name: breakdown.to_dict() for name, breakdown in analysis.compute().items()}
