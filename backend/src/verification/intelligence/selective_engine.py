"""Selective GitHub Execution Engine.

Determines which CI jobs must execute vs. can be skipped
based on the Verification Intelligence Layer analysis.

Heavy verification remains on GitHub Actions.
Local execution stays lightweight.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
GENERATED_DIR = BACKEND_DIR / "tests" / "generated"

@dataclass
class CIJob:
    """A single CI job with its execution status."""

    job_id: str
    name: str
    must_run: bool = True
    reason: str = ""
    targets: list[str] = field(default_factory=list)
    estimated_runtime_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "name": self.name,
            "must_run": self.must_run,
            "reason": self.reason,
            "targets": self.targets,
            "estimated_runtime_seconds": self.estimated_runtime_seconds,
        }

@dataclass
class SelectivePlan:
    """Complete selective execution plan for CI."""

    changed_files: list[str] = field(default_factory=list)
    strategy: str = "full"
    overall_risk: str = "LOW"
    affected_capabilities: list[str] = field(default_factory=list)
    affected_engines: list[str] = field(default_factory=list)
    jobs: list[CIJob] = field(default_factory=list)
    skipped_jobs: list[CIJob] = field(default_factory=list)
    must_run_jobs: list[CIJob] = field(default_factory=list)
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": self.changed_files,
            "strategy": self.strategy,
            "overall_risk": self.overall_risk,
            "affected_capabilities": self.affected_capabilities,
            "affected_engines": self.affected_engines,
            "jobs": [j.to_dict() for j in self.jobs],
            "skipped_jobs": [j.to_dict() for j in self.skipped_jobs],
            "must_run_jobs": [j.to_dict() for j in self.must_run_jobs],
            "generated_at": self.generated_at,
        }

class SelectiveEngine:
    """Intelligence-driven CI job selection engine."""

    JOB_DEFINITIONS: dict[str, dict[str, Any]] = {
        "lint": {
            "name": "Lint & Format",
            "must_run_for": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "estimated_runtime": 60.0,
            "targets": ["ruff", "black", "mypy"],
        },
        "unit": {
            "name": "Unit Tests",
            "must_run_for": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "estimated_runtime": 120.0,
            "targets": ["tests/unit/"],
        },
        "property": {
            "name": "Property Tests",
            "must_run_for": ["HIGH", "CRITICAL"],
            "estimated_runtime": 180.0,
            "targets": ["tests/properties/"],
        },
        "contract": {
            "name": "Contract Tests",
            "must_run_for": ["HIGH", "CRITICAL"],
            "estimated_runtime": 120.0,
            "targets": ["tests/contract/"],
        },
        "capability": {
            "name": "Capability Smoke Tests",
            "must_run_for": ["HIGH", "CRITICAL"],
            "estimated_runtime": 60.0,
            "targets": ["tests/capability/"],
        },
        "invariant": {
            "name": "Invariant Tests",
            "must_run_for": ["MEDIUM", "HIGH", "CRITICAL"],
            "estimated_runtime": 60.0,
            "targets": ["tests/invariants/"],
        },
        "golden": {
            "name": "Golden Regression",
            "must_run_for": ["HIGH", "CRITICAL"],
            "estimated_runtime": 90.0,
            "targets": ["tests/golden/"],
        },
        "integration": {
            "name": "Integration Tests",
            "must_run_for": ["CRITICAL"],
            "estimated_runtime": 180.0,
            "targets": ["tests/integration/"],
        },
        "architecture": {
            "name": "Architecture Tests",
            "must_run_for": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "estimated_runtime": 30.0,
            "targets": ["tests/architecture/"],
        },
        "mutation": {
            "name": "Mutation Testing",
            "must_run_for": ["CRITICAL"],
            "estimated_runtime": 3600.0,
            "targets": ["src/engines/"],
        },
        "meta": {
            "name": "Meta / Registry Tests",
            "must_run_for": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
            "estimated_runtime": 15.0,
            "targets": ["tests/meta/"],
        },
    }

    def __init__(self) -> None:
        self._impact: dict[str, Any] = {}

    def plan(
        self, changed_files: list[str], impact: dict[str, Any] | None = None
    ) -> SelectivePlan:
        """Generate a selective CI execution plan."""
        if impact is None:
            from src.verification.intelligence.impact_engine import ImpactEngine

            impact_engine = ImpactEngine()
            impact_result = impact_engine.analyze(changed_files)
            impact = impact_result.to_dict()

        plan = SelectivePlan(
            changed_files=changed_files,
            strategy=impact.get("strategy", "full"),
            overall_risk=impact.get("overall_risk", "LOW"),
            affected_capabilities=[
                c["id"] for c in impact.get("affected_capabilities", [])
            ],
            affected_engines=[e["id"] for e in impact.get("affected_engines", [])],
            generated_at=hashlib.sha256(
                (str(changed_files) + str(impact.get("affected_capabilities", []))).encode()
            ).hexdigest()[:16],
        )

        risk = plan.overall_risk

        for job_id, job_def in self.JOB_DEFINITIONS.items():
            must_run = risk in job_def["must_run_for"]
            reason = (
                f"Risk level {risk} requires this job"
                if must_run
                else f"Risk level {risk} below threshold for {job_def['name']}"
            )

            job = CIJob(
                job_id=job_id,
                name=job_def["name"],
                must_run=must_run,
                reason=reason,
                targets=job_def["targets"],
                estimated_runtime_seconds=job_def["estimated_runtime"],
            )

            plan.jobs.append(job)
            if must_run:
                plan.must_run_jobs.append(job)
            else:
                plan.skipped_jobs.append(job)

        return plan

    def generate_github_actions_matrix(self, plan: SelectivePlan) -> dict[str, Any]:
        """Generate GitHub Actions matrix configuration."""
        matrix: dict[str, list[str]] = {}

        for job in plan.must_run_jobs:
            if job.targets:
                matrix[job.job_id] = job.targets

        return matrix

    def generate_workflow_increment(self, plan: SelectivePlan) -> dict[str, Any]:
        """Generate incremental workflow configuration."""
        return {
            "strategy": plan.strategy,
            "overall_risk": plan.overall_risk,
            "affected_capabilities": plan.affected_capabilities,
            "affected_engines": plan.affected_engines,
            "must_run_jobs": [j.job_id for j in plan.must_run_jobs],
            "skipped_jobs": [j.job_id for j in plan.skipped_jobs],
            "estimated_total_runtime_seconds": sum(
                j.estimated_runtime_seconds for j in plan.must_run_jobs
            ),
        }

def generate_selective_plan(
    changed_files: list[str],
    impact: dict[str, Any] | None = None,
) -> SelectivePlan:
    """Convenience function to generate a selective plan."""
    engine = SelectiveEngine()
    return engine.plan(changed_files, impact)

def get_ci_job_status(job_id: str, risk_level: str) -> bool:
    """Check if a CI job must run for a given risk level."""
    job_def = SelectiveEngine.JOB_DEFINITIONS.get(job_id)
    if not job_def:
        return True
    return risk_level in job_def["must_run_for"]
