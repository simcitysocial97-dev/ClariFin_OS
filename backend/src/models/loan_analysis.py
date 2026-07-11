"""Service DTOs for loan analysis responses.

All monetary values in paise (₹1.00 = 100 paise).
All interest rates in basis points.
"""

from pydantic import BaseModel


class LoanRecommendation(BaseModel):
    """Recommendation for a specific loan action."""

    loan_id: int
    action: str  # PREPAY | FORECLOSE | NONE
    reason: str
    interest_saved_paise: int = 0
    tenure_saved_months: int = 0


class SurplusAllocationResult(BaseModel):
    """Result of surplus allocation analysis."""

    surplus_paise: int
    recommendations: list[LoanRecommendation]
    total_interest_saved_paise: int
