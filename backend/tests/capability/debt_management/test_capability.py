"""Smoke tests for Debt Management capability."""

from __future__ import annotations



from tests.golden.builders.salary_plus_loan import load_salary_plus_loan


class TestDebtManagementCapability:
    """Validate Debt Management capability wiring and invariants."""

    def test_import_loan_engine(self) -> None:
        """Loan engine must be importable."""
        from src.engines import loan_engine

        assert loan_engine is not None

    def test_golden_dataset_loan_scenario(self) -> None:
        """Golden dataset with loan must load and validate."""
        data = load_salary_plus_loan()
        assert "transactions" in data or "accounts" in data