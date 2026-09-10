"""
M9-C54 — Workflow greenness audit (Q3).

Analyzes workflow execution semantics to classify each job's greenness
status independent of CI pass/fail outcome.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory


class GreennessStatus(str, Enum):
    EXECUTES = "executes"
    CONDITIONAL = "conditional"
    CONTINUE_ON_ERROR = "continue_on_error"
    MASKED = "masked"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class GreennessAudit:
    workflow: str
    job: str
    status: GreennessStatus
    verification_completeness: str  # "complete" | "partial" | "none" | "misleading"
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "job": self.job,
            "status": self.status.value,
            "verification_completeness": self.verification_completeness,
            "notes": self.notes,
        }


def audit_workflow_greenness(
    inventories: list[WorkflowInventory],
) -> list[GreennessAudit]:
    """Audit each workflow's greenness semantics."""
    audits: list[GreennessAudit] = []
    for inv in inventories:
        for job in inv.jobs:
            has_verif = bool(job.verification_steps)
            has_continue = job.has_continue_on_error
            has_always_summary = any(
                s.if_condition and "always()" in s.if_condition for s in job.steps
            )

            if has_continue:
                status = GreennessStatus.CONTINUE_ON_ERROR
            elif has_always_summary and not has_verif:
                status = GreennessStatus.MASKED
            else:
                status = GreennessStatus.EXECUTES

            if has_verif:
                completeness = "complete"
            elif has_always_summary:
                completeness = "none"
            else:
                completeness = "none"

            notes_parts: list[str] = []
            if has_continue:
                notes_parts.append("continue-on-error masks verification failures")
            if has_always_summary and has_verif:
                notes_parts.append(
                    "WARNING: if: always() on summary step can mask verification failure"
                )
            if has_always_summary and not has_verif:
                notes_parts.append(
                    "if: always() on summary step (no verification in this job)"
                )
            if not has_verif:
                notes_parts.append("no verification steps in job")

            audits.append(
                GreennessAudit(
                    workflow=inv.filename,
                    job=job.job_id,
                    status=status,
                    verification_completeness=completeness,
                    notes=(
                        "; ".join(notes_parts) if notes_parts else "standard execution"
                    ),
                )
            )
    return audits
