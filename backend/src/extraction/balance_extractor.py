"""
Balance Extractor
=================
Helper module for extracting opening and closing balances from bank statement text.

This module provides conservative, deterministic extraction of balance values
using regex patterns that support common statement formats and Indian number
notations.

Usage:
    from src.extraction.balance_extractor import extract_opening_closing_from_text

    opening_paise, closing_paise = extract_opening_closing_from_text(text)
    # Returns: (Optional[int], Optional[int]) - amounts in paise or None
"""

import re
from typing import Optional, Tuple

# Import the existing parse_amount_to_paise function
import sys
from pathlib import Path

# Add parent src directory to path for imports
src_path = Path(__file__).parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from utils import parse_amount_to_paise


# ============================================================
# Balance Label Patterns
# ============================================================
# These patterns match various ways banks label opening/closing balances

OPENING_BALANCE_LABELS = [
    r'Opening\s*Balance',
    r'Op\.?\s*Bal\.?',
    r'Balance\s*Brought\s*Forward',
    r'Brought\s*Forward',
    r'Previous\s*Balance',
    r'Prev\.?\s*Balance',
    r'Prev\.?\s*Bal\.?',
    r'Beginning\s*Balance',
    r'Starting\s*Balance',
    r'Opening',
]

CLOSING_BALANCE_LABELS = [
    r'Closing\s*Balance',
    r'Cl\.?\s*Bal\.?',
    r'Balance\s*Carried\s*Forward',
    r'Carried\s*Forward',
    r'Ending\s*Balance',
    r'Closing',
    r'End\s*Balance',
    r'Final\s*Balance',
]

# ============================================================
# Amount Patterns
# ============================================================
# These patterns match Indian and international number formats

# Indian lakh format: 1,23,456.78 or 1,23,45,678.90 (multiple groups)
INDIAN_LAKH_PATTERN = r'\d{1,2}(?:,\d{2})+(?:,\d{3})+\.\d{2}'

# Standard thousands format: 123,456.78 or 9,382.00
STANDARD_PATTERN = r'\d{1,3}(?:,\d{3})+\.\d{2}'

# Plain number with decimals: 123456.78
PLAIN_DECIMAL_PATTERN = r'\d{4,}\.\d{2}'

# Small amounts: 123.45
SMALL_AMOUNT_PATTERN = r'\d{1,3}\.\d{2}'

# Currency symbols and prefixes
# Note: ` is used by ICICI, r is used by IDFC First Bank
# The backtick ` needs to be handled specially as it's a regex metacharacter
CURRENCY_PREFIX = r"(?:₹|Rs\.?|INR|`|[\`\']?r\s*)\s*"

# Credit/Debit suffixes
CR_SUFFIX = r'\s*(?:Cr|CR|cr)\.?'
DR_SUFFIX = r'\s*(?:Dr|DR|dr)\.?'


def _build_amount_pattern() -> str:
    """
    Build a regex pattern that matches various amount formats.
    
    Returns a pattern that matches:
    - Indian lakh format: 1,23,456.78
    - Standard format: 123,456.78
    - Plain format: 123456.78
    - With/without currency symbols
    """
    # Combine all number patterns
    number_patterns = [
        INDIAN_LAKH_PATTERN,
        STANDARD_PATTERN,
        PLAIN_DECIMAL_PATTERN,
        SMALL_AMOUNT_PATTERN,
    ]
    number_part = f"(?:{'|'.join(number_patterns)})"
    
    # Optional currency prefix + number + optional Cr/Dr suffix
    pattern = f"(?:{CURRENCY_PREFIX})?({number_part})(?:{CR_SUFFIX}|{DR_SUFFIX})?"
    
    return pattern


def _extract_amount_near_label(text: str, label_pattern: str, max_distance: int = 100) -> Optional[int]:
    """
    Extract an amount value near a label pattern.
    
    Args:
        text: The text to search in
        label_pattern: Regex pattern for the label
        max_distance: Maximum characters to search after the label
        
    Returns:
        Amount in paise, or None if no valid amount found
    """
    amount_pattern = _build_amount_pattern()
    
    # Pattern: label followed by amount within max_distance chars
    # Allow for whitespace, colons, and other separators
    full_pattern = rf'{label_pattern}\s*:?\s*({amount_pattern})'
    
    # Search case-insensitively
    match = re.search(full_pattern, text, re.IGNORECASE)
    
    if match:
        amount_str = match.group(1)
        # Check if there's a Cr/Dr suffix in the full match
        full_match = match.group(0)
        
        # Parse the amount
        paise = parse_amount_to_paise(amount_str)
        
        # Handle Cr/Dr suffixes
        # Cr (Credit) = negative balance (bank owes customer)
        # Dr (Debit) = positive balance (customer owes bank)
        if re.search(CR_SUFFIX + r'$', full_match, re.IGNORECASE):
            paise = -abs(paise)
        elif re.search(DR_SUFFIX + r'$', full_match, re.IGNORECASE):
            paise = abs(paise)
        
        return paise if paise != 0 else None
    
    return None


def extract_balance_from_text(text: str, balance_type: str = 'opening') -> Optional[int]:
    """
    Extract a specific balance type from text.
    
    Args:
        text: The text to extract from
        balance_type: 'opening' or 'closing'
        
    Returns:
        Balance in paise, or None if not found
    """
    if not text:
        return None
    
    labels = OPENING_BALANCE_LABELS if balance_type == 'opening' else CLOSING_BALANCE_LABELS
    
    # Try each label pattern
    for label in labels:
        result = _extract_amount_near_label(text, label)
        if result is not None:
            return result
    
    return None


def extract_opening_closing_from_text(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract opening and closing balances from statement text.
    
    This is a conservative, deterministic extraction that only returns
    balances when confidence is high (clear label + valid number format).
    
    Args:
        text: Statement text (can be multi-line)
        
    Returns:
        Tuple of (opening_balance_paise, closing_balance_paise)
        Each value is either an integer (paise) or None if not found
        
    Examples:
        >>> text = "Opening Balance: ₹1,234.56\\nClosing Balance: ₹2,345.67"
        >>> extract_opening_closing_from_text(text)
        (123456, 234567)
        
        >>> text = "Op Bal 9,382.00 Cr"
        >>> extract_opening_closing_from_text(text)
        (-938200, None)
        
        >>> text = "Some random text"
        >>> extract_opening_closing_from_text(text)
        (None, None)
    """
    if not text or not isinstance(text, str):
        return (None, None)
    
    opening = extract_balance_from_text(text, 'opening')
    closing = extract_balance_from_text(text, 'closing')
    
    return (opening, closing)


# ============================================================
# Convenience Functions for Legacy Extractor Integration
# ============================================================

def extract_opening_balance_from_text(text: str) -> Optional[int]:
    """Extract opening balance from text. Returns paise or None."""
    return extract_balance_from_text(text, 'opening')


def extract_closing_balance_from_text(text: str) -> Optional[int]:
    """Extract closing balance from text. Returns paise or None."""
    return extract_balance_from_text(text, 'closing')
