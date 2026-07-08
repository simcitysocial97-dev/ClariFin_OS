"""
FastAPI REST API for Personal Finance Tracker
==============================================

This API wraps the existing database and pipeline, exposing functionality
as HTTP endpoints for use by external applications (Next.js, mobile apps, etc.).

Run: python src/api.py
API Docs: http://localhost:8000/docs
"""

import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Import health module for router registration
import src.health as health
from categorizer import categorize

# Import configuration and utilities
from config import settings

# Import mapper for DTO transformation
from core.mappers import transaction_mapper
from csv_importer import CSVImporter

# Import existing modules
from db import FinanceDB
from engines.balance_engine import (
    compute_account_balance,
    compute_running_balance,
    get_accounts_list,
    validate_statement_balance,
)
from engines.behavior_engine import (
    compute_behavior_profile,
    get_cached_behavior_profile,
    invalidate_behavior_cache,
    set_cached_behavior_profile,
)
from engines.insight_generator import (
    generate_behavioral_insights,
    generate_summary_text,
)
from engines.ledger_audit_engine import (
    run_full_audit,
)
from engines.nudge_engine import (
    generate_nudges,
    get_nudge_summary,
    get_top_nudge,
)
from engines.reconciliation_engine import (
    find_potential_matches,
)
from errors import NotFoundError, register_error_handlers
from metadata_extractor import MetadataExtractor

# Import shared utilities from common module
from src.common import (
    DB_PATH,
    clean_description,
    compute_behavioral_insights,
    compute_is_large,
    enrich_transaction,
    format_date_display,
    format_inr,
    get_db,
    parse_date,
    percentage_change,
)
from statement_extractor import StatementExtractor

# ============================================================
# Configuration
# ============================================================

# Upload directory
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Helper Functions
# ============================================================

# Note: All utility functions (format_inr, parse_date, enrich_transaction, etc.)
# are now imported from src.common module to avoid duplication.


# ============================================================
# Pydantic Models
# ============================================================

class CategoryUpdate(BaseModel):
    category: str
    subcategory: str | None = None


class BulkCategoryUpdate(BaseModel):
    ids: list[int]
    category: str


class ImportExecute(BaseModel):
    filename: str
    mapping: dict
    member: str = "Self"


class MemberCreate(BaseModel):
    name: str
    color: str = "#6366F1"


# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="Personal Finance API",
    description="REST API for personal finance tracker",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register error handlers
register_error_handlers(app)

# Register health router
health.register_health_routes(app)

# Register routers
from src.routers import banks, investments, loans, members

app.include_router(banks.router)
app.include_router(investments.router)
app.include_router(loans.router)
app.include_router(members.router)

# Banks routes → routers/banks.py
# Investments routes → routers/investments.py
# Loans routes → routers/loans.py
# Members routes → routers/members.py


# ============================================================
# Dashboard Endpoints
# ============================================================

@app.get("/api/transactions")
def get_transactions(
    search: str | None = None,
    bank: str | None = "All",
    category: str | None = "All",
    type: str | None = "All",
    member: str | None = "All",
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get transactions with filters using DTO mapper."""
    try:
        db = get_db()
        filters = {}
        if search:
            filters["search"] = search
        if bank and bank != "All":
            filters["bank"] = bank
        if category and category != "All":
            filters["category"] = category
        if type and type != "All":
            filters["type"] = type
        if member and member != "All":
            filters["member"] = member

        raw = db.get_all_transactions_with_bank(filters)

        # Convert to DTOs using mapper
        response = transaction_mapper.TransactionMapper.to_list_response(
            transactions=raw,
            total=len(raw),
            limit=limit,
            offset=offset
        )

        # Serialize to JSON
        return response.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/overview")
def get_overview(
    exclude_transfers: bool = Query(True),
    member: str | None = "All",
):
    """Get overview metrics and charts."""
    try:
        db = get_db()
        filters = {}
        if member and member != "All":
            filters["member"] = member

        raw = db.get_all_transactions_with_bank(filters)
        transactions = [enrich_transaction(dict(t)) for t in raw]

        # Get confirmed transfer transaction IDs
        confirmed_transfer_ids = set()
        for debit_id, credit_id in db.get_confirmed_transfer_ids():
            confirmed_transfer_ids.add(debit_id)
            confirmed_transfer_ids.add(credit_id)

        # Filter out transfers if requested
        if exclude_transfers:
            # Exclude by category AND by confirmed reconciliation
            transactions = [
                t for t in transactions
                if t.get("category") != "Payments & Transfers"
                and t.get("id") not in confirmed_transfer_ids
            ]

        # Compute metrics
        debit_txns = [t for t in transactions if t.get("type") == "debit"]
        month_keys = sorted({t.get("month_key", "") for t in debit_txns if t.get("month_key")})

        total_spend = sum(t.get("amount", 0) for t in debit_txns)

        this_month = month_keys[-1] if month_keys else ""
        last_month = month_keys[-2] if len(month_keys) >= 2 else ""

        this_month_spend = sum(t.get("amount", 0) for t in debit_txns if t.get("month_key") == this_month)
        last_month_spend = sum(t.get("amount", 0) for t in debit_txns if t.get("month_key") == last_month)

        month_change = percentage_change(this_month_spend, last_month_spend) if last_month_spend > 0 else "—"

        # Monthly chart
        monthly: dict = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly[mk] += t.get("amount", 0)

        monthly_chart = [
            {"month": datetime.strptime(m, "%Y-%m").strftime("%b %y"), "amount": round(monthly[m], 2)}
            for m in sorted(monthly.keys())[-12:]
        ]

        # Category chart
        cat_totals: dict = defaultdict(float)
        for t in debit_txns:
            cat_totals[t.get("category", "Uncategorized")] += t.get("amount", 0)

        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        category_chart = [{"name": cat, "value": round(amt, 2)} for cat, amt in sorted_cats[:8]]

        # Bank chart
        bank_totals: dict = defaultdict(float)
        for t in debit_txns:
            bank_totals[t.get("bank", "Unknown")] += t.get("amount", 0)

        bank_chart = [
            {"bank": bank, "amount": round(amt, 2)}
            for bank, amt in sorted(bank_totals.items(), key=lambda x: x[1], reverse=True)
        ]

        # Recent transactions
        recent = sorted(transactions, key=lambda t: t.get("parsed_date", ""), reverse=True)[:10]
        recent = compute_is_large(recent)

        # Behavioral insights
        insights = compute_behavioral_insights(transactions)

        # Above/below average
        if monthly:
            avg_monthly = sum(monthly.values()) / len(monthly)
            diff = this_month_spend - avg_monthly
            above_below = f"+{format_inr(diff)} above avg" if diff > 0 else f"{format_inr(abs(diff))} below avg"
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/categories")
def get_categories(
    exclude_transfers: bool = Query(True),
    member: str | None = "All",
    drill_category: str | None = None,
):
    """Get category summary and breakdown."""
    try:
        db = get_db()
        filters = {}
        if member and member != "All":
            filters["member"] = member

        raw = db.get_all_transactions_with_bank(filters)
        transactions = [enrich_transaction(dict(t)) for t in raw]

        if exclude_transfers:
            transactions = [t for t in transactions if t.get("category") != "Payments & Transfers"]

        # Category summary
        cat_data: dict = defaultdict(lambda: {"amount": 0.0, "count": 0})
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
                "percentage": round((data["amount"] / total_debit) * 100, 1) if total_debit > 0 else 0,
            }
            for cat, data in sorted(cat_data.items(), key=lambda x: x[1]["amount"], reverse=True)
        ]

        # Monthly breakdown
        data: dict = defaultdict(lambda: defaultdict(float))
        for t in transactions:
            if t.get("type") == "debit":
                mk = t.get("month_key", "")
                cat = t.get("category", "Uncategorized")
                if mk:
                    data[mk][cat] += t.get("amount", 0)

        top_cats = [c for c, _ in sorted(cat_data.items(), key=lambda x: x[1]["amount"], reverse=True)[:6]]
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
                t for t in transactions
                if t.get("category") == drill_category
            ][:50]

        # Uncategorized patterns
        raw_uncat = db.get_uncategorized_patterns(limit=30)
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics")
def get_analytics(
    exclude_transfers: bool = Query(True),
    member: str | None = "All",
):
    """Get analytics data."""
    try:
        db = get_db()
        filters = {}
        if member and member != "All":
            filters["member"] = member

        raw = db.get_all_transactions_with_bank(filters)
        transactions = [enrich_transaction(dict(t)) for t in raw]

        if exclude_transfers:
            transactions = [t for t in transactions if t.get("category") != "Payments & Transfers"]

        debit_txns = [t for t in transactions if t.get("type") == "debit"]

        # Monthly data
        monthly: dict = defaultdict(float)
        for t in debit_txns:
            mk = t.get("month_key", "")
            if mk:
                monthly[mk] += t.get("amount", 0)

        sorted_months = sorted(monthly.keys())
        monthly_amounts = [monthly[m] for m in sorted_months]
        avg_monthly = sum(monthly_amounts) / len(monthly_amounts) if monthly_amounts else 0

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
            {"month": datetime.strptime(m, "%Y-%m").strftime("%b %y"), "amount": round(monthly[m], 2), "average": round(avg_monthly, 2)}
            for m in sorted_months
        ]

        # Day of week
        day_totals: dict = defaultdict(lambda: {"amount": 0.0, "count": 0})
        for t in debit_txns:
            wd = t.get("weekday", "")
            if wd:
                day_totals[wd]["amount"] += t.get("amount", 0)
                day_totals[wd]["count"] += 1

        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_of_week = [
            {
                "day": day[:3],
                "amount": round(day_totals[day]["amount"], 2),
                "count": day_totals[day]["count"],
            }
            for day in day_order
        ]

        # Top merchants
        merchant_data: dict = defaultdict(lambda: {"amount": 0.0, "count": 0})
        for t in debit_txns:
            if t.get("description"):
                desc = (t["description"] or "")[:40]
                merchant_data[desc]["amount"] += t.get("amount", 0)
                merchant_data[desc]["count"] += 1

        sorted_m = sorted(merchant_data.items(), key=lambda x: x[1]["amount"], reverse=True)[:10]
        top_merchants = [
            {
                "merchant": name,
                "amount_display": format_inr(data["amount"]),
                "count": data["count"],
            }
            for name, data in sorted_m
        ]

        # Recurring charges
        merchant_txns: dict = defaultdict(list)
        for t in debit_txns:
            if t.get("description"):
                merchant_txns[t["description"]].append(t.get("amount", 0))

        recurring = []
        for desc, amounts in merchant_txns.items():
            if len(amounts) >= 2:
                avg_amt = sum(amounts) / len(amounts)
                if avg_amt > 0:
                    variance = max(abs(a - avg_amt) / avg_amt for a in amounts)
                    if variance < 0.2:
                        recurring.append({
                            "description": desc[:50],
                            "frequency": len(amounts),
                            "avg_display": format_inr(avg_amt),
                            "annual_display": format_inr(avg_amt * 12),
                        })

        recurring.sort(key=lambda x: x["frequency"], reverse=True)

        # Largest transactions
        sorted_debits = sorted(debit_txns, key=lambda t: t.get("amount", 0), reverse=True)
        largest_transactions = [
            {
                "rank": i + 1,
                "date_display": t.get("date_display", ""),
                "description": t.get("description_display", "") or t.get("description", ""),
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statements")
def get_statements():
    """Get all statements with metadata."""
    try:
        db = get_db()
        raw = db.get_all_statements_with_metadata()

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
                "✅ Exact Match" if validation_status == "exact_match"
                else f"⚠️ Close (₹{diff:,.0f} off)" if validation_status == "close_match"
                else f"❌ Mismatch (₹{diff:,.0f})" if validation_status == "mismatch"
                else "— No Data" if validation_status == "no_metadata"
                else "⏳ Pending"
            )
            badge_color = (
                "green" if validation_status == "exact_match"
                else "amber" if validation_status == "close_match"
                else "red" if validation_status == "mismatch"
                else "gray"
            )

            statements.append({
                "id": stmt.get("id"),
                "bank": stmt.get("bank"),
                "file_name": stmt.get("file_name"),
                "card_last4": stmt.get("card_last4"),
                "card_display": f"****{stmt.get('card_last4')}" if stmt.get("card_last4") else "",
                "period_from": stmt.get("statement_period_from"),
                "period_to": stmt.get("statement_period_to"),
                "period_display": f"{stmt.get('statement_period_from')} – {stmt.get('statement_period_to')}" if stmt.get("statement_period_from") else "",
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
            })

        return statements
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/cards")
def get_cards():
    """
    Returns credit cards with their latest statement summary.
    Groups statements by card_last4 and bank.
    Returns one entry per unique card with latest statement data.
    """
    try:
        db = get_db()
        raw = db.get_all_statements_with_metadata()

        # Group statements by (bank, card_last4)
        card_groups: dict = defaultdict(list)
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
                statements,
                key=lambda s: s.get("imported_at") or "",
                reverse=True
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
                utilization_percent = round((current_outstanding / credit_limit) * 100, 1)

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

            cards.append({
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
            })

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


# Banks routes → routers/banks.py


@app.get("/api/categories/list")
def get_categories_list():
    """Get list of categories."""
    try:
        db = get_db()
        # Get from transactions
        raw = db.get_all_transactions_with_bank()
        cats = sorted({t.get("category") for t in raw if t.get("category")})
        return {"categories": cats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Members routes → routers/members.py


# ============================================================
# Cashflow Endpoint
# ============================================================

@app.get("/api/cashflow/monthly")
def get_cashflow_monthly(
    months: int = Query(default=6, ge=1, le=12),
    member: str | None = Query(default=None),
):
    """
    Returns month-by-month income and expense aggregation.
    All monetary values in paise (INTEGER).
    """
    try:
        db = get_db()

        # Build query with optional member filter
        conditions = ["t.date_iso IS NOT NULL"]
        params = []

        if member and member != "All":
            conditions.append("t.member = ?")
            params.append(member)

        where = "WHERE " + " AND ".join(conditions)

        # Query using date_iso for proper month grouping
        # date_iso is in YYYY-MM-DD format, so we extract YYYY-MM
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

        conn = db._get_conn()
        cur = conn.execute(sql, params)
        rows = [dict(row) for row in cur.fetchall()]
        if db._conn is None:
            conn.close()

        # Format response - limit to requested number of months
        months_data = []
        total_income = 0
        total_expense = 0

        # Get the most recent N months
        rows_sorted = sorted(rows, key=lambda r: r.get("month_key", ""), reverse=True)
        rows_limited = rows_sorted[:months]

        for row in rows_limited:
            month_key = row.get("month_key", "")
            if not month_key:
                continue

            income = int(row.get("income_paise", 0) or 0)
            expense = int(row.get("expense_paise", 0) or 0)

            # Create month label (e.g., "Jan 2025")
            try:
                month_dt = datetime.strptime(month_key, "%Y-%m")
                month_label = month_dt.strftime("%b %Y")
            except ValueError:
                month_label = month_key

            months_data.append({
                "month_key": month_key,
                "month_label": month_label,
                "income_paise": income,
                "expense_paise": expense,
                "net_paise": income - expense,
                "transaction_count": int(row.get("transaction_count", 0) or 0),
            })

            total_income += income
            total_expense += expense

        # Sort by month_key ascending for the response
        months_data.sort(key=lambda m: m["month_key"])

        return {
            "months": months_data,
            "period_months": len(months_data),
            "total_income_paise": total_income,
            "total_expense_paise": total_expense,
            "total_net_paise": total_income - total_expense,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Action Endpoints
# ============================================================

@app.post("/api/upload")
async def upload_statement(
    file: UploadFile = File(...),
    member: str = Form("Self"),
):
    """Upload and process a PDF statement."""
    try:
        db = get_db()
        log = []

        # Save file
        filename = file.filename
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files allowed")

        save_path = UPLOAD_DIR / filename
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        log.append(f"📄 Processing: {filename}")

        # Check duplicate
        if db.get_duplicate_check_by_filename(filename):
            return {
                "success": False,
                "error": "File already imported",
                "log": log + ["⚠️ Already imported, skipping"],
            }

        # Extract
        extractor = StatementExtractor(str(save_path))
        result = extractor.extract()
        bank = result.get("bank", "Unknown")
        transactions = result.get("transactions", [])

        log.append(f"✅ Bank: {bank}")
        log.append(f"✅ Extracted {len(transactions)} transactions")

        # Categorize
        for txn in transactions:
            amount_paise = int(txn.get("amount_paise") or 0)
            amount_float = amount_paise / 100.0 if amount_paise else None
            cat, subcat = categorize(txn.get("description", ""), amount_float)
            txn["category"] = cat
            txn["subcategory"] = subcat
            txn["member"] = member

        # Insert
        period = result.get("statement_period", {})
        statement_id = db.insert_statement(
            bank=bank,
            file_name=filename,
            period_from=period.get("from", ""),
            period_to=period.get("to", ""),
        )
        db.insert_transactions(statement_id, transactions)

        # Metadata
        metadata = {}
        try:
            meta_extractor = MetadataExtractor(str(save_path), bank=bank)
            metadata = meta_extractor.extract()
            db.update_statement_metadata(statement_id, metadata)
            if metadata.get("total_amount_due"):
                log.append(f"✅ Total Due: ₹{metadata['total_amount_due']:,.2f}")
        except Exception as e:
            log.append(f"⚠️ Metadata: {str(e)[:60]}")

        # Validation
        total_due = metadata.get("total_amount_due")
        if total_due and total_due > 0:
            # Use amount_paise (canonical integer) for computation
            total_due_paise = int(round(total_due * 100))
            debit_sum_paise = sum(
                int(t.get("amount_paise") or 0)
                for t in transactions if t.get("type") == "debit"
            )
            credit_sum_paise = sum(
                int(t.get("amount_paise") or 0)
                for t in transactions if t.get("type") == "credit"
            )
            net_paise = debit_sum_paise - credit_sum_paise
            diff_paise = abs(net_paise - total_due_paise)
            diff_rupees = diff_paise / 100.0

            if diff_paise < 100:  # < ₹1.00
                val_status = "exact_match"
                log.append("✅ Validation: exact match")
            elif diff_paise < 5000:  # < ₹50.00
                val_status = "close_match"
                log.append(f"⚠️ Validation: close match (₹{diff_rupees:.2f} off)")
            else:
                val_status = "mismatch"
                log.append(f"❌ Validation: mismatch (₹{diff_rupees:.2f} off)")

            db.update_validation_status(statement_id, val_status, round(diff_rupees, 2))
        else:
            db.update_validation_status(statement_id, "no_metadata", 0.0)
            log.append("⚠️ Validation: total due not found")

        log.append(f"✅ Saved (Member: {member})")

        # Invalidate behavior cache after data changes
        invalidate_behavior_cache()

        return {
            "success": True,
            "bank": bank,
            "transaction_count": len(transactions),
            "validation_status": val_status if total_due and total_due > 0 else "no_metadata",
            "metadata": metadata,
            "log": log,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/import/detect")
async def import_detect(file: UploadFile = File(...)):
    """Detect CSV/Excel format."""
    try:
        # Save file
        filename = file.filename
        suffix = Path(filename).suffix.lower()
        if suffix not in [".csv", ".xlsx", ".xls"]:
            raise HTTPException(status_code=400, detail="Unsupported file type")

        save_path = UPLOAD_DIR / filename
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        # Detect format
        importer = CSVImporter(str(save_path))
        detected = importer.detect_format()

        return {
            "filename": filename,
            "columns": detected.get("columns", []),
            "sample_rows": detected.get("sample_rows", []),
            "detected_mapping": detected.get("detected_mapping", {}),
            "row_count": detected.get("row_count", 0),
            "date_format": detected.get("date_format", "%d/%m/%Y"),
            "skip_rows": detected.get("skip_rows", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/import/execute")
def import_execute(data: ImportExecute):
    """Execute CSV/Excel import."""
    try:
        db = get_db()
        save_path = UPLOAD_DIR / data.filename

        if not save_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        importer = CSVImporter(str(save_path))
        transactions, warnings = importer.import_transactions(data.mapping)

        if not transactions:
            return {
                "success": False,
                "error": "No valid transactions found",
                "warnings": warnings,
            }

        # Insert
        inserted = db.insert_csv_transactions(
            transactions=transactions,
            member=data.member,
            source="csv",
            bank=data.mapping.get("bank", "Manual Import"),
            file_name=data.filename,
        )

        # Invalidate behavior cache after data changes
        invalidate_behavior_cache()

        return {
            "success": True,
            "count": inserted,
            "skipped": len(transactions) - inserted,
            "errors": warnings,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Phase 2A.1: Removed mutable endpoints for ledger immutability
# - PUT /api/transactions/{id}/category - REMOVED
# - PUT /api/transactions/bulk-category - REMOVED
# - DELETE /api/statements/{id} - REMOVED
# Ledger is now append-only. Use compensating transactions for corrections.


# ============================================================
# Balance API Endpoints (Phase 2A)
# ============================================================

@app.get("/api/accounts")
def api_get_accounts():
    """Get all accounts with their computed balances."""
    try:
        accounts = get_accounts_list(DB_PATH)
        return {"accounts": accounts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{account_id}/balance")
def api_get_account_balance(account_id: str):
    """Get current balance for a specific account."""
    try:
        result = compute_account_balance(DB_PATH, account_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/accounts/{account_id}/running-balance")
def api_get_running_balance(account_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get running balance history for an account."""
    try:
        result = compute_running_balance(DB_PATH, account_id)
        # Return limited results
        return {
            "account_id": account_id,
            "transactions": result[:limit],
            "total": len(result),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statements/{statement_id}/validate")
def api_validate_statement(statement_id: int, claimed_balance_paise: int = Query(..., description="Claimed closing balance in paise")):
    """Validate a statement's closing balance against computed balance."""
    try:
        result = validate_statement_balance(DB_PATH, statement_id, claimed_balance_paise)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/export/csv")
def export_csv(
    search: str | None = None,
    bank: str | None = "All",
    category: str | None = "All",
    type: str | None = "All",
    member: str | None = "All",
):
    """Export transactions to CSV."""
    try:
        db = get_db()
        filters = {}
        if search:
            filters["search"] = search
        if bank and bank != "All":
            filters["bank"] = bank
        if category and category != "All":
            filters["category"] = category
        if type and type != "All":
            filters["type"] = type
        if member and member != "All":
            filters["member"] = member

        raw = db.get_all_transactions_with_bank(filters)

        import io
        output = io.StringIO()
        output.write("Date,Bank,Description,Amount,Type,Category\n")

        for txn in raw:
            date = format_date_display(txn.get("date", ""))
            bank_name = txn.get("bank", "")
            desc = (clean_description(txn.get("description", ""))).replace(",", ";").replace('"', '""')
            amount = txn.get("amount", 0)
            txn_type = txn.get("type", "")
            cat = txn.get("category", "")

            output.write(f'"{date}","{bank_name}","{desc}",{amount},"{txn_type}","{cat}"\n')

        csv_data = output.getvalue()
        output.close()

        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=transactions.csv"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Reconciliation API Endpoints (Phase 2B)
# ============================================================

@app.get("/api/reconciliations")
def api_get_reconciliations(status: str | None = None):
    """
    Get all reconciliations with transaction details.

    Phase 2B: Metadata-only, no ledger mutation.

    Args:
        status: Optional filter ('pending', 'confirmed', 'rejected')
    """
    try:
        db = get_db()
        reconciliations = db.get_reconciliations(status)

        # Enrich with display fields
        for r in reconciliations:
            # Amount is already in rupees in new schema
            amount = r.get("amount", 0)
            r["amount_display"] = format_inr(amount)
            r["confidence_display"] = f"{r.get('match_confidence', 0) * 100:.0f}%"

        return {"reconciliations": reconciliations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reconciliations/pending")
def api_get_pending_reconciliations():
    """Get all pending reconciliations."""
    return api_get_reconciliations(status="pending")


@app.get("/api/reconciliations/scan")
def api_scan_reconciliations():
    """
    Scan for potential transfer matches across accounts.

    Phase 2B.1: Deterministic matching with confidence scoring.

    Returns potential matches that can be saved as reconciliations.
    """
    try:
        matches = find_potential_matches(DB_PATH)

        # Enrich with display fields
        for m in matches:
            m["amount_display"] = format_inr(m.get("amount", 0))
            m["confidence_display"] = f"{m.get('match_confidence', 0) * 100:.0f}%"

        return {"matches": matches, "count": len(matches)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reconciliations/create")
def api_create_reconciliation(
    debit_txn_id: int = Query(..., description="Debit transaction ID"),
    credit_txn_id: int = Query(..., description="Credit transaction ID"),
    debit_account_id: str = Query(..., description="Debit account ID"),
    credit_account_id: str = Query(..., description="Credit account ID"),
    amount: float = Query(..., description="Matched amount in rupees"),
    date_diff_days: int = Query(0, description="Days between transaction dates"),
    match_confidence: float = Query(..., description="Confidence score 0.0-1.0"),
    match_type: str = Query("exact", description="'exact', 'window', 'fuzzy', or 'manual'"),
):
    """
    Create a reconciliation record between two transactions.

    Phase 2B: Metadata-only, no ledger mutation.
    Uses INSERT OR IGNORE for idempotency.
    """
    try:
        db = get_db()
        inserted = db.insert_reconciliation(
            debit_txn_id=debit_txn_id,
            credit_txn_id=credit_txn_id,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            date_diff_days=date_diff_days,
            match_confidence=match_confidence,
            match_type=match_type,
        )
        return {"success": True, "inserted": inserted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reconciliations/batch-insert")
def api_batch_insert_reconciliations():
    """
    Scan and insert all potential matches as pending reconciliations.

    Uses INSERT OR IGNORE for idempotency - existing records are not duplicated.
    """
    try:
        db = get_db()
        matches = find_potential_matches(DB_PATH)

        inserted_count = 0
        for m in matches:
            inserted = db.insert_reconciliation(
                debit_txn_id=m["debit_txn_id"],
                credit_txn_id=m["credit_txn_id"],
                debit_account_id=m["debit_account_id"],
                credit_account_id=m["credit_account_id"],
                amount=m["amount"],
                date_diff_days=m["date_diff_days"],
                match_confidence=m["match_confidence"],
                match_type=m["match_type"],
            )
            if inserted:
                inserted_count += 1

        return {
            "success": True,
            "scanned": len(matches),
            "inserted": inserted_count,
            "skipped": len(matches) - inserted_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reconciliations/{reconciliation_id}/confirm")
def api_confirm_reconciliation(reconciliation_id: int):
    """
    Confirm a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    """
    try:
        db = get_db()
        updated = db.confirm_reconciliation(reconciliation_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Reconciliation not found or not pending")
        return {"success": True, "status": "confirmed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reconciliations/{reconciliation_id}/reject")
def api_reject_reconciliation(reconciliation_id: int):
    """
    Reject a pending reconciliation.

    Phase 2B: Updates reconciliation.status only. No ledger mutation.
    """
    try:
        db = get_db()
        updated = db.reject_reconciliation(reconciliation_id)
        if not updated:
            raise HTTPException(status_code=404, detail="Reconciliation not found or not pending")
        return {"success": True, "status": "rejected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Audit API Endpoints (Phase 2C)
# ============================================================

@app.get("/api/audit/report")
def api_audit_report():
    """
    Run full ledger audit and return combined report.

    Phase 2C: Read-only integrity verification.

    Returns:
        {
            "overall_status": "PASS" or "FAIL",
            "ledger_integrity": {...},
            "hash_verification": {...}
        }
    """
    try:
        report = run_full_audit(DB_PATH)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Behavioral Intelligence API Endpoints (Phase 3)
# ============================================================

@app.get("/api/behavior/summary")
def api_behavior_summary():
    """
    Get comprehensive behavioral profile.

    Phase 3: Advanced Behavioral Intelligence Layer.

    Returns:
        {
            "temporal_patterns": {...},
            "behavioral_indices": {...},
            "risk_signals": {...},
            "confidence": float (0–1),
            "financial_health_score": float (0–100)
        }
    """
    try:
        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            return cached

        # Compute and cache
        profile = compute_behavior_profile(DB_PATH)
        set_cached_behavior_profile(DB_PATH, profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behavior/score")
def api_behavior_score():
    """
    Get financial health score with breakdown.

    Phase 3: Composite health score with component breakdown.

    Returns:
        {
            "financial_health_score": float (0–100),
            "confidence": float (0–1),
            "components": {...},
            "summary": str
        }
    """
    try:
        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            profile = cached
        else:
            profile = compute_behavior_profile(DB_PATH)
            set_cached_behavior_profile(DB_PATH, profile)

        indices = profile.get("behavioral_indices", {})

        return {
            "financial_health_score": profile.get("financial_health_score", 50),
            "confidence": profile.get("confidence", 0),
            "components": {
                "savings_discipline": indices.get("savings_discipline", {}).get("score", 0.5),
                "habit_stability": indices.get("habit_stability", {}).get("score", 0.5),
                "impulsivity": indices.get("impulsivity", {}).get("score", 0.5),
                "financial_stress": indices.get("financial_stress", {}).get("score", 0.5),
                "loss_aversion": indices.get("loss_aversion", {}).get("score", 0.5),
            },
            "risk_flags": profile.get("risk_signals", {}),
            "summary": generate_summary_text(profile),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/behavior/insights")
def api_behavior_insights():
    """
    Get behavioral insights and nudges.

    Phase 3: Evidence-based insights with actionable suggestions.

    Returns:
        {
            "insights": [...],
            "nudges": [...],
            "top_nudge": {...},
            "summary": str
        }
    """
    try:
        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            profile = cached
        else:
            profile = compute_behavior_profile(DB_PATH)
            set_cached_behavior_profile(DB_PATH, profile)

        insights = generate_behavioral_insights(profile)
        nudges = generate_nudges(profile)
        top_nudge = get_top_nudge(profile)
        summary = get_nudge_summary(profile)

        return {
            "insights": insights,
            "nudges": nudges,
            "top_nudge": top_nudge,
            "summary": summary,
            "financial_health_score": profile.get("financial_health_score", 50),
            "confidence": profile.get("confidence", 0),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Dashboard Summary API (MVP v1.0.0)
# ============================================================

@app.get("/api/dashboard/summary")
def api_dashboard_summary():
    """
    Get simplified dashboard summary for MVP.

    Returns 4 key metrics:
    - Net Cash Flow
    - Savings Rate %
    - EMI Ratio %
    - Buffer Days
    """
    try:
        db = get_db()

        # Check cache first
        cached = get_cached_behavior_profile(DB_PATH)
        if cached is not None:
            profile = cached
        else:
            profile = compute_behavior_profile(DB_PATH)
            set_cached_behavior_profile(DB_PATH, profile)

        indices = profile.get("behavioral_indices", {})

        # Calculate net cash flow from savings discipline
        savings_discipline = indices.get("savings_discipline", {})
        savings_rate = savings_discipline.get("savings_rate", 0)

        # Get financial stress data for EMI ratio and buffer
        financial_stress = indices.get("financial_stress", {})
        emi_ratio = profile.get("risk_signals", {}).get("india_specific", {}).get("emi_ratio", 0)
        buffer_days = financial_stress.get("buffer_days", 0)

        # Calculate net cash flow (simplified)
        # Net cash flow = (income - expenses) over last 30 days
        raw = db.get_all_transactions_with_bank({})
        transactions = [enrich_transaction(dict(t)) for t in raw]

        # Get last 30 days transactions
        from datetime import datetime, timedelta
        cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        recent_txns = [t for t in transactions if t.get("parsed_date", "") >= cutoff]

        total_income = sum(t.get("amount", 0) for t in recent_txns if t.get("type") == "credit")
        total_expenses = sum(t.get("amount", 0) for t in recent_txns if t.get("type") == "debit")
        net_cash_flow = total_income - total_expenses

        # Calculate 7-day trend
        seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        seven_day_txns = [t for t in transactions if t.get("parsed_date", "") >= seven_days_ago]

        prev_seven_start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        prev_seven_txns = [t for t in transactions if prev_seven_start <= t.get("parsed_date", "") < seven_days_ago]

        current_spend = sum(t.get("amount", 0) for t in seven_day_txns if t.get("type") == "debit")
        prev_spend = sum(t.get("amount", 0) for t in prev_seven_txns if t.get("type") == "debit")

        seven_day_trend = 0
        if prev_spend > 0:
            seven_day_trend = (current_spend - prev_spend) / prev_spend

        # Category drift alert (simplified)
        category_drift_alert = None
        if profile.get("risk_signals", {}).get("high_impulsivity"):
            category_drift_alert = "High impulsivity detected. Consider reviewing discretionary spending."
        elif profile.get("risk_signals", {}).get("low_savings"):
            category_drift_alert = "Savings rate is below target. Consider reducing non-essential expenses."

        # Recent transactions
        recent = sorted(transactions, key=lambda t: t.get("parsed_date", ""), reverse=True)[:10]

        return {
            "net_cash_flow_paise": int(round(net_cash_flow * 100)),
            "savings_rate": savings_rate,
            "emi_ratio": emi_ratio,
            "buffer_days": buffer_days,
            "financial_health_score": profile.get("financial_health_score", 50),
            "seven_day_trend": seven_day_trend,
            "category_drift_alert": category_drift_alert,
            "recent_transactions": recent,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Accounts Management API (Phase 4 - DB-backed)
# ============================================================

class AccountCreate(BaseModel):
    name: str
    bank: str
    account_type: str = "savings"
    balance_paise: int
    account_number_last4: str | None = None
    notes: str | None = None

class AccountUpdate(BaseModel):
    name: str | None = None
    bank: str | None = None
    account_type: str | None = None
    balance_paise: int | None = None
    account_number_last4: str | None = None
    notes: str | None = None

@app.get("/api/accounts/manage")
def api_get_managed_accounts():
    """Get all persistently stored accounts."""
    try:
        with FinanceDB() as db:
            accounts = db.get_all_accounts()
            return {"accounts": accounts, "total": len(accounts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/manage")
def api_create_managed_account(account: AccountCreate):
    """Create a new persistent account."""
    try:
        with FinanceDB() as db:
            created = db.create_account(
                account_id=0,  # Will use auto-increment
                name=account.name,
                bank=account.bank,
                account_type=account.account_type,
                balance_paise=account.balance_paise,
                account_number_last4=account.account_number_last4,
                notes=account.notes
            )
            return {"success": True, "account": created}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/accounts/manage/{account_id}")
def api_update_managed_account(account_id: str, account: AccountUpdate):
    """Update an existing account."""
    try:
        with FinanceDB() as db:
            updated = db.update_account(
                account_id,
                **{k: v for k, v in account.model_dump().items() if v is not None}
            )
            if not updated:
                raise NotFoundError(f"Account {account_id} not found")
            return {"success": True, "account": updated}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/accounts/manage/{account_id}")
def api_delete_managed_account(account_id: str):
    """Soft delete an account."""
    try:
        with FinanceDB() as db:
            success = db.delete_account(account_id)
            if not success:
                raise NotFoundError(f"Account {account_id} not found")
            return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Investments routes → routers/investments.py
# Loans routes → routers/loans.py


# ============================================================
# NET WORTH ENDPOINT ───────────────────────────────────────────────────

@app.get("/api/networth")
def get_networth():
    """
    Compute net worth from all financial data.

    Net Worth = Assets - Liabilities
    Assets = account balances + investment current values
    Liabilities = loan outstanding + card outstanding
    """
    with FinanceDB() as db:
        accounts = db.get_all_accounts()
        loans = db.get_all_loans()
        investments = db.get_all_investments()
        statements = db.get_all_statements()

    # Assets
    account_balance_paise = sum(a['balance_paise'] for a in accounts)
    investment_value_paise = sum(i['current_value_paise'] for i in investments)
    total_assets_paise = account_balance_paise + investment_value_paise

    # Liabilities
    loan_outstanding_paise = sum(loan['outstanding_paise'] for loan in loans)

    # Card outstanding from latest statement per card
    card_outstanding_paise = 0
    seen_cards: set[str] = set()
    for stmt in sorted(statements, key=lambda s: s.get('statement_period_to', ''), reverse=True):
        card_key = f"{stmt.get('bank', '')}_{stmt.get('card_last4', '')}"
        if card_key not in seen_cards:
            seen_cards.add(card_key)
            due = stmt.get('total_amount_due', 0) or 0
            card_outstanding_paise += int(round(due * 100))

    total_liabilities_paise = loan_outstanding_paise + card_outstanding_paise
    net_worth_paise = total_assets_paise - total_liabilities_paise

    return {
        "net_worth_paise": net_worth_paise,
        "assets": {
            "total_paise": total_assets_paise,
            "accounts_paise": account_balance_paise,
            "investments_paise": investment_value_paise,
            "account_count": len(accounts),
            "investment_count": len(investments),
        },
        "liabilities": {
            "total_paise": total_liabilities_paise,
            "loans_paise": loan_outstanding_paise,
            "cards_paise": card_outstanding_paise,
            "loan_count": len(loans),
            "card_count": len(seen_cards),
        },
        "is_partial": len(accounts) == 0 and len(investments) == 0,
        "partial_reason": "Add accounts and investments for complete net worth" if len(accounts) == 0 else None,
    }


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
