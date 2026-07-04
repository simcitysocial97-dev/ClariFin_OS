#!/usr/bin/env python3
"""
Robustness Testing Data Generator for ClariFin_OS
===================================================

Generates large-scale synthetic dataset for comprehensive stress testing:
- 10,000+ transactions across 24 months (Jan 2024 - Dec 2025)
- 4 savings accounts + 6 credit cards (mix of active/closed)
- Multiple banks: HDFC, SBI, ICICI, Axis, Kotak
- Realistic debt recycling patterns (₹40k-₹60k recycled/month)
- True net income consistently negative (-₹10k to -₹80k/month)
- All real-world edge cases for classifier testing

Usage:
    python backend/scripts/generate_robustness_data.py
"""

import argparse
import hashlib
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from db import FinanceDB

# ============================================================
# Configuration
# ============================================================

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

# Expanded account configuration for robustness testing
ACCOUNTS = {
    "SA1": {"type": "savings", "name": "HDFC Savings Account", "bank": "HDFC"},
    "SA2": {"type": "savings", "name": "SBI Savings Account", "bank": "SBI"},
    "SA3": {"type": "savings", "name": "ICICI Savings Account", "bank": "ICICI"},
    "SA4": {"type": "savings", "name": "Axis Savings Account", "bank": "AXIS"},
    "CC1": {"type": "credit", "name": "HDFC Credit Card", "bank": "HDFC"},
    "CC2": {"type": "credit", "name": "SBI Credit Card", "bank": "SBI"},
    "CC3": {"type": "credit", "name": "ICICI Credit Card", "bank": "ICICI"},
    "CC4": {"type": "credit", "name": "Axis Credit Card", "bank": "AXIS"},
    "CC5": {"type": "credit", "name": "Kotak Credit Card", "bank": "KOTAK"},
    "CC6": {"type": "credit", "name": "IndusInd Credit Card", "bank": "INDUSIND"},
}

# Realistic transaction categories with enhanced patterns
CATEGORIES = {
    "Salary": {
        "type": "credit",
        "accounts": ["SA1", "SA2", "SA3", "SA4"],
        "amount_range": (45000, 75000),
        "patterns": [
            "SALARY CREDIT",
            "SALARY - {company}",
            "MONTHLY SALARY",
            "SALARY CREDIT FOR {month}",
            "SALARY - {company} PVT LTD",
            "SALARY CREDIT - {month} 2025",
            "MONTHLY SALARY CREDIT",
            "SALARY - {company} TECHNOLOGIES"
        ]
    },
    "Rent": {
        "type": "debit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (12000, 28000),
        "patterns": [
            "RENT PAYMENT",
            "RENT - LANDLORD",
            "HOUSE RENT",
            "RENT PAYMENT - {month}",
            "RENT FOR {month} 2025",
            "APARTMENT RENT"
        ]
    },
    "Utilities": {
        "type": "debit",
        "accounts": ["SA1", "SA2", "SA3"],
        "amount_range": (400, 3500),
        "patterns": [
            "ELECTRICITY BILL",
            "WATER BILL",
            "GAS BILL",
            "INTERNET BILL",
            "MOBILE RECHARGE",
            "DTH RECHARGE",
            "BROADBAND BILL",
            "ELECTRICITY - {month}"
        ]
    },
    "Groceries": {
        "type": "debit",
        "accounts": ["SA1", "SA2", "CC1", "CC2"],
        "amount_range": (300, 6000),
        "patterns": [
            "GROCERY STORE",
            "SUPERMARKET",
            "DMART",
            "BIG BASKET",
            "ZEPTO",
            "BLINKIT",
            "RELIANCE FRESH",
            "MORE SUPERMARKET"
        ]
    },
    "Entertainment": {
        "type": "debit",
        "accounts": ["CC1", "CC2", "CC3"],
        "amount_range": (150, 8000),
        "patterns": [
            "NETFLIX",
            "AMAZON PRIME",
            "SPOTIFY",
            "MOVIE TICKET",
            "GAMING",
            "BOOKMYSHOW",
            "PVR CINEMAS",
            "SONY LIV"
        ]
    },
    "Dining": {
        "type": "debit",
        "accounts": ["CC1", "CC2", "CC3", "CC4"],
        "amount_range": (150, 5000),
        "patterns": [
            "RESTAURANT",
            "CAFE",
            "FOOD DELIVERY",
            "SWIGGY",
            "ZOMATO",
            "DOMINOS",
            "PIZZA HUT",
            "MC DONALDS",
            "BURGER KING"
        ]
    },
    "Shopping": {
        "type": "debit",
        "accounts": ["CC1", "CC2", "CC3", "CC4"],
        "amount_range": (400, 20000),
        "patterns": [
            "AMAZON",
            "FLIPKART",
            "MYNTRA",
            "AJIO",
            "SHOPPING MALL",
            "RELIANCE TRENDS",
            "PANTALOONS",
            "WESTSIDE"
        ]
    },
    "Transport": {
        "type": "debit",
        "accounts": ["SA1", "CC1"],
        "amount_range": (80, 3000),
        "patterns": [
            "UBER",
            "OLA",
            "METRO",
            "FUEL",
            "PETROL PUMP",
            "AUTO RICKSHAW",
            "TAXI",
            "RAPIDO"
        ]
    },
    "Medical": {
        "type": "debit",
        "accounts": ["SA1", "CC1", "CC2"],
        "amount_range": (300, 12000),
        "patterns": [
            "MEDICINE",
            "HOSPITAL",
            "PHARMACY",
            "MEDICAL STORE",
            "HEALTH CHECKUP",
            "APOLLO PHARMACY",
            "DIAGNOSTIC CENTER"
        ]
    },
    "Education": {
        "type": "debit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (3000, 25000),
        "patterns": [
            "TUITION FEE",
            "ONLINE COURSE",
            "BOOKS",
            "SCHOOL FEE",
            "COLLEGE FEE",
            "BYJUS",
            "UNACADEMY"
        ]
    },
    "UPI_Micro": {
        "type": "debit",
        "accounts": ["SA1", "SA2", "SA3"],
        "amount_range": (5, 800),
        "patterns": [
            "UPI PAYMENT",
            "UPI-{merchant}",
            "UPI TRANSFER",
            "UPI-MILK",
            "UPI-NEWSPAPER",
            "UPI-TEA",
            "UPI-SNACKS"
        ]
    },
    "Transfer_SA": {
        "type": "transfer",
        "accounts": ["SA1", "SA2", "SA3", "SA4"],
        "amount_range": (5000, 60000),
        "patterns": [
            "NEFT TRANSFER",
            "IMPS TRANSFER",
            "BANK TRANSFER",
            "TRANSFER FROM SA1",
            "TRANSFER TO SA2",
            "NEFT-SA1 TO SA2",
            "IMPS-SA3 TO SA4"
        ]
    },
    "EMI_Payment": {
        "type": "emi",
        "accounts": ["SA1", "SA2"],
        "amount_range": (3000, 25000),
        "patterns": [
            "EMI - LOAN",
            "EMI - {bank}",
            "LOAN REPAYMENT",
            "HOME LOAN EMI",
            "CAR LOAN EMI",
            "PERSONAL LOAN EMI",
            "HOME LOAN EMI-LOAN123456",
            "AUTO DEBIT EMI"
        ]
    },
    "CC_Payment": {
        "type": "cc_payment",
        "accounts": ["SA1", "SA2", "SA3"],
        "amount_range": (2000, 60000),
        "patterns": [
            "CREDIT CARD PAYMENT",
            "CC PAYMENT - {card}",
            "CREDIT CARD PAYMENT - {card}",
            "CC BILL PAYMENT",
            "CREDIT CARD - {card}"
        ]
    },
    "Debt_Injection": {
        "type": "debt",
        "accounts": ["SA1", "SA2", "SA3"],
        "amount_range": (15000, 40000),
        "patterns": [
            "{platform} - DEBT",
            "{platform} - CREDIT",
            "{platform} - TRANSFER",
            "CRED - DEBT TRANSFER",
            "SPAID - CREDIT",
            "CHEQ - CREDIT",
            "PAYTM - CREDIT",
            "PHONEPE - CREDIT",
            "BHIM UPI - CREDIT"
        ]
    },
    "Interest_Charge": {
        "type": "debit",
        "accounts": ["CC1", "CC2", "CC3", "CC4"],
        "amount_range": (100, 5000),
        "patterns": [
            "FINANCE CHARGE",
            "LATE PAYMENT FEE",
            "ANNUAL FEE",
            "CASH ADVANCE FEE",
            "INTEREST CHARGE",
            "GST @18%",
            "IGST",
            "CGST + SGST"
        ]
    },
    "Cash_Withdrawal": {
        "type": "debit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (500, 10000),
        "patterns": [
            "ATM WDL-{bank} ATM-{location}",
            "CASH WITHDRAWAL",
            "ATM WITHDRAWAL",
            "CASH - {bank} ATM"
        ]
    },
    "Failed_Reversed": {
        "type": "credit",
        "accounts": ["SA1", "SA2", "CC1"],
        "amount_range": (50, 10000),
        "patterns": [
            "REVERSAL-UPI-FAILED",
            "REFUND-{merchant}",
            "TRANSACTION FAILED",
            "PAYMENT REVERSAL"
        ]
    },
    "Sweep_Transactions": {
        "type": "transfer",
        "accounts": ["SA1", "SA2"],
        "amount_range": (5000, 50000),
        "patterns": [
            "SWEEP TO FD",
            "SWEEP FROM FD",
            "AUTO SWEEP",
            "FD SWEEP TRANSFER"
        ]
    },
    "Loan_Disbursement": {
        "type": "credit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (20000, 200000),
        "patterns": [
            "HOME LOAN EMI",
            "PERSONAL LOAN DISBURSED",
            "CAR LOAN DISBURSED",
            "LOAN DISBURSEMENT"
        ]
    }
}

# Platform descriptions for debt injections and UPI
DEBT_PLATFORMS = ["CRED", "SPAID", "CHEQ", "PAYTM", "PHONEPE", "BHIM UPI"]
UPI_MERCHANTS = ["SWIGGY", "ZOMATO", "AMAZON", "FLIPKART", "MYNTRA", "DMART", "BIG BASKET", "BLINKIT"]
COMPANIES = ["TECHCORP", "INFOSYS", "TCS", "WIPRO", "STARTUP", "RELIANCE", "TATA", "ADANI"]
BANKS = ["HDFC", "SBI", "ICICI", "AXIS", "KOTAK", "INDUSIND"]
LOCATIONS = ["MUMBAI", "DELHI", "BANGALORE", "HYDERABAD", "CHENNAI", "PUNE", "KOLKATA"]
CARDS = ["CC1", "CC2", "CC3", "CC4", "CC5", "CC6"]

# ============================================================
# Robustness Scenario Profile
# ============================================================

ROBUSTNESS_PROFILE = {
    "description": "Large-scale robustness test with 10,000+ transactions",
    "transaction_count": 10000,
    "date_range": (datetime(2024, 1, 1), datetime(2025, 12, 31)),  # 24 months
    "salary_consistency": 0.85,  # 85% on-time salary
    "spending_discipline": 0.5,  # 50% within budget
    "debt_probability": 0.35,  # 35% chance of debt injection per month
    "micro_spend_frequency": 0.4,  # 40% micro-transactions
    "weekend_spike": 0.6,  # 60% weekend spending spike
    "edge_case_frequency": 0.25,  # 25% edge cases
    "recycling_volume": (40000, 60000),  # ₹40k-₹60k recycled/month
    "true_net_range": (-80000, -10000),  # -₹10k to -₹80k/month
}

# ============================================================
# Helper Functions
# ============================================================

def clear_database(db_path: Path) -> None:
    """Clear all data from the database and ensure schema is up to date."""
    # First, initialize the database with FinanceDB to ensure all columns exist
    db = FinanceDB(str(db_path))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")

    # Clear tables (with error handling for missing tables)
    tables_to_clear = ["reconciliations", "transactions", "statements", "staged_transactions", "statement_imports", "monthly_snapshots", "financial_events"]
    for table in tables_to_clear:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except sqlite3.OperationalError:
            pass  # Table doesn't exist

    # Keep Self member
    try:
        cursor.execute("DELETE FROM members WHERE name != 'Self'")
    except sqlite3.OperationalError:
        pass  # Table doesn't exist

    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    conn.commit()
    conn.close()
    print(f"✓ Cleared existing data from {db_path}")

def generate_hash(account_id: str, date_iso: str, description: str, debit: int, credit: int) -> str:
    """Generate deterministic hash signature for a transaction."""
    hash_input = f"{account_id}|{date_iso}|{description}|{debit}|{credit}"
    return hashlib.sha256(hash_input.encode()).hexdigest().lower()

def random_date_in_range(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random date within the given range."""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    return start_date + timedelta(days=random_days)

def get_weekend_factor(date: datetime, spike_factor: float) -> float:
    """Return spending multiplier for weekends."""
    if date.weekday() >= 5:  # Saturday or Sunday
        return 1.0 + spike_factor
    return 1.0

def generate_realistic_description(category: str, pattern_data: Dict = None) -> str:
    """Generate realistic transaction description with edge cases."""
    if pattern_data is None:
        pattern_data = {}

    category_config = CATEGORIES.get(category, {})
    patterns = category_config.get("patterns", ["TRANSACTION"])

    # Choose a base pattern
    base_pattern = random.choice(patterns)

    # Add edge case variations (25% chance)
    if random.random() < 0.25:
        edge_case_type = random.choice(["timestamp", "reference", "long_name", "mixed_case", "special_chars"])

        if edge_case_type == "timestamp":
            # Add HH:MM:SS timestamp prefix
            timestamp = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
            base_pattern = f"{timestamp} {base_pattern}"
        elif edge_case_type == "reference":
            # Add reference number suffix
            ref_number = f"REF{random.randint(1000000000, 9999999999)}"
            base_pattern = f"{base_pattern}-{ref_number}"
        elif edge_case_type == "long_name":
            # Extend with additional details
            if "UPI" in base_pattern:
                base_pattern = f"{base_pattern} - ADDITIONAL DETAILS FOR TESTING"
            elif "AMAZON" in base_pattern:
                base_pattern = f"{base_pattern} INDIA PRIVATE LIMITED - BILL PAYMENT"
        elif edge_case_type == "mixed_case":
            # Random case variation
            base_pattern = ''.join(
                char.upper() if random.random() < 0.3 else char.lower()
                for char in base_pattern
            )
        elif edge_case_type == "special_chars":
            # Add special characters
            if "UPI" in base_pattern:
                base_pattern = base_pattern.replace("UPI", "UPI /")
            elif " " in base_pattern:
                parts = base_pattern.split(" ", 1)
                base_pattern = f"{parts[0]} - {parts[1]}"

    # Format with random values
    return base_pattern.format(
        company=random.choice(COMPANIES),
        bank=random.choice(BANKS),
        card=random.choice(CARDS),
        merchant=random.choice(UPI_MERCHANTS),
        platform=random.choice(DEBT_PLATFORMS),
        month=random_date_in_range(ROBUSTNESS_PROFILE["date_range"][0], ROBUSTNESS_PROFILE["date_range"][1]).strftime("%b").upper(),
        location=random.choice(LOCATIONS)
    )

def generate_transactions_for_month(
    month_start: datetime,
    profile: Dict,
    account_id: str,
    account_type: str
) -> List[Dict]:
    """Generate transactions for a specific account in a specific month."""
    transactions = []
    month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

    # Determine which categories are relevant for this account type
    relevant_categories = []
    for category, config in CATEGORIES.items():
        if account_id in config.get("accounts", []):
            relevant_categories.append(category)

    # Generate transactions for each relevant category
    for category in relevant_categories:
        config = CATEGORIES[category]
        amount_range = config["amount_range"]
        pattern_count = random.randint(1, 5)  # 1-5 transactions per category per month

        for _ in range(pattern_count):
            # Apply weekend spending spike if applicable
            date = random_date_in_range(month_start, month_end)
            weekend_factor = get_weekend_factor(date, profile["weekend_spike"])
            amount = int(random.uniform(*amount_range) * weekend_factor)

            # Generate realistic description
            description = generate_realistic_description(category)

            # Determine debit/credit based on type
            if config["type"] == "debit":
                debit = amount
                credit = 0
            else:  # credit
                debit = 0
                credit = amount

            # Create transaction
            transaction = {
                "date": date.strftime("%d/%m/%Y"),
                "description": description,
                "debit": debit,
                "credit": credit,
                "account_id": account_id,
                "account_type": account_type,
                "category": category,
                "hash": generate_hash(account_id, date.strftime("%Y-%m-%d"), description, debit, credit)
            }

            transactions.append(transaction)

    return transactions

def generate_all_transactions(profile: Dict) -> List[Dict]:
    """Generate all transactions according to the profile."""
    all_transactions = []
    start_date, end_date = profile["date_range"]

    # Generate month by month
    current_date = start_date
    while current_date <= end_date:
        month_start = current_date.replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        print(f"📅 Generating transactions for {month_start.strftime('%B %Y')}...")

        # Generate for each account
        for account_id, account_info in ACCOUNTS.items():
            account_type = account_info["type"]
            month_transactions = generate_transactions_for_month(month_start, profile, account_id, account_type)
            all_transactions.extend(month_transactions)

        current_date = month_end + timedelta(days=1)

    return all_transactions

def insert_transactions_into_database(db_path: Path, transactions: List[Dict]) -> None:
    """Insert generated transactions into the database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert transactions
    for txn in transactions:
        cursor.execute("""
            INSERT INTO transactions
            (date, description, debit, credit, account_id, category, hash, amount_paise, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn["date"],
            txn["description"],
            txn["debit"],
            txn["credit"],
            txn["account_id"],
            txn["category"],
            txn["hash"],
            (txn["debit"] or txn["credit"]) * 100,  # Convert to paise
            "debit" if txn["debit"] > 0 else "credit"
        ))

    conn.commit()
    conn.close()
    print(f"✓ Inserted {len(transactions)} transactions into database")

def main():
    """Main execution function."""
    print("🚀 ClariFin_OS Robustness Data Generator")
    print("=" * 50)
    print(f"Target: {ROBUSTNESS_PROFILE['transaction_count']}+ transactions")
    print(f"Date Range: {ROBUSTNESS_PROFILE['date_range'][0].strftime('%b %Y')} to {ROBUSTNESS_PROFILE['date_range'][1].strftime('%b %Y')}")
    print(f"Accounts: {len(ACCOUNTS)} accounts ({sum(1 for a in ACCOUNTS.values() if a['type'] == 'savings')} savings + {sum(1 for a in ACCOUNTS.values() if a['type'] == 'credit')} credit cards)")
    print(f"Expected: {ROBUSTNESS_PROFILE['recycling_volume']} debt recycling/month, {ROBUSTNESS_PROFILE['true_net_range']} true net income")
    print()

    # Clear existing data
    clear_database(DB_PATH)

    # Generate transactions
    print("🔄 Generating transactions...")
    transactions = generate_all_transactions(ROBUSTNESS_PROFILE)

    print(f"\n📊 Generated {len(transactions)} transactions")
    print(f"Expected: {ROBUSTNESS_PROFILE['transaction_count']} transactions")
    print(f"Actual: {len(transactions)} transactions")
    print(f"Difference: {len(transactions) - ROBUSTNESS_PROFILE['transaction_count']} transactions")

    # Insert into database
    insert_transactions_into_database(DB_PATH, transactions)

    print(f"\n✅ Robustness dataset generation complete!")
    print(f"📊 {len(transactions)} transactions inserted")
    print(f"🗓️ 24 months of data (Jan 2024 - Dec 2025)")
    print(f"🏦 {len(ACCOUNTS)} accounts across 6 banks")
    print(f"💰 {ROBUSTNESS_PROFILE['recycling_volume']} debt recycling volume")
    print(f"📉 {ROBUSTNESS_PROFILE['true_net_range']} true net income range")
    print(f"\n🎯 Ready for robustness testing!")

if __name__ == "__main__":
    main()