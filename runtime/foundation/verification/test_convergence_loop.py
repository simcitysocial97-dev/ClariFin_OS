"""Repository-Wide Convergence Loop Tests.

Tests that verify the convergence pipeline and overall verification
infrastructure work together in a continuous loop.
"""

from __future__ import annotations

from datetime import UTC


class TestConvergencePipelineImports:
    """Test that convergence pipeline can be imported."""

    def test_convergence_pipeline_imports(self) -> None:
        """Convergence pipeline module can be imported."""
        from runtime.foundation.verification import convergence_pipeline

        assert convergence_pipeline is not None

    def test_convergence_result_imports(self) -> None:
        """ConvergenceResult can be imported."""
        from runtime.foundation.verification.convergence_pipeline import (
            ConvergenceResult,
        )

        assert ConvergenceResult is not None

    def test_gap_target_imports(self) -> None:
        """GapTarget can be imported."""
        from runtime.foundation.verification.convergence_pipeline import GapTarget

        assert GapTarget is not None


class TestConvergenceDataClasses:
    """Test convergence pipeline dataclasses."""

    def test_convergence_result_creates(self) -> None:
        """ConvergenceResult can be instantiated."""
        from datetime import datetime

        from runtime.foundation.verification.convergence_pipeline import (
            ConvergenceResult,
        )

        result = ConvergenceResult(
            run_id="test-run-1",
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            initial_score=80.0,
            final_score=85.0,
            targets_loaded=10,
            tests_generated=5,
            tests_applied=3,
            tests_passed=3,
            survivors_killed=2,
            duration_seconds=60.0,
        )

        assert result.run_id == "test-run-1"
        assert result.initial_score == 80.0
        assert result.final_score == 85.0
        assert result.targets_loaded == 10

    def test_gap_target_creates(self) -> None:
        """GapTarget can be instantiated."""
        from runtime.foundation.verification.convergence_pipeline import GapTarget

        target = GapTarget(
            gap_id="gap-1",
            component="account_engine",
            capability="account-metrics",
            surface="compute_balance",
            gap_type="mutation_survivor",
            original_expression="balance_paise > 0",
            mutated_expression="balance_paise >= 0",
            classification="A",
            subclassification="safe_boundary",
        )

        assert target.gap_id == "gap-1"
        assert target.component == "account_engine"
        assert target.gap_type == "mutation_survivor"


class TestVerificationOrchestrator:
    """Test verification orchestrator."""

    def test_orchestrator_imports(self) -> None:
        """Verification orchestrator can be imported."""
        from runtime.foundation.verification.orchestrator import (
            VerificationOrchestrator,
        )

        assert VerificationOrchestrator is not None


class TestVerificationIntegration:
    """Test that verification components integrate together."""

    def test_profiles_work_with_cache(self, tmp_path) -> None:
        """Verification profiles work with cache system."""
        from runtime.foundation.verification.cache import VerificationCache
        from runtime.foundation.verification.profiles import get_profile

        profile = get_profile("quick")
        assert profile.name == "quick"

        cache = VerificationCache(tmp_path / "cache.json")
        assert cache is not None

    def test_evidence_aggregator_imports(self) -> None:
        """Evidence aggregator can be imported."""
        from runtime.system.evidence.aggregator import EvidenceAggregator

        assert EvidenceAggregator is not None

    def test_profiles_can_be_listed(self) -> None:
        """All profiles can be listed."""
        from runtime.foundation.verification.profiles import list_profiles

        profiles = list_profiles()
        assert len(profiles) >= 11
        profile_names = [p.name for p in profiles]
        assert "quick" in profile_names
        assert "backend" in profile_names
        assert "golden" in profile_names


class TestVerificationLoop:
    """Test the complete verification loop."""

    def test_convergence_result_to_dict(self) -> None:
        """ConvergenceResult can be serialized to dict."""
        from datetime import datetime

        from runtime.foundation.verification.convergence_pipeline import (
            ConvergenceResult,
        )

        result = ConvergenceResult(
            run_id="test-1",
            started_at=datetime.now(UTC).isoformat(),
            completed_at=datetime.now(UTC).isoformat(),
            initial_score=75.0,
            final_score=80.0,
            targets_loaded=5,
            tests_generated=3,
            tests_applied=2,
            tests_passed=2,
            survivors_killed=1,
            duration_seconds=30.0,
        )

        data = result.to_dict()
        assert isinstance(data, dict)
        assert data["run_id"] == "test-1"
        assert data["initial_score"] == 75.0
        assert data["final_score"] == 80.0

    def test_cache_integrates_with_profiles(self, tmp_path) -> None:
        """Cache correctly handles profile results."""
        from runtime.foundation.verification.cache import (
            VerificationCache,
        )

        cache = VerificationCache(tmp_path / "cache.json")
        assert hasattr(cache, "save")
        assert hasattr(cache, "replay")
        assert hasattr(cache, "is_valid")

    def test_evidence_unifies_across_types(self) -> None:
        """Evidence can be unified across different evidence types."""
        from runtime.system.evidence.models.evidence import (
            CoverageEvidence,
            MutationEvidence,
            VerificationEvidence,
        )

        coverage = CoverageEvidence(
            percentage=90.0, covered_lines=900, total_lines=1000
        )
        mutation = MutationEvidence(score=85.0, killed=85, survived=15)

        evidence = VerificationEvidence(
            commit_sha="abc123",
            branch="main",
            timestamp="2026-09-03T00:00:00Z",
            status="pass",
            coverage=coverage,
            mutation=mutation,
        )

        assert evidence.coverage is not None
        assert evidence.mutation is not None
        assert evidence.coverage.percentage == 90.0
        assert evidence.mutation.score == 85.0
