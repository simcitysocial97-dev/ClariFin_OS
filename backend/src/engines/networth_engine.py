"""
Net Worth Engine
================

Deterministic net worth computation engine for calculating total assets,
liabilities, and net worth from accounts, investments, and loans tables.

Key Principles:
1. All amounts are stored as INTEGER paise (1 rupee = 100 paise)
2. No floating-point arithmetic - all calculations use integers
3. All computations via SQL aggregation, NOT Python loops
4. Deterministic: same data → same output, every time
"""

from typing import Dict, List, TYPE_CHECKING

from src.logger import log

if TYPE_CHECKING:
    from src.db import FinanceDB


# ============================================================
# Function 1: Compute Net Worth
# ============================================================

def compute_net_worth(db: "FinanceDB") -> dict:
    """
    Compute total assets, liabilities, and net worth.

    Args:
        db: FinanceDB instance

    Returns:
        Dict with:
            - total_assets_paise: SUM of all asset values
            - total_liabilities_paise: SUM of all liability values
            - net_worth_paise: assets - liabilities
            - asset_breakdown: dict with bank_accounts_paise, fixed_deposits_paise, investments_paise
            - liability_breakdown: dict with loans_paise, credit_cards_paise
    """
    log.info("Computing net worth")

    with db.connection() as conn:
        # Asset: Bank Accounts (savings, current, wallet)
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as bank_accounts_paise
            FROM accounts
            WHERE account_type IN ('savings', 'current', 'wallet')
            AND is_active = 1
        """)
        row = cur.fetchone()
        bank_accounts_paise = row["bank_accounts_paise"] if row else 0

        # Asset: Fixed Deposits
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as fixed_deposits_paise
            FROM accounts
            WHERE account_type = 'fd'
            AND is_active = 1
        """)
        row = cur.fetchone()
        fixed_deposits_paise = row["fixed_deposits_paise"] if row else 0

        # Asset: Investments (active only)
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as investments_paise
            FROM investments
            WHERE is_active = 1
        """)
        row = cur.fetchone()
        investments_paise = row["investments_paise"] if row else 0

        # Liability: Loans (active only)
        cur = conn.execute("""
            SELECT COALESCE(SUM(outstanding_paise), 0) as loans_paise
            FROM loans
            WHERE status = 'active'
        """)
        row = cur.fetchone()
        loans_paise = row["loans_paise"] if row else 0

        # Liability: Credit Cards (balance_paise represents amount owed)
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as credit_cards_paise
            FROM accounts
            WHERE account_type = 'credit_card'
            AND is_active = 1
        """)
        row = cur.fetchone()
        credit_cards_paise = row["credit_cards_paise"] if row else 0

    # Calculate totals
    total_assets_paise = bank_accounts_paise + fixed_deposits_paise + investments_paise
    total_liabilities_paise = loans_paise + credit_cards_paise
    net_worth_paise = total_assets_paise - total_liabilities_paise

    result = {
        "total_assets_paise": total_assets_paise,
        "total_liabilities_paise": total_liabilities_paise,
        "net_worth_paise": net_worth_paise,
        "asset_breakdown": {
            "bank_accounts_paise": bank_accounts_paise,
            "fixed_deposits_paise": fixed_deposits_paise,
            "investments_paise": investments_paise,
        },
        "liability_breakdown": {
            "loans_paise": loans_paise,
            "credit_cards_paise": credit_cards_paise,
        },
    }

    log.info("Net worth computed: assets=₹%.2f, liabilities=₹%.2f, net=₹%.2f",
             total_assets_paise / 100, total_liabilities_paise / 100, net_worth_paise / 100)
    return result


# ============================================================
# Function 2: Compute Net Worth Trend
# ============================================================

def compute_net_worth_trend(db: "FinanceDB", months: int = 12) -> list[dict]:
    """
    Query monthly_snapshots table for the last N months.

    Args:
        db: FinanceDB instance
        months: Number of months to look back (default 12)

    Returns:
        List of dicts with:
            - month: "YYYY-MM"
            - net_worth_paise
            - total_assets_paise
            - total_liabilities_paise
        Sorted by month ascending (oldest first).
        Returns empty list if no snapshots exist.
    """
    log.info("Computing net worth trend for last %d months", months)

    with db.connection() as conn:
        # Check if snapshots table exists and has data
        cur = conn.execute("SELECT 1 FROM monthly_snapshots LIMIT 1")
        if not cur.fetchone():
            log.warning("No monthly snapshots found for trend computation")
            return []

        # Query snapshots for the last N months
        sql = """
            SELECT
                month,
                COALESCE(net_worth_paise, 0) as net_worth_paise,
                COALESCE(
                    (SELECT SUM(balance_paise) FROM accounts WHERE is_active = 1),
                    0
                ) +
                COALESCE(
                    (SELECT SUM(current_value_paise) FROM investments WHERE is_active = 1),
                    0
                ) as total_assets_paise,
                COALESCE(
                    (SELECT SUM(outstanding_paise) FROM loans WHERE status = 'active'),
                    0
                ) +
                COALESCE(
                    (SELECT SUM(balance_paise) FROM accounts WHERE account_type = 'credit_card' AND is_active = 1),
                    0
                ) as total_liabilities_paise
            FROM monthly_snapshots
            ORDER BY month DESC
            LIMIT ?
        """
        cur = conn.execute(sql, (months,))
        rows = cur.fetchall()

    # Reverse to get ascending order (oldest first)
    results = []
    for row in reversed(rows):
        results.append({
            "month": row["month"],
            "net_worth_paise": row["net_worth_paise"],
            "total_assets_paise": row["total_assets_paise"],
            "total_liabilities_paise": row["total_liabilities_paise"],
        })

    log.info("Net worth trend computed for %d months", len(results))
    return results


# ============================================================
# Function 3: Compute Asset Allocation
# ============================================================

def compute_asset_allocation(db: "FinanceDB") -> list[dict]:
    """
    Combine accounts and investments into allocation buckets.

    Args:
        db: FinanceDB instance

    Returns:
        List of dicts with:
            - category: Allocation category name
            - value_paise: Total value in paise
            - percentage: Percentage of total assets (0-100)
        Categories: "Bank Accounts", "Fixed Deposits", "Mutual Funds",
                   "Stocks", "PPF/EPF/NPS", "Gold", "Real Estate",
                   "Crypto", "Other"
    """
    log.info("Computing asset allocation")

    with db.connection() as conn:
        # Bank Accounts (savings, current, wallet)
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as value_paise
            FROM accounts
            WHERE account_type IN ('savings', 'current', 'wallet')
            AND is_active = 1
        """)
        row = cur.fetchone()
        bank_accounts_paise = row["value_paise"] if row else 0

        # Fixed Deposits (from accounts table)
        cur = conn.execute("""
            SELECT COALESCE(SUM(balance_paise), 0) as value_paise
            FROM accounts
            WHERE account_type = 'fd'
            AND is_active = 1
        """)
        row = cur.fetchone()
        fixed_deposits_paise = row["value_paise"] if row else 0

        # Mutual Funds
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type = 'mutual_fund'
            AND is_active = 1
        """)
        row = cur.fetchone()
        mutual_funds_paise = row["value_paise"] if row else 0

        # Stocks
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type = 'stock'
            AND is_active = 1
        """)
        row = cur.fetchone()
        stocks_paise = row["value_paise"] if row else 0

        # PPF/EPF/NPS
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type IN ('ppf', 'epf', 'nps')
            AND is_active = 1
        """)
        row = cur.fetchone()
        retirement_paise = row["value_paise"] if row else 0

        # Gold
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type = 'gold'
            AND is_active = 1
        """)
        row = cur.fetchone()
        gold_paise = row["value_paise"] if row else 0

        # Real Estate
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type = 'real_estate'
            AND is_active = 1
        """)
        row = cur.fetchone()
        real_estate_paise = row["value_paise"] if row else 0

        # Crypto
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type = 'crypto'
            AND is_active = 1
        """)
        row = cur.fetchone()
        crypto_paise = row["value_paise"] if row else 0

        # Other investments
        cur = conn.execute("""
            SELECT COALESCE(SUM(current_value_paise), 0) as value_paise
            FROM investments
            WHERE type = 'other'
            AND is_active = 1
        """)
        row = cur.fetchone()
        other_paise = row["value_paise"] if row else 0

    # Calculate total
    total_assets_paise = (
        bank_accounts_paise + fixed_deposits_paise + mutual_funds_paise +
        stocks_paise + retirement_paise + gold_paise +
        real_estate_paise + crypto_paise + other_paise
    )

    # Build allocation list with percentages
    allocation = [
        {"category": "Bank Accounts", "value_paise": bank_accounts_paise},
        {"category": "Fixed Deposits", "value_paise": fixed_deposits_paise},
        {"category": "Mutual Funds", "value_paise": mutual_funds_paise},
        {"category": "Stocks", "value_paise": stocks_paise},
        {"category": "PPF/EPF/NPS", "value_paise": retirement_paise},
        {"category": "Gold", "value_paise": gold_paise},
        {"category": "Real Estate", "value_paise": real_estate_paise},
        {"category": "Crypto", "value_paise": crypto_paise},
        {"category": "Other", "value_paise": other_paise},
    ]

    # Calculate percentages
    for item in allocation:
        if total_assets_paise > 0:
            item["percentage"] = round((item["value_paise"] / total_assets_paise) * 100, 2)
        else:
            item["percentage"] = 0.0

    # Sort by value descending
    allocation.sort(key=lambda x: x["value_paise"], reverse=True)

    log.info("Asset allocation computed: %d categories, total=₹%.2f",
             len(allocation), total_assets_paise / 100)
    return allocation


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
    log.info("Net Worth Engine Test")
    log.info("=" * 60)
    log.info("Database: %s", db_path)

    db = FinanceDB(db_path=db_path)

    # Test compute_net_worth
    log.info("\n--- Net Worth Summary ---")
    net_worth = compute_net_worth(db)
    log.info("  Total Assets: ₹%.2f", net_worth['total_assets_paise'] / 100)
    log.info("  Total Liabilities: ₹%.2f", net_worth['total_liabilities_paise'] / 100)
    log.info("  Net Worth: ₹%.2f", net_worth['net_worth_paise'] / 100)
    log.info("\n  Asset Breakdown:")
    log.info("    Bank Accounts: ₹%.2f", net_worth['asset_breakdown']['bank_accounts_paise'] / 100)
    log.info("    Fixed Deposits: ₹%.2f", net_worth['asset_breakdown']['fixed_deposits_paise'] / 100)
    log.info("    Investments: ₹%.2f", net_worth['asset_breakdown']['investments_paise'] / 100)
    log.info("\n  Liability Breakdown:")
    log.info("    Loans: ₹%.2f", net_worth['liability_breakdown']['loans_paise'] / 100)
    log.info("    Credit Cards: ₹%.2f", net_worth['liability_breakdown']['credit_cards_paise'] / 100)

    # Test compute_net_worth_trend
    log.info("\n--- Net Worth Trend (last 12 months) ---")
    trend = compute_net_worth_trend(db, months=12)
    if trend:
        for t in trend:
            log.info("  %s: Net=₹%.2f, Assets=₹%.2f, Liabilities=₹%.2f",
                     t['month'],
                     t['net_worth_paise'] / 100,
                     t['total_assets_paise'] / 100,
                     t['total_liabilities_paise'] / 100)
    else:
        log.info("  No snapshot data available")

    # Test compute_asset_allocation
    log.info("\n--- Asset Allocation ---")
    allocation = compute_asset_allocation(db)
    for item in allocation:
        if item['value_paise'] > 0:
            log.info("  %s: ₹%.2f (%.1f%%)",
                     item['category'],
                     item['value_paise'] / 100,
                     item['percentage'])

    db.close()
