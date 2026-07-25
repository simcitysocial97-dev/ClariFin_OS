"""Behaviour Service - Orchestration layer for financial behaviour analysis.

Coordinates repositories and behaviour engines to implement business logic.
No direct database access - uses repositories only.
No calculations - delegates to behaviour_engine pure functions.
"""

from datetime import date
from decimal import Decimal
from typing import Any, cast

from src.engines.behaviour_engine import (
    classify_financial_personality,
    compute_borrowed_lifestyle_ratio,
    compute_cashflow_stability_index,
    compute_credit_dependency_ratio,
    compute_credit_revolver_ratio,
    compute_debt_cycle_score,
    compute_expense_stability,
    compute_foir,
    compute_income_stability,
    compute_lifestyle_inflation,
    compute_monthly_surplus,
    compute_resilience_index,
    compute_true_savings_rate,
    detect_impulse_transactions,
)
from src.engines.behaviour_engine.income import classify_income_source
from src.errors import AppError, NotFoundError
from src.logger import logger
from src.models.behaviour import (
    BehaviourSnapshotCreate,
    CashflowHealthResponse,
    DebtHealthBand,
    DebtHealthResponse,
    FinancialPattern,
    FinancialProfileResponse,
    MonthlySummaryResponse,
    ProfileType,
    RecommendationResponse,
    RecommendationsResponse,
    WellnessBand,
    WellnessScoreResponse,
)
from src.repositories.account_repository import AccountRepository
from src.repositories.behaviour_repository import BehaviourRepository
from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.loan_repository import LoanRepository
from src.repositories.pattern_repository import PatternRepository
from src.repositories.transaction_repository import TransactionRepository


class BehaviourService:
    """Orchestrates financial behaviour analysis and persistence logic.

    Delegates calculations to behaviour_engine (pure functions).
    Delegates persistence to repositories.
    """

    def __init__(
        self,
        db_path: str | None = None,
        transaction_repo: TransactionRepository | None = None,
        account_repo: AccountRepository | None = None,
        loan_repo: LoanRepository | None = None,
        credit_card_repo: CreditCardRepository | None = None,
        behaviour_repo: BehaviourRepository | None = None,
        pattern_repo: PatternRepository | None = None,
    ) -> None:
        """Initialize BehaviourService with optional repository instances.

        Args:
            db_path: Database path for repository initialization
            transaction_repo: TransactionRepository instance (optional)
            account_repo: AccountRepository instance (optional)
            loan_repo: LoanRepository instance (optional)
            credit_card_repo: CreditCardRepository instance (optional)
            behaviour_repo: BehaviourRepository instance (optional)
            pattern_repo: PatternRepository instance (optional)
        """
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)
        self.account_repo = account_repo or AccountRepository(db_path)
        self.loan_repo = loan_repo or LoanRepository(db_path)
        self.credit_card_repo = credit_card_repo or CreditCardRepository(db_path)
        self.behaviour_repo = behaviour_repo or BehaviourRepository(db_path)
        self.pattern_repo = pattern_repo or PatternRepository(db_path)

    def compute_financial_profile(
        self, household_id: str = "default"
    ) -> FinancialProfileResponse:
        """Compute and persist a comprehensive financial behaviour profile.

        1. Fetch financial data from repositories
        2. Call behaviour engines to compute metrics
        3. Persist snapshot via BehaviourRepository
        4. Return financial profile classification

        Args:
            household_id: Household identifier (default: "default")

        Returns:
            FinancialProfileResponse with profile classification

        Raises:
            AppError: If data is insufficient or engine computation fails
        """
        try:
            # Fetch required data
            transactions = self.transaction_repo.get_all_transactions()
            accounts = self.account_repo.get_all_accounts()
            loans = self.loan_repo.list_loans()
            credit_cards = self.credit_card_repo.list_cards()

            if not transactions:
                logger.warning("Insufficient transaction data for profile computation")
                return FinancialProfileResponse(
                    profile_type="INSUFFICIENT_DATA",
                    confidence=Decimal("0"),
                    explanation="Insufficient transaction data for profile classification",
                    snapshot_date=date.today().isoformat(),
                )

            # Compute metrics using behaviour engine
            snapshot_date = date.today().isoformat()

            # Savings metrics
            total_income = sum(
                t["amount_paise"] for t in transactions if t["type"] == "credit"
            )
            total_expenses = sum(
                t["amount_paise"] for t in transactions if t["type"] == "debit"
            )
            financial_fees = self._compute_financial_fees(transactions, credit_cards)

            savings_rate = compute_true_savings_rate(
                total_income, total_expenses, financial_fees
            )
            borrowed_lifestyle_ratio = compute_borrowed_lifestyle_ratio(
                self._compute_credit_funded_expenses(transactions), total_expenses
            )

            # Cashflow metrics
            monthly_incomes = self._get_monthly_incomes(transactions)
            monthly_expenses = self._get_monthly_expenses(transactions)

            compute_income_stability(monthly_incomes)
            compute_expense_stability(monthly_expenses)
            cashflow_stability = compute_cashflow_stability_index(
                monthly_incomes, monthly_expenses
            )
            compute_monthly_surplus(total_income, total_expenses, financial_fees)

            # Debt metrics
            compute_credit_dependency_ratio(
                self._compute_credit_funded_expenses(transactions), total_expenses
            )
            credit_advances = self._count_credit_advances(transactions)
            revolving_months = self._count_revolving_months(credit_cards)
            debt_increase_trend = self._compute_debt_trend(loans)

            debt_cycle_score = compute_debt_cycle_score(
                credit_advances, revolving_months, debt_increase_trend
            )
            foir, foir_band = compute_foir(
                self._compute_fixed_obligations(loans, credit_cards),
                self._compute_minimum_obligations(loans, credit_cards),
                total_income,
            )
            credit_revolver_ratio = compute_credit_revolver_ratio(
                self._compute_revolving_balance(credit_cards), total_expenses
            )

            # Resilience metrics
            liquid_assets = self._compute_liquid_assets(accounts)
            essential_expenses = self._compute_essential_expenses(transactions)

            resilience_index = compute_resilience_index(
                liquid_assets, essential_expenses, total_income, monthly_incomes
            )

            # Lifestyle metrics
            non_essential_current = self._compute_non_essential_expenses(transactions)
            non_essential_previous = self._compute_previous_non_essential_expenses(
                transactions
            )

            lifestyle_inflation = compute_lifestyle_inflation(
                non_essential_current, non_essential_previous
            )

            # Wellness score
            wellness_score = self._compute_wellness_score(
                cashflow_stability,
                debt_cycle_score,
                savings_rate,
                resilience_index,
                lifestyle_inflation,
                credit_revolver_ratio,
                foir,
            )

            # Create and persist snapshot
            snapshot_data = BehaviourSnapshotCreate(
                snapshot_date=snapshot_date,
                household_id=household_id,
                savings_discipline_score_bps=int(savings_rate * 10000),
                cashflow_stability_score_bps=int(cashflow_stability * 10000),
                salary_dependence_ratio_bps=int(
                    self._compute_salary_dependence(transactions) * 10000
                ),
                lifestyle_inflation_rate_bps=int(lifestyle_inflation * 10000),
                subscription_burn_rate_bps=int(
                    self._compute_subscription_burn_rate(transactions) * 10000
                ),
                resilience_index_bps=int(resilience_index * 10000),
                wellness_score_bps=int(wellness_score * 10000),
                version=1,
            )

            self.behaviour_repo.create_snapshot(snapshot_data.model_dump())

            # Classify financial personality
            profile_type, confidence, explanation = classify_financial_personality(
                savings_rate=savings_rate,
                borrowed_lifestyle_ratio=borrowed_lifestyle_ratio,
                credit_revolver_ratio=credit_revolver_ratio,
                discretionary_spending_ratio=self._compute_discretionary_spending_ratio(
                    transactions
                ),
                impulse_transaction_ratio=self._compute_impulse_transaction_ratio(
                    transactions
                ),
                lifestyle_creep_index=self._compute_lifestyle_creep_index(transactions),
                transaction_count=len(transactions),
            )

            return FinancialProfileResponse(
                profile_type=cast(ProfileType, profile_type),
                confidence=confidence,
                explanation=explanation,
                snapshot_date=snapshot_date,
            )

        except Exception as e:
            logger.error(f"Error computing financial profile: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to compute financial profile: {str(e)}",
            )

    def get_wellness_score(
        self, household_id: str = "default"
    ) -> WellnessScoreResponse:
        """Get the latest financial wellness score.

        Args:
            household_id: Household identifier (default: "default")

        Returns:
            WellnessScoreResponse with score, band, and components

        Raises:
            NotFoundError: If no snapshot is available
        """
        try:
            snapshot = self.behaviour_repo.get_latest_snapshot(household_id)
            if not snapshot:
                raise NotFoundError("No behaviour snapshot available")

            # Reconstruct wellness score components
            # Repository returns scores already in 0-100 range (scaled by * 100)
            components: dict[str, Decimal] = {
                "cashflow_health": Decimal(str(snapshot["cashflow_stability_score"])),
                "debt_health": Decimal("1")
                - (Decimal(str(snapshot["debt_cycle_score"])) / Decimal("100")),
                "savings_behaviour": max(
                    Decimal("0"),
                    Decimal(str(snapshot["savings_discipline_score"])),
                ),
                "resilience": Decimal(str(snapshot["resilience_index"])),
                "lifestyle_control": Decimal("1")
                - min(
                    Decimal("1"),
                    max(
                        Decimal("0"), Decimal(str(snapshot["lifestyle_inflation_rate"]))
                    ),
                ),
                "credit_behaviour": Decimal("0.5")
                * (Decimal("1") - Decimal(str(snapshot["credit_revolver_ratio"])))
                + Decimal("0.5")
                * (Decimal("1") - min(Decimal("1"), Decimal("0.4"))),  # Simplified FOIR
            }

            from src.engines.behaviour_engine.wellness import classify_wellness_band

            band = cast(
                WellnessBand,
                classify_wellness_band(Decimal(str(snapshot["wellness_score"]))),
            )

            return WellnessScoreResponse(
                score=Decimal(str(snapshot["wellness_score"])),
                band=band,
                components=components,
                snapshot_date=snapshot["snapshot_date"],
                version=snapshot["version"],
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting wellness score: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to get wellness score: {str(e)}",
            )

    def get_debt_health(self, household_id: str = "default") -> DebtHealthResponse:
        """Get the latest debt health metrics.

        Args:
            household_id: Household identifier (default: "default")

        Returns:
            DebtHealthResponse with debt health metrics

        Raises:
            NotFoundError: If no snapshot is available
        """
        try:
            snapshot = self.behaviour_repo.get_latest_snapshot(household_id)
            if not snapshot:
                raise NotFoundError("No behaviour snapshot available")

            # Get latest transactions for dynamic debt metrics
            transactions = self.transaction_repo.get_all_transactions()
            credit_cards = self.credit_card_repo.list_cards()
            loans = self.loan_repo.list_loans()

            total_income = sum(
                t["amount_paise"] for t in transactions if t["type"] == "credit"
            )
            total_expenses = sum(
                t["amount_paise"] for t in transactions if t["type"] == "debit"
            )

            # Compute dynamic debt metrics
            foir, foir_band = compute_foir(
                self._compute_fixed_obligations(loans, credit_cards),
                self._compute_minimum_obligations(loans, credit_cards),
                total_income,
            )
            credit_dependency_ratio = compute_credit_dependency_ratio(
                self._compute_credit_funded_expenses(transactions), total_expenses
            )
            credit_revolver_ratio = compute_credit_revolver_ratio(
                self._compute_revolving_balance(credit_cards), total_expenses
            )

            band = cast(DebtHealthBand, foir_band)

            return DebtHealthResponse(
                foir=foir,
                credit_dependency_ratio=credit_dependency_ratio,
                debt_cycle_score=snapshot["debt_cycle_score"],
                credit_revolver_ratio=credit_revolver_ratio,
                band=band,
                snapshot_date=snapshot["snapshot_date"],
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting debt health: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to get debt health: {str(e)}",
            )

    def get_cashflow_health(
        self, household_id: str = "default"
    ) -> CashflowHealthResponse:
        """Get the latest cashflow health metrics.

        Args:
            household_id: Household identifier (default: "default")

        Returns:
            CashflowHealthResponse with cashflow health metrics

        Raises:
            NotFoundError: If no snapshot is available
        """
        try:
            snapshot = self.behaviour_repo.get_latest_snapshot(household_id)
            if not snapshot:
                raise NotFoundError("No behaviour snapshot available")

            # Get latest transactions for dynamic cashflow metrics
            transactions = self.transaction_repo.get_all_transactions()
            total_income = sum(
                t["amount_paise"] for t in transactions if t["type"] == "credit"
            )
            total_expenses = sum(
                t["amount_paise"] for t in transactions if t["type"] == "debit"
            )
            financial_fees = self._compute_financial_fees(transactions, [])

            monthly_surplus = compute_monthly_surplus(
                total_income, total_expenses, financial_fees
            )

            return CashflowHealthResponse(
                cashflow_stability_index=Decimal(
                    str(snapshot["cashflow_stability_score"])
                ),
                income_stability=Decimal(str(snapshot["income_stability_score"])),
                expense_stability=Decimal(str(snapshot["expense_stability_score"])),
                monthly_surplus_paise=monthly_surplus,
                snapshot_date=snapshot["snapshot_date"],
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting cashflow health: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to get cashflow health: {str(e)}",
            )

    def get_patterns(
        self, household_id: str = "default", limit: int = 5
    ) -> list[FinancialPattern]:
        """Get the latest detected financial patterns.

        Args:
            household_id: Household identifier (default: "default")
            limit: Maximum number of patterns to return (converted to days for repo)

        Returns:
            List of FinancialPattern objects

        Raises:
            AppError: If pattern retrieval fails
        """
        try:
            # Get patterns from repository - convert limit (int) to days for get_recent_patterns
            patterns = self.pattern_repo.get_recent_patterns(
                days=limit, household_id=household_id
            )

            return [
                FinancialPattern(
                    pattern_type=p["pattern_type"],
                    pattern_key=p["pattern_key"],
                    strength=Decimal(str(p["strength_bps"])) / Decimal("10000"),
                    transaction_count=p["transaction_count"],
                    total_amount_paise=p["total_amount_paise"],
                    first_observed=p["first_observed"],
                    last_observed=p["last_observed"],
                )
                for p in patterns
            ]

        except Exception as e:
            logger.error(f"Error getting patterns: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to get patterns: {str(e)}",
            )

    def generate_monthly_summary(
        self, period: str, household_id: str = "default"
    ) -> MonthlySummaryResponse:
        """Generate a monthly financial summary report.

        Args:
            period: Period in YYYY-MM format
            household_id: Household identifier (default: "default")

        Returns:
            MonthlySummaryResponse with comprehensive financial summary

        Raises:
            NotFoundError: If no snapshot exists for the period
            AppError: If summary generation fails
        """
        try:
            # Get snapshot for the period
            start_date = f"{period}-01"
            end_date = f"{period}-31"  # Simple approach, could be improved

            snapshots = self.behaviour_repo.get_snapshots_by_date_range(
                start_date, end_date, household_id
            )
            if not snapshots:
                raise NotFoundError(f"No snapshots available for period {period}")

            # Use the latest snapshot in the period
            latest_snapshot = snapshots[-1]

            # Get patterns for the period - convert limit (int) to days for get_recent_patterns
            patterns = self.pattern_repo.get_recent_patterns(
                days=5, household_id=household_id
            )

            # Get all transactions (simplified - would filter by date in real implementation)
            transactions = self.transaction_repo.get_all_transactions()
            total_income = sum(
                t["amount_paise"] for t in transactions if t["type"] == "credit"
            )
            total_expenses = sum(
                t["amount_paise"] for t in transactions if t["type"] == "debit"
            )

            # Create wellness score response - scores already in 0-100 range from repository
            wellness_score = WellnessScoreResponse(
                score=Decimal(str(latest_snapshot["wellness_score"])),
                band=cast(
                    WellnessBand,
                    self._classify_wellness_band(
                        Decimal(str(latest_snapshot["wellness_score"]))
                    ),
                ),
                components={
                    "cashflow_health": Decimal(
                        str(latest_snapshot["cashflow_stability_score"])
                    ),
                    "debt_health": Decimal("1")
                    - (
                        Decimal(str(latest_snapshot["debt_cycle_score"]))
                        / Decimal("100")
                    ),
                    "savings_behaviour": max(
                        Decimal("0"),
                        Decimal(str(latest_snapshot["savings_discipline_score"])),
                    ),
                    "resilience": Decimal(str(latest_snapshot["resilience_index"])),
                    "lifestyle_control": Decimal("1")
                    - min(
                        Decimal("1"),
                        max(
                            Decimal("0"),
                            Decimal(str(latest_snapshot["lifestyle_inflation_rate"])),
                        ),
                    ),
                },
                snapshot_date=latest_snapshot["snapshot_date"],
                version=latest_snapshot["version"],
            )

            # Create debt health response
            debt_health = DebtHealthResponse(
                foir=Decimal("0.4"),  # Simplified - would compute from latest data
                credit_dependency_ratio=Decimal(
                    str(latest_snapshot["credit_dependency_ratio"])
                ),
                debt_cycle_score=latest_snapshot["debt_cycle_score"],
                credit_revolver_ratio=Decimal(
                    str(latest_snapshot["credit_revolver_ratio"])
                ),
                band="MODERATE",  # Simplified - would compute from latest data
                snapshot_date=latest_snapshot["snapshot_date"],
            )

            # Create cashflow health response - scores already in 0-100 range from repository
            cashflow_health = CashflowHealthResponse(
                cashflow_stability_index=Decimal(
                    str(latest_snapshot["cashflow_stability_score"])
                ),
                income_stability=Decimal(
                    str(latest_snapshot["income_stability_score"])
                ),
                expense_stability=Decimal(
                    str(latest_snapshot["expense_stability_score"])
                ),
                monthly_surplus_paise=total_income - total_expenses,
                snapshot_date=latest_snapshot["snapshot_date"],
            )

            # Create financial patterns
            financial_patterns = [
                FinancialPattern(
                    pattern_type=p["pattern_type"],
                    pattern_key=p["pattern_key"],
                    strength=Decimal(str(p["strength_bps"])) / Decimal("10000"),
                    transaction_count=p["transaction_count"],
                    total_amount_paise=p["total_amount_paise"],
                    first_observed=p["first_observed"],
                    last_observed=p["last_observed"],
                )
                for p in patterns
            ]

            # Compute savings rate
            financial_fees = self._compute_financial_fees(transactions, [])
            savings_rate = compute_true_savings_rate(
                total_income, total_expenses, financial_fees
            )

            # Generate alerts
            alerts = self._generate_alerts(latest_snapshot, financial_patterns)

            return MonthlySummaryResponse(
                period=period,
                wellness_score=wellness_score,
                debt_health=debt_health,
                cashflow_health=cashflow_health,
                top_patterns=financial_patterns,
                savings_rate=savings_rate,
                total_income_paise=total_income,
                total_expenses_paise=total_expenses,
                alerts=alerts,
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error generating monthly summary: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to generate monthly summary: {str(e)}",
            )

    def get_recommendations(
        self,
        household_id: str = "default",
        limit: int = 10,
        severity_filter: str | None = None,
    ) -> RecommendationsResponse:
        """Get financial recommendations based on current behaviour metrics.

        Args:
            household_id: Household identifier (default: "default")
            limit: Maximum number of recommendations to return (default: 10)
            severity_filter: Optional filter for severity (LOW, MEDIUM, HIGH, CRITICAL)

        Returns:
            RecommendationsResponse with triggered recommendations sorted by severity

        Raises:
            NotFoundError: If no snapshot is available
            AppError: If recommendation generation fails
        """
        try:
            # Get latest snapshot for context
            snapshot = self.behaviour_repo.get_latest_snapshot(household_id)
            if not snapshot:
                raise NotFoundError(
                    "No behaviour snapshot available for recommendations"
                )

            # Get transactions for recommendation inputs
            transactions = self.transaction_repo.get_all_transactions()
            credit_cards = self.credit_card_repo.list_cards()
            loans = self.loan_repo.list_loans()

            # Calculate metrics needed for recommendations
            total_income = sum(
                t["amount_paise"] for t in transactions if t["type"] == "credit"
            )
            total_expenses = sum(
                t["amount_paise"] for t in transactions if t["type"] == "debit"
            )

            borrowed_lifestyle_ratio = compute_borrowed_lifestyle_ratio(
                self._compute_credit_funded_expenses(transactions), total_expenses
            )

            foir, _ = compute_foir(
                self._compute_fixed_obligations(loans, credit_cards),
                self._compute_minimum_obligations(loans, credit_cards),
                total_income,
            )

            # Calculate liquidity months
            liquid_assets = self._compute_liquid_assets(
                self.account_repo.get_all_accounts()
            )
            essential_expenses = self._compute_essential_expenses(transactions)
            liquidity_months = (
                int(liquid_assets / essential_expenses) if essential_expenses > 0 else 0
            )

            # Get subscriptions for recommendation input
            subscription_patterns = [
                p
                for p in self.pattern_repo.get_recent_patterns(
                    days=30, household_id=household_id
                )
                if p["pattern_type"] == "SUBSCRIPTION"
            ]
            subscriptions = [
                {
                    "merchant": p["pattern_key"],
                    "avg_amount_paise": p["total_amount_paise"]
                    // max(1, p["transaction_count"]),
                }
                for p in subscription_patterns
            ]

            # Generate recommendations
            from src.engines.recommendation_engine.recommendations import (
                compute_recommendations,
            )

            recommendations = compute_recommendations(
                borrowed_lifestyle_ratio=borrowed_lifestyle_ratio,
                foir=foir,
                liquidity_months=liquidity_months,
                current_subscriptions=subscriptions,
                previous_subscriptions=None,
            )

            # Apply severity filter if provided
            if severity_filter:
                recommendations = [
                    r for r in recommendations if r.severity == severity_filter
                ]

            # Apply limit
            recommendations = recommendations[:limit]

            # Convert to response models
            recommendation_responses = [
                RecommendationResponse(
                    title=r.title,
                    reason=r.reason,
                    metric=r.metric,
                    severity=r.severity,
                    suggested_action=r.suggested_action,
                )
                for r in recommendations
            ]

            return RecommendationsResponse(
                recommendations=recommendation_responses,
                total_count=len(recommendation_responses),
                snapshot_date=snapshot["snapshot_date"],
            )

        except NotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}", exc_info=True)
            raise AppError(
                message=f"Failed to get recommendations: {str(e)}",
            )

    # ============================================================
    # Helper Methods
    # ============================================================

    def _compute_wellness_score(
        self,
        cashflow_stability: Decimal,
        debt_cycle_score: int,
        savings_rate: Decimal,
        resilience_index: Decimal,
        lifestyle_inflation: Decimal,
        credit_revolver_ratio: Decimal,
        foir: Decimal,
    ) -> Decimal:
        """Compute wellness score from components."""
        from src.engines.behaviour_engine.wellness import compute_wellness_score

        return compute_wellness_score(
            cashflow_stability=cashflow_stability,
            debt_cycle_score=debt_cycle_score,
            savings_rate=savings_rate,
            resilience_index=resilience_index,
            lifestyle_inflation=lifestyle_inflation,
            credit_revolver_ratio=credit_revolver_ratio,
            foir=foir,
        )

    def _classify_wellness_band(self, score: Decimal) -> str:
        """Classify wellness score into band."""
        from src.engines.behaviour_engine.wellness import classify_wellness_band

        return classify_wellness_band(score)

    def _compute_financial_fees(
        self, transactions: list[dict[str, Any]], credit_cards: list[dict[str, Any]]
    ) -> int:
        """Compute total financial fees from transactions and credit cards."""
        # Simplified implementation - would use actual fee detection logic
        return sum(
            t["amount_paise"]
            for t in transactions
            if "fee" in t.get("description", "").lower()
            or "interest" in t.get("description", "").lower()
        )

    def _compute_credit_funded_expenses(
        self, transactions: list[dict[str, Any]]
    ) -> int:
        """Compute credit-funded expenses from transactions."""
        # Simplified implementation - would use actual credit detection logic
        return sum(
            t["amount_paise"]
            for t in transactions
            if t["type"] == "debit" and "credit" in t.get("description", "").lower()
        )

    def _get_monthly_incomes(self, transactions: list[dict[str, Any]]) -> list[int]:
        """Extract monthly income values from transactions."""
        monthly_incomes: dict[str, int] = {}
        for t in transactions:
            if t["type"] == "credit":
                month_key = t["date_iso"][:7]  # YYYY-MM
                monthly_incomes[month_key] = (
                    monthly_incomes.get(month_key, 0) + t["amount_paise"]
                )

        return list(monthly_incomes.values())

    def _get_monthly_expenses(self, transactions: list[dict[str, Any]]) -> list[int]:
        """Extract monthly expense values from transactions."""
        monthly_expenses: dict[str, int] = {}
        for t in transactions:
            if t["type"] == "debit":
                month_key = t["date_iso"][:7]  # YYYY-MM
                monthly_expenses[month_key] = (
                    monthly_expenses.get(month_key, 0) + t["amount_paise"]
                )

        return list(monthly_expenses.values())

    def _compute_salary_dependence(self, transactions: list[dict[str, Any]]) -> Decimal:
        """Compute salary dependence ratio from transactions."""
        # Classify income sources
        salary_income = 0
        true_income = 0

        for t in transactions:
            if t["type"] == "credit":
                category, _ = classify_income_source(t)
                if category in {"salary", "business", "investment"}:
                    true_income += t["amount_paise"]
                    if category == "salary":
                        salary_income += t["amount_paise"]

        if true_income == 0:
            return Decimal("0")

        return Decimal(str(salary_income)) / Decimal(str(true_income))

    def _compute_fixed_obligations(
        self, loans: list[dict[str, Any]], credit_cards: list[dict[str, Any]]
    ) -> int:
        """Compute total fixed obligations from loans and credit cards."""
        loan_obligations = sum(loan.get("emi_paise", 0) for loan in loans)
        card_obligations = sum(self._compute_minimum_due(card) for card in credit_cards)
        return int(loan_obligations) + int(card_obligations)

    def _compute_minimum_obligations(
        self, loans: list[dict[str, Any]], credit_cards: list[dict[str, Any]]
    ) -> int:
        """Compute minimum obligations (minimum due amounts)."""
        loan_minimums = sum(loan.get("minimum_due_paise", 0) for loan in loans)
        card_minimums = sum(self._compute_minimum_due(card) for card in credit_cards)
        return int(loan_minimums) + int(card_minimums)

    def _compute_minimum_due(self, credit_card: dict[str, Any]) -> int:
        """Compute minimum due for a credit card."""
        limit = credit_card.get("credit_limit_paise", 0)
        if isinstance(limit, Decimal):
            return int(limit * Decimal("0.05"))  # 5% of limit
        return int(limit * 0.05) if limit else 0

    def _compute_revolving_balance(self, credit_cards: list[dict[str, Any]]) -> int:
        """Compute total revolving balance from credit cards."""
        return sum(card.get("outstanding_paise", 0) for card in credit_cards)

    def _count_credit_advances(self, transactions: list[dict[str, Any]]) -> int:
        """Count credit advances from transactions."""
        return sum(
            1
            for t in transactions
            if t["type"] == "credit" and "loan" in t.get("description", "").lower()
        )

    def _count_revolving_months(self, credit_cards: list[dict[str, Any]]) -> int:
        """Count months with revolving credit usage."""
        return sum(1 for card in credit_cards if card.get("outstanding_paise", 0) > 0)

    def _compute_debt_trend(self, loans: list[dict[str, Any]]) -> Decimal:
        """Compute debt increase trend from loans."""
        if not loans:
            return Decimal("0")

        # Would compare with previous period in real implementation
        return Decimal("0.1")  # Simplified

    def _compute_liquid_assets(self, accounts: list[dict[str, Any]]) -> int:
        """Compute total liquid assets from accounts."""
        return sum(
            acc["balance_paise"]
            for acc in accounts
            if acc["account_type"] in {"savings", "current"}
        )

    def _compute_essential_expenses(self, transactions: list[dict[str, Any]]) -> int:
        """Compute essential monthly expenses from transactions."""
        essential_categories = {"rent", "utilities", "groceries", "loan", "insurance"}
        return sum(
            t["amount_paise"]
            for t in transactions
            if t["type"] == "debit"
            and t.get("category", "").lower() in essential_categories
        )

    def _compute_non_essential_expenses(
        self, transactions: list[dict[str, Any]]
    ) -> int:
        """Compute current period non-essential expenses."""
        non_essential_categories = {
            "entertainment",
            "dining",
            "shopping",
            "travel",
            "lifestyle",
        }
        return sum(
            t["amount_paise"]
            for t in transactions
            if t["type"] == "debit"
            and t.get("category", "").lower() in non_essential_categories
        )

    def _compute_previous_non_essential_expenses(
        self, transactions: list[dict[str, Any]]
    ) -> int:
        """Compute previous period non-essential expenses."""
        return self._compute_non_essential_expenses(transactions)

    def _compute_subscription_burn_rate(
        self, transactions: list[dict[str, Any]]
    ) -> Decimal:
        """Compute subscription burn rate from transactions."""
        subscription_keywords = {"subscription", "membership", "monthly fee"}
        subscription_expenses = sum(
            t["amount_paise"]
            for t in transactions
            if t["type"] == "debit"
            and any(
                keyword in t.get("description", "").lower()
                for keyword in subscription_keywords
            )
        )

        total_expenses = sum(
            t["amount_paise"] for t in transactions if t["type"] == "debit"
        )
        if total_expenses == 0:
            return Decimal("0")

        return Decimal(str(subscription_expenses)) / Decimal(str(total_expenses))

    def _compute_discretionary_spending_ratio(
        self, transactions: list[dict[str, Any]]
    ) -> Decimal:
        """Compute discretionary spending ratio."""
        discretionary_categories = {"entertainment", "dining", "shopping", "travel"}
        discretionary_expenses = sum(
            t["amount_paise"]
            for t in transactions
            if t["type"] == "debit"
            and t.get("category", "").lower() in discretionary_categories
        )

        total_expenses = sum(
            t["amount_paise"] for t in transactions if t["type"] == "debit"
        )
        if total_expenses == 0:
            return Decimal("0")

        return Decimal(str(discretionary_expenses)) / Decimal(str(total_expenses))

    def _compute_impulse_transaction_ratio(
        self, transactions: list[dict[str, Any]]
    ) -> Decimal:
        """Compute impulse transaction ratio."""
        impulse_transactions = detect_impulse_transactions(transactions)
        if not transactions:
            return Decimal("0")

        return Decimal(str(len(impulse_transactions))) / Decimal(str(len(transactions)))

    def _compute_lifestyle_creep_index(
        self, transactions: list[dict[str, Any]]
    ) -> Decimal:
        """Compute lifestyle creep index from transactions."""
        from src.engines.behaviour_engine.lifestyle import compute_lifestyle_creep_index

        monthly_discretionary = self._get_monthly_discretionary_spending(transactions)
        return compute_lifestyle_creep_index(monthly_discretionary)

    def _get_monthly_discretionary_spending(
        self, transactions: list[dict[str, Any]]
    ) -> list[int]:
        """Extract monthly discretionary spending from transactions."""
        monthly_discretionary: dict[str, int] = {}
        discretionary_categories = {"entertainment", "dining", "shopping", "travel"}

        for t in transactions:
            if (
                t["type"] == "debit"
                and t.get("category", "").lower() in discretionary_categories
            ):
                month_key = t["date_iso"][:7]  # YYYY-MM
                monthly_discretionary[month_key] = (
                    monthly_discretionary.get(month_key, 0) + t["amount_paise"]
                )

        return list(monthly_discretionary.values())

    def _generate_alerts(
        self, snapshot: dict[str, Any], patterns: list[FinancialPattern]
    ) -> list[str]:
        """Generate financial alerts from snapshot and patterns."""
        alerts: list[str] = []
        wellness_score = Decimal(str(snapshot["wellness_score"]))

        # Wellness alerts
        if wellness_score < Decimal("25"):
            alerts.append("Critical financial health - immediate action required")
        elif wellness_score < Decimal("50"):
            alerts.append("Financial health at risk - review spending and debt")

        # Debt alerts
        debt_cycle_score = snapshot["debt_cycle_score"]
        if debt_cycle_score > 70:
            alerts.append("High debt cycle score - reduce credit dependence")
        elif debt_cycle_score > 50:
            alerts.append("Elevated debt cycle score - monitor credit usage")

        # Pattern alerts
        for pattern in patterns:
            if pattern.strength > Decimal("0.7") and pattern.pattern_type == "IMPULSE":
                alerts.append(
                    f"High impulse spending detected for {pattern.pattern_key}"
                )
            elif (
                pattern.strength > Decimal("0.8")
                and pattern.pattern_type == "SUBSCRIPTION"
            ):
                alerts.append(
                    f"High subscription spending detected for {pattern.pattern_key}"
                )

        return alerts
