"""
PURE TABLE EXTRACTION - NO REGEX ALLOWED
Extract tables from PDF using pdfplumber's table detection
"""
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber


class TableExtractor:
    """Extract tables from PDF using pdfplumber's table detection"""

    # Table extraction settings to try
    EXTRACTION_STRATEGIES: list[dict[str, Any]] = [
        {
            "name": "lines",
            "settings": {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 5,
                "join_tolerance": 5,
            }
        },
        {
            "name": "text",
            "settings": {
                "vertical_strategy": "text",
                "horizontal_strategy": "text",
                "snap_tolerance": 5,
            }
        },
        {
            "name": "lines_explicit",
            "settings": {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_tolerance": 3,
                "join_tolerance": 3,
                "snap_tolerance": 3,
            }
        },
    ]

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract_all_tables(self) -> list[pd.DataFrame]:
        """
        Extract ALL tables from PDF.
        Returns list of DataFrames, one per table found.
        """
        all_tables = []

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                page_tables = self._extract_page_tables(page, page_num)
                all_tables.extend(page_tables)

        return all_tables

    def _extract_page_tables(self, page: pdfplumber.page.Page, page_num: int) -> list[pd.DataFrame]:
        """Extract tables from a single page using multiple strategies"""

        dfs = []

        for strategy in self.EXTRACTION_STRATEGIES:
            tables = page.extract_tables(table_settings=strategy["settings"])

            for table in tables:
                if not table or len(table) < 1:
                    continue

                # Convert to DataFrame with first row as headers
                df = self._table_to_dataframe(table, page_num)

                if df is not None and not df.empty:
                    dfs.append(df)

        # Remove duplicates (same table detected by multiple strategies)
        return self._deduplicate_tables(dfs)

    def _table_to_dataframe(self, table: list[Any], page_num: int) -> pd.DataFrame | None:
        """Convert raw table data to DataFrame"""

        if not table or len(table) < 1:
            return None

        # Check if first row looks like headers
        first_row = table[0]

        # If first row has date-like values, it's probably data not headers
        has_date_in_first = any(self._looks_like_date(str(v)) for v in first_row if v)

        if has_date_in_first or len(table) == 1:
            # No headers - use generic column names
            headers = [f"col_{i}" for i in range(len(first_row))]
            data = table
        else:
            # First row as headers
            headers = [str(h).strip() if h else f"col_{i}" for i, h in enumerate(first_row)]
            data = table[1:]

        # Create DataFrame
        df = pd.DataFrame(data, columns=headers)

        # Add metadata
        df['_page'] = page_num

        return df

    def _deduplicate_tables(self, dfs: list[pd.DataFrame]) -> list[pd.DataFrame]:
        """Remove duplicate tables (same content, different strategies)"""

        if not dfs:
            return []

        unique = []
        seen_hashes = set()

        for df in dfs:
            # Create hash based on shape and first row content
            content_hash = hash((
                df.shape[0],
                df.shape[1],
                tuple(str(v) for v in df.iloc[0].values if pd.notna(v)) if len(df) > 0 else ()
            ))

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique.append(df)

        return unique

    def find_transaction_tables(self) -> list[pd.DataFrame]:
        """
        Find tables that look like transaction tables.
        A transaction table has date and amount columns.
        """
        all_tables = self.extract_all_tables()
        transaction_tables = []

        for df in all_tables:
            if self._is_transaction_table(df):
                transaction_tables.append(df)

        # Also try to merge single-row tables (ICICI style)
        merged = self._merge_single_row_tables(all_tables)
        if merged is not None and not merged.empty:
            if self._is_transaction_table(merged):
                transaction_tables.append(merged)

        return transaction_tables

    def _merge_single_row_tables(self, tables: list[pd.DataFrame]) -> pd.DataFrame | None:
        """
        Merge tables that have similar column structure.
        This handles cases like ICICI where each row is a separate table.
        """

        # Find tables with similar column counts
        col_counts: dict[int, list[pd.DataFrame]] = {}
        for df in tables:
            n_cols = len([c for c in df.columns if not c.startswith('_')])
            if n_cols not in col_counts:
                col_counts[n_cols] = []
            col_counts[n_cols].append(df)

        # Find groups of single-row tables with same column count
        for n_cols, dfs in col_counts.items():
            if len(dfs) >= 3 and n_cols >= 4:  # At least 3 tables with 4+ columns
                # Check if they look like transaction data
                all_have_date = all(
                    any(self._looks_like_date(str(v)) for v in df.iloc[0].values if pd.notna(v))
                    for df in dfs if len(df) > 0
                )

                if all_have_date:
                    # Merge them
                    merged = pd.concat(dfs, ignore_index=True)
                    return merged

        return None

    def _is_transaction_table(self, df: pd.DataFrame) -> bool:
        """Check if a table looks like a transaction table"""

        if df.empty or len(df.columns) < 2:
            return False

        # Check columns for transaction-like names
        col_names = ' '.join(str(c).lower() for c in df.columns)

        has_date = any(kw in col_names for kw in ['date', 'txn'])
        has_amount = any(kw in col_names for kw in ['amount', 'rs', 'debit', 'credit', 'dr', 'cr'])

        if has_date and has_amount:
            return True

        # Check if any column has date-like values
        for col in df.columns:
            if col.startswith('_'):
                continue

            date_count = 0
            for val in df[col].head(10):
                if val and self._looks_like_date(str(val)):
                    date_count += 1

            if date_count >= 2:  # At least 2 date-like values
                return True

        return False

    def _looks_like_date(self, value: str) -> bool:
        """Check if value looks like a date (NO REGEX - simple string check)"""

        value = str(value).strip()

        # Check for common separators
        if '/' in value or '-' in value:
            parts = value.replace('/', '-').replace(' ', '-').split('-')
            if len(parts) >= 2:
                try:
                    # Check if parts are numbers in date ranges
                    for part in parts[:2]:
                        num = int(part.strip())
                        if 1 <= num <= 31 or 1 <= num <= 12:
                            return True
                except ValueError:
                    pass

        # Check for "DD MMM YY" format (e.g., "04 Oct 25")
        parts = value.split()
        if len(parts) >= 3:
            try:
                int(parts[0])  # Day
                months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                         'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
                if parts[1].lower()[:3] in months:
                    return True
            except ValueError:
                pass

        return False

    def _looks_like_amount(self, value: str) -> bool:
        """Check if value looks like an amount (NO REGEX)"""

        value = str(value).strip()

        # Remove common amount characters
        cleaned = value
        for char in ['₹', ',', ' ', 'Rs', '.', 'Cr', 'Dr', 'INR']:
            cleaned = cleaned.replace(char, '')

        # Check if remaining is numeric
        try:
            float(cleaned)
            return True
        except ValueError:
            return False

    def debug_tables(self, output_dir: str = 'debug') -> None:
        """Save visual debug images showing detected tables"""

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                im = page.to_image(resolution=150)

                tables = page.find_tables()

                for _i, table in enumerate(tables):
                    # Draw outer boundary
                    im.draw_rect(table.bbox, stroke="red", stroke_width=2)

                    # Draw cells
                    for cell in table.cells:
                        im.draw_rect(cell, stroke="blue", stroke_width=1)

                    # Label
                    x, y = table.bbox[:2]

                output_path = f"{output_dir}/page_{page_num}.png"
                im.save(output_path)
                print(f"✅ Saved: {output_path} ({len(tables)} tables)")

        print(f"\n📁 Debug images saved to {output_dir}/")
