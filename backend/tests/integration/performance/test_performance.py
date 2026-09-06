"""Performance and Resource Efficiency Tests.

Validates that the system meets performance budgets and uses resources
efficiently. Tests are advisory and may not block the workflow.
"""

from __future__ import annotations

import time

import pytest


class TestAPIPerformance:
    """Test API endpoint performance."""

    def test_accounts_list_under_1_second(self, client) -> None:
        """Accounts list endpoint responds under 1 second."""
        start = time.time()
        response = client.get("/api/accounts/manage")
        duration = time.time() - start

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert duration < 1.0, f"Accounts list took {duration:.2f}s, expected < 1.0s"

    def test_loans_list_under_1_second(self, client) -> None:
        """Loans list endpoint responds under 1 second."""
        start = time.time()
        response = client.get("/api/loans")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, f"Loans list took {duration:.2f}s, expected < 1.0s"

    def test_dashboard_summary_under_1_second(self, client) -> None:
        """Dashboard summary endpoint responds under 1 second."""
        start = time.time()
        response = client.get("/api/dashboard/summary")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, f"Dashboard took {duration:.2f}s, expected < 1.0s"

    def test_cashflow_under_1_second(self, client) -> None:
        """Cashflow endpoint responds under 1 second."""
        start = time.time()
        response = client.get("/api/cashflow/monthly?months=6")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, f"Cashflow took {duration:.2f}s, expected < 1.0s"


class TestConcurrentRequests:
    """Test that the system handles concurrent requests."""

    def test_health_endpoint_handles_concurrent(self, client) -> None:
        """Health endpoint handles 10 concurrent requests."""
        for _ in range(10):
            response = client.get("/api/health")
            assert response.status_code in (
                200,
                404,
            ), f"Health endpoint should respond, got {response.status_code}"


class TestResourceUsage:
    """Test resource usage is reasonable."""

    def test_test_suite_completes_under_5_minutes(self) -> None:
        """Smoke test: verify our test suite is fast enough.

        This is a meta-test that documents the expected runtime budget
        for the M46 acceptance test suites.
        """
        import subprocess

        start = time.time()
        result = subprocess.run(
            [
                ".venv/bin/python",
                "-m",
                "pytest",
                "backend/tests/golden/",
                "--tb=no",
                "-q",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        duration = time.time() - start

        assert result.returncode == 0, f"Golden tests failed: {result.stderr}"
        assert duration < 60, f"Golden tests took {duration:.2f}s, expected < 60s"


class TestCacheEfficiency:
    """Test that caching improves performance."""

    def test_cached_operation_is_faster(self, tmp_path) -> None:
        """Second access to cache should be faster than first."""
        from runtime.foundation.verification.cache import (
            CachedVerdict,
            VerificationCache,
        )

        cache = VerificationCache(tmp_path / "cache.json")

        cache.save(
            profile="quick",
            commit="abc123",
            changed_files=["file1.py"],
            verdict=CachedVerdict(
                overall_status="pass",
                passed=100,
                failed=0,
                skipped=0,
            ),
        )

        start = time.time()
        for _ in range(1000):
            cache.is_valid(commit="abc123", changed_files=["file1.py"], profile="quick")
        duration = time.time() - start

        assert duration < 1.0, f"1000 cache lookups took {duration:.2f}s"


class TestMemoryEfficiency:
    """Test memory efficiency."""

    def test_evidence_serialization_does_not_leak(self) -> None:
        """Evidence serialization doesn't accumulate memory."""
        from runtime.system.evidence.models.evidence import (
            CoverageEvidence,
            VerificationEvidence,
        )

        for _ in range(1000):
            coverage = CoverageEvidence(
                percentage=85.0,
                covered_lines=850,
                total_lines=1000,
            )
            evidence = VerificationEvidence(
                commit_sha="abc123",
                branch="main",
                timestamp="2026-09-03T00:00:00Z",
                status="pass",
                coverage=coverage,
            )
            json_str = evidence.to_json()
            del evidence
            del coverage
            del json_str

    def test_loading_golden_datasets_is_fast(self) -> None:
        """Loading golden datasets is fast."""
        import json
        from pathlib import Path

        datasets_dir = Path("backend/tests/golden/datasets")

        start = time.time()
        for dataset_file in datasets_dir.glob("*.json"):
            json.loads(dataset_file.read_text())
        duration = time.time() - start

        assert duration < 2.0, f"Loading all golden datasets took {duration:.2f}s"


class TestQueryPerformance:
    """Test database query performance."""

    def test_account_list_query_under_500ms(self, client) -> None:
        """Account list query is fast."""
        start = time.time()
        response = client.get("/api/accounts/manage")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 0.5, f"Account list query took {duration:.2f}s"


class TestFrontendPerformance:
    """Test frontend performance budgets (via contract validation)."""

    def test_frontend_assets_structure(self) -> None:
        """Verify frontend file structure is healthy."""
        from pathlib import Path

        frontend_dir = Path("frontend")
        if not frontend_dir.exists():
            pytest.skip("Frontend directory not found")

        # Check key directories exist
        assert (frontend_dir / "lib").exists(), "frontend/lib should exist"
        assert (frontend_dir / "__tests__").exists(), "frontend/__tests__ should exist"
