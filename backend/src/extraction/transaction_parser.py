"""
Parse transactions from table rows.
ONLY regex allowed: Date parsing (DD/MM/YYYY)
"""

import re  # ONLY for date validation
from typing import Any

import pandas as pd


class TransactionParser:
    """Convert table rows to transaction objects"""

    # ONLY regex: Validate date format - this is ALLOWED per requirements
    DATE_PATTERN = re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})")

    def __init__(self, column_mapping: dict[str, str], bank_name: str = "Unknown"):
        self.mapping = column_mapping
        self.bank_name = bank_name

    def parse_dataframe(self, df: pd.DataFrame) -> list[dict[str, Any]]:
        """Parse all rows in DataFrame"""
        transactions: list[dict[str, Any]] = []

        for _idx, row in df.iterrows():
            tx = self.parse_row(row)
            if tx:
                transactions.append(tx)

        return transactions

    def parse_row(self, row: pd.Series) -> dict[str, Any] | None:
        """Parse a single row into transaction dict"""

        # Get date
        date_col = self.mapping.get("date")
        if not date_col:
            return None

        date_val = str(row.get(date_col, "")).strip()
        date = self._parse_date(date_val)
        if not date:
            return None  # Skip rows without valid date

        # Get description
        desc_col = self.mapping.get("description")
        description = str(row.get(desc_col, "")).strip() if desc_col else ""

        # Get amount - try separate debit/credit columns first
        amount = 0.0
        tx_type = "debit"

        debit_col = self.mapping.get("debit")
        credit_col = self.mapping.get("credit")
        amount_col = self.mapping.get("amount")

        if debit_col and credit_col:
            # Separate columns
            debit_val = self._parse_amount(row.get(debit_col))
            credit_val = self._parse_amount(row.get(credit_col))

            if debit_val > 0:
                amount = debit_val
                tx_type = "debit"
            elif credit_val > 0:
                amount = credit_val
                tx_type = "credit"
        elif amount_col:
            # Single amount column
            amount = self._parse_amount(row.get(amount_col))

        if amount == 0:
            return None

        return {
            "date": date,
            "description": description,
            "amount_paise": int(amount * 100),
            "type": tx_type,
            "bank": self.bank_name,
            "category": "Uncategorized",
        }

    def _parse_date(self, value: str) -> str | None:
        """
        Parse date to DD/MM/YYYY format.
        Uses regex - this is the ONLY allowed regex per requirements.
        """
        if not value or value == "None":
            return None

        value = str(value).strip()

        match = self.DATE_PATTERN.search(value)
        if not match:
            return None

        day, month, year = match.groups()

        # Fix 2-digit year
        if len(year) == 2:
            year_int = int(year)
            if year_int < 50:
                year = "20" + year
            else:
                year = "19" + year

        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"

    def _parse_amount(self, value: Any) -> float:
        """
        Parse amount from cell value.
        NO REGEX - just clean and convert.
        """
        if pd.isna(value):
            return 0.0

        # Convert to string
        amount_str = str(value)

        # Remove common characters (NO REGEX - simple string operations)
        for char in ["₹", ",", " ", "Rs.", "Rs", "INR", "inr"]:
            amount_str = amount_str.replace(char, "")

        # Handle Cr/Dr suffix (NO REGEX)
        amount_str = amount_str.replace("Cr", "").replace("Dr", "")
        amount_str = amount_str.replace("cr", "").replace("dr", "")
        amount_str = amount_str.strip()

        # Handle negative
        amount_str = amount_str.replace("-", "")

        try:
            amount = float(amount_str)
            return abs(amount)
        except ValueError:
            return 0.0
