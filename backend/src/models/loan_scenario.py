"""Loan scenario domain model for prepayment simulations."""

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator

from src.models.base import DomainModel


class LoanScenario(DomainModel):
    """Saved prepayment/refinance scenario."""

    id: int | None = None
    loan_id: int
    scenario_name: str
    prepayment_paise: int | None = None
    prepayment_date: str | None = None
    new_tenure_months: int | None = None
    new_emi_paise: int | None = None
    interest_saved_paise: int | None = None
    months_saved: int | None = None
    created_at: str | None = None

    @field_validator("prepayment_paise", "new_emi_paise", "interest_saved_paise")
    @classmethod
    def validate_non_negative(cls, v: int | None) -> int | None:
        """Ensure monetary fields are non-negative when provided."""
        if v is not None and v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "LoanScenario":
        return cls(
            id=row.get("id"),
            loan_id=row["loan_id"],
            scenario_name=row["scenario_name"],
            prepayment_paise=row.get("prepayment_paise"),
            prepayment_date=row.get("prepayment_date"),
            new_tenure_months=row.get("new_tenure_months"),
            new_emi_paise=row.get("new_emi_paise"),
            interest_saved_paise=row.get("interest_saved_paise"),
            months_saved=row.get("months_saved"),
            created_at=row.get("created_at"),
        )


class LoanScenarioCreate(DomainModel):
    """DTO for creating a loan scenario."""

    loan_id: int
    scenario_name: str
    prepayment_paise: int | None = None
    prepayment_date: str | None = None
    new_tenure_months: int | None = None
    new_emi_paise: int | None = None
    interest_saved_paise: int | None = None
    months_saved: int | None = None


class SavingsSummary(BaseModel):
    """Summary of savings from a prepayment scenario.

    All monetary values in paise (₹1.00 = 100 paise).
    """

    interest_saved_paise: int = 0
    months_saved: int = 0
    new_tenure_months: int | None = None
    new_emi_paise: int | None = None

    @field_validator("interest_saved_paise")
    @classmethod
    def validate_interest_saved(cls, v: int) -> int:
        """Ensure interest saved is non-negative."""
        if v < 0:
            raise ValueError("interest_saved_paise must be non-negative")
        return v


class PrepaymentSimulation(BaseModel):
    """Immutable prepayment simulation result.

    Frozen to prevent mutation of simulation results.
    Contains original and new amortization schedules for comparison.
    """

    model_config = ConfigDict(frozen=True)

    original_schedule: list[dict[str, Any]]
    new_schedule: list[dict[str, Any]]
    savings_summary: SavingsSummary

    @classmethod
    def from_schedules(
        cls,
        original_schedule: list[dict[str, Any]],
        new_schedule: list[dict[str, Any]],
        savings_summary: SavingsSummary,
    ) -> "PrepaymentSimulation":
        """Create PrepaymentSimulation from schedule data."""
        return cls(
            original_schedule=original_schedule,
            new_schedule=new_schedule,
            savings_summary=savings_summary,
        )
