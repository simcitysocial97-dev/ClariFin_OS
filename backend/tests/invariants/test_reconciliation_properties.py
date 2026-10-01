"""
Property-Based Tests for Reconciliation Determinism
=================================================

Tests for:
1. Match uniqueness: No duplicate matches for the same transaction pair.
2. Deterministic matching: Same input must always produce the same matches.
3. No cycles: Matching must not create cycles in the transaction graph.
4. Bipartite matching: Matches must be valid for bipartite graphs (debit ↔ credit).
5. Edge cases: Handle boundary conditions (zero transactions, single transaction).

Run: python -m pytest tests/invariants/test_reconciliation_properties.py -v
"""

import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from repositories.statement_repository import StatementRepository
from src.engines.reconciliation_engine import find_potential_matches


@pytest.fixture
def reconciliation_db(temp_db: str) -> str:
    """Provide a database pre-initialized with reconciliation test statements."""
    stmt_repo = StatementRepository(temp_db)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")
    return temp_db


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
        max_size=10,
        unique_by=lambda txn: txn["statement_id"],
    ).filter(
        lambda txns: any(txn["type"] == "debit" for txn in txns)
        and any(txn["type"] == "credit" for txn in txns)
    )


def _fresh_reconciliation_db(template: Path) -> str:
    """Create a new reconciliation database seeded with the two test statements.

    Hypothesis runs every example of a property test against one function-scoped
    fixture, so examples accumulate rows in a single database. That matters here
    because the transactions table is append-only by design — StatementRepository
    installs a trigger that refuses DELETE, which is correct for a financial
    ledger and is not something a test should route around. Isolation therefore
    has to come from a new database per example, not from clearing the existing
    one.

    Without it, a later example that generates a row colliding with an earlier
    one fails on
      UNIQUE (statement_id, date, description, amount_paise, sequence_num)
    which is the schema constraint doing its job, not the property under test.

    `template` is the session-scoped pristine schema, so this copies the same
    fully-initialised database the temp_db fixture would have produced.
    """

    fd, path = tempfile.mkstemp(prefix="recon_prop_", suffix=".db")
    os.close(fd)
    os.unlink(path)
    shutil.copy2(template, path)
    stmt_repo = StatementRepository(path)
    stmt_repo.insert_statement("Account_A", "stmt_a.pdf", "01/01/2025", "31/01/2025")
    stmt_repo.insert_statement("Account_B", "stmt_b.pdf", "01/01/2025", "31/01/2025")
    return path


@given(transactions=transactions_strategy())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_match_uniqueness_property(
    transactions, reconciliation_db: str, _pristine_db_template: Path
):
    """Property: No duplicate matches for the same transaction pair."""
    reconciliation_db = _fresh_reconciliation_db(_pristine_db_template)
    conn = sqlite3.connect(reconciliation_db)
    try:
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

        matches = find_potential_matches(reconciliation_db)

        seen_pairs = set()
        for match in matches:
            pair = (match["debit_txn_id"], match["credit_txn_id"])
            assert pair not in seen_pairs, f"Duplicate match found: {pair}"
            seen_pairs.add(pair)
    finally:
        conn.close()


@given(transactions=transactions_strategy())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_deterministic_matching_property(
    transactions, reconciliation_db: str, _pristine_db_template: Path
):
    """Property: Same input must always produce the same matches."""
    reconciliation_db = _fresh_reconciliation_db(_pristine_db_template)
    conn = sqlite3.connect(reconciliation_db)
    try:
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

        matches_1 = find_potential_matches(reconciliation_db)
        matches_2 = find_potential_matches(reconciliation_db)

        assert len(matches_1) == len(matches_2), "Match count should be identical"

        keys_1 = sorted([m["deterministic_key"] for m in matches_1])
        keys_2 = sorted([m["deterministic_key"] for m in matches_2])
        assert keys_1 == keys_2, "Match keys should be identical"

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


@given(transactions=transactions_strategy())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_no_cycles_property(
    transactions, reconciliation_db: str, _pristine_db_template: Path
):
    """Property: Matching must not create cycles in the transaction graph."""
    reconciliation_db = _fresh_reconciliation_db(_pristine_db_template)
    conn = sqlite3.connect(reconciliation_db)
    try:
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

        matches = find_potential_matches(reconciliation_db)

        pairs = set()
        for match in matches:
            pair = (match["debit_txn_id"], match["credit_txn_id"])
            mirrored = (match["credit_txn_id"], match["debit_txn_id"])
            assert mirrored not in pairs, f"Cycle detected: {pair} and {mirrored}"
            pairs.add(pair)
    finally:
        conn.close()


@given(transactions=transactions_strategy())
@settings(
    max_examples=10,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_bipartite_matching_property(
    transactions, reconciliation_db: str, _pristine_db_template: Path
):
    """Property: Matches must be valid for bipartite graphs (debit ↔ credit)."""
    reconciliation_db = _fresh_reconciliation_db(_pristine_db_template)
    conn = sqlite3.connect(reconciliation_db)
    try:
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

        matches = find_potential_matches(reconciliation_db)

        for match in matches:
            assert (
                match["debit_account_id"] != match["credit_account_id"]
            ), f"Invalid bipartite match: same account {match['debit_account_id']}"
            assert (
                match["debit_txn_id"] != match["credit_txn_id"]
            ), "Invalid bipartite match: same transaction"
    finally:
        conn.close()


@given(
    transactions=st.lists(
        transaction_strategy(),
        min_size=0,
        max_size=1,
    )
)
@settings(
    max_examples=5,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_edge_cases_property(transactions, reconciliation_db: str):
    """Property: Handle edge cases (zero or single transaction)."""
    conn = sqlite3.connect(reconciliation_db)
    try:
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

        matches = find_potential_matches(reconciliation_db)
        assert isinstance(matches, list), "Matches should always be a list"
        assert len(matches) == 0, "No matches expected for edge cases"
    finally:
        conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
