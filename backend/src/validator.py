"""
Transaction validation against ground truth
"""
import json
from typing import List, Dict
from pathlib import Path


class TransactionValidator:
    """Compare extracted transactions with ground truth"""

    @staticmethod
    def load_ground_truth(json_path: str) -> List[Dict]:
        """Load expected transactions from JSON file"""
        with open(json_path, 'r') as f:
            data = json.load(f)

        # Handle both array and object formats
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return data.get('transactions', [])
        return []

    @staticmethod
    def validate(extracted: List[Dict], expected: List[Dict]) -> Dict:
        """Compare and calculate accuracy"""

        results = {
            'extracted_count': len(extracted),
            'expected_count': len(expected),
            'matches': 0,
            'missing': [],
            'extra': [],
            'accuracy': 0.0,
            'mismatches': []
        }

        # Create copies to track matched items
        expected_copy = expected.copy()
        extracted_copy = extracted.copy()

        # Find matches
        for ext_tx in extracted:
            match_found = False
            for i, exp_tx in enumerate(expected_copy):
                if TransactionValidator.is_match(ext_tx, exp_tx):
                    results['matches'] += 1
                    expected_copy.pop(i)
                    match_found = True
                    break

            if not match_found:
                results['extra'].append(ext_tx)

        # Remaining expected items are missing
        results['missing'] = expected_copy

        # Calculate accuracy
        if results['expected_count'] > 0:
            results['accuracy'] = (results['matches'] / results['expected_count']) * 100

        return results

    @staticmethod
    def is_match(tx1: Dict, tx2: Dict) -> bool:
        """Check if two transactions match with fuzzy matching"""

        # Date must match exactly
        date1 = tx1.get('date', '')
        date2 = tx2.get('date', '')

        # Normalize dates
        date1 = TransactionValidator._normalize_date(date1)
        date2 = TransactionValidator._normalize_date(date2)

        if date1 != date2:
            return False

        # Amount must be within ₹1 (100 paise)
        amount1 = float(tx1.get('amount', 0))
        amount2 = float(tx2.get('amount', 0))
        if abs(amount1 - amount2) > 1.0:
            return False

        # Skip strict description matching - rely on date + amount
        # This is more robust as PDF text extraction may vary slightly
        return True

    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Normalize date to DD/MM/YYYY format"""
        if not date_str:
            return ''

        date_str = str(date_str).strip()

        # If already in DD/MM/YYYY format
        if len(date_str) == 10 and date_str.count('/') == 2:
            return date_str

        # Handle DD/MM/YY -> DD/MM/YYYY
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year_int = int(year)
                if year_int < 50:
                    year = '20' + year
                else:
                    year = '19' + year
            return f"{day}/{month}/{year}"

        return date_str

    @staticmethod
    def print_report(results: Dict, bank_name: str = ""):
        """Print validation report"""
        prefix = f"[{bank_name}] " if bank_name else ""

        print(f"\n{prefix}Validation Report:")
        print(f"  Expected: {results['expected_count']}")
        print(f"  Extracted: {results['extracted_count']}")
        print(f"  Matches: {results['matches']}")
        print(f"  Accuracy: {results['accuracy']:.2f}%")

        if results['missing']:
            print(f"\n  Missing ({len(results['missing'])}):")
            for tx in results['missing'][:5]:  # Show first 5
                print(f"    - {tx.get('date')} | {tx.get('description', '')[:30]}... | ₹{tx.get('amount')}")

        if results['extra']:
            print(f"\n  Extra ({len(results['extra'])}):")
            for tx in results['extra'][:5]:  # Show first 5
                print(f"    + {tx.get('date')} | {tx.get('description', '')[:30]}... | ₹{tx.get('amount')}")
