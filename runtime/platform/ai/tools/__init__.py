"""Tool Registry (Phase 13).

Central registry for all governed AI tools. Each tool must be registered
with its schema, authority level, and policy constraints before it can
be invoked. Tools are validated against their schema at registration time.
"""

from __future__ import annotations

import logging
from typing import Any

from runtime.platform.api.contracts.ai import ToolSchema, ToolParameter, AUTHORITY_LEVELS
from runtime.platform.ai.policy import POLICY_ENGINE_INSTANCE

logger = logging.getLogger(__name__)

__all__ = ["ToolRegistry", "TOOL_REGISTRY_INSTANCE"]


class ToolRegistry:
    """Central registry for governed AI tools."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSchema] = {}
        self._handlers: dict[str, Any] = {}  # tool_name -> callable

    def register(self, schema: ToolSchema, handler: Any) -> None:
        """Register a tool with its schema and execution handler."""
        # Validate schema
        if schema.authority_level < 0 or schema.authority_level > 4:
            raise ValueError(f"Invalid authority level for {schema.name}: {schema.authority_level}")

        # Validate parameter types
        for param in schema.parameters:
            if param.type not in ("string", "integer", "boolean", "object", "array"):
                raise ValueError(f"Invalid parameter type for {schema.name}.{param.name}: {param.type}")

        if schema.name in self._tools:
            logger.warning("Overriding existing tool registration: %s", schema.name)

        self._tools[schema.name] = schema
        self._handlers[schema.name] = handler

        # Also register with policy engine
        POLICY_ENGINE_INSTANCE.register_tool(schema.name, schema.authority_level)

        logger.info("Registered tool: %s (level %d)", schema.name, schema.authority_level)

    def get(self, tool_name: str) -> ToolSchema | None:
        return self._tools.get(tool_name)

    def list_tools(self, *, authority_level: int | None = None) -> list[ToolSchema]:
        tools = list(self._tools.values())
        if authority_level is not None:
            tools = [t for t in tools if t.authority_level <= authority_level]
        return sorted(tools, key=lambda t: t.name)

    def invoke(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool with validated arguments."""
        schema = self._tools.get(tool_name)
        if not schema:
            raise ValueError(f"Tool '{tool_name}' not registered")

        # Validate required arguments
        for param in schema.parameters:
            if param.required and param.name not in arguments:
                raise ValueError(f"Missing required argument for {tool_name}: {param.name}")

        # Type validation (basic)
        for param in schema.parameters:
            if param.name in arguments:
                val = arguments[param.name]
                if param.type == "integer" and not isinstance(val, int):
                    raise ValueError(f"Argument {param.name} must be integer")
                elif param.type == "boolean" and not isinstance(val, bool):
                    raise ValueError(f"Argument {param.name} must be boolean")
                elif param.type == "array" and not isinstance(val, list):
                    raise ValueError(f"Argument {param.name} must be array")

        handler = self._handlers.get(tool_name)
        if not handler:
            raise ValueError(f"No handler registered for tool '{tool_name}'")

        return handler(arguments)

    def get_tool_schema(self, tool_name: str) -> dict[str, Any] | None:
        """Get tool schema as dict for API serialization."""
        schema = self._tools.get(tool_name)
        if not schema:
            return None
        return {
            "name": schema.name,
            "description": schema.description,
            "authority_level": schema.authority_level,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                }
                for p in schema.parameters
            ],
            "returns": schema.returns,
            "idempotent": schema.idempotent,
            "side_effects": schema.side_effects,
        }


# ---------------------------------------------------------------------------
# Built-in Level 0/1 tools (Phase 16 will populate these)
# ---------------------------------------------------------------------------

LEVEL_0_TOOLS: list[dict[str, Any]] = [
    {
        "name": "inspect_health",
        "description": "Get system health snapshot from /platform/v1/health",
        "level": 0,
        "params": [],
        "returns": "platform.health_snapshot",
    },
    {
        "name": "inspect_capability",
        "description": "Get capability detail from /platform/v1/capabilities/{id}",
        "level": 0,
        "params": [{"name": "capability_id", "type": "string", "required": True, "description": "Capability identifier"}],
        "returns": "platform.capability_detail",
    },
    {
        "name": "inspect_architecture",
        "description": "Get architecture authorities from /platform/v1/architecture/authorities",
        "level": 0,
        "params": [],
        "returns": "platform.architecture_authorities",
    },
    {
        "name": "inspect_errors",
        "description": "Get current errors from /platform/v1/errors/current",
        "level": 0,
        "params": [{"name": "window", "type": "string", "required": False, "description": "Time window (1h, 24h, 7d)"}],
        "returns": "platform.errors_current",
    },
    {
        "name": "inspect_history",
        "description": "Get verification history from /platform/v1/history/runs",
        "level": 0,
        "params": [{"name": "limit", "type": "integer", "required": False, "description": "Max runs to return"}],
        "returns": "platform.history_runs",
    },
    {
        "name": "inspect_evidence",
        "description": "Get evidence detail from /platform/v1/evidence/{id}",
        "level": 0,
        "params": [{"name": "evidence_id", "type": "string", "required": True, "description": "Evidence identifier"}],
        "returns": "platform.evidence_detail",
    },
    {
        "name": "inspect_file",
        "description": "Read a file from the repository (read-only)",
        "level": 0,
        "params": [{"name": "path", "type": "string", "required": True, "description": "Repository-relative path"}],
        "returns": "string",
    },
    {
        "name": "search_code",
        "description": "Search repository code using the platform index",
        "level": 0,
        "params": [
            {"name": "query", "type": "string", "required": True, "description": "Search query"},
            {"name": "limit", "type": "integer", "required": False, "description": "Max results"},
        ],
        "returns": "list[dict]",
    },
    {
        "name": "inspect_run",
        "description": "Get execution detail from /platform/v1/executions/{id}",
        "level": 0,
        "params": [{"name": "execution_id", "type": "string", "required": True, "description": "Execution identifier"}],
        "returns": "platform.execution_detail",
    },
    {
        "name": "inspect_ai_run",
        "description": "Get AI run detail from /platform/v1/ai/runs/{id}",
        "level": 0,
        "params": [{"name": "run_id", "type": "string", "required": True, "description": "AI run identifier"}],
        "returns": "platform.ai_run",
    },
    {
        "name": "list_capabilities",
        "description": "List all capabilities from /platform/v1/capabilities",
        "level": 0,
        "params": [],
        "returns": "platform.capability_list",
    },
]


LEVEL_1_TOOLS: list[dict[str, Any]] = [
    {
        "name": "diagnose_failure",
        "description": "Run deterministic diagnostic engine on a symptom",
        "level": 1,
        "params": [
            {"name": "symptom", "type": "string", "required": True, "description": "Failure symptom description"},
            {"name": "error_code", "type": "string", "required": False, "description": "Error code if known"},
            {"name": "capability_id", "type": "string", "required": False, "description": "Affected capability if known"},
        ],
        "returns": "platform.diagnostic_result",
    },
    {
        "name": "compare_runs",
        "description": "Compare two runs via /platform/v1/history/compare",
        "level": 1,
        "params": [
            {"name": "current_run_id", "type": "string", "required": True, "description": "Current run ID or sentinel"},
            {"name": "baseline", "type": "string", "required": True, "description": "Baseline type (LAST, LAST_PASS, KNOWN_GOOD, BASELINE)"},
        ],
        "returns": "platform.history_compare",
    },
    {
        "name": "compute_change_intelligence",
        "description": "Get blast radius + stale evidence from /platform/v1/change/intelligence",
        "level": 1,
        "params": [],
        "returns": "platform.change_intelligence",
    },
    {
        "name": "run_verification_capability",
        "description": "Run a single capability verification via /platform/v1/verification/run",
        "level": 1,
        "params": [{"name": "capability_id", "type": "string", "required": True, "description": "Capability to verify"}],
        "returns": "platform.verification_run_result",
    },
    {
        "name": "run_diagnostic",
        "description": "Run deterministic diagnostic via /platform/v1/diagnose",
        "level": 1,
        "params": [
            {"name": "symptom", "type": "string", "required": True, "description": "Failure symptom"},
            {"name": "error_code", "type": "string", "required": False, "description": "Error code if known"},
            {"name": "capability_id", "type": "string", "required": False, "description": "Affected capability"},
        ],
        "returns": "platform.diagnostic_result",
    },
    {
        "name": "run_what_should_i_run",
        "description": "Get verification recommendations from /platform/v1/verification/what-should-i-run",
        "level": 1,
        "params": [{"name": "changed_files", "type": "array", "required": False, "description": "Optional file list"}],
        "returns": "platform.verification_recommendation",
    },
    {
        "name": "run_capability_group",
        "description": "Run a group of capabilities via /platform/v1/verification/run/group",
        "level": 1,
        "params": [{"name": "capability_ids", "type": "array", "required": True, "description": "List of capability IDs"}],
        "returns": "platform.verification_run_result",
    },
    {
        "name": "cancel_task",
        "description": "Cancel a running task/execution via /platform/v1/tasks/{id}/cancel",
        "level": 1,
        "params": [{"name": "task_id", "type": "string", "required": True, "description": "Task to cancel"}],
        "returns": "platform.task_cancel_result",
    },
]


def register_builtin_tools(registry: "ToolRegistry") -> None:
    """Register all built-in Level 0 and 1 tools.

    Phase 16: wire to real platform service handlers instead of mocks.
    Falls back to mock only if handlers module is unavailable.
    """
    try:
        from runtime.platform.ai.tools.handlers import LEVEL_0_HANDLERS, LEVEL_1_HANDLERS

        # Level 0 — real handlers backed by platform services
        for tpl in LEVEL_0_TOOLS:
            name = tpl["name"]
            handler = LEVEL_0_HANDLERS.get(name)
            if handler is None:
                logger.warning("No real handler for %s — using mock", name)
                handler = lambda args, _n=name: {"status": "mock", "tool": _n, "args": args}
            schema = ToolSchema(
                name=name,
                description=tpl["description"],
                authority_level=tpl["level"],
                parameters=[ToolParameter(**p) for p in tpl["params"]],
                returns=tpl["returns"],
                idempotent=True,
                side_effects="read",
            )
            registry.register(schema, handler)

        # Level 1 — real handlers (may create tasks/evidence)
        for tpl in LEVEL_1_TOOLS:
            name = tpl["name"]
            handler = LEVEL_1_HANDLERS.get(name)
            if handler is None:
                logger.warning("No real handler for %s — using mock", name)
                handler = lambda args, _n=name: {"status": "mock", "tool": _n, "args": args}
            schema = ToolSchema(
                name=name,
                description=tpl["description"],
                authority_level=tpl["level"],
                parameters=[ToolParameter(**p) for p in tpl["params"]],
                returns=tpl["returns"],
                idempotent=False,
                side_effects="read",
            )
            registry.register(schema, handler)
        return
    except Exception as exc:
        logger.warning("Real handler wiring failed (%s) — falling back to mocks", exc)

    # Fallback: mocks (should not happen in normal operation)
    for tpl in LEVEL_0_TOOLS:
        schema = ToolSchema(
            name=tpl["name"],
            description=tpl["description"],
            authority_level=tpl["level"],
            parameters=[ToolParameter(**p) for p in tpl["params"]],
            returns=tpl["returns"],
            idempotent=True,
            side_effects="read",
        )
        registry.register(schema, lambda args: {"status": "mock", "tool": schema.name, "args": args})

    for tpl in LEVEL_1_TOOLS:
        schema = ToolSchema(
            name=tpl["name"],
            description=tpl["description"],
            authority_level=tpl["level"],
            parameters=[ToolParameter(**p) for p in tpl["params"]],
            returns=tpl["returns"],
            idempotent=False,
            side_effects="read",
        )
        registry.register(schema, lambda args: {"status": "mock", "tool": schema.name, "args": args})


# Singleton instance
TOOL_REGISTRY_INSTANCE = ToolRegistry()