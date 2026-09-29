"""
Ledger integrity checks against data written by a foreign writer — M9-C71.

`debit` and `credit` are `GENERATED ALWAYS ... STORED` columns derived from
`type` and `amount_paise`, so the application's own writer can never produce a
negative leg or a dual entry. Checks 2, 3 and 4 of `validate_ledger_integrity`
and the `hash_signature` uniqueness clause of check 6 are therefore DEFENSIVE:
they exist for rows written by something other than this writer — an importer, a
migration, a restored backup, a hand-edited file.

The pre-existing suite could only assert the ABSENCE of those violations
(`test_validate_ledger_integrity_defensive_checks_exist`,
`test_validate_ledger_integrity_schema_prevents_duplicates`). The append blocks
that emit NEGATIVE_DEBIT, NEGATIVE_CREDIT, DUAL_ENTRY and DUPLICATE_HASH were
therefore never executed by any test, and the mutation campaign showed it: 73
of the 82 surviving mutants in this component were in
`validate_ledger_integrity`, concentrated in exactly those four blocks. A
corrupted row in a real database would have gone unreported for the same reason.

The fixture below recreates `transactions` with PLAIN debit/credit columns —
i.e. the shape a foreign writer leaves behind — so the defensive checks can be
exercised for real. Each test then asserts the violation that must be reported,
including the offending id and the message content, so a check that silently
stops reporting is detected.
"""

from __future__ import annotations

import pytest

from src.engines.ledger_audit_engine import validate_ledger_integrity

# Recreate `transactions` with plain (non-generated) debit/credit columns and a
# plain hash_signature, matching the shape a foreign or legacy writer leaves
# behind. The application writer cannot produce any of these rows.
_FOREIGN_WRITER_SCHEMA = """
DROP TABLE IF EXISTS transactions;
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    statement_id INTEGER,
    date TEXT,
    date_iso TEXT,
    description TEXT,
    amount_paise INTEGER,
    type TEXT,
    account_id TEXT,
    hash_signature TEXT,
    sequence_num INTEGER,
    debit INTEGER,
    credit INTEGER
);
"""


def _seed_leg(
    conn,
    *,
    txn_id: int,
    description: str,
    debit: int = 0,
    credit: int = 0,
    account_id: str = "HDFC",
    hash_signature: str | None = "h0",
    date_iso: str = "2025-01-01",
) -> int:
    conn.execute(
        """
        INSERT INTO transactions
            (id, statement_id, date, date_iso, description, amount_paise, type,
             account_id, hash_signature, sequence_num, debit, credit)
        VALUES (?, 1, ?, ?, ?, ?, 'debit', ?, ?, ?, ?, ?)
        """,
        (
            txn_id,
            date_iso,
            date_iso,
            description,
            debit or credit,
            account_id,
            hash_signature,
            txn_id,
            debit,
            credit,
        ),
    )
    return txn_id


@pytest.fixture
def foreign_writer_db(temp_db: str) -> str:
    """A ledger whose debit/credit columns were written directly."""
    from src.core.db.connection import get_connection

    conn = get_connection(temp_db)
    conn.executescript(_FOREIGN_WRITER_SCHEMA)
    conn.execute(
        "INSERT INTO statements (id, bank, file_name) VALUES (1, 'HDFC', 'stmt1.pdf')"
    )
    # A clean control row, so a reported violation can never be attributed to
    # fixture noise.
    _seed_leg(
        conn, txn_id=1, description="Clean", debit=1000, credit=0, hash_signature="h0"
    )
    conn.commit()
    conn.close()
    return temp_db


def _of_type(result: dict, violation_type: str) -> list[dict]:
    return [v for v in result["violations"] if v["type"] == violation_type]


class TestForeignWriterNegativeDebit:
    def test_negative_debit_is_reported(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Refund Out", debit=-5000, credit=0)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)

        assert result["status"] == "FAIL"
        found = _of_type(result, "NEGATIVE_DEBIT")
        assert len(found) == 1
        assert found[0]["transaction_id"] == 2
        assert "-5000" in found[0]["message"]
        assert "negative debit" in found[0]["message"].lower()

    def test_zero_debit_is_not_a_violation(self, foreign_writer_db):
        """The check is `debit < 0`, so a plain zero leg is clean. If the
        comparison were weakened the report would be noisy and unusable."""
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Zero", debit=0, credit=0)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)
        assert _of_type(result, "NEGATIVE_DEBIT") == []


class TestForeignWriterNegativeCredit:
    def test_negative_credit_is_reported(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Reversal", debit=0, credit=-2500)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)

        assert result["status"] == "FAIL"
        found = _of_type(result, "NEGATIVE_CREDIT")
        assert len(found) == 1
        assert found[0]["transaction_id"] == 2
        assert "-2500" in found[0]["message"]
        assert "negative credit" in found[0]["message"].lower()

    def test_zero_credit_is_not_a_violation(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Zero", debit=0, credit=0)
        conn.commit()
        conn.close()

        assert (
            _of_type(validate_ledger_integrity(foreign_writer_db), "NEGATIVE_CREDIT")
            == []
        )


class TestForeignWriterDualEntry:
    def test_both_legs_populated_is_reported(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Split", debit=7000, credit=7000)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)

        assert result["status"] == "FAIL"
        found = _of_type(result, "DUAL_ENTRY")
        assert len(found) == 1
        assert found[0]["transaction_id"] == 2
        assert "both debit" in found[0]["message"].lower()
        # Both amounts must be quoted, so an operator can find the row.
        assert "7000" in found[0]["message"]

    def test_a_single_populated_leg_is_clean(self, foreign_writer_db):
        """The check is `debit > 0 AND credit > 0`. A debit-only or
        credit-only row is the normal case and must not be flagged."""
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Debit Only", debit=1000, credit=0)
        _seed_leg(conn, txn_id=3, description="Credit Only", debit=0, credit=1000)
        conn.commit()
        conn.close()

        assert (
            _of_type(validate_ledger_integrity(foreign_writer_db), "DUAL_ENTRY") == []
        )

    def test_dual_entry_is_reported_alongside_the_other_violations(
        self, foreign_writer_db
    ):
        """The six checks are independent and all findings must be reported in
        one pass — a reader must not have to re-run the audit per invariant."""
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Split", debit=7000, credit=7000)
        _seed_leg(conn, txn_id=3, description="Refund", debit=-10, credit=0)
        _seed_leg(conn, txn_id=4, description="Reversal", debit=0, credit=-10)
        _seed_leg(conn, txn_id=5, description="No Account", debit=1, account_id=None)
        _seed_leg(conn, txn_id=6, description="No Hash", debit=1, hash_signature=None)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)

        assert result["status"] == "FAIL"
        assert result["violation_count"] == len(result["violations"])
        assert result["violation_count"] >= 5
        for expected in (
            "DUAL_ENTRY",
            "NEGATIVE_DEBIT",
            "NEGATIVE_CREDIT",
            "NULL_ACCOUNT_ID",
            "NULL_HASH",
        ):
            assert _of_type(result, expected), f"{expected} was not reported"

    def test_violation_count_matches_the_reported_violations(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="Split", debit=7000, credit=7000)
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)
        assert result["violation_count"] == len(result["violations"])


class TestForeignWriterDuplicateHash:
    def test_duplicate_hash_is_reported_with_every_affected_id(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(
            conn, txn_id=2, description="Copy A", debit=1000, hash_signature="dup"
        )
        _seed_leg(
            conn, txn_id=3, description="Copy B", debit=1000, hash_signature="dup"
        )
        _seed_leg(
            conn, txn_id=4, description="Unique", debit=1000, hash_signature="solo"
        )
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)

        assert result["status"] == "FAIL"
        found = _of_type(result, "DUPLICATE_HASH")
        assert len(found) == 1
        assert found[0]["hash_signature"] == "dup"
        # Every id sharing the signature must be listed, so an operator can
        # quarantine the whole set rather than one row at a time.
        assert sorted(found[0]["transaction_ids"]) == [2, 3]
        # The message names the colliding ids (the signature itself is carried
        # in the structured field above).
        assert "2,3" in found[0]["message"] or "2, 3" in found[0]["message"]

    def test_unique_hashes_are_clean(self, foreign_writer_db):
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="A", debit=1, hash_signature="a")
        _seed_leg(conn, txn_id=3, description="B", debit=1, hash_signature="b")
        _seed_leg(conn, txn_id=4, description="C", debit=1, hash_signature="c")
        conn.commit()
        conn.close()

        assert (
            _of_type(validate_ledger_integrity(foreign_writer_db), "DUPLICATE_HASH")
            == []
        )

    def test_empty_and_null_hashes_do_not_collide_with_each_other(
        self, foreign_writer_db
    ):
        """The uniqueness clause filters `hash_signature IS NOT NULL AND
        hash_signature != ''`, so two blank signatures must not be reported as
        a duplicate pair — they are a NULL_HASH finding, reported once each."""
        from src.core.db.connection import get_connection

        conn = get_connection(foreign_writer_db)
        _seed_leg(conn, txn_id=2, description="No Hash", debit=1, hash_signature=None)
        _seed_leg(conn, txn_id=3, description="Empty Hash", debit=1, hash_signature="")
        conn.commit()
        conn.close()

        result = validate_ledger_integrity(foreign_writer_db)
        assert _of_type(result, "DUPLICATE_HASH") == []
        assert len(_of_type(result, "NULL_HASH")) == 2
