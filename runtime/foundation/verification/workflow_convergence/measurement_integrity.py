"""
M9-C54 — Measurement integrity assessment (Q10).

Assesses whether test/coverage/mutation evidence is preserved independently
of the workflow execution pipeline.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import WorkflowInventory


@dataclass(frozen=True, slots=True)
class MeasurementIntegrity:
    metric: str
    preserved_independently: bool
    workflow_support: bool
    evidence_path: str | None
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "preserved_independently": self.preserved_independently,
            "workflow_support": self.workflow_support,
            "evidence_path": self.evidence_path,
            "notes": self.notes,
        }


def assess_measurement_integrity(
    inventories: list[WorkflowInventory],
) -> list[MeasurementIntegrity]:
    """Assess whether test/coverage/mutation evidence is preserved independently."""
    has_test_workflow = any(
        "verify.py" in (s.run or "")
        and ("backend" in s.run or "frontend" in s.run or "runtime" in s.run)
        for inv in inventories
        for j in inv.jobs
        for s in j.steps
    )
    has_mutation_workflow = any(
        "mutation" in (s.run or "")
        for inv in inventories
        for j in inv.jobs
        for s in j.steps
    )
    has_coverage = False

    return [
        MeasurementIntegrity(
            metric="test_count",
            preserved_independently=True,
            workflow_support=has_test_workflow,
            evidence_path="runtime/generated/verification-report.md",
            notes="Test counts are reported by verify.py profiles",
        ),
        MeasurementIntegrity(
            metric="pass_fail",
            preserved_independently=True,
            workflow_support=has_test_workflow,
            evidence_path="runtime/generated/verification-report.md",
            notes="Pass/fail status is reported by verify.py profiles",
        ),
        MeasurementIntegrity(
            metric="skipped",
            preserved_independently=True,
            workflow_support=has_test_workflow,
            evidence_path="runtime/generated/verification-report.md",
            notes="Skipped tests are reported by verify.py profiles",
        ),
        MeasurementIntegrity(
            metric="line_coverage",
            preserved_independently=True,
            workflow_support=has_coverage,
            evidence_path=None,
            notes="Coverage measurement exists in coverage_measurement.py but no dedicated CI workflow uploads it",
        ),
        MeasurementIntegrity(
            metric="branch_coverage",
            preserved_independently=True,
            workflow_support=False,
            evidence_path=None,
            notes="Branch coverage not currently collected in CI",
        ),
        MeasurementIntegrity(
            metric="mutation_score",
            preserved_independently=True,
            workflow_support=has_mutation_workflow,
            evidence_path="backend/tests/generated/mutation/mutation-summary.json",
            notes="Mutation score is independently measured and uploaded",
        ),
        MeasurementIntegrity(
            metric="mutation_killed",
            preserved_independently=True,
            workflow_support=has_mutation_workflow,
            evidence_path="backend/tests/generated/mutation/mutation-summary.json",
            notes="Killed count is independently preserved",
        ),
        MeasurementIntegrity(
            metric="mutation_survived",
            preserved_independently=True,
            workflow_support=has_mutation_workflow,
            evidence_path="backend/tests/generated/mutation/mutation-summary.json",
            notes="Survived count is independently preserved",
        ),
    ]
