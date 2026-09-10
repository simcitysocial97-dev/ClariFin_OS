"""
M9-C54 — Workflow bypass analysis (Q7).

Analyzes every workflow for paths that bypass the verification control plane.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory


class BypassRisk(str, Enum):
    SAFE = "SAFE"
    CONTROLLED = "CONTROLLED"
    INTENTIONAL_LOW_LEVEL = "INTENTIONAL_LOW_LEVEL_ESCAPE"
    BYPASS_RISK = "BYPASS_RISK"
    BLOCKING = "BLOCKING_BYPASS"


@dataclass(frozen=True, slots=True)
class BypassAnalysis:
    workflow: str
    job: str
    step: str
    risk: BypassRisk
    bypassed_stage: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "job": self.job,
            "step": self.step,
            "risk": self.risk.value,
            "bypassed_stage": self.bypassed_stage,
            "rationale": self.rationale,
        }


def analyze_workflow_bypass(
    inventories: list[WorkflowInventory],
) -> list[BypassAnalysis]:
    """Analyze every workflow for paths that bypass the control plane."""
    results: list[BypassAnalysis] = []
    for inv in inventories:
        for job in inv.jobs:
            for step in job.steps:
                raw_cmd = step.run or step.uses
                if not raw_cmd:
                    continue
                sem = step.semantics
                if sem is not None:
                    continue
                if "verify.py" in raw_cmd and sem is None:
                    results.append(
                        BypassAnalysis(
                            workflow=inv.filename,
                            job=job.job_id,
                            step=step.name,
                            risk=BypassRisk.BYPASS_RISK,
                            bypassed_stage="control_plane",
                            rationale=f"verify.py invocation not in command matcher table: {raw_cmd[:80]}",
                        )
                    )
                elif step.continue_on_error and sem is not None:
                    results.append(
                        BypassAnalysis(
                            workflow=inv.filename,
                            job=job.job_id,
                            step=step.name,
                            risk=BypassRisk.CONTROLLED,
                            bypassed_stage="certification",
                            rationale="continue-on-error on verification step: failure is logged but does not fail the job",
                        )
                    )
                elif "bash" in raw_cmd and ".sh" in raw_cmd and sem is None:
                    results.append(
                        BypassAnalysis(
                            workflow=inv.filename,
                            job=job.job_id,
                            step=step.name,
                            risk=BypassRisk.CONTROLLED,
                            bypassed_stage="change_detection",
                            rationale="shell script invocation outside verify.py control plane",
                        )
                    )
    return results
