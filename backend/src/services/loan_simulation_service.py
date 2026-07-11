"""Loan Simulation Service - Pure what-if scenario calculations.

All methods perform calculations only - no database mutations.
Use LoanRepository for persistence operations.
"""

from typing import Any

from src.engines.loan_engine import (
    apply_floating_rate_change,
    generate_schedule,
)
from src.engines.loan_engine.models import PrepaymentMode
from src.repositories.loan_repository import LoanRepository


class LoanSimulationService:
    """Orchestrates loan simulation workflows.

    All simulations are read-only calculations.
    No database mutations occur in this service.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.loan_repo = LoanRepository(db_path)

    def simulate_prepayment(
        self,
        loan_id: int,
        prepayment_paise: int,
        mode: PrepaymentMode | str = PrepaymentMode.REDUCE_TENURE,
    ) -> dict[str, Any]:
        """
        Simulate prepayment impact on a loan.

        Returns structured result without modifying database.
        Aligns with spec format: original_interest_paise, new_interest_paise, interest_saved_paise, tenure_saved_months.
        """
        from src.engines.loan_engine import apply_prepayment, total_interest_paise

        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        # Convert string mode to PrepaymentMode enum
        prepayment_mode = PrepaymentMode(mode) if isinstance(mode, str) else mode

        # Calculate original interest for the full tenure
        original_schedule = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=remaining_months,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )
        original_interest = total_interest_paise(original_schedule)

        result = apply_prepayment(
            outstanding_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_paise=prepayment_paise,
            mode=prepayment_mode,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        # Calculate new total interest from regenerated schedule
        new_interest = original_interest - result.interest_saved_paise
        if result.new_schedule:
            new_interest = result.new_schedule[-1].cumulative_interest_paise if result.new_schedule else 0

        return {
            "original_interest_paise": original_interest,
            "new_interest_paise": new_interest,
            "interest_saved_paise": result.interest_saved_paise,
            "tenure_saved_months": result.months_saved,
        }

    def simulate_foreclosure(
        self,
        loan_id: int,
        prepayment_penalty_bps: int = 0,
    ) -> dict[str, Any]:
        """
        Simulate foreclosure impact on a loan.

        Returns breakdown of foreclosure costs without mutating database.
        """
        from src.engines.loan_engine import compute_foreclosure_amount

        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        result = compute_foreclosure_amount(
            outstanding_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_penalty_bps=prepayment_penalty_bps,
        )

        return {
            "outstanding_paise": result.outstanding_paise,
            "penalty_paise": result.penalty_paise,
            "foreclosure_amount_paise": result.foreclosure_amount_paise,
        }

    def simulate_rate_change(
        self,
        loan_id: int,
        change_month: int,
        new_rate_bps: int,
    ) -> dict[str, Any]:
        """
        Simulate floating rate change impact on a loan.

        Returns regenerated schedule without modifying database.
        """
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        # Generate initial schedule
        schedule = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=remaining_months,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        new_schedule = apply_floating_rate_change(
            schedule,
            change_month,
            new_rate_bps,
            "adjust_emi",
            loan.get("disbursed_date") or "2025-01-01",
        )

        return {
            "original_rate_bps": rate_bps,
            "new_rate_bps": new_rate_bps,
            "change_month": change_month,
            "new_schedule": [
                {
                    "month": row.month_number,
                    "date": row.payment_date,
                    "emi_paise": row.emi_paise,
                    "principal_paise": row.principal_paise,
                    "interest_paise": row.interest_paise,
                    "balance_paise": row.balance_paise,
                }
                for row in new_schedule
            ],
        }
