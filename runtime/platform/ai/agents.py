"""AI Agents (Phase 13 — foundation only).

Agent definitions for future phases. Phase 13 only establishes the
agent framework; actual agents are implemented in later phases.
"""

from __future__ import annotations

from typing import Any

__all__ = ["Agent", "AGENT_REGISTRY"]


class Agent:
    """Base class for AI agents. Phase 13 only defines the framework."""

    def __init__(self, name: str, description: str, authority_level: int) -> None:
        self.name = name
        self.description = description
        self.authority_level = authority_level
        self.enabled = False  # All agents disabled by default in Phase 13

    def can_execute(self, run_mode: str, run_authorization_level: int) -> bool:
        """Check if agent can execute in current mode."""
        return self.enabled and self.authority_level <= run_authorization_level

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's logic. Override in subclasses."""
        raise NotImplementedError


# Placeholder agents for future phases
class DiagnosticAssistantAgent(Agent):
    """Phase 17 - AI Diagnostic Assistant."""
    def __init__(self) -> None:
        super().__init__("diagnostic_assistant", "AI-assisted diagnostic interpretation", 1)

class EngineeringAgent(Agent):
    """Phase 18 - Engineering Agent / Development Authority."""
    def __init__(self) -> None:
        super().__init__("engineering_agent", "Controlled code modification", 2)

class FinancialAIAgent(Agent):
    """Phase 19 - Financial AI."""
    def __init__(self) -> None:
        super().__init__("financial_ai", "Read-only financial intelligence", 1)

class WorkflowAutomationAgent(Agent):
    """Phase 20 - Controlled Workflow Automation."""
    def __init__(self) -> None:
        super().__init__("workflow_automation", "Controlled workflow execution", 3)

class HighRiskAgent(Agent):
    """Phase 21 - High-Risk Authority."""
    def __init__(self) -> None:
        super().__init__("high_risk", "High-risk operations", 4)


# Registry of all known agents
AGENT_REGISTRY: dict[str, Agent] = {
    "diagnostic_assistant": DiagnosticAssistantAgent(),
    "engineering_agent": EngineeringAgent(),
    "financial_ai": FinancialAIAgent(),
    "workflow_automation": WorkflowAutomationAgent(),
    "high_risk": HighRiskAgent(),
}


def get_agent(name: str) -> Agent | None:
    return AGENT_REGISTRY.get(name)


def list_agents(*, enabled_only: bool = False) -> list[dict[str, Any]]:
    result = []
    for name, agent in AGENT_REGISTRY.items():
        result.append({
            "name": name,
            "description": agent.description,
            "authority_level": agent.authority_level,
            "enabled": agent.enabled,
        })
    return result