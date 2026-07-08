from pydantic import BaseModel, ConfigDict
from datetime import date, datetime


class DomainModel(BaseModel):
    """Base class for all domain models"""

    model_config = ConfigDict(
        from_attributes=True,  # Allow ORM mode (dict/Row conversion)
        frozen=False,          # Allow mutation for now
        validate_assignment=True,
        str_strip_whitespace=True,
    )


class Money(BaseModel):
    """Money value in paise (₹1.00 = 100 paise)"""
    paise: int

    @property
    def rupees(self) -> float:
        return self.paise / 100.0

    @classmethod
    def from_rupees(cls, rupees: float) -> "Money":
        return cls(paise=int(round(rupees * 100)))

    def __str__(self) -> str:
        return f"₹{self.rupees:.2f}"