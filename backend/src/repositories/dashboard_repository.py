"""Dashboard domain repository (cross-domain orchestration).

LOC WATCH: No repository file > 200 LOC.
If it grows beyond 200, split by sub-domain.
"""
from datetime import datetime, timedelta

from src.common import enrich_transaction
from src.engines.behavior_engine import (
    compute_behavior_profile,
    get_cached_behavior_profile,
    set_cached_behavior_profile,
)
from src.repositories.base import DB_PATH
from src.repositories.transaction_repository import TransactionRepository


class DashboardRepository:
    """Repository for dashboard operations (cross-domain orchestration)."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or DB_PATH
        self._txn_repo = TransactionRepository(self.db_path)

    def get_summary(self) -> dict:
        """
        Get simplified dashboard summary for MVP.

        Returns 4 key metrics:
        - Net Cash Flow
        - Savings Rate %
        - EMI Ratio %
        - Buffer Days
        """
        # Check cache first
        cached = get_cached_behavior_profile(self.db_path)
        if cached is not None:
            profile = cached
        else:
            profile = compute_behavior_profile(self.db_path)
            set_cached_behavior_profile(self.db_path, profile)

        indices = profile.get("behavioral_indices", {})

        # Calculate net cash flow from savings discipline
        savings_discipline = indices.get("savings_discipline", {})
        savings_rate = savings_discipline.get("savings_rate", 0)

        # Get financial stress data for EMI ratio and buffer
        financial_stress = indices.get("financial_stress", {})
        emi_ratio = profile.get("risk_signals", {}).get("india_specific", {}).get("emi_ratio", 0)
        buffer_days = financial_stress.get("buffer_days", 0)

        # Calculate net cash flow (simplified)
        # Net cash flow = (income - expenses) over last 30 days
        raw = self._txn_repo.get_all_transactions_with_bank({})
        transactions = [enrich_transaction(dict(t)) for t in raw]

        # Get last 30 days transactions
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        recent_txns = [t for t in transactions if t.get("parsed_date", "") >= cutoff]

        total_income = sum(t.get("amount", 0) for t in recent_txns if t.get("type") == "credit")
        total_expenses = sum(t.get("amount", 0) for t in recent_txns if t.get("type") == "debit")
        net_cash_flow = total_income - total_expenses

        # Calculate 7-day trend
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        seven_day_txns = [t for t in transactions if t.get("parsed_date", "") >= seven_days_ago]

        prev_seven_start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        prev_seven_txns = [t for t in transactions if prev_seven_start <= t.get("parsed_date", "") < seven_days_ago]

        current_spend = sum(t.get("amount", 0) for t in seven_day_txns if t.get("type") == "debit")
        prev_spend = sum(t.get("amount", 0) for t in prev_seven_txns if t.get("type") == "debit")

        seven_day_trend = 0
        if prev_spend > 0:
            seven_day_trend = (current_spend - prev_spend) / prev_spend

        # Category drift alert (simplified)
        category_drift_alert = None
        if profile.get("risk_signals", {}).get("high_impulsivity"):
            category_drift_alert = "High impulsivity detected. Consider reviewing discretionary spending."
        elif profile.get("risk_signals", {}).get("low_savings"):
            category_drift_alert = "Savings rate is below target. Consider reducing non-essential expenses."

        # Recent transactions
        recent = sorted(transactions, key=lambda t: t.get("parsed_date", ""), reverse=True)[:10]

        return {
            "net_cash_flow_paise": int(round(net_cash_flow * 100)),
            "savings_rate": savings_rate,
            "emi_ratio": emi_ratio,
            "buffer_days": buffer_days,
            "financial_health_score": profile.get("financial_health_score", 50),
            "seven_day_trend": seven_day_trend,
            "category_drift_alert": category_drift_alert,
            "recent_transactions": recent,
        }
