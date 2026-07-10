"""
Transaction DTOs
================

Data Transfer Objects for transaction-related API responses.
All monetary fields use _paise suffix for explicit units.
"""


from pydantic import BaseModel, Field


class MoneyDTO(BaseModel):
    """
    Money data transfer object.

    Represents monetary value with explicit paise (integer) and rupees (float) fields.
    This is the canonical API representation of the Money domain object.
    """
    paise: int = Field(description="Amount in paise (canonical integer representation)")
    rupees: float = Field(description="Amount in rupees (for display purposes)")

    class Config:
        json_schema_extra = {
            "example": {
                "paise": 123456,
                "rupees": 1234.56
            }
        }


class TransactionDTO(BaseModel):
    """
    Transaction data transfer object.

    Monetary fields:
    - amount: MoneyDTO with paise and rupees (canonical)
    - balance: MoneyDTO with paise and rupees (optional)
    """
    id: int | str = Field(description="Unique transaction identifier")
    date: str = Field(description="Transaction date (ISO format)")
    description: str = Field(description="Transaction description")
    amount: MoneyDTO = Field(description="Transaction amount as Money object")
    balance: MoneyDTO | None = Field(
        default=None,
        description="Running balance after transaction as Money object"
    )
    category: str = Field(description="Transaction category")
    subcategory: str | None = Field(default=None, description="Transaction subcategory")
    bank: str = Field(description="Bank name")
    transaction_type: str = Field(description="Transaction type (debit/credit)")
    reference_number: str | None = Field(default=None, description="Bank reference number")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "txn_123",
                "date": "2026-07-05",
                "description": "Amazon Purchase",
                "amount": {
                    "paise": -150000,
                    "rupees": -1500.0
                },
                "balance": {
                    "paise": 850000,
                    "rupees": 8500.0
                },
                "category": "Shopping",
                "subcategory": "E-commerce",
                "bank": "HDFC Bank",
                "transaction_type": "debit",
                "reference_number": "REF123"
            }
        }


class TransactionListResponse(BaseModel):
    """Response for transaction list endpoint."""
    transactions: list[TransactionDTO] = Field(description="List of transactions")
    total: int = Field(description="Total number of transactions")
    limit: int = Field(description="Number of transactions per page")
    offset: int = Field(description="Offset for pagination")

    class Config:
        json_schema_extra = {
            "example": {
                "transactions": [],
                "total": 0,
                "limit": 50,
                "offset": 0
            }
        }


class CategorySummaryDTO(BaseModel):
    """Category summary with monetary values."""
    category: str = Field(description="Category name")
    amount: MoneyDTO = Field(description="Total amount as Money object")
    count: int = Field(description="Number of transactions")
    percentage: float = Field(description="Percentage of total (0-100)")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "Shopping",
                "amount": {
                    "paise": 500000,
                    "rupees": 5000.0
                },
                "count": 15,
                "percentage": 25.5
            }
        }
