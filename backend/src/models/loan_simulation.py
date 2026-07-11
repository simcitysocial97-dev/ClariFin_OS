"""
Loan Simulation DTOs - Request/Response models for simulation endpoints.

All monetary values in paise (₹1.00 = 100 paise).
All interest rates in basis points (1% = 100 bps).
"""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.engines.loan_engine.models import PrepaymentMode

# ============================================================
# Prepayment Simulation DTOs
# ============================================================

class PrepaymentSimulationRequest(BaseModel):
    """Prepayment simulation request."""

    amount_paise: int = Field(gt=0, description="Prepayment amount in paise")
    month: int | None = Field(default=1, ge=1, description="Month number for prepayment")
    mode: PrepaymentMode | str = PrepaymentMode.REDUCE_TENURE

    @field_validator("amount_paise")
    @classmethod
    def validate_positive(cls, v: int) -> int:
        """Ensure prepayment amount is positive."""
        if v <= 0:
            raise ValueError("amount_paise must be greater than zero")
        return v

    @field_validator("month")
    @classmethod
    def validate_month(cls, v: int | None) -> int:
        """Ensure month is >= 1 if provided."""
        if v is not None and v < 1:
            raise ValueError("month must be at least 1")
        return v or 1


class PrepaymentSimulationResponse(BaseModel):
    """Prepayment simulation response model matching spec."""

    original_interest_paise: int
    new_interest_paise: int
    interest_saved_paise: int
    tenure_saved_months: int


# ============================================================
# Foreclosure Simulation DTOs
# ============================================================

class ForeclosureSimulationResponse(BaseModel):
    """Foreclosure simulation response model matching spec."""

    outstanding_paise: int
    penalty_paise: int
    foreclosure_amount_paise: int


# ============================================================
# Rate Change Simulation DTOs
# ============================================================

class RateChangeSimulationRequest(BaseModel):
    """Rate change simulation request."""

    month: int = Field(ge=1, description="Month number when rate changes")
    new_rate_bps: int = Field(ge=0, le=5000, description="New annual rate in basis points (0-5000)")

    @field_validator("month")
    @classmethod
    def validate_month_positive(cls, v: int) -> int:
        """Ensure month is at least 1."""
        if v < 1:
            raise ValueError("month must be at least 1")
        return v

    @field_validator("new_rate_bps")
    @classmethod
    def validate_rate_range(cls, v: int) -> int:
        """Ensure rate is within valid range (0-5000 bps = 0-50%)."""
        if v < 0 or v > 5000:
            raise ValueError("new_rate_bps must be between 0 and 5000")
        return v


class RateChangeSimulationResponse(BaseModel):
    """Rate change simulation response model."""

    original_rate_bps: int
    new_rate_bps: int
    change_month: int
    new_schedule: list[dict[str, Any]]


# ============================================================
# Payment Request DTO
# ============================================================

class PaymentRequest(BaseModel):
    """Record payment request model."""

    amount_paise: int = Field(gt=0, description="Payment amount in paise")
    payment_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="ISO 8601 date")
    principal_paise: int | None = None
    interest_paise: int | None = None
    late_fee_paise: int | None = None
    source_account_id: int | None = None

    @field_validator("amount_paise")
    @classmethod
    def validate_amount_positive(cls, v: int) -> int:
        """Ensure payment amount is positive."""
        if v <= 0:
            raise ValueError("amount_paise must be greater than zero")
        return v


class PaymentResponse(BaseModel):
    """Payment response model."""

    success: bool = True
    payment_id: int
