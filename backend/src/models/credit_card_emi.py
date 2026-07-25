"""Credit Card EMI Conversion domain models."""

from pydantic import BaseModel, Field


class EmiConversionRequest(BaseModel):
    """Request to convert a purchase to EMI."""

    amount_paise: int = Field(gt=0, description="Amount to convert in paise")
    tenure_months: int = Field(ge=3, le=24, description="EMI tenure in months (3-24)")
    annual_rate_bps: int | None = Field(
        default=None,
        ge=0,
        le=5000,
        description="Override annual rate in basis points. Uses card rate if not provided.",
    )


class EmiConversionResponse(BaseModel):
    """EMI conversion response."""

    emi_paise: int
    total_interest_paise: int
    total_repayment_paise: int
    monthly_interest_paise: int
