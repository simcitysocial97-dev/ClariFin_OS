"""
ClariFin Database Maintenance
==============================
Standalone script for database health checks, backups, and optimization.
Run: python3 -m src.maintenance [command]
"""

import sys
import json
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from src.logger import log
from src.db import FinanceDB

DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"


def cmd_status(db_path: str):
    """Show database size, table counts, and health."""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print("❌ Database not found:", db_path)
        return
    
    size_mb = db_file.stat().st_size / (1024 * 1024)
    print(f"Database: {db_path}")
    print(f"Size: {size_mb:.2f} MB")
    
    db = FinanceDB(db_path)
    with db.connection() as conn:
        # Table row counts
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        
        print(f"\nTables ({len(tables)}):")
        total_rows = 0
        for table in tables:
            name = table[0]
            count = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
            total_rows += count
            print(f"  {name:30s} {count:>8,} rows")
        
        print(f"\n  {'TOTAL':30s} {total_rows:>8,} rows")
        
        # Index count
        idx_count = conn.execute(
            "SELECT COUNT(*) FROM sqlite_master WHERE type='index'"
        ).fetchone()[0]
        print(f"\nIndexes: {idx_count}")
        
        # WAL mode check
        journal = conn.execute("PRAGMA journal_mode").fetchone()[0]
        print(f"Journal mode: {journal}")
        
        # Integrity check
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        print(f"Integrity: {'✅ OK' if integrity == 'ok' else '❌ ' + integrity}")
        
        # Foreign key check
        fk_errors = conn.execute("PRAGMA foreign_key_check").fetchall()
        print(f"Foreign key violations: {'✅ None' if not fk_errors else f'❌ {len(fk_errors)} violations'}")
        if fk_errors:
            for err in fk_errors[:5]:
                print(f"  Table: {err[0]}, Row: {err[1]}, Ref: {err[2]}")
    
    db.close()


def cmd_vacuum(db_path: str):
    """Optimize database — reclaim space, rebuild indexes."""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print("❌ Database not found:", db_path)
        return
    
    size_before = db_file.stat().st_size
    
    conn = sqlite3.connect(db_path)
    conn.execute("VACUUM")
    conn.execute("ANALYZE")
    conn.close()
    
    size_after = db_file.stat().st_size
    saved = size_before - size_after
    print(f"Vacuumed: {size_before/1024/1024:.2f} MB → {size_after/1024/1024:.2f} MB (saved {saved/1024:.1f} KB)")


def cmd_backup(db_path: str):
    """Create a timestamped backup of the database."""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print("❌ Database not found:", db_path)
        return
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"finance_{timestamp}.db"
    backup_path = BACKUP_DIR / backup_name
    
    # Use SQLite backup API for consistency
    src_conn = sqlite3.connect(db_path)
    dst_conn = sqlite3.connect(str(backup_path))
    src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()
    
    size_mb = backup_path.stat().st_size / (1024 * 1024)
    print(f"✅ Backup created: {backup_path} ({size_mb:.2f} MB)")
    
    # Cleanup old backups — keep last 5
    backups = sorted(BACKUP_DIR.glob("finance_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old_backup in backups[5:]:
        old_backup.unlink()
        print(f"  Removed old backup: {old_backup.name}")
    
    return str(backup_path)


def cmd_export_json(db_path: str):
    """Export entire database to JSON file."""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print("❌ Database not found:", db_path)
        return
    
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    export_path = BACKUP_DIR / f"clarifin_export_{timestamp}.json"
    
    db = FinanceDB(db_path)
    with db.connection() as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "tables": {}
        }
        
        for table in tables:
            name = table[0]
            rows = conn.execute(f"SELECT * FROM [{name}]").fetchall()
            # Convert Row objects to dicts
            if rows:
                columns = [desc[0] for desc in conn.execute(f"SELECT * FROM [{name}] LIMIT 0").description]
                export_data["tables"][name] = [
                    dict(zip(columns, row)) for row in rows
                ]
            else:
                export_data["tables"][name] = []
    
    db.close()
    
    with open(export_path, 'w') as f:
        json.dump(export_data, f, indent=2, default=str)
    
    size_mb = export_path.stat().st_size / (1024 * 1024)
    print(f"✅ Exported to: {export_path} ({size_mb:.2f} MB)")


def cmd_check_orphans(db_path: str):
    """Find orphaned records across all tables."""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print("❌ Database not found:", db_path)
        return
    
    db = FinanceDB(db_path)
    with db.connection() as conn:
        issues = []
        
        # Transactions referencing non-existent statements
        orphan_txns = conn.execute("""
            SELECT COUNT(*) FROM transactions t
            WHERE NOT EXISTS (SELECT 1 FROM statements s WHERE s.id = t.statement_id)
        """).fetchone()[0]
        if orphan_txns:
            issues.append(f"❌ {orphan_txns} transactions reference missing statements")
        
        # Loan payments referencing non-existent loans
        orphan_payments = conn.execute("""
            SELECT COUNT(*) FROM loan_payments lp
            WHERE NOT EXISTS (SELECT 1 FROM loans l WHERE l.id = lp.loan_id)
        """).fetchone()[0]
        if orphan_payments:
            issues.append(f"❌ {orphan_payments} loan payments reference missing loans")
        
        # Cards referencing non-existent accounts
        orphan_cards = conn.execute("""
            SELECT COUNT(*) FROM cards c
            WHERE c.account_id IS NOT NULL
            AND NOT EXISTS (SELECT 1 FROM accounts a WHERE a.id = c.account_id)
        """).fetchone()[0]
        if orphan_cards:
            issues.append(f"❌ {orphan_cards} cards reference missing accounts")
        
        # Transactions with NULL hash_signature
        null_hash = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE hash_signature IS NULL"
        ).fetchone()[0]
        if null_hash:
            issues.append(f"⚠️ {null_hash} transactions have NULL hash_signature")
        
        # Transactions with NULL date_iso
        null_date = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE date_iso IS NULL"
        ).fetchone()[0]
        if null_date:
            issues.append(f"⚠️ {null_date} transactions have NULL date_iso")
        
        # Duplicate hash signatures
        dup_hash = conn.execute("""
            SELECT hash_signature, COUNT(*) as cnt
            FROM transactions
            WHERE hash_signature IS NOT NULL
            GROUP BY hash_signature
            HAVING cnt > 1
        """).fetchall()
        if dup_hash:
            issues.append(f"❌ {len(dup_hash)} duplicate hash_signatures found")
        
        if issues:
            print("Data integrity issues found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("✅ No orphaned records or integrity issues found")
    
    db.close()


if __name__ == "__main__":
    commands = {
        "status": cmd_status,
        "vacuum": cmd_vacuum,
        "backup": cmd_backup,
        "export-json": cmd_export_json,
        "check-orphans": cmd_check_orphans,
    }
    
    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: python3 -m src.maintenance <command>")
        print(f"Commands: {', '.join(commands.keys())}")
        sys.exit(1)
    
    cmd = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else DB_PATH
    
    commands[cmd](db_path)
