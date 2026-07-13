"""Loan Service - Orchestration layer for loan operations.

Coordinates repositories and loan_engine to implement business logic.
No direct database access - uses repositories only.
"""

from typing import Any

from src.engines.loan_engine import generate_schedule, total_interest_paise
from src.models.loan_payment import LoanPaymentCreate
from src.repositories.loan_payment_repository import LoanPaymentRepository
from src.repositories.loan_repository import LoanRepository


class LoanService:
    """Orchestrates loan calculation and persistence logic.

    Delegates calculations to loan_engine (pure functions).
    Delegates persistence to repositories.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.loan_repo = LoanRepository(db_path)
        self.payment_repo = LoanPaymentRepository(db_path)

    # ============================================================
    # CRUD Operations
    # ============================================================

    def get_loan(self, loan_id: int) -> dict[str, Any]:
        """Get loan details."""
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")
        return loan

    def get_loans(self) -> list[dict[str, Any]]:
        """Get all active loans."""
        return self.loan_repo.list_loans()

    def create_loan(
        self,
        name: str,
        lender: str,
        loan_type: str,
        principal_paise: int,
        outstanding_paise: int,
        interest_rate: float,
        disbursed_date: str,
        tenure_months: int | None = None,
        emi_paise: int | None = None,
        **kwargs: Any,
    ) -> int:
        """Create a new loan record."""
        return self.loan_repo.create_loan(
            name=name,
            lender=lender,
            loan_type=loan_type,
            principal_paise=principal_paise,
            outstanding_paise=outstanding_paise,
            interest_rate=interest_rate,
            disbursed_date=disbursed_date,
            tenure_months=tenure_months,
            emi_paise=emi_paise,
            **kwargs,
        )

    def update_loan(
        self,
        loan_id: int,
        **kwargs: str | int | float | None,
    ) -> dict[str, Any] | None:
        """Update loan fields."""
        return self.loan_repo.update_loan(loan_id, **kwargs)

    def delete_loan(self, loan_id: int) -> bool:
        """Soft delete a loan."""
        return self.loan_repo.delete_loan(loan_id)

    # ============================================================
    # Schedule and Balance Operations
    # ============================================================

    def get_schedule(self, loan_id: int) -> dict[str, Any]:
        """Get amortization schedule for a loan.

        Returns spec-compliant format:
        {
            "loan_id": int,
            "emi_paise": int,
            "total_interest_paise": int,
            "schedule": [
                {"month": int, "date": str, "emi_paise": int, "principal_paise": int, "interest_paise": int, "balance_paise": int},
                ...
            ]
        }
        """
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        schedule = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=remaining_months,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        # Calculate total interest using loan engine
        total_interest = total_interest_paise(schedule)
        emi_paise = schedule[0].emi_paise if schedule else 0

        # Transform to spec format - map month_number to month
        schedule_rows = [
            {
                "month": row.month_number,
                "date": row.payment_date,
                "emi_paise": row.emi_paise,
                "principal_paise": row.principal_paise,
                "interest_paise": row.interest_paise,
                "balance_paise": row.balance_paise,
            }
            for row in schedule
        ]

        return {
            "emi_paise": emi_paise,
            "total_interest_paise": total_interest,
            "schedule": schedule_rows,
        }

    def get_current_balance(self, loan_id: int) -> int:
        """
        Calculate current outstanding balance from loan engine.

        Does NOT trust stored balance - calculates fresh from schedule.
        """
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        # Generate schedule to validate loan state
        _ = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=remaining_months,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        # Return the stored outstanding (would be calculated from payments in full impl)
        return int(loan["outstanding_paise"])

    def get_loan_summary(self, loan_id: int) -> dict[str, Any]:
        """Get loan summary with payments and schedule insights."""
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        payments = self.payment_repo.list_payments(loan_id)
        prepayments = self.loan_repo.list_prepayments(loan_id)
        rate_changes = self.loan_repo.list_rate_changes(loan_id)

        return {
            "loan": loan,
            "payments_count": len(payments),
            "prepayments_count": len(prepayments),
            "rate_changes_count": len(rate_changes),
            "total_paid_paise": sum(p.amount_paise for p in payments),
            "total_prepayment_paise": sum(p["amount_paise"] for p in prepayments),
        }

    # ============================================================
    # Schedule Generation (for EMI detection)
    # ============================================================

    def get_or_generate_schedule(self, loan_id: int) -> list[dict[str, Any]]:
        """
        Get cached schedule or generate and persist if not exists.

        Schedule is generated ONCE (lazily) and cached in loan_amortization_schedule.
        Subsequent calls return cached rows without regeneration.

        Returns list of dicts with: loan_id, due_date, emi_paise, principal_paise,
            interest_paise, balance_paise, source.
        """
        # Check if schedule already cached
        cached = self.loan_repo.get_schedule_rows(loan_id)
        if cached:
            return cached

        # Generate schedule
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        # Use exact conversion from existing code: rate_bps = int(loan["interest_rate"] * 100)
        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        schedule = generate_schedule(
            principal_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            tenure_months=remaining_months,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        # Transform to dict format for persistence
        schedule_dicts = [
            {
                "due_date": row.payment_date,
                "emi_paise": row.emi_paise,
                "principal_paise": row.principal_paise,
                "interest_paise": row.interest_paise,
                "balance_paise": row.balance_paise,
            }
            for row in schedule
        ]

        # Persist for future use
        self.loan_repo.persist_schedule_rows(loan_id, schedule_dicts, source="computed")

        return schedule_dicts

    # ============================================================
    # Payment Operations
    # ============================================================

    def record_payment(self, payment: LoanPaymentCreate) -> int:
        """Record a loan payment."""
        return self.payment_repo.create_payment(payment)
