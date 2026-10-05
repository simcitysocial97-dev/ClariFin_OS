"""Investment business logic service."""

from typing import Any

from src.core.dtos.investments_dto import InvestmentsDTO
from src.core.mappers.investment_mapper import InvestmentMapper
from src.repositories.investment_repository import InvestmentRepository
from src.services.base import BaseService


class InvestmentService(BaseService):
    """Service for investment-related business logic."""

    def __init__(self) -> None:
        super().__init__(repository=InvestmentRepository())

    def get_portfolio(self) -> InvestmentsDTO:
        """Get all investments with calculated returns."""
        assert self.repository is not None
        # `get_all_models` returns `Investment` domain entities, which carry
        # `Money` value objects (`inv.invested.paise`) and name the type field
        # `type` (it comes from the `investment_type` column). This method read
        # `inv.invested_paise` / `inv.current_value_paise` /
        # `inv.investment_type`, none of which exist, so it raised
        # AttributeError on the first investment row. That was invisible while
        # every create failed with HTTP 500 and the table could never hold a
        # row; it is reached now that creation works.
        investments = self.repository.get_all_models()  # type: ignore[attr-defined]
        total_invested = sum(i.invested.paise for i in investments)
        total_current = sum(i.current_value.paise for i in investments)

        investments_data = [
            {
                "id": inv.id,
                "name": inv.name,
                "type": inv.type,
                "institution": getattr(inv, "institution", "") or "",
                "current_value_paise": inv.current_value.paise,
                "invested_paise": inv.invested.paise,
                "returns_paise": inv.current_value.paise - inv.invested.paise,
                "returns_percentage": (
                    (
                        (inv.current_value.paise - inv.invested.paise)
                        / inv.invested.paise
                        * 100
                    )
                    if inv.invested.paise > 0
                    else 0
                ),
                "returns_ytd_bps": 0,
                "status": "active",
            }
            for inv in investments
        ]

        return InvestmentsDTO(
            investments=InvestmentMapper._to_investment_summaries(investments_data),
            total_value_paise=total_current,
            total_invested_paise=total_invested,
            total_returns_paise=total_current - total_invested,
            investment_count=len(investments),
            insights=[],
            evidence_chain=None,
        )

    def get_investment_by_id(self, investment_id: str) -> dict[str, Any] | None:
        """Get a single investment by ID."""
        assert self.repository is not None
        investment = self.repository.get_by_id(investment_id)  # type: ignore[attr-defined]
        return investment  # type: ignore[no-any-return]

    def create_investment(
        self,
        name: str,
        investment_type: str,
        invested_paise: int,
        current_value_paise: int,
        units: float | None = None,
        buy_price_paise: int | None = None,
        current_price_paise: int | None = None,
        as_of_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Create a new investment."""
        assert self.repository is not None
        investment_id = self.repository.create(  # type: ignore[attr-defined]
            name=name,
            investment_type=investment_type,
            invested_paise=invested_paise,
            current_value_paise=current_value_paise,
            as_of_date=as_of_date,
            units=units,
            buy_price_paise=buy_price_paise,
            current_price_paise=current_price_paise,
            notes=notes,
        )
        result = self.repository.get_by_id(investment_id)  # type: ignore[attr-defined]
        if not result:
            return {}
        # The row's primary key is an integer; the API contract for an
        # investment identifier is a string (``InvestmentSummaryDTO.id``,
        # ``HoldingDTO.id``). Coercing here keeps the mutation response and the
        # read response reporting the same identifier for the same row.
        return {**result, "id": str(result["id"])}

    def update_investment(
        self,
        investment_id: str,
        units: float | None = None,
        current_price_paise: int | None = None,
        current_value_paise: int | None = None,
        as_of_date: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any] | None:
        """Update an investment."""
        assert self.repository is not None
        return self.repository.update(  # type: ignore[attr-defined,no-any-return]
            investment_id,
            units=units,
            current_price_paise=current_price_paise,
            current_value_paise=current_value_paise,
            as_of_date=as_of_date,
            notes=notes,
        )

    def delete_investment(self, investment_id: str) -> bool:
        """Delete an investment."""
        assert self.repository is not None
        return self.repository.delete(investment_id)  # type: ignore[attr-defined,no-any-return]
