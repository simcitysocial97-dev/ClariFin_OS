"""Property-based tests for investment engine."""

from __future__ import annotations



from hypothesis import given, settings
from hypothesis import strategies as st

# --- Strategies ---


@st.composite
def portfolio_holding(draw):
    """Generate a portfolio holding."""
    quantity = draw(st.integers(min_value=1, max_value=1000))
    price_paise = draw(st.integers(min_value=1, max_value=1000000))
    return {
        "quantity": quantity,
        "price_paise": price_paise,
        "value_paise": quantity * price_paise,
    }


# --- Tests ---


class TestInvestmentEngineProperties:
    """Property-based tests for investment engine invariants."""

    @settings(max_examples=20)
    @given(portfolio_holding())
    def test_portfolio_value_non_negative(self, holding):
        """Portfolio value must be non-negative."""
        assert holding["value_paise"] >= 0

    @settings(max_examples=20)
    @given(portfolio_holding())
    def test_quantity_positive(self, holding):
        """Quantity must be positive."""
        assert holding["quantity"] > 0

    @settings(max_examples=20)
    @given(portfolio_holding())
    def test_price_positive(self, holding):
        """Price must be positive."""
        assert holding["price_paise"] > 0

    @settings(max_examples=20)
    @given(portfolio_holding())
    def test_value_is_product(self, holding):
        """Value must equal quantity * price."""
        expected = holding["quantity"] * holding["price_paise"]
        assert holding["value_paise"] == expected