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

    primary_account_id: str
    linked_account_id: str
    relationship_type: str
    created_at: str | None = None

    @classmethod
    def from_link_dict(cls, link: dict[str, Any]) -> "AccountLinkResponse":
        """Create AccountLinkResponse from link dict."""
        return cls(
            primary_account_id=link["primary_account_id"],
            linked_account_id=link["linked_account_id"],
            relationship_type=link["relationship_type"],
            created_at=link.get("created_at"),
        )
