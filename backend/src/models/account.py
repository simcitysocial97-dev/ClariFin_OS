from typing import Any, Literal

from pydantic import BaseModel, Field

from src.models.base import DomainModel, Money

AccountType = Literal[
    "savings",
    "current",
    "credit_card",
    "investment",
    "loan",
    "other",
]


class Account(DomainModel):
    """Account domain entity"""

    id: int
    name: str
    type: AccountType
    initial_balance: Money

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Account":
        """Convert a database row into an Account model.

        Expects a row exposing `initial_balance_paise` (int) — the canonical
        paise storage for the account's opening balance.
        """
        return cls(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            initial_balance=Money(paise=row["initial_balance_paise"]),
        )


# ============================================================
# Request/Response DTOs for Account CRUD
# ============================================================


class AccountCreateRequest(BaseModel):
    """Account creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    bank: str = Field(..., min_length=1, max_length=50)
    account_type: str = Field(default="savings", max_length=20)
    balance_paise: int = Field(default=0, ge=0, description="Initial balance in paise")
    account_number_last4: str | None = Field(
        default=None, pattern=r"^\d{4}$", description="Last 4 digits of account number"
    )
    notes: str | None = None


class AccountUpdateRequest(BaseModel):
    """Account update request."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    bank: str | None = Field(default=None, min_length=1, max_length=50)
    account_type: str | None = Field(default=None, max_length=20)
    balance_paise: int | None = Field(default=None, ge=0)
    account_number_last4: str | None = Field(default=None, pattern=r"^\d{4}$")
    notes: str | None = None


class AccountResponse(BaseModel):
    """Account response model."""

    id: int
    name: str
    bank: str
    account_type: str
    balance_paise: int
    account_number_last4: str | None = None
    notes: str | None = None
    is_active: bool = True
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_account_dict(cls, account: dict[str, Any]) -> "AccountResponse":
        """Create AccountResponse from account dict."""
        return cls(
            id=account["id"],
            name=account["name"],
            bank=account.get("bank", ""),
            account_type=account.get("account_type", "savings"),
            balance_paise=account.get("balance_paise", 0),
            account_number_last4=account.get("account_number_last4"),
            notes=account.get("notes"),
            is_active=bool(account.get("is_active", 1)),
            created_at=account.get("created_at"),
            updated_at=account.get("updated_at"),
        )


class AccountAnalytics(BaseModel):
    """Account analytics response."""

    average_balance_paise: int
    balance_change_paise: int
    balance_growth_bps: int
    trend: str
    velocity_paise_per_day: int
