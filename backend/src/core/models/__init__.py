"""Core Financial Models

Typed financial entities for the audit system.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List
from enum import Enum

class AuditStatus(Enum):
    """Audit result status."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"

@dataclass
class Finding:
    """Individual audit finding."""
    description: str
    severity: str
    details: Optional[dict] = None

@dataclass
class AuditResult:
    """Standardized audit output format."""
    audit_name: str
    timestamp: datetime
    metrics: dict
    summary: dict
    findings: List[Finding]
    status: AuditStatus

@dataclass
class Account:
    """Financial account model."""
    id: int
    name: str
    bank_name: str
    account_type: str
    balance_paise: int
    credit_limit_paise: int
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Card:
    """Credit/debit card model."""
    id: int
    card_name: str
    issuer: str
    card_type: str
    credit_limit_paise: int
    account_id: Optional[int] = None
    is_active: bool = True

@dataclass
class Loan:
    """Loan model."""
    id: int
    lender: str
    loan_type: str
    principal_paise: int
    outstanding_paise: int
    emi_paise: int
    status: str
    linked_account_id: Optional[int] = None

@dataclass
class Investment:
    """Investment model."""
    id: int
    investment_type: str
    platform: str
    current_value_paise: int
    is_active: bool = True

@dataclass
class Transaction:
    """Financial transaction model."""
    id: int
    description: str
    amount_paise: int
    type: str  # 'debit' or 'credit'
    category: str
    date_iso: str
    account_id: Optional[str] = None
    statement_id: Optional[int] = None

@dataclass
class RecurringTransaction:
    """Recurring transaction model."""
    description: str
    category: str
    amount_paise: int
    frequency: str
    account_id: Optional[str] = None
    is_active: bool = True