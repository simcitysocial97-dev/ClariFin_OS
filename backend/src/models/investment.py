from src.models.base import DomainModel, Money


class Investment(DomainModel):
    """Investment domain entity"""

    id: int
    name: str
    type: str  # investment_type
    units: float | None = None
    buy_price: Money
    current_price: Money
    invested: Money
    current_value: Money
    as_of_date: str | None = None

    @classmethod
    def from_db_row(cls, row: dict) -> "Investment":
        return cls(
            id=row["id"],
            name=row["name"],
            type=row["investment_type"],
            units=row.get("units"),
            buy_price=Money(paise=row["buy_price_paise"]),
            current_price=Money(paise=row["current_price_paise"]),
            invested=Money(paise=row["invested_paise"]),
            current_value=Money(paise=row["current_value_paise"]),
            as_of_date=row.get("as_of_date"),
        )
