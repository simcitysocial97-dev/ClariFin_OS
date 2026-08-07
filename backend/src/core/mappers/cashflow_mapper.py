"""Cashflow Mapper

Transforms cashflow domain objects into CashflowDTO instances.
This is the ONLY location where cashflow API responses are constructed.
"""

from typing import Any

from src.core.dtos.cashflow_dto import (
    CashflowCategoryDTO,
    CashflowInsightDTO,
    CashflowMonthlyDTO,
    CashflowSummaryDTO,
    CashflowTransactionDTO,
    CashflowTrendDTO,
)


class CashflowMapper:
    """Mapper for cashflow domain objects to DTOs."""

    @staticmethod
    def to_summary_dto(cashflow_data: dict[str, Any]) -> CashflowSummaryDTO:
        """Convert cashflow data to CashflowSummaryDTO."""
        return CashflowSummaryDTO(
            total_income_paise=cashflow_data.get("total_income_paise", 0),
            total_expenses_paise=cashflow_data.get("total_expenses_paise", 0),
            net_cashflow_paise=cashflow_data.get("net_cashflow_paise", 0),
            transaction_count=cashflow_data.get("transaction_count", 0),
            trend=CashflowMapper._to_trend_dto(cashflow_data.get("trend")),
            insights=CashflowMapper._to_insights(cashflow_data.get("insights", [])),
            evidence_chain=cashflow_data.get("evidence_chain"),
        )

    @staticmethod
    def _to_trend_dto(trend_data: dict[str, Any] | None) -> CashflowTrendDTO | None:
        """Convert trend data to CashflowTrendDTO."""
        if not trend_data:
            return None
        return CashflowTrendDTO(
            direction=trend_data.get("direction", "flat"),
            percentage_change=trend_data.get("percentage_change", 0.0),
            period=trend_data.get("period", "1M"),
            volatility_score=trend_data.get("volatility_score", 0.0),
        )

    @staticmethod
    def _to_insights(insights: list[dict[str, Any]]) -> list[CashflowInsightDTO]:
        """Convert insights to CashflowInsightDTO list."""
        return [
            CashflowInsightDTO(
                type=insight.get("type", "info"),
                severity=insight.get("severity", "medium"),
                message=insight.get("message", ""),
                action_url=insight.get("action_url"),
            )
            for insight in insights
        ]

    @staticmethod
    def to_monthly_dto(monthly_data: dict[str, Any]) -> CashflowMonthlyDTO:
        """Convert monthly cashflow data to CashflowMonthlyDTO."""
        return CashflowMonthlyDTO(
            month=monthly_data.get("month", ""),
            income_paise=monthly_data.get("income_paise", 0),
            expenses_paise=monthly_data.get("expenses_paise", 0),
            net_paise=monthly_data.get("net_paise", 0),
            transaction_count=monthly_data.get("transaction_count", 0),
        )

    @staticmethod
    def to_category_dto(category_data: dict[str, Any]) -> CashflowCategoryDTO:
        """Convert category data to CashflowCategoryDTO."""
        return CashflowCategoryDTO(
            category_id=category_data.get("category_id", ""),
            category_name=category_data.get("category_name", "Unknown"),
            amount_paise=category_data.get("amount_paise", 0),
            percentage=category_data.get("percentage", 0.0),
            transaction_count=category_data.get("transaction_count", 0),
        )

    @staticmethod
    def to_transaction_dto(transaction_data: dict[str, Any]) -> CashflowTransactionDTO:
        """Convert transaction data to CashflowTransactionDTO."""
        return CashflowTransactionDTO(
            id=transaction_data.get("id", ""),
            date=transaction_data.get("date", ""),
            description=transaction_data.get("description", ""),
            amount_paise=transaction_data.get("amount_paise", 0),
            category=transaction_data.get("category", "Uncategorized"),
            merchant=transaction_data.get("merchant"),
        )
