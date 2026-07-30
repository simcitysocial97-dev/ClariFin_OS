"""Capability tests for fund transfer revocation.

Tests revocation logic with smart defaults:
- Revocation within 7-day window
- Auto-revoke for failed transfers
- Lifecycle state transitions
- Lineage linking
"""

from datetime import datetime, timedelta

import pytest

from src.engines.financial_events.lineage_walker import (
    DEFAULT_REVOCATION_LOOKBACK_DAYS,
    walk_lineage,
)


@pytest.fixture
def sample_transfer_events():
    """Fixture: Sample transfer events for testing."""
    datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    last_week = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")

    return [
        # Transfer 1: Recent transfer (within revocation window)
        {
            "id": 101,
            "event_type": "fund_transfer_out",
            "account_id": "acc_1",
            "transfer_id": "transfer_1",
            "date_iso": yesterday,
            "lifecycle_state": "open",
            "liability_change_paise": -500000,  # -₹5,000
        },
        {
            "id": 102,
            "event_type": "fund_transfer_in",
            "account_id": "acc_2",
            "transfer_id": "transfer_1",
            "date_iso": yesterday,
            "lifecycle_state": "open",
            "liability_change_paise": 500000,  # +₹5,000
        },
        # Transfer 2: Old transfer (outside revocation window)
        {
            "id": 201,
            "event_type": "fund_transfer_out",
            "account_id": "acc_1",
            "transfer_id": "transfer_2",
            "date_iso": last_week,
            "lifecycle_state": "open",
            "liability_change_paise": -300000,  # -₹3,000
        },
        {
            "id": 202,
            "event_type": "fund_transfer_in",
            "account_id": "acc_2",
            "transfer_id": "transfer_2",
            "date_iso": last_week,
            "lifecycle_state": "open",
            "liability_change_paise": 300000,  # +₹3,000
        },
        # Transfer 3: Failed transfer (auto-revoke candidate)
        {
            "id": 301,
            "event_type": "fund_transfer_out",
            "account_id": "acc_1",
            "transfer_id": "transfer_3",
            "date_iso": yesterday,
            "lifecycle_state": "failed",
            "liability_change_paise": -200000,  # -₹2,000
        },
    ]


@pytest.fixture
def revocation_event():
    """Fixture: Revocation event for transfer_1."""
    return {
        "id": 901,
        "event_type": "transfer_revocation",
        "transfer_id": "transfer_1",
        "date_iso": datetime.now().strftime("%Y-%m-%d"),
        "lifecycle_state": "open",
    }


def test_revocation_within_window(sample_transfer_events, revocation_event):
    """Test: Revocation within 7-day window should succeed."""
    events = sample_transfer_events + [revocation_event]
    proposal = walk_lineage(events)

    # Should create revocation links
    revoke_links = [
        link for link in proposal.proposed_links if link["link_type"] == "revokes"
    ]
    assert len(revoke_links) == 2  # Both sides of transfer_1

    # Should update lifecycle state to "revoked" for transfer_1
    revoked_updates = [
        update
        for update in proposal.lifecycle_updates
        if update["lifecycle_state"] == "revoked" and update["event_id"] in [101, 102]
    ]
    assert len(revoked_updates) == 2
    assert all(update["outstanding_paise"] == 0 for update in revoked_updates)

    # Should supersede transfer_1 events
    assert 101 in proposal.superseded_events
    assert 102 in proposal.superseded_events

    # Should also auto-revoke failed transfer (transfer_3)
    auto_revoked = [
        update for update in proposal.lifecycle_updates if update.get("auto_revoked")
    ]
    assert len(auto_revoked) == 1
    assert 301 in proposal.superseded_events


def test_revocation_outside_window(sample_transfer_events):
    """Test: Revocation outside 7-day window should fail."""
    old_revocation = {
        "id": 902,
        "event_type": "transfer_revocation",
        "transfer_id": "transfer_2",  # 8 days old
        "date_iso": datetime.now().strftime("%Y-%m-%d"),
        "lifecycle_state": "open",
    }
    events = sample_transfer_events + [old_revocation]
    proposal = walk_lineage(events)

    # Should NOT create any revocation links
    revoke_links = [
        link for link in proposal.proposed_links if link["link_type"] == "revokes"
    ]
    assert len(revoke_links) == 0


def test_auto_revoke_failed_transfer(sample_transfer_events):
    """Test: Failed transfers should be auto-revoked (smart default)."""
    # Add auto-revocation event for failed transfer
    auto_revocation = {
        "id": 903,
        "event_type": "transfer_revocation",
        "transfer_id": "transfer_3",  # Failed transfer
        "date_iso": datetime.now().strftime("%Y-%m-%d"),
        "lifecycle_state": "open",
        "auto_generated": True,
    }
    events = sample_transfer_events + [auto_revocation]
    proposal = walk_lineage(events)

    # Should auto-revoke failed transfer (no explicit revocation link needed)
    auto_revoked = [
        update for update in proposal.lifecycle_updates if update.get("auto_revoked")
    ]
    assert len(auto_revoked) == 1
    assert auto_revoked[0]["event_id"] == 301
    assert auto_revoked[0]["lifecycle_state"] == "revoked"


def test_revocation_lookback_window():
    """Test: DEFAULT_REVOCATION_LOOKBACK_DAYS is set to 7 days."""
    assert DEFAULT_REVOCATION_LOOKBACK_DAYS == 7
