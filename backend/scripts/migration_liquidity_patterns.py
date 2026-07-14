"""Migration for Liquidity Provider/Purpose Patterns - tables and seed data.

Idempotent: Uses CREATE TABLE IF NOT EXISTS pattern and INSERT OR IGNORE for seed data.
"""
import sqlite3
from pathlib import Path


def run_migration(db_path: str) -> None:
    """Create tables for liquidity extraction patterns."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Create liquidity_provider_patterns table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS liquidity_provider_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_name TEXT NOT NULL,
            description_pattern TEXT NOT NULL,
            fee_min_bps INTEGER DEFAULT 150,
            fee_max_bps INTEGER DEFAULT 400,
            review_fee_min_bps INTEGER DEFAULT 50,
            review_fee_max_bps INTEGER DEFAULT 800,
            typical_settlement_days INTEGER DEFAULT 2,
            is_active INTEGER DEFAULT 1,
            confirmed_by_user INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # Index for efficient lookups
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_liquidity_provider_active
        ON liquidity_provider_patterns(is_active)
    """)

    # Create liquidity_purpose_patterns table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS liquidity_purpose_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purpose TEXT NOT NULL,
            description_pattern TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_liquidity_purpose_active
        ON liquidity_purpose_patterns(is_active)
    """)

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        run_migration(sys.argv[1])
    else:
        run_migration(str(Path(__file__).parent.parent / "src" / "data" / "finance.db"))
