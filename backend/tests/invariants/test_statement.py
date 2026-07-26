"""Statement invariant tests."""

from __future__ import annotations

from invariants.statement import (  # noqa: F401,F403
    assert_statement_detection_invariants,
    assert_statement_integrity,
)


def test_statement_invariant_module_exists() -> None:
    """Verify statement invariant module functions are callable."""
    assert callable(assert_statement_integrity)
    assert callable(assert_statement_detection_invariants)
    assert_statement_integrity(
        {"statement_cycle_day": 15, "total_outstanding_paise": 1000}
    )
    assert_statement_detection_invariants(
        {"total_outstanding_paise": 1000, "confidence_bps": 5000}
    )
