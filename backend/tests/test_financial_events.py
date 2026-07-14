"""Tests for FinancialEvent model and lineage walker.

Run: python -m pytest tests/test_financial_events.py -v
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from engines.financial_events.lineage_walker import (
    DEFAULT_ROLLOVER_LOOKBACK_DAYS,
    walk_lineage,
)
from models.financial_event import FinancialEvent
from repositories.financial_event_repository import FinancialEventRepository

# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    conn = sqlite3.connect(db_path)

    # Create financial_events table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            transaction_ids TEXT NOT NULL,
            amount_paise INTEGER DEFAULT 0,
            asset_change_paise INTEGER DEFAULT 0,
            liability_change_paise INTEGER DEFAULT 0,
            expense_paise INTEGER DEFAULT 0,
            income_paise INTEGER DEFAULT 0,
            date_iso TEXT NOT NULL,
            month_bucket TEXT NOT NULL,
            account_id TEXT,
            counterparty_account_id TEXT,
            category TEXT,
            subcategory TEXT,
            sub_type TEXT,
            provider TEXT,
            household_id TEXT DEFAULT 'primary',
            owner_id TEXT DEFAULT 'self',
            lifecycle_state TEXT DEFAULT 'open',
            settled_by_event_id INTEGER,
            outstanding_paise INTEGER DEFAULT 0,
            superseded_by INTEGER,
            confidence REAL DEFAULT 0.0,
            confidence_bps INTEGER,
            notes TEXT,
            reviewed_by_user INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

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

    # Create financial_event_lifecycle_log table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS financial_event_lifecycle_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES financial_events(id),
            previous_lifecycle_state TEXT,
            new_lifecycle_state TEXT NOT NULL,
            previous_outstanding_paise INTEGER,
            new_outstanding_paise INTEGER,
            caused_by_event_id INTEGER,
            actor TEXT NOT NULL DEFAULT 'system',
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()

    yield db_path

    os.unlink(db_path)


# ============================================================
# Test 1: FinancialEvent Model - Backward Compatibility
# ============================================================

def test_financial_event_backward_compatible_fields():
    """Test that original fields still work and new fields default correctly."""
    event = FinancialEvent(
        event_type="expense",
        date_iso="2025-01-15",
        amount_paise=50000,  # ₹500
    )

    assert event.event_type == "expense"
    assert event.amount_paise == 50000
    assert event.asset_change_paise == 0
    assert event.liability_change_paise == 0
    assert event.expense_paise == 0
    assert event.income_paise == 0
    assert event.month_bucket == "2025-01"  # Derived from date_iso
    assert event.lifecycle_state == "open"
    assert event.household_id == "primary"
    assert event.owner_id == "self"


def test_financial_event_new_event_types():
    """Test that new event types with granular fields work correctly."""
    # EMI payment: reduces liability, creates expense
    emi_event = FinancialEvent(
        event_type="emi_payment",
        transaction_ids=[1, 2, 3],
        date_iso="2025-01-15",
        liability_change_paise=-100000,  # Liability decreases (negative)
        expense_paise=100000,  # Expense of ₹1000
        amount_paise=100000,  # Backward compatible
        account_id="HDFC_CC",
        category="EMI & Loans",
        confidence_bps=8500,
    )

    assert emi_event.event_type == "emi_payment"
    assert emi_event.liability_change_paise == -100000
    assert emi_event.expense_paise == 100000
    assert emi_event.amount_paise == 100000  # Preserved for backward compat


def test_financial_event_month_bucket_derived():
    """Test that month_bucket is derived from date_iso when not provided."""
    event = FinancialEvent(
        event_type="income",
        date_iso="2025-06-30",
    )

    assert event.month_bucket == "2025-06"


def test_financial_event_month_bucket_explicit():
    """Test that explicit month_bucket overrides derivation."""
    event = FinancialEvent(
        event_type="income",
        date_iso="2025-06-30",
        month_bucket="2025-05",  # Explicitly set
    )

    # Explicit value should be preserved
    assert event.month_bucket == "2025-05"


# ============================================================
# Test 2: Repository Operations
# ============================================================

def test_insert_and_fetch_event(temp_db):
    """Test inserting and fetching financial events."""
    repo = FinancialEventRepository(temp_db)

    event = FinancialEvent(
        event_type="emi_payment",
        transaction_ids=[100, 101],
        date_iso="2025-01-15",
        liability_change_paise=-50000,
        expense_paise=50000,
        amount_paise=50000,
        account_id="HDFC_loan",
        category="EMI & Loans",
        confidence_bps=8500,
        household_id="primary",
    )

    event_id = repo.insert_event(event)
    assert event_id > 0

    # Fetch events for month
    events = repo.get_events_for_month("2025-01", "primary")
    assert len(events) == 1
    assert events[0]["event_type"] == "emi_payment"
    assert events[0]["transaction_ids"] == "[100, 101]"  # JSON stored


def test_lifecycle_update(temp_db):
    """Test updating lifecycle state of an event."""
    repo = FinancialEventRepository(temp_db)

    event = FinancialEvent(
        event_type="credit_card_cash_advance",
        transaction_ids=[200],
        date_iso="2025-01-15",
        liability_change_paise=100000,  # Liability increases
        amount_paise=100000,
        account_id="ICICI_CC",
        outstanding_paise=100000,
        household_id="primary",
    )

    event_id = repo.insert_event(event)

    # Update lifecycle
    updated = repo.update_lifecycle(
        event_id=event_id,
        lifecycle_state="partially_settled",
        outstanding_paise=50000,
    )
    assert updated is True

    # Verify update
    events = repo.get_events_for_month("2025-01", "primary")
    assert events[0]["lifecycle_state"] == "partially_settled"


def test_insert_link(temp_db):
    """Test creating links between events."""
    repo = FinancialEventRepository(temp_db)

    # Create two events
    advance = FinancialEvent(
        event_type="credit_card_cash_advance",
        transaction_ids=[300],
        date_iso="2025-01-01",
        liability_change_paise=100000,
        amount_paise=100000,
        account_id="ICICI_CC",
        outstanding_paise=100000,
    )
    advance_id = repo.insert_event(advance)

    payment = FinancialEvent(
        event_type="liability_repayment",
        transaction_ids=[301],
        date_iso="2025-01-15",
        liability_change_paise=-100000,
        amount_paise=100000,
        account_id="ICICI_CC",
    )
    payment_id = repo.insert_event(payment)

    # Create link
    link_id = repo.insert_link(
        event_id=payment_id,
        linked_event_id=advance_id,
        link_type="settles",
    )
    assert link_id > 0

    # Fetch links
    links = repo.get_links_for_event(payment_id)
    assert len(links) == 1
    assert links[0]["link_type"] == "settles"


# ============================================================
# Test 3: Lifecycle Logging Tests
# ============================================================

def test_lifecycle_update_creates_log_entry(temp_db):
    """Test that update_lifecycle creates exactly one log entry with correct values."""
    repo = FinancialEventRepository(temp_db)

    event = FinancialEvent(
        event_type="credit_card_cash_advance",
        transaction_ids=[400],
        date_iso="2025-01-15",
        liability_change_paise=100000,
        amount_paise=100000,
        account_id="ICICI_CC",
        outstanding_paise=100000,
        household_id="primary",
    )
    event_id = repo.insert_event(event)

    # Update lifecycle
    updated = repo.update_lifecycle(
        event_id=event_id,
        lifecycle_state="partially_settled",
        outstanding_paise=50000,
        actor="system",
    )
    assert updated is True

    # Verify exactly one log entry exists
    log_entries = repo.get_lifecycle_history(event_id)
    assert len(log_entries) == 1

    # Verify log entry has correct previous/new values
    entry = log_entries[0]
    assert entry["event_id"] == event_id
    assert entry["previous_lifecycle_state"] == "open"
    assert entry["new_lifecycle_state"] == "partially_settled"
    assert entry["previous_outstanding_paise"] == 100000
    assert entry["new_outstanding_paise"] == 50000
    assert entry["actor"] == "system"


def test_lifecycle_update_multiple_transitions(temp_db):
    """Test multiple sequential updates produce complete ordered history."""
    repo = FinancialEventRepository(temp_db)

    event = FinancialEvent(
        event_type="credit_card_cash_advance",
        transaction_ids=[500],
        date_iso="2025-01-01",
        liability_change_paise=150000,
        amount_paise=150000,
        account_id="ICICI_CC",
        outstanding_paise=150000,
        household_id="primary",
    )
    event_id = repo.insert_event(event)

    # Transition 1: open -> partially_settled
    repo.update_lifecycle(
        event_id=event_id,
        lifecycle_state="partially_settled",
        outstanding_paise=75000,
    )

    # Transition 2: partially_settled -> settled
    repo.update_lifecycle(
        event_id=event_id,
        lifecycle_state="settled",
        outstanding_paise=0,
    )

    # Verify complete history
    log_entries = repo.get_lifecycle_history(event_id)
    assert len(log_entries) == 2

    # Verify first entry (open -> partially_settled)
    entry1 = log_entries[0]
    assert entry1["previous_lifecycle_state"] == "open"
    assert entry1["new_lifecycle_state"] == "partially_settled"
    assert entry1["previous_outstanding_paise"] == 150000
    assert entry1["new_outstanding_paise"] == 75000

    # Verify second entry (partially_settled -> settled)
    entry2 = log_entries[1]
    assert entry2["previous_lifecycle_state"] == "partially_settled"
    assert entry2["new_lifecycle_state"] == "settled"
    assert entry2["previous_outstanding_paise"] == 75000
    assert entry2["new_outstanding_paise"] == 0


def test_lifecycle_log_with_caused_by_event(temp_db):
    """Test that caused_by_event_id is logged correctly."""
    repo = FinancialEventRepository(temp_db)

    # Create a cash advance
    advance = FinancialEvent(
        event_type="credit_card_cash_advance",
        transaction_ids=[600],
        date_iso="2025-01-01",
        liability_change_paise=100000,
        amount_paise=100000,
        account_id="ICICI_CC",
        outstanding_paise=100000,
        household_id="primary",
    )
    advance_id = repo.insert_event(advance)

    # Create a payment event
    payment = FinancialEvent(
        event_type="liability_repayment",
        transaction_ids=[601],
        date_iso="2025-01-15",
        liability_change_paise=-100000,
        amount_paise=100000,
        account_id="ICICI_CC",
    )
    payment_id = repo.insert_event(payment)

    # Update with caused_by_event_id
    repo.update_lifecycle(
        event_id=advance_id,
        lifecycle_state="settled",
        outstanding_paise=0,
        caused_by_event_id=payment_id,
    )

    log_entries = repo.get_lifecycle_history(advance_id)
    assert len(log_entries) == 1
    assert log_entries[0]["caused_by_event_id"] == payment_id


def test_lifecycle_update_nonexistent_event_returns_false(temp_db):
    """Test that updating nonexistent event returns False."""
    repo = FinancialEventRepository(temp_db)

    updated = repo.update_lifecycle(
        event_id=99999,
        lifecycle_state="settled",
        outstanding_paise=0,
    )
    assert updated is False


# ============================================================
# Test 4: Lineage Walker - Pure Function Tests
# ============================================================

def test_lineage_walker_no_db_calls():
    """Test that walk_lineage makes no DB calls."""
    from unittest.mock import patch

    events = [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "date_iso": "2025-01-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": 100000,
            "outstanding_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "liability_repayment",
            "date_iso": "2025-01-15",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": -100000,
        },
    ]

    with patch('sqlite3.connect') as mock_connect:
        proposal = walk_lineage(events)
        assert mock_connect.call_count == 0, "walk_lineage should not call sqlite3.connect"
        assert len(proposal.proposed_links) == 1
        assert proposal.proposed_links[0]["link_type"] == "settles"


def test_full_payment_creates_settled_state():
    """Test that full payment updates advance to settled state."""
    events = [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "date_iso": "2025-01-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": 100000,
            "outstanding_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "liability_repayment",
            "date_iso": "2025-01-15",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": -100000,
        },
    ]

    proposal = walk_lineage(events)

    assert len(proposal.lifecycle_updates) == 1
    assert proposal.lifecycle_updates[0]["lifecycle_state"] == "settled"
    assert proposal.lifecycle_updates[0]["outstanding_paise"] == 0


def test_partial_payment_creates_partially_settled_state():
    """Test that partial payment updates advance to partially_settled state."""
    events = [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "date_iso": "2025-01-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": 100000,
            "outstanding_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "liability_repayment",
            "date_iso": "2025-01-15",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": -50000,  # Partial payment
        },
    ]

    proposal = walk_lineage(events)

    assert len(proposal.lifecycle_updates) == 1
    assert proposal.lifecycle_updates[0]["lifecycle_state"] == "partially_settled"
    assert proposal.lifecycle_updates[0]["outstanding_paise"] == 50000


def test_lineage_walker_idempotent():
    """Test that re-running lineage walker produces no duplicate links."""
    events = [
        {
            "id": 1,
            "event_type": "credit_card_cash_advance",
            "date_iso": "2025-01-01",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": 100000,
            "outstanding_paise": 100000,
        },
        {
            "id": 2,
            "event_type": "liability_repayment",
            "date_iso": "2025-01-15",
            "account_id": "CC1",
            "lifecycle_state": "open",
            "liability_change_paise": -100000,
        },
    ]

    proposal1 = walk_lineage(events)
    proposal2 = walk_lineage(events)

    assert len(proposal1.proposed_links) == len(proposal2.proposed_links)


# ============================================================
# Test 4: BehaviourInput with FinancialEvents
# ============================================================

def test_behaviour_input_with_financial_events():
    """Test that BehaviourInput accepts financial_events field."""
    from models.financial_event import BehaviourInput

    input_data = BehaviourInput(
        transactions=[{"id": 1, "amount_paise": 10000}],
        accounts=[{"id": "A1", "balance_paise": 50000}],
        loans=[{"id": 1}],
        credit_cards=[{"id": "CC1"}],
        reconciliations=[(1, 2)],
        financial_events=[
            {"event_type": "expense", "amount_paise": 5000, "date_iso": "2025-01-15"}
        ],
    )

    assert input_data.financial_events is not None
    assert len(input_data.financial_events) == 1


# ============================================================
# Test 5: Constants
# ============================================================

def test_rollover_lookback_constant():
    """Test that rollover lookback constant is defined correctly."""
    assert DEFAULT_ROLLOVER_LOOKBACK_DAYS == 90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
