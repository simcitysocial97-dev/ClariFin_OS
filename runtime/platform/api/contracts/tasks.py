"""Task / obligation contracts (Phase 1 — ``/platform/v1/tasks``).

The Platform API surfaces C50 obligations as "tasks". This module defines
the JSON shape. Phase 2 services populate these contracts from
``runtime.foundation.verification.obligation*``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from runtime.platform.api.contracts._primitives import Identity, Status, Timestamp


TASK_LIST_KIND: str = "platform.task_list"
TASK_DETAIL_KIND: str = "platform.task_detail"
TASK_CANCEL_KIND: str = "platform.task_cancel_result"


class TaskListItem(BaseModel):
    """Single row in the task list response."""

    id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    capability_id: str = Field(min_length=1, max_length=256)
    status: Status
    created_at: Timestamp
    closed_at: Optional[Timestamp] = None


class TaskListData(BaseModel):
    open_count: int = Field(ge=0)
    closed_count: int = Field(ge=0)
    items: list[TaskListItem] = Field(default_factory=list)


class TaskListEnvelope(BaseModel):
    kind: str = Field(default=TASK_LIST_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: TaskListData


class TaskDetailData(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    name: str = Field(min_length=1, max_length=256)
    capability_id: str = Field(min_length=1, max_length=256)
    status: Status
    created_at: Timestamp
    closed_at: Optional[Timestamp] = None
    plan: list[str] = Field(default_factory=list)
    obligations: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    decision_id: Optional[str] = None


class TaskDetailEnvelope(BaseModel):
    kind: str = Field(default=TASK_DETAIL_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: TaskDetailData


class TaskCancelResultData(BaseModel):
    id: str = Field(min_length=1, max_length=256)
    cancelled: bool
    reason: str = Field(min_length=1, max_length=512)


class TaskCancelResultEnvelope(BaseModel):
    kind: str = Field(default=TASK_CANCEL_KIND, frozen=True)
    version: str
    generated_at: Timestamp
    id: Identity
    data: TaskCancelResultData


__all__ = [
    "TASK_CANCEL_KIND",
    "TASK_DETAIL_KIND",
    "TASK_LIST_KIND",
    "TaskCancelResultData",
    "TaskCancelResultEnvelope",
    "TaskDetailData",
    "TaskDetailEnvelope",
    "TaskListData",
    "TaskListEnvelope",
    "TaskListItem",
]
