"""
Main entry point - orchestrates table extraction and parsing
PURE TABLE EXTRACTION - NO REGEX FOR TRANSACTION MATCHING
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


from column_mapper import ColumnMapper
from table_extractor import TableExtractor
from transaction_parser import TransactionParser


def extract_transactions(pdf_path: str, bank_name: str = None) -> list[dict]:
    """
    Extract transactions from bank statement PDF.
    Uses PURE TABLE EXTRACTION - no regex patterns for transaction matching.
    """

    print(f"\n{'='*70}")
    print(f"Extracting: {Path(pdf_path).name}")
    print(f"Bank: {bank_name or 'Auto-detect'}")
    print(f"{'='*70}")

    # Step 1: Extract all tables from PDF
    extractor = TableExtractor(pdf_path)

    # Find transaction tables specifically
    print("\n📊 Finding transaction tables...")
    transaction_tables = extractor.find_transaction_tables()

    if not transaction_tables:
        print("⚠️ No transaction tables found with auto-detection")
        print("📊 Trying all tables...")
        all_tables = extractor.extract_all_tables()
        print(f"Found {len(all_tables)} total tables")

        # Show table info for debugging
        for i, df in enumerate(all_tables):
            print(f"\n  Table {i+1}: {len(df)} rows x {len(df.columns)} cols")
            print(f"  Columns: {list(df.columns)[:5]}...")

        return []

    print(f"✅ Found {len(transaction_tables)} transaction tables")

    all_transactions = []
    mapper = ColumnMapper()

    for i, df in enumerate(transaction_tables):
        print(f"\n--- Processing Table {i+1} ---")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")

        # Step 2: Map columns to standard fields
        column_map = mapper.map_columns(list(df.columns))
        print(f"  Mapping: {column_map}")

        if not mapper.has_required_fields(column_map):
            missing = mapper.get_missing_fields(column_map)
            print(f"  ⚠️ Missing required fields: {missing}")
            continue

        # Step 3: Parse rows into transactions
        parser = TransactionParser(column_map, bank_name or 'Unknown')
        transactions = parser.parse_dataframe(df)

        print(f"  ✅ Extracted {len(transactions)} transactions")
        all_transactions.extend(transactions)

    return all_transactions


def test_bank(pdf_path: str, json_path: str, bank_name: str = None):
    """Test extraction for a single bank"""

    import json

    # Extract
    transactions = extract_transactions(pdf_path, bank_name)

    # Load expected
    with open(json_path) as f:
        data = json.load(f)
        expected = data.get('transactions', data) if isinstance(data, dict) else data

    # Compare
    print("\n📈 Results:")
    print(f"  Expected: {len(expected)}")
    print(f"  Extracted: {len(transactions)}")

    # Simple match by date and amount
    matches = 0
    for tx in transactions:
        for exp in expected:
            if tx['date'] == exp['date'] and abs(tx['amount'] - exp['amount']) < 1:
                matches += 1
                break

    accuracy = (matches / len(expected) * 100) if expected else 0
    print(f"  Matches: {matches}")
    print(f"  Accuracy: {accuracy:.2f}%")

    return accuracy, matches, len(expected)


def main():
    """Test all banks"""

    base_path = Path(__file__).parent.parent.parent / 'backup-core' / 'test'

    test_cases = [
        ('hdfc_Apr.pdf', 'hdfc_Apr.json', 'HDFC Bank'),
        ('idfc_Aug.pdf', 'idfc_Aug.json', 'IDFC First Bank'),
        ('icici_feb.pdf', 'icici_feb.json', 'ICICI Bank'),
        ('sbi_oct.pdf', 'sbi_oct.json', 'SBI Card'),
        ('Axis_Apr.pdf', 'Axis_Apr.json', 'Axis Bank'),
        ('Indusind_jun.pdf', 'Indusind_jun.json', 'IndusInd Bank'),
    ]

    results = []

    for pdf_file, json_file, bank_name in test_cases:
        pdf_path = base_path / 'statements' / pdf_file
        json_path = base_path / 'expected' / json_file

        if not pdf_path.exists():
            print(f"❌ PDF not found: {pdf_path}")
            continue

        if not json_path.exists():
            print(f"❌ JSON not found: {json_path}")
            continue

        accuracy, matches, expected = test_bank(str(pdf_path), str(json_path), bank_name)
        results.append({
            'bank': bank_name,
            'pdf': pdf_file,
            'accuracy': accuracy,
            'matches': matches,
            'expected': expected
        })

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    total_matches = sum(r['matches'] for r in results)
    total_expected = sum(r['expected'] for r in results)
    overall = (total_matches / total_expected * 100) if total_expected > 0 else 0

    for r in results:
        status = "✅" if r['accuracy'] >= 100 else "❌"
        print(f"{status} {r['bank']:15} | {r['accuracy']:6.2f}% | {r['matches']}/{r['expected']}")

    print(f"\n🎯 Overall: {overall:.2f}% ({total_matches}/{total_expected})")


if __name__ == "__main__":
    main()
