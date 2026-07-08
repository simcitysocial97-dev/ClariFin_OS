"""Cashflow endpoints."""
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from src.common import get_db

router = APIRouter(prefix="/api", tags=["cashflow"])


@router.get("/cashflow/monthly")
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
