"""Regression test for BE-001 — transaction dedup hash collision.

BE-001: `TransactionRepository.insert_transactions` computes its deduplication
hash (`hash_signature`) from
`account_id | date_iso | description | debit_paise | credit_paise` only, which
omits `sequence_num`. Two legitimately distinct transactions that share all
five hash-input fields (e.g. two identical purchases on the same day) produce
the same hash, so the second row is silently swallowed by `INSERT OR IGNORE`.

This test inserts two such transactions — identical across all five hash-input
fields, differing only in list position (hence different `sequence_num`) — and
asserts both rows persist (`COUNT(*) == 2`).

Expected state: FAILS until M05 widens the hash (tracked as a known expected
failure in BASELINE.md; resolved by M05).
"""

from __future__ import annotations

import sqlite3

from src.repositories.statement_repository import StatementRepository
from src.repositories.transaction_repository import TransactionRepository


def test_two_distinct_transactions_with_same_hash_inputs_both_persist(
    temp_db: str,
) -> None:
    """BE-001: identical hash inputs at different positions must not dedupe."""
    stmt_repo = StatementRepository(temp_db)
    txn_repo = TransactionRepository(temp_db)

    stmt_id = stmt_repo.insert_statement(
        bank="HashTest",
        file_name="hash_test.pdf",
    )

    # The two dicts are identical across all five hash-input fields
    # (account_id derives from the statement's bank for both; date_iso,
    # description, debit_paise, credit_paise are literally equal) and differ
    # only in list position (-> different sequence_num).
    txn = {
        "date": "15/01/2025",
        "description": "IDENTICAL_MERCHANT",
        "amount_paise": 10000,
        "type": "debit",
    }
    inserted = txn_repo.insert_transactions(stmt_id, [dict(txn), dict(txn)])

    conn = sqlite3.connect(temp_db)
    try:
        cur = conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE statement_id = ?",
            (stmt_id,),
        )
        count = cur.fetchone()[0]
    finally:
        conn.close()

    assert inserted == 2, (
        f"BE-001: expected both rows inserted (2), got {inserted}"
    )
    assert count == 2, (
        f"BE-001: expected 2 persisted rows, found {count} — "
        "the second transaction was swallowed by the hash dedup"
    )
