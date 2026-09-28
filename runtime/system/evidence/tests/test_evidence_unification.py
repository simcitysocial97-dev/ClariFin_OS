"""Evidence Unification Tests.

Validates that all evidence types, collectors, and models work together
in a unified evidence system.
"""

from __future__ import annotations


class TestEvidenceModelUnification:
    """Validate evidence models are consistent."""

    def test_all_evidence_models_have_to_dict(self) -> None:
        """All evidence models have to_dict() method."""
        from runtime.system.evidence.models.evidence import (
            ContractEvidence,
            CoverageEvidence,
            EvidenceCollectionResult,
            MutationEvidence,
            TestResultEvidence,
            VerificationEvidence,
        )

        for model_cls in [
            CoverageEvidence,
            MutationEvidence,
            TestResultEvidence,
            ContractEvidence,
            VerificationEvidence,
            EvidenceCollectionResult,
        ]:
            assert hasattr(
                model_cls, "to_dict"
            ), f"{model_cls.__name__} missing to_dict()"
            assert callable(
                model_cls.to_dict
            ), f"{model_cls.__name__}.to_dict not callable"

    def test_all_evidence_models_have_to_json(self) -> None:
        """All evidence models have to_json() method."""
        from runtime.system.evidence.models.evidence import (
            ContractEvidence,
            CoverageEvidence,
            EvidenceCollectionResult,
            MutationEvidence,
            TestResultEvidence,
            VerificationEvidence,
        )

        for model_cls in [
            CoverageEvidence,
            MutationEvidence,
            TestResultEvidence,
            ContractEvidence,
            VerificationEvidence,
            EvidenceCollectionResult,
        ]:
            assert hasattr(
                model_cls, "to_json"
            ), f"{model_cls.__name__} missing to_json()"

    def test_verification_evidence_has_from_methods(self) -> None:
        """VerificationEvidence has from_dict() and from_json() for round-trip."""
        from runtime.system.evidence.models.evidence import VerificationEvidence

        assert hasattr(VerificationEvidence, "from_dict")
        assert hasattr(VerificationEvidence, "from_json")
        assert hasattr(VerificationEvidence, "write")


class TestCollectorUnification:
    """Validate all collectors are consistent."""

    def test_all_collectors_extend_base(self) -> None:
        """All collectors extend EvidenceCollector base class."""
        from runtime.system.evidence.collectors.base import EvidenceCollector
        from runtime.system.evidence.collectors.contract import ContractCollector
        from runtime.system.evidence.collectors.contract_tests import (
            ContractTestCollector,
        )
        from runtime.system.evidence.collectors.coverage import CoverageCollector
        from runtime.system.evidence.collectors.mutation import MutationCollector
        from runtime.system.evidence.collectors.property_tests import (
            PropertyTestCollector,
        )
        from runtime.system.evidence.collectors.test_results import ResultsCollector

        collectors = [
            CoverageCollector,
            MutationCollector,
            ResultsCollector,
            ContractCollector,
            ContractTestCollector,
            PropertyTestCollector,
        ]

        for collector_cls in collectors:
            assert issubclass(
                collector_cls, EvidenceCollector
            ), f"{collector_cls.__name__} does not extend EvidenceCollector"

    def test_all_collectors_have_artifact_type(self) -> None:
        """All collectors have artifact_type property."""
        from runtime.system.evidence.collectors.contract import ContractCollector
        from runtime.system.evidence.collectors.contract_tests import (
            ContractTestCollector,
        )
        from runtime.system.evidence.collectors.coverage import CoverageCollector
        from runtime.system.evidence.collectors.mutation import MutationCollector
        from runtime.system.evidence.collectors.property_tests import (
            PropertyTestCollector,
        )
        from runtime.system.evidence.collectors.test_results import ResultsCollector

        collectors = [
            CoverageCollector,
            MutationCollector,
            ResultsCollector,
            ContractCollector,
            ContractTestCollector,
            PropertyTestCollector,
        ]

        for collector_cls in collectors:
            assert hasattr(
                collector_cls, "artifact_type"
            ), f"{collector_cls.__name__} missing artifact_type"

    def test_artifact_types_are_unique(self) -> None:
        """Each collector has a unique artifact_type."""
        from runtime.system.evidence.collectors.contract import ContractCollector
        from runtime.system.evidence.collectors.contract_tests import (
            ContractTestCollector,
        )
        from runtime.system.evidence.collectors.coverage import CoverageCollector
        from runtime.system.evidence.collectors.mutation import MutationCollector
        from runtime.system.evidence.collectors.property_tests import (
            PropertyTestCollector,
        )
        from runtime.system.evidence.collectors.test_results import ResultsCollector

        collectors = [
            CoverageCollector,
            MutationCollector,
            ResultsCollector,
            ContractCollector,
            ContractTestCollector,
            PropertyTestCollector,
        ]

        types = [c.artifact_type for c in collectors]
        assert len(types) == len(set(types)), f"Duplicate artifact types: {types}"


class TestEvidenceSerialization:
    """Test evidence can be serialized to JSON and back."""

    def test_coverage_evidence_round_trip(self) -> None:
        """CoverageEvidence can be serialized to JSON and dict."""
        import json

        from runtime.system.evidence.models.evidence import CoverageEvidence

        evidence = CoverageEvidence(
            percentage=85.5,
            covered_lines=1000,
            total_lines=1170,
        )
        json_str = evidence.to_json()
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed["percentage"] == 85.5
        assert parsed["covered_lines"] == 1000

    def test_mutation_evidence_round_trip(self) -> None:
        """MutationEvidence can be serialized to JSON and dict."""
        import json

        from runtime.system.evidence.models.evidence import MutationEvidence

        evidence = MutationEvidence(
            score=85.0,
            killed=85,
            survived=15,
        )
        json_str = evidence.to_json()
        parsed = json.loads(json_str)
        assert parsed["score"] == 85.0
        assert parsed["killed"] == 85
        assert parsed["survived"] == 15

    def test_test_result_evidence_round_trip(self) -> None:
        """TestResultEvidence can be serialized to JSON and dict."""
        import json

        from runtime.system.evidence.models.evidence import TestResultEvidence

        evidence = TestResultEvidence(
            passed=100,
            failed=2,
            errors=0,
            skipped=3,
        )
        json_str = evidence.to_json()
        parsed = json.loads(json_str)
        assert parsed["passed"] == 100
        assert parsed["failed"] == 2

    def test_verification_evidence_round_trip(self) -> None:
        """VerificationEvidence can be serialized and deserialized."""
        from runtime.system.evidence.models.evidence import (
            CoverageEvidence,
            VerificationEvidence,
        )

        coverage = CoverageEvidence(
            percentage=90.0, covered_lines=900, total_lines=1000
        )
        evidence = VerificationEvidence(
            commit_sha="abc123",
            branch="main",
            timestamp="2026-09-03T00:00:00Z",
            status="pass",
            coverage=coverage,
        )

        json_str = evidence.to_json()
        recovered = VerificationEvidence.from_json(json_str)

        assert recovered.commit_sha == "abc123"
        assert recovered.branch == "main"
        assert recovered.status == "pass"
        assert recovered.coverage is not None
        assert recovered.coverage.percentage == 90.0


class TestEvidenceAggregation:
    """Test evidence aggregator combines multiple types."""

    def test_aggregator_can_collect(self) -> None:
        """EvidenceAggregator has collect() or aggregate() method."""
        from runtime.system.evidence.aggregator import EvidenceAggregator

        methods = dir(EvidenceAggregator)
        has_method = any(
            name in methods for name in ["collect", "aggregate", "build_report"]
        )
        assert has_method, "EvidenceAggregator should have collect/aggregate method"


class TestEvidencePersistence:
    """Test evidence can be written to disk."""

    def test_verification_evidence_write(self, tmp_path) -> None:
        """VerificationEvidence can be written to a file."""
        from runtime.system.evidence.models.evidence import VerificationEvidence

        evidence = VerificationEvidence(
            commit_sha="test123",
            branch="test-branch",
            timestamp="2026-09-03T00:00:00Z",
            status="pass",
        )
        output_path = tmp_path / "evidence.json"
        evidence.write(output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "test123" in content
        assert "pass" in content

    def test_collection_result_write(self, tmp_path) -> None:
        """EvidenceCollectionResult can be written to a file."""
        from runtime.system.evidence.models.evidence import EvidenceCollectionResult

        result = EvidenceCollectionResult(
            workspace_root="/test/path",
            collected_at="2026-09-03T00:00:00Z",
            artifacts=[],
            collectors={},
        )
        output_path = tmp_path / "collection.json"
        result.write(output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "test/path" in content
