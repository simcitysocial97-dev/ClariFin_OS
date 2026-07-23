"""Smoke tests for Pattern Analysis capability."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.datasets.irregular_income import load_irregular_income


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
