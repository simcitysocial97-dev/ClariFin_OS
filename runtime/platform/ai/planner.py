"""AI Planner (Phase 13).

Produces deterministic plans with policy gates. Plans are sequences of
tool invocations with explicit authority checks. No LLM.
"""

from __future__ import annotations

from typing import Any


class PlanStep:
    """A single step in a deterministic plan."""

    def __init__(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        authority_level: int,
        depends_on: list[int] | None = None,
        description: str = "",
    ):
        self.tool_name = tool_name
        self.arguments = arguments
        self.authority_level = authority_level
        self.depends_on = depends_on or []
        self.description = description


class Plan:
    """A deterministic plan for an AI run."""

    def __init__(
        self,
        plan_id: str,
        symptom: str,
        intent_type: str,
        steps: list[PlanStep],
        required_level: int,
        policy_check: bool = True,
    ):
        self.plan_id = plan_id
        self.symptom = symptom
        self.intent_type = intent_type
        self.steps = steps
        self.required_level = required_level
        self.policy_check = policy_check
        self.status = "PENDING"
        self.current_step = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "symptom": self.symptom,
            "intent_type": self.intent_type,
            "required_level": self.required_level,
            "steps": [
                {
                    "tool_name": s.tool_name,
                    "arguments": s.arguments,
                    "authority_level": s.authority_level,
                    "depends_on": s.depends_on,
                    "description": s.description,
                }
                for s in self.steps
            ],
            "policy_check": self.policy_check,
        }


# ---------------------------------------------------------------------------
# Built-in plan templates
# ---------------------------------------------------------------------------

PLAN_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "observe": [
        {
            "tool": "inspect_health",
            "args": {},
            "level": 0,
            "desc": "Get system health snapshot",
        },
    ],
    "diagnose": [
        {
            "tool": "inspect_health",
            "args": {},
            "level": 0,
            "desc": "Get health baseline",
        },
        {
            "tool": "run_diagnostic",
            "args": {"symptom": "{symptom}"},
            "level": 1,
            "desc": "Run deterministic diagnostic",
        },
    ],
    "verify": [
        {
            "tool": "run_verification_capability",
            "args": {"capability_id": "{capability_id}"},
            "level": 1,
            "desc": "Run targeted verification",
        },
    ],
    "analyze": [
        {
            "tool": "compute_change_intelligence",
            "args": {},
            "level": 1,
            "desc": "Compute blast radius and stale evidence",
        },
        {
            "tool": "compare_runs",
            "args": {"current": "LAST", "baseline": "LAST_PASS"},
            "level": 1,
            "desc": "Compare with last pass",
        },
    ],
    "develop": [
        {
            "tool": "propose_patch",
            "args": {"description": "{symptom}"},
            "level": 2,
            "desc": "Propose code change",
        },
    ],
}


def build_plan(
    *,
    symptom: str,
    intent_type: str,
    required_level: int,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic plan from intent.

    Returns a plan dict that can be executed step by step.
    """
    import uuid

    template = PLAN_TEMPLATES.get(intent_type, PLAN_TEMPLATES["observe"])
    steps = []

    for i, tpl in enumerate(template):
        # Substitute placeholders
        args = {}
        for k, v in tpl["args"].items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                key = v[1:-1]
                if key == "symptom":
                    # Prefer explicit symptom argument; fall back to context
                    args[k] = (
                        symptom
                        if symptom
                        else (context.get("symptom", "") if context else "")
                    )
                elif key == "capability_id":
                    args[k] = context.get("capability_id", "") if context else ""
                    if not args[k] and symptom:
                        # Try to extract capability_id if mentioned in symptom (heuristic)
                        args[k] = ""
                else:
                    args[k] = v
            else:
                args[k] = v

        steps.append(
            {
                "step_number": i + 1,
                "tool_name": tpl["tool"],
                "arguments": args,
                "authority_level": tpl["level"],
                "depends_on": [],
                "description": tpl["desc"],
            }
        )

    plan_id = f"plan-{uuid.uuid4().hex[:8]}"
    return {
        "plan_id": plan_id,
        "symptom": symptom,
        "intent_type": intent_type,
        "required_level": required_level,
        "steps": steps,
        "status": "PENDING",
        "current_step": 0,
    }
