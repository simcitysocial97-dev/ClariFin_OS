"""
ClariFin Dependencies
=====================
Shared dependencies, utilities, and Pydantic models for all routers.
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict
from pydantic import BaseModel, Field, field_validator

from src.logger import log
from src.utils import parse_date_to_iso, format_paise, parse_amount_to_paise

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from db import FinanceDB

# ============================================================
# Configuration
# ============================================================

# Database path (relative to this file)
DB_PATH = str(Path(__file__).parent.parent / "data" / "finance.db")
UPLOAD_DIR = Path(__file__).parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# Pydantic Models
# ============================================================

class CategoryUpdate(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)


class BulkCategoryUpdate(BaseModel):
    ids: List[int] = Field(..., min_length=1)
    category: str = Field(..., min_length=1, max_length=100)


class ImportExecute(BaseModel):
    filename: str = Field(..., min_length=1, max_length=500)
    mapping: dict
    member: str = Field("Self", max_length=100)


class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field("#6366F1", max_length=7)


class AccountCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    bank_name: str = Field("", max_length=200)
    account_type: str = Field("savings")
    account_number_masked: str = Field("XXXX", max_length=20)
    balance_paise: int = Field(0, ge=0)
    credit_limit_paise: int = Field(0, ge=0)
    currency: str = Field("INR", max_length=3)
    color: str = Field("#6366F1", max_length=7)
    icon: str = Field("building", max_length=50)

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        allowed = {"savings", "current", "credit_card", "fd", "wallet", "loan"}
        if v not in allowed:
            raise ValueError(f"account_type must be one of: {', '.join(sorted(allowed))}")
        return v


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    bank_name: Optional[str] = Field(None, max_length=200)
    account_type: Optional[str] = None
    account_number_masked: Optional[str] = Field(None, max_length=20)
    balance_paise: Optional[int] = Field(None, ge=0)
    credit_limit_paise: Optional[int] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=3)
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"savings", "current", "credit_card", "fd", "wallet", "loan"}
        if v not in allowed:
            raise ValueError(f"account_type must be one of: {', '.join(sorted(allowed))}")
        return v


class CardCreate(BaseModel):
    account_id: Optional[int] = None
    card_name: str = Field(..., min_length=1, max_length=200)
    card_type: str = Field("visa")
    issuer: str = Field("", max_length=100)
    last_four: str = Field("XXXX", max_length=4, min_length=4)
    cardholder_name: str = Field("", max_length=200)
    credit_limit_paise: int = Field(0, ge=0)
    billing_date: int = Field(1, ge=1, le=31)
    card_color: str = Field("#1E293B", max_length=7)
    card_gradient: str = Field("from-slate-800 to-slate-900", max_length=100)

    @field_validator("card_type")
    @classmethod
    def validate_card_type(cls, v: str) -> str:
        allowed = {"visa", "mastercard", "rupay", "amex", "diners"}
        if v not in allowed:
            raise ValueError(f"card_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("last_four")
    @classmethod
    def validate_last_four(cls, v: str) -> str:
        if v != "XXXX" and not v.isdigit():
            raise ValueError("last_four must be 4 digits or 'XXXX'")
        return v


class CardUpdate(BaseModel):
    account_id: Optional[int] = None
    card_name: Optional[str] = Field(None, min_length=1, max_length=200)
    card_type: Optional[str] = None
    issuer: Optional[str] = Field(None, max_length=100)
    last_four: Optional[str] = Field(None, max_length=4, min_length=4)
    cardholder_name: Optional[str] = Field(None, max_length=200)
    credit_limit_paise: Optional[int] = Field(None, ge=0)
    billing_date: Optional[int] = Field(None, ge=1, le=31)
    card_color: Optional[str] = Field(None, max_length=7)
    card_gradient: Optional[str] = Field(None, max_length=100)

    @field_validator("card_type")
    @classmethod
    def validate_card_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"visa", "mastercard", "rupay", "amex", "diners"}
        if v not in allowed:
            raise ValueError(f"card_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("last_four")
    @classmethod
    def validate_last_four(cls, v: Optional[str]) -> Optional[str]:
        if v is None or v == "XXXX":
            return v
        if not v.isdigit():
            raise ValueError("last_four must be 4 digits or 'XXXX'")
        return v


class IncomeSourceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field("other")
    account_id: Optional[int] = None
    amount_paise: int = Field(0, ge=0)
    frequency: str = Field("monthly")
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"salary", "freelance", "business", "rental", "dividend", "interest", "other"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        allowed = {"daily", "weekly", "monthly", "quarterly", "annual", "irregular"}
        if v not in allowed:
            raise ValueError(f"frequency must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[str] = None
    account_id: Optional[int] = None
    amount_paise: Optional[int] = Field(None, ge=0)
    frequency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"salary", "freelance", "business", "rental", "dividend", "interest", "other"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"daily", "weekly", "monthly", "quarterly", "annual", "irregular"}
        if v not in allowed:
            raise ValueError(f"frequency must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


class LoanCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    lender: Optional[str] = Field(None, max_length=200)
    loan_type: str = Field("other")
    principal_paise: int = Field(..., gt=0)
    outstanding_paise: int = Field(..., ge=0)
    interest_rate: float = Field(..., ge=0, le=100)
    emi_paise: int = Field(0, ge=0)
    tenure_months: Optional[int] = Field(None, gt=0)
    start_date: str = Field(...)
    end_date: Optional[str] = None
    linked_account_id: Optional[int] = None
    status: str = Field("active")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: str) -> str:
        allowed = {"home", "car", "personal", "education", "credit_card", "gold", "other"}
        if v not in allowed:
            raise ValueError(f"loan_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"active", "closed", "defaulted"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


class LoanUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    lender: Optional[str] = Field(None, max_length=200)
    loan_type: Optional[str] = None
    outstanding_paise: Optional[int] = Field(None, ge=0)
    interest_rate: Optional[float] = Field(None, ge=0, le=100)
    emi_paise: Optional[int] = Field(None, ge=0)
    status: Optional[str] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"home", "car", "personal", "education", "credit_card", "gold", "other"}
        if v not in allowed:
            raise ValueError(f"loan_type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"active", "closed", "defaulted"}
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v


class LoanPaymentCreate(BaseModel):
    loan_id: Optional[int] = Field(None, gt=0)
    transaction_id: Optional[int] = Field(None, gt=0)
    principal_component_paise: int = Field(0, ge=0)
    interest_component_paise: int = Field(0, ge=0)
    payment_date: str = Field(...)
    remaining_principal_paise: int = Field(0, ge=0)

    @field_validator("payment_date")
    @classmethod
    def validate_payment_date(cls, v: str) -> str:
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


class InvestmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: str = Field("other")
    platform: Optional[str] = Field(None, max_length=200)
    invested_paise: int = Field(0, ge=0)
    current_value_paise: int = Field(0, ge=0)
    units: float = Field(0, ge=0)
    purchase_date: Optional[str] = None
    maturity_date: Optional[str] = None
    linked_account_id: Optional[int] = None
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"mutual_fund", "stock", "fd", "ppf", "epf", "nps", "gold", "real_estate", "crypto", "other"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("purchase_date", "maturity_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


class InvestmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[str] = None
    platform: Optional[str] = Field(None, max_length=200)
    invested_paise: Optional[int] = Field(None, ge=0)
    current_value_paise: Optional[int] = Field(None, ge=0)
    units: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"mutual_fund", "stock", "fd", "ppf", "epf", "nps", "gold", "real_estate", "crypto", "other"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {', '.join(sorted(allowed))}")
        return v


class RecurringTransactionCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    amount_paise: int = Field(..., gt=0)
    type: str = Field("debit")
    category: str = Field("Uncategorized", max_length=100)
    frequency: str = Field("monthly")
    account_id: Optional[str] = Field(None, max_length=100)
    next_due_date: Optional[str] = None
    is_active: bool = True
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        allowed = {"debit", "credit"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        allowed = {"daily", "weekly", "monthly", "quarterly", "annual"}
        if v not in allowed:
            raise ValueError(f"frequency must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("next_due_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


class RecurringTransactionUpdate(BaseModel):
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    amount_paise: Optional[int] = Field(None, gt=0)
    type: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    frequency: Optional[str] = None
    next_due_date: Optional[str] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"debit", "credit"}
        if v not in allowed:
            raise ValueError(f"type must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed = {"daily", "weekly", "monthly", "quarterly", "annual"}
        if v not in allowed:
            raise ValueError(f"frequency must be one of: {', '.join(sorted(allowed))}")
        return v

    @field_validator("next_due_date")
    @classmethod
    def validate_date(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        parsed = parse_date_to_iso(v)
        if parsed is None:
            raise ValueError(f"Invalid date format: {v}. Use YYYY-MM-DD or DD/MM/YYYY.")
        return parsed


# ============================================================
# Database Dependency (Singleton Pattern)
# ============================================================

_db_instance: FinanceDB | None = None


def get_db() -> FinanceDB:
    """Get database instance (singleton)."""
    global _db_instance
    if _db_instance is None:
        _db_instance = FinanceDB(db_path=DB_PATH)
        log.info("Database initialized: %s", DB_PATH)
    return _db_instance


def close_db() -> None:
    """Close the database connection (singleton cleanup)."""
    global _db_instance
    if _db_instance is not None:
        _db_instance.close()
        _db_instance = None



# ============================================================
# Utility Functions
# ============================================================

# Backward-compatible alias - format_inr now delegates to format_paise
def format_inr(amount: float) -> str:
    """Format amount in Indian Rupee notation with lakh/crore grouping."""
    if amount is None:
        return "₹0.00"
    paise = int(round(amount * 100))
    return format_paise(paise)


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse various Indian date formats to datetime."""
    if not date_str:
        return None
    # Use utils.parse_date_to_iso for consistent parsing
    iso_date = parse_date_to_iso(date_str)
    if iso_date:
        try:
            return datetime.strptime(iso_date, "%Y-%m-%d")
        except ValueError:
            pass
    return None


def format_date_display(date_str: str) -> str:
    """Convert any date format to: 15 Jun 2025"""
    iso_date = parse_date_to_iso(date_str)
    if iso_date:
        try:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")
            return dt.strftime("%d %b %Y")
        except ValueError:
            pass
    return date_str


def clean_description(desc: str) -> str:
    """Clean transaction descriptions for display."""
    if not desc:
        return ""
    # Remove leading date+time
    cleaned = re.sub(r'^\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+', '', desc)
    # Remove leading timestamp
    cleaned = re.sub(r'^\d{2}:\d{2}:\d{2}\s+', '', cleaned)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def get_month_key(date_str: str) -> str:
    """Extract YYYY-MM from date string."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%Y-%m")
    return ""


def get_weekday(date_str: str) -> str:
    """Get day of week name from date string."""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%A")
    return ""


def percentage_change(current: float, previous: float) -> str:
    """Calculate percentage change, return formatted string."""
    if previous == 0:
        return "+100%" if current > 0 else "0%"
    change = ((current - previous) / previous) * 100
    sign = "+" if change >= 0 else ""
    return f"{sign}{change:.1f}%"


# ============================================================
# Helper Functions
# ============================================================

def enrich_transaction(txn: dict) -> dict:
    """Add computed fields to a transaction."""
    dt = parse_date(txn.get("date", ""))
    amount = float(txn.get("amount") or 0)

    return {
        **txn,
        "parsed_date": dt.strftime("%Y-%m-%d") if dt else "",
        "date_display": format_date_display(txn.get("date", "")),
        "month_key": dt.strftime("%Y-%m") if dt else "",
        "weekday": dt.strftime("%A") if dt else "",
        "amount_display": format_inr(amount),
        "amount": amount,
        "description_display": clean_description(txn.get("description", "")),
    }


def compute_is_large(transactions: list) -> list:
    """Flag transactions that are >2.5x average debit."""
    debit_txns = [t for t in transactions if t.get("type") == "debit"]
    if not debit_txns:
        return transactions

    avg_debit = sum(t.get("amount", 0) for t in debit_txns) / len(debit_txns)
    threshold = avg_debit * 2.5

    for t in transactions:
        t["is_large"] = bool(t.get("type") == "debit" and t.get("amount", 0) > threshold)

    return transactions


def compute_behavioral_insights(transactions: list) -> list:
    """Generate behavioral insights from transactions."""
    insights = []
    debit_txns = [t for t in transactions if t.get("type") == "debit"]

    if not debit_txns:
        return []

    # Get month keys
    month_keys = sorted(set(t.get("month_key", "") for t in debit_txns if t.get("month_key")))
    if len(month_keys) < 1:
        return []

    this_month = month_keys[-1]

    # Category drift
    cat_monthly: dict = defaultdict(lambda: defaultdict(float))
    for t in debit_txns:
        mk = t.get("month_key", "")
        cat = t.get("category", "Uncategorized")
        if mk:
            cat_monthly[cat][mk] += t.get("amount", 0)

    for cat, monthly_data in cat_monthly.items():
        if len(monthly_data) >= 2:
            this_month_cat = monthly_data.get(this_month, 0)
            other_months = [v for k, v in monthly_data.items() if k != this_month]
            if other_months:
                avg_other = sum(other_months) / len(other_months)
                if avg_other > 0:
                    pct_change = ((this_month_cat - avg_other) / avg_other) * 100
                    if pct_change > 30:
                        insights.append({
                            "title": f"{cat} Spending Up",
                            "description": f"You spent {int(pct_change)}% more on {cat} this month",
                            "severity": "warning",
                            "icon": "trending-up",
                        })
                    elif pct_change < -30:
                        insights.append({
                            "title": f"{cat} Savings",
                            "description": f"You spent {int(abs(pct_change))}% less on {cat}",
                            "severity": "positive",
                            "icon": "trending-down",
                        })

    # Spending trend
    monthly_totals: dict = defaultdict(float)
    for t in debit_txns:
        mk = t.get("month_key", "")
        if mk:
            monthly_totals[mk] += t.get("amount", 0)

    if len(monthly_totals) >= 2:
        this_month_total = monthly_totals.get(this_month, 0)
        other_totals = [v for k, v in monthly_totals.items() if k != this_month]
        if other_totals:
            avg_other_total = sum(other_totals) / len(other_totals)
            if avg_other_total > 0:
                pct_change_total = ((this_month_total - avg_other_total) / avg_other_total) * 100
                if pct_change_total > 15:
                    insights.append({
                        "title": "Spending Trending Up",
                        "description": f"Overall spending is up {int(pct_change_total)}%",
                        "severity": "warning",
                        "icon": "alert-triangle",
                    })
                elif pct_change_total < -15:
                    insights.append({
                        "title": "Spending Down",
                        "description": f"Spending is down {int(abs(pct_change_total))}%",
                        "severity": "positive",
                        "icon": "check-circle",
                    })

    # Largest expense
    this_month_txns = [t for t in debit_txns if t.get("month_key") == this_month]
    if this_month_txns:
        largest = max(this_month_txns, key=lambda t: t.get("amount", 0))
        desc = (largest.get("description_display") or largest.get("description", ""))[:30]
        amt = format_inr(largest.get("amount", 0))
        insights.append({
            "title": "Largest Expense",
            "description": f"Your biggest: {desc} at {amt}",
            "severity": "info",
            "icon": "zap",
        })

    return insights[:6]
