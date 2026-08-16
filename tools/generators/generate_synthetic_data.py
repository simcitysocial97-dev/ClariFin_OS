#!/usr/bin/env python3
"""
Synthetic Dataset Generator for ClariFin_OS Testing
====================================================

Generates realistic transaction datasets for testing:
- 3 scenarios: Healthy, Debt Trap, Erratic
- 5 accounts: SA1, SA2, CC1, CC2, CC3
- 8 months of data (Jan-Aug 2025)
- Edge cases: late-night spends, weekend spikes, micro-transactions

Usage:
    python backend/scripts/generate_synthetic_data.py --scenario healthy
    python backend/scripts/generate_synthetic_data.py --scenario debt_trap
    python backend/scripts/generate_synthetic_data.py --scenario erratic
    python backend/scripts/generate_synthetic_data.py --scenario all
"""

import argparse
import contextlib
import hashlib
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.db.schema import create_all

# ============================================================
# Configuration
# ============================================================

DB_PATH = Path(__file__).parent.parent / "data" / "finance.db"

ACCOUNTS = {
    "SA1": {"type": "savings", "name": "Savings Account 1"},
    "SA2": {"type": "savings", "name": "Savings Account 2"},
    "CC1": {"type": "credit", "name": "Credit Card 1"},
    "CC2": {"type": "credit", "name": "Credit Card 2"},
    "CC3": {"type": "credit", "name": "Credit Card 3"},
}

CATEGORIES = {
    "Salary": {
        "type": "credit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (50000, 80000),
    },
    "Rent": {"type": "debit", "accounts": ["SA1"], "amount_range": (15000, 25000)},
    "Utilities": {
        "type": "debit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (500, 3000),
    },
    "Groceries": {
        "type": "debit",
        "accounts": ["SA1", "SA2", "CC1"],
        "amount_range": (500, 5000),
    },
    "Entertainment": {
        "type": "debit",
        "accounts": ["CC1", "CC2"],
        "amount_range": (200, 5000),
    },
    "Dining": {
        "type": "debit",
        "accounts": ["CC1", "CC2"],
        "amount_range": (200, 3000),
    },
    "Shopping": {
        "type": "debit",
        "accounts": ["CC1", "CC2", "CC3"],
        "amount_range": (500, 15000),
    },
    "Transport": {"type": "debit", "accounts": ["SA1"], "amount_range": (100, 2000)},
    "Medical": {
        "type": "debit",
        "accounts": ["SA1", "CC1"],
        "amount_range": (500, 10000),
    },
    "Education": {"type": "debit", "accounts": ["SA1"], "amount_range": (5000, 20000)},
    "UPI_Micro": {
        "type": "debit",
        "accounts": ["SA1", "SA2"],
        "amount_range": (10, 500),
    },
    "Transfer_SA": {
        "type": "transfer",
        "accounts": ["SA1", "SA2"],
        "amount_range": (1000, 50000),
    },
    "EMI_Payment": {
        "type": "emi",
        "accounts": ["SA1", "SA2"],
        "amount_range": (5000, 20000),
    },
    "CC_Payment": {
        "type": "cc_payment",
        "accounts": ["SA1", "SA2"],
        "amount_range": (5000, 50000),
    },
    "Debt_Injection": {
        "type": "debt",
        "accounts": ["SA1", "SA2"],
        "amount_range": (20000, 30000),
    },
}

# Platform descriptions for debt injections
DEBT_PLATFORMS = ["CRED", "SPAID", "CHEQ", "PAYTM", "PHONEPE", "BHIM UPI"]


# ============================================================
# Scenario Profiles
# ============================================================

SCENARIO_PROFILES = {
    "healthy": {
        "description": "Regular income, controlled spending, no debt cycles",
        "transaction_count": 300,
        "salary_consistency": 0.95,  # 95% on-time salary
        "spending_discipline": 0.8,  # 80% within budget
        "debt_probability": 0.0,  # No debt injections
        "micro_spend_frequency": 0.1,  # Low micro-spending
        "weekend_spike": 0.2,  # Low weekend spending spike
    },
    "debt_trap": {
        "description": "Heavy credit card usage, EMI burden, debt injections",
        "transaction_count": 400,
        "salary_consistency": 0.7,  # 70% on-time (some delays)
        "spending_discipline": 0.4,  # 40% within budget
        "debt_probability": 0.3,  # 30% chance of debt injection per month
        "micro_spend_frequency": 0.3,  # Higher micro-spending
        "weekend_spike": 0.5,  # Moderate weekend spike
    },
    "erratic": {
        "description": "Impulsive spending, irregular income, micro-transaction clusters",
        "transaction_count": 350,
        "salary_consistency": 0.5,  # 50% on-time (irregular)
        "spending_discipline": 0.2,  # 20% within budget
        "debt_probability": 0.15,  # Some debt
        "micro_spend_frequency": 0.6,  # High micro-spending
        "weekend_spike": 0.8,  # High weekend spike
    },
}


# ============================================================
# Helper Functions
# ============================================================


def clear_database(db_path: Path) -> None:
    """Clear all data from the database and ensure schema is up to date."""
    # First, initialize the database with the canonical schema to ensure all columns exist
    create_all(str(db_path))

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Disable foreign keys temporarily
    cursor.execute("PRAGMA foreign_keys = OFF")

    # Clear tables (with error handling for missing tables)
    tables_to_clear = ["reconciliations", "transactions", "statements"]
    for table in tables_to_clear:
        with contextlib.suppress(sqlite3.OperationalError):
            cursor.execute(f"DELETE FROM {table}")

    # Keep Self member
    with contextlib.suppress(sqlite3.OperationalError):
        cursor.execute("DELETE FROM members WHERE name != 'Self'")

    # Re-enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    conn.commit()
    conn.close()
    print(f"✓ Cleared existing data from {db_path}")


def generate_hash(
    account_id: str, date_iso: str, description: str, debit: int, credit: int
) -> str:
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


def generate_description(category: str, platform: str = None) -> str:
    """Generate realistic transaction description."""
    templates = {
        "Salary": ["SALARY CREDIT", "SALARY - {company}", "MONTHLY SALARY"],
        "Rent": ["RENT PAYMENT", "RENT - LANDLORD", "HOUSE RENT"],
        "Utilities": [
            "ELECTRICITY BILL",
            "WATER BILL",
            "GAS BILL",
            "INTERNET BILL",
            "MOBILE RECHARGE",
        ],
        "Groceries": [
            "GROCERY STORE",
            "SUPERMARKET",
            "DMART",
            "BIG BASKET",
            "ZEPTO",
            "BLINKIT",
        ],
        "Entertainment": [
            "NETFLIX",
            "AMAZON PRIME",
            "SPOTIFY",
            "MOVIE TICKET",
            "GAMING",
        ],
        "Dining": [
            "RESTAURANT",
            "CAFE",
            "FOOD DELIVERY",
            "SWIGGY",
            "ZOMATO",
            "DOMINOS",
        ],
        "Shopping": ["AMAZON", "FLIPKART", "MYNTRA", "AJIO", "SHOPPING MALL"],
        "Transport": ["UBER", "OLA", "METRO", "FUEL", "PETROL PUMP"],
        "Medical": [
            "MEDICINE",
            "HOSPITAL",
            "PHARMACY",
            "MEDICAL STORE",
            "HEALTH CHECKUP",
        ],
        "Education": ["TUITION FEE", "ONLINE COURSE", "BOOKS", "SCHOOL FEE"],
        "UPI_Micro": ["UPI PAYMENT", "UPI-{merchant}", "UPI TRANSFER"],
        "Transfer_SA": ["NEFT TRANSFER", "IMPS TRANSFER", "BANK TRANSFER"],
        "EMI_Payment": ["EMI - LOAN", "EMI - {bank}", "LOAN REPAYMENT"],
        "CC_Payment": ["CREDIT CARD PAYMENT", "CC PAYMENT - {card}"],
        "Debt_Injection": [f"{platform} - DEBT" if platform else "DEBT TRANSFER"],
    }

    template_list = templates.get(category, ["TRANSACTION"])
    return random.choice(template_list).format(
        company=random.choice(["TECHCORP", "INFOSYS", "TCS", "WIPRO", "STARTUP"]),
        bank=random.choice(["HDFC", "ICICI", "SBI", "AXIS", "KOTAK"]),
        card=random.choice(["CC1", "CC2", "CC3"]),
        merchant=random.choice(["MERCHANT", "SHOP", "STORE", "VENDOR"]),
        platform=platform or "PLATFORM",
    )


# ============================================================
# Transaction Generators
# ============================================================


def generate_salary_transactions(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate monthly salary transactions."""
    transactions = []
    current_month = start_date.replace(day=1)

    while current_month <= end_date:
        # Salary day (1st-5th of month)
        salary_day = random.randint(1, 5)
        salary_date = current_month.replace(day=salary_day)

        # Sometimes salary is delayed (based on consistency profile)
        if random.random() > profile["salary_consistency"]:
            salary_date += timedelta(days=random.randint(1, 10))

        if salary_date > end_date:
            break

        account = random.choice(CATEGORIES["Salary"]["accounts"])
        amount = random.randint(*CATEGORIES["Salary"]["amount_range"])

        transactions.append(
            {
                "date": salary_date,
                "account_id": account,
                "category": "Salary",
                "description": generate_description("Salary"),
                "amount": amount,
                "type": "credit",
            }
        )

        current_month += timedelta(days=32)
        current_month = current_month.replace(day=1)

    return transactions


def generate_regular_expenses(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate regular monthly expenses."""
    transactions = []

    # Rent (monthly)
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        rent_date = current_month.replace(day=random.randint(1, 5))
        if rent_date <= end_date:
            transactions.append(
                {
                    "date": rent_date,
                    "account_id": "SA1",
                    "category": "Rent",
                    "description": generate_description("Rent"),
                    "amount": random.randint(*CATEGORIES["Rent"]["amount_range"]),
                    "type": "debit",
                }
            )
        current_month += timedelta(days=32)
        current_month = current_month.replace(day=1)

    # Utilities (monthly)
    current_month = start_date.replace(day=1)
    while current_month <= end_date:
        for util in ["ELECTRICITY", "WATER", "INTERNET", "MOBILE"]:
            util_date = current_month.replace(day=random.randint(5, 15))
            if util_date <= end_date:
                transactions.append(
                    {
                        "date": util_date,
                        "account_id": random.choice(
                            CATEGORIES["Utilities"]["accounts"]
                        ),
                        "category": "Utilities",
                        "description": f"{util} BILL",
                        "amount": random.randint(300, 2000),
                        "type": "debit",
                    }
                )
        current_month += timedelta(days=32)
        current_month = current_month.replace(day=1)

    return transactions


def generate_daily_expenses(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate daily variable expenses."""
    transactions = []
    current_date = start_date

    while current_date <= end_date:
        # Weekend spike
        weekend_factor = get_weekend_factor(current_date, profile["weekend_spike"])

        # Daily spending probability
        if random.random() < 0.7 * weekend_factor:
            # Groceries
            if random.random() < 0.3:
                transactions.append(
                    {
                        "date": current_date,
                        "account_id": random.choice(
                            CATEGORIES["Groceries"]["accounts"]
                        ),
                        "category": "Groceries",
                        "description": generate_description("Groceries"),
                        "amount": random.randint(
                            *CATEGORIES["Groceries"]["amount_range"]
                        ),
                        "type": "debit",
                    }
                )

            # Dining
            if random.random() < 0.4 * weekend_factor:
                transactions.append(
                    {
                        "date": current_date,
                        "account_id": random.choice(CATEGORIES["Dining"]["accounts"]),
                        "category": "Dining",
                        "description": generate_description("Dining"),
                        "amount": random.randint(*CATEGORIES["Dining"]["amount_range"]),
                        "type": "debit",
                    }
                )

            # Entertainment
            if random.random() < 0.2 * weekend_factor:
                transactions.append(
                    {
                        "date": current_date,
                        "account_id": random.choice(
                            CATEGORIES["Entertainment"]["accounts"]
                        ),
                        "category": "Entertainment",
                        "description": generate_description("Entertainment"),
                        "amount": random.randint(
                            *CATEGORIES["Entertainment"]["amount_range"]
                        ),
                        "type": "debit",
                    }
                )

            # Shopping
            if random.random() < 0.15 * weekend_factor:
                transactions.append(
                    {
                        "date": current_date,
                        "account_id": random.choice(CATEGORIES["Shopping"]["accounts"]),
                        "category": "Shopping",
                        "description": generate_description("Shopping"),
                        "amount": random.randint(
                            *CATEGORIES["Shopping"]["amount_range"]
                        ),
                        "type": "debit",
                    }
                )

        current_date += timedelta(days=1)

    return transactions


def generate_micro_transactions(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate UPI micro-transactions."""
    transactions = []
    current_date = start_date

    while current_date <= end_date:
        # Number of micro-transactions per day
        num_micro = int(random.random() * 5 * profile["micro_spend_frequency"])

        for _ in range(num_micro):
            # Random time (including late-night)
            hour = random.randint(0, 23)
            txn_datetime = current_date.replace(hour=hour, minute=random.randint(0, 59))

            transactions.append(
                {
                    "date": txn_datetime,
                    "account_id": random.choice(CATEGORIES["UPI_Micro"]["accounts"]),
                    "category": "UPI_Micro",
                    "description": f"UPI-{random.choice(['TEA', 'SNACKS', 'AUTO', 'PARKING', 'MILK', 'NEWSPAPER'])}",
                    "amount": random.randint(*CATEGORIES["UPI_Micro"]["amount_range"]),
                    "type": "debit",
                }
            )

        current_date += timedelta(days=1)

    return transactions


def generate_transfers(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate inter-account transfers (SA1 ↔ SA2)."""
    transactions = []
    current_date = start_date

    while current_date <= end_date:
        if random.random() < 0.1:  # 10% chance per day
            amount = random.randint(*CATEGORIES["Transfer_SA"]["amount_range"])

            # Debit from one SA, credit to other
            if random.random() < 0.5:
                from_acc, to_acc = "SA1", "SA2"
            else:
                from_acc, to_acc = "SA2", "SA1"

            # Debit transaction
            transactions.append(
                {
                    "date": current_date,
                    "account_id": from_acc,
                    "category": "Transfer_SA",
                    "description": f"TRANSFER TO {to_acc}",
                    "amount": amount,
                    "type": "debit",
                }
            )

            # Credit transaction (same day or next day)
            credit_date = (
                current_date
                if random.random() < 0.7
                else current_date + timedelta(days=1)
            )
            if credit_date <= end_date:
                transactions.append(
                    {
                        "date": credit_date,
                        "account_id": to_acc,
                        "category": "Transfer_SA",
                        "description": f"TRANSFER FROM {from_acc}",
                        "amount": amount,
                        "type": "credit",
                    }
                )

        current_date += timedelta(days=1)

    return transactions


def generate_emi_payments(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate EMI payments."""
    transactions = []
    current_month = start_date.replace(day=1)

    # Create 1-3 active EMIs
    emis = [
        {
            "amount": random.randint(10000, 20000),
            "day": 5,
            "description": "HOME LOAN EMI",
        },
        {
            "amount": random.randint(5000, 15000),
            "day": 10,
            "description": "CAR LOAN EMI",
        },
        {
            "amount": random.randint(3000, 8000),
            "day": 15,
            "description": "PERSONAL LOAN EMI",
        },
    ]

    # Select EMIs based on scenario
    if profile["debt_probability"] > 0.2:
        active_emis = emis  # All EMIs for debt trap
    elif profile["debt_probability"] > 0.1:
        active_emis = random.sample(emis, 2)
    else:
        active_emis = random.sample(emis, 1)

    while current_month <= end_date:
        for emi in active_emis:
            emi_date = current_month.replace(day=emi["day"])
            if emi_date <= end_date:
                transactions.append(
                    {
                        "date": emi_date,
                        "account_id": random.choice(
                            CATEGORIES["EMI_Payment"]["accounts"]
                        ),
                        "category": "EMI_Payment",
                        "description": emi["description"],
                        "amount": emi["amount"],
                        "type": "debit",
                    }
                )

        current_month += timedelta(days=32)
        current_month = current_month.replace(day=1)

    return transactions


def generate_cc_payments(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate credit card payments from savings accounts."""
    transactions = []
    current_month = start_date.replace(day=1)

    while current_month <= end_date:
        # CC payment around 20th-25th of each month
        payment_date = current_month.replace(day=random.randint(20, 25))

        if payment_date <= end_date:
            for cc in ["CC1", "CC2", "CC3"]:
                if random.random() < 0.7:  # 70% chance to pay each card
                    amount = random.randint(*CATEGORIES["CC_Payment"]["amount_range"])

                    # Debit from SA
                    transactions.append(
                        {
                            "date": payment_date,
                            "account_id": random.choice(["SA1", "SA2"]),
                            "category": "CC_Payment",
                            "description": f"CREDIT CARD PAYMENT - {cc}",
                            "amount": amount,
                            "type": "debit",
                        }
                    )

                    # Credit to CC
                    transactions.append(
                        {
                            "date": payment_date,
                            "account_id": cc,
                            "category": "CC_Payment",
                            "description": "PAYMENT RECEIVED FROM SA",
                            "amount": amount,
                            "type": "credit",
                        }
                    )

        current_month += timedelta(days=32)
        current_month = current_month.replace(day=1)

    return transactions


def generate_debt_injections(
    start_date: datetime,
    end_date: datetime,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate debt injections from credit cards to savings accounts."""
    transactions = []
    current_month = start_date.replace(day=1)

    while current_month <= end_date:
        # Check if debt injection happens this month
        if random.random() < profile["debt_probability"]:
            # Debt injection date (usually end of month for rent/education)
            injection_date = current_month.replace(day=random.randint(25, 28))

            if injection_date <= end_date:
                amount = random.randint(*CATEGORIES["Debt_Injection"]["amount_range"])
                platform = random.choice(DEBT_PLATFORMS)
                from_cc = random.choice(["CC1", "CC2", "CC3"])
                to_sa = random.choice(["SA1", "SA2"])

                # Debit from CC (cash advance/transfer)
                transactions.append(
                    {
                        "date": injection_date,
                        "account_id": from_cc,
                        "category": "Debt_Injection",
                        "description": f"{platform} - DEBT TRANSFER",
                        "amount": amount,
                        "type": "debit",
                    }
                )

                # Credit to SA
                transactions.append(
                    {
                        "date": injection_date,
                        "account_id": to_sa,
                        "category": "Debt_Injection",
                        "description": f"{platform} - CREDIT",
                        "amount": amount,
                        "type": "credit",
                    }
                )

        current_month += timedelta(days=32)
        current_month = current_month.replace(day=1)

    return transactions


# ============================================================
# Main Generator
# ============================================================


def generate_scenario(scenario_name: str, db_path: Path) -> dict[str, Any]:
    """Generate a complete scenario dataset."""
    profile = SCENARIO_PROFILES[scenario_name]
    print(f"\n{'=' * 60}")
    print(f"Generating '{scenario_name}' scenario: {profile['description']}")
    print(f"{'=' * 60}")

    # Date range: 8 months
    start_date = datetime(2025, 1, 1)
    end_date = datetime(2025, 8, 31)

    all_transactions = []

    # Generate all transaction types
    print("  Generating salary transactions...")
    all_transactions.extend(generate_salary_transactions(start_date, end_date, profile))

    print("  Generating regular expenses...")
    all_transactions.extend(generate_regular_expenses(start_date, end_date, profile))

    print("  Generating daily expenses...")
    all_transactions.extend(generate_daily_expenses(start_date, end_date, profile))

    print("  Generating micro-transactions...")
    all_transactions.extend(generate_micro_transactions(start_date, end_date, profile))

    print("  Generating transfers...")
    all_transactions.extend(generate_transfers(start_date, end_date, profile))

    print("  Generating EMI payments...")
    all_transactions.extend(generate_emi_payments(start_date, end_date, profile))

    print("  Generating CC payments...")
    all_transactions.extend(generate_cc_payments(start_date, end_date, profile))

    print("  Generating debt injections...")
    all_transactions.extend(generate_debt_injections(start_date, end_date, profile))

    # Sort by date
    all_transactions.sort(key=lambda x: x["date"])

    # Insert into database
    print(f"\n  Inserting {len(all_transactions)} transactions into database...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    inserted = 0

    # Create statements for each account
    statement_ids = {}
    for account_id in ACCOUNTS:
        cursor.execute(
            """
            INSERT INTO statements (bank, file_name, source)
            VALUES (?, ?, ?)
        """,
            (account_id, f"synthetic_{scenario_name}_{account_id}", "synthetic"),
        )
        statement_ids[account_id] = cursor.lastrowid

    # Insert transactions
    for txn in all_transactions:
        date_iso = txn["date"].strftime("%Y-%m-%d")
        date_str = txn["date"].strftime("%d/%m/%Y")

        amount_paise = int(txn["amount"] * 100)
        debit = amount_paise if txn["type"] == "debit" else 0
        credit = amount_paise if txn["type"] == "credit" else 0

        hash_sig = generate_hash(
            txn["account_id"], date_iso, txn["description"], debit, credit
        )

        try:
            cursor.execute(
                """
                INSERT INTO transactions (
                    statement_id, date, date_iso, description, type,
                    category, debit, credit, amount_paise, hash_signature, account_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    statement_ids[txn["account_id"]],
                    date_str,
                    date_iso,
                    txn["description"],
                    txn["type"],
                    txn["category"],
                    debit,
                    credit,
                    amount_paise,
                    hash_sig,
                    txn["account_id"],
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass  # Duplicate hash, skip

    conn.commit()
    conn.close()

    stats = {
        "scenario": scenario_name,
        "total_generated": len(all_transactions),
        "inserted": inserted,
        "duplicates": len(all_transactions) - inserted,
    }

    print(
        f"  ✓ Inserted {inserted} transactions ({len(all_transactions) - inserted} duplicates skipped)"
    )

    return stats


# ============================================================
# CLI Entry Point
# ============================================================


def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic transaction data for ClariFin_OS"
    )
    parser.add_argument(
        "--scenario",
        choices=["healthy", "debt_trap", "erratic", "all"],
        default="debt_trap",
        help="Scenario to generate (default: debt_trap)",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="Keep existing data (don't clear database)",
    )

    args = parser.parse_args()

    print(f"\n{'#' * 60}")
    print("# ClariFin_OS Synthetic Data Generator")
    print(f"{'#' * 60}")
    print(f"\nDatabase: {DB_PATH}")

    # Clear database
    if not args.keep_existing:
        clear_database(DB_PATH)

    # Generate scenarios
    if args.scenario == "all":
        scenarios = ["healthy", "debt_trap", "erratic"]
        # For "all", we generate sequentially (will need separate DBs or clear between)
        print("\nNote: 'all' scenario generates each scenario sequentially.")
        print("Each scenario clears the previous data.\n")

        all_stats = []
        for scenario in scenarios:
            clear_database(DB_PATH)
            stats = generate_scenario(scenario, DB_PATH)
            all_stats.append(stats)

            # Run validation
            print(f"\n  Validating {scenario} scenario...")
            # Could add validation here

        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        for stats in all_stats:
            print(f"  {stats['scenario']}: {stats['inserted']} transactions")
    else:
        stats = generate_scenario(args.scenario, DB_PATH)

        print(f"\n{'=' * 60}")
        print("SUMMARY")
        print(f"{'=' * 60}")
        print(f"  Scenario: {stats['scenario']}")
        print(f"  Total generated: {stats['total_generated']}")
        print(f"  Inserted: {stats['inserted']}")
        print(f"  Duplicates skipped: {stats['duplicates']}")

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
