#!/usr/bin/env python3
"""Benchmark fixture performance before/after the canonicalization refactor.

Run from the backend directory:
    python tests/fixtures/benchmark_fixtures.py
"""

from __future__ import annotations

import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def benchmark_db_init(db_path: str) -> float:
    """Time a single canonical database initialization on a fresh database.

    Program K: this previously timed ``FinanceDB(db_path=...)``. It now calls
    the canonical ``src.core.db.schema`` entry points directly. These are
    exactly the three calls ``FinanceDB.__init__`` made, so the measurement is
    unchanged while the legacy compatibility wrapper is no longer imported.
    """
    from src.core.db.schema import create_all, run_migrations, verify_schema

    start = time.perf_counter()
    create_all(db_path)
    run_migrations(db_path)
    verify_schema(db_path)
    return time.perf_counter() - start


def benchmark_db_init_on_copy(db_path_template: str, db_path_copy: str) -> float:
    """Time canonical initialization on an already-initialized database copy."""
    import shutil

    shutil.copy2(db_path_template, db_path_copy)
    return benchmark_db_init(db_path_copy)


def benchmark_seed(db_path: str) -> float:
    """Time the seed inserts on an initialized database."""
    from src.core.db.connection import get_connection_context

    start = time.perf_counter()
    with get_connection_context(db_path) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO accounts
                (id, name, bank, account_type, balance_paise, account_number_last4)
            VALUES (1, 'Primary Checking', 'Test Bank', 'savings', 500000, '1234')
            """)
        conn.execute(
            "INSERT OR IGNORE INTO statements (id, bank, file_name) VALUES (1, 'Test Bank', 'test.pdf')"
        )
        conn.execute("""
            INSERT OR IGNORE INTO transactions
                (id, statement_id, date, date_iso, description, amount_paise, type, account_id)
            VALUES (1, 1, '01/01/2025', '2025-01-01', 'Test Txn', 100000, 'debit', 1)
            """)
        conn.execute("""
            INSERT OR IGNORE INTO account_balance_history
                (account_id, timestamp, balance_paise)
            VALUES (1, '2025-01-01T00:00:00', 500000)
            """)
        conn.execute(
            "INSERT OR IGNORE INTO account_links (account_id, linked_account_id) VALUES (1, 1)"
        )
    return time.perf_counter() - start


def benchmark_template_copy(tmp_path: str) -> float:
    """Time a single file copy of the schema template."""
    import shutil

    src = os.path.join(tmp_path, "template.db")
    dst = os.path.join(tmp_path, "copy.db")
    # Create a dummy file to copy
    with open(src, "wb") as f:
        f.write(b"\x00" * 1024 * 1024)  # 1MB
    start = time.perf_counter()
    shutil.copy2(src, dst)
    return time.perf_counter() - start


def main() -> int:
    import tempfile

    print("=" * 60)
    print("Fixture Performance Benchmark")
    print("=" * 60)

    results: dict[str, list[float]] = {
        "finance_db_init_fresh": [],
        "finance_db_init_copy": [],
        "seed_inserts": [],
        "template_copy_1mb": [],
    }

    with tempfile.TemporaryDirectory() as tmp:

        # 1. Benchmark fresh canonical DB init (old approach)
        print("\n1. Fresh canonical DB init (old approach)...")
        for i in range(3):
            db_path = os.path.join(tmp, f"fresh_{i}.db")
            t = benchmark_db_init(db_path)
            results["finance_db_init_fresh"].append(t)
            print(f"   Run {i+1}: {t:.3f}s")

        # 2. Benchmark template + copy approach (new approach)
        print("\n2. Template copy + canonical DB init (new approach)...")
        template_path = os.path.join(tmp, "template.db")
        benchmark_db_init(template_path)  # Create template
        for i in range(10):
            copy_path = os.path.join(tmp, f"copy_{i}.db")
            t = benchmark_db_init_on_copy(template_path, copy_path)
            results["finance_db_init_copy"].append(t)
        print(f"   Mean: {statistics.mean(results['finance_db_init_copy']):.3f}s")
        print(f"   Median: {statistics.median(results['finance_db_init_copy']):.3f}s")

        # 3. Benchmark seed inserts (old approach had secondary connection)
        print("\n3. Seed inserts (canonical connection)...")
        for i in range(10):
            db_path = os.path.join(tmp, f"seed_{i}.db")
            benchmark_db_init(db_path)
            t = benchmark_seed(db_path)
            results["seed_inserts"].append(t)
        print(f"   Mean: {statistics.mean(results['seed_inserts']):.3f}s")
        print(f"   Median: {statistics.median(results['seed_inserts']):.3f}s")

        # 4. Benchmark template file copy
        print("\n4. Template file copy (1MB)...")
        for _ in range(20):
            t = benchmark_template_copy(tmp)
            results["template_copy_1mb"].append(t)
        print(f"   Mean: {statistics.mean(results['template_copy_1mb']):.6f}s")
        print(f"   Median: {statistics.median(results['template_copy_1mb']):.6f}s")

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    fresh_mean = statistics.mean(results["finance_db_init_fresh"])
    copy_mean = statistics.mean(results["finance_db_init_copy"])
    speedup = fresh_mean / copy_mean

    print(f"Fresh init (old):        {fresh_mean:.3f}s")
    print(f"Copy + init (new):       {copy_mean:.3f}s")
    print(f"Speedup per test:        {speedup:.1f}x")
    print(f"Seed inserts:            {statistics.mean(results['seed_inserts']):.3f}s")
    print(
        f"File copy (1MB):         {statistics.mean(results['template_copy_1mb']):.6f}s"
    )

    # Estimate for 1200 tests
    old_total = 1200 * fresh_mean
    new_total = 4.5 + 1200 * copy_mean  # 1 template + 1200 copies
    print("\nEstimated 1200-test suite:")
    print(f"  Old (fresh init each): {old_total:.0f}s ({old_total/60:.1f} min)")
    print(f"  New (template copy):   {new_total:.0f}s ({new_total/60:.1f} min)")
    print(
        f"  Time saved:            {old_total - new_total:.0f}s ({(1 - new_total/old_total)*100:.1f}%)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
