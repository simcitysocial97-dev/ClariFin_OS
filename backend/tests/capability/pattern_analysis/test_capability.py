"""Smoke tests for Pattern Analysis capability."""

from __future__ import annotations



from tests.golden.builders.irregular_income import load_irregular_income


class TestPatternAnalysisCapability:
    """Validate Pattern Analysis capability wiring."""

    def test_import_pattern_engine(self) -> None:
        """Pattern engine must be importable."""
        from src.engines import insight_generator

        assert insight_generator is not None

    def test_golden_dataset_pattern_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_irregular_income()
        assert "transactions" in data or "accounts" in data