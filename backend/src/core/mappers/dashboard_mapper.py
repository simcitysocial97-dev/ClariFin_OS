"""
Dashboard Mapper
================

Transforms dashboard domain objects into DashboardDTO instances.
This is the ONLY location where dashboard API responses are constructed.
"""

from typing import Any

from src.core.domain.money import Money
from src.core.dtos.dashboard_dto import CategoryBreakdownDTO, DashboardSummaryDTO, OverviewDTO


class DashboardMapper:
    """
    Mapper for dashboard domain objects to DTOs.

    Responsibilities:
    - Transform dashboard data to DashboardSummaryDTO
    - Transform overview data to OverviewDTO
    - Add backward compatibility fields (_rupees)
    - Ensure all monetary fields have explicit units (_paise suffix)
    """

    @staticmethod
    def to_summary_dto(
        net_cash_flow: Money,
        total_income: Money,
        total_expenses: Money,
        savings_rate: float,
        emi: Money,
        emi_ratio: float,
        buffer_days: int,
        include_rupees_field: bool = True
    ) -> DashboardSummaryDTO:
        """
        Convert dashboard summary data to DashboardSummaryDTO.

        Args:
            net_cash_flow: Money instance for net cash flow
            total_income: Money instance for total income
            total_expenses: Money instance for total expenses
            savings_rate: Savings rate as percentage (0-100)
            emi: Money instance for EMI amount
            emi_ratio: EMI to income ratio (0-100)
            buffer_days: Emergency buffer in days
            include_rupees_field: If True, include deprecated net_cash_flow_rupees field

        Returns:
            DashboardSummaryDTO instance
        """
        dto_data = {
            "net_cash_flow_paise": net_cash_flow.paise,
            "total_income_paise": total_income.paise,
            "total_expenses_paise": total_expenses.paise,
            "savings_rate": savings_rate,
            "emi_paise": emi.paise,
            "emi_ratio": emi_ratio,
            "buffer_days": buffer_days,
        }

        # TODO: Remove in Phase 2 - backward compatibility
        if include_rupees_field:
            dto_data["net_cash_flow_rupees"] = net_cash_flow.to_rupees()

        return DashboardSummaryDTO(**dto_data)

    @staticmethod
    def to_overview_dto(
        total_spend: Money,
        transaction_count: int,
        category_chart: list[dict[str, Any]],
        monthly_chart: list[dict[str, Any]],
        bank_wise_chart: list[dict[str, Any]],
        include_rupees_field: bool = True
    ) -> OverviewDTO:
        """
        Convert overview data to OverviewDTO.

        Args:
            total_spend: Money instance for total spending
            transaction_count: Total number of transactions
            category_chart: Category-wise spending data for charts
            monthly_chart: Monthly spending trend data
            bank_wise_chart: Bank-wise spending distribution
            include_rupees_field: If True, include deprecated total_spend_rupees field

        Returns:
            OverviewDTO instance
        """
        dto_data = {
            "total_spend_paise": total_spend.paise,
            "transaction_count": transaction_count,
            "category_chart": category_chart,
            "monthly_chart": monthly_chart,
            "bank_wise_chart": bank_wise_chart,
        }

        # TODO: Remove in Phase 2 - backward compatibility
        if include_rupees_field:
            dto_data["total_spend_rupees"] = total_spend.to_rupees()

        return OverviewDTO(**dto_data)

    @staticmethod
    def to_category_breakdown(
        category: str,
        amount_paise: int,
        count: int,
        percentage: float
    ) -> CategoryBreakdownDTO:
        """
        Convert category breakdown data to CategoryBreakdownDTO.

        Args:
            category: Category name
            amount_paise: Amount in paise
            count: Number of transactions
            percentage: Percentage of total

        Returns:
            CategoryBreakdownDTO instance
        """
        return CategoryBreakdownDTO(
            category=category,
            amount_paise=amount_paise,
            count=count,
            percentage=percentage
        )
