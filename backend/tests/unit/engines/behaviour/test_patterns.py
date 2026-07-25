"""Tests for Behaviour Engine Phase 3 — Pattern Detection.

Consolidated from test_behaviour_engine_patterns.py.
Tests weekend/night spend ratios, impulse detection, recurring merchants,
and subscription patterns.

All monetary values are integers in paise (₹1.00 = 100 paise).
"""

from datetime import datetime, timedelta
from decimal import Decimal

from engines.behaviour_engine import (
    compute_night_spend_ratio,
    compute_weekend_spend_ratio,
    detect_impulse_transactions,
    detect_recurring_merchants,
    detect_subscription_patterns,
)
from tests.conftest import make_transaction

# ============================================================
# Tests: Weekend Spending
# ============================================================


def test_weekend_purchases():
    """Weekend purchases should be detected."""
    # Use known dates: Jan 4 (Saturday), Jan 5 (Sunday), Jan 6 (Monday)
    transactions = [
        make_transaction("2025-01-04", amount_paise=50000),  # Saturday
        make_transaction("2025-01-05", amount_paise=50000),  # Sunday
        make_transaction("2025-01-06", amount_paise=50000),  # Monday
    ]

    ratio = compute_weekend_spend_ratio(transactions)
    assert ratio == Decimal("0.6667")  # 2/3 rounded


def test_weekend_ratio_no_debits():
    """No debit transactions should return 0 ratio."""
    transactions = [
        {
            "date_iso": datetime.now().strftime("%Y-%m-%d"),
            "amount_paise": 50000,
            "type": "credit",
        },
    ]

    ratio = compute_weekend_spend_ratio(transactions)
    assert ratio == Decimal("0")


def test_weekend_ratio_empty():
    """Empty transactions should return 0 ratio."""
    ratio = compute_weekend_spend_ratio([])
    assert ratio == Decimal("0")


# ============================================================
# Tests: Night Spending
# ============================================================


def test_night_spending_with_time():
    """Night spending should be detected when time data is present."""
    transactions = [
        make_transaction("2025-01-15", time_iso="21:30", amount_paise=50000),  # night
        make_transaction("2025-01-15", time_iso="13:00", amount_paise=50000),  # day
        make_transaction("2025-01-15", time_iso="01:30", amount_paise=50000),  # night
    ]

    ratio = compute_night_spend_ratio(transactions)
    assert ratio == Decimal("0.6667")  # 33333/50000 rounded


def test_night_spending_missing_time():
    """Missing time data should return 0 ratio."""
    transactions = [
        make_transaction("2025-01-15"),  # no time
        make_transaction("2025-01-15"),  # no time
    ]

    ratio = compute_night_spend_ratio(transactions)
    assert ratio == Decimal("0")


def test_night_spending_boundary():
    """Time at boundary 19:59 should be day, 20:00 should be night."""
    transactions = [
        make_transaction("2025-01-15", time_iso="19:59", amount_paise=50000),  # day
        make_transaction("2025-01-15", time_iso="20:00", amount_paise=50000),  # night
    ]

    ratio = compute_night_spend_ratio(transactions)
    assert ratio == Decimal("0.5")  # 1/2 at night


# ============================================================
# Tests: Impulse Purchase Detection
# ============================================================


def test_impulse_transactions_weekend():
    """Weekend impulse transactions should be detected."""
    saturday = (
        datetime.now() + timedelta(days=(5 - datetime.now().weekday()) % 7)
    ).strftime("%Y-%m-%d")

    transactions = [
        make_transaction(saturday, "AMAZON", 60000, "shopping"),  # impulse
        make_transaction(
            "2025-01-15", "AMAZON", 60000, "shopping"
        ),  # weekday - not impulse
        make_transaction(
            saturday, "BIG BAZAAR", 10000, "groceries"
        ),  # too small, wrong category
    ]

    impulse = detect_impulse_transactions(transactions)
    assert len(impulse) == 1
    assert impulse[0]["description"] == "AMAZON"


def test_impulse_transactions_night_time():
    """Night time impulse transactions should be detected when time available."""
    transactions = [
        make_transaction(
            "2025-01-15", "SWIGGY", 60000, "food", "21:30"
        ),  # night impulse
        make_transaction(
            "2025-01-15", "SWIGGY", 60000, "food", "12:00"
        ),  # day - not impulse
    ]

    impulse = detect_impulse_transactions(transactions)
    assert len(impulse) == 1


def test_impulse_transactions_amount_threshold():
    """Transactions below amount threshold should be excluded."""
    transactions = [
        make_transaction("2025-01-15", "STORE", 40000, "shopping"),  # too small
    ]

    impulse = detect_impulse_transactions(transactions)
    assert len(impulse) == 0


# ============================================================
# Tests: Recurring Merchant Detection
# ============================================================


def test_recurring_netflix_style():
    """Netflix-style monthly charges should be detected as recurring."""
    base_date = datetime(2025, 1, 15)
    transactions = []

    # Same day, same amount, 4 months
    for i in range(4):
        date = (base_date + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        transactions.append(make_transaction(date, "NETFLIX", 79000, "entertainment"))

    recurring = detect_recurring_merchants(transactions, min_occurrences=1)
    assert len(recurring) == 1
    assert recurring[0]["merchant"] == "NETFLIX"
    assert recurring[0]["months_covered"] >= 2


def test_recurring_food_delivery():
    """Food delivery patterns across months should be detected."""
    base_date = datetime(2025, 1, 10)
    transactions = []

    # Multiple days per month, same merchant
    for month in range(3):
        for day in [5, 10, 15, 20]:
            date = (base_date + timedelta(days=30 * month + day)).strftime("%Y-%m-%d")
            transactions.append(make_transaction(date, "SWIGGY", 30000, "food"))

    recurring = detect_recurring_merchants(transactions, min_occurrences=2)
    assert len(recurring) == 1


def test_recurring_false_positive():
    """One-time large purchases should not be detected as recurring."""
    transactions = [
        make_transaction("2025-01-15", "ELECTRONICS", 500000, "shopping"),  # one-time
    ]

    recurring = detect_recurring_merchants(transactions)
    assert len(recurring) == 0


# ============================================================
# Tests: Subscription Detection
# ============================================================


def test_subscription_patterns():
    """Subscription patterns should be detected."""
    base_date = datetime(2025, 1, 15)
    transactions = []

    # Same day (15th), same amount, multiple months
    for i in range(4):
        date = (base_date + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        transactions.append(make_transaction(date, "NETFLIX", 79000, "entertainment"))

    subscriptions = detect_subscription_patterns(transactions)
    assert len(subscriptions) == 1
    assert subscriptions[0]["merchant"] == "NETFLIX"
    assert subscriptions[0]["day_of_month"] == 15
    assert subscriptions[0]["avg_amount_paise"] == 79000


def test_subscription_amount_variation():
    """Subscriptions with small amount variations should be detected."""
    base_date = datetime(2025, 1, 15)
    transactions = []

    # Netflix varies slightly (tax included)
    for i, amount in enumerate([79000, 79500, 79200, 79300]):
        date = (base_date + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        transactions.append(make_transaction(date, "NETFLIX", amount, "entertainment"))

    subscriptions = detect_subscription_patterns(
        transactions, amount_tolerance_bps=2000
    )
    assert len(subscriptions) == 1


def test_subscription_single_appearance():
    """Single appearance should not be detected as subscription."""
    transactions = [
        make_transaction("2025-01-15", "ONE-TIME", 79000, "entertainment"),
    ]

    subscriptions = detect_subscription_patterns(transactions)
    assert len(subscriptions) == 0


# ============================================================
# Tests: Determinism
# ============================================================


def test_weekend_ratio_deterministic():
    """Weekend ratio should be deterministic."""
    transactions = [
        make_transaction("2025-01-04", amount_paise=50000),  # Saturday
        make_transaction("2025-01-05", amount_paise=50000),  # Sunday
        make_transaction("2025-01-06", amount_paise=50000),  # Monday
    ]

    for _ in range(5):
        ratio = compute_weekend_spend_ratio(transactions)
        assert ratio == Decimal("0.6667")


def test_subscription_deterministic():
    """Subscription detection should be deterministic."""
    base_date = datetime(2025, 1, 15)
    transactions = []

    for i in range(4):
        date = (base_date + timedelta(days=30 * i)).strftime("%Y-%m-%d")
        transactions.append(make_transaction(date, "NETFLIX", 79000, "entertainment"))

    for _ in range(5):
        subscriptions = detect_subscription_patterns(transactions)
        assert len(subscriptions) == 1
        assert subscriptions[0]["merchant"] == "NETFLIX"
