"""
M9-C42.27 — M27.9 Evidence Correlation Layer

Canonical answer to:

    * What changed?
    * What was affected?
    * What was tested?
    * What was not tested?
    * What evidence was reused?
    * What evidence was freshly generated?
    * What evidence was derived?
    * What remains uncertain?
    * Why is the result certifiable (or not)?

This is the single artifact the eventual Diagnostic & Forensic Agent
will consume.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from runtime.foundation.verification.evidence_planner import (  # noqa: E402
    EvidenceAwarePlan,
    PlannedTask,
)
from runtime.foundation.verification.evidence_reuse import (  # noqa: E402
    DerivedAggregate,
    EvidenceReuse,
)


@dataclass(frozen=True, slots=True)
class Correlation:
    """The full correlation between change, plan, evidence, and decision."""

    correlation_id: str
    generated_at: str
    plan_id: str

    # What changed
    changed_files: tuple[str, ...]
    changed_kinds: tuple[str, ...]

    # What was affected
    affected_sources: tuple[str, ...]
    affected_capabilities: tuple[str, ...]
    affected_components: tuple[str, ...]

    # What was tested
    tested_components: tuple[str, ...]
    untested_components: tuple[str, ...]

    # What evidence was reused
    reused_evidence: tuple[EvidenceReuse, ...]
    fresh_evidence_targets: tuple[str, ...]

    # What evidence was derived
    derived_aggregates: tuple[DerivedAggregate, ...]

    # What remains uncertain
    uncertain_components: tuple[str, ...]
    drift_blockers: tuple[str, ...]
    certification_gaps: tuple[str, ...]

    # Certifiability verdict
    certifiable: bool
    rationale: str

    def to_dict(self) -> dict:
        return {
            "correlation_id": self.correlation_id,
            "generated_at": self.generated_at,
            "plan_id": self.plan_id,
            "changed_files": list(self.changed_files),
            "changed_kinds": list(self.changed_kinds),
            "affected_sources": list(self.affected_sources),
            "affected_capabilities": list(self.affected_capabilities),
            "affected_components": list(self.affected_components),
            "tested_components": list(self.tested_components),
            "untested_components": list(self.untested_components),
            "reused_evidence": [r.to_dict() for r in self.reused_evidence],
            "fresh_evidence_targets": list(self.fresh_evidence_targets),
            "derived_aggregates": [a.to_dict() for a in self.derived_aggregates],
            "uncertain_components": list(self.uncertain_components),
            "drift_blockers": list(self.drift_blockers),
            "certification_gaps": list(self.certification_gaps),
            "certifiable": self.certifiable,
            "rationale": self.rationale,
        }


def correlate(plan: EvidenceAwarePlan) -> Correlation:
    """Produce a correlation from an evidence-aware plan."""
    # Changed kinds
    kinds: list[str] = []
    for f in plan.changed_files:
        if f.startswith("backend/src/"):
            kinds.append("source")
        elif f.startswith("backend/tests/"):
            kinds.append("test")
        elif f.endswith((".toml", ".cfg", ".coveragerc", "ruff.toml")):
            kinds.append("config")
        else:
            kinds.append("other")

    # Tested / untested components
    tested = tuple(
        t.target
        for t in plan.selected_tasks
        if t.disposition
        in ("selected_fresh", "selected_revalidation", "selected_aggregate")
    )
    untested = tuple(
        t.target
        for t in plan.excluded_tasks
        if t.disposition == "excluded_reusable_evidence"
    )

    # Reused evidence
    reused = tuple(
        r
        for r in plan.reuses
        if r.disposition
        in ("reusable", "reusable_aggregate", "reusable_with_revalidation")
    )

    # Fresh evidence targets
    fresh = tuple(
        t.target
        for t in plan.selected_tasks
        if t.disposition in ("selected_fresh", "selected_revalidation")
    )

    # Uncertain components
    uncertain: list[str] = []
    for r in plan.reuses:
        if r.disposition in (
            "no_evidence",
            "invalidated_component",
            "invalidated_capability",
            "invalidated_task",
            "invalidated_evidence_only",
        ):
            uncertain.append(r.scope_id)

    # Certifiability: blocked if drift or invalidations remain unaddressed
    certifiable = (
        len(plan.drift_blockers) == 0
        and len(plan.certification_gaps) == 0
        and all(r.disposition != "no_evidence" for r in plan.reuses)
    )

    rationale_parts: list[str] = []
    if plan.drift_blockers:
        rationale_parts.append(
            f"blocked by {len(plan.drift_blockers)} drift blocker(s)"
        )
    if plan.certification_gaps:
        rationale_parts.append(f"{len(plan.certification_gaps)} certification gap(s)")
    if not rationale_parts:
        rationale_parts.append("all components have valid reusable evidence")

    rationale = (
        "certifiable: " + "; ".join(rationale_parts)
        if certifiable
        else "NOT certifiable: " + "; ".join(rationale_parts)
    )

    return Correlation(
        correlation_id=f"corr::{plan.plan_id}",
        generated_at=datetime.now(UTC).isoformat(),
        plan_id=plan.plan_id,
        changed_files=plan.changed_files,
        changed_kinds=tuple(kinds),
        affected_sources=plan.affected_sources,
        affected_capabilities=plan.affected_capabilities,
        affected_components=plan.affected_components,
        tested_components=tested,
        untested_components=untested,
        reused_evidence=reused,
        fresh_evidence_targets=fresh,
        derived_aggregates=plan.derived_aggregates,
        uncertain_components=tuple(uncertain),
        drift_blockers=plan.drift_blockers,
        certification_gaps=plan.certification_gaps,
        certifiable=certifiable,
        rationale=rationale,
    )


def main() -> int:
    from runtime.foundation.verification.evidence_planner import default_planner

    planner = default_planner()
    out_dir = REPO_ROOT / "runtime" / "generated" / "m9-c42.27"
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios: list[tuple[str, tuple[str, ...]]] = [
        ("A_no_change", ()),
        ("B_source_change", ("backend/src/engines/credit_card_engine/foo.py",)),
        ("C_test_change", ("backend/tests/unit/engines/credit_card_engine/test_x.py",)),
        ("D_config_change", ("pyproject.toml",)),
    ]
    for name, files in scenarios:
        plan = planner.plan(files)
        corr = correlate(plan)
        path = out_dir / f"correlation-{name}.json"
        path.write_text(json.dumps(corr.to_dict(), indent=2))
        print(
            f"{name}: certifiable={corr.certifiable} "
            f"selected={len(plan.selected_tasks)} "
            f"excluded={len(plan.excluded_tasks)} "
            f"drift={len(plan.drift_blockers)}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
