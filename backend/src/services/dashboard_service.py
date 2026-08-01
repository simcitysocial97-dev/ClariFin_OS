"""Dashboard business orchestration service."""

from datetime import datetime

from src.common import enrich_transaction
from src.core.dtos.dashboard_dto import DashboardSummaryDTO
from src.engines.behaviour_engine.core import (
    compute_behavior_profile,
    get_cached_behavior_profile,
    set_cached_behavior_profile,
)
from src.repositories.reconciliation_repository import ReconciliationRepository
from src.repositories.transaction_repository import TransactionRepository
from src.services.base import BaseService


class DashboardService(BaseService):
    """Service for dashboard orchestration."""

    def __init__(self, db_path: str | None = None):
        super().__init__(db_path)
        self.txn_repo = TransactionRepository(self.db_path)
        self.recon_repo = ReconciliationRepository(self.db_path)

    def get_summary(self) -> DashboardSummaryDTO:
        """
        Orchestrate dashboard data from multiple sources.

        Returns a DashboardSummaryDTO with financial metrics in paise.
        """
        # Check cache first
        cached = get_cached_behavior_profile(self.db_path)
        if cached is not None:
            profile = cached
        else:
            # Get transactions for behavior analysis
            raw_transactions = self.txn_repo.get_all_transactions_with_bank({})
            transactions = [dict(t) for t in raw_transactions]
            profile = compute_behavior_profile(transactions)
            set_cached_behavior_profile(self.db_path, profile)

        # Get transactions
        raw = self.txn_repo.get_all_transactions_with_bank({})
        transactions = [enrich_transaction(dict(t)) for t in raw]

        # Calculate income and expenses this month
        this_month_cutoff = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        this_month_txns = [
            t for t in transactions if t.get("parsed_date", "") >= this_month_cutoff
        ]
        total_income_paise = sum(
            t.get("amount_paise", 0)
            for t in this_month_txns
            if t.get("type") == "credit"
        )
        total_expenses_paise = sum(
            t.get("amount_paise", 0)
            for t in this_month_txns
            if t.get("type") == "debit"
        )
        net_cash_flow_paise = total_income_paise - total_expenses_paise

        # Savings rate
        savings_rate = 0.0
        if total_income_paise > 0:
            savings_rate = round((net_cash_flow_paise / total_income_paise) * 100, 2)

        # EMI ratio (from profile or calculated)
        indices = profile.get("behavioral_indices", {})
        savings_discipline = indices.get("savings_discipline", {})
        emi_paise = int(savings_discipline.get("emi_paise", 0) or 0)
        emi_ratio = 0.0
        if total_income_paise > 0:
            emi_ratio = round((emi_paise / total_income_paise) * 100, 2)

        # Buffer days (from profile)
        buffer_days = int(savings_discipline.get("buffer_days", 0) or 0)

        return DashboardSummaryDTO(
            net_cash_flow_paise=net_cash_flow_paise,
            total_income_paise=total_income_paise,
            total_expenses_paise=total_expenses_paise,
            savings_rate=savings_rate,
            emi_paise=emi_paise,
            emi_ratio=emi_ratio,
            buffer_days=buffer_days,
        )
