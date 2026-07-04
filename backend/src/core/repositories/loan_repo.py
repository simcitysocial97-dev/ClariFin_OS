"""Loan Repository

Data access layer for loan entities.
"""

from typing import List
import sqlite3
from core.models import Loan
from core.db.connection import DatabaseConnection

class LoanRepository:
    """Repository for loan data access."""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def get_all_loans(self) -> List[Loan]:
        """Get all loans from database."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT l.id, l.lender, l.loan_type, l.principal_paise,
                       l.outstanding_paise, l.emi_paise, l.status,
                       l.linked_account_id
                FROM loans l
                ORDER BY lender
            """)

            loans = []
            for row in cursor.fetchall():
                loans.append(Loan(
                    id=row['id'],
                    lender=row['lender'],
                    loan_type=row['loan_type'],
                    principal_paise=row['principal_paise'],
                    outstanding_paise=row['outstanding_paise'],
                    emi_paise=row['emi_paise'],
                    status=row['status'],
                    linked_account_id=row['linked_account_id']
                ))

            return loans

    def get_loan_by_id(self, loan_id: int) -> Loan | None:
        """Get loan by ID."""
        with self.db.connection() as conn:
            cursor = conn.execute("""
                SELECT l.id, l.lender, l.loan_type, l.principal_paise,
                       l.outstanding_paise, l.emi_paise, l.status,
                       l.linked_account_id
                FROM loans l
                WHERE l.id = ?
            """, (loan_id,))

            row = cursor.fetchone()
            if row:
                return Loan(
                    id=row['id'],
                    lender=row['lender'],
                    loan_type=row['loan_type'],
                    principal_paise=row['principal_paise'],
                    outstanding_paise=row['outstanding_paise'],
                    emi_paise=row['emi_paise'],
                    status=row['status'],
                    linked_account_id=row['linked_account_id']
                )
            return None