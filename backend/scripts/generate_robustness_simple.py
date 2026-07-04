#!/usr/bin/env python3
"""
Standalone Robustness Data Generator for ClariFin_OS
=====================================================

Generates large-scale synthetic dataset directly into database:
- 10,000+ transactions across 24 months (Jan 2024 - Dec 2025)
- 4 savings accounts + 6 credit cards
- Multiple banks: HDFC, SBI, ICICI, Axis, Kotak
- Realistic debt recycling patterns
- All edge cases for classifier testing

No external dependencies - works standalone.
"""

import hashlib
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# Database path
DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

# Configuration
ACCOUNTS = {
    "SA1": {"type": "savings", "name": "HDFC Savings", "bank": "HDFC"},
    "SA2": {"type": "savings", "name": "SBI Savings", "bank": "SBI"},
    "SA3": {"type": "savings", "name": "ICICI Savings", "bank": "ICICI"},
    "SA4": {"type": "savings", "name": "Axis Savings", "bank": "AXIS"},
    "CC1": {"type": "credit", "name": "HDFC CC", "bank": "HDFC"},
    "CC2": {"type": "credit", "name": "SBI CC", "bank": "SBI"},
    "CC3": {"type": "credit", "name": "ICICI CC", "bank": "ICICI"},
    "CC4": {"type": "credit", "name": "Axis CC", "bank": "AXIS"},
    "CC5": {"type": "credit", "name": "Kotak CC", "bank": "KOTAK"},
    "CC6": {"type": "credit", "name": "IndusInd CC", "bank": "INDUSIND"},
}

# Transaction patterns with edge cases
PATTERNS = {
    "Salary": {
        "type": "credit",
        "accounts": ["SA1", "SA2", "SA3", "SA4"],
        "amount": (45000, 75000),
        "templates": [
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
        "amount": (12000, 28000),
        "templates": [
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
        "amount": (400, 3500),
        "templates": [
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
        "amount": (300, 6000),
        "templates": [
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
        "amount": (150, 8000),
        "templates": [
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
        "amount": (150, 5000),
        "templates": [
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
        "amount": (400, 20000),
        "templates": [
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
        "amount": (80, 3000),
        "templates": [
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
        "amount": (300, 12000),
        "templates": [
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
        "amount": (3000, 25000),
        "templates": [
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
        "amount": (5, 800),
        "templates": [
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
        "amount": (5000, 60000),
        "templates": [
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
        "amount": (3000, 25000),
        "templates": [
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
        "amount": (2000, 60000),
        "templates": [
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
        "amount": (15000, 40000),
        "templates": [
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
        "amount": (100, 5000),
        "templates": [
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
        "amount": (500, 10000),
        "templates": [
            "ATM WDL-{bank} ATM-{location}",
            "CASH WITHDRAWAL",
            "ATM WITHDRAWAL",
            "CASH - {bank} ATM"
        ]
    },
    "Failed_Reversed": {
        "type": "credit",
        "accounts": ["SA1", "SA2", "CC1"],
        "amount": (50, 10000),
        "templates": [
            "REVERSAL-UPI-FAILED",
            "REFUND-{merchant}",
            "TRANSACTION FAILED",
            "PAYMENT REVERSAL"
        ]
    },
    "Sweep_Transactions": {
        "type": "transfer",
        "accounts": ["SA1", "SA2"],
        "amount": (5000, 50000),
        "templates": [
            "SWEEP TO FD",
            "SWEEP FROM FD",
            "AUTO SWEEP",
            "FD SWEEP TRANSFER"
        ]
    },
    "Loan_Disbursement": {
        "type": "credit",
        "accounts": ["SA1", "SA2"],
        "amount": (20000, 200000),
        "templates": [
            "HOME LOAN EMI",
            "PERSONAL LOAN DISBURSED",
            "CAR LOAN DISBURSED",
            "LOAN DISBURSEMENT"
        ]
    }
}

# Data for pattern generation
DEBT_PLATFORMS = ["CRED", "SPAID", "CHEQ", "PAYTM", "PHONEPE", "BHIM UPI"]
UPI_MERCHANTS = ["SWIGGY", "ZOMATO", "AMAZON", "FLIPKART", "MYNTRA", "DMART", "BIG BASKET", "BLINKIT"]
COMPANIES = ["TECHCORP", "INFOSYS", "TCS", "WIPRO", "STARTUP", "RELIANCE", "TATA", "ADANI"]
BANKS = ["HDFC", "SBI", "ICICI", "AXIS", "KOTAK", "INDUSIND"]
LOCATIONS = ["MUMBAI", "DELHI", "BANGALORE", "HYDERABAD", "CHENNAI", "PUNE", "KOLKATA"]
CARDS = ["CC1", "CC2", "CC3", "CC4", "CC5", "CC6"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

# Robustness profile
PROFILE = {
    "transaction_count": 10000,
    "date_range": (datetime(2024, 1, 1), datetime(2025, 12, 31)),
    "salary_consistency": 0.85,
    "debt_probability": 0.35,
    "edge_case_frequency": 0.25,
    "recycling_volume": (40000, 60000),
    "true_net_range": (-80000, -10000)
}

def clear_database():
    """Clear existing data from database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Disable foreign keys
    cursor.execute("PRAGMA foreign_keys = OFF")

    # Clear tables
    tables = ["reconciliations", "transactions", "statements", "staged_transactions", "statement_imports", "monthly_snapshots", "financial_events"]
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table}")
        except:
            pass

    # Keep Self member
    try:
        cursor.execute("DELETE FROM members WHERE name != 'Self'")
    except:
        pass

    cursor.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    conn.close()
    print(f"✓ Cleared database")

def generate_hash(account_id, date_iso, description, debit, credit):
    """Generate deterministic hash."""
    hash_input = f"{account_id}|{date_iso}|{description}|{debit}|{credit}"
    return hashlib.sha256(hash_input.encode()).hexdigest().lower()

def random_date(start, end):
    """Random date in range."""
    return start + timedelta(days=random.randint(0, (end - start).days))

def add_edge_case(description):
    """Add edge case variations (25% chance)."""
    if random.random() < 0.25:
        edge_type = random.choice(["timestamp", "reference", "long_name", "mixed_case", "special_chars"])

        if edge_type == "timestamp":
            timestamp = f"{random.randint(0, 23):02d}:{random.randint(0, 59):02d}:{random.randint(0, 59):02d}"
            return f"{timestamp} {description}"
        elif edge_type == "reference":
            ref = f"REF{random.randint(1000000000, 9999999999)}"
            return f"{description}-{ref}"
        elif edge_type == "long_name":
            if "UPI" in description:
                return f"{description} - ADDITIONAL DETAILS FOR TESTING"
            elif "AMAZON" in description:
                return f"{description} INDIA PRIVATE LIMITED - BILL PAYMENT"
        elif edge_type == "mixed_case":
            return ''.join(char.upper() if random.random() < 0.3 else char.lower() for char in description)
        elif edge_type == "special_chars":
            if "UPI" in description:
                return description.replace("UPI", "UPI /")
            elif " " in description:
                parts = description.split(" ", 1)
                return f"{parts[0]} - {parts[1]}"

    return description

def generate_description(category, pattern):
    """Generate realistic description."""
    formatted = pattern.format(
        company=random.choice(COMPANIES),
        bank=random.choice(BANKS),
        card=random.choice(CARDS),
        merchant=random.choice(UPI_MERCHANTS),
        platform=random.choice(DEBT_PLATFORMS),
        month=random.choice(MONTHS),
        location=random.choice(LOCATIONS)
    )
    return add_edge_case(formatted)

def generate_transactions():
    """Generate all transactions."""
    transactions = []
    start_date, end_date = PROFILE["date_range"]
    current_date = start_date

    print(f"🔄 Generating {PROFILE['transaction_count']} transactions...")

    while current_date <= end_date and len(transactions) < PROFILE["transaction_count"]:
        month_start = current_date.replace(day=1)
        month_end = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        # Generate for each account
        for account_id, account_info in ACCOUNTS.items():
            if len(transactions) >= PROFILE["transaction_count"]:
                break

            # Select relevant categories for this account
            relevant_cats = [cat for cat, config in PATTERNS.items() if account_id in config["accounts"]]

            for category in relevant_cats:
                if len(transactions) >= PROFILE["transaction_count"]:
                    break

                config = PATTERNS[category]
                amount_min, amount_max = config["amount"]
                pattern_count = random.randint(1, 5)

                for _ in range(pattern_count):
                    if len(transactions) >= PROFILE["transaction_count"]:
                        break

                    date = random_date(month_start, month_end)
                    amount = random.randint(amount_min, amount_max)

                    # Apply weekend spike
                    if date.weekday() >= 5:  # Weekend
                        amount = int(amount * 1.6)

                    description = generate_description(category, random.choice(config["templates"]))

                    if config["type"] == "debit":
                        debit, credit = amount, 0
                    else:
                        debit, credit = 0, amount

                    transaction = {
                        "date": date.strftime("%d/%m/%Y"),
                        "description": description,
                        "debit": debit,
                        "credit": credit,
                        "account_id": account_id,
                        "category": category,
                        "hash": generate_hash(account_id, date.strftime("%Y-%m-%d"), description, debit, credit)
                    }

                    transactions.append(transaction)

        current_date = month_end + timedelta(days=1)
        print(f"📅 Generated {len(transactions)} transactions up to {current_date.strftime('%b %Y')}")

    return transactions

def insert_transactions(transactions):
    """Insert transactions into database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create a synthetic statement for all transactions
    cursor.execute("""
        INSERT INTO statements (bank, file_name, source)
        VALUES ('SYNTHETIC', 'robustness_test_statement', 'synthetic')
    """)
    statement_id = cursor.lastrowid

    for txn in transactions:
        amount = txn["debit"] or txn["credit"]
        cursor.execute("""
            INSERT INTO transactions
            (statement_id, date, description, amount, debit, credit, account_id, category, amount_paise, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            statement_id,
            txn["date"],
            txn["description"],
            amount,  # Add amount column
            txn["debit"],
            txn["credit"],
            txn["account_id"],
            txn["category"],
            amount * 100,  # Convert to paise
            "debit" if txn["debit"] > 0 else "credit"
        ))

    conn.commit()
    conn.close()
    print(f"✓ Inserted {len(transactions)} transactions with statement_id {statement_id}")

def main():
    """Main execution."""
    print("🚀 ClariFin_OS Robustness Data Generator")
    print("=" * 50)
    print(f"Target: {PROFILE['transaction_count']} transactions")
    print(f"Date Range: {PROFILE['date_range'][0].strftime('%b %Y')} to {PROFILE['date_range'][1].strftime('%b %Y')}")
    print(f"Accounts: {len(ACCOUNTS)} accounts")
    print(f"Edge Cases: {PROFILE['edge_case_frequency']*100}% frequency")
    print()

    # Clear and generate
    clear_database()
    transactions = generate_transactions()
    insert_transactions(transactions)

    print(f"\n✅ Generation complete!")
    print(f"📊 {len(transactions)} transactions created")
    print(f"🗓️ 24 months of data")
    print(f"🏦 {len(ACCOUNTS)} accounts across 6 banks")
    print(f"💰 {PROFILE['recycling_volume']} debt recycling volume")
    print(f"📉 {PROFILE['true_net_range']} true net income range")
    print(f"\n🎯 Ready for robustness testing!")

if __name__ == "__main__":
    main()