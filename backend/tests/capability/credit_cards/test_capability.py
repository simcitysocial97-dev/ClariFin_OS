"""Smoke tests for Credit Cards capability."""

from __future__ import annotations



from tests.golden.builders.credit_card_revolver import load_credit_card_revolver


class TestCreditCardsCapability:
    """Validate Credit Cards capability wiring and invariants."""

    def test_import_credit_card_engine(self) -> None:
        """Credit card engine must be importable."""
        from src.engines import credit_card_engine

        assert credit_card_engine is not None

    def test_golden_dataset_credit_card_scenario(self) -> None:
        """Golden credit card dataset must load and validate."""
        data = load_credit_card_revolver()
        assert "accounts" in data or "transactions" in data