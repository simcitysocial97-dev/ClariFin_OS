from __future__ import annotations

from enum import Enum
from typing import Any

class AIMode(str, Enum):
    MANUAL = "MANUAL"
    ASSISTED = "ASSISTED"
    AUTONOMOUS = "AUTONOMOUS"
class AIStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
class AuthorityLevel:
    level: int
    name: str
    description: str
    enabled_by_default: bool
AUTHORITY_LEVELS: list[AuthorityLevel]
AI_RUN_KIND: str
AI_TOOL_KIND: str
AI_TOOL_LIST_KIND: str
AI_MODE_KIND: str
AI_RUN_LIST_KIND: str
AI_POLICY_KIND: str
AI_AUDIT_KIND: str
class PolicyDecision:
    allowed: bool
    reason: str
    required_authorization: str | None
class ToolSchema:
    name: str
    authority_level: int
    parameters: list[Any]
class ToolParameter:
    name: str
    type: str
    required: bool
    description: str
