"""Smoke tests for Reconciliation capability."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from tests.golden.datasets.salary_plus_loan import load_salary_plus_loan


class TestReconciliationCapability:
    """Validate Reconciliation capability wiring."""

    def test_import_reconciliation_engine(self) -> None:
        """Reconciliation engine must be importable."""
        from src.engines import reconciliation_engine

        assert reconciliation_engine is not None

    def test_golden_dataset_reconciliation_scenario(self) -> None:
        """Golden dataset must load and validate."""
        data = load_salary_plus_loan()
        assert "transactions" in data or "accounts" in data
