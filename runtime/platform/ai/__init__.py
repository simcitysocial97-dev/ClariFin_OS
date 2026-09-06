"""AI Control Layer package (Phase 13).

Governance machinery for AI without connecting a model provider.
"""

from __future__ import annotations

from runtime.platform.ai.agents import AGENT_REGISTRY, Agent, get_agent, list_agents

# Phase 14: Context engine
from runtime.platform.ai.context import (
    CONTEXT_PACK_KIND,
    build_context_pack,
)
from runtime.platform.ai.intent import (
    ResolvedIntent,
    infer_mode_from_intent,
    resolve_intent,
)
from runtime.platform.ai.memory import AI_MEMORY_INSTANCE, AIMemory
from runtime.platform.ai.orchestrator import AI_ORCHESTRATOR_INSTANCE, AIOrchestrator
from runtime.platform.ai.planner import Plan, PlanStep, build_plan
from runtime.platform.ai.policy import (
    POLICY_ENGINE_INSTANCE,
    PolicyEngine,
    evaluate_policy,
)

# Phase 15: Model routing
from runtime.platform.ai.providers import (
    DETERMINISTIC_FALLBACK,
    LOCAL_LARGE_PROVIDER,
    LOCAL_OLLAMA_PROVIDER,
    MODEL_ROUTER_INSTANCE,
    OPENROUTER_PROVIDER,
    CompletionResult,
    DeterministicFallbackProvider,
    LocalLargeProvider,
    LocalOllamaProvider,
    ModelRouter,
    OpenRouterProvider,
    ProviderKind,
    RoutingProfile,
)
from runtime.platform.ai.runs import AI_RUNS_STORE_INSTANCE, AIRunsStore
from runtime.platform.ai.tools import (
    TOOL_REGISTRY_INSTANCE,
    ToolRegistry,
    register_builtin_tools,
)
from runtime.platform.ai.tools.handlers import ALL_HANDLERS, execute_tool
from runtime.platform.api.contracts.ai import (
    AI_AUDIT_KIND,
    AI_MODE_KIND,
    AI_POLICY_KIND,
    AI_RUN_KIND,
    AI_RUN_LIST_KIND,
    AI_TOOL_KIND,
    AI_TOOL_LIST_KIND,
    AUTHORITY_LEVELS,
    AIEnvelope,
    AIMode,
    AIStatus,
    AIStep,
    AuditEvent,
    AuthorityLevel,
    PolicyDecision,
    ToolInvocationRequest,
    ToolInvocationResponse,
    ToolParameter,
    ToolSchema,
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
    "LocalLargeProvider",
    "OpenRouterProvider",
    "DeterministicFallbackProvider",
    "LOCAL_OLLAMA_PROVIDER",
    "LOCAL_LARGE_PROVIDER",
    "OPENROUTER_PROVIDER",
    "DETERMINISTIC_FALLBACK",
    # Context (Phase 14)
    "build_context_pack",
    "CONTEXT_PACK_KIND",
]
