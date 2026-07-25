"""Cards and statements endpoints."""

from collections import defaultdict
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from src.common import format_inr, parse_date
from src.repositories import StatementRepository
from src.services.statement_service import StatementService

router = APIRouter(prefix="/api", tags=["cards", "statements"])


@router.get("/statements")
def get_statements() -> list[dict[str, Any]]:
    """Get all statements with metadata."""
    try:
        repo = StatementRepository()
        raw = repo.get_all_statements_with_metadata()

        statements = []
        for stmt in raw:
            total_debit = float(stmt.get("total_debit") or 0)
            total_credit = float(stmt.get("total_credit") or 0)
            total_due = float(stmt.get("total_amount_due") or 0)
            min_due = float(stmt.get("minimum_amount_due") or 0)
            diff = float(stmt.get("validation_difference") or 0)
            extracted_net = total_debit - total_credit

            validation_status = stmt.get("validation_status") or "pending"
            badge_text = (
                "✅ Exact Match"
                if validation_status == "exact_match"
                else (
                    f"⚠️ Close (₹{diff:,.0f} off)"
                    if validation_status == "close_match"
                    else (
                        f"❌ Mismatch (₹{diff:,.0f})"
                        if validation_status == "mismatch"
                        else (
                            "— No Data"
                            if validation_status == "no_metadata"
                            else "⏳ Pending"
                        )
                    )
                )
            )
            badge_color = (
                "green"
                if validation_status == "exact_match"
                else (
                    "amber"
                    if validation_status == "close_match"
                    else "red"
                    if validation_status == "mismatch"
                    else "gray"
                )
            )

            statements.append(
                {
                    "id": stmt.get("id"),
                    "bank": stmt.get("bank"),
                    "file_name": stmt.get("file_name"),
                    "card_last4": stmt.get("card_last4"),
                    "card_display": (
                        f"****{stmt.get('card_last4')}"
                        if stmt.get("card_last4")
                        else ""
                    ),
                    "period_from": stmt.get("statement_period_from"),
                    "period_to": stmt.get("statement_period_to"),
                    "period_display": (
                        f"{stmt.get('statement_period_from')} – {stmt.get('statement_period_to')}"
                        if stmt.get("statement_period_from")
                        else ""
                    ),
                    "transaction_count": stmt.get("transaction_count", 0),
                    "total_debit": total_debit,
                    "total_credit": total_credit,
                    "total_debit_display": format_inr(total_debit),
                    "total_credit_display": format_inr(total_credit),
                    "total_due": total_due,
                    "total_due_display": format_inr(total_due) if total_due else "—",
                    "extracted_net": extracted_net,
                    "extracted_net_display": format_inr(extracted_net),
                    "min_due_display": format_inr(min_due) if min_due else "",
                    "due_date": stmt.get("payment_due_date"),
                    "validation_status": validation_status,
                    "validation_difference": diff,
                    "badge_text": badge_text,
                    "badge_color": badge_color,
                }
            )

        return statements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cards")
def get_cards() -> dict[str, Any]:
    """
    Returns credit cards with their latest statement summary.
    Groups statements by card_last4 and bank.
    Returns one entry per unique card with latest statement data.
    """
    try:
        repo = StatementRepository()
        raw = repo.get_all_statements_with_metadata()

        # Group statements by (bank, card_last4)
        card_groups: dict[tuple[str, str], list[Any]] = defaultdict(list)
        for stmt in raw:
            bank = stmt.get("bank") or "Unknown"
            card_last4 = stmt.get("card_last4") or "Unknown"
            key = (bank, card_last4)
            card_groups[key].append(stmt)

        cards = []
        total_outstanding = 0.0
        total_credit_limit = 0.0

        for (bank, card_last4), statements in card_groups.items():
            # Sort by imported_at descending to get most recent
            statements_sorted = sorted(
                statements, key=lambda s: s.get("imported_at") or "", reverse=True
            )
            latest = statements_sorted[0]

            # Get values from latest statement
            credit_limit = float(latest.get("credit_limit") or 0)
            current_outstanding = float(latest.get("total_amount_due") or 0)
            minimum_due = float(latest.get("minimum_amount_due") or 0)
            payment_due_date = latest.get("payment_due_date")
            statement_date = latest.get("statement_date")
            bill_cycle_start = latest.get("bill_cycle_start")
            bill_cycle_end = latest.get("bill_cycle_end")
            validation_status = latest.get("validation_status") or "pending"

            # Compute utilization
            utilization_percent = 0.0
            if credit_limit > 0:
                utilization_percent = round(
                    (current_outstanding / credit_limit) * 100, 1
                )

            # Compute days until due
            days_until_due = None
            if payment_due_date:
                try:
                    due_dt = parse_date(payment_due_date)
                    if due_dt:
                        today = datetime.now()
                        days_until_due = (due_dt - today).days
                except Exception:
                    pass

            # Compute payment status
            if days_until_due is None:
                payment_status = "unknown"
            elif days_until_due < 0:
                payment_status = "overdue"
            elif days_until_due <= 3:
                payment_status = "due_soon"
            elif days_until_due <= 7:
                payment_status = "upcoming"
            else:
                payment_status = "on_track"

            card_id = f"{bank}_{card_last4}"

            cards.append(
                {
                    "card_id": card_id,
                    "bank": bank,
                    "card_last4": card_last4,
                    "credit_limit": credit_limit,
                    "current_outstanding": current_outstanding,
                    "minimum_due": minimum_due,
                    "payment_due_date": payment_due_date,
                    "statement_date": statement_date,
                    "bill_cycle_start": bill_cycle_start,
                    "bill_cycle_end": bill_cycle_end,
                    "utilization_percent": utilization_percent,
                    "days_until_due": days_until_due,
                    "payment_status": payment_status,
                    "validation_status": validation_status,
                    "statement_count": len(statements),
                    "latest_statement_id": latest.get("id"),
                }
            )

            total_outstanding += current_outstanding
            total_credit_limit += credit_limit

        # Sort cards by bank name
        cards.sort(key=lambda c: c.get("bank", ""))

        total_utilization = 0.0
        if total_credit_limit > 0:
            total_utilization = round((total_outstanding / total_credit_limit) * 100, 1)

        return {
            "cards": cards,
            "total_cards": len(cards),
            "total_outstanding": total_outstanding,
            "total_credit_limit": total_credit_limit,
            "total_utilization_percent": total_utilization,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statements/{statement_id}/validate")
def api_validate_statement(
    statement_id: int,
    claimed_balance_paise: int = Query(
        ..., description="Claimed closing balance in paise"
    ),
) -> dict[str, Any]:
    """Validate a statement's closing balance against computed balance."""
    try:
        service = StatementService()
        result = service.validate_statement(statement_id, claimed_balance_paise)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
