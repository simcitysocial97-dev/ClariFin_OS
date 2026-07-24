"""Statement Processing Orchestrator

Coordinates the post-upload pipeline:
- BehaviourService (profile, wellness recalculation)
- CashflowService (summary recalculation)
- FinancialIntelligenceService (forecasting, goals)
- RecommendationService (loan optimization)
- Dashboard refresh
- TransactionIntelligenceService (EMI/CC/cash classification)

Synchronous orchestration with graceful degradation.
"""

from typing import Any

from src.services.behaviour_service import BehaviourService
from src.services.cashflow_service import CashflowService
from src.services.dashboard_service import DashboardService
from src.services.financial_intelligence_service import FinancialIntelligenceService
from src.services.loan_service import LoanService
from src.services.transaction_intelligence_service import TransactionIntelligenceService


class StatementProcessingOrchestrator:
    """Coordinates post-upload financial intelligence pipeline."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path
        self.behaviour_service = BehaviourService(db_path)
        self.cashflow_service = CashflowService(db_path)
        self.intelligence_service = FinancialIntelligenceService(db_path)
        self.loan_service = LoanService(db_path)
        self.dashboard_service = DashboardService(db_path)
        self.transaction_intelligence_service = TransactionIntelligenceService(db_path)

    def process_after_upload(self, statement_id: int) -> dict[str, Any]:
        """Execute full pipeline after statement upload.

        Args:
            statement_id: ID of uploaded statement

        Returns:
            Pipeline execution summary
        """
        summary: dict[str, Any] = {
            "statement_id": statement_id,
            "behaviour": None,
            "cashflow": None,
            "intelligence": None,
            "recommendations": None,
            "dashboard": None,
            "transaction_intelligence": None,
        }

        # Stage 1: Behaviour recalculation
        try:
            summary["behaviour"] = self._run_behaviour()
        except Exception as e:
            summary["behaviour_error"] = str(e)

        # Stage 2: Cashflow recalculation
        try:
            summary["cashflow"] = self._run_cashflow()
        except Exception as e:
            summary["cashflow_error"] = str(e)

        # Stage 3: Financial Intelligence
        try:
            summary["intelligence"] = self._run_intelligence()
        except Exception as e:
            summary["intelligence_error"] = str(e)

        # Stage 4: Recommendations
        try:
            summary["recommendations"] = self._run_recommendations()
        except Exception as e:
            summary["recommendations_error"] = str(e)

        # Stage 5: Dashboard refresh
        try:
            summary["dashboard"] = self._run_dashboard_refresh()
        except Exception as e:
            summary["dashboard_error"] = str(e)

        # Stage 6: Transaction Intelligence (EMI/CC/cash classification)
        try:
            summary["transaction_intelligence"] = self._run_transaction_intelligence()
        except Exception as e:
            summary["transaction_intelligence_error"] = str(e)

        return summary

    def _run_behaviour(self) -> dict[str, Any]:
        """Run behaviour profile recalculation.

        Returns:
            Behaviour result summary
        """
        profile = self.behaviour_service.compute_financial_profile(household_id="default")
        return {
            "profile_generated": bool(profile),
            "profile_type": profile.profile_type if profile else None,
        }

    def _run_cashflow(self) -> dict[str, Any]:
        """Run cashflow summary recalculation.

        Returns:
            Cashflow result summary
        """
        summary = self.cashflow_service.calculate_summary()
        return {
            "summary_generated": bool(summary),
            "net_cashflow_paise": summary.net_cashflow_paise if summary else 0,
        }

    def _run_intelligence(self) -> dict[str, Any]:
        """Run financial intelligence analysis.

        Returns:
            Intelligence result summary
        """
        outlook = self.intelligence_service.get_financial_outlook(forecast_months=3)
        optimization = self.intelligence_service.get_optimization_plan()
        report = self.intelligence_service.get_financial_intelligence_report()

        return {
            "outlook_generated": bool(outlook),
            "optimization_generated": bool(optimization),
            "report_generated": bool(report),
        }

    def _run_recommendations(self) -> dict[str, Any]:
        """Run loan analysis recommendations.

        Returns:
            Recommendation result summary
        """
        loans = self.loan_service.get_loans()
        if not loans:
            return {"loan_count": 0, "recommendations_generated": False}

        from src.services.loan_analysis_service import LoanAnalysisService

        analysis = LoanAnalysisService(self.db_path)
        priority = analysis.analyze_loan_priority()

        return {
            "loan_count": len(loans),
            "recommendations_generated": True,
            "recommendation_count": len(priority),
        }

    def _run_dashboard_refresh(self) -> dict[str, Any]:
        """Refresh dashboard summaries.

        Returns:
            Dashboard refresh status
        """
        # DashboardService aggregates data on-demand; no explicit refresh needed.
        # This method validates that key dashboard inputs are available.
        summary = self.dashboard_service.get_summary()
        return {
            "refreshed": True,
            "summary_available": bool(summary),
        }

    def _run_transaction_intelligence(self) -> dict[str, Any]:
        """Run transaction intelligence classification.

        Classifies EMI payments, credit card payments, and cash conversions
        from unclassified transactions after statement upload.

        Returns:
            Transaction intelligence result summary
        """
        emi_results = self.transaction_intelligence_service.classify_emi_payments()
        cc_results = self.transaction_intelligence_service.classify_cc_payments()
        cash_results = self.transaction_intelligence_service.classify_cash_conversions()

        return {
            "emi_classified": len(emi_results),
            "cc_classified": len(cc_results),
            "cash_conversions_classified": len(cash_results),
            "total_classified": len(emi_results) + len(cc_results) + len(cash_results),
        }
