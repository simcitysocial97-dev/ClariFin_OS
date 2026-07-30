"""
Test Suite for Phase 2B: Reconciliation Determinism
====================================================

Tests for:
1. Same dataset → same reconciliation rows
2. Re-run engine → no duplicates
3. Confirmed rows remain unchanged
4. Ledger replay still produces identical balances
5. Property-based invariants for match determinism

Run: python -m pytest tests/invariants/test_reconciliation_determinism.py -v
"""

import os
import sqlite3
import tempfile
from datetime import datetime

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from db import FinanceDB
from repositories.statement_repository import StatementRepository
from src.engines.reconciliation_engine import find_potential_matches

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)

    # Insert test statements for different accounts
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    yield db, db_path

    # Cleanup - ensure connection is closed
    if db._conn:
        db._conn.close()
        db._conn = None
    os.unlink(db_path)


@pytest.fixture
def populated_db(temp_db):
    """Populate database with deterministic test transactions."""
    db, db_path = temp_db

    conn = sqlite3.connect(db_path)

    # Insert transactions for Account A (debits)
    # Note: debit/credit are GENERATED columns from amount_paise and type
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES
            (1, '01/01/2025', '2025-01-01', 'Transfer to B', 100000, 'debit', 'Account_A'),
            (1, '05/01/2025', '2025-01-05', 'Transfer to B late', 200000, 'debit', 'Account_A'),
            (1, '10/01/2025', '2025-01-10', 'Different amount', 50000, 'debit', 'Account_A')
    """)

    # Insert transactions for Account B (credits)
    # Note: debit/credit are GENERATED columns from amount_paise and type
    conn.execute("""
        INSERT INTO transactions (statement_id, date, date_iso, description, amount_paise, type, account_id)
        VALUES
            (2, '01/01/2025', '2025-01-01', 'Transfer from A', 100000, 'credit', 'Account_B'),
            (2, '07/01/2025', '2025-01-07', 'Transfer from A late', 200000, 'credit', 'Account_B'),
            (2, '10/01/2025', '2025-01-10', 'Different amount', 75000, 'credit', 'Account_B')
    """)

    conn.commit()
    conn.close()

    return db, db_path


# ============================================================
# Hypothesis Strategies
# ============================================================


def transaction_strategy():
    """Generate valid transaction data for property testing."""
    return st.fixed_dictionaries(
        {
            "statement_id": st.integers(min_value=1, max_value=10),
            "date": st.dates(
                min_value=datetime(2020, 1, 1).date(),
                max_value=datetime(2030, 12, 31).date(),
            ).map(lambda d: d.strftime("%d/%m/%Y")),
            "date_iso": st.dates(
                min_value=datetime(2020, 1, 1).date(),
                max_value=datetime(2030, 12, 31).date(),
            ).map(lambda d: d.strftime("%Y-%m-%d")),
            "description": st.text(min_size=1, max_size=50),
            "amount_paise": st.integers(min_value=1, max_value=10_000_000),
            "type": st.sampled_from(["debit", "credit"]),
            "account_id": st.sampled_from(["Account_A", "Account_B"]),
        }
    )


def transactions_strategy():
    """Generate a list of transactions with at least one debit and one credit."""
    return st.lists(
        transaction_strategy(),
        min_size=2,
        max_size=20,
        unique_by=lambda txn: (
            txn["date_iso"],
            txn["amount_paise"],
            txn["account_id"],
            txn["type"],
        ),
    ).filter(
        lambda txns: any(txn["type"] == "debit" for txn in txns)
        and any(txn["type"] == "credit" for txn in txns)
    )


# ============================================================
# Property Tests
# ============================================================


@given(transactions=transactions_strategy())
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_match_uniqueness_property(transactions):
    """Property: No duplicate matches for the same transaction pair."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    conn = sqlite3.connect(db_path)
    try:
        # Insert generated transactions
        for txn in transactions:
            conn.execute(
                """
                INSERT INTO transactions
                (statement_id, date, date_iso, description, amount_paise, type, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    txn["statement_id"],
                    txn["date"],
                    txn["date_iso"],
                    txn["description"],
                    txn["amount_paise"],
                    txn["type"],
                    txn["account_id"],
                ),
            )

        conn.commit()

        # Run reconciliation
        matches = find_potential_matches(db_path)

        # Check for duplicates
        seen_pairs = set()
        for match in matches:
            pair = (match["debit_txn_id"], match["credit_txn_id"])
            assert pair not in seen_pairs, f"Duplicate match found: {pair}"
            seen_pairs.add(pair)
    finally:
        conn.close()
        if db._conn:
            db._conn.close()
        os.unlink(db_path)


@given(transactions=transactions_strategy())
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_deterministic_matching_property(transactions):
    """Property: Same input must always produce the same matches."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    conn = sqlite3.connect(db_path)
    try:
        # Insert generated transactions
        for txn in transactions:
            conn.execute(
                """
                INSERT INTO transactions
                (statement_id, date, date_iso, description, amount_paise, type, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    txn["statement_id"],
                    txn["date"],
                    txn["date_iso"],
                    txn["description"],
                    txn["amount_paise"],
                    txn["type"],
                    txn["account_id"],
                ),
            )

        conn.commit()

        # Run reconciliation twice
        matches_1 = find_potential_matches(db_path)
        matches_2 = find_potential_matches(db_path)

        # Check deterministic output
        assert len(matches_1) == len(matches_2), "Match count should be identical"

        keys_1 = sorted([m["deterministic_key"] for m in matches_1])
        keys_2 = sorted([m["deterministic_key"] for m in matches_2])
        assert keys_1 == keys_2, "Match keys should be identical"

        # Check confidence scores
        for m1, m2 in zip(
            sorted(matches_1, key=lambda x: x["deterministic_key"]),
            sorted(matches_2, key=lambda x: x["deterministic_key"]),
            strict=True,
        ):
            assert (
                m1["match_confidence"] == m2["match_confidence"]
            ), f"Confidence should be identical for {m1['deterministic_key']}"
    finally:
        conn.close()
        if db._conn:
            db._conn.close()
        os.unlink(db_path)


@given(transactions=transactions_strategy())
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_no_cycles_property(transactions):
    """Property: Matching must not create cycles in the transaction graph."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    conn = sqlite3.connect(db_path)
    try:
        # Insert generated transactions
        for txn in transactions:
            conn.execute(
                """
                INSERT INTO transactions
                (statement_id, date, date_iso, description, amount_paise, type, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    txn["statement_id"],
                    txn["date"],
                    txn["date_iso"],
                    txn["description"],
                    txn["amount_paise"],
                    txn["type"],
                    txn["account_id"],
                ),
            )

        conn.commit()

        # Run reconciliation
        matches = find_potential_matches(db_path)

        # Check for cycles (A->B and B->A)
        pairs = set()
        for match in matches:
            pair = (match["debit_txn_id"], match["credit_txn_id"])
            mirrored = (match["credit_txn_id"], match["debit_txn_id"])
            assert mirrored not in pairs, f"Cycle detected: {pair} and {mirrored}"
            pairs.add(pair)
    finally:
        conn.close()
        if db._conn:
            db._conn.close()
        os.unlink(db_path)


@given(transactions=transactions_strategy())
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_bipartite_matching_property(transactions):
    """Property: Matches must be valid for bipartite graphs (debit ↔ credit)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    conn = sqlite3.connect(db_path)
    try:
        # Insert generated transactions
        for txn in transactions:
            conn.execute(
                """
                INSERT INTO transactions
                (statement_id, date, date_iso, description, amount_paise, type, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    txn["statement_id"],
                    txn["date"],
                    txn["date_iso"],
                    txn["description"],
                    txn["amount_paise"],
                    txn["type"],
                    txn["account_id"],
                ),
            )

        conn.commit()

        # Run reconciliation
        matches = find_potential_matches(db_path)

        # Check bipartite validity: debit ↔ credit only
        for match in matches:
            assert (
                match["debit_account_id"] != match["credit_account_id"]
            ), f"Invalid bipartite match: same account {match['debit_account_id']}"
            assert (
                match["debit_txn_id"] != match["credit_txn_id"]
            ), "Invalid bipartite match: same transaction"
    finally:
        conn.close()
        if db._conn:
            db._conn.close()
        os.unlink(db_path)


@given(
    transactions=st.lists(
        transaction_strategy(),
        min_size=0,
        max_size=1,
    )
)
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_edge_cases_property(transactions):
    """Property: Handle edge cases (zero or single transaction)."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    db = FinanceDB(db_path=db_path)
    stmt_repo = StatementRepository(db_path)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")

    conn = sqlite3.connect(db_path)
    try:
        # Insert generated transactions
        for txn in transactions:
            conn.execute(
                """
                INSERT INTO transactions
                (statement_id, date, date_iso, description, amount_paise, type, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    txn["statement_id"],
                    txn["date"],
                    txn["date_iso"],
                    txn["description"],
                    txn["amount_paise"],
                    txn["type"],
                    txn["account_id"],
                ),
            )

        conn.commit()

        # Run reconciliation
        matches = find_potential_matches(db_path)
        assert isinstance(matches, list), "Matches should always be a list"
        assert len(matches) == 0, "No matches expected for edge cases"
    finally:
        conn.close()
        if db._conn:
            db._conn.close()
        os.unlink(db_path)


# ============================================================
# Test 1: Same Dataset → Same Reconciliation Rows
# ============================================================


def test_deterministic_matching(populated_db):
    """Test that same dataset produces same reconciliation matches."""
    db, db_path = populated_db

    # Run matching twice
    matches_1 = find_potential_matches(db_path)
    matches_2 = find_potential_matches(db_path)

    # Should produce identical results
    assert len(matches_1) == len(matches_2), "Match count should be identical"

    # Sort by deterministic key for comparison
    keys_1 = sorted([m["deterministic_key"] for m in matches_1])
    keys_2 = sorted([m["deterministic_key"] for m in matches_2])

    assert keys_1 == keys_2, "Match keys should be identical"

    # Verify confidence scores are identical
    for m1, m2 in zip(
        sorted(matches_1, key=lambda x: x["deterministic_key"]),
        sorted(matches_2, key=lambda x: x["deterministic_key"]),
        strict=False,
    ):
        assert (
            m1["match_confidence"] == m2["match_confidence"]
        ), f"Confidence should be identical for {m1['deterministic_key']}"


# [Rest of the existing tests remain unchanged...]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
