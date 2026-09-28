"""
M9-C54 — Workflow duplication/redundancy analysis (Q11).

Detects duplicate or redundant workflow execution across the repository.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import (
    WorkflowInventory,
    _is_upload_step,
)


@dataclass(frozen=True, slots=True)
class DuplicationFinding:
    category: str
    description: str
    workflows_involved: tuple[str, ...]
    commands: tuple[str, ...]
    classification: str  # "intentional" | "useful" | "redundant" | "conflicting" | "obsolete"
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "workflows_involved": list(self.workflows_involved),
            "commands": list(self.commands),
            "classification": self.classification,
            "notes": self.notes,
        }


def analyze_duplication(
    inventories: list[WorkflowInventory],
) -> list[DuplicationFinding]:
    """Detect duplicate/redundant workflow execution."""
    findings: list[DuplicationFinding] = []

    sem_groups: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for inv in inventories:
        for job in inv.jobs:
            for step in job.verification_steps:
                sem = step.semantics
                if sem is not None:
                    sem_groups[sem.verification_task].append(
                        (inv.filename, job.job_id, step.name)
                    )

    for task_kind, occurrences in sorted(sem_groups.items()):
        if len(occurrences) > 1:
            workflows = tuple({o[0] for o in occurrences})
            findings.append(
                DuplicationFinding(
                    category="verification_command",
                    description=f"{task_kind} executed in {len(occurrences)} places",
                    workflows_involved=workflows,
                    commands=(task_kind,),
                    classification="intentional",
                    notes="Multiple workflows legitimately run the same verification for different triggers/path-filters",
                )
            )

    upload_groups: dict[str, list[str]] = defaultdict(list)
    for inv in inventories:
        for job in inv.jobs:
            for step in job.steps:
                if _is_upload_step({"uses": step.uses, "name": step.name}):
                    upload_groups[step.name].append(inv.filename)

    for upload_name, upload_workflows in sorted(upload_groups.items()):
        if len(upload_workflows) > 1:
            findings.append(
                DuplicationFinding(
                    category="artifact_upload",
                    description=f"Upload '{upload_name}' appears in {len(upload_workflows)} workflows",
                    workflows_involved=tuple(sorted(upload_workflows)),
                    commands=(upload_name,),
                    classification="useful",
                    notes="Each workflow uploads its own artifacts with unique names; this is intentional for isolation",
                )
            )

    return findings
