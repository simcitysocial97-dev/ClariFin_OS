#!/usr/bin/env python3
"""
PDF Extraction Test Runner
==========================

Tests the PDF extraction pipeline against known test files
to verify extraction accuracy before importing real statements.

Usage:
    python scripts/test_extraction.py

Tests:
- Extracts transactions from all PDFs in data/test/statements/
- Compares against expected JSON in data/test/expected/
- Reports count matches and amount accuracy
"""

import json
import sys
import os
from pathlib import Path

# Add backend/src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from extraction.factory import get_extractor

def test_extraction():
    """Test extraction pipeline against all test files."""
    print("🧪 Testing PDF Extraction Pipeline")
    print("=" * 50)

    # Directories
    STATEMENTS_DIR = Path(__file__).parent.parent / 'data' / 'test' / 'statements'
    EXPECTED_DIR = Path(__file__).parent.parent / 'data' / 'test' / 'expected'

    # Get extractor
    extractor = get_extractor()
    print(f"🔧 Using {extractor.name} extractor")

    # Find all PDF files
    pdf_files = list(STATEMENTS_DIR.glob('*.pdf'))
    print(f"📁 Found {len(pdf_files)} PDF test files")

    results = []

    for pdf_file in pdf_files:
        pdf_path = str(pdf_file)
        base_name = pdf_file.stem
        expected_path = EXPECTED_DIR / f"{base_name}.json"

        if not expected_path.exists():
            print(f"⚠️  No expected file for {pdf_file.name}")
            continue

        # Load expected data
        with open(expected_path) as f:
            expected_data = json.load(f)

        # Extract from PDF
        try:
            print(f"📄 Processing {pdf_file.name}...", end=" ")
            result = extractor.extract(pdf_path)

            # Count transactions
            expected_count = len(expected_data)
            extracted_count = len(result.normalized_rows)

            # Check count match
            count_match = extracted_count == expected_count

            # Check first few amounts if counts match
            amount_mismatches = []
            if count_match and extracted_count > 0:
                for i, (exp, ext) in enumerate(zip(expected_data[:5],
                                                  result.normalized_rows[:5])):
                    exp_amt = float(exp.get('amount', exp.get('amount_inr', 0)))
                    ext_amt = float(ext.get('amount', ext.get('amount_inr', 0)))
                    if abs(exp_amt - ext_amt) > 0.01:
                        amount_mismatches.append(
                            f"Row {i}: expected {exp_amt}, got {ext_amt}")

            results.append({
                'file': pdf_file.name,
                'expected_count': expected_count,
                'extracted_count': extracted_count,
                'count_match': count_match,
                'amount_mismatches': amount_mismatches,
                'status': '✅' if count_match and not amount_mismatches else '❌'
            })

            status_emoji = '✅' if count_match else '❌'
            print(f"{status_emoji} {extracted_count}/{expected_count} transactions")

            if amount_mismatches:
                print(f"   ⚠️  Amount mismatches: {amount_mismatches}")

        except Exception as e:
            results.append({
                'file': pdf_file.name,
                'status': '❌ ERROR',
                'error': str(e)
            })
            print(f"❌ ERROR: {e}")

    # Summary
    print(f"\n{'='*50}")
    passed = sum(1 for r in results if r['status'] == '✅')
    total = len(results)
    print(f"📊 RESULTS: {passed}/{total} tests passing")

    if passed == total:
        print("🎉 All PDFs extracted correctly!")
    else:
        print("❌ Some PDFs failed extraction")

    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    for result in results:
        status_emoji = result['status']
        print(f"  {status_emoji} {result['file']}: {result['extracted_count']}/{result['expected_count']} transactions")

    return results

if __name__ == "__main__":
    test_extraction()