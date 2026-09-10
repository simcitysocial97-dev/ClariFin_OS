"""M28.13 — Forensic execution record.

The single artifact the Diagnostic & Forensic Agent will consume.
Captures the entire change→plan→execute→reconcile→certify chain in
one immutable record.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime

from runtime.foundation.verification.evidence_planner import EvidenceAwarePlan
from runtime.foundation.verification.execution.evidence import _git_sha
from runtime.foundation.verification.execution.reconciliation import (
    ReconciledVerificationState,
)
from runtime.foundation.verification.execution.task import ExecutableVerificationPlan


@dataclass(frozen=True, slots=True)
class ForensicExecutionRecord:
    """The single artifact the Diagnostic & Forensic Agent will consume.

    Captures the entire change→plan→execute→reconcile→certify chain in
    one immutable record.
    """

    record_id: str
    generated_at: str
    repository_sha: str
    change: dict
    affected_graph_nodes: dict
    invalidations: dict
    reused_evidence: dict
    selected_tasks: dict
    executed_tasks: dict
    execution_results: dict
    new_evidence: dict
    derived_evidence: dict
    failures: dict
    uncertainties: dict
    certification_decision: dict

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "generated_at": self.generated_at,
            "repository_sha": self.repository_sha,
            "change": self.change,
            "affected_graph_nodes": self.affected_graph_nodes,
            "invalidations": self.invalidations,
            "reused_evidence": self.reused_evidence,
            "selected_tasks": self.selected_tasks,
            "executed_tasks": self.executed_tasks,
            "execution_results": self.execution_results,
            "new_evidence": self.new_evidence,
            "derived_evidence": self.derived_evidence,
            "failures": self.failures,
            "uncertainties": self.uncertainties,
            "certification_decision": self.certification_decision,
        }


def build_forensic_record(
    plan: EvidenceAwarePlan,
    executable: ExecutableVerificationPlan,
    fresh: dict[str, "ExecutionEvidence"],
    reconciled: ReconciledVerificationState,
) -> ForensicExecutionRecord:
    """Build a forensic execution record from the full pipeline state."""
    from runtime.foundation.verification.execution.evidence import ExecutionEvidence  # noqa: PLC0415

    rid = hashlib.sha256(
        "|".join([plan.plan_id, executable.plan_id, _git_sha()]).encode()
    ).hexdigest()[:12]

    invalidations = {
        "by_component": {
            comp: [inv for inv in reuses if inv]
            for comp, reuses in ((r.scope_id, r.invalidations) for r in plan.reuses)
        }
    }
    reused_evidence = {
        "count": sum(1 for c in reconciled.components if c.source == "reused"),
        "components": [
            c.component for c in reconciled.components if c.source == "reused"
        ],
    }
    selected = {
        "count": len(plan.selected_tasks),
        "components": [t.target for t in plan.selected_tasks],
    }
    executed = {
        "count": len(fresh),
        "components": sorted(fresh.keys()),
    }
    results = {
        "by_component": {c: ev.to_dict() for c, ev in fresh.items()},
    }
    new_evidence = {
        "count": sum(1 for c in reconciled.components if c.source == "fresh_measured"),
        "components": [
            c.component for c in reconciled.components if c.source == "fresh_measured"
        ],
    }
    derived = {
        "aggregate": reconciled.aggregate.to_dict() if reconciled.aggregate else None,
    }
    failures = {
        "by_component": {
            c.component: {
                "kind": (
                    c.evidence.failure_kind.value
                    if c.evidence and c.evidence.failure_kind
                    else None
                ),
                "message": c.evidence.failure_message if c.evidence else None,
            }
            for c in reconciled.components
            if c.evidence is not None and c.evidence.failure_kind is not None
        },
        "count": sum(
            1
            for c in reconciled.components
            if c.evidence is not None and c.evidence.failure_kind is not None
        ),
    }
    uncertainties = {
        "no_evidence": [
            c.component for c in reconciled.components if c.source == "no_evidence"
        ],
        "invalidated": [
            c.component for c in reconciled.components if c.source == "invalidated"
        ],
        "drift_blockers": list(plan.drift_blockers),
        "certification_gaps": list(plan.certification_gaps),
    }
    decision = {
        "certifiable": reconciled.certifiable,
        "rationale": reconciled.rationale,
        "aggregate_label": reconciled.aggregate.label if reconciled.aggregate else None,
        "aggregate_result": (
            reconciled.aggregate.result if reconciled.aggregate else None
        ),
    }

    return ForensicExecutionRecord(
        record_id=f"forensic::{rid}",
        generated_at=datetime.now(UTC).isoformat(),
        repository_sha=_git_sha(),
        change={
            "changed_files": list(plan.changed_files),
            "affected_components": list(plan.affected_components),
            "affected_capabilities": list(plan.affected_capabilities),
        },
        affected_graph_nodes={
            "sources": list(plan.affected_sources),
            "capabilities": list(plan.affected_capabilities),
        },
        invalidations=invalidations,
        reused_evidence=reused_evidence,
        selected_tasks=selected,
        executed_tasks=executed,
        execution_results=results,
        new_evidence=new_evidence,
        derived_evidence=derived,
        failures=failures,
        uncertainties=uncertainties,
        certification_decision=decision,
    )
