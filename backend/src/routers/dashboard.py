"""
Dashboard Router
================
Endpoints for dashboard overview, analytics, and summaries.
"""

import os
import shutil
import sqlite3
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Any

from fastapi import APIRouter, Query
from collections import defaultdict

from src.dependencies import (
    get_db,
    enrich_transaction,
    format_inr,
    format_date_display,
    get_month_key,
    percentage_change,
    compute_behavioral_insights,
    DB_PATH,
)
from src.engines.behavior_engine import compute_behavior_profile
from src.engines.cashflow_engine import (
    compute_monthly_cashflow,
    compute_cashflow_breakdown,
    compute_cashflow_summary,
)
from src.engines.networth_engine import (
    compute_net_worth,
    compute_net_worth_trend,
    compute_asset_allocation,
)
from src.logger import log
from src.errors import NotFoundError

router = APIRouter()


# ============================================================
# Health Check Endpoints
# ============================================================

@router.get("/api/diagnostics")
def run_diagnostics():
    """
    Run full pipeline validation checks.
    
    Returns comprehensive validation results including:
    - Database schema validation
    - API route consistency
    - Engine health
    - Frontend build status
    - Cross-layer type consistency
    """
    from src.validate_pipeline import PipelineValidator, Severity
    
    validator = PipelineValidator()
    issues = validator.run_all_checks()
    
    return {
        "status": "fail" if any(i.severity == Severity.ERROR for i in issues) else "pass",
        "error_count": sum(1 for i in issues if i.severity == Severity.ERROR),
        "warning_count": sum(1 for i in issues if i.severity == Severity.WARNING),
        "info_count": sum(1 for i in issues if i.severity == Severity.INFO),
        "issues": [
            {
                "severity": i.severity.value,
                "category": i.category,
                "message": i.message,
                "file": i.file,
                "line": i.line,
                "fix_hint": i.fix_hint,
            }
            for i in issues
        ],
    }


@router.get("/api/health/detailed")
def health_detailed() -> dict[str, Any]:
    """
    Detailed health check endpoint.
    
    Returns comprehensive health status including:
    - Database connectivity and data counts
    - Engine import status
    - Disk space availability
    - Database file size
    """
    checks = []
    
    # Check 1: Database connectivity
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5)
        try:
            cur = conn.execute("SELECT 1")
            cur.fetchone()
            
            # Get data counts
            cur = conn.execute("SELECT COUNT(*) FROM transactions")
            txn_count = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM statements")
            stmt_count = cur.fetchone()[0]
            cur = conn.execute("SELECT COUNT(*) FROM accounts")
            account_count = cur.fetchone()[0]
            
            checks.append({
                "check": "database",
                "status": "pass",
                "detail": f"Connected, {txn_count} transactions, {stmt_count} statements, {account_count} accounts"
            })
        finally:
            conn.close()
    except Exception as e:
        checks.append({
            "check": "database",
            "status": "fail",
            "detail": f"Database error: {str(e)}"
        })
    
    # Check 2: Engine imports
    engines = [
        "src.engines.balance_engine",
        "src.engines.behavior_engine",
        "src.engines.reconciliation_engine",
        "src.engines.ledger_audit_engine",
        "src.engines.insight_generator",
        "src.engines.nudge_engine",
    ]
    failed_engines = []
    for engine in engines:
        try:
            __import__(engine)
        except ImportError:
            failed_engines.append(engine.split(".")[-1])
    
    if failed_engines:
        checks.append({
            "check": "engines",
            "status": "fail",
            "detail": f"{len(engines) - len(failed_engines)}/{len(engines)} engines loaded, failed: {', '.join(failed_engines)}"
        })
    else:
        checks.append({
            "check": "engines",
            "status": "pass",
            "detail": f"{len(engines)}/{len(engines)} engines loaded"
        })
    
    # Check 3: Disk space
    try:
        data_dir = Path(DB_PATH).parent
        usage = shutil.disk_usage(data_dir)
        free_gb = usage.free / (1024 ** 3)
        checks.append({
            "check": "disk",
            "status": "pass",
            "detail": f"{free_gb:.1f} GB free"
        })
    except Exception as e:
        checks.append({
            "check": "disk",
            "status": "warn",
            "detail": f"Could not check disk space: {str(e)}"
        })
    
    # Check 4: Database file size
    try:
        db_size_mb = os.path.getsize(DB_PATH) / (1024 ** 2)
        checks.append({
            "check": "db_size",
            "status": "pass",
            "detail": f"{db_size_mb:.1f} MB"
        })
    except Exception as e:
        checks.append({
            "check": "db_size",
            "status": "warn",
            "detail": f"Could not check DB size: {str(e)}"
        })
    
    # Determine overall status
    fail_count = sum(1 for c in checks if c["status"] == "fail")
    warn_count = sum(1 for c in checks if c["status"] == "warn")
    
    if fail_count > 0:
        overall_status = "unhealthy"
    elif warn_count > 0:
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/api/overview")
def get_overview():
    """Get dashboard overview data using SQL aggregation."""
    db = get_db()
    
    # Get overview stats via SQL aggregation (high performance)
    stats = db.get_overview_stats()
    
    # Get recent transactions (paginated, latest 20)
    recent_result = db.get_all_transactions_with_bank({}, page=1, per_page=20)
    recent_transactions = [enrich_transaction(dict(t)) for t in recent_result["items"]]
    
    # Monthly breakdown
    monthly = db.get_monthly_summary()
    
    # Category breakdown
    categories = db.get_category_summary()
    
    # Get actual card count from cards table
    cards = db.get_cards(include_inactive=False)
    card_count = len(cards)
    
    # Calculate derived fields for frontend
    total_spend = stats["total_expense_paise"] / 100
    total_credit = stats["total_income_paise"] / 100
    transaction_count = stats["transaction_count"]
    
    # Calculate this month vs last month from monthly data
    this_month_total = 0
    last_month_total = 0
    month_change = "0%"
    
    if monthly and len(monthly) > 0:
        # Monthly is sorted DESC, so first is most recent
        this_month_total = monthly[0].get("total_debit", 0)
        if len(monthly) > 1:
            last_month_total = monthly[1].get("total_debit", 0)
        
        if last_month_total > 0:
            change_pct = ((this_month_total - last_month_total) / last_month_total) * 100
            sign = "+" if change_pct >= 0 else ""
            month_change = f"{sign}{change_pct:.1f}%"
        elif this_month_total > 0:
            month_change = "+100%"
    
    # Calculate monthly average
    months_of_data = len(monthly) if monthly else 0
    monthly_average = total_spend / months_of_data if months_of_data > 0 else 0
    
    # Calculate above/below average
    above_below_avg = ""
    above_avg_is_bad = True  # Spending more than average is bad
    if monthly_average > 0 and this_month_total > 0:
        diff_pct = ((this_month_total - monthly_average) / monthly_average) * 100
        if diff_pct > 0:
            above_below_avg = f"+{diff_pct:.0f}% above avg"
        else:
            above_below_avg = f"{diff_pct:.0f}% below avg"
    
    # Format monthly chart for frontend (reverse to get ascending order)
    monthly_chart = []
    for m in reversed(monthly):
        month_label = m.get("month", "")
        # Convert YYYY-MM to Mon YYYY format
        if month_label and len(month_label) == 7:
            try:
                year, month = month_label.split("-")
                month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
                month_label = f"{month_names[int(month)]} {year}"
            except:
                pass
        monthly_chart.append({
            "month": month_label,
            "amount": m.get("total_debit", 0)
        })
    
    # Format category chart for frontend
    category_chart = []
    for cat in categories:
        category_chart.append({
            "name": cat.get("category", "Unknown"),
            "value": cat.get("total_amount", 0)
        })
    
    # Get bank chart data - OPTIMIZED: Single query with GROUP BY
    # Was: N banks × 1 query per bank = N queries (N+1 pattern)
    # Now: 1 query with GROUP BY
    bank_totals = db.get_bank_transaction_totals()
    bank_chart = [
        {"bank": bt["bank"], "amount": bt["total_debit"] / 100}  # Convert paise to rupees
        for bt in bank_totals
    ]
    
    # Generate behavioral insights
    all_txns = [enrich_transaction(dict(t)) for t in db.get_all_transactions()]
    behavioral_insights = compute_behavioral_insights(all_txns)
    
    return {
        # Core stats
        "total_spend": total_spend,
        "total_spend_display": format_inr(total_spend),
        "this_month": this_month_total,
        "this_month_display": format_inr(this_month_total),
        "last_month": last_month_total,
        "last_month_display": format_inr(last_month_total),
        "month_change": month_change,
        "transaction_count": transaction_count,
        "card_count": card_count,
        "months_of_data": months_of_data,
        "monthly_average": monthly_average,
        "monthly_average_display": format_inr(monthly_average),
        "above_below_avg": above_below_avg,
        "above_avg_is_bad": above_avg_is_bad,
        "monthly_chart": monthly_chart,
        "category_chart": category_chart,
        "bank_chart": bank_chart,
        "recent_transactions": recent_transactions,
        "behavioral_insights": behavioral_insights,
        # Legacy fields for backward compatibility
        "total_debit": total_spend,
        "total_credit": total_credit,
        "net_cashflow": stats["net_cashflow_paise"] / 100,
        "category_count": stats["category_count"],
        "earliest_date": stats["earliest_date"],
        "latest_date": stats["latest_date"],
        "monthly_summary": monthly,
        "categories": categories,
    }


@router.get("/api/analytics")
def get_analytics():
    """Get detailed analytics data."""
    db = get_db()
    
    # Get all transactions
    raw = db.get_all_transactions()
    transactions = [enrich_transaction(dict(t)) for t in raw]
    
    # Filter to debit transactions for spending analysis
    debit_transactions = [t for t in transactions if t.get("type") == "debit"]
    
    # Spending by category over time
    category_trends = db.get_category_totals_by_month()
    
    # Calculate monthly spending for trend analysis
    from collections import defaultdict
    from datetime import datetime
    
    monthly_totals = defaultdict(float)
    for t in debit_transactions:
        month_key = t.get("month_key") or t.get("date_iso", "")[:7]
        if month_key:
            monthly_totals[month_key] += t.get("amount", 0)
    
    # Sort months and create spending trend
    sorted_months = sorted(monthly_totals.keys())
    spending_trend = []
    if sorted_months:
        avg_monthly = sum(monthly_totals.values()) / len(monthly_totals)
        for month in sorted_months:
            spending_trend.append({
                "month": month,
                "amount": monthly_totals[month],
                "average": avg_monthly,
            })
    
    # Find highest month
    highest_month = ""
    highest_month_amount = "₹0"
    if sorted_months:
        highest = max(sorted_months, key=lambda m: monthly_totals[m])
        highest_month = highest
        highest_month_amount = format_inr(monthly_totals[highest])
    
    # Calculate average monthly
    avg_monthly = 0
    if monthly_totals:
        avg_monthly = sum(monthly_totals.values()) / len(monthly_totals)
    
    # Top merchants with count
    merchant_data = defaultdict(lambda: {"amount": 0, "count": 0})
    for t in debit_transactions:
        desc = t.get("description_display", t.get("description", ""))
        merchant_data[desc]["amount"] += t.get("amount", 0)
        merchant_data[desc]["count"] += 1
    
    top_merchants = sorted(
        [{
            "name": k,
            "merchant": k,
            "amount": v["amount"],
            "amount_display": format_inr(v["amount"]),
            "count": v["count"],
            "count_display": f"{v['count']}x",
        } for k, v in merchant_data.items()],
        key=lambda x: x["amount"],
        reverse=True,
    )[:10]
    
    # Find biggest transaction
    biggest_txn_amount = "₹0"
    biggest_txn_desc = "No data"
    if debit_transactions:
        biggest = max(debit_transactions, key=lambda t: t.get("amount", 0))
        biggest_txn_amount = format_inr(biggest.get("amount", 0))
        biggest_txn_desc = biggest.get("description_display", biggest.get("description", ""))[:30]
    
    # Count unique merchants
    unique_merchants = len(merchant_data)
    unique_merchants_display = f"{unique_merchants}"
    
    # Day of week analysis
    day_of_week_totals = defaultdict(lambda: {"amount": 0, "count": 0})
    day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for t in debit_transactions:
        date_str = t.get("date_iso") or t.get("date", "")
        if date_str:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                day_idx = dt.weekday()  # 0 = Monday
                day_of_week_totals[day_idx]["amount"] += t.get("amount", 0)
                day_of_week_totals[day_idx]["count"] += 1
            except:
                pass
    
    day_of_week_data = []
    for i, day in enumerate(day_names):
        day_of_week_data.append({
            "day": day,
            "amount": day_of_week_totals[i]["amount"],
            "count": day_of_week_totals[i]["count"],
        })
    
    # Recurring charges detection (transactions appearing 2+ times)
    recurring_candidates = {k: v for k, v in merchant_data.items() if v["count"] >= 2}
    recurring_charges = []
    for desc, data in sorted(recurring_candidates.items(), key=lambda x: x[1]["count"], reverse=True)[:10]:
        avg_amount = data["amount"] / data["count"]
        recurring_charges.append({
            "description": desc,
            "frequency": data["count"],
            "frequency_display": f"{data['count']}x",
            "avg_amount": avg_amount,
            "avg_display": format_inr(avg_amount),
            "annual_display": format_inr(avg_amount * 12),
        })
    
    # Largest transactions (top 10)
    sorted_by_amount = sorted(debit_transactions, key=lambda t: t.get("amount", 0), reverse=True)[:10]
    largest_transactions = []
    for rank, t in enumerate(sorted_by_amount, 1):
        largest_transactions.append({
            "rank": rank,
            "id": t.get("id"),
            "date": t.get("date_iso") or t.get("date", ""),
            "date_display": format_date_display(t.get("date_iso") or t.get("date", "")),
            "description": t.get("description", ""),
            "description_display": t.get("description_display", t.get("description", ""))[:40],
            "amount": t.get("amount", 0),
            "amount_display": format_inr(t.get("amount", 0)),
            "bank": t.get("bank", ""),
        })
    
    return {
        # Monthly stats
        "highest_month": highest_month,
        "highest_month_amount": highest_month_amount,
        "avg_monthly": avg_monthly,
        "avg_monthly_display": format_inr(avg_monthly),
        "biggest_txn_amount": biggest_txn_amount,
        "biggest_txn_desc": biggest_txn_desc,
        "unique_merchants": unique_merchants,
        "unique_merchants_display": unique_merchants_display,
        "transaction_count": len(debit_transactions),
        
        # Charts data
        "spending_trend": spending_trend,
        "day_of_week_data": day_of_week_data,
        "top_merchants": top_merchants,
        "recurring_charges": recurring_charges,
        "largest_transactions": largest_transactions,
        
        # Legacy fields
        "category_trends": category_trends,
    }


@router.get("/api/dashboard/summary")
def api_dashboard_summary():
    """Get dashboard summary with insights, recent transactions, and behavioral metrics."""
    db = get_db()
    
    # Get recent transactions (latest 10)
    recent_result = db.get_all_transactions_with_bank({}, page=1, per_page=10)
    recent_transactions = [enrich_transaction(dict(t)) for t in recent_result.items]
    
    # Get all transactions for insights and monthly calculations
    raw = db.get_all_transactions()
    transactions = [enrich_transaction(dict(t)) for t in raw]
    
    # Calculate this month vs last month
    monthly_totals = defaultdict(float)
    income_totals = defaultdict(float)
    for t in transactions:
        if t.get("month_key"):
            if t.get("type") == "debit":
                monthly_totals[t["month_key"]] += t.get("amount", 0)
            elif t.get("type") == "credit":
                income_totals[t["month_key"]] += t.get("amount", 0)
    
    months = sorted(monthly_totals.keys())
    this_month = months[-1] if months else None
    last_month = months[-2] if len(months) > 1 else None
    
    this_month_total = monthly_totals.get(this_month, 0) if this_month else 0
    this_month_income = income_totals.get(this_month, 0) if this_month else 0
    last_month_total = monthly_totals.get(last_month, 0) if last_month else 0
    
    # Calculate behavioral metrics
    # Net cash flow (income - expenses for this month)
    net_cash_flow = this_month_income - this_month_total
    
    # Savings rate (savings / income)
    savings_rate = (net_cash_flow / this_month_income) if this_month_income > 0 else 0
    
    # EMI ratio (calculate from transactions with EMI in description)
    emi_total = sum(
        t.get("amount", 0) for t in transactions 
        if t.get("type") == "debit" and "emi" in (t.get("description", "")).lower()
    )
    emi_ratio = (emi_total / this_month_income) if this_month_income > 0 else 0
    
    # Buffer days (months of runway if no income)
    # Simplified: assume daily spend rate continues
    days_in_month = 30
    daily_spend = this_month_total / days_in_month if days_in_month > 0 else 0
    buffer_days = (net_cash_flow / daily_spend) if daily_spend > 0 else 0
    
    # Calculate 7-day trend from recent transactions
    from datetime import datetime, timedelta
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    fourteen_days_ago = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
    
    recent_7_day_spend = sum(
        t.get("amount", 0) for t in transactions
        if t.get("type") == "debit" and t.get("parsed_date", "") >= seven_days_ago
    )
    previous_7_day_spend = sum(
        t.get("amount", 0) for t in transactions
        if t.get("type") == "debit" 
        and fourteen_days_ago <= t.get("parsed_date", "") < seven_days_ago
    )
    
    seven_day_trend = 0
    if previous_7_day_spend > 0:
        seven_day_trend = (recent_7_day_spend - previous_7_day_spend) / previous_7_day_spend
    elif recent_7_day_spend > 0:
        seven_day_trend = 1.0
    
    # Category drift alert (check if any category is >30% above average)
    category_monthly = defaultdict(lambda: defaultdict(float))
    for t in transactions:
        if t.get("type") == "debit" and t.get("month_key"):
            category_monthly[t.get("category", "Uncategorized")][t["month_key"]] += t.get("amount", 0)
    
    category_drift_alert = None
    for cat, monthly_data in category_monthly.items():
        if len(monthly_data) >= 2:
            this_month_cat = monthly_data.get(this_month, 0)
            other_months = [v for k, v in monthly_data.items() if k != this_month]
            if other_months:
                avg_other = sum(other_months) / len(other_months)
                if avg_other > 0 and this_month_cat > avg_other * 1.3:
                    if category_drift_alert is None:
                        category_drift_alert = f"Spending on {cat} is up {int((this_month_cat/avg_other - 1) * 100)}% this month"
    
    # Generate insights
    insights = compute_behavioral_insights(transactions)
    
    # Compute financial health score using behavior engine
    profile = compute_behavior_profile(db)
    financial_health_score = profile.get("financial_health_score", 50)
    
    return {
        "this_month": {
            "month": this_month,
            "total": this_month_total,
            "formatted": format_inr(this_month_total),
        },
        "last_month": {
            "month": last_month,
            "total": last_month_total,
            "formatted": format_inr(last_month_total),
        },
        "change": percentage_change(this_month_total, last_month_total),
        "insights": insights,
        "recent_transactions": recent_transactions,
        # Behavioral metrics for dashboard
        "net_cash_flow": net_cash_flow,
        "savings_rate": max(0, min(1, savings_rate)),  # Clamp to 0-1
        "emi_ratio": emi_ratio,
        "buffer_days": max(0, buffer_days),
        "financial_health_score": financial_health_score,
        "seven_day_trend": seven_day_trend,
        "category_drift_alert": category_drift_alert,
    }


@router.get("/api/statements")
def get_statements(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Get imported statements with pagination."""
    db = get_db()
    result = db.get_statements_paginated(page=page, per_page=per_page)
    return {
        "statements": result["items"],
        "pagination": {
            "page": result["page"],
            "per_page": result["per_page"],
            "total": result["total"],
            "has_next": result["has_next"],
        }
    }


@router.get("/api/statements/{statement_id}/validate")
def api_validate_statement(statement_id: int):
    """Validate a statement's balance."""
    db = get_db()
    # Get statement
    statements = db.get_all_statements_with_metadata()
    statement = next((s for s in statements if s["id"] == statement_id), None)
    
    if not statement:
        raise NotFoundError("Statement", statement_id)
    
    return {
        "statement_id": statement_id,
        "validation_status": statement.get("validation_status", "unknown"),
        "total_amount_due": statement.get("total_amount_due"),
        "total_debit": statement.get("total_debit"),
        "difference": statement.get("validation_difference"),
    }


@router.delete("/api/statements/{statement_id}")
def api_delete_statement(statement_id: int):
    """Delete a statement and all its transactions."""
    db = get_db()
    
    # Check if statement exists
    statements = db.get_all_statements_with_metadata()
    statement = next((s for s in statements if s["id"] == statement_id), None)
    
    if not statement:
        raise NotFoundError("Statement", statement_id)
    
    # Delete the statement
    db.delete_statement(statement_id)
    log.info("Statement deleted: %s", statement_id)
    
    return {"success": True, "message": "Statement deleted successfully"}


@router.get("/api/export/csv")
def api_export_csv(
    search: Optional[str] = None,
    bank: Optional[str] = None,
    category: Optional[str] = None,
    type: Optional[str] = None,
):
    """Export transactions as CSV."""
    db = get_db()
    
    # Build filters
    filters = {}
    if search:
        filters["search"] = search
    if bank:
        filters["bank"] = bank
    if category:
        filters["category"] = category
    if type:
        filters["type"] = type
    
    # Get all transactions matching filters (no pagination for export)
    transactions = db.get_all_transactions(filters)
    
    # Build CSV content
    import csv
    import io
    from datetime import datetime
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Date", "Description", "Amount", "Type", "Category", "Bank", "Member"])
    
    # Write data
    for txn in transactions:
        writer.writerow([
            txn.get("date", ""),
            txn.get("description", ""),
            txn.get("amount", 0),
            txn.get("type", ""),
            txn.get("category", "Uncategorized"),
            txn.get("bank", ""),
            txn.get("member", "Self"),
        ])
    
    # Get the CSV content
    csv_content = output.getvalue()
    output.close()
    
    # Return as plain text with CSV content type
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


# ============================================================
# Cash Flow Endpoints
# ============================================================

@router.get("/api/cashflow/monthly")
def api_cashflow_monthly(
    months: int = Query(12, ge=1, le=60),
):
    """
    Get monthly cash flow data.
    
    Args:
        months: Number of months to look back (default 12, max 60)
    
    Returns:
        List of monthly cashflow metrics including income, expenses, 
        net cashflow, savings rate, and transaction count.
    """
    db = get_db()
    result = compute_monthly_cashflow(db, months=months)
    return {
        "months": result,
        "count": len(result),
    }


def sanitize_for_json(obj):
    """Replace inf/nan with 0 to ensure JSON compliance."""
    if isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return 0
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_json(i) for i in obj]
    return obj

@router.get("/api/cashflow/breakdown")
def api_cashflow_breakdown(
    month: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
):
    """
    Get detailed cash flow breakdown for a specific month.

    Args:
        month: Month in YYYY-MM format, or None for current month

    Returns:
        Detailed breakdown including fixed/variable expenses,
        income by source, expense by category, daily burn rate,
        liquid assets, and runway months.
    """
    db = get_db()
    result = compute_cashflow_breakdown(db, month=month)
    result = sanitize_for_json(result)
    return result


@router.get("/api/cashflow/summary")
def api_cashflow_summary():
    """
    Get comprehensive cash flow summary over all available data.
    
    Returns:
        Summary including average monthly income/expense, savings rate,
        best/worst months, positive/negative month counts, and trend.
    """
    db = get_db()
    result = compute_cashflow_summary(db)
    return result


# ============================================================
# Net Worth Endpoints
# ============================================================

@router.get("/api/networth")
def api_networth():
    """
    Get current net worth summary.
    
    Returns:
        Total assets, liabilities, and net worth with breakdowns.
    """
    db = get_db()
    result = compute_net_worth(db)
    return result


@router.get("/api/networth/trend")
def api_networth_trend(
    months: int = Query(12, ge=1, le=60),
):
    """
    Get net worth trend over time.
    
    Args:
        months: Number of months to look back (default 12, max 60)
    
    Returns:
        List of monthly net worth snapshots.
    """
    db = get_db()
    result = compute_net_worth_trend(db, months=months)
    return {
        "trend": result,
        "count": len(result),
    }


@router.get("/api/networth/allocation")
def api_networth_allocation():
    """
    Get asset allocation breakdown.
    
    Returns:
        List of asset categories with values and percentages.
    """
    db = get_db()
    result = compute_asset_allocation(db)
    return {
        "allocation": result,
        "count": len(result),
    }
