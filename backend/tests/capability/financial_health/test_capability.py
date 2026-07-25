"""Smoke tests for Financial Health capability."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.builders.normal_household import load_normal_household


class TestFinancialHealthCapability:
    """Validate Financial Health capability wiring."""

    def test_import_behaviour_engine(self) -> None:
        """Behaviour engine must be importable."""
        from src.engines import behaviour_engine

        assert behaviour_engine is not None

    def test_golden_dataset_behaviour_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_normal_household()
        assert "transactions" in data or "accounts" in data
