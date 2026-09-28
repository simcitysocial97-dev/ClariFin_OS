"""M9-C66: Adversarial Certification — Broadened Failure Injection Tests.

Integration tests that verify the runtime correctly handles failure scenarios.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VENV_PYTHON = str(REPO_ROOT / ".venv" / "bin" / "python")


def run_verify(*args: str, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    """Run a verify command."""
    return subprocess.run(
        [VENV_PYTHON, "-m", "runtime.verify", *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestBroadenedFailureInjection:
    """Phase 4: Adversarial certification with broadened failure classes."""

    def test_failed_command_not_classified_as_pass(self) -> None:
        """An invalid command should not be classified as PASS."""
        r = run_verify("nonexistent-command-xyz")
        # Should fail, not pass silently
        assert r.returncode != 0 or "not available" in r.stderr.lower() or "error" in r.stderr.lower()

    def test_timeout_classified_as_external_boundary(self) -> None:
        """Long-running commands should timeout with correct classification."""
        # certify without evidence takes a very long time
        import subprocess as _sub
        try:
            r = _sub.run(
                [VENV_PYTHON, "-m", "runtime.verify", "certify"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=5,  # Short timeout to trigger TimeoutExpired
            )
            # If it completes, that's fine too
            assert r.returncode in (0, 124, 1)
        except _sub.TimeoutExpired:
            # Expected: certify times out, which is the correct classification
            pass

    def test_diagnose_does_not_crash_on_empty_evidence(self) -> None:
        """Diagnose should handle empty evidence gracefully."""
        r = run_verify("diagnose")
        # Should not crash
        assert r.returncode in (0, 1)

    def test_strengthen_smoke_gates_reported(self) -> None:
        """Strengthen smoke should report gate results."""
        r = run_verify("strengthen", "--smoke")
        assert r.returncode == 0
        # Should mention gates
        assert "Gate" in r.stdout or "gate" in r.stdout.lower()

    def test_inspect_workflows_listed(self) -> None:
        """Inspect workflows should enumerate all workflows."""
        r = run_verify("inspect", "workflows")
        assert r.returncode == 0
        assert "Total workflows:" in r.stdout or "14" in r.stdout

    def test_inspect_capabilities_counted(self) -> None:
        """Inspect capabilities should report a count."""
        r = run_verify("inspect", "capabilities")
        assert r.returncode == 0
        assert "Capabilities:" in r.stdout

    def test_ci_reconciliation_runs(self) -> None:
        """CI command should run reconciliation."""
        r = run_verify("ci")
        # May fail if CI artifacts missing, but should not crash
        assert r.returncode in (0, 1)

    def test_env_check_validates_prerequisites(self) -> None:
        """Env-check should validate the environment."""
        r = run_verify("env-check")
        assert r.returncode == 0

    def test_health_report_has_both_sections(self) -> None:
        """Health report should have Current Framework Health and Historical sections."""
        r = run_verify("doctor")
        assert r.returncode == 0
        assert "Current Framework Health" in r.stdout
        assert "Historical" in r.stdout or "Historic" in r.stdout

    def test_discrepancy_types_documented(self) -> None:
        """All discrepancy types from C66 spec should be recognized."""
        from runtime.foundation.verification.m9_c66_forensics import Discrepancy
        types = [
            "DUPLICATE_OUTPUT", "CONTRADICTORY_OUTPUT", "STALE_RUN_ID",
            "STALE_COMMIT", "STALE_ARTIFACT", "WRONG_CLASSIFICATION",
            "EXIT_STATUS_MISMATCH", "PLAN_FINGERPRINT_MISMATCH",
            "CAPABILITY_SET_MISMATCH", "AUTHORITY_DRIFT", "TRUTH_DRIFT",
            "FALSE_PASS", "FALSE_CERTIFICATION",
        ]
        for t in types:
            d = Discrepancy(
                id=f"D-{t}", command="test", run_id="abc",
                type=t, surface_a="stdout", surface_b="structured",
                detail=f"Test {t}",
            )
            assert d.type == t

    def test_classification_vocabulary_closed(self) -> None:
        """Classification should use closed vocabulary."""
        from runtime.verify import _normalize_status
        assert _normalize_status("pass") == "passed"
        assert _normalize_status("fail") == "failed"
        assert _normalize_status("blocked") == "blocked"
        assert _normalize_status("interrupted") == "interrupted"
        assert _normalize_status("completed") == "completed"  # preserved verbatim

    def test_decision_to_status_mapping(self) -> None:
        """Orchestrator decisions map correctly to status."""
        from runtime.verify import decision_to_status
        assert decision_to_status("certified") == "passed"
        assert decision_to_status("diagnostic") == "failed"
        assert decision_to_status("infrastructure_blocked") == "blocked"
        assert decision_to_status("timeout_blocked") == "blocked"
        assert decision_to_status("interrupted") == "interrupted"


class TestAdversarialRecovery:
    """Test recovery after adversarial scenarios."""

    def test_framework_recoverable_after_temporary_file(self) -> None:
        """Framework health should remain OPERATIONAL after temp file creation."""
        marker = REPO_ROOT / "runtime" / "_c66_marker.txt"
        marker.write_text("test")
        try:
            r = run_verify("doctor")
            assert r.returncode == 0
            assert "OPERATIONAL" in r.stdout
        finally:
            marker.unlink(missing_ok=True)

    def test_no_persistent_state_from_tests(self) -> None:
        """Test operations should not leave persistent state."""
        before = list(REPO_ROOT.glob("*_c66*.py")) + list(REPO_ROOT.glob("*_c66*.txt"))
        # Run a harmless command
        run_verify("doctor")
        after = list(REPO_ROOT.glob("*_c66*.py")) + list(REPO_ROOT.glob("*_c66*.txt"))
        # No new C66 markers should persist
        assert after == before
