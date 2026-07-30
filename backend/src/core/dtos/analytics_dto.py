"""
Analytics DTOs
==============

Data Transfer Objects for analytics API responses.
All monetary fields use _paise suffix for explicit units.
"""

from typing import Any

from pydantic import BaseModel, Field


class SpendingTrendPoint(BaseModel):
    """Monthly spending trend data point."""

    month: str = Field(description="Month label (e.g., 'Jan 25')")
    amount_paise: int = Field(description="Total spending in paise")
    average_paise: int = Field(description="Average monthly spending in paise")


class DayOfWeekData(BaseModel):
    """Day-of-week spending breakdown."""

    day: str = Field(description="Day name (e.g., 'Mon')")
    amount_paise: int = Field(description="Total spending in paise")
    count: int = Field(description="Number of transactions")


class MerchantData(BaseModel):
    """Top merchant spending data."""

    merchant: str = Field(description="Merchant description")
    amount_paise: int = Field(description="Total spending in paise")
    count: int = Field(description="Number of transactions")


class RecurringCharge(BaseModel):
    """Recurring charge detection result."""

    description: str = Field(description="Charge description")
    frequency: int = Field(description="Number of occurrences")
    avg_amount_paise: int = Field(description="Average amount in paise")
    annual_amount_paise: int = Field(description="Projected annual amount in paise")


class LargestTransaction(BaseModel):
    """Largest transaction detail."""

    rank: int = Field(description="Rank (1-based)")
    date_display: str = Field(description="Formatted date")
    description: str = Field(description="Transaction description")
    amount_paise: int = Field(description="Transaction amount in paise")
    bank: str = Field(description="Bank name")


class AnalyticsResponse(BaseModel):
    """Analytics API response."""

    highest_month: str = Field(description="Month with highest spending")
    highest_month_amount_paise: int = Field(description="Highest month amount in paise")
    avg_monthly_paise: int = Field(description="Average monthly spending in paise")
    biggest_transaction: dict[str, Any] | None = Field(
        default=None, description="Biggest single transaction details"
    )
    unique_merchants: int = Field(description="Number of unique merchants")
    spending_trend: list[SpendingTrendPoint] = Field(
        description="Monthly spending trend data"
    )
    day_of_week: list[DayOfWeekData] = Field(
        description="Day-of-week spending breakdown"
    )
    top_merchants: list[MerchantData] = Field(description="Top merchants by spending")
    recurring_charges: list[RecurringCharge] = Field(
        description="Detected recurring charges"
    )
    largest_transactions: list[LargestTransaction] = Field(
        description="Largest transactions"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "highest_month": "Jun 25",
                "highest_month_amount_paise": 5000000,
                "avg_monthly_paise": 3500000,
                "biggest_transaction": None,
                "unique_merchants": 45,
                "spending_trend": [],
                "day_of_week": [],
                "top_merchants": [],
                "recurring_charges": [],
                "largest_transactions": [],
            }
        }
