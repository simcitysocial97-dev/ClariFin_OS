"""Loan Builder - Plain Python builder for loan data."""

from __future__ import annotations

from typing import Any


class LoanBuilder:
    """Build loan data dictionaries for testing."""

    def __init__(self) -> None:
        self._data: dict[str, Any] = {
            "name": "Test Loan",
            "lender": "HDFC",
            "loan_type": "personal",
            "principal_paise": 10000000,
            "outstanding_paise": 10000000,
            "interest_rate": 12.0,  # 1200 bps
            "tenure_months": 60,
            "emi_paise": 25000,
            "disbursed_date": "2025-01-01",
            "is_active": 1,
        }

    def with_principal(self, principal_paise: int) -> LoanBuilder:
        """Set loan principal in paise."""
        self._data["principal_paise"] = principal_paise
        self._data["outstanding_paise"] = principal_paise
        return self

    def with_outstanding(self, outstanding_paise: int) -> LoanBuilder:
        """Set outstanding balance in paise."""
        self._data["outstanding_paise"] = outstanding_paise
        return self

    def with_rate_bps(self, rate_bps: int) -> LoanBuilder:
        """Set interest rate in basis points."""
        self._data["interest_rate"] = rate_bps / 100.0
        return self

    def with_tenure(self, tenure_months: int) -> LoanBuilder:
        """Set loan tenure in months."""
        self._data["tenure_months"] = tenure_months
        return self

    def with_date(self, disbursed_date: str) -> LoanBuilder:
        """Set disbursement date."""
        self._data["disbursed_date"] = disbursed_date
        return self

    def with_type(self, loan_type: str) -> LoanBuilder:
        """Set loan type (personal/home/car/gold)."""
        self._data["loan_type"] = loan_type
        return self

    def build(self) -> dict[str, Any]:
        """Build and return loan dictionary."""
        return dict(self._data)
