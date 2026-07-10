"""
metadata_extractor.py
=====================
Proximity-based metadata extractor for Indian credit card statements.
Ported from metadata-proximity.js (100% accuracy on 6 banks).

Architecture:
  1. Extract text from first 3 pages via pdfplumber
  2. For each metadata field, try bank-specific directPattern first
  3. If no directPattern or no match, use proximity search:
     find label text, then search for value within maxDistance chars
  4. Parse currency values (Indian format: 1,23,456.78)
  5. Calculate bill cycle from statement date

Supports: HDFC, ICICI, Axis, SBI, IDFC First, IndusInd
"""

import json
import re
import sys
from datetime import datetime, timedelta
from typing import Any

import pdfplumber

# ============================================================
# Core Proximity Helpers (ported from JS)
# ============================================================

def extract_currency(text: str) -> float | None:
    """
    Extract first currency value from text.
    Handles Indian lakh format (1,23,456.78) and standard format.
    Returns NEGATIVE value for credit balances (Cr suffix).
    Ported exactly from JS extractCurrency().
    """
    # Check for Cr/Dr suffix first to determine sign
    cr_pattern = r'([\d,]+\.\d{2})\s*Cr'
    dr_pattern = r'([\d,]+\.\d{2})\s*Dr'

    cr_match = re.search(cr_pattern, text, re.IGNORECASE)
    if cr_match:
        try:
            # Credit balance = negative (bank owes customer)
            return -float(cr_match.group(1).replace(',', ''))
        except (ValueError, TypeError):
            pass

    dr_match = re.search(dr_pattern, text, re.IGNORECASE)
    if dr_match:
        try:
            # Debit balance = positive (customer owes bank)
            return float(dr_match.group(1).replace(',', ''))
        except (ValueError, TypeError):
            pass

    patterns = [
        r'(\d{1,2},\d{2},\d{3}\.\d{2})',           # Indian lakh: 1,23,456.78
        r'(\d{1,3}(?:,\d{3})+\.\d{2})',             # Standard: 123,456.78
        r'(\d{4,}\.\d{2})',                          # Plain large: 12345.78
        r'(?:₹|Rs\.?|`)\s*([\d,]+\.\d{2})',          # With symbol: ₹1,234.56
        r'(\d{3,}(?:,\d{3})*\.\d{2})',              # 3+ digits with commas
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1) if match.group(1) else match.group(0)
            try:
                return float(value.replace(',', ''))
            except (ValueError, TypeError):
                continue
    return None


def extract_date(text: str) -> str | None:
    """
    Extract first date from text.
    Ported exactly from JS extractDate().
    """
    patterns = [
        r'(\d{2}/\d{2}/\d{4})',                     # DD/MM/YYYY
        r'(\d{2}-\d{2}-\d{4})',                      # DD-MM-YYYY
        r'(\d{2}/\w{3}/\d{4})',                      # DD/Mon/YYYY
        r'(\d{2}\s+\w{3}\s+\d{2,4})',               # DD Mon YY(YY)
        r'(\w+\s+\d{1,2},?\s+\d{4})',               # Month DD, YYYY
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def standardize_date(date_str: str) -> str | None:
    """
    Convert any date format to standardized DD/MM/YYYY.
    Handles all formats extracted from Indian bank statements.
    """
    if not date_str:
        return None

    months3 = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    months_full = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    parsed_date = None

    # Try DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'(\d{2})[/\-](\d{2})[/\-](\d{4})', date_str)
    if m:
        try:
            parsed_date = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # Try DD/Mon/YYYY (e.g., 03/Sep/2025)
    if not parsed_date:
        m = re.match(r'(\d{2})/(\w{3})/(\d{4})', date_str)
        if m and m.group(2) in months3:
            try:
                parsed_date = datetime(int(m.group(3)), months3[m.group(2)], int(m.group(1)))
            except ValueError:
                pass

    # Try DD Mon YYYY (e.g., 06 Nov 2025)
    if not parsed_date:
        m = re.match(r'(\d{1,2})\s+(\w{3})\s+(\d{4})', date_str)
        if m and m.group(2) in months3:
            try:
                parsed_date = datetime(int(m.group(3)), months3[m.group(2)], int(m.group(1)))
            except ValueError:
                pass

    # Try Month DD, YYYY (e.g., January 19, 2025)
    if not parsed_date:
        m = re.match(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', date_str)
        if m and m.group(1) in months_full:
            try:
                parsed_date = datetime(int(m.group(3)), months_full[m.group(1)], int(m.group(2)))
            except ValueError:
                pass

    if parsed_date:
        return parsed_date.strftime('%d/%m/%Y')

    return date_str  # Return as-is if parsing failed


def format_currency(amount: float) -> str:
    """
    Format currency with ₹ symbol and 2 decimal places.
    Returns '-' for None values.
    """
    if amount is None:
        return '-'
    sign = '-' if amount < 0 else ''
    return f"{sign}₹{abs(amount):,.2f}"


def extract_card_number(text: str) -> str | None:
    """
    Extract masked card number from text.
    Ported exactly from JS extractCardNumber().
    """
    patterns = [
        r'(\d{4}\s*\d{2}XX\s*XXXX\s*\d{4})',       # 4321 23XX XXXX 1234
        r'(\d{6}\*+\d{4})',                          # 432123****1234
        r'(XXXX\s*XXXX\s*XXXX\s*XX\d{2})',          # XXXX XXXX XXXX XX34
        r'(\d{4}X{8}\d{4})',                         # 4321XXXXXXXX1234
        r'(\d{4}X{4,}\d+)',                          # 4321XXXX1234
        r'(XX\d{4})',                                # XX1234
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def find_value_near(text: str, label: str, value_type: str = 'currency',
                    max_distance: int = 200) -> Any | None:
    """
    Find a value near a label in text (proximity search).
    Ported exactly from JS findValueNear().

    1. Find the label in text
    2. Take the substring after the label (up to max_distance chars)
    3. Extract value of the specified type from that substring
    """
    # Escape the label for regex
    escaped_label = re.escape(label)
    match = re.search(escaped_label, text, re.IGNORECASE)

    if not match:
        return None

    start_pos = match.end()
    search_area = text[start_pos:start_pos + max_distance]

    if value_type == 'currency':
        return extract_currency(search_area)
    elif value_type == 'date':
        return extract_date(search_area)
    elif value_type == 'cardNumber':
        return extract_card_number(search_area)

    return None


def calculate_bill_cycle(statement_date: str) -> dict[str, str | None]:
    """
    Calculate billing cycle (30 days ending on statement date).
    Ported exactly from JS calculateBillCycle().
    """
    if not statement_date:
        return {'bill_cycle_start': None, 'bill_cycle_end': None}

    months3 = {
        'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
    }
    months_full = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4,
        'May': 5, 'June': 6, 'July': 7, 'August': 8,
        'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    end_date = None

    # Try DD/MM/YYYY or DD-MM-YYYY
    m = re.match(r'(\d{2})[/\-](\d{2})[/\-](\d{4})', statement_date)
    if m:
        try:
            end_date = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # Try DD Mon YY(YY)
    if not end_date:
        m = re.match(r'(\d{2})\s+(\w{3})\s+(\d{2,4})', statement_date)
        if m and m.group(2) in months3:
            year_str = m.group(3)
            year = int('20' + year_str) if len(year_str) == 2 else int(year_str)
            try:
                end_date = datetime(year, months3[m.group(2)], int(m.group(1)))
            except ValueError:
                pass

    # Try DD/Mon/YYYY
    if not end_date:
        m = re.match(r'(\d{2})/(\w{3})/(\d{4})', statement_date)
        if m and m.group(2) in months3:
            try:
                end_date = datetime(int(m.group(3)), months3[m.group(2)], int(m.group(1)))
            except ValueError:
                pass

    # Try Month DD, YYYY
    if not end_date:
        m = re.match(r'(\w+)\s+(\d{1,2}),?\s+(\d{4})', statement_date)
        if m and m.group(1) in months_full:
            try:
                end_date = datetime(int(m.group(3)), months_full[m.group(1)], int(m.group(2)))
            except ValueError:
                pass

    if not end_date:
        return {'bill_cycle_start': None, 'bill_cycle_end': None}

    start_date = end_date - timedelta(days=29)

    def fmt(d: datetime) -> str:
        return d.strftime('%d/%m/%Y')

    return {
        'bill_cycle_start': fmt(start_date),
        'bill_cycle_end': fmt(end_date),
    }


# ============================================================
# Bank-Specific Configurations
# ============================================================
# Each field config is a dict with:
#   direct_pattern: compiled regex (tried first)
#   extract_index: which group to extract (default 1)
#   labels: list[Any] of label strings for proximity search (fallback)
#   value_type: 'currency' | 'date' | 'cardNumber'
#   distance: max chars for proximity search
#   transform: optional callable to transform the extracted string
#   search_after: optional string — start searching only after this marker
#
# Pattern porting notes:
#   - JS `[\s\S]*?` → Python `[\s\S]*?` (identical, crosses newlines)
#   - ICICI uses backtick ` as rupee symbol in PDF text
#   - IndusInd has `\n` in patterns — actual newline in extracted text
# ============================================================

BANK_CONFIGS: dict[str, dict[str, Any]] = {

    'HDFC Bank': {
        'card_number': {
            'labels': ['Card No:'],
            'value_type': 'cardNumber',
            'distance': 50,
        },
        'total_amount_due': {
            # HDFC has header on one line, values on next line after some text
            # "Payment Due Date Total Dues Minimum Amount Due" ... "21/05/2025 9,382.00 470.00"
            'direct_pattern': re.compile(
                r'Payment Due Date\s+Total Dues\s+Minimum Amount Due[\s\S]*?'
                r'(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
            'extract_index': 2,
        },
        'minimum_amount_due': {
            'direct_pattern': re.compile(
                r'Payment Due Date\s+Total Dues\s+Minimum Amount Due[\s\S]*?'
                r'(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
            'extract_index': 3,
        },
        'due_date': {
            'direct_pattern': re.compile(
                r'Payment Due Date\s+Total Dues\s+Minimum Amount Due[\s\S]*?'
                r'(\d{2}/\d{2}/\d{4})\s+[\d,]+\.\d{2}',
                re.IGNORECASE
            ),
        },
        'credit_limit': {
            'direct_pattern': re.compile(
                r'Credit Limit\s+Available Credit Limit\s+Available Cash Limit\s+'
                r'([\d,]+)',
                re.IGNORECASE
            ),
        },
        'opening_balance': {
            'direct_pattern': re.compile(
                r'Opening\s*Balance[\s\S]*?([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'bill_cycle': {
            'pattern': re.compile(
                r'Statement Date[:\s]+(\d{2}/\d{2}/\d{4})',
                re.IGNORECASE
            ),
        },
    },

    'Axis Bank': {
        'card_number': {
            'direct_pattern': re.compile(r'(\d{6}\*+\d{4})'),
        },
        'total_amount_due': {
            # Axis: "Total Payment Due Minimum Payment Due Statement Period Payment Due Date Statement Generation Date"
            # then: "612.00 Cr 0.00 Cr 17/03/2025 - 15/04/2025 05/05/2025 15/04/2025"
            # Capture amount with Cr/Dr suffix - extract_currency() handles the sign
            'direct_pattern': re.compile(
                r'Total Payment Due\s+Minimum Payment Due[\s\S]*?'
                r'([\d,]+\.\d{2}\s*(?:Cr|Dr))\s+([\d,]+\.\d{2}\s*(?:Cr|Dr))',
                re.IGNORECASE
            ),
            'extract_index': 1,
        },
        'minimum_amount_due': {
            'direct_pattern': re.compile(
                r'Total Payment Due\s+Minimum Payment Due[\s\S]*?'
                r'([\d,]+\.\d{2}\s*(?:Cr|Dr))\s+([\d,]+\.\d{2}\s*(?:Cr|Dr))',
                re.IGNORECASE
            ),
            'extract_index': 2,
        },
        'due_date': {
            # Due date is the 3rd date in the payment summary line
            'direct_pattern': re.compile(
                r'Total Payment Due\s+Minimum Payment Due[\s\S]*?'
                r'\d{2}/\d{2}/\d{4}\s*-\s*\d{2}/\d{2}/\d{4}\s+(\d{2}/\d{2}/\d{4})',
                re.IGNORECASE
            ),
        },
        'credit_limit': {
            'direct_pattern': re.compile(
                r'Credit Limit[\s\S]*?([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'opening_balance': {
            'direct_pattern': re.compile(
                r'Previous Balance[\s\S]*?([\d,]+\.\d{2})\s+Dr',
                re.IGNORECASE
            ),
        },
        'bill_cycle': {
            'pattern': re.compile(
                r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})'
            ),
        },
    },

    'ICICI Bank': {
        'card_number': {
            'direct_pattern': re.compile(r'(\d{4}X{4,}\d+)', re.IGNORECASE),
        },
        'total_amount_due': {
            # ICICI uses backtick ` as rupee symbol in PDF text
            # Anchor to "Total Amount due" label to get correct value
            'direct_pattern': re.compile(
                r'Total Amount due[\s\S]*?`\s*([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'minimum_amount_due': {
            # Anchor to "Minimum Amount due" label to get correct value
            'direct_pattern': re.compile(
                r'Minimum Amount due[\s\S]*?`\s*([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'due_date': {
            'direct_pattern': re.compile(
                r'PAYMENT DUE DATE[\s\S]*?(\w+\s+\d{1,2},\s*\d{4})',
                re.IGNORECASE
            ),
        },
        'credit_limit': {
            'direct_pattern': re.compile(
                r'Credit Limit[\s\S]*?`\s*(\d{1,2},\d{2},\d{3}\.\d{2})',
                re.IGNORECASE
            ),
        },
        'opening_balance': {
            'direct_pattern': re.compile(
                r'Previous Balance[\s\S]*?`\s*([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'bill_cycle': {
            'pattern': re.compile(
                r'STATEMENT DATE[\s\S]*?(\w+\s+\d{1,2},\s*\d{4})',
                re.IGNORECASE
            ),
        },
    },

    'SBI Card': {
        'card_number': {
            'direct_pattern': re.compile(
                r'XXXX XXXX XXXX XX(\d{2})',
                re.IGNORECASE
            ),
            'transform': lambda m: 'XXXX XXXX XXXX XX' + m,
        },
        'total_amount_due': {
            # SBI: "*Total Amount Due ( ` )" on one line, value on next line
            'direct_pattern': re.compile(
                r'\*Total Amount Due[\s\S]*?([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'minimum_amount_due': {
            # SBI: "**Minimum Amount Due( ` )" then CKYC line with value
            'direct_pattern': re.compile(
                r'CKYC No[\s\S]*?:\s*\d+\s+([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'due_date': {
            # SBI: "Payment Due Date" on one line, date on next line
            'direct_pattern': re.compile(
                r'Payment Due Date[\s\S]*?(\d{1,2}\s+\w{3}\s+\d{4})',
                re.IGNORECASE
            ),
        },
        'credit_limit': {
            'direct_pattern': re.compile(
                r'Credit Limit[\s\S]*?([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'opening_balance': {
            'direct_pattern': re.compile(
                r'Previous Balance[\s\S]*?([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'bill_cycle': {
            'pattern': re.compile(
                r'for Statement Period:\s*(\d{1,2}\s+\w{3}\s+\d{2})\s+to\s+'
                r'(\d{1,2}\s+\w{3}\s+\d{2})',
                re.IGNORECASE
            ),
        },
    },

    'IDFC First Bank': {
        'card_number': {
            'direct_pattern': re.compile(
                r'FIRST\s+\w+\+?\s+(XX\d{4})',
                re.IGNORECASE
            ),
        },
        'total_amount_due': {
            'direct_pattern': re.compile(
                r'Total Amount Due[\s\S]*?r\s*([\d,]+\.\d{2})\s*DR',
                re.IGNORECASE
            ),
        },
        'minimum_amount_due': {
            'direct_pattern': re.compile(
                r'Minimum Amount Due[\s\S]*?r\s*([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'due_date': {
            'direct_pattern': re.compile(
                r'Payment Due Date[\s\S]*?(\d{2}/\w{3}/\d{4})',
                re.IGNORECASE
            ),
        },
        'credit_limit': {
            'direct_pattern': re.compile(
                r'Credit Limit[\s\S]*?r\s*([\d,]+)',
                re.IGNORECASE
            ),
        },
        'opening_balance': {
            'direct_pattern': re.compile(
                r'Opening Balance[\s\S]*?r\s*([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'bill_cycle': {
            'pattern': re.compile(
                r'(\d{2}/\w{3}/\d{4})\s*-\s*(\d{2}/\w{3}/\d{4})',
                re.IGNORECASE
            ),
        },
    },

    'IndusInd Bank': {
        'card_number': {
            'direct_pattern': re.compile(r'(\d{4}X{8}\d{4})'),
        },
        'total_amount_due': {
            # IndusInd: "Total Amount Due" on one line, value on next line with DR suffix
            'direct_pattern': re.compile(
                r'Total Amount Due[\s\S]*?([\d,]+\.\d{2})\s*DR',
                re.IGNORECASE
            ),
        },
        'minimum_amount_due': {
            # IndusInd: "Minimum Amount Due" on one line, value on next line
            'direct_pattern': re.compile(
                r'Minimum Amount Due[\s\S]*?([\d,]+\.\d{2})',
                re.IGNORECASE
            ),
        },
        'due_date': {
            # IndusInd: "Payment Due Date" on one line, date on next line
            'direct_pattern': re.compile(
                r'Payment Due Date[\s\S]*?(\d{2}/\d{2}/\d{4})',
                re.IGNORECASE
            ),
        },
        'credit_limit': {
            'direct_pattern': re.compile(
                r'Credit Limit[\s\S]*?([\d,]+)',
                re.IGNORECASE
            ),
        },
        'opening_balance': {
            'direct_pattern': re.compile(
                r'Previous Balance[\s\S]*?([\d,]+\.\d{2})\s*DR',
                re.IGNORECASE
            ),
        },
        'bill_cycle': {
            'pattern': re.compile(
                r'(\d{2}/\d{2}/\d{4})\s*To\s*(\d{2}/\d{2}/\d{4})',
                re.IGNORECASE
            ),
        },
    },
}

# Fields that should be parsed as float
_NUMERIC_FIELDS = {
    'total_amount_due', 'minimum_amount_due',
    'opening_balance', 'credit_limit',
}


# ============================================================
# MetadataExtractor Class
# ============================================================

class MetadataExtractor:
    """
    Extract statement metadata using bank-specific patterns with
    proximity fallback. Ported from metadata-proximity.js.
    """

    def __init__(self, pdf_path: str, bank: str = 'Unknown', debug: bool = False):
        self.pdf_path = pdf_path
        self.bank = bank
        self.debug = debug
        self._full_text: str = ''
        self._page_texts: list[str] = []

    def _log(self, msg: str) -> None:
        if self.debug:
            print(f'[MetadataExtractor] {msg}')

    def _load_text(self, max_pages: int = 3) -> None:
        """Extract text from first N pages."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages[:max_pages]):
                    text = page.extract_text() or ''
                    self._page_texts.append(text)
                    self._log(f'Page {i}: {len(text)} chars')
                self._full_text = '\n'.join(self._page_texts)
        except Exception as e:
            self._log(f'Error loading text: {e}')

    def _extract_field(self, field_name: str, field_config: dict[str, Any]) -> Any | None:
        """
        Extract a single metadata field.
        Strategy (mirrors JS exactly):
          1. Try directPattern regex on full text
          2. If no directPattern or no match, try proximity search using labels
        """
        value = None
        text = self._full_text

        # If search_after is specified, only search text after that marker
        search_after = field_config.get('search_after')
        if search_after:
            idx = text.find(search_after)
            if idx >= 0:
                text = text[idx:]

        # Strategy 1: directPattern
        direct = field_config.get('direct_pattern')
        if direct:
            match = direct.search(text)
            if match:
                extract_idx = field_config.get('extract_index', 1)

                try:
                    extracted = match.group(extract_idx)
                except IndexError:
                    extracted = match.group(1) if match.lastindex >= 1 else match.group(0)

                if extracted:
                    # Apply transform if specified
                    transform = field_config.get('transform')
                    if transform and callable(transform):
                        extracted = transform(extracted)

                    # Parse numeric fields using extract_currency (handles Cr/Dr globally)
                    if field_name in _NUMERIC_FIELDS:
                        value = extract_currency(extracted)
                    else:
                        value = extracted

                    self._log(f'  {field_name}: directPattern matched → {value}')
                    return value

        # Strategy 2: Proximity search using labels
        labels = field_config.get('labels', [])
        value_type = field_config.get('value_type', 'currency')
        distance = field_config.get('distance', 200)

        for label in labels:
            result = find_value_near(self._full_text, label, value_type, distance)
            if result is not None:
                self._log(f'  {field_name}: proximity matched (label={label!r}) → {result}')
                return result

        self._log(f'  {field_name}: no match found')
        return None

    def extract(self) -> dict[str, Any]:
        """
        Extract all metadata fields for the detected bank.
        Returns dict matching the JS output structure:
        {
            bank_name, card_number, total_amount_due, minimum_amount_due,
            due_date, credit_limit, opening_balance,
            bill_cycle_start, bill_cycle_end,
            statement_date, card_last4,
            raw: {original string values}
        }
        """
        self._load_text()

        config = BANK_CONFIGS.get(self.bank)
        if not config:
            self._log(f'No config for bank: {self.bank}')
            # Try all banks' patterns as fallback
            for bank_name, bank_config in BANK_CONFIGS.items():
                self._log(f'Trying {bank_name} patterns as fallback...')
                test_total = self._extract_field('total_amount_due',
                    bank_config.get('total_amount_due', {}))
                if test_total is not None and test_total > 0:
                    self._log(f'Fallback match on {bank_name}!')
                    config = bank_config
                    break
            if not config:
                return self._empty_result()

        result: dict[str, Any] = {
            'bank_name': self.bank,
            'card_number': None,
            'total_amount_due': None,
            'minimum_amount_due': None,
            'due_date': None,
            'credit_limit': None,
            'opening_balance': None,
            'bill_cycle_start': None,
            'bill_cycle_end': None,
            'statement_date': None,
            'card_last4': None,
            'raw': {},
        }

        # Extract each field
        for field_name, field_config in config.items():
            if field_name == 'bill_cycle':
                # Special handling: bill cycle extraction
                pattern = field_config.get('pattern')
                if pattern:
                    match = pattern.search(self._full_text)
                    if match:
                        if match.lastindex and match.lastindex >= 2:
                            # Pattern captured both start and end
                            result['bill_cycle_start'] = match.group(1)
                            result['bill_cycle_end'] = match.group(2)
                            result['statement_date'] = match.group(2)
                            self._log(f'  bill_cycle: {match.group(1)} to {match.group(2)}')
                        else:
                            # Only statement date captured, calculate cycle
                            stmt_date = match.group(1)
                            result['statement_date'] = stmt_date
                            cycle = calculate_bill_cycle(stmt_date)
                            result['bill_cycle_start'] = cycle['bill_cycle_start']
                            result['bill_cycle_end'] = cycle['bill_cycle_end']
                            self._log(f'  bill_cycle: calculated from {stmt_date}')
                continue

            value = self._extract_field(field_name, field_config)
            if value is not None:
                # Map field names to result dict keys
                key_map = {
                    'card_number': 'card_number',
                    'total_amount_due': 'total_amount_due',
                    'minimum_amount_due': 'minimum_amount_due',
                    'due_date': 'due_date',
                    'credit_limit': 'credit_limit',
                    'opening_balance': 'opening_balance',
                }
                result_key = key_map.get(field_name, field_name)
                result[result_key] = value
                result['raw'][field_name] = str(value)

        # Derive card_last4 from card_number
        if result['card_number']:
            cn = str(result['card_number']).replace(' ', '')
            # Extract last 4 digits
            digits = ''.join(c for c in cn if c.isdigit())
            if len(digits) >= 4:
                result['card_last4'] = digits[-4:]
            elif cn:
                # For formats like XX1234
                last_digits = re.findall(r'\d+', cn)
                if last_digits:
                    result['card_last4'] = last_digits[-1][-4:]

        # Standardize due_date to DD/MM/YYYY format
        if result['due_date']:
            result['due_date'] = standardize_date(str(result['due_date']))

        self._log(f'Final result: total_due={result["total_amount_due"]}, '
                  f'min_due={result["minimum_amount_due"]}, '
                  f'due_date={result["due_date"]}, '
                  f'card={result["card_number"]}')

        return result

    def _empty_result(self) -> dict[str, Any]:
        return {
            'bank_name': self.bank,
            'card_number': None,
            'total_amount_due': None,
            'minimum_amount_due': None,
            'due_date': None,
            'credit_limit': None,
            'opening_balance': None,
            'bill_cycle_start': None,
            'bill_cycle_end': None,
            'statement_date': None,
            'card_last4': None,
            'raw': {},
        }


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python metadata_extractor.py <pdf_path> [bank_name] [--debug]')
        print('Example: python metadata_extractor.py hdfc_Apr.pdf "HDFC Bank" --debug')
        sys.exit(1)

    pdf_path = sys.argv[1]
    bank = 'Unknown'
    debug = '--debug' in sys.argv

    # Find bank name argument (not --debug, not pdf path)
    for arg in sys.argv[2:]:
        if not arg.startswith('--'):
            bank = arg
            break

    # If bank is Unknown, try to detect from PDF
    if bank == 'Unknown':
        try:
            from src.statement_extractor import StatementExtractor
            se = StatementExtractor(pdf_path)
            bank = se.detect_bank()
            if debug:
                print(f'Auto-detected bank: {bank}')
        except Exception:
            pass

    extractor = MetadataExtractor(pdf_path, bank=bank, debug=debug)
    result = extractor.extract()
    print(json.dumps(result, indent=2, default=str))
