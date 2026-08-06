"""Engineering Intelligence pipeline — Program 14.0.

Runs Phases 1-9 in dependency order and writes the deliverable artifacts.

Ordering matters and is fixed:

    change -> blast -> plan -> memory -> risk -> repair -> ci -> cost -> state

Memory is built before risk because the CI risk dimension consumes observed
history. Everything downstream of ``change`` consumes already-computed
results, so the provider is read exactly once per run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.intelligence.platform.blast import (
    BlastRadius,
    compute_blast_radius,
)
from runtime.foundation.intelligence.platform.change import (
    ChangeIntelligence,
    analyze_changes,
)
from runtime.foundation.intelligence.platform.ci import (
    GitHubIntelligence,
    collect_github_intelligence,
)
from runtime.foundation.intelligence.platform.cost import (
    VerificationCost,
    estimate_cost,
)
from runtime.foundation.intelligence.platform.memory import (
    EngineeringMemory,
    build_memory,
)
from runtime.foundation.intelligence.platform.optimizer import (
    VerificationPlanIntel,
    optimize_verification,
)
from runtime.foundation.intelligence.platform.repair import (
    RepairPlan,
    build_repair_intelligence,
)
from runtime.foundation.intelligence.platform.resolver import (
    EntityResolver,
    get_resolver,
)
from runtime.foundation.intelligence.platform.risk import (
    EngineeringRisk,
    assess_risk,
)
from runtime.foundation.intelligence.platform.state import build_platform_state

__all__ = ["IntelligenceRun", "run_intelligence", "ARTIFACTS"]

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"

ARTIFACTS = (
    "change-intelligence.json",
    "blast-radius.json",
    "verification-plan.json",
    "engineering-risk.json",
    "repair-intelligence.json",
    "engineering-memory.json",
    "github-intelligence.json",
    "verification-cost.json",
    "platform-state.json",
)


@dataclass(frozen=True, slots=True)
class IntelligenceRun:
    change: ChangeIntelligence
    blast: BlastRadius
    plan: VerificationPlanIntel
    risk: EngineeringRisk
    repair: RepairPlan
    memory: EngineeringMemory
    github: GitHubIntelligence
    cost: VerificationCost
    state: dict[str, Any]
    written: tuple[Path, ...] = ()

    def documents(self) -> dict[str, dict[str, Any]]:
        return {
            "change-intelligence.json": self.change.to_dict(),
            "blast-radius.json": self.blast.to_dict(),
            "verification-plan.json": self.plan.to_dict(),
            "engineering-risk.json": self.risk.to_dict(),
            "repair-intelligence.json": self.repair.to_dict(),
            "engineering-memory.json": self.memory.to_dict(),
            "github-intelligence.json": self.github.to_dict(),
            "verification-cost.json": self.cost.to_dict(),
            "platform-state.json": self.state,
        }


def _write(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=False, default=str) + "\n",
        encoding="utf-8",
    )
    return path


def run_intelligence(
    paths: list[str] | None = None,
    resolver: EntityResolver | None = None,
    write: bool = True,
    collect_ci: bool = True,
    allow_logs: bool = False,
    generated_dir: Path | None = None,
) -> IntelligenceRun:
    """Execute the full intelligence layer and optionally persist artifacts."""
    res = resolver or get_resolver()
    gen = generated_dir or GENERATED_DIR

    change = analyze_changes(resolver=res, paths=paths)
    blast = compute_blast_radius(change, resolver=res)
    plan = optimize_verification(blast, resolver=res)
    memory = build_memory(generated_dir=gen)
    risk = assess_risk(
        change, blast, plan, resolver=res, memory=memory.as_risk_input()
    )
    repair = build_repair_intelligence(blast, resolver=res)

    if collect_ci:
        github = collect_github_intelligence(allow_logs=allow_logs)
    else:
        github = GitHubIntelligence(
            generated_at=datetime.now(timezone.utc).isoformat(),
            available=False,
            notes=("CI collection disabled for this run",),
        )

    cost = estimate_cost(plan)
    state = build_platform_state(
        change, blast, plan, risk, repair, memory, github, cost,
        resolver=res, generated_dir=gen,
    )

    run = IntelligenceRun(
        change=change,
        blast=blast,
        plan=plan,
        risk=risk,
        repair=repair,
        memory=memory,
        github=github,
        cost=cost,
        state=state,
    )

    written: list[Path] = []
    if write:
        for name, payload in run.documents().items():
            written.append(_write(gen / name, payload))

    return IntelligenceRun(
        change=change,
        blast=blast,
        plan=plan,
        risk=risk,
        repair=repair,
        memory=memory,
        github=github,
        cost=cost,
        state=state,
        written=tuple(written),
    )
