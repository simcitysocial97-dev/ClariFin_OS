"""Financial Intelligence Service - Orchestration layer for forecasting and goal planning.

Coordinates existing services to provide financial forecasts and goal projections.
No calculation logic - delegates to financial_intelligence engine functions.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

from src.common import DB_PATH
from src.engines.financial_intelligence import (
    ScenarioComparison,
    calculate_goal_health,
    calculate_goal_projection,
    calculate_household_goal_summary,
    compare_scenario,
    derive_cash_advance_debt_entry,
    detect_future_cash_shortfall,
    forecast_cashflow,
    forecast_credit_utilization,
    forecast_liquidity,
    generate_financial_intelligence_report,
    generate_optimization_plan,
    simulate_credit_behaviour_change,
    simulate_debt_prepayment,
    simulate_expense_reduction,
    simulate_income_change,
    simulate_new_loan,
)
from src.repositories import CashflowRepository
from src.repositories.financial_event_repository import FinancialEventRepository
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
        household_id: str = "primary",
        owner_id: str = "self",
    ) -> dict[str, Any]:
        """Get cashflow forecast for the household.

        Args:
            forecast_months: Number of months to forecast (1-12, default: 3)
            household_id: Household identifier (default: "primary")
            owner_id: Owner filter - "self" for individual, None for household-wide

        Returns:
            Forecast result from engine with model_version metadata
        """
        # Get TRUE historical cashflow data (adjusted for artificial income)
        monthly_data = self.cashflow_repo.get_true_monthly_cashflow(
            months=12,
            household_id=household_id,
            owner_id=owner_id,
        )

        # Convert to engine input format
        cashflow_history = [
            {
                "month": row.get("month_key", ""),
                "income_paise": int(row.get("income_paise", 0) or 0),
                "expense_paise": int(row.get("expense_paise", 0) or 0),
                "surplus_paise": int(row.get("surplus_paise", 0) or 0),
            }
            for row in monthly_data
            if row.get("month_key")
        ]

        return forecast_cashflow(cashflow_history, forecast_months)

    def get_liquidity_forecast(
        self,
        forecast_months: int = 3,
        emergency_threshold_paise: int | None = None,
        household_id: str = "primary",
        owner_id: str = "self",
    ) -> dict[str, Any]:
        """Get liquidity forecast for the household.

        Args:
            forecast_months: Number of months to forecast (1-12, default: 3)
            emergency_threshold_paise: Custom emergency threshold (default: 3,000,000 paise)
            household_id: Household identifier (default: "primary")
            owner_id: Owner filter - "self" for individual, None for household-wide

        Returns:
            Liquidity forecast result from engine with model_version metadata
        """
        # Get cashflow forecast first (now uses true cashflow)
        cashflow_result = self.get_cashflow_forecast(forecast_months=forecast_months, household_id=household_id, owner_id=owner_id)
        cashflow_forecast = cashflow_result.get("forecast", [])

        # Get current liquidity from accounts
        # Note: In production, this would use AccountService to aggregate liquid assets
        current_liquidity = 0
        # For now, estimate from most recent cash surplus (use true cashflow)
        monthly_data = self.cashflow_repo.get_true_monthly_cashflow(
            months=1,
            household_id=household_id,
            owner_id=owner_id,
        )
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
        loans: list[dict[str, Any]] = []
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
    ) -> ScenarioComparison:
        """Compare baseline vs scenario results.

        Delegates directly to scenario engine.

        Args:
            baseline: Baseline scenario result
            scenario: Simulated scenario result

        Returns:
            Comparison result with improvements, risks, delta
        """
        return compare_scenario(baseline, scenario)

    # ============================================================
    # Optimization Methods
    # ============================================================

    def _compute_holding_period(
        self,
        event_repo: FinancialEventRepository,
        event: dict[str, Any],
    ) -> int:
        """Compute holding period for a cash advance event.

        Checks for settlement links to determine actual holding period.
        Falls back to 30 days if no settlement link found.

        Args:
            event_repo: FinancialEventRepository instance
            event: The cash advance event dict

        Returns:
            Holding period in days (30 as default estimate)
        """
        DEFAULT_HOLDING_DAYS = 30

        # Check for settlement links
        links = event_repo.get_links_for_event(event["id"])
        for link in links:
            if link.get("link_type") == "settles":
                linked_event_id = link.get("linked_event_id")
                if linked_event_id:
                    with event_repo._get_conn() as conn:
                        row = conn.execute(
                            "SELECT date_iso FROM financial_events WHERE id = ?",
                            (linked_event_id,),
                        ).fetchone()
                    if row and row["date_iso"]:
                        advance_date = datetime.fromisoformat(event.get("date_iso", "2025-01-01"))
                        settle_date = datetime.fromisoformat(row["date_iso"])
                        days = (settle_date - advance_date).days
                        if days > 0:
                            return days

        return DEFAULT_HOLDING_DAYS

    def get_optimization_plan(
        self,
        household_id: str = "primary",
    ) -> dict[str, Any]:
        """Get optimization plan for the household.

        Orchestrates data fetching from:
        - CashflowService → surplus
        - LoanService → loans
        - CreditCardService → credit card liabilities
        - FinancialEventRepository → cash advance liabilities
        - BehaviourService → risk indicators
        - FinancialGoalRepository → goals

        Then delegates to generate_optimization_plan() in the engine.

        Args:
            household_id: Household identifier (default: "primary")

        Returns:
            Optimization plan with recommended_actions, allocation_plan, warnings, confidence
        """
        # Fetch surplus data
        cashflow_result = self.get_cashflow_forecast(forecast_months=1)
        monthly_surplus = (
            cashflow_result.get("forecast", [{}])[0].get("expected_surplus_paise", 0) or 0
        )

        # Fetch debt data (loans)
        loans = self.loan_service.get_loans()

        # Fetch credit card data
        credit_cards = self.credit_card_service.list_cards()

        # Combine debts in engine format
        debts = [
            {
                "id": loan.get("id"),
                "type": "loan",
                "name": loan.get("name", "Unknown Loan"),
                "outstanding_paise": int(loan.get("outstanding_paise", 0) or 0),
                "interest_rate_bps": int(loan.get("interest_rate_bps", 0) or 0),
            }
            for loan in loans
        ] + [
            {
                "id": card.get("id"),
                "type": "credit_card",
                "name": card.get("name", "Unknown Card"),
                "outstanding_paise": int(card.get("outstanding_paise", 0) or 0),
                "interest_rate_bps": int(card.get("interest_rate_bps", 0) or 0),
                "minimum_due_paise": int(card.get("minimum_due_paise", 0) or 0),
            }
            for card in credit_cards
        ]

        # Fetch open cash advance liabilities
        event_repo = FinancialEventRepository(self.db_path)
        cash_advance_events = event_repo.get_open_cash_advance_events(household_id=household_id)

        for event in cash_advance_events:
            # Determine holding period by checking for settlement link
            holding_period_days = self._compute_holding_period(event_repo, event)

            # Convert to debt entry format and append
            cash_advance_debt = derive_cash_advance_debt_entry(
                event=event,
                holding_period_days=holding_period_days,
            )
            if cash_advance_debt["outstanding_paise"] > 0:
                debts.append(cash_advance_debt)

        # Fetch goals
        goals = self.get_household_goals(household_id=household_id, status=None)

        # Fetch liquidity forecast for emergency fund status
        liquidity_result = self.get_liquidity_forecast(forecast_months=3)

        # Fetch credit risk indicators
        credit_result = self.get_credit_forecast()

        # Build financial state for engine
        financial_state = {
            "surplus": {"monthly_surplus_paise": monthly_surplus},
            "debts": debts,
            "goals": goals,
            "forecast": liquidity_result,
            "risk": {
                "credit_revolver_ratio": credit_result.get("current_dependency_ratio", Decimal("0")),
            },
        }

        return generate_optimization_plan(financial_state)

    # ============================================================
    # Financial Intelligence Report Methods
    # ============================================================

    def get_financial_intelligence_report(
        self,
        household_id: str = "primary",
    ) -> dict[str, Any]:
        """Get comprehensive financial intelligence report.

        Orchestrates data fetching from:
        - BehaviourService → behaviour profile, wellness score
        - CashflowService → monthly analysis
        - LoanService → loans
        - CreditCardService → credit cards
        - FinancialGoalRepository → goals
        - Forecasting engine → cashflow, liquidity, credit forecasts
        - Optimization engine → optimization plan

        Then delegates to generate_financial_intelligence_report() in the engine.

        Args:
            household_id: Household identifier (default: "primary")

        Returns:
            IntelligenceReport with snapshot, health_score, priorities, risks, opportunities, confidence
        """
        # 1. Fetch behaviour data using wellness and debt health endpoints
        wellness_response = self.behaviour_service.get_wellness_score(household_id="default")
        debt_response = self.behaviour_service.get_debt_health(household_id="default")

        behaviour = {
            "wellness_score": wellness_response.score,
            "credit_revolver_ratio": debt_response.credit_revolver_ratio,
            "debt_cycle_score": debt_response.debt_cycle_score,
        }

        # 2. Fetch cashflow data
        cashflow_result = self.get_cashflow_forecast(forecast_months=3)
        cashflow = {
            "income_paise": cashflow_result.get("income_paise", 0),
            "expense_paise": cashflow_result.get("expense_paise", 0),
            "monthly_surplus_paise": cashflow_result.get("monthly_surplus_paise", 0),
        }

        # 3. Fetch liquidity forecast
        liquidity = self.get_liquidity_forecast(forecast_months=3)

        # 4. Fetch debt data
        loans = self.loan_service.get_loans()
        credit_cards = self.credit_card_service.list_cards()

        debts = [
            {
                "id": loan.get("id"),
                "type": "loan",
                "outstanding_paise": int(loan.get("outstanding_paise", 0) or 0),
                "interest_rate_bps": int(loan.get("interest_rate_bps", 0) or 0),
            }
            for loan in loans
        ] + [
            {
                "id": card.get("id"),
                "type": "credit_card",
                "outstanding_paise": int(card.get("outstanding_paise", 0) or 0),
                "interest_rate_bps": int(card.get("interest_rate_bps", 0) or 0),
            }
            for card in credit_cards
        ]

        # 5. Fetch goals
        goals = self.get_household_goals(household_id=household_id, status=None)

        # 6. Fetch forecasts
        credit_forecast = self.get_credit_forecast()
        forecasts = {
            "cashflow": cashflow_result,
            "liquidity": liquidity,
            "credit": credit_forecast,
        }

        # 7. Fetch optimization plan
        optimisation = self.get_optimization_plan(household_id=household_id)

        # 8. Build financial state for intelligence engine
        financial_state = {
            "cashflow": cashflow,
            "liquidity": liquidity,
            "debts": debts,
            "goals": goals,
            "behaviour": behaviour,
            "forecasts": forecasts,
            "optimization": optimisation,
        }

        # 9. Delegate to intelligence engine
        result = generate_financial_intelligence_report(financial_state)
        return cast(dict[str, Any], result)
