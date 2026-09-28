# backend/tests/unit/engines/behaviour/test_month_bucket_contract.py
#
# M9-C71 — Contract tests for the behaviour-engine MONTH-BUCKET contract.
#
# WHY THIS FILE EXISTS
# --------------------
# `_get_monthly_income_expenses_data` and `_get_monthly_category_spending_data`
# reduce a flat transaction list into `{month: {...}}` maps, and the KEY of that
# map is a `YYYY-MM` string. Every behaviour index in the engine — savings
# discipline, spending stability, stress — is computed by iterating those keys,
# so a key that is not a real month silently corrupts every downstream number.
#
# The fragile part is the month derivation:
#
#     date_iso = txn.get("date_iso", "")
#     month    = date_iso[:7] if date_iso else ""
#
# A transaction with no `date_iso` is assigned the empty-string key "", which is
# not a month. Mutating the default to any non-empty string ("" -> "XXXX")
# instead routes that transaction into a fabricated month, so the mutation is
# observable and was surviving because no test supplied a dateless transaction.
#
# The pre-existing tests cover ordinary dated transactions well. None supply a
# transaction whose `date_iso` is missing, and none assert that every key the
# function returns is a real `YYYY-MM` month.
#
# These tests pin the key contract and the totals, which is what the rest of the
# engine is entitled to assume.

from __future__ import annotations

import re

from src.engines.behaviour_engine import core

#: A real month key is exactly YYYY-MM.
MONTH_KEY = re.compile(r"^\d{4}-\d{2}$")

CUTOFF = "2025-01-01"


def _txn(**overrides) -> dict:
    """A plausible transaction.

    A key whose value is the string ``"__DROP__"`` is removed rather than set,
    because these functions read every field with a default, so a present-but-
    null field is not the same as an absent one.
    """
    base = {
        "id": 1,
        "type": "debit",
        "date_iso": "2025-01-15",
        "amount_paise": 100_000,
        "category": "Food",
    }
    for key, value in overrides.items():
        if value == "__DROP__":
            base.pop(key, None)
        else:
            base[key] = value
    return base


# ── the key contract ─────────────────────────────────────────────────────────


class TestMonthKeysAreRealMonths:
    def test_income_expense_keys_are_yyyy_mm(self):
        result = core._get_monthly_income_expenses_data(
            [_txn(), _txn(id=2, date_iso="2025-02-20")], CUTOFF
        )

        assert result
        for month in result:
            assert MONTH_KEY.match(month), f"{month!r} is not a YYYY-MM month"

    def test_category_spending_keys_are_yyyy_mm(self):
        result = core._get_monthly_category_spending_data(
            [_txn(), _txn(id=2, date_iso="2025-02-20")], CUTOFF
        )

        assert result
        for month in result:
            assert MONTH_KEY.match(month), f"{month!r} is not a YYYY-MM month"

    def test_a_dateless_transaction_produces_no_month_at_all(self):
        """An undated transaction cannot be assigned to a month, so it is
        dropped by the cutoff comparison — "" sorts before any ISO date.

        The mutation `txn.get("date_iso", "XXXX")` flips that: "XXXX" sorts
        AFTER the cutoff, so an undated transaction is admitted and lands in a
        fabricated month bucket. Asserting that no fabricated key appears is
        what kills it, and it is the honest statement of the contract —
        undated spend is not a month of spending.
        """
        result = core._get_monthly_income_expenses_data(
            [_txn(), _txn(id=2, date_iso="__DROP__")], CUTOFF
        )

        assert result == {"2025-01": {"income_paise": 0, "expenses_paise": 100_000}}
        for month in result:
            assert MONTH_KEY.match(month), f"fabricated month key {month!r}"

    def test_undated_category_spend_is_dropped_not_bucketed(self):
        """Same contract for the category aggregation."""
        result = core._get_monthly_category_spending_data(
            [_txn(), _txn(id=2, date_iso="__DROP__")], CUTOFF
        )

        assert result == {"2025-01": {"Food": 100_000}}
        for month in result:
            assert MONTH_KEY.match(month), f"fabricated month key {month!r}"

    def test_every_returned_key_parses_as_a_month(self):
        """The blanket guarantee, across a mixed population.

        Whatever else is true of a month bucket, its key must be a real
        `YYYY-MM` month, because every behaviour index in the engine iterates
        these keys and parses them.
        """
        result = core._get_monthly_income_expenses_data(
            [
                _txn(),
                _txn(id=2, date_iso="2025-02-20"),
                _txn(id=3, date_iso="__DROP__"),
                _txn(id=4, date_iso="2024-01-01"),  # before cutoff
            ],
            CUTOFF,
        )

        assert result
        for month in result:
            assert MONTH_KEY.match(month), f"{month!r} is not a YYYY-MM month"


# ── the cutoff contract ──────────────────────────────────────────────────────


class TestMonthCutoffBoundary:
    def test_a_transaction_before_the_cutoff_is_excluded(self):
        result = core._get_monthly_income_expenses_data(
            [_txn(date_iso="2024-12-31", amount_paise=999_999)], CUTOFF
        )

        assert result == {}

    def test_a_transaction_on_the_cutoff_is_included(self):
        """The comparison is `>=`, so the cutoff day itself counts."""
        result = core._get_monthly_income_expenses_data(
            [_txn(date_iso=CUTOFF, amount_paise=100_000)], CUTOFF
        )

        assert result.get("2025-01", {}).get("expenses_paise") == 100_000

    def test_one_day_before_the_cutoff_is_excluded(self):
        result = core._get_monthly_income_expenses_data(
            [_txn(date_iso="2024-12-31", amount_paise=100_000)], CUTOFF
        )

        assert "2025-01" not in result


# ── the totals contract ──────────────────────────────────────────────────────


class TestMonthlyTotals:
    def test_credits_are_income_and_debits_are_expenses(self):
        result = core._get_monthly_income_expenses_data(
            [
                _txn(type="credit", amount_paise=500_000, date_iso="2025-01-10"),
                _txn(id=2, type="debit", amount_paise=200_000, date_iso="2025-01-11"),
            ],
            CUTOFF,
        )

        month = result["2025-01"]
        assert month["income_paise"] == 500_000
        assert month["expenses_paise"] == 200_000

    def test_months_are_kept_separate(self):
        """Money spent in January is not February's spending."""
        result = core._get_monthly_income_expenses_data(
            [
                _txn(amount_paise=100_000, date_iso="2025-01-05"),
                _txn(id=2, amount_paise=300_000, date_iso="2025-02-05"),
            ],
            CUTOFF,
        )

        assert result["2025-01"]["expenses_paise"] == 100_000
        assert result["2025-02"]["expenses_paise"] == 300_000

    def test_transactions_in_the_same_month_are_summed(self):
        result = core._get_monthly_income_expenses_data(
            [
                _txn(amount_paise=100_000, date_iso="2025-01-05"),
                _txn(id=2, amount_paise=250_000, date_iso="2025-01-25"),
            ],
            CUTOFF,
        )

        assert result["2025-01"]["expenses_paise"] == 350_000

    def test_credits_are_not_counted_as_category_spending(self):
        """Only debits are spending; a credit is income, not a category total."""
        result = core._get_monthly_category_spending_data(
            [
                _txn(type="credit", amount_paise=500_000, category="Refund"),
                _txn(id=2, type="debit", amount_paise=100_000, category="Food"),
            ],
            CUTOFF,
        )

        month = result["2025-01"]
        assert "Refund" not in month
        assert month["Food"] == 100_000

    def test_an_uncategorised_transaction_lands_in_uncategorised(self):
        """A missing category is 'Uncategorized', never silently dropped."""
        result = core._get_monthly_category_spending_data(
            [_txn(category="__DROP__")], CUTOFF
        )

        month = result["2025-01"]
        assert month.get("Uncategorized") == 100_000

    def test_a_missing_amount_counts_as_zero_not_a_crash(self):
        result = core._get_monthly_income_expenses_data(
            [_txn(amount_paise="__DROP__")], CUTOFF
        )

        assert result["2025-01"]["expenses_paise"] == 0

    def test_empty_input_produces_empty_output(self):
        assert core._get_monthly_income_expenses_data([], CUTOFF) == {}
        assert core._get_monthly_category_spending_data([], CUTOFF) == {}
