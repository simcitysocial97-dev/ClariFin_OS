"""M9-C65 — inspect workflows first-class capability tests.

Verifies that `verify inspect workflows` enumerates .github/workflows/*.yml
with complete metadata, replacing the old capability-resolver delegation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.foundation.verification.workflow_inspection import (
    BoundaryClassification,
    WorkflowJob,
    WorkflowRecord,
    cmd_inspect_workflows,
    enumerate_workflows,
    format_workflows_table,
)


class TestInspectWorkflows:
    """inspect workflows must be a first-class enumeration capability."""

    def test_enumerates_all_workflows(self):
        """All .github/workflows/*.yml files must be enumerated."""
        records = enumerate_workflows()
        wf_dir = Path(".github/workflows")
        expected = len(list(wf_dir.glob("*.yml")))
        assert len(records) == expected, f"Expected {expected} workflows, got {len(records)}"

    def test_each_record_has_required_fields(self):
        """Every workflow record must have all required metadata fields."""
        records = enumerate_workflows()
        for w in records:
            assert w.workflow_id, "workflow_id must be non-empty"
            assert w.name, "name must be non-empty"
            assert w.path.startswith(".github/workflows/"), f"path must be relative: {w.path}"
            assert isinstance(w.triggers, list)
            assert isinstance(w.jobs, list)
            assert isinstance(w.commands, list)
            assert isinstance(w.local_executable, bool)
            assert isinstance(w.boundary_classification, BoundaryClassification)
            assert isinstance(w.parity_status, str)

    def test_job_metadata_complete(self):
        """Each job must have id, runs_on, steps, timeout."""
        records = enumerate_workflows()
        for w in records:
            for j in w.jobs:
                assert isinstance(j, WorkflowJob)
                assert j.job_id, f"job_id empty in {w.workflow_id}"
                assert isinstance(j.steps, list)
                assert j.timeout_minutes >= 0

    def test_boundary_classifications_reasonable(self):
        """Known workflows must have plausible boundary classifications."""
        records = enumerate_workflows()
        by_id = {w.workflow_id: w for w in records}

        # These are known GitHub-only workflows
        assert by_id["release"].boundary_classification == BoundaryClassification.GITHUB_ONLY
        assert by_id["security-codeql"].boundary_classification == BoundaryClassification.GITHUB_ONLY
        assert by_id["dependency-update"].boundary_classification == BoundaryClassification.GITHUB_ONLY

        # Known browser-boundary
        assert by_id["playwright"].boundary_classification == BoundaryClassification.BROWSER

        # Known local workflows
        assert by_id["backend-verify"].boundary_classification == BoundaryClassification.LOCAL
        assert by_id["verification-runtime"].boundary_classification == BoundaryClassification.LOCAL

    def test_local_executable_matches_boundary(self):
        """local_executable must be True only for LOCAL boundary workflows."""
        records = enumerate_workflows()
        for w in records:
            if w.boundary_classification == BoundaryClassification.LOCAL:
                assert w.local_executable is True, f"{w.workflow_id} should be local executable"
            elif w.boundary_classification in (
                BoundaryClassification.BROWSER,
                BoundaryClassification.ENVIRONMENT_BOUNDARY,
            ):
                assert w.local_executable is False, f"{w.workflow_id} should not be local executable"

    def test_output_not_empty(self):
        """Table output must contain workflow names and counts."""
        out = format_workflows_table(enumerate_workflows())
        assert "CI WORKFLOW INVENTORY" in out
        assert "Total workflows:" in out
        # Must list at least the known workflows
        assert "release" in out
        assert "mutation" in out

    def test_json_output_valid(self):
        """--json flag must produce valid JSON with expected schema."""
        import io
        from contextlib import redirect_stdout

        f = io.StringIO()
        with redirect_stdout(f):
            cmd_inspect_workflows(["--json"])
        data = json.loads(f.getvalue())
        assert data["schema"] == "m9-c65-workflow-inventory/v1"
        assert "workflows" in data
        assert len(data["workflows"]) > 0
        w = data["workflows"][0]
        assert "workflow_id" in w
        assert "boundary_classification" in w
        assert "local_executable" in w
        assert "canonical_command" in w

    def test_no_capability_resolver_delegation(self):
        """inspect workflows must NOT delegate to help-resolve/capability discovery."""
        import io
        from contextlib import redirect_stdout, redirect_stderr

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
            rc = cmd_inspect_workflows([])
        stdout = stdout_buf.getvalue()
        stderr = stderr_buf.getvalue()
        # Must not contain capability resolver output
        assert "CAPABILITY DISCOVERY" not in stdout
        assert "help-resolve" not in stdout.lower()
        assert "help-resolve" not in stderr.lower()
        # Must contain workflow inventory header
        assert "CI WORKFLOW INVENTORY" in stdout
        assert rc == 0

    def test_canonical_command_mapping(self):
        """Workflows with verify.py commands must map to canonical commands."""
        records = enumerate_workflows()
        by_id = {w.workflow_id: w for w in records}
        # m9-forensic-diagnostic-lab maps to verify doctor
        assert by_id["m9-forensic-diagnostic-lab"].canonical_command == "verify doctor"
        # playwright maps to evidence inspection proxy
        assert by_id["playwright"].canonical_command == "verify inspect evidence"

    def test_parity_status_consistent(self):
        """Parity status must match boundary classification logic."""
        records = enumerate_workflows()
        for w in records:
            if w.canonical_command:
                assert w.parity_status in ("PARITY_OK", "UNKNOWN")
            elif w.boundary_classification == BoundaryClassification.GITHUB_ONLY:
                assert w.parity_status == "GITHUB_ONLY"
            elif w.boundary_classification in (
                BoundaryClassification.BROWSER,
                BoundaryClassification.ENVIRONMENT_BOUNDARY,
            ):
                assert w.parity_status == "ENVIRONMENT_BOUNDARY"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
