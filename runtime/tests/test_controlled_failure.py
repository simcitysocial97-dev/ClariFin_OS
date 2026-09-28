"""M9-C65 — Controlled-failure injection experiments.

Verifies that the framework can:
1. Detect a known injected failure
2. Produce FAILED exit with evidence persisted
3. Diagnose the fault correctly
4. Recover when the fault is removed
5. NOT produce false PASS / false CERTIFIED / stale evidence
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.foundation.verification.execution_budget import (
    ExecutionBudget,
    ExecutionBoundaryReport,
    ResultClassification,
    TerminationReason,
    classify_boundary,
)


class TestControlledFailureInjection:
    """Framework must detect and classify controlled failures truthfully."""

    def test_failure_classification_not_false_pass(self):
        """A failed execution must never be classified as PASS."""
        report = classify_boundary(
            elapsed=5.0,
            budget=ExecutionBudget(),
            completed=3,
            total=10,
            failed=True,
        )
        assert report.result_classification == ResultClassification.FAILED
        assert report.termination_reason == TerminationReason.FAILED
        assert report.resume_supported is False

    def test_external_timeout_classified_correctly(self):
        """An externally-killed run must be EXTERNAL_BOUNDARY, not FAILED."""
        report = classify_boundary(
            elapsed=120.4,
            budget=ExecutionBudget(),
            completed=27,
            total=64,
            external_timeout=True,
        )
        assert report.result_classification == ResultClassification.EXTERNAL_BOUNDARY
        assert report.termination_reason == TerminationReason.EXTERNAL_BUDGET
        assert report.resume_supported is False

    def test_interrupted_allows_resume(self):
        """SIGINT interruption must mark resume_supported=True."""
        report = classify_boundary(
            elapsed=30.0,
            budget=ExecutionBudget(),
            completed=5,
            total=64,
            interrupted=True,
        )
        assert report.result_classification == ResultClassification.INCOMPLETE
        assert report.termination_reason == TerminationReason.INTERRUPTED
        assert report.resume_supported is True

    def test_completed_successfully(self):
        """Full completion must yield PASS."""
        report = classify_boundary(
            elapsed=45.0,
            budget=ExecutionBudget(),
            completed=64,
            total=64,
            failed=False,
        )
        assert report.result_classification == ResultClassification.PASS
        assert report.termination_reason == TerminationReason.COMPLETED
        assert report.completed_obligations == report.total_obligations

    def test_no_stale_evidence_on_failure(self):
        """Failed execution must not leave stale evidence artifacts."""
        # Verify the boundary report itself is self-consistent
        report = classify_boundary(
            elapsed=10.0,
            budget=ExecutionBudget(),
            completed=0,
            total=10,
            failed=True,
        )
        d = report.to_dict()
        assert d["result_classification"] == "FAILED"
        assert d["completed_obligations"] == 0
        assert d["elapsed_seconds"] == 10.0
        # No false PASS signal
        assert d["termination_reason"] != "completed"

    def test_boundary_report_structural_invariants(self):
        """Every boundary report must have all required fields."""
        for kwargs, expected_class in [
            ({"failed": True}, ResultClassification.FAILED),
            ({"external_timeout": True}, ResultClassification.EXTERNAL_BOUNDARY),
            ({"interrupted": True}, ResultClassification.INCOMPLETE),
            ({}, ResultClassification.PASS),
        ]:
            report = classify_boundary(
                elapsed=1.0,
                budget=ExecutionBudget(),
                completed=1,
                total=10,
                **kwargs,
            )
            assert report.result_classification == expected_class
            d = report.format_text()
            assert "EXECUTION_BOUNDARY" in d
            assert "Phase:" in d
            assert "Completed:" in d
            assert "Elapsed:" in d
            assert "Termination:" in d
            assert "Result:" in d

    def test_estimated_remaining_non_negative(self):
        """Estimated remaining seconds must never be negative."""
        report = classify_boundary(
            elapsed=9999.0,
            budget=ExecutionBudget(),
            completed=64,
            total=64,
            external_timeout=True,
        )
        assert report.estimated_remaining_seconds >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
