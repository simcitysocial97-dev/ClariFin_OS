"""Smoke tests for Forecasting capability."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.builders.irregular_income import load_irregular_income


class TestForecastingCapability:
    """Validate Forecasting capability wiring."""

    def test_import_forecasting_engine(self) -> None:
        """Forecasting engine must be importable."""
        from src.engines import financial_intelligence

        assert financial_intelligence is not None

    def test_golden_dataset_forecasting_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_irregular_income()
        assert "transactions" in data or "accounts" in data
