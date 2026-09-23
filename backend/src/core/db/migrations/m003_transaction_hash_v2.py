"""Migration 003 — transaction hash widening (M05, BE-001).

Additive-then-cutover, never alters existing transaction row content:

1. ``ALTER TABLE transactions ADD COLUMN hash_signature_v2 TEXT``
   (idempotent, existing try/except OperationalError pattern).
2. Backfill ``hash_signature_v2`` for existing rows in Python via a
   parameterized ``UPDATE ... WHERE id = ?`` loop (matching the existing
   ``date_iso`` backfill pattern — NOT an in-SQL SHA256() call, to avoid
   repeating the DB-003 pattern).
3. Zero-collision check (``GROUP BY hash_signature_v2 HAVING COUNT(*) > 1``)
   must return zero rows before the new unique index is created. This is
   zero-returning by construction: ``hash_signature_v2`` includes
   ``sequence_num``, and ``account_id`` derives deterministically from
   ``statements.bank``, so the tuple inherits the existing
   ``UNIQUE(statement_id, date, description, amount_paise, sequence_num)``
   table constraint. Non-zero means the existing invariant is already
   violated — abort and escalate (§10), no workaround.
4. Create ``UNIQUE idx_transaction_hash_v2`` on ``hash_signature_v2``,
   then drop the old ``UNIQUE idx_transaction_hash`` (on ``hash_signature``).
   The old column stays populated (rollback depends on its data being
   current); its removal is out of scope.
"""

from __future__ import annotations

import hashlib
import logging
import sqlite3

logger = logging.getLogger(__name__)

DESCRIPTION = "transaction hash v2"


def _compute_v2(
    account_id: str,
    date_iso: str,
    description: str,
    debit_paise: int,
    credit_paise: int,
    sequence_num: int,
) -> str:
    hash_input = (
        f"{account_id}|{date_iso}|{description}|"
        f"{debit_paise}|{credit_paise}|{sequence_num}"
    )
    return hashlib.sha256(hash_input.encode()).hexdigest().lower()


def migrate(conn: sqlite3.Connection) -> None:
    """Add, backfill, collision-check, then cut over the unique index.

    The prevent_transaction_update trigger aborts ANY UPDATE on
    transactions — including this migration's backfill. It is dropped for
    the duration of the backfill and recreated byte-identical afterwards
    (SQLite DDL is transactional, so a failed migration rolls the DROP
    back and the trigger is never left missing).
    """
    try:
        conn.execute("ALTER TABLE transactions ADD COLUMN hash_signature_v2 TEXT")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e).lower():
            raise
    conn.execute("DROP TRIGGER IF EXISTS prevent_transaction_update")
    try:
        _backfill_and_cutover(conn)
    finally:
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS prevent_transaction_update
            BEFORE UPDATE ON transactions
            BEGIN
                SELECT RAISE(ABORT, 'Transactions are immutable. Cannot update.');
            END
            """)


def _backfill_and_cutover(conn: sqlite3.Connection) -> None:
    pre_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    pre_sum = conn.execute(
        "SELECT COALESCE(SUM(amount_paise), 0) FROM transactions"
    ).fetchone()[0]
    logger.info("Migration 003 pre-backfill: count=%s sum=%s", pre_count, pre_sum)

    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, statement_id, sequence_num, date, description, type, "
        "amount_paise, date_iso, account_id FROM transactions "
        "WHERE hash_signature_v2 IS NULL"
    ).fetchall()
    backfilled = 0
    for row in rows:
        statement_id = row["statement_id"]
        account_id = row["account_id"] or ""
        if not account_id and statement_id is not None:
            stmt = conn.execute(
                "SELECT bank FROM statements WHERE id = ?", (statement_id,)
            ).fetchone()
            account_id = stmt["bank"] if stmt and stmt["bank"] else ""
        date_iso = row["date_iso"] or ""
        if not date_iso and row["date"]:
            from src.repositories.transaction_repository import _parse_date_to_ymd

            try:
                date_iso = _parse_date_to_ymd(str(row["date"]))
            except ValueError:
                date_iso = ""
        amount_paise = int(row["amount_paise"] or 0)
        txn_type = str(row["type"] or "")
        debit_paise = amount_paise if txn_type == "debit" else 0
        credit_paise = amount_paise if txn_type == "credit" else 0
        v2 = _compute_v2(
            account_id,
            date_iso,
            str(row["description"] or ""),
            debit_paise,
            credit_paise,
            int(row["sequence_num"] or 0),
        )
        conn.execute(
            "UPDATE transactions SET hash_signature_v2 = ? WHERE id = ?",
            (v2, row["id"]),
        )
        backfilled += 1
    logger.info("Migration 003 backfilled %s rows", backfilled)

    collisions = conn.execute(
        "SELECT hash_signature_v2, COUNT(*) AS c FROM transactions "
        "GROUP BY hash_signature_v2 HAVING COUNT(*) > 1"
    ).fetchall()
    if collisions:
        raise RuntimeError(
            "Migration 003 aborted: non-zero hash_signature_v2 collisions "
            f"({len(collisions)} groups) — existing invariant violated, escalate"
        )
    logger.info("Migration 003 zero-collision check passed")

    post_count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    post_sum = conn.execute(
        "SELECT COALESCE(SUM(amount_paise), 0) FROM transactions"
    ).fetchone()[0]
    if post_count != pre_count or post_sum != pre_sum:
        raise RuntimeError(
            "Migration 003 aborted: row count/sum changed during backfill "
            f"(count {pre_count}->{post_count}, sum {pre_sum}->{post_sum})"
        )
    logger.info(
        "Migration 003 count/sum unchanged: count=%s sum=%s", post_count, post_sum
    )

    # Index cutover: additive first, destructive second (never the reverse).
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS "
        "idx_transaction_hash_v2 ON transactions(hash_signature_v2)"
    )
    conn.execute("DROP INDEX IF EXISTS idx_transaction_hash")
    logger.info("Migration 003 index cutover complete")
