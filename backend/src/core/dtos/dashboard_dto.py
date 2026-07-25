"""
Dashboard DTOs
==============

Data Transfer Objects for dashboard and analytics API responses.
All monetary fields use _paise suffix for explicit units.
"""

from typing import Any

from pydantic import BaseModel, Field


class DashboardSummaryDTO(BaseModel):
    """
    Dashboard summary data transfer object.

    Monetary fields:
    - net_cash_flow_paise: Net cash flow in paise (canonical)
    - total_income_paise: Total income in paise
    - total_expenses_paise: Total expenses in paise
    - emi_paise: EMI amount in paise
    - savings_paise: Savings amount in paise
    """

    net_cash_flow_paise: int = Field(
        description="Net cash flow in paise (income - expenses)"
    )
    net_cash_flow_rupees: float | None = Field(
        default=None,
        description="Net cash flow in rupees (DEPRECATED - use net_cash_flow_paise)",
    )
    total_income_paise: int = Field(description="Total income in paise")
    total_expenses_paise: int = Field(description="Total expenses in paise")
    savings_rate: float = Field(description="Savings rate as percentage (0-100)")
    emi_paise: int = Field(description="EMI amount in paise")
    emi_ratio: float = Field(description="EMI to income ratio (0-100)")
    buffer_days: int = Field(description="Emergency buffer in days")

    class Config:
        json_schema_extra = {
            "example": {
                "net_cash_flow_paise": 2500000,  # ₹25,000.00
                "net_cash_flow_rupees": 25000.0,  # TODO: Remove in Phase 2
                "total_income_paise": 10000000,  # ₹1,00,000.00
                "total_expenses_paise": 7500000,  # ₹75,000.00
                "savings_rate": 25.0,
                "emi_paise": 1250000,  # ₹12,500.00
                "emi_ratio": 12.5,
                "buffer_days": 45,
            }
        }


class OverviewDTO(BaseModel):
    """
    Overview data transfer object for dashboard.

    Contains aggregated financial metrics and chart data.
    """

    total_spend_paise: int = Field(description="Total spending in paise")
    total_spend_rupees: float | None = Field(
        default=None, description="Total spending in rupees (DEPRECATED)"
    )
    transaction_count: int = Field(description="Total number of transactions")
    category_chart: list[dict[str, Any]] = Field(
        description="Category-wise spending data for charts"
    )
    monthly_chart: list[dict[str, Any]] = Field(
        description="Monthly spending trend data"
    )
    bank_wise_chart: list[dict[str, Any]] = Field(
        description="Bank-wise spending distribution"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "total_spend_paise": 5000000,  # ₹50,000.00
                "total_spend_rupees": 50000.0,  # TODO: Remove in Phase 2
                "transaction_count": 150,
                "category_chart": [],
                "monthly_chart": [],
                "bank_wise_chart": [],
            }
        }


class CategoryBreakdownDTO(BaseModel):
    """Category breakdown for analytics."""

    category: str = Field(description="Category name")
    amount_paise: int = Field(description="Amount in paise")
    count: int = Field(description="Number of transactions")
    percentage: float = Field(description="Percentage of total")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "Shopping",
                "amount_paise": 500000,  # ₹5,000.00
                "count": 15,
                "percentage": 25.5,
            }
        }
