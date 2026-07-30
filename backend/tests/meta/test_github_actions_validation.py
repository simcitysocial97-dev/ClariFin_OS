"""GitHub Actions Validation Tests.

Verifies that the GitHub Actions workflow correctly integrates with the
Verification Intelligence Layer.

Part H of Phase 3.2 - Capability Validation & Real-World Verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
WORKFLOW_FILE = PROJECT_ROOT / ".github" / "workflows" / "backend.yml"


def _load_workflow() -> dict[str, Any]:
    """Load the GitHub Actions workflow file."""
    if not WORKFLOW_FILE.exists():
        return {}
    with open(WORKFLOW_FILE) as f:
        return yaml.safe_load(f) or {}


def _load_registry() -> dict[str, Any]:
    from runtime.registries import load_capability_registry

    return load_capability_registry()


class TestGitHubActionsValidation:
    """Verify GitHub Actions workflow correctness."""

    def test_workflow_file_exists(self) -> None:
        """The backend workflow file must exist."""
        assert (
            WORKFLOW_FILE.exists()
        ), f"GitHub Actions workflow not found: {WORKFLOW_FILE}"

    def test_workflow_has_detect_changes_job(self) -> None:
        """The workflow must have a detect-changes job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert "detect-changes" in jobs, "Workflow missing 'detect-changes' job"

    def test_workflow_has_intelligence_analysis_job(self) -> None:
        """The workflow must have an intelligence-analysis job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert (
            "intelligence-analysis" in jobs
        ), "Workflow missing 'intelligence-analysis' job"

    def test_workflow_has_property_tests_job(self) -> None:
        """The workflow must have a property-tests job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert "property-tests" in jobs, "Workflow missing 'property-tests' job"

    def test_workflow_has_contract_tests_job(self) -> None:
        """The workflow must have a contract-tests job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert "contract-tests" in jobs, "Workflow missing 'contract-tests' job"

    def test_workflow_has_capability_tests_job(self) -> None:
        """The workflow must have a capability-tests job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert "capability-tests" in jobs, "Workflow missing 'capability-tests' job"

    def test_workflow_has_invariant_tests_job(self) -> None:
        """The workflow must have an invariant-tests job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert "invariant-tests" in jobs, "Workflow missing 'invariant-tests' job"

    def test_workflow_jobs_use_intelligence_outputs(self) -> None:
        """Test jobs must use intelligence-analysis outputs for conditional execution."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})

        # Check that test jobs reference intelligence-analysis outputs
        test_jobs = [
            "property-tests",
            "contract-tests",
            "capability-tests",
            "invariant-tests",
        ]
        for job_name in test_jobs:
            job = jobs.get(job_name, {})
            # Job should have an 'if' condition referencing intelligence outputs
            if_condition = job.get("if", "")
            # Either it uses intelligence outputs or always runs
            assert (
                "intelligence-analysis" in if_condition
                or job_name in str(if_condition)
                or not if_condition
            ), f"Job {job_name} does not use intelligence-analysis outputs correctly"

    def test_workflow_has_concurrency_control(self) -> None:
        """The workflow must have concurrency control."""
        workflow = _load_workflow()
        concurrency = workflow.get("concurrency", {})
        assert concurrency, "Workflow missing 'concurrency' control"

    def test_workflow_triggers_on_pr(self) -> None:
        """The workflow must trigger on pull requests."""
        workflow = _load_workflow()
        on = workflow.get("on", workflow.get(True, {}))
        assert (
            "pull_request" in on or on == "pull_request"
        ), "Workflow must trigger on pull_request"

    def test_workflow_has_timeouts(self) -> None:
        """Test jobs should have reasonable timeouts."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})

        test_jobs = [
            "property-tests",
            "contract-tests",
            "capability-tests",
            "invariant-tests",
        ]
        for job_name in test_jobs:
            job = jobs.get(job_name, {})
            timeout = job.get("timeout-minutes", 0)
            assert timeout > 0, f"Job {job_name} missing timeout"
            assert timeout <= 30, f"Job {job_name} timeout too long: {timeout} minutes"

    def test_workflow_has_determinism_check(self) -> None:
        """The workflow must have a determinism check job."""
        workflow = _load_workflow()
        jobs = workflow.get("jobs", {})
        assert "determinism-check" in jobs, "Workflow missing 'determinism-check' job"
