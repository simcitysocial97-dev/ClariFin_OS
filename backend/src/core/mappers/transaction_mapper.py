"""
Transaction Mapper
==================

Transforms transaction domain objects into TransactionDTO instances.
This is the ONLY location where transaction API responses are constructed.
"""

from typing import Any

from core.domain.money import Money
from core.dtos.transaction_dto import CategorySummaryDTO, TransactionDTO, TransactionListResponse


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
        category: str,
        subcategory: str | None,
        bank: str,
        transaction_type: str,
        reference_number: str | None = None,
        include_rupees_field: bool = True
    ) -> TransactionDTO:
        """
        Convert transaction data to TransactionDTO.

        Args:
            txn_id: Unique transaction identifier
            date: Transaction date (ISO format)
            description: Transaction description
            amount: Money instance for transaction amount
            balance: Money instance for running balance (optional)
            category: Transaction category
            subcategory: Transaction subcategory (optional)
            bank: Bank name
            transaction_type: Transaction type (debit/credit)
            reference_number: Bank reference number (optional)
            include_rupees_field: If True, include deprecated amount_rupees field

        Returns:
            TransactionDTO instance
        """
        dto_data = {
            "id": txn_id,
            "date": date,
            "description": description,
            "amount_paise": amount.paise,
            "balance_paise": balance.paise if balance else None,
            "category": category,
            "subcategory": subcategory,
            "bank": bank,
            "transaction_type": transaction_type,
            "reference_number": reference_number,
        }

        # TODO: Remove in Phase 2 - backward compatibility
        if include_rupees_field:
            dto_data["amount_rupees"] = amount.to_rupees()

        return TransactionDTO(**dto_data)

    @staticmethod
    def to_list_response(
        transactions: list[dict[str, Any]],
        total: int,
        limit: int,
        offset: int,
        include_rupees_field: bool = True
    ) -> TransactionListResponse:
        """
        Convert list of transaction dictionaries to TransactionListResponse.

        Args:
            transactions: List of transaction dicts from database/engine
            total: Total number of transactions
            limit: Number of transactions per page
            offset: Offset for pagination
            include_rupees_field: If True, include deprecated amount_rupees field

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
            category = txn.get("category", "Uncategorized")
            subcategory = txn.get("subcategory")
            bank = txn.get("bank", "")
            transaction_type = txn.get("type", "debit")
            reference_number = txn.get("reference_number")

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
                category=category,
                subcategory=subcategory,
                bank=bank,
                transaction_type=transaction_type,
                reference_number=reference_number,
                include_rupees_field=include_rupees_field
            )
            transaction_dtos.append(dto)

        return TransactionListResponse(
            transactions=transaction_dtos,
            total=total,
            limit=limit,
            offset=offset
        )

    @staticmethod
    def to_category_summary(
        category: str,
        amount_paise: int,
        count: int,
        percentage: float,
        include_rupees_field: bool = True
    ) -> CategorySummaryDTO:
        """
        Convert category summary data to CategorySummaryDTO.

        Args:
            category: Category name
            amount_paise: Total amount in paise
            count: Number of transactions
            percentage: Percentage of total (0-100)
            include_rupees_field: If True, include deprecated amount_rupees field

        Returns:
            CategorySummaryDTO instance
        """
        dto_data = {
            "category": category,
            "amount_paise": amount_paise,
            "count": count,
            "percentage": percentage,
        }

        # TODO: Remove in Phase 2 - backward compatibility
        if include_rupees_field:
            dto_data["amount_rupees"] = Money(amount_paise).to_rupees()

        return CategorySummaryDTO(**dto_data)
