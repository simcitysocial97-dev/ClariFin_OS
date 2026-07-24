"""Smoke tests for Transaction Intelligence capability."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.datasets.normal_household import load_normal_household


class TestTransactionIntelligenceCapability:
    """Validate Transaction Intelligence capability wiring."""

    def test_import_transaction_intelligence_engine(self) -> None:
        """Transaction intelligence engine must be importable."""
        from src.engines import transaction_intelligence

        assert transaction_intelligence is not None

    def test_golden_dataset_transaction_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_normal_household()
        assert "transactions" in data
