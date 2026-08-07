"""Plain-Python builder functions for test data.

These module-level builder functions provide a lightweight alternative to
class-based builders for simple test objects.

Backward compatibility:
    ``tests.conftest`` re-exports these symbols so existing imports such as::

        from tests.conftest import make_transaction

    continue to work unchanged.
"""

from __future__ import annotations

from typing import Any


def make_transaction(
    date_iso: str = "2025-01-15",
    description: str = "ENTERPRISE_MERCHANT",
    amount_paise: int = 10000,
    category: str = "operations",
    time_iso: str | None = "10:00:00",
    txn_type: str = "debit",
    account_id: str = "1",
) -> dict[str, Any]:
    """Build a strongly-typed transaction dictionary adhering to core domain schema."""
    return {
        "date_iso": date_iso,
        "time_iso": time_iso,
        "description": description,
        "amount_paise": amount_paise,
        "category": category,
        "type": txn_type,
        "account_id": account_id,
    }


def make_reconciliation_match(
    debit_txn_id: int = 1,
    credit_txn_id: int = 2,
    debit_account_id: str = "1",
    credit_account_id: str = "ACC_SECONDARY_02",
    amount_paise: int = 10000,
    date_diff_days: int = 0,
    confidence_bps: int = 10000,
    match_type: str = "exact",
) -> dict[str, Any]:
    """Build a strongly-typed reconciliation match dictionary."""
    return {
        "debit_txn_id": debit_txn_id,
        "credit_txn_id": credit_txn_id,
        "debit_account_id": debit_account_id,
        "credit_account_id": credit_account_id,
        "amount_paise": amount_paise,
        "date_diff_days": date_diff_days,
        "confidence_bps": confidence_bps,
        "match_type": match_type,
        "deterministic_key": f"{debit_txn_id}:{credit_txn_id}",
    }
