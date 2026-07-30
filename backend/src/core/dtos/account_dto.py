"""
Account DTOs
============

Data Transfer Objects for account-related API responses.
All monetary fields use _paise suffix for explicit units.
"""

from pydantic import BaseModel, Field


class AccountDTO(BaseModel):
    """
    Account data transfer object.

    Monetary fields:
    - balance_paise: Account balance in paise (canonical)
    - balance_rupees: Account balance in rupees (temporary, for backward compatibility)
    """

    id: str = Field(description="Unique account identifier")
    name: str = Field(description="Account name")
    bank_name: str = Field(description="Bank name")
    account_type: str = Field(description="Account type (Savings, Current, FD, RD)")
    balance_paise: int = Field(description="Balance in paise (1 INR = 100 paise)")
    last_updated: str = Field(description="Last update timestamp (ISO format)")

    # TODO: Remove in Phase 2 - backward compatibility during migration
    # Frontend will migrate to use balance_paise, then this field can be removed
    balance_rupees: float | None = Field(
        default=None, description="Balance in rupees (DEPRECATED - use balance_paise)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "acc_123",
                "name": "Primary Savings",
                "bank_name": "HDFC Bank",
                "account_type": "Savings",
                "balance_paise": 1000000,  # ₹10,000.00
                "balance_rupees": 10000.0,  # TODO: Remove in Phase 2
                "last_updated": "2026-07-05T10:30:00",
            }
        }


class AccountListResponse(BaseModel):
    """Response for account list endpoint."""

    accounts: list[AccountDTO] = Field(description="List of accounts")
    total_accounts: int = Field(description="Total number of accounts")
    total_balance_paise: int = Field(
        description="Total balance across all accounts in paise"
    )

    class Config:
        json_schema_extra = {
            "example": {"accounts": [], "total_accounts": 0, "total_balance_paise": 0}
        }
