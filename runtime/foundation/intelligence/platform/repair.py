"""Phase 5 — Repair Intelligence.

Given a defect, produce an ordered, evidence-backed repair strategy.

A "defect" here is a structured observation: a failing test, a failing CI
step, or a runtime-detected issue. Defects are supplied by the caller or read
from artifacts the runtime already produces (``runtime-defects.json``,
``normalized-issues.json``). This module never invents defects and never
guesses which file is at fault: the defect's own evidence path is resolved
through the canonical provider to find owners.

Repair order is topological: fix providers before consumers. That ordering is
taken from the canonical dependency/ownership graphs, so it is reproducible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.intelligence.platform.blast import BlastRadius
from runtime.foundation.intelligence.platform.resolver import (
    EntityRef,
    EntityResolver,
    get_resolver,
)

__all__ = ["Defect", "RepairPlan", "load_defects", "build_repair_intelligence"]

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"


@dataclass(frozen=True, slots=True)
class Defect:
    id: str
    source: str
    summary: str
    paths: tuple[str, ...] = ()
    severity: str = "unknown"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "summary": self.summary,
            "paths": list(self.paths),
            "severity": self.severity,
        }


@dataclass(frozen=True, slots=True)
class RepairPlan:
    generated_at: str
    defects: tuple[Defect, ...]
    items: tuple[dict[str, Any], ...]
    rollback: dict[str, Any]
    total_defects: int = 0
    deferred: tuple[dict[str, Any], ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": "repair-intelligence/v1",
            "generated_at": self.generated_at,
            "provider": "runtime.foundation.architecture.get_architecture",
            "defect_count": self.total_defects or len(self.defects),
            "planned_count": len(self.defects),
            "deferred_count": len(self.deferred),
            "prioritization": (
                "defects are ordered by severity; the highest-severity "
                f"{len(self.defects)} are fully planned, the remainder are listed "
                "as deferred"
            ),
            "defects": [d.to_dict() for d in self.defects],
            "repairs": list(self.items),
            "deferred": list(self.deferred),
            "rollback_strategy": self.rollback,
        }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def load_defects(generated_dir: Path | None = None) -> list[Defect]:
    """Load defects from artifacts the runtime already produces."""
    gen = generated_dir or GENERATED_DIR
    defects: list[Defect] = []

    data = _read_json(gen / "runtime-defects.json")
    if isinstance(data, dict):
        entries = data.get("defects") or data.get("issues") or []
        for i, entry in enumerate(entries if isinstance(entries, list) else []):
            if not isinstance(entry, dict):
                continue
            paths = [
                p
                for p in (
                    entry.get("path"),
                    entry.get("file"),
                    entry.get("location"),
                )
                if isinstance(p, str) and p
            ]
            defects.append(
                Defect(
                    id=str(entry.get("id", f"runtime-defect-{i}")),
                    source="runtime-defects.json",
                    summary=str(
                        entry.get("description")
                        or entry.get("message")
                        or entry.get("title")
                        or "unspecified runtime defect"
                    ),
                    paths=tuple(paths),
                    severity=str(entry.get("severity", "unknown")),
                )
            )

    normalized = _read_json(gen / "normalized-issues.json")
    if isinstance(normalized, dict):
        entries = normalized.get("issues") or []
        for i, entry in enumerate(entries if isinstance(entries, list) else []):
            if not isinstance(entry, dict):
                continue
            paths = [
                p
                for p in [entry.get("path"), entry.get("file")]
                if isinstance(p, str) and p
            ]
            defects.append(
                Defect(
                    id=str(entry.get("id", f"normalized-issue-{i}")),
                    source="normalized-issues.json",
                    summary=str(entry.get("message") or entry.get("title") or "issue"),
                    paths=tuple(paths),
                    severity=str(entry.get("severity", "unknown")),
                )
            )

    return defects


def _build_dependency_ranks(res: EntityResolver) -> dict[str, int]:
    """Precompute provider-before-consumer rank for every entity, once.

    Rank == number of outgoing dependency edges. Providers (low fan-out) are
    repaired before consumers. Computed in a single pass over the dependency
    graph so repair planning stays linear in the number of defects.
    """
    ranks: dict[str, int] = {}
    for edge in res.arch.dependency.edges:
        entity = res.resolve_node(edge.source)
        if entity is not None:
            ranks[entity.ref] = ranks.get(entity.ref, 0) + 1
    return ranks


# Defects are ordered by severity so the most important ones are planned first.
_SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "error": 1,
    "medium": 2,
    "warning": 3,
    "low": 4,
    "info": 5,
    "unknown": 6,
}

# Cap on fully-planned defects. The remainder are still counted and reported,
# but producing 400+ identical repair plans is noise, not intelligence.
MAX_PLANNED_DEFECTS = 25


def build_repair_intelligence(
    blast: BlastRadius,
    defects: list[Defect] | None = None,
    resolver: EntityResolver | None = None,
    max_planned: int = MAX_PLANNED_DEFECTS,
) -> RepairPlan:
    """Produce ordered repair guidance for the supplied defects."""
    res = resolver or get_resolver()
    arch = res.arch
    found = defects if defects is not None else load_defects()
    ranks = _build_dependency_ranks(res)

    def rank_of(ref: EntityRef) -> int:
        return ranks.get(ref.ref, 0)

    prioritized = sorted(
        found,
        key=lambda d: (_SEVERITY_ORDER.get(d.severity.lower(), 6), d.id),
    )
    planned = prioritized[:max_planned]
    deferred = prioritized[max_planned:]

    items: list[dict[str, Any]] = []

    for defect in planned:
        # Root cause: resolve the defect's evidence paths through the provider.
        owners: list[EntityRef] = []
        for path in defect.paths:
            owners.extend(res.classify_path(path))
        if not owners:
            # Fall back to the directly changed surface, which is still
            # evidence rather than a guess.
            owners = [n.ref for n in blast.direct]

        unique_owners = {o.ref: o for o in owners}
        ordered_owners = sorted(
            unique_owners.values(), key=lambda r: (rank_of(r), r.ref)
        )

        capabilities: set[str] = set()
        tests: set[str] = set()
        workflows: set[str] = set()

        for owner in ordered_owners:
            engine = None
            if owner.kind == "engine":
                engine = arch.engines.get(owner.key)
            else:
                eng_ref = res.owning_engine(owner.path) if owner.path else None
                if eng_ref is not None:
                    engine = arch.engines.get(eng_ref.key)
            if engine is not None:
                capabilities.update(engine.capabilities)
                tests.update(engine.tests)
                for cap_name in engine.capabilities:
                    cap = arch.capabilities.get(cap_name)
                    if cap is not None:
                        workflows.update(cap.workspaces)

        # Verification order mirrors repair order: unit -> contract -> e2e.
        verification_order = []
        if tests:
            verification_order.append(
                {
                    "step": 1,
                    "action": "run impacted unit tests",
                    "targets": sorted(tests),
                }
            )
        if capabilities:
            verification_order.append(
                {
                    "step": len(verification_order) + 1,
                    "action": "run contract verification for affected capabilities",
                    "targets": sorted(capabilities),
                }
            )
        if workflows:
            verification_order.append(
                {
                    "step": len(verification_order) + 1,
                    "action": "run workspace/e2e verification",
                    "targets": sorted(workflows),
                }
            )

        # Confidence: how much of the defect was provider-explainable.
        explained = sum(1 for p in defect.paths if res.classify_path(p))
        total = max(1, len(defect.paths))
        confidence = round(explained / total, 3) if defect.paths else 0.4

        items.append(
            {
                "defect_id": defect.id,
                "root_cause": {
                    "entities": [o.to_dict() for o in ordered_owners[:10]],
                    "basis": (
                        "provider path resolution"
                        if defect.paths
                        else "directly changed surface (defect had no path evidence)"
                    ),
                    "summary": defect.summary,
                },
                "affected_owners": [o.ref for o in ordered_owners],
                "affected_capabilities": sorted(capabilities),
                "affected_tests": sorted(tests),
                "affected_workflows": sorted(workflows),
                "repair_order": [
                    {
                        "step": i + 1,
                        "target": owner.ref,
                        "path": owner.path,
                        "rationale": (
                            f"dependency rank {rank_of(owner)} "
                            "(providers repaired before consumers)"
                        ),
                    }
                    for i, owner in enumerate(ordered_owners[:10])
                ],
                "verification_order": verification_order,
                "confidence": confidence,
            }
        )

    rollback = {
        "strategy": "revert-by-ownership-root",
        "steps": [
            "identify the smallest changed ownership root from change-intelligence.json",
            "git revert the commits touching that root only",
            "re-run the verification units listed in verification-plan.json",
            "if endpoints were impacted, re-run contract verification before merge",
        ],
        "safe_revert_units": sorted(
            {n.ref.key for n in blast.direct if n.ref.kind == "engine"}
        ),
    }

    return RepairPlan(
        generated_at=datetime.now(timezone.utc).isoformat(),
        defects=tuple(planned),
        items=tuple(items),
        rollback=rollback,
        total_defects=len(found),
        deferred=tuple(
            {"defect_id": d.id, "severity": d.severity, "source": d.source}
            for d in deferred
        ),
    )
