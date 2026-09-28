from __future__ import annotations

from typing import Any

__all__ = ["Agent", "AGENT_REGISTRY", "get_agent", "list_agents"]
class Agent:
    name: str
    description: str
    authority_level: int
    enabled: bool
    def can_execute(self, run_mode: str, run_authorization_level: int) -> bool: ...
    def execute(self, context: dict[str, Any]) -> dict[str, Any]: ...
AGENT_REGISTRY: dict[str, Agent]
def get_agent(name: str) -> Agent | None: ...
def list_agents(*, enabled_only: bool = ...) -> list[dict[str, Any]]: ...
