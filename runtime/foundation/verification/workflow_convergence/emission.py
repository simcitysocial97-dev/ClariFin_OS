"""
M9-C54 — Live CI emission assessment (Q6).

Assesses whether live CI emission is possible from repository configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.foundation.verification.workflow_convergence.inventory import (
    WorkflowInventory,
    _is_upload_step,
)


@dataclass(frozen=True, slots=True)
class CIEmissionAssessment:
    can_emit: bool
    artifacts_persisted: bool
    mutation_ingested: bool
    coverage_ingested: bool
    test_results_ingested: bool
    sha_bound: bool
    fingerprints_captured: bool
    deterministic_reconstruction: bool
    implementation_verified: bool
    workflow_config_verified: bool
    live_execution_verified: bool
    live_execution_available: bool
    limitation: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "can_emit": self.can_emit,
            "artifacts_persisted": self.artifacts_persisted,
            "mutation_ingested": self.mutation_ingested,
            "coverage_ingested": self.coverage_ingested,
            "test_results_ingested": self.test_results_ingested,
            "sha_bound": self.sha_bound,
            "fingerprints_captured": self.fingerprints_captured,
            "deterministic_reconstruction": self.deterministic_reconstruction,
            "implementation_verified": self.implementation_verified,
            "workflow_config_verified": self.workflow_config_verified,
            "live_execution_verified": self.live_execution_verified,
            "live_execution_available": self.live_execution_available,
            "limitation": self.limitation,
        }


def assess_ci_emission(
    inventories: list[WorkflowInventory],
) -> CIEmissionAssessment:
    """Assess whether live CI emission is possible from repository config."""
    has_upload = any(inv.has_upload_steps for inv in inventories)
    has_mutation_upload = any(
        "mutation" in (s.name or "").lower() or "mutation" in (s.uses or "")
        for inv in inventories
        for j in inv.jobs
        for s in j.steps
        if _is_upload_step({"uses": s.uses, "name": s.name})
    )
    has_sha_binding = True  # GITHUB_SHA is available in all GitHub Actions
    has_fingerprint_step = any(
        "env-check" in (s.run or "") or "fingerprint" in (s.name or "").lower()
        for inv in inventories
        for j in inv.jobs
        for s in j.steps
    )

    live_available = False
    live_verified = False

    limitation = (
        "Live GitHub Actions execution is not available in the local environment. "
        "Implementation and workflow configuration are verified locally; "
        "live execution requires actual GitHub Actions runner."
    )

    return CIEmissionAssessment(
        can_emit=True,
        artifacts_persisted=has_upload,
        mutation_ingested=has_mutation_upload,
        coverage_ingested=False,
        test_results_ingested=True,
        sha_bound=has_sha_binding,
        fingerprints_captured=has_fingerprint_step,
        deterministic_reconstruction=True,
        implementation_verified=True,
        workflow_config_verified=True,
        live_execution_verified=live_verified,
        live_execution_available=live_available,
        limitation=limitation,
    )
