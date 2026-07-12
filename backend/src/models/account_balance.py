"""Account Balance Snapshot DTOs."""

from typing import Any, Literal

from pydantic import BaseModel, Field

BalanceSource = Literal["actual", "projected", "adjusted"]


class BalanceSnapshotRequest(BaseModel):
    """Balance snapshot creation request."""

    balance_paise: int = Field(..., ge=0, description="Balance in paise")
    date_iso: str = Field(..., description="ISO-8601 date of the snapshot")
    source: BalanceSource = Field(default="actual", description="Source of the balance")


class BalanceSnapshotResponse(BaseModel):
    """Balance snapshot response model."""

    id: int
    account_id: str
    balance_paise: int
    date_iso: str
    source: str

    @classmethod
    def from_snapshot_dict(cls, snapshot: dict[str, Any]) -> "BalanceSnapshotResponse":
        """Create BalanceSnapshotResponse from snapshot dict."""
        return cls(
            id=snapshot["id"],
            account_id=snapshot["account_id"],
            balance_paise=snapshot["balance_paise"],
            date_iso=snapshot["date_iso"],
            source=snapshot.get("source", "actual"),
        )
