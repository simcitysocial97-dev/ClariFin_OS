"""M9-C29 — Deterministic contract-wire fixture.

Produces a minimal, non-zero test dataset seeded into an isolated SQLite DB
so that semantic value contracts (savings_rate, emi_ratio ranges) are actually
exercised during wire validation.

The fixture is owned by the contract verifier and does NOT depend on Playwright,
E2E state, or any external seeding mechanism.
"""

from __future__ import annotations

import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def seed_contract_fixture(db_path: str) -> None:
    """Seed a deterministic fixture into the given database path.

    Produces:
    - One statement for the current month
    - One credit transaction (income = 10,00,000 paise = ₹10,000)
    - Two debit transactions (expenses = 5,00,000 + 2,50,000 = 7,50,000 paise = ₹7,500)
    - One loan with EMI to test emi_ratio semantics

    Expected dashboard summary:
    - savings_rate = 0.25  (net 2,50,000 / income 10,00,000)
    - emi_ratio > 0        (loan EMI present for semantic validation)
    """
    from src.core.db.schema import create_all, run_migrations
    from src.repositories.statement_repository import StatementRepository
    from src.repositories.transaction_repository import TransactionRepository
    from src.repositories.loan_repository import LoanRepository

    create_all(db_path)
    run_migrations(db_path)

    stmt_repo = StatementRepository(db_path)
    txn_repo = TransactionRepository(db_path)
    loan_repo = LoanRepository(db_path)

    today = datetime.date.today().isoformat()

    # Insert one statement
    statement_id = stmt_repo.insert_statement(
        bank="ContractFixtureBank",
        file_name="contract-wire-fixture.csv",
        period_from=today,
        period_to=today,
    )

    # Income: 10,000 rupees = 10,000,000 paise
    # Expenses: 7,500 rupees = 7,500,000 paise
    # Net: 2,500 rupees → savings_rate = 0.25
    transactions = [
        {
            "amount_paise": 10000000,
            "type": "credit",
            "category": "Salary",
            "date": today,
            "description": "Monthly salary",
        },
        {
            "amount_paise": 5000000,
            "type": "debit",
            "category": "Rent",
            "date": today,
            "description": "Monthly rent",
        },
        {
            "amount_paise": 2500000,
            "type": "debit",
            "category": "Food",
            "date": today,
            "description": "Groceries",
        },
    ]
    txn_repo.insert_transactions(statement_id, transactions)

    # Insert a loan to produce non-zero emi_ratio for semantic validation
    loan_id = loan_repo.create_loan(
        name="Home Loan",
        lender="State Bank",
        loan_type="home",
        principal_paise=500000000,  # ₹5,00,000
        outstanding_paise=450000000,  # ₹4,50,000 remaining
        interest_rate=8.5,
        tenure_months=240,
        emi_paise=4500000,  # ₹45,000 EMI monthly
        disbursed_date="2025-01-01",
    )

    return loan_id  # type: ignore[return-value]
