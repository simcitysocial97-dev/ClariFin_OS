"""
Database migration for Financial Events persistence (Phase 6).

Creates tables:
- financial_events: First persistence layer for FinancialEvent model
- financial_event_links: Links between events (settles, funds, rolls_over)

All monetary values are INTEGER paise.
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")


def migrate(db_path: str | None = None) -> None:
    """Run financial events migration."""
    if db_path is None:
        db_path = DB_PATH
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys=ON")

    # Create financial_events table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Event classification
            event_type TEXT NOT NULL,
            
            -- Transaction linkage (JSON array stored as TEXT)
            transaction_ids TEXT NOT NULL,
            
            -- Amount fields
            amount_paise INTEGER DEFAULT 0,
            asset_change_paise INTEGER DEFAULT 0,
            liability_change_paise INTEGER DEFAULT 0,
            expense_paise INTEGER DEFAULT 0,
            income_paise INTEGER DEFAULT 0,
            
            -- Temporal fields
            date_iso TEXT NOT NULL,
            month_bucket TEXT NOT NULL,
            
            -- Account linkage
            account_id TEXT,
            counterparty_account_id TEXT,
            
            -- Categorization
            category TEXT,
            subcategory TEXT,
            sub_type TEXT,
            provider TEXT,
            
            -- Multi-user support
            household_id TEXT DEFAULT 'primary',
            owner_id TEXT DEFAULT 'self',
            
            -- Lifecycle tracking
            lifecycle_state TEXT DEFAULT 'open',
            settled_by_event_id INTEGER,
            outstanding_paise INTEGER DEFAULT 0,
            superseded_by INTEGER,
            
            -- Confidence (new authoritative field alongside deprecated float)
            confidence REAL DEFAULT 0.0,
            confidence_bps INTEGER,
            
            -- Notes
            notes TEXT,
            
            -- Audit
            reviewed_by_user INTEGER DEFAULT 0,
            
            -- Timestamps
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("✓ financial_events table created")

    # Create financial_event_links table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_event_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES financial_events(id),
            linked_event_id INTEGER NOT NULL REFERENCES financial_events(id),
            link_type TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    print("✓ financial_event_links table created")

    # Create indexes for efficient queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_events_month_bucket ON financial_events(month_bucket)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_events_household ON financial_events(household_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_events_account ON financial_events(account_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_events_lifecycle ON financial_events(lifecycle_state)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_events_type ON financial_events(event_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_event_links_event ON financial_event_links(event_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_financial_event_links_type ON financial_event_links(link_type)")
    print("✓ Indexes created")

    conn.commit()
    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()