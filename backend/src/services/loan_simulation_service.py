"""Loan Simulation Service - Pure what-if scenario calculations.

All methods perform calculations only - no database mutations.
Use LoanRepository for persistence operations.
"""

from typing import Any

from src.engines.loan_engine import (
    apply_floating_rate_change,
    apply_multiple_prepayments,
    apply_prepayment,
    compute_foreclosure_amount,
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
        """
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        # Convert string mode to PrepaymentMode enum
        prepayment_mode = PrepaymentMode(mode) if isinstance(mode, str) else mode

        result = apply_prepayment(
            outstanding_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_paise=prepayment_paise,
            mode=prepayment_mode,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        return {
            "original_emi_paise": result.original_emi_paise,
            "new_emi_paise": result.new_emi_paise,
            "original_remaining_months": result.original_remaining_months,
            "new_remaining_months": result.new_remaining_months,
            "interest_saved_paise": result.interest_saved_paise,
            "tenure_saved_months": result.months_saved,
            "new_schedule": [row.model_dump() for row in (result.new_schedule or [])],
        }

    def simulate_multiple_prepayments(
        self,
        loan_id: int,
        prepayments: list[tuple[int, int]],  # (month, amount_paise)
    ) -> dict[str, Any]:
        """
        Simulate multiple prepayments on a loan.

        Args:
            loan_id: Loan to simulate
            prepayments: List of (month_number, amount_paise) tuples

        Returns:
            Simulation result without database mutation
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

        # Apply prepayments
        result_schedule, results = apply_multiple_prepayments(
            schedule,
            prepayments,
            rate_bps,
        )

        # Get total savings from all prepayments
        total_interest_saved = sum(r.interest_saved_paise for r in results)
        total_months_saved = sum(r.months_saved for r in results)
        final_emi = results[-1].new_emi_paise if results else (loan.get("emi_paise") or 0)

        return {
            "original_emi_paise": loan.get("emi_paise") or 0,
            "new_emi_paise": final_emi,
            "original_remaining_months": remaining_months,
            "new_remaining_months": remaining_months - total_months_saved,
            "interest_saved_paise": total_interest_saved,
            "tenure_saved_months": total_months_saved,
            "new_schedule": [row.model_dump() for row in result_schedule],
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
            "accrued_interest_paise": result.accrued_interest_paise,
            "penalty_paise": result.penalty_paise,
            "foreclosure_amount_paise": result.foreclosure_amount_paise,
            "remaining_months_saved": result.remaining_months_saved,
        }

    def simulate_rate_change(
        self,
        loan_id: int,
        change_month: int,
        new_rate_bps: int,
        mode: str = "adjust_emi",
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
            "adjust_emi" if mode == "adjust_emi" else "adjust_tenure",
            loan.get("disbursed_date") or "2025-01-01",
        )

        return {
            "original_rate_bps": rate_bps,
            "new_rate_bps": new_rate_bps,
            "change_month": change_month,
            "new_schedule": [row.model_dump() for row in new_schedule],
        }
