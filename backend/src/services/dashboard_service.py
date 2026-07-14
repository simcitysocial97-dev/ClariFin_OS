"""Dashboard business orchestration service."""

from collections import Counter
from datetime import datetime

from src.common import enrich_transaction
from src.models.base import Money
from src.models.dashboard import DashboardSummary
from src.repositories.reconciliation_repository import ReconciliationRepository
from src.repositories.transaction_repository import TransactionRepository
from src.services.behaviour_service import BehaviourService


class DashboardService:
    """Service for dashboard orchestration."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or "data/finance.db"
        self.txn_repo = TransactionRepository(self.db_path)
        self.recon_repo = ReconciliationRepository(self.db_path)

    def get_summary(self) -> DashboardSummary:
        """
        Orchestrate dashboard data from multiple sources.

        Returns a typed DashboardSummary with behavior insights.
        """
        # Use BehaviourService for profile computation
        behaviour_svc = BehaviourService(self.db_path)
        cached = behaviour_svc.get_cached_profile()

        if cached is not None:
            profile = cached
        else:
            profile_result = behaviour_svc.compute_financial_profile()
            profile = {
                "profile_type": profile_result.profile_type,
                "confidence": float(profile_result.confidence),
                "financial_health_score": 50,
            }
            behaviour_svc.set_cached_profile(profile)

        # Get transactions
        raw = self.txn_repo.get_all_transactions_with_bank({})
        transactions = [enrich_transaction(dict(t)) for t in raw]

        # Calculate spending this month
        this_month_cutoff = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        this_month_txns = [t for t in transactions if t.get("parsed_date", "") >= this_month_cutoff]
        spending_this_month = sum(
            t.get("amount", 0) for t in this_month_txns if t.get("type") == "debit"
        )

        # Top category by spend
        category_spends = [t.get("category", "Uncategorized") for t in this_month_txns if t.get("type") == "debit"]
        top_category = Counter(category_spends).most_common(1)[0][0] if category_spends else "None"

        # Large transactions (>= ₹10,000)
        large_threshold_paise = 10000 * 100  # ₹10,000
        large_transactions = [
            t
            for t in transactions
            if t.get("amount_paise", 0) >= large_threshold_paise
        ][:5]

        # Pending reconciliations
        pending_count = len(self.recon_repo.get_reconciliations(status="pending"))

        # Insights and nudges (derived from profile)
        insights: list[str] = []
        nudges: list[str] = []

        if profile.get("risk_signals", {}).get("low_savings"):
            nudges.append("Consider setting aside more for savings this month.")

        # Use profile type from BehaviourService result
        profile_type = profile.get("profile_type", "INSUFFICIENT_DATA")
        if profile_type == "SAVER":
            insights.append("Great job! Your savings rate exceeds 20%.")

        return DashboardSummary(
            behavior_score=float(profile.get("financial_health_score", 50)) / 100.0,
            spending_this_month=Money(paise=int(round(spending_this_month * 100))),
            top_category=top_category,
            insights=insights,
            nudges=nudges,
            reconciliation_pending=pending_count,
            large_transactions=large_transactions,
        )
