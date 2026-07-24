"""Cashflow domain repository."""
import json
from typing import Any

from src.repositories.base import BaseRepository
from src.repositories.financial_event_repository import FinancialEventRepository


class CashflowRepository(BaseRepository):
    """Repository for cashflow operations."""

    def get_monthly_cashflow(
        self,
        months: int = 6,
        member: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Returns month-by-month income and expense aggregation.
        All monetary values in paise (INTEGER).
        Uses date_iso for proper month grouping.
        This is the LEGACY method - see get_true_monthly_cashflow for adjusted values.
        """
        with self._get_conn() as conn:
            conditions = ["t.date_iso IS NOT NULL"]
            params = []

            if member and member != "All":
                conditions.append("t.member = ?")
                params.append(member)

            where = "WHERE " + " AND ".join(conditions)

            sql = f"""
                SELECT
                    substr(t.date_iso, 1, 7) as month_key,
                    SUM(CASE WHEN t.type = 'credit' THEN t.amount_paise ELSE 0 END) as income_paise,
                    SUM(CASE WHEN t.type = 'debit' THEN t.amount_paise ELSE 0 END) as expense_paise,
                    COUNT(*) as transaction_count
                FROM transactions t
                {where}
                GROUP BY substr(t.date_iso, 1, 7)
                ORDER BY month_key ASC
            """

            cur = conn.execute(sql, params)
            rows = [dict(row) for row in cur.fetchall()]
        return rows

    def get_true_monthly_cashflow(
        self,
        months: int = 12,
        household_id: str = "primary",
        owner_id: str | None = "self",
    ) -> list[dict[str, Any]]:
        """
        Returns month-by-month TRUE income and expense aggregation.
        Adjusted for artificial income and transfers via financial_events.

        Adjustments applied:
        - credit_card_cash_advance: credit leg excluded from income,
          fee included as expense (not the full debit amount)
        - transfer_internal: both legs excluded from income AND expense
        - emi_payment: only expense_paise (interest) counted as expense,
          NOT the full EMI debit amount

        Args:
            months: Number of months to look back (default: 12)
            household_id: Household identifier (default: "primary")
            owner_id: Owner filter - "self" for individual, None for household-wide

        Returns:
            List of month dicts with month_key, income_paise, expense_paise,
            surplus_paise, and adjustments_applied.
        """
        event_repo = FinancialEventRepository(self.db_path)

        with self._get_conn() as conn:
            # Build conditions for household/owner filtering
            # Join transactions to accounts for proper scoping
            conditions = ["t.date_iso IS NOT NULL"]
            params: list[Any] = []

            if owner_id == "self":
                # Filter for self owner within household
                conditions.append("a.owner_id = ?")
                params.append("self")
            # If owner_id is None, get all accounts in household

            conditions.append("a.household_id = ?")
            params.append(household_id)

            where = "WHERE " + " AND ".join(conditions)

            # Get raw monthly aggregation with proper scoping
            sql = f"""
                SELECT
                    substr(t.date_iso, 1, 7) as month_key,
                    SUM(CASE WHEN t.type = 'credit' THEN t.amount_paise ELSE 0 END) as raw_income_paise,
                    SUM(CASE WHEN t.type = 'debit' THEN t.amount_paise ELSE 0 END) as raw_expense_paise
                FROM transactions t
                JOIN accounts a ON CAST(t.account_id AS INTEGER) = a.id
                {where}
                GROUP BY substr(t.date_iso, 1, 7)
                ORDER BY month_key ASC
            """

            cur = conn.execute(sql, params)
            raw_monthly = {row["month_key"]: dict(row) for row in cur.fetchall()}

        # Get all months to process
        all_months = sorted(raw_monthly.keys())
        results: list[dict[str, Any]] = []

        for month_key in all_months:
            raw_income = raw_monthly[month_key].get("raw_income_paise", 0) or 0
            raw_expense = raw_monthly[month_key].get("raw_expense_paise", 0) or 0

            # Fetch financial events for this month
            events = event_repo.get_events_for_month(
                month_bucket=month_key,
                household_id=household_id,
                owner_id=owner_id,
            )

            adjustments: list[dict[str, Any]] = []

            for event in events:
                event_type = event.get("event_type", "")
                txn_ids = event.get("transaction_ids", "[]")

                # Parse transaction_ids JSON
                try:
                    txn_id_list = json.loads(txn_ids) if isinstance(txn_ids, str) else txn_ids
                except (json.JSONDecodeError, TypeError):
                    txn_id_list = []

                # credit_card_cash_advance adjustments
                if event_type == "credit_card_cash_advance":
                    liability_change = int(event.get("liability_change_paise", 0) or 0)
                    asset_change = int(event.get("asset_change_paise", 0) or 0)
                    expense = int(event.get("expense_paise", 0) or 0)

                    # Exclude asset change (credit leg) from income
                    if asset_change > 0:
                        raw_income -= asset_change
                        adjustments.append({
                            "event_id": event.get("id"),
                            "type": "artificial_income_exclusion",
                            "amount_paise": asset_change,
                            "transaction_ids": txn_id_list,
                        })

                    # Replace full debit amount with just fee in expense
                    # The raw_expense already includes the full debit (liability_change)
                    # We need to adjust: remove the principle, keep only the fee
                    if liability_change > 0:
                        raw_expense -= (liability_change - expense)  # Keep only fee
                        adjustments.append({
                            "event_id": event.get("id"),
                            "type": "cash_advance_fee_adjustment",
                            "amount_paise": expense,
                            "transaction_ids": txn_id_list,
                        })

                # transfer_internal adjustments
                elif event_type == "transfer_internal":
                    # Both legs should be excluded
                    # Fetch actual transaction amounts for adjustment
                    for txn_id in txn_id_list:
                        txn_row = None
                        with self._get_conn() as check_conn:
                            txn_row = check_conn.execute(
                                "SELECT amount_paise, type FROM transactions WHERE id = ?",
                                (txn_id,),
                            ).fetchone()
                        if txn_row:
                            txn_amount = int(txn_row["amount_paise"] or 0)
                            txn_type = txn_row["type"]
                            if txn_type == "credit":
                                raw_income -= txn_amount
                            elif txn_type == "debit":
                                raw_expense -= txn_amount
                            adjustments.append({
                                "event_id": event.get("id"),
                                "type": "transfer_exclusion",
                                "amount_paise": txn_amount,
                                "transaction_type": txn_type,
                                "transaction_id": txn_id,
                            })

                # emi_payment adjustments
                elif event_type == "emi_payment":
                    expense = int(event.get("expense_paise", 0) or 0)
                    # The raw_expense already includes the full EMI debit
                    # Fetch the full EMI amount from the transaction
                    emi_amount = 0
                    if txn_id_list:
                        with self._get_conn() as check_conn:
                            txn_row = check_conn.execute(
                                "SELECT amount_paise FROM transactions WHERE id = ?",
                                (txn_id_list[0],),
                            ).fetchone()
                            if txn_row:
                                emi_amount = int(txn_row["amount_paise"] or 0)

                    # Adjust: remove full EMI, add back just interest
                    if emi_amount > 0:
                        raw_expense -= (emi_amount - expense)
                        adjustments.append({
                            "event_id": event.get("id"),
                            "type": "emi_interest_only",
                            "amount_paise": expense,
                            "transaction_ids": txn_id_list,
                        })

            # Calculate surplus
            surplus = raw_income - raw_expense

            results.append({
                "month_key": month_key,
                "income_paise": raw_income,
                "expense_paise": raw_expense,
                "surplus_paise": surplus,
                "adjustments_applied": adjustments,
            })

        return results

