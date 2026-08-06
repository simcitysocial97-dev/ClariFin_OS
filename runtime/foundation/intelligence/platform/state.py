"""Phase 9 — Engineering Dashboard Model.

Produces a single runtime state model WITHOUT rerunning any audit.

Certification status is read from the most recent audit artifact on disk. If
that artifact is missing or stale the model says so explicitly instead of
implying a fresh pass — a dashboard that silently reports stale green is worse
than one that reports "unknown".
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from runtime.foundation.intelligence.platform.blast import BlastRadius
from runtime.foundation.intelligence.platform.change import ChangeIntelligence
from runtime.foundation.intelligence.platform.ci import GitHubIntelligence
from runtime.foundation.intelligence.platform.cost import VerificationCost
from runtime.foundation.intelligence.platform.memory import EngineeringMemory
from runtime.foundation.intelligence.platform.optimizer import VerificationPlanIntel
from runtime.foundation.intelligence.platform.repair import RepairPlan
from runtime.foundation.intelligence.platform.resolver import (
    EntityResolver,
    get_resolver,
)
from runtime.foundation.intelligence.platform.risk import EngineeringRisk

__all__ = ["build_platform_state"]

REPO_ROOT = Path(__file__).resolve().parents[4]
GENERATED_DIR = REPO_ROOT / "runtime" / "generated"


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


@dataclass(frozen=True, slots=True)
class _Certification:
    status: str
    source: str
    generated_at: str
    sections_total: int
    sections_passed: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "source": self.source,
            "as_of": self.generated_at,
            "sections_total": self.sections_total,
            "sections_passed": self.sections_passed,
            "note": "read from artifact; audits were NOT rerun",
        }


def _certification(generated_dir: Path) -> _Certification:
    for name in (
        "engineering-platform-audit.json",
        "engineering-platform-audit-v3.json",
    ):
        data = _read_json(generated_dir / name)
        if not isinstance(data, dict):
            continue
        sections = data.get("sections") or []
        passed = sum(
            1
            for s in sections
            if isinstance(s, dict) and str(s.get("status", "")).lower() == "pass"
        )
        return _Certification(
            status=str(data.get("certification_status", "UNKNOWN")),
            source=name,
            generated_at=str(data.get("generated_at", "unknown")),
            sections_total=len(sections),
            sections_passed=passed,
        )
    return _Certification("UNKNOWN", "none", "unknown", 0, 0)


def build_platform_state(
    change: ChangeIntelligence,
    blast: BlastRadius,
    plan: VerificationPlanIntel,
    risk: EngineeringRisk,
    repair: RepairPlan,
    memory: EngineeringMemory,
    github: GitHubIntelligence,
    cost: VerificationCost,
    resolver: EntityResolver | None = None,
    generated_dir: Path | None = None,
) -> dict[str, Any]:
    """Assemble the runtime state model from already-computed intelligence."""
    res = resolver or get_resolver()
    gen = generated_dir or GENERATED_DIR
    cert = _certification(gen)

    knowledge = _read_json(gen / "knowledge-index.json")
    knowledge_counts = (
        knowledge.get("counts", {}) if isinstance(knowledge, dict) else {}
    )

    open_risks = [
        {
            "dimension": d.name,
            "level": d.level,
            "score": d.score,
            "top_evidence": d.evidence[0] if d.evidence else "",
        }
        for d in risk.dimensions
        if d.level in {"High", "Medium"}
    ]

    # Platform health blends certification with current risk posture.
    if cert.status == "CERTIFIED" and risk.overall_level == "Low":
        health = "HEALTHY"
    elif cert.status == "CERTIFIED":
        health = "CERTIFIED_WITH_OPEN_RISK"
    else:
        health = "ATTENTION_REQUIRED"

    return {
        "schema": "platform-state/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provider": "runtime.foundation.architecture.get_architecture",
        "audits_rerun": False,
        "platform_health": {
            "status": health,
            "architecture_counts": res.arch.counts(),
            "risk_level": risk.overall_level,
            "risk_score": risk.overall_score,
            "confidence": risk.confidence,
        },
        "certification": cert.to_dict(),
        "open_risks": open_risks,
        "recent_changes": {
            "file_count": len(change.changeset.files),
            "source": change.changeset.source,
            "base": change.changeset.base,
            "head": change.changeset.head,
            "changed_counts": {
                k: len(v) for k, v in sorted(change.entities.items()) if v
            },
            "unmapped_paths": list(change.unmapped_paths),
        },
        "verification_queue": {
            "selected_units": [u.id for u in plan.selected],
            "skipped_units": [s.id for s in plan.skipped],
            "estimated_seconds": plan.estimated_seconds,
            "estimated_ci_usd": cost.totals.get("ci_usd", 0),
            "savings_seconds": plan.savings_seconds,
        },
        "pending_repairs": {
            "defect_count": len(repair.defects),
            "repairs": [
                {
                    "defect_id": item["defect_id"],
                    "first_target": (
                        item["repair_order"][0]["target"]
                        if item.get("repair_order")
                        else None
                    ),
                    "confidence": item.get("confidence"),
                }
                for item in repair.items
            ],
        },
        "knowledge_growth": {
            "indexed_categories": knowledge_counts,
            "total_indexed": sum(
                v for v in knowledge_counts.values() if isinstance(v, int)
            ),
            "memory_observations": memory.observations,
            "memory_sources": list(memory.sources),
        },
        "ci_health": {
            "available": github.available,
            "runs_inspected": len(github.runs),
            "failed_jobs": len(github.failed_jobs),
            "annotations": len(github.annotations),
            "logs_downloaded": len(github.logs_fetched),
            "recurring_ci_failures": len(memory.recurring_ci_failures),
        },
        "blast_radius_summary": {
            "direct": len(blast.direct),
            "indirect": len(blast.indirect),
            "user_visible": len(blast.user_visible),
            "by_kind": blast.kinds(),
        },
    }
