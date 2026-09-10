"""M9-C55 — Configuration Consistency Tests.

Verifies verification.yaml loads correctly and thresholds are accessible.
"""
from __future__ import annotations

from pathlib import Path

import pytest


class TestConfigConsistency:
    """Test verification configuration integrity."""

    def test_verification_yaml_loads(self):
        """verification.yaml must be valid YAML and loadable."""
        config_file = Path("runtime/foundation/verification/verification.yaml")
        assert config_file.exists(), "verification.yaml not found"

        try:
            import yaml  # noqa
        except ImportError:
            pytest.skip("PyYAML not installed")

        with open(config_file) as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert "workflows" in config
        assert "backend" in config
        assert "frontend" in config

    def test_config_loader_reads_thresholds(self):
        """ConfigLoader must read threshold values with fallback defaults."""
        from runtime.foundation.verification.config_loader import get_threshold

        # Mutation thresholds
        mutation_full = get_threshold("mutation_thresholds", "full_campaign", 80)
        assert isinstance(mutation_full, (int, float))

        # Regression thresholds
        coverage_drop_warn = get_threshold("regression_thresholds", "coverage_drop_warning", 5)
        assert isinstance(coverage_drop_warn, (int, float))

    def test_thresholds_have_reasonable_values(self):
        """Loaded thresholds must be within sane bounds."""
        from runtime.foundation.verification.config_loader import get_threshold

        mutation_score = get_threshold("mutation_thresholds", "full_campaign", 80)
        assert 0 <= mutation_score <= 100, f"Mutation threshold out of range: {mutation_score}"

        coverage_drop = get_threshold("regression_thresholds", "coverage_drop_warning", 5)
        assert 0 < coverage_drop <= 50, f"Coverage drop threshold out of range: {coverage_drop}"
