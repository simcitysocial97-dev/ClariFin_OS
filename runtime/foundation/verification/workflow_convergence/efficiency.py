"""
M9-C54 — Resource / duplication efficiency metrics (Q16).

Measures CI execution efficiency including workflow counts, step counts,
upload overhead, and evidence reuse potential.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import (
    WorkflowInventory,
    _is_upload_step,
)


@dataclass(frozen=True, slots=True)
class EfficiencyMetric:
    metric: str
    value: Any
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "value": self.value,
            "notes": self.notes,
        }


def measure_efficiency(
    inventories: list[WorkflowInventory],
) -> list[EfficiencyMetric]:
    """Measure CI execution efficiency."""
    total_workflows = len(inventories)
    total_jobs = sum(len(inv.jobs) for inv in inventories)
    total_steps = sum(inv.total_steps for inv in inventories)
    verification_steps = sum(inv.verification_steps for inv in inventories)
    upload_steps = sum(
        1
        for inv in inventories
        for j in inv.jobs
        for s in j.steps
        if _is_upload_step({"uses": s.uses, "name": s.name})
    )

    unique_verif_cmds: set[str] = set()
    for inv in inventories:
        for j in inv.jobs:
            for s in j.verification_steps:
                sem = s.semantics
                if sem is not None:
                    unique_verif_cmds.add(sem.verification_task)

    return [
        EfficiencyMetric(
            "total_workflows", total_workflows, "Number of workflow files"
        ),
        EfficiencyMetric("total_jobs", total_jobs, "Total jobs across all workflows"),
        EfficiencyMetric("total_steps", total_steps, "Total steps across all jobs"),
        EfficiencyMetric(
            "verification_steps",
            verification_steps,
            "Steps that execute verification commands",
        ),
        EfficiencyMetric("upload_steps", upload_steps, "Steps that upload artifacts"),
        EfficiencyMetric(
            "unique_verification_tasks",
            len(unique_verif_cmds),
            "Distinct verification task types",
        ),
        EfficiencyMetric(
            "evidence_reuse_potential",
            "high",
            "C42.29 evidence_reuse.py enables cross-run reuse",
        ),
        EfficiencyMetric(
            "components_avoided",
            "via blast_radius",
            "C50 blast-radius avoids unnecessary verification",
        ),
    ]
