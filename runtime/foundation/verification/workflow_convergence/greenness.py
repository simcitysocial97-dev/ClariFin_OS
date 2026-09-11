"""
M9-C54 — Workflow greenness audit (Q3).

Analyzes workflow execution semantics to classify each job's greenness
status independent of CI pass/fail outcome.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import (
    WorkflowInventory,
)

# Step-name substrings that identify a legitimate `if: always()` usage.
# These are cleanup, reporting, or artifact-handling steps that are
# intentionally decoupled from verification pass/fail — they MUST run
# regardless and do NOT mask any verification semantics.
LEGITIMATE_ALWAYS_PATTERNS: tuple[str, ...] = (
    "summary",
    "upload",
    "cleanup",
    "save cache",
    "restore",
    "artifact",
    "diagnostic",
    "capture",
    "post ",
)


def _is_legitimate_always(step_name: str) -> bool:
    """Return True when *step_name* is a known-good cleanup/reporting step."""
    lower = step_name.lower()
    return any(pat in lower for pat in LEGITIMATE_ALWAYS_PATTERNS)


def _has_problematic_always(job) -> bool:
    """Return True only when a non-legitimate step uses `if: always()`."""
    for s in job.steps:
        if (
            s.if_condition
            and "always()" in s.if_condition
            and not _is_legitimate_always(s.name)
        ):
            return True
    return False


def _has_any_always(job) -> bool:
    """Return True when ANY step uses `if: always()` (legacy compat)."""
    return any(s.if_condition and "always()" in s.if_condition for s in job.steps)


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
            # Only treat `if: always()` as problematic when it is on a
            # non-legitimate step (i.e. not a known cleanup / summary /
            # upload / diagnostic pattern).
            has_problematic_always = _has_problematic_always(job)
            has_any_always = _has_any_always(job)

            if has_continue:
                status = GreennessStatus.CONTINUE_ON_ERROR
            elif has_problematic_always and not has_verif:
                status = GreennessStatus.MASKED
            else:
                status = GreennessStatus.EXECUTES

            if has_verif:
                completeness = "complete"
            elif has_problematic_always:
                completeness = "none"
            else:
                completeness = "none"

            notes_parts: list[str] = []
            if has_continue:
                notes_parts.append("continue-on-error masks verification failures")
            if has_problematic_always and has_verif:
                notes_parts.append(
                    "WARNING: if: always() on non-summary step can mask verification failure"
                )
            if has_problematic_always and not has_verif:
                notes_parts.append(
                    "if: always() on non-summary step (no verification in this job)"
                )
            # Record (but do not flag) legitimate always() steps so the
            # audit trail shows they were observed and explicitly exempted.
            if has_any_always and not has_problematic_always:
                legit_names = [
                    s.name
                    for s in job.steps
                    if s.if_condition
                    and "always()" in s.if_condition
                    and _is_legitimate_always(s.name)
                ]
                if legit_names:
                    notes_parts.append(
                        f"legitimate if: always() steps: {', '.join(legit_names)}"
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
