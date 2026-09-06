"""Policy Engine (Phase 13).

Enforces authority levels, mode constraints, and tool authorization.
Every tool invocation passes through policy evaluation before execution.
"""

from __future__ import annotations

from runtime.platform.api.contracts.ai import AUTHORITY_LEVELS, PolicyDecision

# ---------------------------------------------------------------------------
# Policy Engine
# ---------------------------------------------------------------------------


class PolicyEngine:
    """Central policy enforcement point for AI operations."""

    def __init__(self) -> None:
        # Tool -> required authority level mapping (populated by tool registry)
        self._tool_levels: dict[str, int] = {}
        # Mode -> max allowed level
        self._mode_limits = {
            "MANUAL": 0,
            "ASSISTED": 1,
            "AUTONOMOUS": 4,
        }
        # Explicit authorization grants: run_id -> {tool: True}
        self._authorizations: dict[str, dict[str, bool]] = {}

    def register_tool(self, tool_name: str, authority_level: int) -> None:
        """Register a tool with its required authority level."""
        if authority_level < 0 or authority_level > 4:
            raise ValueError(f"Invalid authority level: {authority_level}")
        self._tool_levels[tool_name] = authority_level

    def evaluate(
        self,
        *,
        tool_name: str,
        run_mode: str,
        run_authorization_level: int,
        run_id: str | None = None,
    ) -> PolicyDecision:
        """Evaluate whether a tool invocation is allowed."""
        # Check if tool is registered
        required_level = self._tool_levels.get(tool_name)
        if required_level is None:
            return PolicyDecision(
                allowed=False,
                reason=f"Tool '{tool_name}' is not registered in policy engine",
                required_authorization="tool_registration",
            )

        # Check mode limit
        mode_limit = self._mode_limits.get(run_mode, 0)
        if required_level > mode_limit:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Tool '{tool_name}' requires level {required_level} "
                    f"but mode '{run_mode}' only allows up to level {mode_limit}"
                ),
                required_authorization="mode_elevation",
            )

        # Check run's authorized level
        if required_level > run_authorization_level:
            return PolicyDecision(
                allowed=False,
                reason=(
                    f"Tool '{tool_name}' requires level {required_level} "
                    f"but run is authorized for level {run_authorization_level}"
                ),
                required_authorization="run_authorization",
            )

        # Check explicit authorization for this run
        if (
            run_id
            and run_id in self._authorizations
            and self._authorizations[run_id].get(tool_name) is True
        ):
            return PolicyDecision(allowed=True, reason="explicitly_authorized")

        # Check if level is enabled by default (levels 0-1 are default enabled)
        level_info = next(
            (lvl for lvl in AUTHORITY_LEVELS if lvl.level == required_level), None
        )
        if level_info and level_info.enabled_by_default:
            return PolicyDecision(allowed=True, reason="enabled_by_default")

        return PolicyDecision(
            allowed=False,
            reason=f"Authority level {required_level} not enabled and not explicitly authorized",
            required_authorization="authority_enablement",
        )

    def authorize_tool(self, run_id: str, tool_name: str) -> None:
        """Grant explicit authorization for a tool in a specific run."""
        self._authorizations.setdefault(run_id, {})[tool_name] = True

    def revoke_tool(self, run_id: str, tool_name: str) -> None:
        """Revoke explicit authorization."""
        if run_id in self._authorizations:
            self._authorizations[run_id].pop(tool_name, None)

    def get_max_level_for_mode(self, mode: str) -> int:
        """Get the maximum authority level allowed for a mode."""
        return self._mode_limits.get(mode, 0)


# Singleton instance
POLICY_ENGINE_INSTANCE = PolicyEngine()


def evaluate_policy(
    *,
    tool_name: str,
    run_mode: str,
    run_authorization_level: int,
    run_id: str | None = None,
) -> PolicyDecision:
    """Convenience function for policy evaluation."""
    return POLICY_ENGINE_INSTANCE.evaluate(
        tool_name=tool_name,
        run_mode=run_mode,
        run_authorization_level=run_authorization_level,
        run_id=run_id,
    )
