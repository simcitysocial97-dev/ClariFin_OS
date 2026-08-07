"""Credit Card Mapper

Transforms credit card domain objects into CreditCardDTO instances.
This is the ONLY location where credit card API responses are constructed.
"""

from typing import Any

from src.core.dtos.credit_cards_dto import CreditCardSummaryDTO, StatementDTO


class CreditCardMapper:
    """Mapper for credit card domain objects to DTOs."""

    @staticmethod
    def to_dto(card: dict[str, Any]) -> CreditCardSummaryDTO:
        """Convert credit card data to CreditCardSummaryDTO."""
        return CreditCardSummaryDTO(
            id=str(card["id"]),
            name=card["name"],
            bank=card["bank"],
            card_number_last4=card.get("card_last4", ""),
            credit_limit_paise=card["credit_limit_paise"],
            current_balance_paise=card.get("current_balance_paise", 0),
            available_paise=card["credit_limit_paise"]
            - card.get("current_balance_paise", 0),
            min_due_paise=card.get("min_due_paise", 0),
            total_due_paise=card.get("total_due_paise", 0),
            due_date=card.get("due_date", ""),
            status="active",  # All cards from list_cards are active
            reward_points=card.get("reward_points", 0),
        )

    @staticmethod
    def to_list_dto(cards: list[dict[str, Any]]) -> list[CreditCardSummaryDTO]:
        """Convert list of credit card dicts to list of CreditCardSummaryDTO."""
        return [CreditCardMapper.to_dto(card) for card in cards]

    @staticmethod
    def to_statement_dto(statement: dict[str, Any]) -> StatementDTO:
        """Convert statement data to StatementDTO."""
        return StatementDTO(
            id=str(statement["id"]),
            card_id=str(statement["card_id"]),
            statement_date=statement["statement_date"],
            start_date=statement["start_date"],
            end_date=statement["end_date"],
            due_date=statement["due_date"],
            opening_balance_paise=statement["opening_balance_paise"],
            closing_balance_paise=statement["closing_balance_paise"],
            total_charges_paise=statement["total_charges_paise"],
            total_payments_paise=statement["total_payments_paise"],
            total_credits_paise=statement["total_credits_paise"],
            min_due_paise=statement["min_due_paise"],
            total_due_paise=statement["total_due_paise"],
            interest_charged_paise=statement.get("interest_charged_paise", 0),
            late_fee_paise=statement.get("late_fee_paise", 0),
            is_paid=statement.get("is_paid", False),
        )

    @staticmethod
    def to_statement_list_dto(statements: list[dict[str, Any]]) -> list[StatementDTO]:
        """Convert list of statement dicts to list of StatementDTO."""
        return [
            CreditCardMapper.to_statement_dto(statement) for statement in statements
        ]
