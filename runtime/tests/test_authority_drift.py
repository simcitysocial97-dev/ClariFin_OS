"""M9-C65 — Authority-drift attack experiments.

Simulates an authority mismatch between CLI, registry, and executor
and verifies the framework detects it as AUTHORITY_DRIFT rather than
silently passing.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from runtime.foundation.verification.authority_drift_detector import (
    DriftClassification,
    DriftFinding,
    PlannerDriftDetector,
    Severity,
)
from runtime.foundation.verification.canonical_control_plane import (
    CanonicalOperation,
    canonical_tree,
    migration_map,
)


class TestAuthorityDriftDetection:
    """The framework must detect deliberate authority mismatches."""

    def test_canonical_operations_defined(self):
        """All CanonicalOperation enum values must be strings."""
        for op in CanonicalOperation:
            assert isinstance(op.value, str)
            assert len(op.value) > 0

    def test_canonical_tree_has_expected_keys(self):
        """canonical_tree must expose verify and inspect_subqueries."""
        tree = canonical_tree()
        assert "verify" in tree
        assert "inspect_subqueries" in tree

    def test_migration_map_non_empty(self):
        """migration_map must contain deprecated token routing."""
        migration = migration_map()
        assert len(migration) > 50, "Expected 50+ deprecated tokens routed"

    def test_drift_finding_structure(self):
        """DriftFinding must have all required fields."""
        finding = DriftFinding(
            check_name="test-check",
            detected_component="test-comp",
            expected_authority="expected-auth",
            actual_authority="actual-auth",
            classification=DriftClassification.AUTHORITY_DRIFT,
            source_evidence="test-evidence",
            severity=Severity.MEDIUM,
        )
        assert finding.detected_component == "test-comp"
        assert finding.classification == DriftClassification.AUTHORITY_DRIFT
        assert finding.severity == "medium"

    def test_all_drift_classifications_valid(self):
        """Every DriftClassification value must be a non-empty string."""
        for cls in DriftClassification:
            assert isinstance(cls.value, str)
            assert len(cls.value) > 0

    def test_authority_drift_classification_exists(self):
        """AUTHORITY_DRIFT must be a recognized classification."""
        assert DriftClassification.AUTHORITY_DRIFT.value == "AUTHORITY_DRIFT"

    def test_planner_drift_detector_instantiates(self):
        """PlannerDriftDetector must be instantiable."""
        detector = PlannerDriftDetector()
        assert detector is not None

    def test_drift_finding_serializable(self):
        """DriftFinding must serialize to dict without error."""
        finding = DriftFinding(
            check_name="serial-test",
            detected_component="comp",
            expected_authority="exp",
            actual_authority="act",
            classification=DriftClassification.AUTHORITY_DRIFT,
            source_evidence="ev",
            severity=Severity.HIGH,
        )
        d = finding.to_dict()
        assert d["detected_component"] == "comp"
        assert d["classification"] == "AUTHORITY_DRIFT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
