"""
Statement DTOs
==============

Data Transfer Objects for statement-related API responses.
All monetary fields use _paise suffix for explicit units.
"""

from pydantic import BaseModel, Field


class StatementDTO(BaseModel):
    """
    Statement data transfer object.

    Monetary fields:
    - total_debit_paise: Total debit amount in paise (canonical)
    - total_credit_paise: Total credit amount in paise (canonical)
    - total_due_paise: Total amount due in paise (canonical)
    - min_due_paise: Minimum amount due in paise (canonical)
    - extracted_net_paise: Net (debit - credit) in paise
    - validation_difference_paise: Validation difference in paise
    """

    id: int = Field(description="Statement ID")
    bank: str = Field(description="Bank name")
    file_name: str = Field(description="Original file name")
    card_last4: str = Field(description="Last 4 digits of card")
    card_display: str = Field(description="Formatted card display (e.g., '****1234')")
    period_from: str = Field(description="Statement period start")
    period_to: str = Field(description="Statement period end")
    period_display: str = Field(description="Formatted period display")
    transaction_count: int = Field(description="Number of transactions")

    # Canonical paise fields
    total_debit_paise: int = Field(description="Total debit in paise")
    total_credit_paise: int = Field(description="Total credit in paise")
    total_due_paise: int = Field(description="Total amount due in paise")
    min_due_paise: int = Field(description="Minimum amount due in paise")
    extracted_net_paise: int = Field(description="Net (debit - credit) in paise")
    validation_difference_paise: int = Field(
        description="Validation difference in paise"
    )

    # Display fields
    total_debit_display: str = Field(description="Formatted total debit")
    total_credit_display: str = Field(description="Formatted total credit")
    total_due_display: str = Field(description="Formatted total due")
    extracted_net_display: str = Field(description="Formatted extracted net")
    min_due_display: str = Field(description="Formatted minimum due")

    due_date: str = Field(description="Payment due date")
    validation_status: str = Field(description="Validation status")
    badge_text: str = Field(description="Badge display text")
    badge_color: str = Field(description="Badge color")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "bank": "HDFC Bank",
                "file_name": "statement.pdf",
                "card_last4": "1234",
                "card_display": "****1234",
                "period_from": "01/06/2025",
                "period_to": "30/06/2025",
                "period_display": "01/06/2025 – 30/06/2025",
                "transaction_count": 50,
                "total_debit_paise": 5000000,
                "total_credit_paise": 2000000,
                "total_due_paise": 3000000,
                "min_due_paise": 150000,
                "extracted_net_paise": 3000000,
                "validation_difference_paise": 0,
                "total_debit_display": "₹50,000.00",
                "total_credit_display": "₹20,000.00",
                "total_due_display": "₹30,000.00",
                "extracted_net_display": "₹30,000.00",
                "min_due_display": "₹1,500.00",
                "due_date": "15/07/2025",
                "validation_status": "exact_match",
                "badge_text": "✅ Exact Match",
                "badge_color": "green",
            }
        }
