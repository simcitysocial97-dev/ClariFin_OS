"""
Transaction DTOs
================

Data Transfer Objects for transaction-related API responses.
All monetary fields use _paise suffix for explicit units.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class TransactionDTO(BaseModel):
    """
    Transaction data transfer object.
    
    Monetary fields:
    - amount_paise: Transaction amount in paise (canonical)
    - amount_rupees: Transaction amount in rupees (temporary, for backward compatibility)
    - balance_paise: Running balance after transaction in paise
    """
    id: str = Field(description="Unique transaction identifier")
    date: str = Field(description="Transaction date (ISO format)")
    description: str = Field(description="Transaction description")
    amount_paise: int = Field(description="Transaction amount in paise (canonical)")
    amount_rupees: Optional[float] = Field(
        default=None,
        description="Transaction amount in rupees (DEPRECATED - use amount_paise)"
    )
    balance_paise: Optional[int] = Field(
        default=None,
        description="Running balance after transaction in paise"
    )
    category: str = Field(description="Transaction category")
    subcategory: Optional[str] = Field(default=None, description="Transaction subcategory")
    bank: str = Field(description="Bank name")
    transaction_type: str = Field(description="Transaction type (debit/credit)")
    reference_number: Optional[str] = Field(default=None, description="Bank reference number")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "txn_123",
                "date": "2026-07-05",
                "description": "Amazon Purchase",
                "amount_paise": -150000,  # -₹1,500.00
                "amount_rupees": -1500.0,  # TODO: Remove in Phase 2
                "balance_paise": 850000,  # ₹8,500.00
                "category": "Shopping",
                "subcategory": "E-commerce",
                "bank": "HDFC Bank",
                "transaction_type": "debit",
                "reference_number": "REF123"
            }
        }


class TransactionListResponse(BaseModel):
    """Response for transaction list endpoint."""
    transactions: List[TransactionDTO] = Field(description="List of transactions")
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
    amount_paise: int = Field(description="Total amount in paise")
    amount_rupees: Optional[float] = Field(
        default=None,
        description="Total amount in rupees (DEPRECATED)"
    )
    count: int = Field(description="Number of transactions")
    percentage: float = Field(description="Percentage of total (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "category": "Shopping",
                "amount_paise": 500000,  # ₹5,000.00
                "amount_rupees": 5000.0,  # TODO: Remove in Phase 2
                "count": 15,
                "percentage": 25.5
            }
        }