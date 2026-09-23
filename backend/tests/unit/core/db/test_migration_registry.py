"""Migration registry idempotency tests (M03-T5)."""

from __future__ import annotations

import sqlite3

from src.core.db.migrations._registry import MIGRATIONS, apply_pending_migrations
from src.core.db.schema import create_all


def _schema_snapshot(conn: sqlite3.Connection) -> list[tuple[str, str, str]]:
    rows = conn.execute(
        "SELECT type, name, sql FROM sqlite_master "
        "WHERE sql IS NOT NULL ORDER BY type, name"
    ).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


def test_m001_idempotent_same_connection(tmp_path) -> None:
    """Applying migration 001 twice: no error, identical resulting schema."""
    db_path = str(tmp_path / "m03.db")
    create_all(db_path)
    conn = sqlite3.connect(db_path)
    try:
        first = apply_pending_migrations(conn)
        assert 1 in first
        snapshot_a = _schema_snapshot(conn)
        recorded_a = conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()

        second = apply_pending_migrations(conn)
        assert second == []
        snapshot_b = _schema_snapshot(conn)
        recorded_b = conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()

        assert snapshot_a == snapshot_b
        assert recorded_a == recorded_b
    finally:
        conn.close()


def test_unapplied_migration_runs_exactly_once(tmp_path) -> None:
    """A second, unapplied migration in the list runs exactly once."""
    from src.core.db.migrations import _registry as reg

    db_path = str(tmp_path / "m03b.db")
    create_all(db_path)
    calls: list[int] = []

    def _probe(conn: sqlite3.Connection) -> None:
        calls.append(1)
        conn.execute("CREATE TABLE IF NOT EXISTS m03_probe (id INTEGER PRIMARY KEY)")

    original = list(reg.MIGRATIONS)
    reg.MIGRATIONS.append((999, "probe-once", _probe))
    try:
        conn = sqlite3.connect(db_path)
        try:
            first = apply_pending_migrations(conn)
            assert 999 in first
            assert calls == [1]
            second = apply_pending_migrations(conn)
            assert second == []
            assert calls == [1]
        finally:
            conn.close()
    finally:
        reg.MIGRATIONS[:] = original
    assert [m[0] for m in MIGRATIONS] == [1, 2, 3]


def test_m003_backfill_populates_v2_without_touching_content(tmp_path) -> None:
    """M05-T3: backfill fills hash_signature_v2; count/sum/content identical.

    Seed rows are constructed via direct parameterized INSERT (the
    TransactionBuilder cannot produce valid rows: it lacks `date`,
    `sequence_num`, and a real `statements` row reference).
    """
    from src.core.db.migrations.m003_transaction_hash_v2 import migrate as m003

    db_path = str(tmp_path / "m05.db")
    create_all(db_path)
    conn = sqlite3.connect(db_path)
    try:
        # Pre-populate: statement + two rows colliding on the OLD hash inputs
        # (same bank/date/description/amount/type, distinct sequence_num),
        # with NULL v2 and the old formula hash to simulate a legacy DB.
        import hashlib

        conn.execute(
            "INSERT INTO statements (bank, file_name) "
            "VALUES ('BackfillBank', 'backfill.pdf')"
        )
        statement_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        old_input = "BackfillBank|2025-01-05|BACKFILL SHOP|5000|0"
        old_hash = hashlib.sha256(old_input.encode()).hexdigest().lower()
        seed = [
            (
                statement_id,
                seq,
                "05/01/2025",
                "BACKFILL SHOP",
                "debit",
                5000,
                "2025-01-05",
                old_hash,
                "BackfillBank",
            )
            for seq in (0, 1)
        ]
        conn.executemany(
            "INSERT INTO transactions (statement_id, sequence_num, date, "
            "description, type, amount_paise, date_iso, hash_signature, "
            "account_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            seed,
        )
        conn.commit()
        before_rows = [
            tuple(r)
            for r in conn.execute(
                "SELECT id, amount_paise, date, description, type, category, "
                "sequence_num, account_id, hash_signature FROM transactions "
                "ORDER BY id"
            ).fetchall()
        ]
        before_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        before_sum = conn.execute(
            "SELECT COALESCE(SUM(amount_paise), 0) FROM transactions"
        ).fetchone()[0]

        m003(conn)
        conn.commit()

        after_rows = [
            tuple(r)
            for r in conn.execute(
                "SELECT id, amount_paise, date, description, type, category, "
                "sequence_num, account_id, hash_signature FROM transactions "
                "ORDER BY id"
            ).fetchall()
        ]
        assert after_rows == before_rows
        assert (
            conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            == before_count
            == 2
        )
        assert (
            conn.execute(
                "SELECT COALESCE(SUM(amount_paise), 0) FROM transactions"
            ).fetchone()[0]
            == before_sum
            == 10000
        )
        v2_vals = [
            r[0]
            for r in conn.execute(
                "SELECT hash_signature_v2 FROM transactions ORDER BY id"
            ).fetchall()
        ]
        assert all(v for v in v2_vals)
        assert len(set(v2_vals)) == 2
        collisions = conn.execute(
            "SELECT hash_signature_v2, COUNT(*) FROM transactions "
            "GROUP BY hash_signature_v2 HAVING COUNT(*) > 1"
        ).fetchall()
        assert collisions == []
        idx = conn.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'idx_transaction_hash_v2'"
        ).fetchone()
        assert idx is not None and "UNIQUE" in idx[0].upper()
        assert (
            conn.execute(
                "SELECT name FROM sqlite_master WHERE name = 'idx_transaction_hash'"
            ).fetchone()
            is None
        )
    finally:
        conn.close()
