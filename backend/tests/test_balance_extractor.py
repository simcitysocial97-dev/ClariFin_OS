"""
Unit tests for balance extractor module.

These tests use text snippets only - no PDFs required.
Tests are deterministic and cover various bank statement formats.
"""

import pytest
from src.extraction.balance_extractor import (
    extract_opening_closing_from_text,
    extract_balance_from_text,
    _build_amount_pattern,
    _extract_amount_near_label,
)


class TestBuildAmountPattern:
    """Tests for the amount pattern builder."""

    def test_pattern_matches_indian_lakh(self):
        """Pattern should match Indian lakh format."""
        pattern = _build_amount_pattern()
        import re
        assert re.search(pattern, "1,23,456.78")
        assert re.search(pattern, "12,34,567.89")
        assert re.search(pattern, "1,23,45,678.90")

    def test_pattern_matches_standard(self):
        """Pattern should match standard thousands format."""
        pattern = _build_amount_pattern()
        import re
        assert re.search(pattern, "123,456.78")
        assert re.search(pattern, "9,382.00")
        assert re.search(pattern, "1,234,567.89")

    def test_pattern_matches_plain(self):
        """Pattern should match plain numbers."""
        pattern = _build_amount_pattern()
        import re
        assert re.search(pattern, "123456.78")
        assert re.search(pattern, "9382.00")

    def test_pattern_matches_with_currency(self):
        """Pattern should match numbers with currency symbols."""
        pattern = _build_amount_pattern()
        import re
        assert re.search(pattern, "₹1,234.56")
        assert re.search(pattern, "Rs. 5,000.00")
        assert re.search(pattern, "`9,382.00")

    def test_pattern_matches_with_cr_dr(self):
        """Pattern should match numbers with Cr/Dr suffixes."""
        pattern = _build_amount_pattern()
        import re
        assert re.search(pattern, "1,234.56 Cr")
        assert re.search(pattern, "5,000.00 Dr")
        assert re.search(pattern, "9382.00CR")


class TestExtractAmountNearLabel:
    """Tests for extracting amounts near labels."""

    def test_extract_near_simple_label(self):
        """Extract amount near a simple label."""
        text = "Opening Balance 9,382.00"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result == 938200  # 9,382.00 in paise

    def test_extract_with_colon(self):
        """Extract amount with colon separator."""
        text = "Opening Balance: 1,234.56"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result == 123456

    def test_extract_with_currency(self):
        """Extract amount with currency symbol."""
        text = "Opening Balance: ₹5,000.00"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result == 500000

    def test_extract_with_cr_suffix(self):
        """Extract amount with Cr (credit) suffix - should be negative."""
        text = "Opening Balance: 1,000.00 Cr"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result == -100000  # Negative for credit

    def test_extract_with_dr_suffix(self):
        """Extract amount with Dr (debit) suffix - should be positive."""
        text = "Opening Balance: 1,000.00 Dr"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result == 100000  # Positive for debit

    def test_no_match_returns_none(self):
        """Return None when no amount found."""
        text = "Opening Balance not available"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result is None

    def test_zero_amount_returns_none(self):
        """Zero amount should return None (conservative extraction)."""
        text = "Opening Balance 0.00"
        result = _extract_amount_near_label(text, r'Opening Balance')
        assert result is None


class TestHDFCFormats:
    """Tests for HDFC Bank statement formats."""

    def test_hdfc_opening_balance(self):
        """HDFC style opening balance."""
        text = """
        HDFC Bank Credit Card Statement
        Card No: 4321 23XX XXXX 1234
        Opening Balance 9,382.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 938200
        assert closing is None

    def test_hdfc_with_closing(self):
        """HDFC style with closing balance."""
        text = """
        Statement Period: 01/07/2025 - 31/07/2025
        Opening Balance: 5,000.00
        Closing Balance: 9,382.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 500000
        assert closing == 938200

    def test_hdfc_total_dues(self):
        """HDFC uses Total Dues as closing indicator."""
        text = """
        Payment Due Date    Total Dues    Minimum Amount Due
        21/05/2025         9,382.00      470.00
        """
        # This should not match as closing (it's total dues, not closing balance)
        opening, closing = extract_opening_closing_from_text(text)
        assert opening is None
        assert closing is None


class TestICICIFormats:
    """Tests for ICICI Bank statement formats."""

    def test_icici_previous_balance(self):
        """ICICI style Previous Balance (uses standard format)."""
        text = """
        ICICI Bank Credit Card Statement
        Previous Balance 1,23,456.78
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 12345678  # 1,23,456.78 in paise

    def test_icici_with_closing(self):
        """ICICI style opening and closing (standard format)."""
        text = """
        Statement Date: January 19, 2025
        Opening Balance: 5,000.00
        Closing Balance: 12,345.67
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 500000
        assert closing == 1234567


class TestSBIFormats:
    """Tests for SBI Card statement formats."""

    def test_sbi_previous_balance(self):
        """SBI uses Previous Balance."""
        text = """
        STATE BANK OF INDIA
        Credit Card Statement
        Previous Balance 5,000.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 500000

    def test_sbi_with_dr_suffix(self):
        """SBI with Dr suffix."""
        text = """
        Previous Balance 10,000.00 Dr
        Closing Balance  15,000.00 Dr
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 1000000  # Dr = positive
        assert closing == 1500000


class TestAxisFormats:
    """Tests for Axis Bank statement formats."""

    def test_axis_previous_balance(self):
        """Axis uses Previous Balance with Dr."""
        text = """
        Axis Bank Credit Card Statement
        Previous Balance 612.00 Dr
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 61200

    def test_axis_credit_balance(self):
        """Axis with Cr (credit) balance."""
        text = """
        Previous Balance 1,000.00 Cr
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == -100000  # Cr = negative


class TestIDFCFormats:
    """Tests for IDFC First Bank formats."""

    def test_idfc_opening_balance(self):
        """IDFC style Opening Balance."""
        text = """
        IDFC FIRST Bank
        Opening Balance 25,000.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 2500000


class TestIndusIndFormats:
    """Tests for IndusInd Bank formats."""

    def test_indusind_previous_balance(self):
        """IndusInd uses Previous Balance with DR."""
        text = """
        IndusInd Bank
        Previous Balance 8,500.00 DR
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 850000


class TestVariantLabels:
    """Tests for various label formats."""

    def test_op_bal_abbreviation(self):
        """Op Bal abbreviation."""
        text = "Op Bal 5,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 500000

    def test_op_bal_with_dots(self):
        """Op. Bal. with dots."""
        text = "Op. Bal. 5,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 500000

    def test_brought_forward(self):
        """Balance Brought Forward."""
        text = "Balance Brought Forward 10,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 1000000

    def test_brought_forward_short(self):
        """Brought Forward short form."""
        text = "Brought Forward 10,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 1000000

    def test_cl_bal_abbreviation(self):
        """Cl Bal abbreviation."""
        text = "Cl Bal 15,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert closing == 1500000

    def test_carried_forward(self):
        """Balance Carried Forward."""
        text = "Balance Carried Forward 20,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert closing == 2000000

    def test_ending_balance(self):
        """Ending Balance."""
        text = "Ending Balance 25,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert closing == 2500000


class TestNumberFormats:
    """Tests for various number formats."""

    def test_indian_lakh_format(self):
        """Indian lakh format: 1,23,456.78"""
        text = "Opening Balance 1,23,456.78"
        opening, _ = extract_opening_closing_from_text(text)
        assert opening == 12345678

    def test_standard_format(self):
        """Standard format: 123,456.78"""
        text = "Opening Balance 123,456.78"
        opening, _ = extract_opening_closing_from_text(text)
        assert opening == 12345678

    def test_small_amount(self):
        """Small amount: 123.45"""
        text = "Opening Balance 123.45"
        opening, _ = extract_opening_closing_from_text(text)
        assert opening == 12345

    def test_large_amount(self):
        """Large amount with crore format (1,00,00,000.00 = 1 crore)."""
        text = "Opening Balance 1,00,00,000.00"
        opening, _ = extract_opening_closing_from_text(text)
        assert opening == 1000000000  # 1 crore in paise


class TestNegativeCases:
    """Tests for cases where extraction should return None."""

    def test_empty_text(self):
        """Empty text should return None."""
        opening, closing = extract_opening_closing_from_text("")
        assert opening is None
        assert closing is None

    def test_none_text(self):
        """None text should return None."""
        opening, closing = extract_opening_closing_from_text(None)
        assert opening is None
        assert closing is None

    def test_random_text(self):
        """Random text without balance info."""
        text = "This is just some random text about groceries and shopping."
        opening, closing = extract_opening_closing_from_text(text)
        assert opening is None
        assert closing is None

    def test_numbers_without_labels(self):
        """Numbers without balance labels should not match."""
        text = "Transaction amounts: 1,234.56 and 5,678.90"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening is None
        assert closing is None

    def test_partial_label(self):
        """Partial label should not match."""
        text = "The balance is 1,000.00"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening is None
        assert closing is None

    def test_label_without_amount(self):
        """Label without valid amount."""
        text = "Opening Balance: not available"
        opening, closing = extract_opening_closing_from_text(text)
        assert opening is None
        assert closing is None


class TestBothBalances:
    """Tests for extracting both opening and closing balances."""

    def test_full_statement_snippet(self):
        """Realistic statement snippet with both balances."""
        text = """
        HDFC Bank Credit Card Statement
        Statement Date: 15/07/2025
        
        Opening Balance: 5,000.00
        
        Transactions:
        01/07 - Grocery Store - 1,500.00
        05/07 - Fuel Station - 2,882.00
        
        Closing Balance: 9,382.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 500000
        assert closing == 938200

    def test_multiline_format(self):
        """Multi-line statement format."""
        text = """
        Opening Balance
        10,000.00
        
        Closing Balance
        15,000.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 1000000
        assert closing == 1500000

    def test_tabular_format(self):
        """Tabular statement format."""
        text = """
        Description               Amount
        Opening Balance           8,500.00
        Total Debits             12,000.00
        Total Credits             5,000.00
        Closing Balance           5,500.00
        """
        opening, closing = extract_opening_closing_from_text(text)
        assert opening == 850000
        assert closing == 550000


class TestExtractBalanceFromText:
    """Tests for the specific extract_balance_from_text function."""

    def test_opening_explicit(self):
        """Explicitly request opening balance."""
        text = "Opening Balance: 1,000.00"
        result = extract_balance_from_text(text, 'opening')
        assert result == 100000

    def test_closing_explicit(self):
        """Explicitly request closing balance."""
        text = "Closing Balance: 2,000.00"
        result = extract_balance_from_text(text, 'closing')
        assert result == 200000

    def test_wrong_type_returns_none(self):
        """Requesting opening from text with only closing."""
        text = "Closing Balance: 2,000.00"
        result = extract_balance_from_text(text, 'opening')
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
