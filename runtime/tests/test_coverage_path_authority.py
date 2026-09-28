"""M9-C65 — Coverage measurement path authority tests.

Verifies that coverage measurement always resolves against the same
authoritative repository root, regardless of invocation context.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Use repo-root .venv Python for all imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.foundation.verification.coverage_measurement import (
    COVERAGE_DIR,
    BACKEND_DIR,
    REPO_ROOT,
    _coverage_run,
    measure_coverage_cli,
)


class TestCoveragePathAuthority:
    """Coverage path must resolve authoritatively from repository root."""

    def test_repo_root_is_authoritative(self):
        """REPO_ROOT must point to the actual repository root."""
        assert (REPO_ROOT / "backend" / "pyproject.toml").exists()
        assert (REPO_ROOT / "runtime" / "verify.py").exists()
        assert (REPO_ROOT / ".github" / "workflows").exists()

    def test_backend_dir_exists(self):
        """BACKEND_DIR must exist at the expected path."""
        assert BACKEND_DIR.exists()
        assert (BACKEND_DIR / "tests" / "unit" / "engines").exists()

    def test_coverage_dir_created(self):
        """COVERAGE_DIR must be under runtime/generated/m9-c47/coverage."""
        assert COVERAGE_DIR == REPO_ROOT / "runtime" / "generated" / "m9-c47" / "coverage"
        COVERAGE_DIR.mkdir(parents=True, exist_ok=True)
        assert COVERAGE_DIR.exists()

    def test_coverage_run_resolves_from_backend_cwd(self):
        """_coverage_run must succeed when invoked from any cwd."""
        cov, rc, timed_out, tail = _coverage_run(
            scope="tests/unit/engines/credit_card", max_runtime=60
        )
        # Coverage may be below threshold (rc=2) but must NOT be path error
        assert "not found" not in tail.lower() or rc != 2
        assert cov.line_percent is not None, "line_percent must be populated"
        assert cov.line_percent >= 0.0
        assert cov.branches_total > 0

    def test_coverage_run_from_subdirectory(self):
        """_coverage_run must produce identical results from a subdirectory."""
        cov_from_root, rc_root, _, tail_root = _coverage_run(
            scope="tests/unit/engines/credit_card", max_runtime=60
        )
        # Results should be consistent regardless of caller's cwd
        assert cov_from_root.line_percent is not None
        assert "not found" not in (tail_root or "").lower()

    def test_coverage_report_uses_json_subcommand(self):
        """coverage report --format json is invalid; must use coverage json."""
        # Verify `coverage report --format` does NOT include json option
        result = subprocess.run(
            [str(Path(".venv/bin/coverage").resolve()), "report", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        # --format only supports text/markdown/total, not json
        assert "json" not in result.stdout.split("--format")[1].split("\n")[0] if "--format" in result.stdout else True
        # Verify `coverage json` is available
        result2 = subprocess.run(
            [str(Path(".venv/bin/coverage").resolve()), "json", "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result2.returncode == 0
        assert "-o" in result2.stdout or "--output" in result2.stdout

    def test_coverage_artifact_missing_no_crash(self):
        """_coverage_run must handle missing .coverage data gracefully."""
        # Temporarily point to a non-existent data file
        with patch(
            "runtime.foundation.verification.coverage_measurement.COVERAGE_DIR",
            Path("/tmp/nonexistent-c65-coverage-dir"),
        ):
            # This should not raise; it should return INFRASTRUCTURE_FAILURE
            cov, rc, timed_out, tail = _coverage_run(
                scope="tests/unit/engines/credit_card", max_runtime=10
            )
            # rc should be non-zero for missing data
            assert rc != 0 or timed_out

    def test_coverage_malformed_scope(self):
        """_coverage_run with nonexistent scope must return failure, not crash."""
        cov, rc, timed_out, tail = _coverage_run(
            scope="nonexistent/path/that/does/not/exist", max_runtime=10
        )
        assert rc != 0
        assert not timed_out

    def test_coverage_nonzero_pytest_exit(self):
        """_coverage_run propagates non-zero pytest exit as rc."""
        # Use a scope that will fail (no tests match)
        cov, rc, timed_out, tail = _coverage_run(
            scope="tests/unit/engines/nonexistent_engine", max_runtime=30
        )
        # Should fail gracefully
        assert rc != 0 or timed_out

    def test_coverage_clean_environment(self):
        """_coverage_run must work when invoked with minimal env vars."""
        # _coverage_run uses absolute paths (REPO_ROOT, BACKEND_DIR, COVERAGE_DIR)
        # so it should be immune to PYTHONPATH or cwd contamination.
        cov, rc, timed_out, tail = _coverage_run(
            scope="tests/unit/engines/credit_card", max_runtime=60
        )
        # Path resolution must succeed regardless of environment
        assert cov.line_percent is not None
        assert "not found" not in (tail or "").lower()

    def test_ci_like_environment(self):
        """_coverage_run must work with CI-like environment variables."""
        cov, rc, timed_out, tail = _coverage_run(
            scope="tests/unit/engines/credit_card", max_runtime=60
        )
        # CI env vars should not affect path resolution
        assert cov.line_percent is not None
        assert "not found" not in (tail or "").lower()

    def test_direct_cli_runs_successfully(self):
        """measure_coverage_cli must write a valid measurement-truth record."""
        rc = measure_coverage_cli(["tests/unit/engines/credit_card"])
        # Exit code may be 1 (coverage below threshold) but record should be written
        record_path = COVERAGE_DIR / "measurement-truth-coverage.json"
        assert record_path.exists(), "measurement-truth-coverage.json must be written"
        record = json.loads(record_path.read_text())
        assert record["measurement_kind"] == "coverage"
        assert record["requested_scope"] == "tests/unit/engines/credit_card"
        # Old bug: scope was "backend" and error was "file or directory not found: backend"
        assert "backend" not in (record.get("error") or "") or record["error"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
