"""
Test Data Generator for ClariFin
=================================
Populates database with realistic Indian financial data for testing.
Run: python3 -m tests.generate_test_data [db_path]
"""

import hashlib
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db import FinanceDB
from src.logger import log


# ============================================================
# Configuration
# ============================================================

# Fixed seed for reproducibility
random.seed(42)

# Account definitions
ACCOUNTS = [
    {
        "name": "HDFC Savings",
        "bank_name": "HDFC Bank",
        "account_type": "savings",
        "account_number_masked": "1234",
        "balance_paise": 2_45_000 * 100,  # ₹2,45,000
        "color": "#004C8F",
        "icon": "building",
    },
    {
        "name": "SBI Salary Account",
        "bank_name": "State Bank of India",
        "account_type": "savings",
        "account_number_masked": "5678",
        "balance_paise": 1_87_500 * 100,  # ₹1,87,500
        "color": "#1E4D8C",
        "icon": "building",
    },
    {
        "name": "ICICI Credit Card",
        "bank_name": "ICICI Bank",
        "account_type": "credit_card",
        "account_number_masked": "9012",
        "balance_paise": -32_000 * 100,  # -₹32,000 (outstanding)
        "credit_limit_paise": 2_00_000 * 100,  # ₹2,00,000 limit
        "color": "#C41E3A",
        "icon": "credit-card",
    },
    {
        "name": "Kotak Current",
        "bank_name": "Kotak Mahindra Bank",
        "account_type": "current",
        "account_number_masked": "3456",
        "balance_paise": 5_12_000 * 100,  # ₹5,12,000
        "color": "#FF6B00",
        "icon": "building",
    },
    {
        "name": "Paytm Wallet",
        "bank_name": "Paytm Payments Bank",
        "account_type": "wallet",
        "account_number_masked": "7890",
        "balance_paise": 3_200 * 100,  # ₹3,200
        "color": "#00B9F1",
        "icon": "wallet",
    },
]

# Income source definitions
INCOME_SOURCES = [
    {
        "name": "Monthly Salary",
        "type": "salary",
        "amount_paise": 75_000 * 100,  # ₹75,000/month
        "frequency": "monthly",
        "is_active": 1,
        "notes": "Primary salary from employer",
    },
    {
        "name": "Freelance Projects",
        "type": "freelance",
        "amount_paise": 15_000 * 100,  # ₹15,000/month average
        "frequency": "irregular",
        "is_active": 1,
        "notes": "Freelance development work",
    },
    {
        "name": "FD Interest",
        "type": "interest",
        "amount_paise": 4_500 * 100,  # ₹4,500/quarterly
        "frequency": "quarterly",
        "is_active": 1,
        "notes": "Fixed deposit interest",
    },
]

# Loan definitions
LOANS = [
    {
        "name": "Home Loan",
        "lender": "HDFC Ltd",
        "loan_type": "home",
        "principal_paise": 45_00_000 * 100,  # ₹45,00,000
        "outstanding_paise": 38_50_000 * 100,  # ₹38,50,000
        "interest_rate": 8.5,
        "emi_paise": 38_965 * 100,  # ₹38,965
        "tenure_months": 240,  # 20 years
        "start_date": "2022-01-01",
        "status": "active",
        "notes": "Home loan for apartment",
    },
    {
        "name": "Car Loan",
        "lender": "SBI",
        "loan_type": "car",
        "principal_paise": 8_00_000 * 100,  # ₹8,00,000
        "outstanding_paise": 5_20_000 * 100,  # ₹5,20,000
        "interest_rate": 9.5,
        "emi_paise": 16_789 * 100,  # ₹16,789
        "tenure_months": 60,  # 5 years
        "start_date": "2023-06-01",
        "status": "active",
        "notes": "Car loan for SUV",
    },
]

# Investment definitions
INVESTMENTS = [
    {
        "name": "NIFTY 50 Index Fund",
        "type": "mutual_fund",
        "platform": "Zerodha",
        "invested_paise": 3_50_000 * 100,  # ₹3,50,000
        "current_value_paise": 4_12_000 * 100,  # ₹4,12,000
        "units": 100.5,
        "purchase_date": "2023-01-15",
        "is_active": 1,
        "notes": "Long term equity investment",
    },
    {
        "name": "HDFC Fixed Deposit",
        "type": "fd",
        "platform": "HDFC Bank",
        "invested_paise": 2_00_000 * 100,  # ₹2,00,000
        "current_value_paise": 2_14_000 * 100,  # ₹2,14,000
        "purchase_date": "2024-01-01",
        "maturity_date": "2027-01-01",
        "is_active": 1,
        "notes": "3-year FD at 7% interest",
    },
    {
        "name": "Public Provident Fund",
        "type": "ppf",
        "platform": "SBI",
        "invested_paise": 1_50_000 * 100,  # ₹1,50,000
        "current_value_paise": 1_65_000 * 100,  # ₹1,65,000
        "purchase_date": "2020-04-01",
        "is_active": 1,
        "notes": "PPF account",
    },
    {
        "name": "Sovereign Gold Bonds",
        "type": "gold",
        "platform": "RBI",
        "invested_paise": 50_000 * 100,  # ₹50,000
        "current_value_paise": 58_000 * 100,  # ₹58,000
        "units": 10,
        "purchase_date": "2023-11-01",
        "is_active": 1,
        "notes": "SGB 2023-24 Series",
    },
]

# Recurring transaction definitions
RECURRING_TRANSACTIONS = [
    {
        "description": "Netflix Subscription",
        "amount_paise": 649 * 100,  # ₹649/month
        "type": "debit",
        "category": "Entertainment",
        "frequency": "monthly",
        "is_active": 1,
        "notes": "Netflix Standard Plan",
    },
    {
        "description": "Gold's Gym Membership",
        "amount_paise": 2_000 * 100,  # ₹2,000/month
        "type": "debit",
        "category": "Health & Fitness",
        "frequency": "monthly",
        "is_active": 1,
        "notes": "Monthly gym membership",
    },
    {
        "description": "SIP - NIFTY 50 Index Fund",
        "amount_paise": 10_000 * 100,  # ₹10,000/month
        "type": "debit",
        "category": "Investment",
        "frequency": "monthly",
        "is_active": 1,
        "notes": "Monthly SIP",
    },
    {
        "description": "Home Loan EMI",
        "amount_paise": 38_965 * 100,  # ₹38,965/month
        "type": "debit",
        "category": "Loan EMI",
        "frequency": "monthly",
        "is_active": 1,
        "notes": "Auto-debited from HDFC account",
    },
    {
        "description": "Car Loan EMI",
        "amount_paise": 16_789 * 100,  # ₹16,789/month
        "type": "debit",
        "category": "Loan EMI",
        "frequency": "monthly",
        "is_active": 1,
        "notes": "Auto-debited from SBI account",
    },
]

# Transaction pattern definitions
MERCHANTS = {
    "food_delivery": [
        ("Swiggy", 150, 800),
        ("Zomato", 200, 750),
        ("Swiggy Instamart", 300, 600),
    ],
    "ecommerce": [
        ("Amazon India", 500, 5000),
        ("Flipkart", 400, 4500),
        ("Myntra", 800, 3000),
    ],
    "fuel": [
        ("Indian Oil Petrol Pump", 1500, 2500),
        ("HPCL Petrol Station", 1600, 2400),
        ("BPCL Fuel Station", 1500, 2300),
    ],
    "utilities": [
        ("Tata Power Electricity", 1200, 2800),
        ("BESCOM Electricity Bill", 1100, 2600),
        ("Airtel Broadband", 999, 999),
        ("Jio Fiber", 699, 699),
    ],
    "phone": [
        ("Airtel Prepaid Recharge", 599, 999),
        ("Jio Recharge", 399, 899),
        ("Vi Prepaid", 459, 799),
    ],
    "upi": [
        ("UPI Transfer to Rahul", 500, 5000),
        ("UPI Transfer to Priya", 1000, 10000),
        ("UPI Payment to Ramesh", 200, 5000),
        ("PhonePe Transfer", 100, 3000),
        ("Google Pay Transfer", 500, 8000),
    ],
    "atm": [
        ("ATM Withdrawal - HDFC", 2000, 10000),
        ("ATM Withdrawal - SBI", 5000, 20000),
        ("Cash Withdrawal", 3000, 15000),
    ],
    "misc": [
        ("Apollo Pharmacy", 200, 1500),
        ("MedPlus", 300, 2000),
        ("BigBasket", 800, 3500),
        ("Blinkit", 400, 2000),
        ("Uber Ride", 150, 800),
        ("Ola Cab", 120, 900),
        ("BookMyShow", 300, 1500),
        ("Spotify", 199, 199),
    ],
}


def generate_date_range(months: int = 6) -> list:
    """Generate a list of dates spanning the last N months."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30 * months)
    
    dates = []
    current = start_date
    while current <= end_date:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates


def format_date_ddmmyyyy(date: datetime) -> str:
    """Format date as DD/MM/YYYY."""
    return date.strftime("%d/%m/%Y")


def format_date_iso(date: datetime) -> str:
    """Format date as YYYY-MM-DD."""
    return date.strftime("%Y-%m-%d")


def rupees_to_paise(rupees: float) -> int:
    """Convert rupees to paise."""
    return int(round(rupees * 100))


def compute_hash_signature(account_id: str, date_iso: str, description: str, 
                           debit_paise: int, credit_paise: int) -> str:
    """Compute deterministic hash signature for a transaction."""
    hash_input = f"{account_id}|{date_iso}|{description}|{debit_paise}|{debit_paise}"
    return hashlib.sha256(hash_input.encode()).hexdigest().lower()


def create_accounts(db: FinanceDB) -> dict:
    """Create accounts and return mapping of name to ID."""
    account_ids = {}
    
    for account_data in ACCOUNTS:
        account_id = db.create_account(account_data)
        account_ids[account_data["name"]] = account_id
        log.info("Created account: %s (ID: %d)", account_data["name"], account_id)
    
    return account_ids


def create_income_sources(db: FinanceDB, account_ids: dict) -> list:
    """Create income sources and return list of IDs."""
    source_ids = []
    
    # Map income sources to accounts
    account_mapping = {
        "Monthly Salary": account_ids.get("SBI Salary Account"),
        "Freelance Projects": account_ids.get("HDFC Savings"),
        "FD Interest": account_ids.get("HDFC Savings"),
    }
    
    for source_data in INCOME_SOURCES:
        source_data["account_id"] = account_mapping.get(source_data["name"])
        source_id = db.insert_income_source(source_data)
        source_ids.append(source_id)
        log.info("Created income source: %s (ID: %d)", source_data["name"], source_id)
    
    return source_ids


def create_loans(db: FinanceDB, account_ids: dict) -> dict:
    """Create loans and return mapping of name to ID."""
    loan_ids = {}
    
    # Map loans to accounts for EMI payments
    account_mapping = {
        "Home Loan": account_ids.get("HDFC Savings"),
        "Car Loan": account_ids.get("SBI Salary Account"),
    }
    
    for loan_data in LOANS:
        loan_data["linked_account_id"] = account_mapping.get(loan_data["name"])
        loan_id = db.insert_loan(loan_data)
        loan_ids[loan_data["name"]] = loan_id
        log.info("Created loan: %s (ID: %d)", loan_data["name"], loan_id)
    
    return loan_ids


def create_loan_payments(db: FinanceDB, loan_ids: dict):
    """Create loan payment records for the last 6 months."""
    today = datetime.now()
    
    for loan_name, loan_id in loan_ids.items():
        loan_data = next((l for l in LOANS if l["name"] == loan_name), None)
        if not loan_data:
            continue
        
        emi_paise = loan_data["emi_paise"]
        # Simplified: 70% principal, 30% interest (approximate for demonstration)
        principal_component = int(emi_paise * 0.7)
        interest_component = emi_paise - principal_component
        
        # Create 6 months of payments
        for i in range(6, 0, -1):
            payment_date = today - timedelta(days=30 * i)
            remaining = loan_data["outstanding_paise"] + (principal_component * i)
            
            payment_data = {
                "loan_id": loan_id,
                "transaction_id": None,  # Not linked to a specific transaction
                "principal_component_paise": principal_component,
                "interest_component_paise": interest_component,
                "payment_date": format_date_iso(payment_date),
                "remaining_principal_paise": remaining,
            }
            
            db.insert_loan_payment(payment_data)
        
        log.info("Created 6 payments for loan: %s", loan_name)


def create_investments(db: FinanceDB, account_ids: dict) -> list:
    """Create investments and return list of IDs."""
    investment_ids = []
    
    # Map investments to accounts
    account_mapping = {
        "NIFTY 50 Index Fund": account_ids.get("HDFC Savings"),
        "HDFC Fixed Deposit": account_ids.get("HDFC Savings"),
        "Public Provident Fund": account_ids.get("SBI Salary Account"),
        "Sovereign Gold Bonds": account_ids.get("HDFC Savings"),
    }
    
    for inv_data in INVESTMENTS:
        inv_data["linked_account_id"] = account_mapping.get(inv_data["name"])
        inv_id = db.insert_investment(inv_data)
        investment_ids.append(inv_id)
        log.info("Created investment: %s (ID: %d)", inv_data["name"], inv_id)
    
    return investment_ids


def create_recurring_transactions(db: FinanceDB, account_ids: dict) -> list:
    """Create recurring transactions and return list of IDs."""
    recurring_ids = []
    
    # Map recurring to accounts (using description as key)
    account_mapping = {
        "Netflix Subscription": str(account_ids.get("ICICI Credit Card")),
        "Gold's Gym Membership": str(account_ids.get("HDFC Savings")),
        "SIP - NIFTY 50 Index Fund": str(account_ids.get("HDFC Savings")),
        "Home Loan EMI": str(account_ids.get("HDFC Savings")),
        "Car Loan EMI": str(account_ids.get("SBI Salary Account")),
    }
    
    today = datetime.now()
    
    for rec_data in RECURRING_TRANSACTIONS:
        rec_data["account_id"] = account_mapping.get(rec_data["description"])
        rec_data["next_due_date"] = format_date_iso(today + timedelta(days=5))
        rec_data["last_detected_date"] = format_date_iso(today - timedelta(days=25))
        rec_data["occurrence_count"] = random.randint(6, 24)
        
        rec_id = db.insert_recurring_transaction(rec_data)
        recurring_ids.append(rec_id)
        log.info("Created recurring: %s (ID: %d)", rec_data["description"], rec_id)
    
    return recurring_ids


def generate_transactions(db: FinanceDB, account_ids: dict, months: int = 6) -> int:
    """Generate realistic transactions for the specified period."""
    transactions = []
    today = datetime.now()
    
    # Get account IDs for easy reference
    hdfc_id = account_ids.get("HDFC Savings")
    sbi_id = account_ids.get("SBI Salary Account")
    icici_id = account_ids.get("ICICI Credit Card")
    kotak_id = account_ids.get("Kotak Current")
    paytm_id = account_ids.get("Paytm Wallet")
    
    # Account ID to bank name mapping for hash computation
    account_banks = {
        hdfc_id: "HDFC Bank",
        sbi_id: "State Bank of India",
        icici_id: "ICICI Bank",
        kotak_id: "Kotak Mahindra Bank",
        paytm_id: "Paytm Payments Bank",
    }
    
    # Generate monthly transactions
    for month_offset in range(months, -1, -1):
        month_date = today - timedelta(days=30 * month_offset)
        
        # 1. Salary credit on 1st of month (SBI account)
        salary_date = month_date.replace(day=1)
        if salary_date <= today:
            transactions.append({
                "date": format_date_ddmmyyyy(salary_date),
                "date_iso": format_date_iso(salary_date),
                "description": "Salary Credit - Employer",
                "amount": 75_000.0,
                "type": "credit",
                "category": "Income",
                "account_id": sbi_id,
                "bank": account_banks[sbi_id],
            })
        
        # 2. Rent debit on 5th of month (HDFC account)
        rent_date = month_date.replace(day=5)
        if rent_date <= today:
            transactions.append({
                "date": format_date_ddmmyyyy(rent_date),
                "date_iso": format_date_iso(rent_date),
                "description": "Rent Payment to Landlord",
                "amount": 18_000.0,
                "type": "debit",
                "category": "Housing",
                "account_id": hdfc_id,
                "bank": account_banks[hdfc_id],
            })
        
        # 3. Food delivery (8-12 per month)
        num_food = random.randint(8, 12)
        for _ in range(num_food):
            day = random.randint(1, 28)
            txn_date = month_date.replace(day=day)
            if txn_date <= today:
                merchant, min_amt, max_amt = random.choice(MERCHANTS["food_delivery"])
                amount = round(random.uniform(min_amt, max_amt), 2)
                transactions.append({
                    "date": format_date_ddmmyyyy(txn_date),
                    "date_iso": format_date_iso(txn_date),
                    "description": f"{merchant} Order",
                    "amount": amount,
                    "type": "debit",
                    "category": "Food & Dining",
                    "account_id": random.choice([hdfc_id, icici_id, paytm_id]),
                    "bank": account_banks.get(random.choice([hdfc_id, icici_id, paytm_id])),
                })
        
        # 4. E-commerce (2-3 per month)
        num_ecom = random.randint(2, 3)
        for _ in range(num_ecom):
            day = random.randint(1, 28)
            txn_date = month_date.replace(day=day)
            if txn_date <= today:
                merchant, min_amt, max_amt = random.choice(MERCHANTS["ecommerce"])
                amount = round(random.uniform(min_amt, max_amt), 2)
                transactions.append({
                    "date": format_date_ddmmyyyy(txn_date),
                    "date_iso": format_date_iso(txn_date),
                    "description": f"{merchant} Purchase",
                    "amount": amount,
                    "type": "debit",
                    "category": "Shopping",
                    "account_id": random.choice([hdfc_id, icici_id]),
                    "bank": account_banks.get(random.choice([hdfc_id, icici_id])),
                })
        
        # 5. Petrol (4 per month)
        for _ in range(4):
            day = random.randint(1, 28)
            txn_date = month_date.replace(day=day)
            if txn_date <= today:
                merchant, min_amt, max_amt = random.choice(MERCHANTS["fuel"])
                amount = round(random.uniform(min_amt, max_amt), 2)
                transactions.append({
                    "date": format_date_ddmmyyyy(txn_date),
                    "date_iso": format_date_iso(txn_date),
                    "description": merchant,
                    "amount": amount,
                    "type": "debit",
                    "category": "Transportation",
                    "account_id": random.choice([hdfc_id, icici_id]),
                    "bank": account_banks.get(random.choice([hdfc_id, icici_id])),
                })
        
        # 6. Electricity bill (1 per month)
        elec_day = random.randint(10, 25)
        elec_date = month_date.replace(day=elec_day)
        if elec_date <= today:
            merchant, min_amt, max_amt = random.choice([m for m in MERCHANTS["utilities"] if "Electricity" in m[0]])
            amount = round(random.uniform(min_amt, max_amt), 2)
            transactions.append({
                "date": format_date_ddmmyyyy(elec_date),
                "date_iso": format_date_iso(elec_date),
                "description": merchant,
                "amount": amount,
                "type": "debit",
                "category": "Utilities",
                "account_id": hdfc_id,
                "bank": account_banks[hdfc_id],
            })
        
        # 7. Phone recharge (1 per month)
        phone_day = random.randint(1, 28)
        phone_date = month_date.replace(day=phone_day)
        if phone_date <= today:
            merchant, min_amt, max_amt = random.choice(MERCHANTS["phone"])
            amount = round(random.uniform(min_amt, max_amt), 2)
            transactions.append({
                "date": format_date_ddmmyyyy(phone_date),
                "date_iso": format_date_iso(phone_date),
                "description": merchant,
                "amount": amount,
                "type": "debit",
                "category": "Utilities",
                "account_id": random.choice([hdfc_id, paytm_id]),
                "bank": account_banks.get(random.choice([hdfc_id, paytm_id])),
            })
        
        # 8. UPI transfers (5-8 per month)
        num_upi = random.randint(5, 8)
        for _ in range(num_upi):
            day = random.randint(1, 28)
            txn_date = month_date.replace(day=day)
            if txn_date <= today:
                merchant, min_amt, max_amt = random.choice(MERCHANTS["upi"])
                amount = round(random.uniform(min_amt, max_amt), 2)
                transactions.append({
                    "date": format_date_ddmmyyyy(txn_date),
                    "date_iso": format_date_iso(txn_date),
                    "description": merchant,
                    "amount": amount,
                    "type": "debit",
                    "category": "Transfer",
                    "account_id": random.choice([hdfc_id, sbi_id, paytm_id]),
                    "bank": account_banks.get(random.choice([hdfc_id, sbi_id, paytm_id])),
                })
        
        # 9. ATM withdrawals (2-3 per month)
        num_atm = random.randint(2, 3)
        for _ in range(num_atm):
            day = random.randint(1, 28)
            txn_date = month_date.replace(day=day)
            if txn_date <= today:
                merchant, min_amt, max_amt = random.choice(MERCHANTS["atm"])
                amount = round(random.uniform(min_amt, max_amt), 2)
                transactions.append({
                    "date": format_date_ddmmyyyy(txn_date),
                    "date_iso": format_date_iso(txn_date),
                    "description": merchant,
                    "amount": amount,
                    "type": "debit",
                    "category": "Cash Withdrawal",
                    "account_id": random.choice([hdfc_id, sbi_id]),
                    "bank": account_banks.get(random.choice([hdfc_id, sbi_id])),
                })
        
        # 10. Insurance premium (1 per quarter)
        if month_date.month in [1, 4, 7, 10]:
            ins_day = random.randint(1, 10)
            ins_date = month_date.replace(day=ins_day)
            if ins_date <= today:
                transactions.append({
                    "date": format_date_ddmmyyyy(ins_date),
                    "date_iso": format_date_iso(ins_date),
                    "description": "LIC Insurance Premium",
                    "amount": 8_000.0,
                    "type": "debit",
                    "category": "Insurance",
                    "account_id": hdfc_id,
                    "bank": account_banks[hdfc_id],
                })
        
        # 11. Miscellaneous (3-5 per month)
        num_misc = random.randint(3, 5)
        for _ in range(num_misc):
            day = random.randint(1, 28)
            txn_date = month_date.replace(day=day)
            if txn_date <= today:
                merchant, min_amt, max_amt = random.choice(MERCHANTS["misc"])
                amount = round(random.uniform(min_amt, max_amt), 2)
                category = "Shopping"
                if "Pharmacy" in merchant or "MedPlus" in merchant:
                    category = "Healthcare"
                elif "Basket" in merchant or "Blinkit" in merchant:
                    category = "Groceries"
                elif "Uber" in merchant or "Ola" in merchant:
                    category = "Transportation"
                elif "BookMyShow" in merchant or "Spotify" in merchant:
                    category = "Entertainment"
                
                transactions.append({
                    "date": format_date_ddmmyyyy(txn_date),
                    "date_iso": format_date_iso(txn_date),
                    "description": merchant,
                    "amount": amount,
                    "type": "debit",
                    "category": category,
                    "account_id": random.choice([hdfc_id, icici_id, paytm_id]),
                    "bank": account_banks.get(random.choice([hdfc_id, icici_id, paytm_id])),
                })
    
    # Sort transactions by date
    transactions.sort(key=lambda x: x["date_iso"])
    
    # Create statements and insert transactions
    statement_ids = {}
    inserted_count = 0
    
    # Group transactions by account and month for statements
    for txn in transactions:
        account_id = txn["account_id"]
        month_key = txn["date_iso"][:7]  # YYYY-MM
        bank_name = txn["bank"]
        
        statement_key = (account_id, month_key)
        if statement_key not in statement_ids:
            # Create a new statement
            stmt_id = db.insert_statement(
                bank=bank_name,
                file_name=f"statement_{bank_name.replace(' ', '_')}_{month_key}.pdf",
                period_from=f"01/{month_key[5:7]}/{month_key[:4]}",
                period_to=f"28/{month_key[5:7]}/{month_key[:4]}",
            )
            statement_ids[statement_key] = stmt_id
        
        # Prepare transaction for insertion
        stmt_id = statement_ids[statement_key]
        amount = txn["amount"]
        txn_type = txn["type"]
        amount_paise = rupees_to_paise(amount)
        debit_paise = amount_paise if txn_type == "debit" else 0
        credit_paise = amount_paise if txn_type == "credit" else 0
        
        # Compute hash signature
        hash_sig = compute_hash_signature(
            bank_name,
            txn["date_iso"],
            txn["description"],
            debit_paise,
            credit_paise
        )
        
        # Insert transaction
        with db.transaction() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO transactions
                    (statement_id, date, description, amount, type, category,
                     debit, credit, amount_paise, date_iso, hash_signature, account_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stmt_id,
                    txn["date"],
                    txn["description"],
                    amount,
                    txn_type,
                    txn["category"],
                    debit_paise,
                    credit_paise,
                    amount_paise,
                    txn["date_iso"],
                    hash_sig,
                    bank_name,
                ),
            )
            if cur.rowcount > 0:
                inserted_count += 1
    
    log.info("Inserted %d transactions", inserted_count)
    return inserted_count


def populate_test_data(db: FinanceDB, months: int = 6) -> dict:
    """
    Populate the database with comprehensive test data.
    
    Args:
        db: FinanceDB instance
        months: Number of months of transaction history to generate
    
    Returns:
        Dictionary with counts of created entities
    """
    log.info("Starting test data generation...")
    
    # 1. Create accounts
    account_ids = create_accounts(db)
    
    # 2. Create income sources
    source_ids = create_income_sources(db, account_ids)
    
    # 3. Create loans
    loan_ids = create_loans(db, account_ids)
    
    # 4. Create loan payments
    create_loan_payments(db, loan_ids)
    
    # 5. Create investments
    investment_ids = create_investments(db, account_ids)
    
    # 6. Create recurring transactions
    recurring_ids = create_recurring_transactions(db, account_ids)
    
    # 7. Generate transactions
    txn_count = generate_transactions(db, account_ids, months)
    
    # Get final counts
    stats = {
        "accounts": len(account_ids),
        "income_sources": len(source_ids),
        "loans": len(loan_ids),
        "investments": len(investment_ids),
        "recurring": len(recurring_ids),
        "transactions": txn_count,
    }
    
    log.info("Test data generation complete: %s", stats)
    return stats


def print_summary(db: FinanceDB):
    """Print summary statistics of the populated database."""
    print("\n" + "=" * 60)
    print("TEST DATA SUMMARY")
    print("=" * 60)
    
    # Get counts from database
    accounts = db.get_accounts(include_inactive=True)
    loans = db.get_loans()
    investments = db.get_investments(active_only=False)
    income_sources = db.get_income_sources(active_only=False)
    recurring = db.get_recurring_transactions(active_only=False)
    txn_count = db.get_transaction_count()
    
    print(f"\nAccounts: {len(accounts)}")
    for acc in accounts:
        balance = acc.get("balance_paise", 0) / 100
        print(f"  - {acc['name']}: ₹{balance:,.2f}")
    
    print(f"\nIncome Sources: {len(income_sources)}")
    for src in income_sources:
        amount = src.get("amount_paise", 0) / 100
        print(f"  - {src['name']}: ₹{amount:,.2f} ({src['frequency']})")
    
    print(f"\nLoans: {len(loans)}")
    for loan in loans:
        outstanding = loan.get("outstanding_paise", 0) / 100
        emi = loan.get("emi_paise", 0) / 100
        print(f"  - {loan['name']}: Outstanding ₹{outstanding:,.2f}, EMI ₹{emi:,.2f}")
    
    print(f"\nInvestments: {len(investments)}")
    for inv in investments:
        invested = inv.get("invested_paise", 0) / 100
        current = inv.get("current_value_paise", 0) / 100
        gain = current - invested
        print(f"  - {inv['name']}: ₹{current:,.2f} (Gain: ₹{gain:,.2f})")
    
    print(f"\nRecurring Transactions: {len(recurring)}")
    for rec in recurring:
        amount = rec.get("amount_paise", 0) / 100
        print(f"  - {rec['description']}: ₹{amount:,.2f} ({rec['frequency']})")
    
    print(f"\nTransactions: {txn_count}")
    
    # Get category breakdown
    categories = db.get_category_summary()
    if categories:
        print("\nTop Categories:")
        for cat in categories[:5]:
            print(f"  - {cat['category']}: ₹{cat['total_amount']:,.2f} ({cat['count']} txns)")
    
    print("\n" + "=" * 60)


def main():
    """Main entry point for standalone execution."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate test data for ClariFin")
    parser.add_argument(
        "db_path",
        nargs="?",
        default="test.db",
        help="Path to the database file (default: test.db)"
    )
    parser.add_argument(
        "--months",
        type=int,
        default=6,
        help="Number of months of transaction history (default: 6)"
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Delete existing database if it exists"
    )
    
    args = parser.parse_args()
    
    # Handle fresh flag
    db_path = Path(args.db_path)
    if args.fresh and db_path.exists():
        db_path.unlink()
        print(f"Deleted existing database: {db_path}")
    
    # Create database and populate
    db = FinanceDB(str(db_path))
    try:
        stats = populate_test_data(db, months=args.months)
        print_summary(db)
        print(f"\nDatabase created at: {db_path.absolute()}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
