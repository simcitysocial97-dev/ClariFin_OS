"""Loan Simulation Service - Pure what-if scenario calculations.

All methods perform calculations only - no database mutations.
Use LoanRepository for persistence operations.
"""

import time
from typing import Any

from src.engines.loan_engine import (
    apply_floating_rate_change,
    apply_prepayment,
    generate_schedule,
    total_interest_paise,
    validate_schedule,
)
from src.engines.loan_engine.models import PrepaymentMode
from src.repositories.loan_repository import LoanRepository


def _format_schedule_row(row: Any) -> dict[str, Any]:
    """Format an AmortizationRow to the spec-compliant dict format."""
    return {
        "month": row.month_number,
        "date": row.payment_date,
        "emi_paise": row.emi_paise,
        "principal_paise": row.principal_paise,
        "interest_paise": row.interest_paise,
        "balance_paise": row.balance_paise,
    }


class LoanSimulationService:
    """Orchestrates loan simulation workflows.

    All simulations are read-only calculations.
    No database mutations occur in this service.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.loan_repo = LoanRepository(db_path)

    def _load_loan(self, loan_id: int) -> dict[str, Any]:
        """Load loan data and compute rate/tenure."""
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")
        return loan

    def _get_loan_params(self, loan: dict[str, Any]) -> dict[str, Any]:
        """Extract common loan parameters."""
        return {
            "principal_paise": loan["outstanding_paise"],
            "annual_rate_bps": int(loan["interest_rate"] * 100),
            "tenure_months": loan["tenure_months"] or 0,
            "start_date": loan.get("disbursed_date") or "2025-01-01",
        }

    def simulate_prepayment(
        self,
        loan_id: int,
        prepayment_paise: int,
        mode: PrepaymentMode | str = PrepaymentMode.REDUCE_TENURE,
    ) -> dict[str, Any]:
        """
        Simulate prepayment impact on a loan.

        Returns structured result without modifying database.
        Eliminates duplicate schedule generation by generating once and reusing.

        Aligns with spec format: original_interest_paise, new_interest_paise, interest_saved_paise, tenure_saved_months.
        """
        loan = self._load_loan(loan_id)
        params = self._get_loan_params(loan)

        # Convert string mode to PrepaymentMode enum
        prepayment_mode = PrepaymentMode(mode) if isinstance(mode, str) else mode

        # Generate schedule ONCE and pass to apply_prepayment
        original_schedule = generate_schedule(**params)

        # Validate schedule invariants (debug mode for tests)
        validate_schedule(
            original_schedule,
            original_principal_paise=params["principal_paise"],
            original_tenure_months=params["tenure_months"],
            debug_mode=False,
        )

        original_interest = total_interest_paise(original_schedule)

        # Pass pre-generated schedule to avoid duplicate generation
        result = apply_prepayment(
            outstanding_paise=params["principal_paise"],
            annual_rate_bps=params["annual_rate_bps"],
            remaining_months=params["tenure_months"],
            prepayment_paise=prepayment_paise,
            mode=prepayment_mode,
            start_date=params["start_date"],
            existing_schedule=original_schedule,
        )

        # Calculate new total interest from regenerated schedule
        new_interest = 0
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

        loan = self._load_loan(loan_id)
        params = self._get_loan_params(loan)

        result = compute_foreclosure_amount(
            outstanding_paise=params["principal_paise"],
            annual_rate_bps=params["annual_rate_bps"],
            remaining_months=params["tenure_months"],
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
        Generates schedule once and reuses it for the rate change.
        """
        loan = self._load_loan(loan_id)
        params = self._get_loan_params(loan)

        # Generate initial schedule ONCE
        schedule = generate_schedule(**params)

        new_schedule = apply_floating_rate_change(
            schedule,
            change_month,
            new_rate_bps,
            "adjust_emi",
            params["start_date"],
        )

        return {
            "original_rate_bps": params["annual_rate_bps"],
            "new_rate_bps": new_rate_bps,
            "change_month": change_month,
            "new_schedule": [_format_schedule_row(row) for row in new_schedule],
        }

    def simulate_multiple_prepayments(
        self,
        loan_id: int,
        prepayments: list[tuple[int, int]],
        mode: PrepaymentMode | str = PrepaymentMode.REDUCE_TENURE,
    ) -> dict[str, Any]:
        """
        Simulate multiple prepayments on a loan.

        Generates schedule ONCE and applies all prepayments sequentially.
        Avoids O(n²) execution by reusing the schedule.
        """
        from src.engines.loan_engine import apply_multiple_prepayments

        loan = self._load_loan(loan_id)
        params = self._get_loan_params(loan)

        prepayment_mode = PrepaymentMode(mode) if isinstance(mode, str) else mode

        # Generate schedule ONCE
        original_schedule = generate_schedule(**params)
        original_interest = total_interest_paise(original_schedule)

        # Apply all prepayments in sequence
        new_schedule, results = apply_multiple_prepayments(
            original_schedule,
            prepayments,
            params["annual_rate_bps"],
            mode=prepayment_mode,
            start_date=params["start_date"],
        )

        new_interest = total_interest_paise(new_schedule)
        total_months_saved = sum(r.months_saved for r in results)
        total_interest_saved = sum(r.interest_saved_paise for r in results)

        return {
            "original_interest_paise": original_interest,
            "new_interest_paise": new_interest,
            "interest_saved_paise": total_interest_saved,
            "tenure_saved_months": total_months_saved,
            "prepayment_results": [
                {
                    "prepayment_paise": r.prepayment_paise,
                    "months_saved": r.months_saved,
                    "interest_saved_paise": r.interest_saved_paise,
                    "loan_closed": r.loan_closed,
                }
                for r in results
            ],
        }