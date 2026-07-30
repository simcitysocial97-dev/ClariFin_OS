"""Loan domain models with extended fields for loan engine."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.models.base import DomainModel, Money


class Loan(DomainModel):
    """Loan domain entity."""

    id: int
    name: str
    principal: Money
    interest_rate: float  # Annual percentage (for backward compatibility)
    interest_rate_bps: int | None = None  # Basis points (INVARIANT 2)
    start_date: str  # ISO 8601 date string
    tenure_months: int
    emi: Money
    outstanding_paise: int = 0
    interest_type: str = "fixed"  # fixed | floating | hybrid
    floating_baselined_rate_bps: int | None = None
    last_rate_reset_date: str | None = None
    prepayment_mode: str = "reduce_tenure"
    original_tenure_months: int | None = None

    @field_validator("outstanding_paise")
    @classmethod
    def validate_outstanding_paise(cls, v: int) -> int:
        """Ensure outstanding amount is non-negative."""
        if v < 0:
            raise ValueError("outstanding_paise must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "Loan":
        return cls(
            id=row["id"],
            name=row["name"],
            principal=Money(paise=row["principal_paise"]),
            interest_rate=row["interest_rate"],
            interest_rate_bps=row.get("interest_rate_bps"),
            start_date=row["start_date"],
            tenure_months=row["tenure_months"],
            emi=Money(paise=row["emi_paise"]),
            outstanding_paise=row.get("outstanding_paise", 0),
            interest_type=row.get("interest_type", "fixed"),
            floating_baselined_rate_bps=row.get("floating_baselined_rate_bps"),
            last_rate_reset_date=row.get("last_rate_reset_date"),
            prepayment_mode=row.get("prepayment_mode", "reduce_tenure"),
            original_tenure_months=row.get("original_tenure_months"),
        )


class AmortizationRow(BaseModel):
    """Immutable amortization schedule row for display.

    Frozen to prevent mutation of historical payment data.
    All monetary values in paise (₹1.00 = 100 paise).
    """

    model_config = ConfigDict(frozen=True)

    month_number: int
    payment_date: str  # ISO 8601 date string
    emi_paise: int
    principal_paise: int
    interest_paise: int
    balance_paise: int
    cumulative_interest_paise: int

    @field_validator(
        "emi_paise",
        "principal_paise",
        "interest_paise",
        "balance_paise",
        "cumulative_interest_paise",
    )
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "AmortizationRow":
        """Create AmortizationRow from database row."""
        return cls(
            month_number=row["month_number"],
            payment_date=row["payment_date"],
            emi_paise=row["emi_paise"],
            principal_paise=row["principal_paise"],
            interest_paise=row["interest_paise"],
            balance_paise=row["balance_paise"],
            cumulative_interest_paise=row["cumulative_interest_paise"],
        )


# ============================================================
# Request/Response DTOs for API Contract Compliance
# ============================================================

# Valid loan types
VALID_LOAN_TYPES = {"personal", "home", "vehicle", "education", "gold", "other"}


class LoanCreateRequest(BaseModel):
    """Loan creation request matching Phase 5 API spec."""

    name: str
    lender: str
    loan_type: str = Field(
        default="personal",
        description="Loan type: personal | home | vehicle | education | gold | other",
    )
    principal_paise: int = Field(
        gt=0, description="Principal amount in paise (must be > 0)"
    )
    rate_bps: int = Field(
        ge=0, le=5000, description="Annual interest rate in basis points (0-5000)"
    )
    tenure_months: int = Field(ge=1, le=360, description="Tenure in months (1-360)")
    disbursed_date: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$", description="ISO 8601 date string"
    )
    emi_paise: int | None = None
    outstanding_paise: int | None = None

    @field_validator("loan_type")
    @classmethod
    def validate_loan_type(cls, v: str) -> str:
        """Ensure loan type is valid."""
        if v.lower() not in VALID_LOAN_TYPES:
            raise ValueError(
                f"loan_type must be one of: {', '.join(sorted(VALID_LOAN_TYPES))}"
            )
        return v.lower()


class LoanUpdateRequest(BaseModel):
    """Loan update request matching Phase 5 API spec."""

    outstanding_paise: int | None = Field(default=None, ge=0)
    rate_bps: int | None = Field(default=None, ge=0, le=5000)
    tenure_months: int | None = Field(default=None, ge=1, le=360)
    emi_paise: int | None = Field(default=None, ge=0)
    notes: str | None = None


class LoanResponse(BaseModel):
    """Loan response model matching Phase 5 API spec."""

    id: int
    name: str
    principal_paise: int
    rate_bps: int
    tenure_months: int
    emi_paise: int | None = None
    outstanding_paise: int | None = None
    lender: str | None = None
    loan_type: str | None = None
    disbursed_date: str | None = None

    @classmethod
    def from_loan_dict(cls, loan: dict[str, Any]) -> "LoanResponse":
        """Create LoanResponse from loan dict."""
        return cls(
            id=loan["id"],
            name=loan["name"],
            principal_paise=loan.get("principal_paise", 0),
            rate_bps=int(loan.get("interest_rate", 0) * 100),
            tenure_months=loan.get("tenure_months", 0),
            emi_paise=loan.get("emi_paise"),
            outstanding_paise=loan.get("outstanding_paise"),
            lender=loan.get("lender"),
            loan_type=loan.get("loan_type"),
            disbursed_date=loan.get("disbursed_date"),
        )


class ScheduleRow(BaseModel):
    """Single schedule row for API response."""

    month: int
    date: str
    emi_paise: int
    principal_paise: int
    interest_paise: int
    balance_paise: int


class ScheduleResponse(BaseModel):
    """Schedule response model matching Phase 5 API spec."""

    loan_id: int
    emi_paise: int
    total_interest_paise: int
    schedule: list[ScheduleRow]

    @classmethod
    def from_schedule_data(
        cls,
        loan_id: int,
        emi_paise: int,
        total_interest_paise: int,
        schedule: list[dict[str, Any]],
    ) -> "ScheduleResponse":
        """Create ScheduleResponse from raw schedule data."""
        return cls(
            loan_id=loan_id,
            emi_paise=emi_paise,
            total_interest_paise=total_interest_paise,
            schedule=[
                ScheduleRow(
                    month=row.get("month_number", row.get("month", 0)),
                    date=row.get("date", row.get("payment_date", "")),
                    emi_paise=row["emi_paise"],
                    principal_paise=row["principal_paise"],
                    interest_paise=row["interest_paise"],
                    balance_paise=row["balance_paise"],
                )
                for row in schedule
            ],
        )
