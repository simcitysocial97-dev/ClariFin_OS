"""Cashflow Intelligence Workspace Service.

Returns aggregated cashflow data matching CashflowViewModel format.
"""

# Timing logger
import logging
import time
from typing import Any

from src.services.cashflow_service import CashflowService

logger = logging.getLogger(__name__)


def _timed_log(
    endpoint: str, duration_ms: float, success: bool = True, error: str | None = None
) -> None:
    """Emit structured timing log for cashflow workspace endpoints."""
    log_data = {
        "type": "cashflow_workspace_request",
        "endpoint": endpoint,
        "duration_ms": round(duration_ms, 2),
        "success": success,
    }
    if error:
        log_data["error"] = error
        logger.warning(
            "[CASHFLOW-WS] %s | %.0fms | FAIL: %s", endpoint, duration_ms, error
        )
    else:
        logger.info("[CASHFLOW-WS] %s | %.0fms", endpoint, duration_ms)


class CashflowWorkspaceService:
    """Service for cashflow workspace aggregation."""

    def __init__(self, db_path: str | None = None) -> None:
        self.cashflow_service = CashflowService(db_path)

    def get_cashflow_summary(self, period: str = "monthly") -> dict[str, Any]:
        """Get cashflow summary for the workspace.

        Returns aggregated data matching CashflowViewModel format.
        """
        start = time.monotonic()

        # Get summary data
        summary = self.cashflow_service.calculate_summary()
        monthly = self.cashflow_service.get_monthly(months=12)
        categories = self.cashflow_service.get_categories()
        transactions = self.cashflow_service.get_transactions(limit=50, offset=0)

        # Build evidence chain
        evidence_chain = {
            "summary": f"Cashflow analysis based on {summary.transaction_count} transactions",
            "evidence": [
                {
                    "type": "summary",
                    "summary": f"Total income: ₹{summary.total_income_paise / 100:,.2f}",
                    "source": "cashflow_service",
                    "confidence": 100.0,
                },
                {
                    "type": "summary",
                    "summary": f"Total expenses: ₹{summary.total_expenses_paise / 100:,.2f}",
                    "source": "cashflow_service",
                    "confidence": 100.0,
                },
            ],
            "calculation_steps": [
                {
                    "name": "Cashflow Calculation",
                    "description": "Income minus expenses equals net cashflow",
                    "inputs": {
                        "total_income_paise": summary.total_income_paise,
                        "total_expenses_paise": summary.total_expenses_paise,
                    },
                    "outputs": {
                        "net_cashflow_paise": summary.net_cashflow_paise,
                    },
                },
            ],
            "source_references": ["transactions", "categories"],
            "confidence_score": 95.0,
        }

        # Build insights
        insights = []
        if summary.net_cashflow_paise > 0:
            insights.append(
                {
                    "type": "positive",
                    "severity": "low",
                    "message": f"Positive cashflow of ₹{summary.net_cashflow_paise / 100:,.2f} this period",
                }
            )
        elif summary.net_cashflow_paise < 0:
            insights.append(
                {
                    "type": "alert",
                    "severity": "high",
                    "message": f"Negative cashflow of ₹{abs(summary.net_cashflow_paise) / 100:,.2f} - review expenses",
                }
            )

        # Build monthly data
        monthly_data = [
            {
                "month": m.month,
                "income_paise": m.income_paise,
                "expenses_paise": m.expenses_paise,
                "net_paise": m.net_paise,
                "transaction_count": m.transaction_count,
            }
            for m in monthly.months
        ]

        # Build category data
        category_data = [
            {
                "category_id": c.category_id,
                "category_name": c.category_name,
                "amount_paise": c.amount_paise,
                "percentage": c.percentage,
                "transaction_count": c.transaction_count,
            }
            for c in categories.categories
        ]

        # Build transaction data
        transaction_data = [
            {
                "id": t.id,
                "date": t.date,
                "description": t.description,
                "amount_paise": t.amount_paise,
                "category": t.category,
                "merchant": t.merchant,
            }
            for t in transactions.transactions
        ]

        result = {
            "total_income_paise": summary.total_income_paise,
            "total_expenses_paise": summary.total_expenses_paise,
            "net_cashflow_paise": summary.net_cashflow_paise,
            "transaction_count": summary.transaction_count,
            "trend": (
                {
                    "direction": summary.trend.direction if summary.trend else "flat",
                    "percentage_change": (
                        summary.trend.percentage_change if summary.trend else 0.0
                    ),
                    "period": summary.trend.period if summary.trend else "1M",
                    "volatility_score": (
                        summary.trend.volatility_score if summary.trend else 0.0
                    ),
                }
                if summary.trend
                else None
            ),
            "monthly": monthly_data,
            "categories": category_data,
            "transactions": transaction_data,
            "insights": insights,
            "evidence_chain": evidence_chain,
            "filters": {
                "date_range": None,
                "categories": None,
                "merchants": None,
                "amount_range": None,
            },
            "navigation": {
                "deep_link": "/cashflow",
                "cross_references": {
                    "accounts": "/accounts",
                    "transactions": "/transactions",
                },
            },
        }

        _timed_log("get_cashflow_summary", (time.monotonic() - start) * 1000)
        return result
