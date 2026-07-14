"""
Migration 005: Behaviour Engine Schema
=====================================
Creates behaviour_snapshots, behaviour_patterns, behaviour_alerts, and financial_profiles tables.
Stores all scores as INTEGER basis points (bps) for precision.

Run: cd backend && ./venv/bin/python3 scripts/migration_005_behaviour_engine.py
"""

import sqlite3
from pathlib import Path

DB_PATH = str(Path(__file__).parent.parent / "src" / "data" / "finance.db")

def run_migration(db_path: str | None = None) -> None:
    """Create behaviour engine tables if they don't exist."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    cursor = conn.cursor()

    # behaviour_snapshots table - stores daily behaviour metrics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviour_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            household_id TEXT NOT NULL DEFAULT 'default',
            savings_discipline_score_bps INTEGER NOT NULL,  -- Stored as basis points (10000 = 1.0)
            cashflow_stability_score_bps INTEGER NOT NULL,
            salary_dependence_ratio_bps INTEGER NOT NULL,
            lifestyle_inflation_rate_bps INTEGER NOT NULL,
            subscription_burn_rate_bps INTEGER NOT NULL,
            resilience_index_bps INTEGER NOT NULL,
            wellness_score_bps INTEGER NOT NULL,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(snapshot_date, household_id)
        )
    """)

    # behaviour_patterns table - stores detected behaviour patterns
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviour_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pattern_type TEXT NOT NULL,  -- IMPULSE, SUBSCRIPTION, NIGHT_SPEND, WEEKEND_SPEND, OVERSPEND
            pattern_key TEXT NOT NULL,   -- merchant name, category, or time pattern
            household_id TEXT NOT NULL DEFAULT 'default',
            strength_bps INTEGER NOT NULL,  -- 0-10000 (0.0-1.0)
            first_observed TEXT NOT NULL,
            last_observed TEXT NOT NULL,
            transaction_count INTEGER NOT NULL,
            total_amount_paise INTEGER NOT NULL,
            config_json TEXT,  -- Additional pattern configuration as JSON
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(pattern_type, pattern_key, household_id)
        )
    """)

    # behaviour_alerts table - stores generated alerts and recommendations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS behaviour_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_type TEXT NOT NULL,    -- LOW_BALANCE, HIGH_UTILIZATION, MISSED_INCOME, etc.
            alert_code TEXT NOT NULL,    -- Unique code for each alert type (e.g., LOW_BALANCE_001)
            household_id TEXT NOT NULL DEFAULT 'default',
            severity TEXT NOT NULL CHECK(severity IN ('HIGH', 'MEDIUM', 'LOW')),
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            action_url TEXT,
            is_acknowledged INTEGER NOT NULL DEFAULT 0,
            acknowledged_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            resolved_at TEXT,
            resolution_notes TEXT,
            metadata_json TEXT  -- Additional alert metadata as JSON
        )
    """)

    # financial_profiles table - stores financial personality profiles
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS financial_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_id TEXT NOT NULL DEFAULT 'default',
            profile_type TEXT NOT NULL CHECK(profile_type IN ('SAVER', 'SPENDER', 'BALANCED', 'DEBT_RISK', 'EMERGENCY_FOCUSED')),
            profile_score_bps INTEGER NOT NULL,  -- 0-10000 (0-100)
            last_assessed TEXT NOT NULL,
            income_stability_score_bps INTEGER NOT NULL,
            expense_stability_score_bps INTEGER NOT NULL,
            debt_health_score_bps INTEGER NOT NULL,
            savings_health_score_bps INTEGER NOT NULL,
            credit_health_score_bps INTEGER NOT NULL,
            risk_tolerance_score_bps INTEGER NOT NULL,
            financial_goals_progress_bps INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(household_id)
        )
    """)

    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_snapshots_date ON behaviour_snapshots(snapshot_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_snapshots_household ON behaviour_snapshots(household_id)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_patterns_type ON behaviour_patterns(pattern_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_patterns_household ON behaviour_patterns(household_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_patterns_last_observed ON behaviour_patterns(last_observed)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_alerts_household ON behaviour_alerts(household_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_alerts_severity ON behaviour_alerts(severity)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_alerts_acknowledged ON behaviour_alerts(is_acknowledged)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_behaviour_alerts_alert_code ON behaviour_alerts(alert_code)")

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_profiles_household ON financial_profiles(household_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_financial_profiles_type ON financial_profiles(profile_type)")

    conn.commit()
    conn.close()
    print("[MIGRATION 005] Behaviour engine tables created successfully.")

if __name__ == "__main__":
    run_migration()
