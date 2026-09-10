"""
M9-C54 — Workflow coverage matrix (Q9).

Constructs the repository-wide workflow coverage matrix, mapping every
workflow step to its verification capability, stage, and certification
relevance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.ci_evidence import CommandSemantics
from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory
from runtime.foundation.verification.workflow_convergence.mapping import (
    _infer_capability,
)


@dataclass(frozen=True, slots=True)
class CoverageRow:
    workflow: str
    job: str
    verification_capability: str | None
    verification_stage: str | None
    command: str
    test_surface: str | None
    measurement: str | None
    evidence: str | None
    certification_relevance: str
    bypass_risk: str | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "job": self.job,
            "verification_capability": self.verification_capability,
            "verification_stage": self.verification_stage,
            "command": self.command,
            "test_surface": self.test_surface,
            "measurement": self.measurement,
            "evidence": self.evidence,
            "certification_relevance": self.certification_relevance,
            "bypass_risk": self.bypass_risk,
            "status": self.status,
        }


def build_coverage_matrix(
    inventories: list[WorkflowInventory],
) -> list[CoverageRow]:
    """Construct the repository-wide workflow coverage matrix."""
    rows: list[CoverageRow] = []
    for inv in inventories:
        for job in inv.jobs:
            for step in job.steps:
                raw_cmd = step.run or step.uses
                if not raw_cmd:
                    continue
                sem = step.semantics
                if sem is not None:
                    cap = _infer_capability(sem, raw_cmd)
                    stage = sem.verification_task
                    evidence = sem.evidence_kind
                    relevance = (
                        "authoritative"
                        if sem.execution_mode == "authoritative"
                        else "supporting"
                    )
                    status = "active"
                else:
                    cap = None
                    stage = None
                    evidence = None
                    relevance = "operational"
                    status = "non_verification"

                rows.append(
                    CoverageRow(
                        workflow=inv.filename,
                        job=job.job_id,
                        verification_capability=cap,
                        verification_stage=stage,
                        command=raw_cmd[:120],
                        test_surface=sem.scope if sem else None,
                        measurement=sem.evidence_kind if sem else None,
                        evidence=evidence,
                        certification_relevance=relevance,
                        bypass_risk=None,
                        status=status,
                    )
                )
    return rows
