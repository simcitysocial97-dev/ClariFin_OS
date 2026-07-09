"""
ingest.py
=========
CLI ingestion pipeline: PDF → extract → categorize → database.

Usage:
    python ingest.py <pdf_path_or_directory> [--debug]

    # Single file
    python ingest.py statements/hdfc_jun_2025.pdf

    # Entire directory
    python ingest.py statements/

If a PDF has already been imported (by filename + bank), it is skipped.

Example output:
    Processing: hdfc_jun_2025.pdf
      Bank: HDFC Bank
      Transactions: 82
      Period: 01/06/2025 — 30/06/2025
      Categories: Food & Dining (23), Shopping (18), Travel (12), ...
      ✅ Imported

    Processing: icici_jun_2025.pdf
      Already imported, skipping.

    Done: 1 imported, 1 skipped, 82 transactions total
"""

from typing import Any
import sys
from collections import Counter
from pathlib import Path

# Allow running from any directory by adding src/ to path
_SRC_DIR = Path(__file__).parent
if str(_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR))

from categorizer import categorize
from metadata_extractor import MetadataExtractor
from src.repositories.statement_repository import StatementRepository
from src.repositories.transaction_repository import TransactionRepository
from statement_extractor import StatementExtractor

# ============================================================
# Core Ingestion Logic
# ============================================================

def ingest_pdf(pdf_path: str, db_path: str = "data/finance.db", debug: bool = False) -> dict[str, Any]:
    """
    Process a single PDF file through the full pipeline:
      1. Check for duplicate (skip if already imported)
      2. Extract transactions using StatementExtractor
      3. Categorize each transaction
      4. Insert into database

    Returns a result dict:
      {
        "file": str,
        "status": "imported" | "skipped" | "error",
        "bank": str,
        "transaction_count": int,
        "inserted_count": int,
        "period_from": str,
        "period_to": str,
        "categories": dict[str, Any],
        "error": str (only on error)
      }
    """
    file_name = Path(pdf_path).name
    result = {
        "file": file_name,
        "status": "error",
        "bank": "",
        "transaction_count": 0,
        "inserted_count": 0,
        "period_from": "",
        "period_to": "",
        "categories": {},
        "error": "",
    }

    stmt_repo = StatementRepository(db_path)
    txn_repo = TransactionRepository(db_path)

    try:
        # Step 1: Extract
        extractor = StatementExtractor(pdf_path, debug=debug)
        data = extractor.extract()

        bank = data.get("bank", "Unknown")
        result["bank"] = bank

        # Step 2: Duplicate check (by bank + filename)
        if stmt_repo.get_duplicate_check(bank, file_name):
            result["status"] = "skipped"
            return result

        transactions = data.get("transactions", [])
        result["transaction_count"] = len(transactions)

        period = data.get("statement_period", {})
        period_from = period.get("from", "")
        period_to = period.get("to", "")
        result["period_from"] = period_from
        result["period_to"] = period_to

        # Step 3: Categorize
        category_counts: Counter[Any] = Counter()
        for txn in transactions:
            desc = txn.get("description", "") or ""
            # Fix 4: Pass amount to categorize() for UPI small-transaction fallback
            amount_float = None
            try:
                amount_str = str(txn.get("amount", "")).replace(",", "")
                amount_float = float(amount_str) if amount_str else None
            except (ValueError, TypeError):
                amount_float = None
            cat, sub = categorize(desc, amount_float)
            txn["category"] = cat
            txn["subcategory"] = sub
            category_counts[cat] += 1

        result["categories"] = dict(category_counts.most_common())

        # Step 4: Insert into DB
        stmt_id = stmt_repo.insert_statement(
            bank=bank,
            file_name=file_name,
            period_from=period_from,
            period_to=period_to,
        )
        inserted = txn_repo.insert_transactions(stmt_id, transactions)
        result["inserted_count"] = inserted
        result["status"] = "imported"

        # Step 5: Extract metadata + validate
        try:
            meta_extractor = MetadataExtractor(pdf_path, bank=bank, debug=debug)
            metadata = meta_extractor.extract()
            stmt_repo.update_statement_metadata(stmt_id, metadata)

            # Print metadata findings
            if metadata.get("card_last4"):
                print(f"  Card: ****{metadata['card_last4']}")
            if metadata.get("total_amount_due") is not None:
                total_due = metadata["total_amount_due"]
                if total_due < 0:
                    print(f"  Total Amount Due: -₹{abs(total_due):,.2f} (credit balance)")
                else:
                    print(f"  Total Amount Due: ₹{total_due:,.2f}")
            if metadata.get("minimum_amount_due") is not None:
                print(f"  Minimum Due: ₹{metadata['minimum_amount_due']:,.2f}")
            if metadata.get("due_date"):
                print(f"  Payment Due Date: {metadata['due_date']}")
            if metadata.get("credit_limit") is not None:
                print(f"  Credit Limit: ₹{metadata['credit_limit']:,.0f}")

            # ---- Validation ----
            total_due = metadata.get("total_amount_due")
            opening_bal = metadata.get("opening_balance") or 0.0

            if total_due is not None and total_due > 0:
                debit_sum = 0.0
                credit_sum = 0.0
                for txn in transactions:
                    try:
                        amt = float(str(txn.get("amount", "0")).replace(",", ""))
                    except (ValueError, TypeError):
                        amt = 0.0
                    if txn.get("type") == "debit":
                        debit_sum += amt
                    elif txn.get("type") == "credit":
                        credit_sum += amt

                # Try multiple comparison strategies
                # Different banks define "Total Amount Due" differently:
                # Strategy 1: Total Due = debits - credits (net new charges)
                diff1 = abs((debit_sum - credit_sum) - total_due)
                # Strategy 2: Total Due = debits only (before credits applied)
                diff2 = abs(debit_sum - total_due)
                # Strategy 3: Total Due = opening_balance + debits - credits
                diff3 = abs((debit_sum - credit_sum) - (total_due - opening_bal))
                # Strategy 4: Total Due = opening_balance + debits
                diff4 = abs(debit_sum - (total_due - opening_bal))

                # Pick the strategy with smallest difference
                strategies = [
                    (diff1, "net_vs_total"),
                    (diff2, "debits_vs_total"),
                    (diff3, "net_vs_adjusted"),
                    (diff4, "debits_vs_adjusted"),
                ]
                best_diff, best_strategy = min(strategies, key=lambda x: x[0])

                if best_diff < 1.0:
                    status = "exact_match"
                    symbol = "✅"
                elif best_diff < 100.0:
                    status = "close_match"
                    symbol = "⚠️"
                elif best_diff < 500.0:
                    status = "close_match"
                    symbol = "⚠️"
                else:
                    # Check for SBI EMI exception
                    # SBI Card statements with No-Cost EMI have Total Due < Total Outstanding
                    # because only the first EMI installment is billed, not the full purchase
                    is_emi = any(
                        'emi' in txn.get("description", "").lower() or
                        'fp emi' in txn.get("description", "").lower() or
                        'amortization' in txn.get("description", "").lower()
                        for txn in transactions
                    )
                    if bank == "SBI Card" and is_emi and debit_sum > total_due:
                        status = "emi_exception"
                        symbol = "📋"
                    else:
                        status = "mismatch"
                        symbol = "❌"

                stmt_repo.update_validation_status(stmt_id, status, round(best_diff, 2))
                result["validation_status"] = status
                result["validation_difference"] = round(best_diff, 2)

                print(f"  Validation: {symbol} {status} (strategy: {best_strategy})")
                print(f"    Debits:    ₹{debit_sum:,.2f}")
                print(f"    Credits:   ₹{credit_sum:,.2f}")
                print(f"    Net:       ₹{debit_sum - credit_sum:,.2f}")
                print(f"    Opening:   ₹{opening_bal:,.2f}")
                print(f"    Total Due: ₹{total_due:,.2f}")
                print(f"    Best diff: ₹{best_diff:,.2f}")

            elif total_due is not None and total_due < 0:
                # Credit balance - bank owes customer
                stmt_repo.update_validation_status(stmt_id, "credit_balance", abs(total_due))
                result["validation_status"] = "credit_balance"
                print(f"  Validation: 💰 Credit balance (bank owes you ₹{abs(total_due):,.2f})")
            else:
                stmt_repo.update_validation_status(stmt_id, "no_metadata", 0.0)
                result["validation_status"] = "no_metadata"
                print("  Validation: ⚠️ Total due not found in PDF")

        except Exception as meta_err:
            print(f"  Metadata extraction error: {meta_err}")
            if debug:
                import traceback
                traceback.print_exc()
            try:
                stmt_repo.update_validation_status(stmt_id, "error", 0.0)
            except Exception:
                pass

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        if debug:
            import traceback
            traceback.print_exc()

    return result


def ingest_directory(dir_path: str, db_path: str = "data/finance.db", debug: bool = False) -> list[dict]:
    """Process all .pdf files in a directory. Returns list of result dicts."""
    pdf_files = sorted(Path(dir_path).glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in: {dir_path}")
        return []

    results = []
    for pdf_file in pdf_files:
        result = ingest_pdf(str(pdf_file), db_path, debug=debug)
        results.append(result)
    return results


# ============================================================
# Output Formatting
# ============================================================

def _format_categories(categories: dict[str, Any], top_n: int = 6) -> str:
    """Format category counts as a compact string."""
    if not categories:
        return "None"
    items = list(categories.items())[:top_n]
    parts = [f"{cat} ({count})" for cat, count in items]
    if len(categories) > top_n:
        parts.append(f"... +{len(categories) - top_n} more")
    return ", ".join(parts)


def _print_result(result: dict[str, Any]) -> None:
    """Print a formatted result for one PDF."""
    file_name = result["file"]
    status = result["status"]

    print(f"\nProcessing: {file_name}")

    if status == "skipped":
        print("  Already imported, skipping.")
        return

    if status == "error":
        print(f"  ❌ Error: {result['error']}")
        return

    # Imported successfully
    bank = result["bank"]
    txn_count = result["transaction_count"]
    inserted = result["inserted_count"]
    period_from = result["period_from"]
    period_to = result["period_to"]
    categories = result["categories"]

    print(f"  Bank: {bank}")
    print(f"  Transactions: {txn_count} extracted, {inserted} inserted")

    if period_from or period_to:
        period_str = f"{period_from} — {period_to}" if period_from and period_to else (period_from or period_to)
        print(f"  Period: {period_str}")

    if categories:
        print(f"  Categories: {_format_categories(categories)}")

    print("  ✅ Imported")


def _print_summary(results: list[dict[str, Any]]) -> None:
    """Print final summary line."""
    imported = sum(1 for r in results if r["status"] == "imported")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors = sum(1 for r in results if r["status"] == "error")
    total_txns = sum(r["inserted_count"] for r in results)

    parts = [f"{imported} imported", f"{skipped} skipped"]
    if errors:
        parts.append(f"{errors} errors")
    parts.append(f"{total_txns} transactions total")

    print(f"\nDone: {', '.join(parts)}")


# ============================================================
# CLI Entry Point
# ============================================================

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <pdf_path_or_directory> [--debug]")
        print("       python ingest.py statements/hdfc_jun.pdf")
        print("       python ingest.py statements/")
        sys.exit(1)

    target = sys.argv[1]
    debug = "--debug" in sys.argv

    target_path = Path(target)
    if not target_path.exists():
        print(f"Error: Path not found: {target}")
        sys.exit(1)

    # Database path (relative to CWD)
    db_path = "data/finance.db"

    if target_path.is_dir():
        results = ingest_directory(str(target_path), db_path, debug=debug)
    elif target_path.suffix.lower() == ".pdf":
        result = ingest_pdf(str(target_path), db_path, debug=debug)
        results = [result]
        _print_result(result)
        _print_summary(results)
        return
    else:
        print(f"Error: Expected a .pdf file or directory, got: {target}")
        sys.exit(1)

    # Print results for directory mode
    for result in results:
        _print_result(result)

    _print_summary(results)


if __name__ == "__main__":
    main()
