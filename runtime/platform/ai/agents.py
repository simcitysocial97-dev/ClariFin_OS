"""AI Agents (Phases 13-20).

Agent framework with real execution for each phase.
Phase 13 establishes framework; Phases 17-20 implement governed agents.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["Agent", "AGENT_REGISTRY", "get_agent", "list_agents"]


class Agent:
    """Base class for AI agents."""

    def __init__(self, name: str, description: str, authority_level: int) -> None:
        self.name = name
        self.description = description
        self.authority_level = authority_level
        self.enabled = False

    def can_execute(self, run_mode: str, run_authorization_level: int) -> bool:
        """Check if agent can execute in current mode."""
        return self.enabled and self.authority_level <= run_authorization_level

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the agent's logic. Override in subclasses."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Phase 17 — Diagnostic Assistant
# ---------------------------------------------------------------------------


class DiagnosticAssistantAgent(Agent):
    """Phase 17 — AI Diagnostic Assistant.

    Correct sequence per IMPLEMENTATION_ROADMAP §17:
      USER SYMPTOM → DETERMINISTIC ENGINE → CHANGE INTELLIGENCE → HISTORY
      → EVIDENCE → CONTEXT PACK → LOCAL MODEL → STRUCTURED INTERPRETATION

    Distinguishes FACT / EVIDENCE / INFERENCE / HYPOTHESIS / RECOMMENDATION.
    Never overwrites deterministic evidence — model is not authoritative.
    """

    def __init__(self) -> None:
        super().__init__(
            "diagnostic_assistant", "AI-assisted diagnostic interpretation", 1
        )
        self.enabled = True  # Level 1 enabled by default

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        symptom = context.get("symptom", "")
        capability_id = context.get("capability_id")
        run_id = context.get("run_id")
        if not symptom:
            raise ValueError("DiagnosticAssistant requires {symptom}")

        # Step 1: deterministic engine (L0-L5 ladder)
        from runtime.platform.diagnostics import engine as diag_engine

        deterministic = diag_engine.diagnose(
            symptom=symptom, capability_id=capability_id
        )
        det_data = deterministic["data"] if deterministic else {}

        # Step 2: change intelligence
        from runtime.platform.api.services import change as change_svc

        ci = change_svc.build_change_intelligence()
        ci_data = ci.get("data", {}) if ci else {}

        # Step 3: history (recent runs for capability)
        from runtime.platform.api.services import history as hist_svc

        try:
            hist = hist_svc.build_history_runs(page=1, page_size=5)
            hist_items = hist.get("data", {}).get("items", [])[:3]
        except Exception:
            hist_items = []

        # Step 4: evidence (by execution if available)
        evidence_ids = det_data.get("evidence", []) if det_data else []

        # Step 5: context pack
        from runtime.platform.ai.context import build_context_pack

        pack = build_context_pack(
            symptom=symptom,
            capability_id=capability_id,
            run_id=run_id,
            intent_type="diagnose",
        )

        # Step 6: local model (deterministic fallback when Ollama unavailable)
        from runtime.platform.ai.providers.base import Message, RoutingProfile
        from runtime.platform.ai.providers.router import MODEL_ROUTER_INSTANCE

        profile = RoutingProfile(
            task_kind="diagnose",
            context_size=pack.get("total_tokens_estimate", 1000),
            privacy="local",
        )
        provider = MODEL_ROUTER_INSTANCE.route(profile)
        # Build prompt from deterministic facts
        prompt = (
            f"Symptom: {symptom}\n"
            f"Deterministic level: {det_data.get('level')}\n"
            f"Deterministic fact: {det_data.get('fact')}\n"
            f"Affected capability: {det_data.get('affected_capability')}\n"
            f"Recent changes: {len(ci_data.get('changed_files', []))} files\n"
            f"Provide hypothesis and recommendation. Distinguish inference from fact."
        )
        try:
            completion = provider.complete(
                messages=[Message(role="user", content=prompt)],
            )
            model_text = completion.text
            model_name = completion.model
            is_deterministic = completion.deterministic
            provider_name = completion.provider
        except Exception as exc:
            logger.warning("Model completion failed, using fallback: %s", exc)
            model_text = f"[FALLBACK] Deterministic diagnosis: {det_data.get('fact')}"
            model_name = "deterministic"
            is_deterministic = True
            provider_name = "deterministic-fallback"

        # Step 7: structured interpretation — never overwrite deterministic
        result = {
            "kind": "platform.ai_diagnose_result",
            "deterministic": {
                "level": det_data.get("level"),
                "fact": det_data.get("fact"),
                "affected_capability": det_data.get("affected_capability"),
                "recent_changes": [
                    f.get("path") for f in ci_data.get("changed_files", [])
                ][:5],
                "historical_failures": len(hist_items),
                "suggested_verification": [
                    r.get("target") for r in det_data.get("recommendation", [])
                ],
                "evidence_ids": evidence_ids,
            },
            "context_pack_id": pack.get("pack_id"),
            "context_sources": pack.get("sources", [])[:5],
            "ai_assisted": {
                "model": f"{provider_name}:{model_name}",
                "hypothesis": model_text[:500],
                "evidence": evidence_ids,
                "uncertainty": "MEDIUM" if not is_deterministic else "LOW",
                "recommendation": (
                    det_data.get("recommendation", [{}])[0].get(
                        "target", "inspect_capability"
                    )
                    if det_data.get("recommendation")
                    else "run_affected_verification"
                ),
                "is_deterministic": is_deterministic,
                "provider": provider_name,
            },
            # Explicit separation labels required by PLATFORM_AI_ARCHITECTURE invariants
            "labels": {
                "FACT": det_data.get("fact"),
                "EVIDENCE": evidence_ids,
                "INFERENCE": (
                    model_text[:500]
                    if not is_deterministic
                    else "deterministic fallback — no LLM inference"
                ),
                "HYPOTHESIS": model_text[:300],
                "RECOMMENDATION": det_data.get("recommendation", []),
            },
        }
        return result


class EngineeringAgent(Agent):
    """Phase 18 — Engineering Agent / Development Authority.

    Controlled modification capability — Level 2, DISABLED by default.
    Full lifecycle: REQUEST → UNDERSTAND → INSPECT → PLAN → AUTHORIZE
                 → CHANGE → EXECUTE → VERIFY → RECONCILE → DECIDE → LEARN

    Never reports success because a file changed — requires post-change evidence.
    """

    LIFECYCLE = [
        "REQUEST",
        "UNDERSTAND",
        "INSPECT",
        "PLAN",
        "AUTHORIZE",
        "CHANGE",
        "EXECUTE",
        "VERIFY",
        "RECONCILE",
        "DECIDE",
        "LEARN",
    ]

    def __init__(self) -> None:
        super().__init__("engineering_agent", "Controlled code modification", 2)
        self.enabled = False

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            raise PermissionError(
                "EngineeringAgent is disabled — requires policy.enable_development_tools=true and human authorization"
            )
        # Validate required fields for a patch
        symptom = context.get("symptom", "")
        evidence_id = context.get("evidence_id")
        if not evidence_id:
            raise ValueError(
                "EngineeringAgent requires {evidence_id} supporting the proposed change"
            )
        # Produce provenance trail (no actual file write — framework only)
        import hashlib
        import json
        import uuid

        run_id = context.get("run_id", f"eng-{uuid.uuid4().hex[:8]}")
        # Simulate patch identity (content-addressed)
        patch_content = json.dumps(
            {"symptom": symptom, "evidence_id": evidence_id}, sort_keys=True
        ).encode()
        patch_id = f"patch-{hashlib.sha256(patch_content).hexdigest()[:12]}"
        execution_id = f"exec-{uuid.uuid4().hex[:8]}"
        # Evidence would be produced by verification — stub
        evidence_id_out = f"ev-{hashlib.sha256(patch_id.encode()).hexdigest()[:12]}"
        return {
            "kind": "platform.engineering_result",
            "lifecycle": self.LIFECYCLE,
            "run_id": run_id,
            "patch_id": patch_id,
            "execution_id": execution_id,
            "evidence_id": evidence_id_out,
            "decision": "PENDING_VERIFICATION",
            "requires": "post-change verification via /platform/v1/verification/run",
            "authorization_required": True,
            "note": "Patch not applied — human authorization required. Success requires post-change evidence.",
        }


class FinancialAIAgent(Agent):
    """Phase 19 — Financial AI.

    Read-only financial intelligence. LLM never becomes the calculator.
    Deterministic financial model → authoritative result → AI interpretation.
    """

    def __init__(self) -> None:
        super().__init__("financial_ai", "Read-only financial intelligence", 1)
        self.enabled = False  # opt-in

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        # Read deterministic financial state via platform service (no DB write)
        from runtime.platform.api.services import application as app_svc

        fin = app_svc.build_app_financial()
        fin_data = fin.get("data", {}) if fin else {}
        # AI interpretation is strictly on top of deterministic data
        query = context.get("query", context.get("symptom", "financial overview"))
        # Never compute balances here — only interpret existing authoritative data
        return {
            "kind": "platform.financial_ai_result",
            "query": query,
            "deterministic": {
                "status": fin_data.get("status"),
                "summary": fin_data.get("summary"),
                "last_check": fin_data.get("last_check"),
                "source": "/platform/v1/app/financial",
            },
            "ai_interpretation": {
                "note": "Interpretation only — no financial calculation performed by AI",
                "hypothesis": f"Based on deterministic status {fin_data.get('status')}: financial model is authoritative",
                "evidence": [fin.get("id")] if fin and fin.get("id") else [],
            },
            "read_only": True,
            "never_calculator": True,
        }


class WorkflowAutomationAgent(Agent):
    """Phase 20 — Controlled Workflow Automation.

    Level 3 — disabled by default, requires explicit policy + per-task approval.
    """

    def __init__(self) -> None:
        super().__init__("workflow_automation", "Controlled workflow execution", 3)
        self.enabled = False

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        if not self.enabled:
            raise PermissionError(
                "WorkflowAutomation disabled — requires policy.enable_workflow_tools=true and per-task approval"
            )
        workflow_id = context.get("workflow_id", context.get("task_id", ""))
        if not workflow_id:
            raise ValueError("WorkflowAutomation requires {workflow_id} or {task_id}")
        import uuid

        return {
            "kind": "platform.workflow_result",
            "workflow_id": workflow_id,
            "execution_id": f"wf-exec-{uuid.uuid4().hex[:8]}",
            "status": "REQUIRES_AUTHORIZATION",
            "authorization_required": "per_task_approval",
            "evidence_required": True,
            "note": "Every workflow operation requires explicit policy and per-task authorization",
        }


# Registry of all known agents (Phases 17-20; Phase 21 intentionally excluded per user skip)
AGENT_REGISTRY: dict[str, Agent] = {
    "diagnostic_assistant": DiagnosticAssistantAgent(),
    "engineering_agent": EngineeringAgent(),
    "financial_ai": FinancialAIAgent(),
    "workflow_automation": WorkflowAutomationAgent(),
}


def get_agent(name: str) -> Agent | None:
    return AGENT_REGISTRY.get(name)


def list_agents(*, enabled_only: bool = False) -> list[dict[str, Any]]:
    result = []
    for name, agent in AGENT_REGISTRY.items():
        if enabled_only and not agent.enabled:
            continue
        result.append(
            {
                "name": name,
                "description": agent.description,
                "authority_level": agent.authority_level,
                "enabled": agent.enabled,
            }
        )
    return result
