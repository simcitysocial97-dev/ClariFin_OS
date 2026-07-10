"""Loan Service - Orchestration layer for loan operations."""

from datetime import date
from typing import Any

from src.engines.loan_engine import (
    apply_prepayment,
    compute_health_score,
    evaluate_refinance,
    generate_schedule,
)
from src.engines.loan_engine.types import (
    PrepaymentResult,
    RefinanceInput,
    RefinanceResult,
)
from src.models.loan_payment import LoanPaymentCreate
from src.models.loan_scenario import LoanScenarioCreate
from src.repositories.loan_payment_repository import LoanPaymentRepository
from src.repositories.loan_repository import LoanRepository
from src.repositories.loan_scenario_repository import LoanScenarioRepository


class LoanService:
    """Orchestrates loan calculation and persistence logic."""

    def __init__(self) -> None:
        self.loan_repo = LoanRepository()
        self.payment_repo = LoanPaymentRepository()
        self.scenario_repo = LoanScenarioRepository()

    def get_amortization_schedule(self, loan_id: int) -> dict[str, Any]:
        """Get full amortization schedule for a loan."""
        loan = self.loan_repo.get_by_id(loan_id)
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
        loan = self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0

        return apply_prepayment(
            outstanding_paise=loan["outstanding_paise"],
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_paise=prepayment_paise,
            mode=mode,
            start_date=loan.get("disbursed_date"),
        )

    def evaluate_refinance(
        self,
        loan_id: int,
        new_rate_bps: int,
        new_tenure_months: int,
        processing_fees_paise: int = 0,
    ) -> RefinanceResult:
        """Evaluate refinance opportunity for a loan."""
        loan = self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        current_rate_bps = int(loan["interest_rate"] * 100)

        input_data = RefinanceInput(
            current_outstanding_paise=loan["outstanding_paise"],
            current_rate_bps=current_rate_bps,
            remaining_months=loan["tenure_months"] or 0,
            current_emi_paise=loan["emi_paise"],
            new_rate_bps=new_rate_bps,
            new_tenure_months=new_tenure_months,
            processing_fees_paise=processing_fees_paise,
        )

        return evaluate_refinance(input_data)

    def compute_health_score(self, loan_id: int) -> float:
        """Compute health score for a loan."""
        loan = self.loan_repo.get_by_id(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        # Get payment history for stress score
        payments = self.payment_repo.get_by_loan_id(loan_id)
        total_payments = len(payments)
        missed_payments = sum(1 for p in payments if p.late_fee_paise > 0)

        # Compute months since start
        months_since_start = date.today().year * 12 + date.today().month - date.fromisoformat(loan["disbursed_date"]).year * 12 - date.fromisoformat(loan["disbursed_date"]).month

        result = compute_health_score(
            monthly_emi_paise=loan["emi_paise"],
            monthly_income_paise=5000000,  # ₹50,000 default - should come from user profile
            sanction_amount_paise=loan["principal_paise"],
            outstanding_paise=loan["outstanding_paise"],
            missed_payments=missed_payments,
            total_payments=max(total_payments, 1),
            months_since_start=max(months_since_start, 0),
        )

        return result.overall_score

    def record_payment(self, payment: LoanPaymentCreate) -> int:
        """Record a loan payment."""
        return self.payment_repo.create(payment)

    def save_scenario(
        self,
        loan_id: int,
        scenario_name: str,
        prepayment_paise: int,
        result: PrepaymentResult,
    ) -> int:
        """Save a prepayment scenario for future reference."""
        scenario = LoanScenarioCreate(
            loan_id=loan_id,
            scenario_name=scenario_name,
            prepayment_paise=prepayment_paise,
            new_tenure_months=result.new_remaining_months,
            new_emi_paise=result.new_emi_paise,
            interest_saved_paise=result.interest_saved_paise,
            months_saved=result.months_saved,
        )
        return self.scenario_repo.create(scenario)
