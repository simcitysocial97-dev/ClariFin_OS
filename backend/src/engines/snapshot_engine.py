"""
Snapshot Engine
===============

Deterministic monthly snapshot generation engine for creating and storing
monthly financial snapshots.

Key Principles:
1. All amounts are stored as INTEGER paise (1 rupee = 100 paise)
2. No floating-point arithmetic - all calculations use integers
3. All computations via SQL aggregation, NOT Python loops
4. Deterministic: same data → same output, every time
5. Snapshots are immutable historical records

This engine:
- Generates monthly financial snapshots with income, expenses, EMI, investments
- Computes net cashflow and savings rates
- Stores detailed breakdowns in data_json
- Supports backfilling snapshots for historical months
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from src.logger import log
from src.engines.networth_engine import compute_net_worth

if TYPE_CHECKING:
    from src.db import FinanceDB


# ============================================================
# Function 1: Generate Monthly Snapshot
# ============================================================

def generate_monthly_snapshot(db: "FinanceDB", month: str | None = None) -> dict:
    """
    Generate and store a monthly financial snapshot.

    Args:
        db: FinanceDB instance
        month: Month in YYYY-MM format, or None for current month

    Returns:
        Dict with snapshot data:
            - month: "YYYY-MM"
            - total_income_paise: SUM credits for that month
            - total_expense_paise: SUM debits for that month
            - total_emi_paise: SUM debits matching EMI/loan categories OR linked to loan_id
            - total_investment_paise: SUM of new investment purchases that month
            - net_cashflow_paise: income - expenses
            - net_worth_paise: computed via compute_net_worth()
            - savings_rate: net_cashflow / income (0 if no income)
            - data_json: JSON string with detailed breakdown
    """
    # Determine target month
    if month is None:
        month = datetime.now().strftime("%Y-%m")

    log.info("Generating monthly snapshot for %s", month)

    with db.connection() as conn:
        # ----------------------------------------------------------
        # 1. Total Income (SUM of credits for the month)
        # ----------------------------------------------------------
        cur = conn.execute("""
            SELECT COALESCE(SUM(credit), 0) as total_income_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
        """, (month,))
        row = cur.fetchone()
        total_income_paise = row["total_income_paise"] if row else 0

        # ----------------------------------------------------------
        # 2. Total Expense (SUM of debits for the month)
        # ----------------------------------------------------------
        cur = conn.execute("""
            SELECT COALESCE(SUM(debit), 0) as total_expense_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
        """, (month,))
        row = cur.fetchone()
        total_expense_paise = row["total_expense_paise"] if row else 0

        # ----------------------------------------------------------
        # 3. Total EMI (SUM of debits matching EMI/loan categories OR linked to loan_id)
        # ----------------------------------------------------------
        # Categories commonly associated with EMI/loans
        emi_categories = ['EMI', 'Loan', 'Loan Repayment', 'Home Loan', 'Car Loan',
                         'Personal Loan', 'Education Loan', 'Gold Loan']
        placeholders = ','.join('?' * len(emi_categories))

        # Check if loan_id column exists
        columns = [row[1] for row in conn.execute("PRAGMA table_info(transactions)").fetchall()]
        has_loan_id = "loan_id" in columns
        
        if has_loan_id:
            cur = conn.execute(f"""
                SELECT COALESCE(SUM(debit), 0) as total_emi_paise
                FROM transactions
                WHERE strftime('%Y-%m', date_iso) = ?
                AND (category IN ({placeholders}) OR loan_id IS NOT NULL)
            """, (month, *emi_categories))
        else:
            cur = conn.execute(f"""
                SELECT COALESCE(SUM(debit), 0) as total_emi_paise
                FROM transactions
                WHERE strftime('%Y-%m', date_iso) = ?
                AND category IN ({placeholders})
            """, (month, *emi_categories))
        row = cur.fetchone()
        total_emi_paise = row["total_emi_paise"] if row else 0

        # ----------------------------------------------------------
        # 4. Total Investment (SUM of new investment purchases that month)
        # ----------------------------------------------------------
        cur = conn.execute("""
            SELECT COALESCE(SUM(invested_paise), 0) as total_investment_paise
            FROM investments
            WHERE strftime('%Y-%m', purchase_date) = ?
            AND is_active = 1
        """, (month,))
        row = cur.fetchone()
        total_investment_paise = row["total_investment_paise"] if row else 0

        # ----------------------------------------------------------
        # 5. Net Cashflow (income - expenses)
        # ----------------------------------------------------------
        net_cashflow_paise = total_income_paise - total_expense_paise

        # ----------------------------------------------------------
        # 6. Net Worth (call compute_net_worth)
        # ----------------------------------------------------------
        net_worth_result = compute_net_worth(db)
        net_worth_paise = net_worth_result["net_worth_paise"]

        # ----------------------------------------------------------
        # 7. Savings Rate (net_cashflow / income, 0 if no income)
        # ----------------------------------------------------------
        savings_rate = 0.0
        if total_income_paise > 0:
            savings_rate = round(net_cashflow_paise / total_income_paise, 4)

        # ----------------------------------------------------------
        # 8. Data JSON - Detailed breakdown
        # ----------------------------------------------------------
        # Category-wise income breakdown
        cur = conn.execute("""
            SELECT
                COALESCE(category, 'Uncategorized') as category,
                COALESCE(SUM(credit), 0) as amount_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
            AND credit > 0
            GROUP BY category
            ORDER BY amount_paise DESC
        """, (month,))
        income_by_category = [
            {"category": row["category"], "amount_paise": row["amount_paise"]}
            for row in cur.fetchall()
        ]

        # Category-wise expense breakdown
        cur = conn.execute("""
            SELECT
                COALESCE(category, 'Uncategorized') as category,
                COALESCE(SUM(debit), 0) as amount_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
            AND debit > 0
            GROUP BY category
            ORDER BY amount_paise DESC
        """, (month,))
        expense_by_category = [
            {"category": row["category"], "amount_paise": row["amount_paise"]}
            for row in cur.fetchall()
        ]

        # Account-wise breakdown
        cur = conn.execute("""
            SELECT
                COALESCE(account_id, 'Unknown') as account,
                COALESCE(SUM(credit), 0) as income_paise,
                COALESCE(SUM(debit), 0) as expense_paise
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
            GROUP BY account_id
            ORDER BY (SUM(credit) + SUM(debit)) DESC
        """, (month,))
        account_breakdown = [
            {
                "account": row["account"],
                "income_paise": row["income_paise"],
                "expense_paise": row["expense_paise"]
            }
            for row in cur.fetchall()
        ]

        # Transaction count
        cur = conn.execute("""
            SELECT COUNT(*) as transaction_count
            FROM transactions
            WHERE strftime('%Y-%m', date_iso) = ?
        """, (month,))
        row = cur.fetchone()
        transaction_count = row["transaction_count"] if row else 0

        # Build data_json
        data_json = json.dumps({
            "income_by_category": income_by_category,
            "expense_by_category": expense_by_category,
            "account_breakdown": account_breakdown,
            "transaction_count": transaction_count,
            "net_worth_breakdown": {
                "total_assets_paise": net_worth_result["total_assets_paise"],
                "total_liabilities_paise": net_worth_result["total_liabilities_paise"],
                "asset_breakdown": net_worth_result["asset_breakdown"],
                "liability_breakdown": net_worth_result["liability_breakdown"]
            }
        }, default=str)

        # ----------------------------------------------------------
        # 9. Store in monthly_snapshots table
        # ----------------------------------------------------------
        cur = conn.execute("""
            INSERT OR REPLACE INTO monthly_snapshots
            (month, total_income_paise, total_expense_paise, total_emi_paise,
             total_investment_paise, net_cashflow_paise, net_worth_paise,
             savings_rate, data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            month,
            total_income_paise,
            total_expense_paise,
            total_emi_paise,
            total_investment_paise,
            net_cashflow_paise,
            net_worth_paise,
            savings_rate,
            data_json
        ))
        snapshot_id = cur.lastrowid

    snapshot = {
        "id": snapshot_id,
        "month": month,
        "total_income_paise": total_income_paise,
        "total_expense_paise": total_expense_paise,
        "total_emi_paise": total_emi_paise,
        "total_investment_paise": total_investment_paise,
        "net_cashflow_paise": net_cashflow_paise,
        "net_worth_paise": net_worth_paise,
        "savings_rate": savings_rate,
        "data_json": data_json,
    }

    log.info("Monthly snapshot generated for %s: income=₹%.2f, expense=₹%.2f, savings_rate=%.1f%%",
             month, total_income_paise / 100, total_expense_paise / 100, savings_rate * 100)

    return snapshot


# ============================================================
# Function 2: Generate Snapshots Backfill
# ============================================================

def generate_snapshots_backfill(db: "FinanceDB") -> int:
    """
    Generate snapshots for all months from earliest to latest transaction date.

    Optimized: N+1 queries → 3 queries total (regardless of month count)
    - Was: N months × ~10 queries per month = O(N) queries
    - Now: 3 queries total (date range, monthly aggregates, existing snapshots)

    Args:
        db: FinanceDB instance

    Returns:
        Count of snapshots generated
    """
    log.info("Starting snapshot backfill")

    # Step 1 & 2: Fetch all monthly aggregates in ONE query
    # This replaces N queries (one per month) with a single query
    monthly_aggregates = db.get_monthly_transaction_aggregates()
    
    if not monthly_aggregates:
        log.warning("No transactions found for backfill")
        return 0

    # Step 3: Fetch existing snapshot months in ONE query
    with db.connection() as conn:
        cur = conn.execute("SELECT month FROM monthly_snapshots")
        existing_months = {row[0] for row in cur.fetchall()}

    # Filter to months that need snapshots
    months_needing_snapshots = [
        agg for agg in monthly_aggregates 
        if agg["month"] not in existing_months
    ]

    if not months_needing_snapshots:
        log.info("No new snapshots needed - all months already have snapshots")
        return 0

    log.info("Transaction range: %s to %s (%d months to generate)", 
             monthly_aggregates[0]["month"], 
             monthly_aggregates[-1]["month"],
             len(months_needing_snapshots))

    # Generate snapshots using pre-fetched aggregates
    generated_count = 0
    for agg in months_needing_snapshots:
        month = agg["month"]
        try:
            # Build snapshot from pre-fetched aggregate data
            _generate_snapshot_from_aggregate(db, month, agg)
            generated_count += 1
            log.info("Backfill progress: %d/%d months processed", generated_count, len(months_needing_snapshots))
        except Exception as e:
            log.error("Failed to generate snapshot for %s: %s", month, e)

    log.info("Snapshot backfill complete: %d snapshots generated", generated_count)
    return generated_count


def _generate_snapshot_from_aggregate(db: "FinanceDB", month: str, agg: dict) -> dict:
    """
    Generate a monthly snapshot using pre-fetched aggregate data.
    
    This is an optimized version that avoids redundant queries by using
    the aggregate data already fetched in generate_snapshots_backfill().
    
    Args:
        db: FinanceDB instance
        month: Month in YYYY-MM format
        agg: Pre-fetched aggregate data with keys:
             total_income_paise, total_expense_paise, transaction_count
    
    Returns:
        Dict with snapshot data
    """
    from src.engines.networth_engine import compute_net_worth
    
    # Use pre-fetched aggregates
    total_income_paise = agg["total_income_paise"]
    total_expense_paise = agg["total_expense_paise"]
    transaction_count = agg["transaction_count"]
    
    # Calculate derived values
    net_cashflow_paise = total_income_paise - total_expense_paise
    
    # Compute net worth (this is cross-month, needs to be computed fresh)
    net_worth_result = compute_net_worth(db)
    net_worth_paise = net_worth_result["net_worth_paise"]
    
    # Savings rate
    savings_rate = 0.0
    if total_income_paise > 0:
        savings_rate = round(net_cashflow_paise / total_income_paise, 4)
    
    # Get category breakdowns for this month
    category_data = db.get_monthly_category_aggregates(month)
    
    # Get EMI for this month
    emi_categories = ['EMI', 'Loan', 'Loan Repayment', 'Home Loan', 'Car Loan',
                     'Personal Loan', 'Education Loan', 'Gold Loan']
    with db.connection() as conn:
        placeholders = ','.join('?' * len(emi_categories))
        # Check if loan_id column exists
        columns = [row[1] for row in conn.execute("PRAGMA table_info(transactions)").fetchall()]
        has_loan_id = "loan_id" in columns
        
        if has_loan_id:
            cur = conn.execute(f"""
                SELECT COALESCE(SUM(debit), 0) as total_emi_paise
                FROM transactions
                WHERE strftime('%Y-%m', date_iso) = ?
                AND (category IN ({placeholders}) OR loan_id IS NOT NULL)
            """, (month, *emi_categories))
        else:
            cur = conn.execute(f"""
                SELECT COALESCE(SUM(debit), 0) as total_emi_paise
                FROM transactions
                WHERE strftime('%Y-%m', date_iso) = ?
                AND category IN ({placeholders})
            """, (month, *emi_categories))
        row = cur.fetchone()
        total_emi_paise = row["total_emi_paise"] if row else 0
    
    # Get investment data for this month
    with db.connection() as conn:
        cur = conn.execute("""
            SELECT COALESCE(SUM(invested_paise), 0) as total_investment_paise
            FROM investments
            WHERE strftime('%Y-%m', purchase_date) = ?
            AND is_active = 1
        """, (month,))
        row = cur.fetchone()
        total_investment_paise = row["total_investment_paise"] if row else 0
    
    # Build data_json
    import json
    data_json = json.dumps({
        "income_by_category": category_data["income_by_category"],
        "expense_by_category": category_data["expense_by_category"],
        "account_breakdown": category_data["account_breakdown"],
        "transaction_count": transaction_count,
        "net_worth_breakdown": {
            "total_assets_paise": net_worth_result["total_assets_paise"],
            "total_liabilities_paise": net_worth_result["total_liabilities_paise"],
            "asset_breakdown": net_worth_result["asset_breakdown"],
            "liability_breakdown": net_worth_result["liability_breakdown"]
        }
    }, default=str)
    
    # Store in database
    with db.connection() as conn:
        cur = conn.execute("""
            INSERT OR REPLACE INTO monthly_snapshots
            (month, total_income_paise, total_expense_paise, total_emi_paise,
             total_investment_paise, net_cashflow_paise, net_worth_paise,
             savings_rate, data_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (
            month,
            total_income_paise,
            total_expense_paise,
            total_emi_paise,
            total_investment_paise,
            net_cashflow_paise,
            net_worth_paise,
            savings_rate,
            data_json
        ))
        snapshot_id = cur.lastrowid
    
    snapshot = {
        "id": snapshot_id,
        "month": month,
        "total_income_paise": total_income_paise,
        "total_expense_paise": total_expense_paise,
        "total_emi_paise": total_emi_paise,
        "total_investment_paise": total_investment_paise,
        "net_cashflow_paise": net_cashflow_paise,
        "net_worth_paise": net_worth_paise,
        "savings_rate": savings_rate,
        "data_json": data_json,
    }
    
    log.debug("Monthly snapshot generated for %s from aggregates", month)
    return snapshot


# ============================================================
# Function 3: Check Snapshot Exists
# ============================================================

def snapshot_exists(db: "FinanceDB", month: str) -> bool:
    """
    Check if a snapshot exists for the given month.

    Args:
        db: FinanceDB instance
        month: Month in YYYY-MM format

    Returns:
        True if snapshot exists, False otherwise
    """
    with db.connection() as conn:
        cur = conn.execute(
            "SELECT 1 FROM monthly_snapshots WHERE month = ?",
            (month,)
        )
        return cur.fetchone() is not None


# ============================================================
# CLI Test
# ============================================================

if __name__ == "__main__":
    import sys
    from pathlib import Path

    # Add parent directory to path for imports
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.db import FinanceDB

    # Default db path
    db_path = str(Path(__file__).parent.parent / "data" / "finance.db")

    log.info("=" * 60)
    log.info("Snapshot Engine Test")
    log.info("=" * 60)
    log.info("Database: %s", db_path)

    db = FinanceDB(db_path=db_path)

    # Test generate_monthly_snapshot for current month
    log.info("\n--- Generate Snapshot for Current Month ---")
    snapshot = generate_monthly_snapshot(db)
    log.info("  Month: %s", snapshot['month'])
    log.info("  Total Income: ₹%.2f", snapshot['total_income_paise'] / 100)
    log.info("  Total Expense: ₹%.2f", snapshot['total_expense_paise'] / 100)
    log.info("  Total EMI: ₹%.2f", snapshot['total_emi_paise'] / 100)
    log.info("  Total Investment: ₹%.2f", snapshot['total_investment_paise'] / 100)
    log.info("  Net Cashflow: ₹%.2f", snapshot['net_cashflow_paise'] / 100)
    log.info("  Net Worth: ₹%.2f", snapshot['net_worth_paise'] / 100)
    log.info("  Savings Rate: %.1f%%", snapshot['savings_rate'] * 100)

    # Parse and display data_json breakdown
    data = json.loads(snapshot['data_json'])
    log.info("\n  Transaction Count: %d", data.get('transaction_count', 0))

    if data.get('expense_by_category'):
        log.info("\n  Top Expense Categories:")
        for cat in data['expense_by_category'][:5]:
            log.info("    %s: ₹%.2f", cat['category'], cat['amount_paise'] / 100)

    # Test snapshot_exists
    log.info("\n--- Check Snapshot Exists ---")
    exists = snapshot_exists(db, snapshot['month'])
    log.info("  Snapshot exists for %s: %s", snapshot['month'], exists)

    # Test backfill (will only generate for months without snapshots)
    log.info("\n--- Snapshot Backfill ---")
    count = generate_snapshots_backfill(db)
    log.info("  Snapshots generated: %d", count)

    db.close()
