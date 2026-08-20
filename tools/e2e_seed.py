#!/usr/bin/env python3
"""Canonical E2E fixture seed — populates backend SQLite via API path.

Per M9 constraint: fixtures must seed via canonical backend/API into SQLite,
never direct Zustand/localStorage writes. This script uses FastAPI TestClient
against the running backend to insert deterministic test data.

Usage:
  PYTHONPATH=backend python3 tools/e2e_seed.py
  # Or via playwright hook:
  cd frontend && PLAYWRIGHT_API_URL=http://localhost:8000 npx playwright test
"""
import sys, os, json
from pathlib import Path

# Ensure backend is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from fastapi.testclient import TestClient
from src.api import app

BASE = "http://localhost:8000"

def seed():
    client = TestClient(app)
    
    # Check if already seeded (has transactions)
    resp = client.get(f"{BASE}/api/transactions")
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            print(f"  Already seeded: {len(data)} transactions found, skipping.")
            return
    
    print("Seeding E2E fixtures via canonical API path...")
    
    # Seed banks
    bank_resp = client.post(f"{BASE}/api/banks", json={"name": "Test Bank", "currency": "INR"})
    assert bank_resp.status_code in (200, 201), f"Banks: {bank_resp.status_code}"
    
    # Seed members
    member_resp = client.post(f"{BASE}/api/members", json={"name": "Self", "color": "#3b82f6"})
    assert member_resp.status_code in (200, 201), f"Members: {member_resp.status_code}"
    member_id = member_resp.json().get("id", 1)
    
    # Seed accounts
    for acc_name, acc_type in [("Savings", "savings"), ("Credit Card", "credit_card")]:
        acc_resp = client.post(f"{BASE}/api/accounts", json={
            "name": acc_name, "type": acc_type, "bank_id": 1,
            "balance": 50000 if acc_type == "savings" else 15000
        })
        assert acc_resp.status_code in (200, 201), f"Accounts: {acc_resp.status_code}"
    
    # Seed statements with transactions via CSV import
    csv_data = """date,description,amount,type,category
2025-01-15,Salary Credit,50000,credit,salary
2025-01-16,UPI Payment - Amazon,2999,debit,shopping
2025-01-17,ATM Withdrawal,5000,debit,cash
2025-01-18,Netflix Subscription,649,debit,entertainment
2025-01-20,Grocery Store,1500,debit,groceries
2025-02-01,Salary Credit,52000,credit,salary
2025-02-05,UPI Payment - Swiggy,450,debit,dining
2025-02-10,Mutual Fund SIP,10000,debit,investment
2025-02-15,Electricity Bill,1200,debit,utilities
2025-03-01,Salary Credit,52000,credit,salary
"""
    import io
    from fastapi import UploadFile
    
    csv_file = UploadFile(
        filename="e2e_seed.csv",
        file=io.BytesIO(csv_data.encode())
    )
    
    detect_resp = client.post(f"{BASE}/api/import/detect", files={"file": csv_file})
    if detect_resp.status_code == 200:
        mapping = detect_resp.json().get("detected_mapping", {})
        execute_resp = client.post(f"{BASE}/api/import/execute", json={
            "filename": "e2e_seed.csv",
            "mapping": {
                "date_column": mapping.get("date_column", "date"),
                "description_column": mapping.get("description_column", "description"),
                "amount_column": mapping.get("amount_column", "amount"),
                "type_column": mapping.get("type_column", "type"),
                "date_format": "%Y-%m-%d",
                "bank_name": "Test Bank",
                "member": "Self",
            }
        })
        if execute_resp.status_code in (200, 201):
            result = execute_resp.json()
            print(f"  Imported {result.get('imported', 0)} transactions")
        else:
            print(f"  Import execute failed: {execute_resp.status_code} {execute_resp.text[:100]}")
    else:
        print(f"  Import detect failed: {detect_resp.status_code}")
    
    # Verify
    txn_resp = client.get(f"{BASE}/api/transactions")
    if txn_resp.status_code == 200:
        txns = txn_resp.json()
        print(f"  Verified: {len(txns) if isinstance(txns, list) else 'unknown'} transactions in DB")
    
    print("  Seed complete.")

if __name__ == "__main__":
    seed()
