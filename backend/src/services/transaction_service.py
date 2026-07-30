"""Transaction Service - Orchestration layer for transaction analytics and metrics.

Coordinates repository calls and business logic for transaction operations.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any

from src.common import (
    compute_behavioral_insights,
    compute_is_large,
    enrich_transaction,
    format_inr,
    percentage_change,
)
from src.repositories import TransactionRepository


class TransactionService:
    """Service for transaction analytics and metrics."""

    def __init__(self, db_path: str | None = None):
        self.repo = TransactionRepository(db_path)

    def get_transactions(
        self,
        search: str | None = None,
        bank: str | None = "All",
        category: str | None = "All",
        type: str | None = "All",
        member: str | None = "All",
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get transactions as enriched dictionaries."""
        rows = self.repo.get_all()
        return [dict(r) for r in rows]

    def get_overview(
        self,
        exclude_transfers: bool = True,
        member: str | None = "All",
    ) -> dict[str, Any]:
        """Get overview metrics and charts."""
        filters = {}
        if member and member != "All":
            filters["member"] = member

        raw = self.repo.get_all_transactions_with_bank(filters)
        transactions = [enrich_transaction(dict(t)) for t in raw]

        # Get confirmed transfer transaction IDs
        confirmed_transfer_ids = set()
        for debit_id, credit_id in self.repo.get_confirmed_transfer_ids():
            confirmed_transfer_ids.add(debit_id)
            confirmed_transfer_ids.add(credit_id)

        # Filter out transfers if requested
        if exclude_transfers:
            transactions = [
                t
                for t in transactions
                if t.get("category") != "Payments & Transfers"
                and t.get("id") not in confirmed_transfer_ids
            ]

        # Compute metrics
        debit_txns = [t for t in transactions if t.get("type") == "debit"]
        month_keys = sorted(
            {t.get("month_key", "") for t in debit_txns if t.get("month_key")}
        )

        total_spend = sum(t.get("amount", 0) for t in debit_txns)

        this_month = month_keys[-1] if month_keys else ""
        last_month = month_keys[-2] if len(month_keys) >= 2 else ""

        this_month_spend = sum(
            t.get("amount", 0) for t in debit_txns if t.get("month_key") == this_month
        )
        last_month_spend = sum(
            t.get("amount", 0) for t in debit_txns if t.get("month_key") == last_month
        )

        month_change = (
            percentage_change(this_month_spend, last_month_spend)
            if last_month_spend > 0
            else "—"
        )

        # Monthly chart
        monthly: dict[str, Any] = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly[mk] += t.get("amount", 0)

        monthly_chart = [
            {
                "month": datetime.strptime(m, "%Y-%m").strftime("%b %y"),
                "amount": round(monthly[m], 2),
            }
            for m in sorted(monthly.keys())[-12:]
        ]

        # Category chart
        cat_totals: dict[str, Any] = defaultdict(float)
        for t in debit_txns:
            cat_totals[t.get("category", "Uncategorized")] += t.get("amount", 0)

        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        category_chart = [
            {"name": cat, "value": round(amt, 2)} for cat, amt in sorted_cats[:8]
        ]

        # Bank chart
        bank_totals: dict[str, Any] = defaultdict(float)
        for t in debit_txns:
            bank_totals[t.get("bank", "Unknown")] += t.get("amount", 0)

        bank_chart = [
            {"bank": bank, "amount": round(amt, 2)}
            for bank, amt in sorted(
                bank_totals.items(), key=lambda x: x[1], reverse=True
            )
        ]

        # Recent transactions
        recent = sorted(
            transactions, key=lambda t: t.get("parsed_date", ""), reverse=True
        )[:10]
        recent = compute_is_large(recent)

        # Behavioral insights
        insights = compute_behavioral_insights(transactions)

        # Above/below average
        if monthly:
            avg_monthly = sum(monthly.values()) / len(monthly)
            diff = this_month_spend - avg_monthly
            above_below = (
                f"+{format_inr(diff)} above avg"
                if diff > 0
                else f"{format_inr(abs(diff))} below avg"
            )
            above_is_bad = diff > 0
        else:
            above_below = "at average"
            above_is_bad = False

        return {
            "total_spend": total_spend,
            "total_spend_display": format_inr(total_spend),
            "this_month": this_month_spend,
            "this_month_display": format_inr(this_month_spend),
            "last_month": last_month_spend,
            "last_month_display": format_inr(last_month_spend),
            "month_change": month_change,
            "transaction_count": len(transactions),
            "card_count": len({t.get("bank") for t in transactions if t.get("bank")}),
            "months_of_data": len(month_keys),
            "monthly_average": avg_monthly if monthly else 0,
            "monthly_average_display": format_inr(avg_monthly) if monthly else "₹0",
            "above_below_avg": above_below,
            "above_avg_is_bad": above_is_bad,
            "monthly_chart": monthly_chart,
            "category_chart": category_chart,
            "bank_chart": bank_chart,
            "recent_transactions": recent,
            "behavioral_insights": insights,
        }

    def get_categories(
        self,
        exclude_transfers: bool = True,
        member: str | None = "All",
        drill_category: str | None = None,
    ) -> dict[str, Any]:
        """Get category summary and breakdown."""
        filters = {}
        if member and member != "All":
            filters["member"] = member

        raw = self.repo.get_all_transactions_with_bank(filters)
        transactions = [enrich_transaction(dict(t)) for t in raw]

        if exclude_transfers:
            transactions = [
                t for t in transactions if t.get("category") != "Payments & Transfers"
            ]

        # Category summary
        cat_data: dict[str, Any] = defaultdict(lambda: {"amount": 0.0, "count": 0})
        total_debit = 0.0
        for t in transactions:
            if t.get("type") == "debit":
                cat = t.get("category", "Uncategorized")
                cat_data[cat]["amount"] += t.get("amount", 0)
                cat_data[cat]["count"] += 1
                total_debit += t.get("amount", 0)

        summary = [
            {
                "category": cat,
                "amount": round(data["amount"], 2),
                "amount_display": format_inr(data["amount"]),
                "count": data["count"],
                "percentage": (
                    round((data["amount"] / total_debit) * 100, 1)
                    if total_debit > 0
                    else 0
                ),
            }
            for cat, data in sorted(
                cat_data.items(), key=lambda x: x[1]["amount"], reverse=True
            )
        ]

        # Monthly breakdown
        data: dict[str, Any] = defaultdict(lambda: defaultdict(float))
        for t in transactions:
            if t.get("type") == "debit":
                mk = t.get("month_key", "")
                cat = t.get("category", "Uncategorized")
                if mk:
                    data[mk][cat] += t.get("amount", 0)

        top_cats = [
            c
            for c, _ in sorted(
                cat_data.items(), key=lambda x: x[1]["amount"], reverse=True
            )[:6]
        ]
        sorted_months = sorted(data.keys())[-12:]
        monthly_breakdown = []
        for m in sorted_months:
            row = {"month": datetime.strptime(m, "%Y-%m").strftime("%b %y")}
            for cat in top_cats:
                row[cat] = round(data[m].get(cat, 0), 2)
            monthly_breakdown.append(row)

        # Drill transactions
        drill_transactions = []
        if drill_category:
            drill_transactions = [
                t for t in transactions if t.get("category") == drill_category
            ][:50]

        # Uncategorized patterns
        raw_uncat = self.repo.get_uncategorized_patterns(limit=30)
        uncategorized_patterns = [
            {
                "description": p.get("description", ""),
                "count": p.get("count", 0),
                "total_display": format_inr(p.get("total_amount", 0)),
            }
            for p in raw_uncat
        ]

        return {
            "summary": summary,
            "monthly_breakdown": monthly_breakdown,
            "drill_transactions": drill_transactions,
            "uncategorized_patterns": uncategorized_patterns,
        }

    def get_analytics(
        self,
        exclude_transfers: bool = True,
        member: str | None = "All",
    ) -> dict[str, Any]:
        """Get analytics data."""
        filters = {}
        if member and member != "All":
            filters["member"] = member

        raw = self.repo.get_all_transactions_with_bank(filters)
        transactions = [enrich_transaction(dict(t)) for t in raw]

        if exclude_transfers:
            transactions = [
                t for t in transactions if t.get("category") != "Payments & Transfers"
            ]

        debit_txns = [t for t in transactions if t.get("type") == "debit"]

        # Monthly data
        monthly: dict[str, Any] = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly[mk] += t.get("amount", 0)

        sorted_months = sorted(monthly.keys())
        monthly_amounts = [monthly[m] for m in sorted_months]
        avg_monthly = (
            sum(monthly_amounts) / len(monthly_amounts) if monthly_amounts else 0
        )

        # Highest month
        if monthly:
            max_month = max(monthly, key=lambda k: monthly[k])
            highest_month = datetime.strptime(max_month, "%Y-%m").strftime("%b %y")
            highest_month_amount = format_inr(monthly[max_month])
        else:
            highest_month = ""
            highest_month_amount = "₹0"

        # Biggest transaction
        if debit_txns:
            biggest = max(debit_txns, key=lambda t: t.get("amount", 0))
            biggest_transaction = {
                "description": (biggest.get("description") or "")[:40],
                "amount": biggest.get("amount", 0),
                "date": biggest.get("date", ""),
                "bank": biggest.get("bank", ""),
            }
        else:
            biggest_transaction = None

        # Spending trend
        spending_trend = [
            {
                "month": datetime.strptime(m, "%Y-%m").strftime("%b %y"),
                "amount": round(monthly[m], 2),
                "average": round(avg_monthly, 2),
            }
            for m in sorted_months
        ]

        # Day of week
        day_totals: dict[str, Any] = defaultdict(lambda: {"amount": 0.0, "count": 0})
        for t in debit_txns:
            wd = t.get("weekday", "")
            if wd:
                day_totals[wd]["amount"] += t.get("amount", 0)
                day_totals[wd]["count"] += 1

        day_order = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        day_of_week = [
            {
                "day": day[:3],
                "amount": round(day_totals[day]["amount"], 2),
                "count": day_totals[day]["count"],
            }
            for day in day_order
        ]

        # Top merchants
        merchant_data: dict[str, Any] = defaultdict(lambda: {"amount": 0.0, "count": 0})
        for t in debit_txns:
            if t.get("description"):
                desc = (t["description"] or "")[:40]
                merchant_data[desc]["amount"] += t.get("amount", 0)
                merchant_data[desc]["count"] += 1

        sorted_m = sorted(
            merchant_data.items(), key=lambda x: x[1]["amount"], reverse=True
        )[:10]
        top_merchants = [
            {
                "merchant": name,
                "amount_display": format_inr(data["amount"]),
                "count": data["count"],
            }
            for name, data in sorted_m
        ]

        # Recurring charges
        merchant_txns: dict[str, Any] = defaultdict(list)
        for t in debit_txns:
            if t.get("description"):
                merchant_txns[t["description"]].append(t.get("amount", 0))

        recurring: list[dict[str, Any]] = []
        for desc, amounts in merchant_txns.items():
            if len(amounts) >= 2:
                avg_amt = sum(amounts) / len(amounts)
                if avg_amt > 0:
                    variance = max(abs(a - avg_amt) / avg_amt for a in amounts)
                    if variance < 0.2:
                        recurring.append(
                            {
                                "description": desc[:50],
                                "frequency": len(amounts),
                                "avg_display": format_inr(avg_amt),
                                "annual_display": format_inr(avg_amt * 12),
                            }
                        )

        recurring.sort(key=lambda x: x.get("frequency", 0), reverse=True)

        # Largest transactions
        sorted_debits = sorted(
            debit_txns, key=lambda t: t.get("amount", 0), reverse=True
        )
        largest_transactions = [
            {
                "rank": i + 1,
                "date_display": t.get("date_display", ""),
                "description": t.get("description_display", "")
                or t.get("description", ""),
                "amount_display": format_inr(t.get("amount", 0)),
                "bank": t.get("bank", ""),
            }
            for i, t in enumerate(sorted_debits[:10])
        ]

        return {
            "highest_month": highest_month,
            "highest_month_amount": highest_month_amount,
            "avg_monthly": round(avg_monthly, 2),
            "avg_monthly_display": format_inr(avg_monthly),
            "biggest_transaction": biggest_transaction,
            "unique_merchants": len({t.get("description", "") for t in debit_txns}),
            "spending_trend": spending_trend,
            "day_of_week": day_of_week,
            "top_merchants": top_merchants,
            "recurring_charges": recurring[:15],
            "largest_transactions": largest_transactions,
        }
