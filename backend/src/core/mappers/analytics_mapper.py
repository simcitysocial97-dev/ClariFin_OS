"""
Analytics Mapper
================

Transforms analytics domain objects into AnalyticsResponse DTOs.
This is the ONLY location where analytics API responses are constructed.
"""

from typing import Any

from src.core.dtos.analytics_dto import (
    AnalyticsResponse,
    DayOfWeekData,
    LargestTransaction,
    MerchantData,
    RecurringCharge,
    SpendingTrendPoint,
)


class AnalyticsMapper:
    """
    Mapper for analytics domain objects to DTOs.

    Responsibilities:
    - Transform analytics data to AnalyticsResponse
    - Ensure all monetary fields have explicit units (_paise suffix)
    """

    @staticmethod
    def to_response(
        highest_month: str,
        highest_month_amount_paise: int,
        avg_monthly_paise: int,
        biggest_transaction: dict[str, Any] | None,
        unique_merchants: int,
        spending_trend: list[dict[str, Any]],
        day_of_week: list[dict[str, Any]],
        top_merchants: list[dict[str, Any]],
        recurring_charges: list[dict[str, Any]],
        largest_transactions: list[dict[str, Any]],
    ) -> AnalyticsResponse:
        """
        Convert analytics data to AnalyticsResponse.

        Args:
            highest_month: Month label with highest spending
            highest_month_amount_paise: Amount in paise for highest month
            avg_monthly_paise: Average monthly spending in paise
            biggest_transaction: Biggest single transaction details
            unique_merchants: Number of unique merchants
            spending_trend: Monthly spending trend data
            day_of_week: Day-of-week spending breakdown
            top_merchants: Top merchants by spending
            recurring_charges: Detected recurring charges
            largest_transactions: Largest transactions list

        Returns:
            AnalyticsResponse instance
        """
        return AnalyticsResponse(
            highest_month=highest_month,
            highest_month_amount_paise=highest_month_amount_paise,
            avg_monthly_paise=avg_monthly_paise,
            biggest_transaction=biggest_transaction,
            unique_merchants=unique_merchants,
            spending_trend=[
                SpendingTrendPoint(
                    month=point.get("month", ""),
                    amount_paise=int(point.get("amount_paise", 0)),
                    average_paise=int(point.get("average_paise", 0)),
                )
                for point in spending_trend
            ],
            day_of_week=[
                DayOfWeekData(
                    day=d.get("day", ""),
                    amount_paise=int(d.get("amount_paise", 0)),
                    count=d.get("count", 0),
                )
                for d in day_of_week
            ],
            top_merchants=[
                MerchantData(
                    merchant=m.get("merchant", ""),
                    amount_paise=int(m.get("amount_paise", 0)),
                    count=m.get("count", 0),
                )
                for m in top_merchants
            ],
            recurring_charges=[
                RecurringCharge(
                    description=rc.get("description", ""),
                    frequency=rc.get("frequency", 0),
                    avg_amount_paise=int(rc.get("avg_amount_paise", 0)),
                    annual_amount_paise=int(rc.get("annual_amount_paise", 0)),
                )
                for rc in recurring_charges
            ],
            largest_transactions=[
                LargestTransaction(
                    rank=lt.get("rank", 0),
                    date_display=lt.get("date_display", ""),
                    description=lt.get("description", ""),
                    amount_paise=int(lt.get("amount_paise", 0)),
                    bank=lt.get("bank", ""),
                )
                for lt in largest_transactions
            ],
        )
