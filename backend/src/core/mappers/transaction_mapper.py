"""
Transaction Mapper
==================

Transforms transaction domain objects into TransactionDTO instances.
This is the ONLY location where transaction API responses are constructed.
"""

from typing import Any

from src.core.domain.money import Money
from src.core.dtos.transaction_dto import (
    CategorySummaryDTO,
    MoneyDTO,
    TransactionDTO,
    TransactionListResponse,
)


class TransactionMapper:
    """
    Mapper for transaction domain objects to DTOs.

    Responsibilities:
    - Transform transaction data to TransactionDTO
    - Add backward compatibility fields (_rupees)
    - Ensure all monetary fields have explicit units (_paise suffix)
    """

    @staticmethod
    def to_dto(
        txn_id: str,
        date: str,
        description: str,
        amount: Money,
        balance: Money | None,
        type: str,
        category: str,
        subcategory: str | None,
        bank: str | None,
        member: str | None,
        statement_file: str | None = None,
    ) -> TransactionDTO:
        """
        Convert transaction data to TransactionDTO.

        Args:
            txn_id: Unique transaction identifier
            date: Transaction date (ISO format)
            description: Transaction description
            amount: Money instance for transaction amount
            balance: Money instance for running balance (optional)
            type: Transaction type (debit/credit)
            category: Transaction category
            subcategory: Transaction subcategory (optional)
            bank: Bank name (optional)
            member: Member name (optional)
            statement_file: Statement file name for import tracking (optional)

        Returns:
            TransactionDTO instance
        """
        return TransactionDTO(
            id=txn_id,
            date=date,
            description=description,
            amount=MoneyDTO(paise=amount.paise, rupees=amount.to_rupees()),
            balance=(
                MoneyDTO(paise=balance.paise, rupees=balance.to_rupees())
                if balance
                else None
            ),
            type=type,
            category=category,
            subcategory=subcategory,
            bank=bank,
            member=member,
            statement_file=statement_file,
        )

    @staticmethod
    def to_list_response(
        transactions: list[dict[str, Any]],
        total: int,
        limit: int,
        offset: int,
    ) -> TransactionListResponse:
        """
        Convert list of transaction dictionaries to TransactionListResponse.

        Args:
            transactions: List of transaction dicts from database/engine
            total: Total number of transactions
            limit: Number of transactions per page
            offset: Offset for pagination

        Returns:
            TransactionListResponse instance
        """
        transaction_dtos = []

        for txn in transactions:
            # Extract fields from database row
            txn_id = txn.get("id", "")
            date = txn.get("date", "")
            description = txn.get("description", "")
            amount_paise = txn.get("amount_paise", 0)
            balance_paise = txn.get("balance_paise")
            type_val = txn.get("type", "") or "debit"
            category = txn.get("category", "Uncategorized")
            subcategory = txn.get("subcategory")
            bank = txn.get("bank")
            member = txn.get("member")
            statement_file = txn.get("statement_file")

            # Create Money instances
            amount = Money(amount_paise)
            balance = Money(balance_paise) if balance_paise is not None else None

            # Convert to DTO
            dto = TransactionMapper.to_dto(
                txn_id=txn_id,
                date=date,
                description=description,
                amount=amount,
                balance=balance,
                type=type_val,
                category=category,
                subcategory=subcategory,
                bank=bank,
                member=member,
                statement_file=statement_file,
            )
            transaction_dtos.append(dto)

        return TransactionListResponse(
            transactions=transaction_dtos, total=total, limit=limit, offset=offset
        )

    @staticmethod
    def to_category_summary(
        category: str,
        amount_paise: int,
        count: int,
        percentage: float,
    ) -> CategorySummaryDTO:
        """
        Convert category summary data to CategorySummaryDTO.

        Args:
            category: Category name
            amount_paise: Total amount in paise
            count: Number of transactions
            percentage: Percentage of total (0-100)

        Returns:
            CategorySummaryDTO instance
        """
        amount = Money(amount_paise)
        return CategorySummaryDTO(
            category=category,
            amount=MoneyDTO(paise=amount.paise, rupees=amount.to_rupees()),
            count=count,
            percentage=percentage,
        )
