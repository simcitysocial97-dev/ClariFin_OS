"""AI Control Layer package (Phase 13).

Governance machinery for AI without connecting a model provider.
"""

from __future__ import annotations

from runtime.platform.ai.orchestrator import AIOrchestrator, AI_ORCHESTRATOR_INSTANCE
from runtime.platform.ai.intent import resolve_intent, infer_mode_from_intent, ResolvedIntent
from runtime.platform.ai.planner import build_plan, Plan, PlanStep
from runtime.platform.ai.policy import PolicyEngine, evaluate_policy, POLICY_ENGINE_INSTANCE
from runtime.platform.ai.tools import ToolRegistry, TOOL_REGISTRY_INSTANCE, register_builtin_tools
from runtime.platform.ai.tools.handlers import ALL_HANDLERS, execute_tool
from runtime.platform.ai.runs import AIRunsStore, AI_RUNS_STORE_INSTANCE
from runtime.platform.ai.memory import AIMemory, AI_MEMORY_INSTANCE
from runtime.platform.ai.agents import Agent, AGENT_REGISTRY, get_agent, list_agents
from runtime.platform.api.contracts.ai import (
    AIMode,
    AIStatus,
    AuthorityLevel,
    AUTHORITY_LEVELS,
    ToolSchema,
    ToolParameter,
    AIStep,
    AIEnvelope,
    ToolInvocationRequest,
    ToolInvocationResponse,
    PolicyDecision,
    AuditEvent,
    AI_RUN_KIND,
    AI_RUN_LIST_KIND,
    AI_TOOL_KIND,
    AI_TOOL_LIST_KIND,
    AI_POLICY_KIND,
    AI_AUDIT_KIND,
    AI_MODE_KIND,
)
# Phase 15: Model routing
from runtime.platform.ai.providers import (
    ModelRouter,
    MODEL_ROUTER_INSTANCE,
    ProviderKind,
    RoutingProfile,
    CompletionResult,
    LocalOllamaProvider,
    DeterministicFallbackProvider,
    LOCAL_OLLAMA_PROVIDER,
    DETERMINISTIC_FALLBACK,
)
# Phase 14: Context engine
from runtime.platform.ai.context import (
    build_context_pack,
    CONTEXT_PACK_KIND,
)

__all__ = [
    # Orchestrator
    "AIOrchestrator",
    "AI_ORCHESTRATOR_INSTANCE",
    # Intent
    "resolve_intent",
    "infer_mode_from_intent",
    "ResolvedIntent",
    # Planner
    "build_plan",
    "Plan",
    "PlanStep",
    # Policy
    "PolicyEngine",
    "evaluate_policy",
    "POLICY_ENGINE_INSTANCE",
    # Tools
    "ToolRegistry",
    "TOOL_REGISTRY_INSTANCE",
    "register_builtin_tools",
    "ALL_HANDLERS",
    "execute_tool",
    # Runs
    "AIRunsStore",
    "AI_RUNS_STORE_INSTANCE",
    # Memory
    "AIMemory",
    "AI_MEMORY_INSTANCE",
    # Agents
    "Agent",
    "AGENT_REGISTRY",
    "get_agent",
    "list_agents",
    # Contracts
    "AIMode",
    "AIStatus",
    "AuthorityLevel",
    "AUTHORITY_LEVELS",
    "ToolSchema",
    "ToolParameter",
    "AIStep",
    "AIEnvelope",
    "ToolInvocationRequest",
    "ToolInvocationResponse",
    "PolicyDecision",
    "AuditEvent",
    "AI_RUN_KIND",
    "AI_RUN_LIST_KIND",
    "AI_TOOL_KIND",
    "AI_TOOL_LIST_KIND",
    "AI_POLICY_KIND",
    "AI_AUDIT_KIND",
    "AI_MODE_KIND",
    # Providers (Phase 15)
    "ModelRouter",
    "MODEL_ROUTER_INSTANCE",
    "ProviderKind",
    "RoutingProfile",
    "CompletionResult",
    "LocalOllamaProvider",
    "DeterministicFallbackProvider",
    "LOCAL_OLLAMA_PROVIDER",
    "DETERMINISTIC_FALLBACK",
    # Context (Phase 14)
    "build_context_pack",
    "CONTEXT_PACK_KIND",
]