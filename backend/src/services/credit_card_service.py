"""Credit Card Service - Orchestration layer for credit card operations.

Coordinates repositories and credit_card_engine to implement business logic.
No direct database access - uses repositories only.
"""

from datetime import date
from typing import Any

from src.engines.credit_card_engine import (
    compute_available_credit,
    compute_card_foreclosure,
    compute_due_date,
    compute_emi_conversion,
    compute_financial_metrics,
    compute_minimum_due,
    compute_next_statement_date,
    compute_outstanding,
    compute_utilization,
)
from src.models.credit_card_emi import EmiConversionResponse
from src.models.credit_card_foreclosure import ForeclosureResponse
from src.repositories.credit_card_repository import CreditCardRepository
from src.repositories.credit_card_statement_repository import CreditCardStatementRepository


class CreditCardService:
    """Orchestrates credit card calculation and persistence logic.

    Delegates calculations to credit_card_engine (pure functions).
    Delegates persistence to repositories.
    """

    def __init__(self, db_path: str | None = None) -> None:
        self.card_repo = CreditCardRepository(db_path)
        self.statement_repo = CreditCardStatementRepository(db_path)

    # ============================================================
    # Credit Card CRUD Operations
    # ============================================================

    def get_card(self, card_id: str) -> dict[str, Any]:
        """Get credit card details."""
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")
        return card

    def list_cards(self, account_id: str | None = None) -> list[dict[str, Any]]:
        """Get all active credit cards."""
        return self.card_repo.list_cards(account_id)

    def create_card(
        self,
        card_id: str,
        account_id: str,
        name: str,
        bank: str,
        credit_limit_paise: int,
        interest_rate_bps: int,
        card_last4: str | None = None,
        annual_fee_paise: int = 0,
        billing_day: int | None = None,
        due_day_offset: int = 21,
        notes: str | None = None,
    ) -> str:
        """Create a new credit card record."""
        return self.card_repo.create_card(
            card_id=card_id,
            account_id=account_id,
            name=name,
            bank=bank,
            credit_limit_paise=credit_limit_paise,
            interest_rate_bps=interest_rate_bps,
            card_last4=card_last4,
            annual_fee_paise=annual_fee_paise,
            billing_day=billing_day,
            due_day_offset=due_day_offset,
            notes=notes,
        )

    def update_card(
        self,
        card_id: str,
        **kwargs: str | int | float | None,
    ) -> dict[str, Any] | None:
        """Update credit card fields."""
        return self.card_repo.update_card(card_id, **kwargs)

    def deactivate_card(self, card_id: str) -> bool:
        """Soft delete a credit card."""
        return self.card_repo.deactivate_card(card_id)

    # ============================================================
    # Statement Operations
    # ============================================================

    def generate_statement(
        self,
        card_id: str,
        statement_date_str: str,
    ) -> dict[str, Any]:
        """Generate a new statement for a credit card.

        1. Get card from repo
        2. Calculate outstanding via engine
        3. Calculate minimum due via engine
        4. Calculate due date via engine
        5. Persist statement in transaction
        6. Return statement

        Args:
            card_id: The credit card ID.
            statement_date_str: Statement date as ISO 8601 string.

        Returns:
            The created statement as a dict.
        """
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")

        statement_date = date.fromisoformat(statement_date_str)

        # Calculate due date using engine (fixed day offset)
        due_day_offset = card.get("due_day_offset", 21)
        due_date = compute_due_date(statement_date, due_day_offset)

        # Calculate outstanding (uses stored values; service layer
        # would aggregate from transactions in a full implementation)
        total_spend = card.get("total_spend_paise", 0)
        total_emi = card.get("total_emi_paise", 0)
        total_fees = card.get("annual_fee_paise", 0)
        total_payments = 0  # Payments from current cycle

        outstanding_paise = compute_outstanding(
            total_spend_paise=total_spend,
            total_emi_paise=total_emi,
            total_fees_paise=total_fees,
            total_payments_paise=total_payments,
        )

        # Calculate minimum due using engine
        minimum_due_paise = compute_minimum_due(
            total_outstanding_paise=outstanding_paise,
            min_due_pct_bps=500,  # 5% default
            floor_paise=10000,    # ₹100 floor
        )

        # Persist statement in transaction
        stmt_id = self.statement_repo.create_statement(
            card_id=card_id,
            statement_date=statement_date_str,
            due_date=due_date.isoformat(),
            total_outstanding_paise=outstanding_paise,
            minimum_due_paise=minimum_due_paise,
            interest_charged_paise=0,
        )

        statement = self.statement_repo.get_statement(stmt_id)
        if not statement:
            raise RuntimeError(f"Failed to retrieve created statement {stmt_id}")

        return statement

    def list_statements(
        self,
        card_id: str,
        limit: int = 12,
    ) -> list[dict[str, Any]]:
        """Get statement history for a card."""
        return self.statement_repo.list_statements(card_id, limit)

    def record_payment(
        self,
        card_id: str,
        amount_paise: int,
        payment_date: str,
    ) -> dict[str, Any]:
        """Record a payment on the latest open statement."""
        statement = self.statement_repo.get_latest_open_statement(card_id)
        if not statement:
            raise ValueError(f"No open statement found for card {card_id}")

        success = self.statement_repo.update_payment(
            statement_id=statement["id"],
            payment_date=payment_date,
            amount_paise=amount_paise,
        )
        if not success:
            raise RuntimeError(f"Failed to update payment on statement {statement['id']}")

        updated = self.statement_repo.get_statement(statement["id"])
        return updated or statement

    # ============================================================
    # Calculation Operations (Engine Delegation)
    # ============================================================

    def calculate_outstanding(self, card_id: str) -> int:
        """Calculate current outstanding balance."""
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")

        return compute_outstanding(
            total_spend_paise=card.get("total_spend_paise", 0),
            total_emi_paise=card.get("total_emi_paise", 0),
            total_fees_paise=card.get("annual_fee_paise", 0),
            total_payments_paise=0,
        )

    def calculate_utilization(self, card_id: str) -> dict[str, int]:
        """Calculate credit utilization and available credit."""
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")

        outstanding = self.calculate_outstanding(card_id)
        credit_limit = card["credit_limit_paise"]

        return {
            "utilization_bps": compute_utilization(outstanding, credit_limit),
            "available_credit_paise": compute_available_credit(credit_limit, outstanding),
        }

    def convert_to_emi(
        self,
        card_id: str,
        amount_paise: int,
        tenure_months: int,
        annual_rate_bps: int | None = None,
    ) -> EmiConversionResponse:
        """Convert a purchase to EMI.

        Delegates to credit_card_engine which delegates to loan_engine.
        No EMI formula duplication.

        Args:
            card_id: The credit card ID.
            amount_paise: Amount to convert in paise.
            tenure_months: EMI tenure in months.
            annual_rate_bps: Optional rate override; uses card rate if None.

        Returns:
            EmiConversionResponse with breakdown.
        """
        if annual_rate_bps is None:
            card = self.card_repo.get_card(card_id)
            if not card:
                raise ValueError(f"Credit card {card_id} not found")
            annual_rate_bps = card["interest_rate_bps"]

        result = compute_emi_conversion(
            amount_paise=amount_paise,
            annual_rate_bps=annual_rate_bps,
            tenure_months=tenure_months,
        )

        return EmiConversionResponse(
            emi_paise=result["emi_paise"],
            total_interest_paise=result["total_interest_paise"],
            total_repayment_paise=result["total_repayment_paise"],
            monthly_interest_paise=result["monthly_interest_paise"],
        )

    def quote_foreclosure(
        self,
        card_id: str,
        remaining_months: int,
        penalty_bps: int = 0,
    ) -> ForeclosureResponse:
        """Quote foreclosure payoff for a credit card EMI.

        Delegates to credit_card_engine which delegates to loan_engine.

        Args:
            card_id: The credit card ID.
            remaining_months: Remaining EMI months.
            penalty_bps: Prepayment penalty in basis points.

        Returns:
            ForeclosureResponse with payoff breakdown.
        """
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")

        outstanding = self.calculate_outstanding(card_id)
        rate_bps = card["interest_rate_bps"]

        result = compute_card_foreclosure(
            outstanding_paise=outstanding,
            annual_rate_bps=rate_bps,
            remaining_months=remaining_months,
            penalty_bps=penalty_bps,
        )

        return ForeclosureResponse(
            foreclosure_amount_paise=result["foreclosure_amount_paise"],
            outstanding_paise=result["outstanding_paise"],
            accrued_interest_paise=result["accrued_interest_paise"],
            penalty_paise=result["penalty_paise"],
        )

    def get_financial_metrics(self, card_id: str) -> dict[str, int]:
        """Get core financial metrics for a credit card."""
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")

        outstanding = self.calculate_outstanding(card_id)

        return compute_financial_metrics(
            outstanding_paise=outstanding,
            credit_limit_paise=card["credit_limit_paise"],
            annual_rate_bps=card["interest_rate_bps"],
            total_interest_paid_paise=0,
        )

    def get_next_statement_date(self, card_id: str) -> str:
        """Get the next expected statement date for a card."""
        card = self.card_repo.get_card(card_id)
        if not card:
            raise ValueError(f"Credit card {card_id} not found")

        billing_day = card.get("billing_day")
        if billing_day is None:
            raise ValueError(f"Card {card_id} has no billing_day configured")

        latest = self.statement_repo.get_latest_statement(card_id)
        last_date = None
        if latest:
            last_date = date.fromisoformat(latest["statement_date"])

        next_date = compute_next_statement_date(
            billing_day=billing_day,
            reference_date=date.today(),
            last_statement_date=last_date,
        )

        return next_date.isoformat()

