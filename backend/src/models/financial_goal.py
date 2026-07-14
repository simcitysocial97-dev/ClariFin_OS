"""Financial Goal domain models.

All monetary values are integers in paise (₹1.00 = 100 paise).
Goal types: emergency_fund, debt_payoff, purchase, investment, education, retirement, custom.
Priority levels: critical, high, medium, low.
Status values: active, completed, paused.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from src.models.base import DomainModel

# Goal type enumeration
GoalType = Literal[
    "emergency_fund",
    "debt_payoff",
    "purchase",
    "investment",
    "education",
    "retirement",
    "custom",
]

# Priority enumeration
GoalPriority = Literal["critical", "high", "medium", "low"]

# Status enumeration
GoalStatus = Literal["active", "completed", "paused"]


class FinancialGoal(DomainModel):
    """Financial goal domain entity."""

    id: str
    household_id: str
    owner_id: str | None = None

    goal_type: GoalType
    name: str

    target_amount_paise: int
    current_amount_paise: int = 0

    target_date: str | None = None

    priority: GoalPriority = "medium"
    status: GoalStatus = "active"

    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str | None = None

    @field_validator("target_amount_paise", "current_amount_paise")
    @classmethod
    def validate_non_negative(cls, v: int) -> int:
        """Ensure monetary fields are non-negative."""
        if v < 0:
            raise ValueError("Monetary fields must be non-negative")
        return v

    @field_validator("target_amount_paise")
    @classmethod
    def validate_positive_target(cls, v: int) -> int:
        """Ensure target amount is positive."""
        if v <= 0:
            raise ValueError("target_amount_paise must be positive")
        return v

    @classmethod
    def from_db_row(cls, row: dict[str, Any]) -> "FinancialGoal":
        """Create FinancialGoal from database row."""
        return cls(
            id=str(row["id"]),
            household_id=row["household_id"],
            owner_id=row.get("owner_id"),
            goal_type=row["goal_type"],  # type: ignore
            name=row["name"],
            target_amount_paise=row["target_amount_paise"],
            current_amount_paise=row.get("current_amount_paise", 0),
            target_date=row.get("target_date"),
            priority=row.get("priority", "medium"),  # type: ignore
            status=row.get("status", "active"),  # type: ignore
            created_at=row.get("created_at", cls.created_at.default_factory()),  # type: ignore
            updated_at=row.get("updated_at"),
        )


# ============================================================
# Request/Response DTOs
# ============================================================

class FinancialGoalCreateRequest(BaseModel):
    """Financial goal creation request."""

    household_id: str = "primary"
    owner_id: str | None = None
    goal_type: GoalType
    name: str = Field(..., min_length=1, max_length=100)
    target_amount_paise: int = Field(gt=0, description="Target amount in paise")
    current_amount_paise: int = Field(
        default=0, ge=0, description="Current saved amount in paise"
    )
    target_date: str | None = Field(
        default=None,
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Target date (YYYY-MM-DD)",
    )
    priority: GoalPriority = "medium"
    status: GoalStatus = "active"


class FinancialGoalUpdateRequest(BaseModel):
    """Financial goal update request."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    target_amount_paise: int | None = Field(default=None, gt=0)
    current_amount_paise: int | None = Field(default=None, ge=0)
    target_date: str | None = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority: GoalPriority | None = None
    status: GoalStatus | None = None


class FinancialGoalResponse(BaseModel):
    """Financial goal response model."""

    id: str
    household_id: str
    owner_id: str | None = None
    goal_type: GoalType
    name: str
    target_amount_paise: int
    current_amount_paise: int
    target_date: str | None = None
    priority: GoalPriority
    status: GoalStatus
    created_at: str
    updated_at: str | None = None

    @classmethod
    def from_goal(cls, goal: FinancialGoal) -> "FinancialGoalResponse":
        """Create FinancialGoalResponse from FinancialGoal model."""
        return cls(
            id=goal.id,
            household_id=goal.household_id,
            owner_id=goal.owner_id,
            goal_type=goal.goal_type,
            name=goal.name,
            target_amount_paise=goal.target_amount_paise,
            current_amount_paise=goal.current_amount_paise,
            target_date=goal.target_date,
            priority=goal.priority,
            status=goal.status,
            created_at=goal.created_at,
            updated_at=goal.updated_at,
        )

    @classmethod
    def from_goal_dict(cls, goal: dict[str, Any]) -> "FinancialGoalResponse":
        """Create FinancialGoalResponse from goal dict."""
        return cls(
            id=str(goal["id"]),
            household_id=goal.get("household_id", "primary"),
            owner_id=goal.get("owner_id"),
            goal_type=goal["goal_type"],  # type: ignore
            name=goal["name"],
            target_amount_paise=goal["target_amount_paise"],
            current_amount_paise=goal.get("current_amount_paise", 0),
            target_date=goal.get("target_date"),
            priority=goal.get("priority", "medium"),  # type: ignore
            status=goal.get("status", "active"),  # type: ignore
            created_at=goal.get("created_at", ""),
            updated_at=goal.get("updated_date"),
        )
