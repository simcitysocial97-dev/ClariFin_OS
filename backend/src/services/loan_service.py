"""Loan Service - Orchestration layer for loan operations.

Coordinates repositories and loan_engine to implement business logic.
No direct database access - uses repositories only.
"""

from typing import Any

from src.engines.loan_engine import (
    apply_prepayment,
    generate_schedule,
)
from src.engines.loan_engine.models import PrepaymentResult
from src.models.loan_payment import LoanPaymentCreate
from src.repositories.loan_payment_repository import LoanPaymentRepository
from src.repositories.loan_repository import LoanRepository


class LoanService:
    """Orchestrates loan calculation and persistence logic.

    Delegates calculations to loan_engine (pure functions).
    Delegates persistence to repositories.
    """

    def __init__(self) -> None:
        self.loan_repo = LoanRepository()
        self.payment_repo = LoanPaymentRepository()

    def get_amortization_schedule(self, loan_id: int) -> dict[str, Any]:
        """Get full amortization schedule for a loan."""
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        # Convert rate to basis points if needed
        rate_bps = int(loan["interest_rate"] * 100) if "interest_rate_bps" not in loan else loan["interest_rate_bps"]

        schedule = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=loan["tenure_months"],
            start_date=loan["disbursed_date"],
        )

        return {
            "loan_id": loan_id,
            "schedule": [row.model_dump() for row in schedule],
            "total_payments": len(schedule),
            "total_interest_paise": sum(row.interest_paise for row in schedule),
            "total_payment_paise": sum(row.emi_paise for row in schedule),
        }

    def simulate_prepayment(
        self,
        loan_id: int,
        prepayment_paise: int,
        mode: str = "reduce_tenure",
    ) -> PrepaymentResult:
        """Simulate prepayment impact on a loan."""
        from src.engines.loan_engine.models import PrepaymentMode

        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        # Convert string mode to PrepaymentMode enum
        prepayment_mode = PrepaymentMode(mode) if isinstance(mode, str) else mode

        return apply_prepayment(
            outstanding_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_paise=prepayment_paise,
            mode=prepayment_mode,
            start_date=loan.get("disbursed_date"),
        )

    def record_payment(self, payment: LoanPaymentCreate) -> int:
        """Record a loan payment."""
        return self.payment_repo.create_payment(payment)
