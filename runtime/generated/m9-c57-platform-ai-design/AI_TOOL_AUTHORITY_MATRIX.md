# CLARIFIN AI TOOL AUTHORITY MATRIX

**Document ID:** M9-C57 / AI_TOOL_AUTHORITY_MATRIX
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** AI_CONTROL_LAYER_DESIGN.md

---

## 1. Purpose

Define every governed AI tool, its authority level, its risk, its preconditions, its
authorization rule, and the underlying Platform API it ultimately invokes.

This is the **authoritative registry** for the AI Control Layer.

Tools are grouped by **authority level** (Section 27). The model cannot exceed its current
authority. Elevation is a configuration change, not an in-session capability.

---

## 2. Authority Levels (from AI_CONTROL_LAYER_DESIGN.md §4)

| Level | Description | Default enable |
|-------|-------------|----------------|
| 0 | Observe | YES |
| 1 | Analyze | YES |
| 2 | Development | NO (requires `policy.enable_development_tools=true`) |
| 3 | Controlled operations | NO (requires `policy.enable_workflow_tools=true` + per-task approval) |
| 4 | High-risk operations | NO (requires explicit per-call confirmation + audit) |

---

## 3. Tool Registry — Authority Level 0 (Observe)

| Tool | Risk | Authorization | Underlying Platform API | Evidence behavior |
|------|------|---------------|--------------------------|--------------------|
| `inspect_health` | none | none | `GET /platform/v1/health` | links latest snapshot |
| `inspect_capability` | none | none | `GET /platform/v1/capabilities/{id}` | links capability entry |
| `inspect_architecture` | none | none | `GET /platform/v1/architecture/authorities` | links authority health |
| `inspect_errors` | none | none | `GET /platform/v1/errors/recent` | links error record |
| `inspect_history` | none | none | `GET /platform/v1/history/runs` | links run record |
| `inspect_evidence` | none | none | `GET /platform/v1/evidence/{id}` | links evidence |
| `inspect_file` | low | none | `GET /platform/v1/repository/file?path=...` (reads via scanner) | links repo entry |
| `search_code` | low | none | `POST /platform/v1/repository/search` | links repo entries |
| `inspect_run` | none | none | `GET /platform/v1/history/runs/{id}` | links run |
| `inspect_ai_run` | none | none | `GET /platform/v1/ai/runs/{id}` | links AI run |
| `list_capabilities` | none | none | `GET /platform/v1/capabilities` | links capability list |
| `list_engines` | none | none | `GET /platform/v1/architecture/authorities` | links architecture |

All Level 0 tools are **read-only** and **side-effect free**. They never create evidence or
tasks. They only return existing state.

---

## 4. Tool Registry — Authority Level 1 (Analyze)

| Tool | Risk | Authorization | Underlying Platform API | Evidence behavior |
|------|------|---------------|--------------------------|--------------------|
| `diagnose_failure` | low | none | `POST /platform/v1/ai/diagnose` | links evidence + runs |
| `compare_runs` | low | none | `POST /platform/v1/history/compare` | links runs + evidence |
| `compute_change_intelligence` | low | none | `GET /platform/v1/change/intelligence` | links changes + capabilities |
| `run_verification_capability` | medium | none | `POST /platform/v1/verification/run` | creates evidence |
| `run_diagnostic` | medium | none | `POST /platform/v1/verification/run` (diagnostic profile) | creates evidence |
| `run_what_should_i_run` | medium | none | `POST /platform/v1/verification/run` (recommended) | creates evidence |
| `run_capability_group` | medium | none | `POST /platform/v1/verification/run/group` | creates evidence |
| `cancel_task` | medium | human confirm | `POST /platform/v1/tasks/{id}/cancel` | links existing task |

`run_*` tools create new tasks (obligations). They never bypass the canonical control plane.

---

## 5. Tool Registry — Authority Level 2 (Development)

**Disabled by default.** Require `policy.enable_development_tools=true`.

| Tool | Risk | Authorization | Underlying Platform API | Evidence behavior |
|------|------|---------------|--------------------------|--------------------|
| `propose_patch` | medium | human confirm | `POST /platform/v1/ai/patches` | links diagnosis evidence |
| `apply_patch` | high | human confirm + audit | `POST /platform/v1/ai/patches/{id}/apply` | creates patch evidence |
| `create_test` | medium | human confirm | `POST /platform/v1/ai/tests` | creates test evidence |
| `create_task` | medium | human confirm | `POST /platform/v1/tasks` | creates task evidence |

The Engineering Agent may call these tools. Each call must reference an `evidence_id`
supporting the proposed change.

---

## 6. Tool Registry — Authority Level 3 (Controlled operations)

**Disabled by default.** Require `policy.enable_workflow_tools=true` **and** per-task approval.

| Tool | Risk | Authorization | Underlying Platform API | Evidence behavior |
|------|------|---------------|--------------------------|--------------------|
| `run_workflow` | high | human per-task approval | `POST /platform/v1/workflow/run` | creates workflow evidence |
| `execute_business_action` | high | human per-task approval | `POST /platform/v1/workflow/action` | creates action evidence |
| `trigger_reconciliation` | high | human per-task approval | `POST /platform/v1/workflow/reconcile` | creates evidence |

Financial state mutations are restricted to Level 3+.

---

## 7. Tool Registry — Authority Level 4 (High-risk)

**Disabled by default.** Require explicit per-call confirmation + audit.

| Tool | Risk | Authorization | Underlying Platform API | Evidence behavior |
|------|------|---------------|--------------------------|--------------------|
| `destructive_migration` | critical | explicit confirm + audit | `POST /platform/v1/admin/migrate` | creates audit evidence |
| `bulk_financial_mutation` | critical | explicit confirm + audit | `POST /platform/v1/admin/financial-mutation` | creates audit evidence |
| `data_deletion` | critical | explicit confirm + audit | `POST /platform/v1/admin/delete` | creates audit evidence |
| `production_deployment` | critical | explicit confirm + audit | `POST /platform/v1/admin/deploy` | creates audit evidence |

These tools **must** reference an external human approver (out-of-band). The audit log
records the approver, the timestamp, and a session-bound confirmation token.

---

## 8. Forbidden Tools

These tools **must never** be created:

* `execute_shell` — no arbitrary shell command.
* `read_secret` — no API key / token exposure to the LLM.
* `write_database` — AI never writes directly to DB.
* `bypass_policy` — AI cannot elevate itself.
* `modify_frozen_file` — AI cannot modify C50 files without explicit human confirmation +
  audit. The list of frozen files is determined at design time:

  ```
  runtime/foundation/verification/canonical_control_plane.py
  runtime/foundation/verification/control_plane*.py
  runtime/foundation/verification/executor*.py
  runtime/foundation/verification/evidence_*.py
  runtime/foundation/verification/obligation*.py
  runtime/foundation/verification/capability_authority.py
  runtime/foundation/verification/configuration_authority*.py
  runtime/foundation/verification/cache.py
  runtime/foundation/architecture/ids.py
  runtime/AGENTS.md (operating contract)
  ```

* `exfiltrate_data` — no outbound network calls except via approved providers.

---

## 9. Tool Schema Example

```json
{
  "name": "diagnose_failure",
  "description": "Produce a deterministic + AI-assisted diagnosis for a failure.",
  "schema": {
    "type": "object",
    "properties": {
      "symptom": { "type": "string" },
      "run_id": { "type": "string" },
      "capability_id": { "type": "string" }
    },
    "required": ["symptom"]
  },
  "authorization": "none",
  "risk": "low",
  "preconditions": [
    { "kind": "policy.development_tools", "value": "disabled" }
  ],
  "output_contract": {
    "kind": "platform.ai_diagnose_result",
    "fields": ["deterministic", "ai_assisted"]
  },
  "evidence_behavior": "links",
  "cost_estimate": "low"
}
```

---

## 10. Authorization Enforcement

All tool calls flow through `runtime/platform/ai/policy.py::authorize()`:

```python
def authorize(tool: Tool, args: dict, session: CooperativeSession) -> AuthorizationDecision:
    if tool.authorization == "none":
        return AuthorizationDecision(allow=True)
    if tool.authorization == "human_confirm":
        return session.request_human_confirmation(tool, args)
    if tool.authorization == "policy_gate":
        if session.policy.allows(tool):
            return AuthorizationDecision(allow=True)
        return AuthorizationDecision(allow=False, reason="policy_denied")
    if tool.authorization == "per_task_approval":
        return session.request_per_task_approval(tool, args)
    return AuthorizationDecision(allow=False, reason="unknown_authorization")
```

`authorize()` runs **server-side** for every tool call. The client cannot bypass it.

---

## 11. Audit Trail

Every tool call writes an `EngineeringEvent`:

```json
{
  "kind": "ai_tool_call",
  "id": "sha256:...",
  "session_id": "ai-session-...",
  "tool": "diagnose_failure",
  "args_hash": "sha256:...",
  "authorization": "none",
  "result_kind": "ok | failed",
  "evidence_ids": [],
  "duration_ms": 12
}
```

Audit log channel: `runtime/generated/platform/logs/audit.jsonl`. Never pruned automatically.

---

## 12. Telemetry vs Privacy

* Telemetry: per-tool latency, success rate, model selection, token usage.
* Privacy: tool args are HASHED in audit logs unless `audit.include_args=true`. Tool args
  containing secrets are NEVER logged.

---

## 13. Acceptance Criteria

* Tool registry is the only entry point for AI actions.
* No tool exists outside the registry.
* No tool calls the executor or DB directly.
* Authorization is enforced server-side.
* Every tool call produces an audit event.
* Level 2+ tools are disabled by default.
* Forbidden tools are rejected at registration time (compile-time check).