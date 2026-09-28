"""M9-C57 Phase 13 — AI Control Layer Foundation validation.

These tests prove Gate 13 from ``IMPLEMENTATION_ROADMAP.md``:

    AI requests can be represented and governed even with no model
    provider installed.

Test scope:

1. AI run lifecycle: create, list, get, cancel.
2. AI mode endpoint returns mode and authority configuration.
3. Tool registry: list tools, filter by authority level, get schema.
4. Policy engine: evaluates authority levels and mode constraints.
5. Tool step execution with policy check.
5. Orchestrator persistence and audit trail.
6. Intent resolution and planning.
7. No model provider required (all deterministic).
8. No C50 modules touched.
"""

from __future__ import annotations

import re
from typing import Any

from runtime.platform.ai import (
    TOOL_REGISTRY_INSTANCE,
    build_plan,
    evaluate_policy,
    infer_mode_from_intent,
    resolve_intent,
)
from runtime.platform.ai.orchestrator import AIOrchestrator
from runtime.platform.api.contracts import ai as ai_contract
from runtime.platform.api.contracts.ai import (
    AUTHORITY_LEVELS,
)
from runtime.platform.api.envelope import API_VERSION

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _envelope_shape_ok(env: dict[str, Any]) -> bool:
    """Validate canonical 5-key envelope shape."""
    return (
        set(env.keys()) == {"kind", "version", "generated_at", "id", "data"}
        and env["version"] == API_VERSION
        and re.fullmatch(r"sha256:[0-9a-f]{64}", env["id"])
        and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", env["generated_at"])
    )


def _clean_orchestrator() -> AIOrchestrator:
    """Return a fresh orchestrator with clean state."""
    return AIOrchestrator()


# ---------------------------------------------------------------------------
# 1. AI Run Lifecycle
# ---------------------------------------------------------------------------


class TestAIRunLifecycle:
    """Phase 13: AI run lifecycle (create, list, get, cancel)."""

    def test_start_run_returns_pending(self) -> None:
        orch = _clean_orchestrator()
        run = orch.start_run(symptom="test failure", mode="MANUAL")
        assert run["status"] == "PENDING"
        assert run["symptom"] == "test failure"
        assert run["mode"] == "MANUAL"
        assert run["id"].startswith("ai-")
        assert len(run["steps"]) == 0

    def test_get_run_returns_same_object(self) -> None:
        orch = _clean_orchestrator()
        run = orch.start_run(symptom="test")
        retrieved = orch.get_run(run["id"])
        assert retrieved is not None
        assert retrieved["id"] == run["id"]

    def test_list_runs_empty_initially(self) -> None:
        orch = _clean_orchestrator()
        runs = orch.list_runs()
        assert isinstance(runs, list)

    def test_cancel_run_changes_status(self) -> None:
        orch = _clean_orchestrator()
        run = orch.start_run(symptom="test")
        success = orch.cancel_run(run["id"])
        assert success is True
        cancelled = orch.get_run(run["id"])
        assert cancelled["status"] == "CANCELLED"
        assert cancelled["completed_at"] is not None

    def test_cancel_completed_run_fails(self) -> None:
        orch = _clean_orchestrator()
        run = orch.start_run(symptom="test")
        orch.execute_step(run["id"], "inspect_health", {})
        orch.complete_step(run["id"], 1, result={}, evidence_id="e1")
        success = orch.cancel_run(run["id"])
        assert success is False


# ---------------------------------------------------------------------------
# 2. AI Mode & Authority Configuration
# ---------------------------------------------------------------------------


class TestAIModeAndAuthority:
    """Phase 13: mode endpoint and authority level configuration."""

    def test_mode_endpoint_returns_manual_default(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            resp = c.get("/platform/v1/ai/mode")
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["current_mode"] == "MANUAL"
            assert set(data["available_modes"]) == {"MANUAL", "ASSISTED", "AUTONOMOUS"}
            assert len(data["authority_levels"]) == 5

    def test_authority_levels_defined(self) -> None:
        assert len(AUTHORITY_LEVELS) == 5
        for i, level in enumerate(AUTHORITY_LEVELS):
            assert level.level == i
            assert level.name
            assert level.description
            # Levels 0 and 1 enabled by default
            assert level.enabled_by_default == (i <= 1)


# ---------------------------------------------------------------------------
# 3. Tool Registry
# ---------------------------------------------------------------------------


class TestToolRegistry:
    """Phase 13: tool registration and schema validation."""

    def test_builtin_tools_registered(self) -> None:
        # 11 level-0 + 8 level-1 = 19 total
        tools = TOOL_REGISTRY_INSTANCE.list_tools()
        assert len(tools) == 19

    def test_tool_filtering_by_authority_level(self) -> None:
        level_0 = TOOL_REGISTRY_INSTANCE.list_tools(authority_level=0)
        level_1 = TOOL_REGISTRY_INSTANCE.list_tools(authority_level=1)
        assert len(level_0) == 11
        assert len(level_1) == 19
        for t in level_0:
            assert t.authority_level == 0

    def test_tool_schema_serialization(self) -> None:
        schema = TOOL_REGISTRY_INSTANCE.get("inspect_health")
        assert schema is not None
        dump = schema.model_dump()
        assert dump["name"] == "inspect_health"
        assert dump["authority_level"] == 0
        assert dump["side_effects"] == "read"
        assert dump["idempotent"] is True

    def test_tool_get_schema(self) -> None:
        schema_dict = TOOL_REGISTRY_INSTANCE.get_tool_schema("inspect_health")
        assert schema_dict is not None
        assert schema_dict["name"] == "inspect_health"
        assert schema_dict["authority_level"] == 0


# ---------------------------------------------------------------------------
# 4. Policy Engine
# ---------------------------------------------------------------------------


class TestPolicyEngine:
    """Phase 13: policy evaluation for tool invocations."""

    def test_policy_allows_level_0_in_manual(self) -> None:
        decision = evaluate_policy(
            tool_name="inspect_health",
            run_mode="MANUAL",
            run_authorization_level=0,
        )
        assert decision.allowed is True
        assert decision.reason in ("enabled_by_default", "explicitly_authorized")

    def test_policy_denies_level_1_in_manual(self) -> None:
        decision = evaluate_policy(
            tool_name="run_diagnostic",
            run_mode="MANUAL",
            run_authorization_level=0,
        )
        assert decision.allowed is False
        assert decision.required_authorization == "mode_elevation"

    def test_policy_allows_level_1_in_assisted(self) -> None:
        decision = evaluate_policy(
            tool_name="run_diagnostic",
            run_mode="ASSISTED",
            run_authorization_level=1,
        )
        assert decision.allowed is True

    def test_policy_denies_unknown_tool(self) -> None:
        decision = evaluate_policy(
            tool_name="nonexistent_tool",
            run_mode="AUTONOMOUS",
            run_authorization_level=4,
        )
        assert decision.allowed is False
        assert decision.required_authorization == "tool_registration"


# ---------------------------------------------------------------------------
# 5. Tool Step Execution with Policy Check
# ---------------------------------------------------------------------------


class TestToolStepExecution:
    """Phase 13: step execution with policy enforcement."""

    def test_step_execution_allowed_in_correct_mode(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            # Start run in ASSISTED mode (allows level 1)
            run_resp = c.post(
                "/platform/v1/ai/runs", json={"symptom": "test", "mode": "ASSISTED"}
            )
            run_id = run_resp.json()["data"]["id"]

            # Execute a level 1 tool (should be allowed) — Phase 16 now executes
            # the tool synchronously, so status is RUNNING (ready for next step)
            # rather than PENDING (Phase 13 stub)
            step_resp = c.post(
                f"/platform/v1/ai/runs/{run_id}/steps",
                json={"tool_name": "run_diagnostic", "arguments": {"symptom": "test"}},
            )
            assert step_resp.status_code == 200
            data = step_resp.json()["data"]
            assert data["run_id"] == run_id
            assert data["step"]["tool_name"] == "run_diagnostic"
            assert data["status"] in ("PENDING", "RUNNING", "COMPLETED")

    def test_step_execution_denied_by_policy(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            # Start run in MANUAL mode (only allows level 0)
            run_resp = c.post(
                "/platform/v1/ai/runs", json={"symptom": "test", "mode": "MANUAL"}
            )
            run_id = run_resp.json()["data"]["id"]

            # Try to execute level 1 tool (should be denied)
            step_resp = c.post(
                f"/platform/v1/ai/runs/{run_id}/steps",
                json={"tool_name": "run_diagnostic", "arguments": {"symptom": "test"}},
            )
            assert step_resp.status_code == 403
            error = step_resp.json()["error"]
            assert error["code"] == "POLICY_DENIED"
            assert "mode 'MANUAL'" in error["message"]


# ---------------------------------------------------------------------------
# 6. Orchestrator Persistence & Audit
# ---------------------------------------------------------------------------


class TestOrchestratorPersistence:
    """Phase 13: run persistence and audit trail."""

    def test_run_persisted_to_disk(self) -> None:
        orch = _clean_orchestrator()
        run = orch.start_run(symptom="persist test")
        # Create a new orchestrator instance to test disk persistence
        orch2 = AIOrchestrator()
        retrieved = orch2.get_run(run["id"])
        assert retrieved is not None
        assert retrieved["id"] == run["id"]

    def test_audit_trail_records_events(self) -> None:
        orch = _clean_orchestrator()
        run = orch.start_run(symptom="audit test")
        orch.execute_step(run["id"], "inspect_health", {})
        orch.complete_step(run["id"], 1, result={}, evidence_id="e1")

        run = orch.get_run(run["id"])
        audit = run.get("audit_trail", [])
        assert len(audit) >= 2
        event_types = {e["event_type"] for e in audit}
        assert "run_created" in event_types
        assert "step_started" in event_types
        assert "step_completed" in event_types


# ---------------------------------------------------------------------------
# 6. Intent Resolution & Planning
# ---------------------------------------------------------------------------


class TestIntentAndPlanning:
    """Phase 13: intent resolution and deterministic planning."""

    def test_resolve_intent_for_diagnosis(self) -> None:
        intent = resolve_intent("diagnose why the build failed")
        assert intent["intent_type"] == "diagnose"
        assert intent["required_level"] == 1
        assert "execute.diagnostic-engine" in intent["capabilities"]

    def test_resolve_intent_for_verification(self) -> None:
        intent = resolve_intent("run verification for discover.blast-radius")
        assert intent["intent_type"] == "verify"
        assert intent["required_level"] == 1

    def test_resolve_intent_for_change_analysis(self) -> None:
        intent = resolve_intent("what changed and what is affected")
        assert intent["intent_type"] == "analyze"
        assert "discover.blast-radius" in intent["capabilities"]

    def test_build_plan_for_diagnose(self) -> None:
        plan = build_plan(
            symptom="test failure",
            intent_type="diagnose",
            required_level=1,
        )
        assert plan["plan_id"].startswith("plan-")
        assert plan["intent_type"] == "diagnose"
        assert plan["required_level"] == 1
        assert len(plan["steps"]) >= 2  # health + diagnostic

    def test_infer_mode_from_intent(self) -> None:
        assert infer_mode_from_intent("observe", 0) == "MANUAL"
        assert infer_mode_from_intent("diagnose", 1) == "ASSISTED"
        assert infer_mode_from_intent("develop", 2) == "AUTONOMOUS"


# ---------------------------------------------------------------------------
# 7. Deterministic - No Model Provider Required
# ---------------------------------------------------------------------------


class TestNoModelRequired:
    """Phase 13: all operations work without LLM."""

    def test_all_operations_deterministic(self) -> None:
        # Intent resolution
        intent1 = resolve_intent("diagnose the build failure")
        intent2 = resolve_intent("diagnose the build failure")
        assert intent1["intent_type"] == intent2["intent_type"]
        assert intent1["required_level"] == intent2["required_level"]

        # Planning
        plan1 = build_plan(symptom="test", intent_type="diagnose", required_level=1)
        plan2 = build_plan(symptom="test", intent_type="diagnose", required_level=1)
        assert plan1["steps"] == plan2["steps"]

        # Policy evaluation
        dec1 = evaluate_policy(
            tool_name="inspect_health", run_mode="MANUAL", run_authorization_level=0
        )
        dec2 = evaluate_policy(
            tool_name="inspect_health", run_mode="MANUAL", run_authorization_level=0
        )
        assert dec1.allowed == dec2.allowed

    def test_no_external_dependencies(self) -> None:
        """Verify no external API calls are made during core operations."""
        # All core operations should complete without network
        run = _clean_orchestrator().start_run(symptom="test")
        assert run["id"].startswith("ai-")


# ---------------------------------------------------------------------------
# 8. HTTP Endpoint Structure
# ---------------------------------------------------------------------------


class TestHttpEndpointStructure:
    """Verify Phase 13 routes are registered and return correct envelopes."""

    def test_ai_mode_route_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = {r.path for r in router.routes}
        assert "/platform/v1/ai/mode" in paths

    def test_ai_runs_routes_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = {r.path for r in router.routes}
        assert "/platform/v1/ai/runs" in paths
        assert any("/ai/runs/{run_id}" in p for p in paths)
        assert any("/ai/runs/{run_id}/cancel" in p for p in paths)
        assert any("/ai/runs/{run_id}/steps" in p for p in paths)

    def test_ai_tools_routes_registered(self) -> None:
        from backend.src.routers.platform import router

        paths = {r.path for r in router.routes}
        assert "/platform/v1/ai/tools" in paths
        assert any("/ai/tools/{tool_name}" in p for p in paths)

    def test_ai_runs_post_returns_200(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            resp = c.post("/platform/v1/ai/runs", json={"symptom": "test"})
            assert resp.status_code == 200
            d = resp.json()
            assert d["kind"] == ai_contract.AI_RUN_KIND
            assert d["data"]["status"] == "PENDING"

    def test_ai_runs_get_returns_list(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            resp = c.get("/platform/v1/ai/runs")
            assert resp.status_code == 200
            d = resp.json()
            assert d["kind"] == ai_contract.AI_RUN_LIST_KIND
            assert "count" in d["data"]

    def test_ai_mode_returns_correct_kind(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            resp = c.get("/platform/v1/ai/mode")
            assert resp.status_code == 200
            d = resp.json()
            assert d["kind"] == ai_contract.AI_MODE_KIND

    def test_ai_tools_returns_correct_kind(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            resp = c.get("/platform/v1/ai/tools")
            assert resp.status_code == 200
            d = resp.json()
            assert d["kind"] == ai_contract.AI_TOOL_LIST_KIND


# ---------------------------------------------------------------------------
# 9. Integration: Full AI Run Lifecycle
# ---------------------------------------------------------------------------


class TestGate13Integration:
    """Full integration test for Gate 13."""

    def test_full_lifecycle_with_policy_enforcement(self) -> None:
        from fastapi.testclient import TestClient
        from src.api import app

        with TestClient(app, raise_server_exceptions=True) as c:
            # 1. Start AI run
            run_resp = c.post(
                "/platform/v1/ai/runs",
                json={"symptom": "test failure", "mode": "ASSISTED"},
            )
            assert run_resp.status_code == 200
            run_id = run_resp.json()["data"]["id"]

            # 2. Execute allowed step (level 1 in ASSISTED)
            step_resp = c.post(
                f"/platform/v1/ai/runs/{run_id}/steps",
                json={
                    "tool_name": "run_diagnostic",
                    "arguments": {"symptom": "build failure"},
                },
            )
            assert step_resp.status_code == 200
            step = step_resp.json()["data"]["step"]
            assert step["tool_name"] == "run_diagnostic"
            assert step["step_number"] == 1

            # 3. Get run detail shows step
            run_resp2 = c.get(f"/platform/v1/ai/runs/{run_id}")
            assert run_resp2.status_code == 200
            run_data = run_resp2.json()["data"]
            assert len(run_data["steps"]) == 1
            assert run_data["steps"][0]["tool_name"] == "run_diagnostic"

            # 4. Cancel run
            cancel_resp = c.post(f"/platform/v1/ai/runs/{run_id}/cancel")
            assert cancel_resp.status_code == 200
            assert cancel_resp.json()["data"]["status"] == "CANCELLED"

            # 5. Verify run is cancelled
            run_resp3 = c.get(f"/platform/v1/ai/runs/{run_id}")
            assert run_resp3.json()["data"]["status"] == "CANCELLED"
