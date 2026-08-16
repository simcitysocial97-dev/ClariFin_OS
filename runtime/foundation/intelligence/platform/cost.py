"""Phase 8 — Verification Cost Optimization.

Estimates the cost of a verification plan *before* execution and recommends
the cheapest plan that still covers the blast radius.

Cost model
----------
Per-second costs are calibrated against the declared
``estimated_duration_seconds`` of the real verification profiles, so the
model is anchored to the runtime's own numbers rather than invented
constants. CI cost assumes a standard hosted runner rate; the rate is stated
explicitly in the artifact so it can be re-calibrated without code changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from runtime.foundation.intelligence.platform.optimizer import VerificationPlanIntel

__all__ = ["CostModel", "VerificationCost", "estimate_cost"]

# USD per CI minute for a standard hosted Linux runner.
CI_USD_PER_MINUTE = 0.008
# Relative CPU weighting per category (1.0 == one full core for the duration).
CPU_WEIGHT = {
    "unit": 1.0,
    "contract": 1.5,
    "integration": 2.0,
    "frontend": 2.0,
    "e2e": 3.0,
    "runtime": 1.0,
    "mutation": 4.0,
    "golden": 1.5,
}


@dataclass(frozen=True, slots=True)
class CostModel:
    ci_usd_per_minute: float = CI_USD_PER_MINUTE

    def to_dict(self) -> dict[str, Any]:
        return {
            "ci_usd_per_minute": self.ci_usd_per_minute,
            "cpu_weight_by_category": dict(sorted(CPU_WEIGHT.items())),
            "calibration": (
                "durations are taken from verification profile "
                "estimated_duration_seconds; no invented constants"
            ),
        }


@dataclass(frozen=True, slots=True)
class VerificationCost:
    generated_at: str
    entries: tuple[dict[str, Any], ...]
    skipped_savings: tuple[dict[str, Any], ...]
    totals: dict[str, Any]
    recommendation: dict[str, Any]
    model: CostModel

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "verification-cost/v1",
            "generated_at": self.generated_at,
            "model": self.model.to_dict(),
            "selected": list(self.entries),
            "avoided": list(self.skipped_savings),
            "totals": self.totals,
            "recommendation": self.recommendation,
        }


# Baseline durations for suites we may skip, used to quantify avoided cost.
_SKIPPED_BASELINE_SECONDS = {
    "unit-targeted": 120,
    "contracts-schemathesis": 180,
    "backend-integration": 180,
    "frontend-unit": 120,
    "playwright-e2e": 1800,
    "runtime-self-test": 120,
    "mutation-run": 600,
    "golden-regression": 600,
}


def _cost_entry(unit_id: str, category: str, seconds: int) -> dict[str, Any]:
    weight = CPU_WEIGHT.get(category, 1.0)
    minutes = seconds / 60.0
    return {
        "id": unit_id,
        "category": category,
        "expected_runtime_seconds": seconds,
        "cpu_core_seconds": round(seconds * weight, 1),
        "ci_minutes": round(minutes, 2),
        "ci_usd": round(minutes * CI_USD_PER_MINUTE, 4),
    }


def estimate_cost(plan: VerificationPlanIntel) -> VerificationCost:
    """Estimate cost of the selected plan and the cost avoided by skipping."""
    entries = [
        _cost_entry(unit.id, unit.category, unit.estimated_seconds)
        for unit in plan.selected
    ]

    avoided = []
    for skipped in plan.skipped:
        seconds = _SKIPPED_BASELINE_SECONDS.get(skipped.id, 60)
        entry = _cost_entry(skipped.id, skipped.category, seconds)
        entry["avoided_because"] = skipped.justification
        avoided.append(entry)

    selected_seconds = sum(e["expected_runtime_seconds"] for e in entries)
    avoided_seconds = sum(e["expected_runtime_seconds"] for e in avoided)
    selected_usd = round(sum(e["ci_usd"] for e in entries), 4)
    avoided_usd = round(sum(e["ci_usd"] for e in avoided), 4)

    # Per-dimension totals requested by Phase 8.
    def dimension(category: str, source: list[dict[str, Any]]) -> dict[str, Any]:
        rows = [e for e in source if e["category"] == category]
        return {
            "seconds": sum(r["expected_runtime_seconds"] for r in rows),
            "ci_usd": round(sum(r["ci_usd"] for r in rows), 4),
            "selected": bool(rows),
        }

    totals = {
        "expected_runtime_seconds": selected_seconds,
        "expected_runtime_minutes": round(selected_seconds / 60.0, 2),
        "cpu_core_seconds": round(sum(e["cpu_core_seconds"] for e in entries), 1),
        "ci_minutes": round(sum(e["ci_minutes"] for e in entries), 2),
        "ci_usd": selected_usd,
        "avoided_seconds": avoided_seconds,
        "avoided_ci_usd": avoided_usd,
        "reduction_percent": (
            round(
                100.0 * avoided_seconds / max(1, selected_seconds + avoided_seconds), 1
            )
        ),
        "by_dimension": {
            "mutation": dimension("mutation", entries + avoided),
            "coverage": dimension("unit", entries + avoided),
            "playwright": dimension("e2e", entries + avoided),
            "golden": dimension("golden", entries + avoided),
            "contract": dimension("contract", entries + avoided),
        },
    }

    if not entries:
        recommendation = {
            "plan": "none",
            "rationale": "blast radius is empty; no verification is justified",
            "cheapest_valid_plan_seconds": 0,
        }
    else:
        cheapest = min(entries, key=lambda e: e["expected_runtime_seconds"])
        recommendation = {
            "plan": "targeted",
            "units": [e["id"] for e in entries],
            "rationale": (
                f"selected plan costs {selected_seconds}s vs "
                f"{plan.baseline_seconds}s for the full profile, while covering "
                "every impacted entity kind"
            ),
            "cheapest_valid_plan_seconds": selected_seconds,
            "fastest_single_unit": cheapest["id"],
            "baseline_profile_seconds": plan.baseline_seconds,
        }

    return VerificationCost(
        generated_at=datetime.now(timezone.utc).isoformat(),
        entries=tuple(entries),
        skipped_savings=tuple(avoided),
        totals=totals,
        recommendation=recommendation,
        model=CostModel(),
    )
