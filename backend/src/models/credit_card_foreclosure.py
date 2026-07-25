"""Credit Card Foreclosure domain models."""

from pydantic import BaseModel, Field


class ForeclosureRequest(BaseModel):
    """Request to compute foreclosure payoff."""

    remaining_months: int = Field(ge=1, le=120, description="Remaining EMI months")
    penalty_bps: int = Field(
        default=0, ge=0, le=5000, description="Prepayment penalty in basis points"
    )


class ForeclosureResponse(BaseModel):
    """Foreclosure payoff response."""

    foreclosure_amount_paise: int
    outstanding_paise: int
    accrued_interest_paise: int
    penalty_paise: int
