"""
M9-C54 — CI evidence contract (Q4).

Operationalizes CIEvidenceRecord across workflows, building a contract that
maps every verification step to its required evidence type, path, and
fingerprint requirements.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.ci_evidence import CommandSemantics
from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory


@dataclass(frozen=True, slots=True)
class EvidenceContractEntry:
    workflow: str
    job: str
    step: str
    verification_task: str
    evidence_kind: str
    execution_mode: str
    produces_evidence: bool
    evidence_path: str | None
    fingerprintable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow": self.workflow,
            "job": self.job,
            "step": self.step,
            "verification_task": self.verification_task,
            "evidence_kind": self.evidence_kind,
            "execution_mode": self.execution_mode,
            "produces_evidence": self.produces_evidence,
            "evidence_path": self.evidence_path,
            "fingerprintable": self.fingerprintable,
        }


def build_evidence_contract(
    inventories: list[WorkflowInventory],
) -> list[dict[str, Any]]:
    """Build the CI evidence contract for all verification steps."""
    entries: list[dict[str, Any]] = []
    for inv in inventories:
        for job in inv.jobs:
            for step in job.verification_steps:
                sem = step.semantics
                if sem is None:
                    continue
                evidence_path = _infer_evidence_path(sem)
                entries.append(
                    {
                        "workflow": inv.filename,
                        "job": job.job_id,
                        "step": step.name,
                        "verification_task": sem.verification_task,
                        "evidence_kind": sem.evidence_kind,
                        "execution_mode": sem.execution_mode,
                        "produces_evidence": sem.reusable_evidence,
                        "evidence_path": evidence_path,
                        "fingerprintable": True,
                    }
                )
    return entries


def _infer_evidence_path(sem: CommandSemantics) -> str | None:
    """Infer the expected evidence artifact path from semantics."""
    path_map = {
        "mutation-summary": "backend/tests/generated/mutation/mutation-summary.json",
        "mutation-smoke-summary": "backend/tests/generated/mutation/mutation-smoke-summary.json",
        "test-report": "runtime/generated/verification-report.md",
        "golden": "backend/tests/generated/golden/",
        "security-scan": "results.sarif",
        "environment-fingerprint": None,
        "status-summary": None,
    }
    return path_map.get(sem.evidence_kind)
