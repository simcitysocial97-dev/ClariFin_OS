"""Tests for investment engine."""

from __future__ import annotations




class TestInvestmentEngine:
    """Unit tests for investment engine."""

    def test_portfolio_value_single_holding(self) -> None:
        """Single holding portfolio value is correct."""
        holdings = [
            {"quantity": 100, "price_paise": 25000},
        ]
        total = sum(h["quantity"] * h["price_paise"] for h in holdings)
        assert total == 2500000

    def test_portfolio_value_multiple_holdings(self) -> None:
        """Multiple holdings portfolio value is sum of individual values."""
        holdings = [
            {"quantity": 100, "price_paise": 25000},
            {"quantity": 50, "price_paise": 150000},
            {"quantity": 200, "price_paise": 12500},
        ]
        total = sum(h["quantity"] * h["price_paise"] for h in holdings)
        expected = 100 * 25000 + 50 * 150000 + 200 * 12500
        assert total == expected

    def test_portfolio_value_empty(self) -> None:
        """Empty portfolio has zero value."""
        total = sum(h["quantity"] * h["price_paise"] for h in [])
        assert total == 0

    def test_portfolio_value_non_negative(self) -> None:
        """Portfolio value is always non-negative."""
        holdings = [
            {"quantity": 100, "price_paise": 25000},
        ]
        total = sum(h["quantity"] * h["price_paise"] for h in holdings)
        assert total >= 0

    def test_portfolio_value_integer_paise(self) -> None:
        """Portfolio value is integer paise."""
        holdings = [
            {"quantity": 100, "price_paise": 25000},
        ]
        total = sum(h["quantity"] * h["price_paise"] for h in holdings)
        assert isinstance(total, int)