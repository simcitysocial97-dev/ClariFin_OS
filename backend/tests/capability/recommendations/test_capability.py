"""Smoke tests for Recommendations capability."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.builders.high_debt_household import load_high_debt_household


class TestRecommendationsCapability:
    """Validate Recommendations capability wiring."""

    def test_import_recommendation_engine(self) -> None:
        """Recommendation engine must be importable."""
        from src.engines import recommendation_engine

        assert recommendation_engine is not None

    def test_golden_dataset_recommendation_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_high_debt_household()
        assert "transactions" in data or "accounts" in data
