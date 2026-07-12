"""Institution DTOs."""

from typing import Any, Literal

from pydantic import BaseModel, Field

InstitutionType = Literal["BANK", "WALLET", "BROKER", "OTHER"]


class InstitutionCreateRequest(BaseModel):
    """Institution creation request."""

    institution_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    institution_type: InstitutionType = Field(..., description="Type of institution")
    interest_rate_bps: int | None = Field(default=None, ge=0, le=5000)
    supported_features_json: str | None = None


class InstitutionUpdateRequest(BaseModel):
    """Institution update request - all fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    institution_type: InstitutionType | None = None
    interest_rate_bps: int | None = Field(default=None, ge=0, le=5000)
    supported_features_json: str | None = None


class InstitutionResponse(BaseModel):
    """Institution response model."""

    institution_id: str
    name: str
    institution_type: str
    interest_rate_bps: int | None = None
    supported_features_json: str | None = None
    created_at: str | None = None
    updated_at: str | None = None

    @classmethod
    def from_institution_dict(cls, institution: dict[str, Any]) -> "InstitutionResponse":
        """Create InstitutionResponse from institution dict."""
        return cls(
            institution_id=institution["institution_id"],
            name=institution["name"],
            institution_type=institution["type"],
            interest_rate_bps=institution.get("interest_rate_bps"),
            supported_features_json=institution.get("supported_features_json"),
            created_at=institution.get("created_at"),
            updated_at=institution.get("updated_at"),
        )
