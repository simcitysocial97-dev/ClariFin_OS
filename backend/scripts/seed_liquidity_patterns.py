"""Seed data for Liquidity Provider and Purpose Patterns.

Idempotent: Uses INSERT OR IGNORE to prevent duplicate inserts.
Run after migration_liquidity_patterns.py
"""
import sqlite3
from pathlib import Path


def run_seed(db_path: str) -> None:
    """Insert seed data for liquidity patterns."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Seed liquidity_provider_patterns
    provider_patterns = [
        # (provider_name, description_pattern, fee_min_bps, fee_max_bps, review_fee_min_bps, review_fee_max_bps, typical_settlement_days, is_active, confirmed_by_user)
        ("CRED", "(DREAMPLUG|CRED)", 150, 400, 50, 800, 2, 1, 1),
        ("Cheq", "(INFOLENZ|CHEQ)", 150, 400, 50, 800, 2, 1, 1),
        ("Spaid", "(SPAID)", 150, 400, 50, 800, 2, 1, 1),
        ("NoBroker", "(NOBROKER|SORTING-HAT)", 150, 400, 50, 800, 3, 1, 1),
    ]

    for pattern in provider_patterns:
        conn.execute("""
            INSERT OR IGNORE INTO liquidity_provider_patterns
                (provider_name, description_pattern, fee_min_bps, fee_max_bps,
                 review_fee_min_bps, review_fee_max_bps, typical_settlement_days, is_active, confirmed_by_user)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pattern)

    # Seed liquidity_purpose_patterns
    purpose_patterns = [
        # (purpose, description_pattern, is_active)
        ("Rent", "RENT", 1),
        ("Education", "(TUIT|EDU|FEE)", 1),
        ("Settlement_Inbound", "(SETTLE|REMIT|RECEIPT)", 1),
    ]

    for purpose in purpose_patterns:
        conn.execute("""
            INSERT OR IGNORE INTO liquidity_purpose_patterns
                (purpose, description_pattern, is_active)
            VALUES (?, ?, ?)
        """, purpose)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_seed(sys.argv[1])
    else:
        run_seed(str(Path(__file__).parent.parent / "src" / "data" / "finance.db"))