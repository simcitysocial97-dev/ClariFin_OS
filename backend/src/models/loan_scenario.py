"""Loan scenario domain model for prepayment simulations."""

from typing import Any

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
