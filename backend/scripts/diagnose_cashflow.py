#!/usr/bin/env python3
"""Diagnostic script to investigate cashflow engine discrepancy."""
import sys
sys.path.insert(0, 'backend/src')

from db.core import FinanceDB
from engines.cashflow_engine import compute_monthly_cashflow

DB_PATH = "backend/data/finance.db"
db = FinanceDB(DB_PATH)

# Busiest month from SQL query
month = "2025-03"

print(f"=== Diagnosing cashflow for {month} ===\n")

# Get engine result
result = compute_monthly_cashflow(db, months=12)

print(f"Engine result type: {type(result)}")
print(f"Engine result length: {len(result) if isinstance(result, list) else 'N/A'}\n")

if isinstance(result, list):
    print("All months returned by engine:")
    for m in result:
        print(f"  {m.get('month')}: credits={m.get('total_income_paise', 0):,} debits={m.get('total_expense_paise', 0):,}")
    
    print(f"\nLooking for {month}...")
    for m in result:
        if m.get('month') == month:
            print(f"Found: {m}")
            break
    else:
        print(f"Month {month} NOT in engine results!")
        print(f"\nMost recent month available: {result[0].get('month') if result else 'None'}")