"""Account Link DTOs."""

from typing import Any, Literal

from pydantic import BaseModel, Field

RelationshipType = Literal["TRANSFER", "JOINT", "GUARANTOR"]


class AccountLinkRequest(BaseModel):
    """Account link creation request."""

    linked_account_id: str = Field(..., description="ID of the account to link")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")


class AccountLinkResponse(BaseModel):
    """Account link response model."""

    account_id: int
    linked_account_id: int
    relationship_type: str
    created_at: str | None = None

    @classmethod
    def from_link_dict(cls, link: dict[str, Any]) -> "AccountLinkResponse":
        """Create AccountLinkResponse from link dict."""
        return cls(
            account_id=link["account_id"],
            linked_account_id=link["linked_account_id"],
            relationship_type=link["relationship_type"],
            created_at=link.get("created_at"),
        )
