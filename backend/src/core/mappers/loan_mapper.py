from typing import Any

from src.core.dtos.loans_dto import (
    AmortizationEntryDTO,
    AmortizationScheduleDTO,
    LoanSummaryDTO,
)


class LoanMapper:
    """Mapper for loan domain objects to DTOs."""

    @staticmethod
    def to_dto(loan: dict[str, Any]) -> LoanSummaryDTO:
        """Convert loan data to LoanSummaryDTO."""
        return LoanSummaryDTO(
            id=str(loan["id"]),
            name=loan["name"],
            type=loan["loan_type"],
            lender=loan.get("lender", ""),
            original_amount_paise=loan["principal_paise"],
            outstanding_paise=loan.get("outstanding_paise", loan["principal_paise"]),
            interest_rate_bps=loan.get("interest_rate", 0),
            tenure_months=loan["tenure_months"],
            remaining_months=loan.get("remaining_months", loan["tenure_months"]),
            emi_paise=loan.get("emi_paise", 0),
            status="active",  # All loans from list_loans are active
            start_date=loan.get("disbursed_date") or "",
            end_date=loan.get("end_date"),
        )

    @staticmethod
    def to_list_dto(loans: list[dict[str, Any]]) -> list[LoanSummaryDTO]:
        """Convert list of loan dicts to list of LoanSummaryDTO."""
        return [LoanMapper.to_dto(loan) for loan in loans]

    @staticmethod
    def to_schedule_dto(
        loan_id: int,
        emi_paise: int,
        total_interest_paise: int,
        schedule: list[dict[str, Any]],
    ) -> AmortizationScheduleDTO:
        """Convert schedule data to AmortizationScheduleDTO."""
        return AmortizationScheduleDTO(
            loan_id=str(loan_id),
            emi_paise=emi_paise,
            total_interest_paise=total_interest_paise,
            schedule=[
                AmortizationEntryDTO(
                    month=row["month"],
                    date=row["date"],
                    emi_paise=row["emi_paise"],
                    principal_paise=row["principal_paise"],
                    interest_paise=row["interest_paise"],
                    balance_paise=row["balance_paise"],
                )
                for row in schedule
            ],
        )
