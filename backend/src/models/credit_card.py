"""Credit Card domain models for credit card engine."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from src.models.base import DomainModel


class CreditCard(DomainModel):
    """Credit Card domain entity."""

    id: str
    account_id: str
    name: str
    bank: str
    card_last4: str | None = None
    credit_limit_paise: int
    annual_fee_paise: int = 0
    interest_rate_bps: int
    billing_day: int | None = None
    due_day_offset: int = 21
    is_active: bool = True
    notes: str | None = None

    @field_validator("credit_limit_paise", "annual_fee_paise")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @field_validator("interest_rate_bps")
    @classmethod
    def validate_rate_bps(cls, v: int) -> int:
        """Ensure rate is in valid range (0-5000 = 0-50%)."""
        if v < 0 or v > 5000:
            raise ValueError("interest_rate_bps must be between 0 and 5000")
        return v

    @field_validator("billing_day")
    @classmethod
    def validate_billing_day(cls, v: int | None) -> int | None:
        """Ensure billing day is in valid range (1-31)."""
        if v is not None and (v < 1 or v > 31):
            raise ValueError("billing_day must be between 1 and 31")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "CreditCard":
        """Create CreditCard from database row."""
        return cls(
            id=row["id"],
            account_id=row["account_id"],
            name=row["name"],
            bank=row["bank"],
            card_last4=row.get("card_last4"),
            credit_limit_paise=row["credit_limit_paise"],
            annual_fee_paise=row.get("annual_fee_paise", 0),
            interest_rate_bps=row["interest_rate_bps"],
            billing_day=row.get("billing_day"),
            due_day_offset=row.get("due_day_offset", 21),
            is_active=bool(row.get("is_active", 1)),
            notes=row.get("notes"),
        )


# ============================================================
# Request/Response DTOs
# ============================================================

VALID_BANKS = {
    "hdfc",
    "icici",
    "sbi",
    "axis",
    "kotak",
    "yes",
    "indusind",
    "amex",
    "citi",
    "standard_chartered",
    "hsbc",
    "other",
}


class CreditCardCreateRequest(BaseModel):
    """Credit card creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    account_id: str
    bank: str
    card_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    credit_limit_paise: int = Field(gt=0, description="Credit limit in paise")
    annual_fee_paise: int = Field(default=0, ge=0)
    interest_rate_bps: int = Field(
        ge=0, le=5000, description="Annual rate in basis points"
    )
    billing_day: int | None = Field(default=None, ge=1, le=31)
    due_day_offset: int = Field(default=21, ge=1, le=60)
    notes: str | None = None

    @field_validator("bank")
    @classmethod
    def validate_bank(cls, v: str) -> str:
        """Ensure bank is valid."""
        if v.lower() not in VALID_BANKS:
            raise ValueError(f"bank must be one of: {', '.join(sorted(VALID_BANKS))}")
        return v.lower()


class CreditCardUpdateRequest(BaseModel):
    """Credit card update request."""

    name: str | None = None
    credit_limit_paise: int | None = Field(default=None, gt=0)
    annual_fee_paise: int | None = Field(default=None, ge=0)
    interest_rate_bps: int | None = Field(default=None, ge=0, le=5000)
    billing_day: int | None = Field(default=None, ge=1, le=31)
    due_day_offset: int | None = Field(default=None, ge=1, le=60)
    notes: str | None = None


class CreditCardResponse(BaseModel):
    """Credit card response model."""

    id: str
    account_id: str
    name: str
    bank: str
    card_last4: str | None = None
    credit_limit_paise: int
    annual_fee_paise: int = 0
    interest_rate_bps: int
    billing_day: int | None = None
    due_day_offset: int = 21
    is_active: bool = True
    notes: str | None = None

    @classmethod
    def from_card_dict(cls, card: dict[str, Any]) -> "CreditCardResponse":
        """Create CreditCardResponse from card dict."""
        return cls(
            id=card["id"],
            account_id=card["account_id"],
            name=card["name"],
            bank=card["bank"],
            card_last4=card.get("card_last4"),
            credit_limit_paise=card["credit_limit_paise"],
            annual_fee_paise=card.get("annual_fee_paise", 0),
            interest_rate_bps=card["interest_rate_bps"],
            billing_day=card.get("billing_day"),
            due_day_offset=card.get("due_day_offset", 21),
            is_active=bool(card.get("is_active", 1)),
            notes=card.get("notes"),
        )
