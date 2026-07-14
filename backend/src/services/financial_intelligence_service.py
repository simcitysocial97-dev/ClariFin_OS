"""Financial Intelligence Service - Orchestration layer for forecasting and goal planning.

Coordinates existing services to provide financial forecasts and goal projections.
No calculation logic - delegates to financial_intelligence engine functions.
"""

from datetime import date
from decimal import Decimal
from typing import Any

from src.common import DB_PATH
from src.engines.financial_intelligence import (
    calculate_goal_health,
    calculate_goal_projection,
    calculate_household_goal_summary,
    compare_scenario,
    detect_future_cash_shortfall,
    forecast_cashflow,
    forecast_credit_utilization,
    forecast_liquidity,
    simulate_credit_behaviour_change,
    simulate_debt_prepayment,
    simulate_expense_reduction,
    simulate_income_change,
    simulate_new_loan,
)
from src.repositories import CashflowRepository
from src.repositories.financial_goal_repository import FinancialGoalRepository
from src.services.behaviour_service import BehaviourService
from src.services.cashflow_service import CashflowService
from src.services.credit_card_service import CreditCardService
from src.services.financial_events_service import FinancialEventsService
from src.services.loan_service import LoanService


class FinancialIntelligenceService:
    """
    Orchestrates financial forecasting by coordinating existing services
    and delegating calculations to pure engine functions.
    """

    def __init__(
        self,
        db_path: str | None = None,
        cashflow_service: CashflowService | None = None,
        events_service: FinancialEventsService | None = None,
        behaviour_service: BehaviourService | None = None,
        loan_service: LoanService | None = None,
        credit_card_service: CreditCardService | None = None,
    ) -> None:
        """Initialize FinancialIntelligenceService with optional service instances.

        Args:
            db_path: Database path for service initialization
            cashflow_service: CashflowService instance (optional)
            events_service: FinancialEventsService instance (optional)
            behaviour_service: BehaviourService instance (optional)
            loan_service: LoanService instance (optional)
            credit_card_service: CreditCardService instance (optional)
        """
        self.db_path = db_path or DB_PATH
        self.cashflow_service = cashflow_service or CashflowService(db_path)
        self.cashflow_repo = CashflowRepository(db_path)
        self.events_service = events_service or FinancialEventsService(db_path)
        self.behaviour_service = behaviour_service or BehaviourService(db_path)
        self.loan_service = loan_service or LoanService(db_path)
        self.credit_card_service = credit_card_service or CreditCardService(db_path)

    def get_cashflow_forecast(
        self,
        forecast_months: int = 3,
    ) -> dict[str, Any]:
        """Get cashflow forecast for the household.

        Args:
            forecast_months: Number of months to forecast (1-12, default: 3)

        Returns:
            Forecast result from engine with model_version metadata
        """
        # Get historical cashflow data
        monthly_data = self.cashflow_repo.get_monthly_cashflow(months=12)

        # Convert to engine input format
        cashflow_history = [
            {
                "month": row.get("month_key", ""),
                "income_paise": int(row.get("income_paise", 0) or 0),
                "expense_paise": int(row.get("expense_paise", 0) or 0),
                "surplus_paise": int(
                    (row.get("income_paise", 0) or 0)
                    - (row.get("expense_paise", 0) or 0)
                ),
            }
            for row in monthly_data
            if row.get("month_key")
        ]

        return forecast_cashflow(cashflow_history, forecast_months)

    def get_liquidity_forecast(
        self,
        forecast_months: int = 3,
        emergency_threshold_paise: int | None = None,
    ) -> dict[str, Any]:
        """Get liquidity forecast for the household.

        Args:
            forecast_months: Number of months to forecast (1-12, default: 3)
            emergency_threshold_paise: Custom emergency threshold (default: 3,000,000 paise)

        Returns:
            Liquidity forecast result from engine with model_version metadata
        """
        # Get cashflow forecast first
        cashflow_result = self.get_cashflow_forecast(forecast_months)
        cashflow_forecast = cashflow_result.get("forecast", [])

        # Get current liquidity from accounts
        # Note: In production, this would use AccountService to aggregate liquid assets
        current_liquidity = 0
        # For now, estimate from most recent cash surplus
        monthly_data = self.cashflow_repo.get_monthly_cashflow(months=1)
        if monthly_data:
            # Rough estimate: assume 2x monthly surplus as buffer
            income_p = int(monthly_data[0].get("income_paise", 0) or 0)
            expense_p = int(monthly_data[0].get("expense_paise", 0) or 0)
            surplus = income_p - expense_p
            current_liquidity = max(0, surplus * 2)

        return forecast_liquidity(
            current_liquidity_paise=current_liquidity,
            cashflow_forecast=cashflow_forecast,
            emergency_threshold_paise=emergency_threshold_paise or 3000000,
        )

    def get_credit_forecast(
        self,
        month: str | None = None,
        household_id: str = "primary",
    ) -> dict[str, Any]:
        """Get credit dependency forecast.

        Args:
            month: Month for analysis (YYYY-MM format, default: current month)
            household_id: Household identifier (default: "primary")

        Returns:
            Credit forecast result from engine with model_version metadata
        """
        # Get financial events for recent months
        if month is None:
            month = date.today().strftime("%Y-%m")

        # Get events with links for the specified month
        financial_events = self.events_service.get_events_with_links(
            month_bucket=month,
            household_id=household_id,
        )

        # Convert to normalized credit history format
        # (In production, would aggregate from CreditCardService)
        credit_history = self._build_credit_history(financial_events)

        return forecast_credit_utilization(financial_events, credit_history)

    def get_financial_outlook(
        self,
        forecast_months: int = 3,
        emergency_threshold_paise: int | None = None,
    ) -> dict[str, Any]:
        """Combine all forecasts into a comprehensive financial outlook.

        Args:
            forecast_months: Number of months to forecast (1-12, default: 3)
            emergency_threshold_paise: Custom emergency threshold (default: 3,000,000 paise)

        Returns:
            Combined outlook with cashflow, liquidity, credit forecasts and risk flags
        """
        # Get individual forecasts
        cashflow_result = self.get_cashflow_forecast(forecast_months)
        liquidity_result = self.get_liquidity_forecast(
            forecast_months,
            emergency_threshold_paise,
        )
        credit_result = self.get_credit_forecast()

        # Detect shortfalls
        shortfall_result = detect_future_cash_shortfall(
            cashflow_result.get("forecast", []),
            liquidity_result,
        )

        # Build combined outlook
        risk_flags: list[dict[str, Any]] = []

        if shortfall_result.get("flag"):
            risk_flags.append({
                "type": "cash_shortfall",
                "severity": shortfall_result.get("severity"),
                "month": shortfall_result.get("expected_month"),
                "reason": shortfall_result.get("reason"),
            })

        if liquidity_result.get("risk_level") == "high":
            risk_flags.append({
                "type": "liquidity_stress",
                "severity": "high",
                "months_until_stress": liquidity_result.get("months_until_stress"),
            })

        if credit_result.get("trend") == "worsening":
            risk_flags.append({
                "type": "credit_dependency",
                "severity": "warning",
                "trend": "worsening",
            })

        return {
            "cashflow": cashflow_result,
            "liquidity": liquidity_result,
            "credit": credit_result,
            "risk_flags": risk_flags,
            "model_version": "v1.0-weightedaverage",
        }

    def _build_credit_history(
        self,
        financial_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Build normalized credit history from financial events.

        Args:
            financial_events: List of financial event dicts

        Returns:
            Normalized credit history list
        """
        # Group events by month and compute utilization
        months: dict[str, dict[str, Any]] = {}

        for event in financial_events:
            month = event.get("month_bucket", "")
            if not month:
                continue

            if month not in months:
                months[month] = {
                    "month": month,
                    "utilization_ratio": Decimal("0.0"),
                    "revolver_ratio": Decimal("0.0"),
                    "cash_advance_paise": 0,
                }

            event_type = event.get("event_type", "")
            if event_type in ("cash_advance", "credit_card_cash_advance"):
                months[month]["cash_advance_paise"] += int(event.get("amount_paise", 0) or 0)

            # Track revolving behavior
            lifecycle = event.get("lifecycle_state", "")
            if lifecycle in ("open", "partially_settled", "rolls_over"):
                months[month]["revolver_ratio"] = Decimal("0.5")

        return list(months.values())

    # ============================================================
    # Goal Planning Methods
    # ============================================================

    def create_goal(
        self,
        goal_id: str,
        household_id: str,
        goal_type: str,
        name: str,
        target_amount_paise: int,
        current_amount_paise: int = 0,
        owner_id: str | None = None,
        target_date: str | None = None,
        priority: str = "medium",
        status: str = "active",
    ) -> dict[str, Any]:
        """Create a new financial goal.

        Args:
            goal_id: Unique goal identifier
            household_id: Household identifier
            goal_type: Type of goal (emergency_fund, debt_payoff, etc.)
            name: Goal name
            target_amount_paise: Target amount in paise
            current_amount_paise: Current saved amount (default: 0)
            owner_id: Owner identifier (optional)
            target_date: Target completion date (optional)
            priority: Goal priority (default: medium)
            status: Goal status (default: active)

        Returns:
            Created goal dict
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        goal_repo.create_goal(
            goal_id=goal_id,
            household_id=household_id,
            goal_type=goal_type,
            name=name,
            target_amount_paise=target_amount_paise,
            current_amount_paise=current_amount_paise,
            owner_id=owner_id,
            target_date=target_date,
            priority=priority,
            status=status,
        )
        return self.get_goal(goal_id)

    def get_goal(self, goal_id: str) -> dict[str, Any]:
        """Get a single goal by ID.

        Args:
            goal_id: Goal identifier

        Returns:
            Goal dict
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        goal = goal_repo.get_goal(goal_id)
        if goal is None:
            return {"id": goal_id, "error": "Goal not found"}
        return goal

    def get_household_goals(
        self,
        household_id: str = "primary",
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get all goals for a household.

        Args:
            household_id: Household identifier
            status: Optional filter by status

        Returns:
            List of goal dicts
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        return goal_repo.get_household_goals(household_id=household_id, status=status)

    def update_goal(
        self,
        goal_id: str,
        **kwargs: str | int | None,
    ) -> dict[str, Any]:
        """Update a goal's fields.

        Args:
            goal_id: Goal identifier
            **kwargs: Fields to update

        Returns:
            Updated goal dict
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        return goal_repo.update_goal(goal_id, **kwargs) or {}

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal.

        Args:
            goal_id: Goal identifier

        Returns:
            True if deleted, False otherwise
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        return goal_repo.delete_goal(goal_id)

    def get_goal_projection(
        self,
        goal_id: str,
    ) -> dict[str, Any]:
        """Get goal achievement projection.

        Combines:
        1. FinancialGoalRepository - get goal data
        2. CashflowService - get monthly cashflow analysis
        3. Financial Intelligence forecasting - get surplus forecast
        4. goal_planner - calculate projection

        Args:
            goal_id: Goal identifier

        Returns:
            Projection dict with achieved, months_required, confidence
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        goal = goal_repo.get_goal(goal_id)

        if goal is None:
            return {"goal_id": goal_id, "error": "Goal not found"}

        # Get cashflow forecast for surplus projections
        cashflow_result = self.get_cashflow_forecast(forecast_months=12)
        monthly_surplus_forecast = cashflow_result.get("forecast", [])

        # Calculate projection using engine
        projection = calculate_goal_projection(
            target_amount_paise=goal.get("target_amount_paise", 0),
            current_amount_paise=goal.get("current_amount_paise", 0),
            monthly_surplus_forecast=monthly_surplus_forecast,
        )

        return {
            "goal_id": goal_id,
            "achieved": projection["achieved"],
            "projected_completion_month": projection["projected_completion_month"],
            "months_required": projection["months_required"],
            "confidence": projection["confidence"],
            "model_version": "v1.0-goalplanner",
        }

    def get_goal_health(
        self,
        goal_id: str,
    ) -> dict[str, Any]:
        """Get goal health score.

        Args:
            goal_id: Goal identifier

        Returns:
            Health score dict with score, status, explanation
        """
        goal_repo = FinancialGoalRepository(self.db_path)
        goal = goal_repo.get_goal(goal_id)

        if goal is None:
            return {"goal_id": goal_id, "error": "Goal not found"}

        projection = self.get_goal_projection(goal_id)

        health = calculate_goal_health(
            target_amount_paise=goal.get("target_amount_paise", 0),
            current_amount_paise=goal.get("current_amount_paise", 0),
            months_required=projection.get("months_required"),
            projected_completion_month=projection.get("projected_completion_month"),
            target_date=goal.get("target_date"),
        )

        return {
            "goal_id": goal_id,
            "score": health["score"],
            "status": health["status"],
            "explanation": health["explanation"],
            "model_version": "v1.0-goalplanner",
        }

    def get_household_goal_summary(
        self,
        household_id: str = "primary",
    ) -> dict[str, Any]:
        """Get household-level goal summary.

        Args:
            household_id: Household identifier

        Returns:
            Summary dict with total_goals, completed, on_track, at_risk, critical_goals
        """
        goals = self.get_household_goals(household_id=household_id, status=None)

        # Get projections for all active goals
        projections = []
        for goal in goals:
            if goal.get("status") == "active":
                health = self.get_goal_health(goal["id"])
                projections.append(health)
            else:
                projections.append({"status": "completed"})

        return calculate_household_goal_summary(goals, projections)

    # ============================================================
    # Scenario Simulation Methods
    # ============================================================

    def simulate_expense_change(
        self,
        reduction_paise: int,
        household_id: str = "primary",
        forecast_months: int = 12,
    ) -> dict[str, Any]:
        """Simulate expense reduction scenario.

        Fetches cashflow forecast, then delegates to scenario engine.

        Args:
            reduction_paise: Monthly expense reduction in paise
            household_id: Household identifier
            forecast_months: Number of months to project

        Returns:
            Scenario result dict
        """
        cashflow_result = self.get_cashflow_forecast(forecast_months=12)
        monthly_surplus_forecast = cashflow_result.get("forecast", [])

        return simulate_expense_reduction(
            current_monthly_expense_paise=0,  # Not used in current implementation
            reduction_paise=reduction_paise,
            monthly_surplus_forecast=monthly_surplus_forecast,
            forecast_months=forecast_months,
        )

    def simulate_income_change(
        self,
        change_paise: int,
        household_id: str = "primary",
        forecast_months: int = 12,
    ) -> dict[str, Any]:
        """Simulate income change scenario.

        Fetches cashflow forecast, then delegates to scenario engine.

        Args:
            change_paise: Monthly income change in paise (positive or negative)
            household_id: Household identifier
            forecast_months: Number of months to project

        Returns:
            Scenario result dict
        """
        cashflow_result = self.get_cashflow_forecast(forecast_months=12)
        monthly_surplus_forecast = cashflow_result.get("forecast", [])

        return simulate_income_change(
            current_income_paise=0,  # Not used directly
            change_paise=change_paise,
            monthly_surplus_forecast=monthly_surplus_forecast,
            forecast_months=forecast_months,
        )

    def simulate_debt_prepayment(
        self,
        extra_payment_paise: int,
        household_id: str = "primary",
    ) -> dict[str, Any]:
        """Simulate debt prepayment scenario.

        Fetches loan data, then delegates to scenario engine.

        Args:
            extra_payment_paise: Extra monthly payment toward debt in paise
            household_id: Household identifier

        Returns:
            Scenario result dict
        """
        # Get loans from loan service
        loans = []
        # In production, would use LoanService to get actual loan data

        # Get current surplus
        cashflow_result = self.get_cashflow_forecast(forecast_months=1)
        monthly_surplus = cashflow_result.get("forecast", [{}])[0].get("expected_surplus_paise", 0)

        return simulate_debt_prepayment(
            debt_accounts=loans,
            extra_payment_paise=extra_payment_paise,
            monthly_surplus_paise=monthly_surplus,
        )

    def simulate_new_loan(
        self,
        principal_paise: int,
        annual_rate_bps: int,
        tenure_months: int,
        household_id: str = "primary",
    ) -> dict[str, Any]:
        """Simulate new loan impact scenario.

        Delegates directly to scenario engine (no data fetching needed).

        Args:
            principal_paise: Loan principal in paise
            annual_rate_bps: Annual interest rate in basis points
            tenure_months: Loan tenure in months
            household_id: Household identifier

        Returns:
            Scenario result dict with EMI, FOIR, affordability
        """
        # Get current surplus for FOIR calculation
        cashflow_result = self.get_cashflow_forecast(forecast_months=1)
        monthly_surplus = cashflow_result.get("forecast", [{}])[0].get("expected_surplus_paise", 0)

        return simulate_new_loan(
            principal_paise=principal_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=tenure_months,
            current_surplus_paise=monthly_surplus,
        )

    def simulate_credit_change(
        self,
        household_id: str = "primary",
        average_interest_rate_bps: int | None = None,
    ) -> dict[str, Any]:
        """Simulate credit behavior change scenario.

        Fetches credit metrics from behaviour service, then delegates to scenario engine.

        Args:
            household_id: Household identifier
            average_interest_rate_bps: Optional average interest rate for calculation

        Returns:
            Scenario result dict
        """
        # In production, would fetch actual credit dependency ratio from BehaviourService
        # For now, return baseline values
        return simulate_credit_behaviour_change(
            current_credit_dependency_ratio=Decimal("0.5"),
            current_revolver_ratio=Decimal("0.3"),
            average_interest_rate_bps=average_interest_rate_bps,
        )

    def compare_scenarios(
        self,
        baseline: dict[str, Any],
        scenario: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare baseline vs scenario results.

        Delegates directly to scenario engine.

        Args:
            baseline: Baseline scenario result
            scenario: Simulated scenario result

        Returns:
            Comparison result with improvements, risks, delta
        """
        return compare_scenario(baseline, scenario)
