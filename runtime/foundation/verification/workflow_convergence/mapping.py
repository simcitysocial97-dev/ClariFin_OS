"""
M9-C54 — Workflow -> capability mapping (Q2).

Maps every workflow step to its capability using the certified command-matcher
table from ci_evidence.py, producing a structured mapping that can be used
for coverage analysis and audit trails.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.ci_evidence import CommandSemantics
from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory


@dataclass(frozen=True, slots=True)
class CapabilityMapping:
    workflow: str
    job: str
    step_index: int
    command: str
    capability: str | None
    verification_task: str | None
    evidence_kind: str | None
    execution_mode: str | None
    mapping_status: str  # "mapped" | "unmapped_verification" | "non_verification" | "legacy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "job": self.job,
            "step_index": self.step_index,
            "command": self.command,
            "capability": self.capability,
            "verification_task": self.verification_task,
            "evidence_kind": self.evidence_kind,
            "execution_mode": self.execution_mode,
            "mapping_status": self.mapping_status,
        }


def map_workflows_to_capabilities(
    inventories: list[WorkflowInventory],
) -> list[CapabilityMapping]:
    """Map every workflow step to its capability using the command matchers."""
    mappings: list[CapabilityMapping] = []
    for inv in inventories:
        for job in inv.jobs:
            for step in job.steps:
                raw_cmd = step.run or step.uses
                if not raw_cmd:
                    continue
                sem = step.semantics
                if sem is not None:
                    cap = _infer_capability(sem, raw_cmd)
                    mappings.append(
                        CapabilityMapping(
                            workflow=inv.filename,
                            job=job.job_id,
                            step_index=step.index,
                            command=raw_cmd,
                            capability=cap,
                            verification_task=sem.verification_task,
                            evidence_kind=sem.evidence_kind,
                            execution_mode=sem.execution_mode,
                            mapping_status="mapped",
                        )
                    )
                elif step.is_verification:
                    mappings.append(
                        CapabilityMapping(
                            workflow=inv.filename,
                            job=job.job_id,
                            step_index=step.index,
                            command=raw_cmd,
                            capability=None,
                            verification_task=None,
                            evidence_kind=None,
                            execution_mode=None,
                            mapping_status="unmapped_verification",
                        )
                    )
                else:
                    mappings.append(
                        CapabilityMapping(
                            workflow=inv.filename,
                            job=job.job_id,
                            step_index=step.index,
                            command=raw_cmd,
                            capability=None,
                            verification_task=None,
                            evidence_kind=None,
                            execution_mode=None,
                            mapping_status="non_verification",
                        )
                    )
    return mappings


def _infer_capability(sem: CommandSemantics, raw_cmd: str) -> str | None:
    """Infer the capability from the semantics and command text."""
    task_to_capability = {
        "task::mutation::full": "measure.mutation",
        "task::mutation::smoke": "measure.mutation",
        "task::mutation::targeted": "measure.mutation",
        "task::unit::backend-suite": "verify.backend",
        "task::static::frontend-suite": "verify.frontend",
        "task::e2e::playwright": "verify.e2e",
        "task::golden::regression": "verify.golden",
        "task::static::codeql": "verify.security",
        "task::static::codeql-init": "verify.security",
        "task::static::codeql-build": "verify.security",
        "task::static::env-check": "env.check",
        "task::static::status-summary": "status.summary",
        "task::contract::api": "verify.contracts",
    }
    return task_to_capability.get(sem.verification_task)
