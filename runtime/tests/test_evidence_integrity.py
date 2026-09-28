"""M9-C55 — Evidence Schema Integrity Tests.

Verifies that evidence classes use the unified schema and round-trip
through JSON without data loss.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from runtime.foundation.verification.evidence_schema import (
    CoverageEvidence,
    MutationEvidence,
    VerificationEvidence,
)


class TestEvidenceIntegrity:
    """Test evidence schema correctness."""

    def test_coverage_roundtrip(self):
        original = CoverageEvidence(
            percentage=75.5,
            covered_lines=755,
            total_lines=1000,
            gaps=["line 10", "line 20"],
            source="backend",
        )
        dumped = json.loads(original.to_json())
        restored = CoverageEvidence(**dumped)
        assert original.percentage == restored.percentage
        assert original.covered_lines == restored.covered_lines
        assert original.total_lines == restored.total_lines
        assert original.gaps == restored.gaps

    def test_mutation_roundtrip(self):
        original = MutationEvidence(
            score=88.5,
            killed=180,
            survived=20,
            timeout=1,
            error=0,
            skipped=2,
            survivor_details=[{"loc": "emi.py:42"}],
        )
        dumped = json.loads(original.to_json())
        restored = MutationEvidence(**dumped)
        assert original.score == restored.score
        assert original.survived == restored.survived
        assert original.survivor_details == restored.survivor_details

    def test_verification_roundtrip(self):
        original = VerificationEvidence(
            commit_sha="abc123",
            branch="test-branch",
            timestamp="2024-01-01T00:00:00Z",
            status="pass",
            coverage=CoverageEvidence(percentage=80.0, covered_lines=800, total_lines=1000),
            mutation=MutationEvidence(score=85.0, killed=170, survived=30),
        )
        dumped = json.loads(original.to_json())
        restored = VerificationEvidence.from_dict(dumped)
        assert original.commit_sha == restored.commit_sha
        assert original.status == restored.status
        assert original.coverage.percentage == restored.coverage.percentage  # type: ignore[union-attr]
        assert original.mutation.score == restored.mutation.score  # type: ignore[union-attr]

    def test_backward_compatible_imports(self):
        """Old import paths must still resolve via re-exports."""
        from runtime.system.evidence.models.evidence import (
            CoverageEvidence as OldCoverage,
            MutationEvidence as OldMutation,
            VerificationEvidence as OldVerification,
        )
        assert OldCoverage is CoverageEvidence
        assert OldMutation is MutationEvidence
        assert OldVerification is VerificationEvidence

    def test_old_imports_functional(self):
        """Evidence created via old import path must work identically."""
        from runtime.system.evidence.models.evidence import CoverageEvidence

        ev = CoverageEvidence(percentage=90.0, covered_lines=900, total_lines=1000)
        assert ev.percentage == 90.0
        assert ev.to_dict()["percentage"] == 90.0
