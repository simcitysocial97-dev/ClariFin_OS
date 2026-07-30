"""Loan Analysis Service - Personal loan optimization recommendations.

Pure business logic for loan management decisions.
No database mutations - recommendations only.
"""

from src.engines.loan_engine import apply_prepayment, compute_foreclosure_amount
from src.engines.loan_engine.models import PrepaymentMode
from src.models.loan_analysis import LoanRecommendation, SurplusAllocationResult
from src.repositories.loan_repository import LoanRepository


class LoanAnalysisService:
    """Provides loan management recommendations."""

    def __init__(self, db_path: str | None = None) -> None:
        self.loan_repo = LoanRepository(db_path)

    def analyze_loan_priority(self) -> list[LoanRecommendation]:
        """
        Rank active loans by priority for prepayment.

        Returns recommendations sorted by highest interest savings first.
        """
        loans = self.loan_repo.list_loans()

        recommendations: list[LoanRecommendation] = []

        for loan in loans:
            rate_bps = int(loan["interest_rate"] * 100)
            remaining_months = loan["tenure_months"] or 0
            outstanding = loan["outstanding_paise"]

            # Simulate a standard prepayment (10% of outstanding or ₹100,000)
            prepayment_paise = min(outstanding // 10, 100000)

            if outstanding > 0 and remaining_months > 0:
                result = apply_prepayment(
                    outstanding_paise=outstanding,
                    annual_rate_bps=rate_bps,
                    remaining_months=remaining_months,
                    prepayment_paise=prepayment_paise,
                    mode=PrepaymentMode.REDUCE_TENURE,
                    start_date=loan.get("disbursed_date") or "2025-01-01",
                )

                recommendations.append(
                    LoanRecommendation(
                        loan_id=int(loan["id"]),
                        action="PREPAY",
                        reason=f"Highest interest rate ({loan['interest_rate']}%) saves ₹{result.interest_saved_paise / 100:.0f}",
                        interest_saved_paise=result.interest_saved_paise,
                        tenure_saved_months=result.months_saved,
                    )
                )

        # Sort by interest saved (highest first), then by interest rate
        recommendations.sort(
            key=lambda r: (-r.interest_saved_paise, -r.tenure_saved_months)
        )

        return recommendations

    def analyze_prepayment_vs_foreclosure(
        self,
        loan_id: int,
        available_surplus_paise: int,
    ) -> LoanRecommendation:
        """
        Compare prepayment vs foreclosure for a loan.

        Returns recommendation with financial benefit analysis.
        """
        loan = self.loan_repo.get_loan(loan_id)
        if not loan:
            raise ValueError(f"Loan {loan_id} not found")

        rate_bps = int(loan["interest_rate"] * 100)
        remaining_months = loan["tenure_months"] or 0
        outstanding = loan["outstanding_paise"]

        foreclosure = compute_foreclosure_amount(
            outstanding_paise=outstanding,
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_penalty_bps=0,
        )

        # Calculate prepayment benefit
        prepayment_result = apply_prepayment(
            outstanding_paise=outstanding,
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            prepayment_paise=min(available_surplus_paise, outstanding),
            mode=PrepaymentMode.REDUCE_TENURE,
            start_date=loan.get("disbursed_date") or "2025-01-01",
        )

        # Compare: foreclosure penalty vs interest saved
        # If surplus covers foreclosure, recommend foreclosure
        if available_surplus_paise >= foreclosure.foreclosure_amount_paise:
            return LoanRecommendation(
                loan_id=loan_id,
                action="FORECLOSE",
                reason=f"Surplus covers foreclosure amount (saves {remaining_months} months)",
                interest_saved_paise=foreclosure.accrued_interest_paise,
                tenure_saved_months=remaining_months,
            )

        # Otherwise recommend prepayment
        action = "PREPAY" if prepayment_result.interest_saved_paise > 0 else "NONE"
        return LoanRecommendation(
            loan_id=loan_id,
            action=action,
            reason=f"Prepayment saves ₹{prepayment_result.interest_saved_paise / 100:.0f}",
            interest_saved_paise=prepayment_result.interest_saved_paise,
            tenure_saved_months=prepayment_result.months_saved,
        )

    def analyze_surplus_allocation(
        self,
        available_surplus_paise: int,
    ) -> SurplusAllocationResult:
        """
        Analyze optimal allocation of surplus across all active loans.

        Returns ranked recommendations based on interest savings.
        """
        loans = self.loan_repo.list_loans()

        if available_surplus_paise <= 0:
            return SurplusAllocationResult(
                surplus_paise=available_surplus_paise,
                recommendations=[
                    LoanRecommendation(
                        loan_id=int(loan["id"]),
                        action="NONE",
                        reason="No surplus available",
                    )
                    for loan in loans
                ],
                total_interest_saved_paise=0,
            )

        recommendations: list[LoanRecommendation] = []
        remaining_surplus = available_surplus_paise

        for loan in loans:
            if remaining_surplus <= 0:
                break

            outstanding = loan["outstanding_paise"]
            if outstanding <= 0:
                continue

            # Allocate surplus to this loan
            allocation = min(remaining_surplus, outstanding)
            rate_bps = int(loan["interest_rate"] * 100)
            remaining_months = loan["tenure_months"] or 0

            if allocation > 0 and remaining_months > 0:
                result = apply_prepayment(
                    outstanding_paise=outstanding,
                    annual_rate_bps=rate_bps,
                    remaining_months=remaining_months,
                    prepayment_paise=allocation,
                    mode=PrepaymentMode.REDUCE_TENURE,
                    start_date=loan.get("disbursed_date") or "2025-01-01",
                )

                recommendations.append(
                    LoanRecommendation(
                        loan_id=int(loan["id"]),
                        action="PREPAY",
                        reason=f"Allocate ₹{allocation / 100:.0f} to {loan['name']} (rate: {loan['interest_rate']}%)",
                        interest_saved_paise=result.interest_saved_paise,
                        tenure_saved_months=result.months_saved,
                    )
                )

                remaining_surplus -= allocation

        total_saved = sum(r.interest_saved_paise for r in recommendations)

        return SurplusAllocationResult(
            surplus_paise=available_surplus_paise,
            recommendations=recommendations,
            total_interest_saved_paise=total_saved,
        )
