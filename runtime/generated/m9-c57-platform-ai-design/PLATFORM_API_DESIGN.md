# CLARIFIN PLATFORM API DESIGN

**Document ID:** M9-C57 / PLATFORM_API_DESIGN
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** PLATFORM_READINESS_ASSESSMENT.md, PLATFORM_COMPONENT_MAP.md

---

## 1. Purpose

Define the canonical JSON contracts for the Platform API surface. The Platform API is the
**single source of truth** for both:

* The Next.js `/platform` route group (GUI client).
* The AI Control Layer (governed tools).

It is implemented as a Python module under `runtime/platform/api/` and exposed to the
network through a thin FastAPI mount at `/platform/v1/*` in `backend/src/routers/platform.py`.

---

## 2. Design Principles

1. **Stable identity.** Every response carries `kind`, `id`, `version`, `generated_at`.
2. **Content-addressed where possible.** IDs are SHA-256 over canonical payload.
3. **Read-mostly.** Writes go through `/platform/v1/tasks` (which creates obligations), never
   directly to the DB.
5. **Stateless on the read path.** Writes append to existing event/evidence stores.
6. **Reuses C50 identifiers.** `task_id`, `execution_id`, `evidence_id`, `decision_id` formats
   are inherited from C50 verbatim — no new ID schemes.
7. **No LLM in the request path.** The Platform API is deterministic. LLM calls happen only
   inside the AI Control Layer when explicitly invoked.

---

## 3. Endpoint Surface (`/platform/v1/*`)

| Group | Endpoint | Method | Description |
|-------|----------|--------|-------------|
| **Health** | `/health` | GET | Aggregate health snapshot. |
| | `/health/deep` | GET | Component-level health (longer). |
| **Capabilities** | `/capabilities` | GET | List 55 capabilities. |
| | `/capabilities/{id}` | GET | Capability detail. |
| | `/capabilities/{id}/graph` | GET | Dependency subgraph. |
| **Tasks** | `/tasks` | GET | List open/closed obligations. |
| | `/tasks` | POST | Create obligation (with authorization). |
| | `/tasks/{id}` | GET | Obligation detail. |
| | `/tasks/{id}/cancel` | POST | Cancel obligation if allowed. |
| **Verification** | `/verification/capabilities` | GET | All verification capabilities. |
| | `/verification/run` | POST | Run a capability (creates task). |
| | `/verification/run/group` | POST | Run a group (subset). |
| | `/verification/run/full` | POST | Run full suite (high-risk, requires authorization). |
| | `/verification/capability/{id}/result` | GET | Last result. |
| | `/verification/what-should-i-run` | GET | Blast-radius-driven recommendation. |
| **Execution** | `/executions/{id}` | GET | Execution detail. |
| | `/executions/{id}/stream` | GET (SSE) | Live execution trace. |
| **Evidence** | `/evidence` | GET | List evidence. |
| | `/evidence/{id}` | GET | Evidence detail. |
| | `/evidence/by-execution/{id}` | GET | Evidence for execution. |
| | `/evidence/compare` | POST | Compare two evidence sets. |
| **History** | `/history/runs` | GET | Paginated history. |
| | `/history/runs/{id}` | GET | Single run. |
| | `/history/compare` | POST | Compare CURRENT vs LAST/LAST_PASS/KNOWN_GOOD/BASELINE. |
| | `/history/baselines` | GET | Known baselines. |
| **Errors** | `/errors/current` | GET | Recent errors (last hour). |
| | `/errors/recent` | GET | Recent errors (last 24h). |
| | `/errors/recurring` | GET | Recurring patterns. |
| | `/errors/frequency` | GET | Frequency report. |
| | `/errors/{id}` | GET | Error detail with affected workflow. |
| **Architecture** | `/architecture/authorities` | GET | List authorities. |
| | `/architecture/authority/{name}` | GET | Authority health. |
| | `/architecture/boundaries` | GET | Boundary violations. |
| | `/architecture/duplicates` | GET | Duplicate authorities. |
| | `/architecture/bypasses` | GET | Bypass attempts. |
| | `/architecture/deprecations` | GET | Deprecated calls still in use. |
| | `/architecture/unmapped` | GET | Unmapped capabilities. |
| **Change** | `/change/intelligence` | GET | Blast radius + stale evidence + recommended verification. |
| **Events** | `/events` | GET | Recent events. |
| | `/events/stream` | GET (SSE) | Live event stream. |
| **Application** | `/app/backend` | GET | Backend readiness. |
| | `/app/frontend` | GET | Frontend readiness. |
| | `/app/domain` | GET | Domain invariants. |
| | `/app/financial` | GET | Financial arithmetic integrity. |
| | `/app/workflows` | GET | Workflow readiness. |
| **AI** | `/ai/chat` | POST | Send a user message to AI Control Layer. |
| | `/ai/runs` | GET | List AI runs. |
| | `/ai/runs/{id}` | GET | AI run detail. |
| | `/ai/runs/{id}/trace` | GET | Full trace. |
| | `/ai/tools` | GET | Tool registry. |
| | `/ai/providers` | GET | Model providers + capabilities. |
| | `/ai/diagnose` | POST | Deterministic diagnostic (AI-assisted). |

---

## 4. Response Envelope

Every endpoint returns:

```json
{
  "kind": "platform.health_snapshot",
  "version": "1.0.0",
  "generated_at": "2026-09-05T03:59:00Z",
  "id": "sha256:<hex>",
  "data": { ... }
}
```

Errors:

```json
{
  "kind": "platform.error",
  "version": "1.0.0",
  "generated_at": "...",
  "id": "sha256:<hex>",
  "error": {
    "code": "TASK_NOT_FOUND",
    "layer": "platform.tasks",
    "message": "No task with id obl-xxx",
    "evidence_id": "sha256:...",
    "capability_id": "..."
  }
}
```

---

## 5. Concrete Examples

### `/platform/v1/health`

```json
{
  "kind": "platform.health_snapshot",
  "version": "1.0.0",
  "generated_at": "2026-09-05T03:59:00Z",
  "id": "sha256:...",
  "data": {
    "platform": "HEALTHY",
    "backend": "HEALTHY",
    "frontend": "HEALTHY",
    "database": "HEALTHY",
    "architecture": "SAFE",
    "verification": "CURRENT",
    "evidence": "VALID",
    "ai": "READY",
    "domains": [
      { "name": "Environment", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Repository", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Backend", "status": "HEALTHY", "last_check": "...", "source": "/health" },
      { "name": "Frontend", "status": "HEALTHY", "last_check": "...", "source": "/platform/v1/app/frontend" },
      { "name": "Database", "status": "HEALTHY", "last_check": "...", "source": "/ready" },
      { "name": "Domain Model", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "API Contracts", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Architecture Boundaries", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Verification", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Evidence", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Cache", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "CI", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Runtime Health", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Error Framework", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Observability", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "AI Runtime", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Security / Authorization", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Data Integrity", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Application Workflows", "status": "HEALTHY", "last_check": "...", "source": "..." },
      { "name": "Production Readiness", "status": "HEALTHY", "last_check": "...", "source": "..." }
    ]
  }
}
```

### `/platform/v1/capabilities`

```json
{
  "kind": "platform.capability_list",
  "version": "1.0.0",
  "id": "sha256:...",
  "data": {
    "count": 55,
    "categories": ["DISCOVERY", "PLANNING", "EXECUTION", "CERTIFICATION"],
    "items": [
      {
        "id": "discover.blast-radius",
        "name": "Blast-Radius Contract",
        "stage": "discovery",
        "cost": "low",
        "authorization": "none",
        "produces": ["blast_radius_contract", "evidence_invalidations"],
        "triggers": ["changed_file", "proposed_change"]
      },
      ...
    ]
  }
}
```

### `/platform/v1/history/compare`

Request:

```json
{
  "kind": "platform.history_compare_request",
  "data": {
    "current_run_id": "run-latest",
    "baseline": "LAST_PASS",
    "include_evidence": true
  }
}
```

Response:

```json
{
  "kind": "platform.history_compare_result",
  "id": "sha256:...",
  "data": {
    "current_run": { ... },
    "baseline_run": { ... },
    "delta": {
      "repository_changes": ["backend/src/..."],
      "test_results": { "passed_added": 2, "passed_removed": 1, "failed_added": 1 },
      "durations": { "current": 449, "baseline": 410 },
      "evidence_invalidated": ["sha256:..."],
      "new_obligations": ["obl-..."],
      "closed_obligations": [],
      "capability_state_changes": [
        { "capability": "discover.blast-radius", "from": "HEALTHY", "to": "DEGRAD", "evidence": "sha256:..." }
      ]
    }
  }
}
```

### `/platform/v1/ai/diagnose`

Request:

```json
{
  "kind": "platform.ai_diagnose_request",
  "data": {
    "symptom": "reconciliation failed in last run",
    "context": { "run_id": "run-latest", "capability_id": "reconciliation_engine.contract" }
  }
}
```

Response:

```json
{
  "kind": "platform.ai_diagnose_result",
  "id": "sha256:...",
  "data": {
    "deterministic": {
      "affected_capability": "reconciliation_engine.contract",
      "recent_changes": ["backend/src/engines/reconciliation/..."],
      "historical_failures": 4,
      "suggested_verification": ["discover.blast-radius", "execute.reconciliation-engine.contract"]
    },
    "ai_assisted": {
      "model": "local:qwen2.5-3b-instruct",
      "hypothesis": "Likely a state-shape mismatch after the recent ledger serializer change.",
      "evidence": ["sha256:..."],
      "uncertainty": "MEDIUM",
      "recommendation": "Run targeted reconciliation contract verification before opening a patch."
    }
  }
}
```

### `/platform/v1/ai/runs/{id}/trace`

```json
{
  "kind": "platform.ai_run_trace",
  "id": "sha256:...",
  "data": {
    "request": { "user_message": "Why did reconciliation fail?", "received_at": "..." },
    "model": { "provider": "local", "name": "qwen2.5-3b-instruct", "version": "..." },
    "context_pack_id": "sha256:...",
    "context_sources": ["knowledge", "history", "evidence"],
    "plan": [
      { "step": 1, "tool": "inspect_capability", "args": { "id": "reconciliation_engine.contract" } },
      { "step": 2, "tool": "compare_runs", "args": { "current": "run-latest", "baseline": "LAST_PASS" } },
      { "step": 3, "tool": "diagnose_failure", "args": { "signature": "recon.contract" } }
    ],
    "tool_calls": [
      { "step": 1, "tool": "inspect_capability", "result": "...", "duration_ms": 12, "status": "ok" },
      { "step": 2, "tool": "compare_runs", "result": "...", "duration_ms": 28, "status": "ok" },
      { "step": 3, "tool": "diagnose_failure", "result": "...", "duration_ms": 41, "status": "ok" }
    ],
    "evidence_ids": ["sha256:..."],
    "final_response": "...",
    "outcome": "DIAGNOSED",
    "duration_ms": 2100,
    "token_usage": { "input": 1240, "output": 220, "cost_usd": 0 }
  }
}
```

---

## 6. Authorization

All `/platform/v1/*` endpoints inherit from `runtime/foundation/verification/authorization_boundary.py`.

| Risk | Default behavior |
|------|------------------|
| `none` | Open (read-only endpoints). |
| `human_required` | Local user must approve (CLI flag or GUI dialog). |
| `ai_assisted` | Allowed for AI tools with policy gate. |
| `forbidden` | Rejected. |

AI tools cannot escalate. See `AI_TOOL_AUTHORITY_MATRIX.md`.

---

## 7. Versioning & Stability

* `/platform/v1/*` is the only stable prefix. Breaking changes require `/platform/v2/*`.
* All response envelopes include `version` matching the API major version.
* Optional `?include=` query parameter allows clients to request additional detail
  (e.g. `?include=evidence,decision`).

---

## 8. Streaming Endpoints

`/platform/v1/executions/{id}/stream` and `/platform/v1/events/stream` use Server-Sent Events
with the existing `EngineeringEvent` envelope:

```
event: task.created
data: {"id":"obl-abc","task":"reconcile","capability":"discover.blast-radius",...}

event: execution.started
data: {"id":"exec-xyz","task":"obl-abc",...}
```

The GUI consumes via the standard `EventSource` API. The AI consumes via its tool registry
(which subscribes to the same event bus internally).

---

## 9. Caching

The Platform API caches expensive endpoints in `runtime/generated/platform/snapshot.json`:

* `/health` — refreshed every 60s.
* `/capabilities` — refreshed on catalog change.
* `/history/compare` — refreshed per run.

Read paths always prefer cache unless `?nocache=1` is passed. This satisfies the directive's
Section 37 performance requirement: dashboard does not scan the entire repository.

---

## 10. Cross-Cutting Concerns

* **Correlation IDs:** every request carries `X-Correlation-Id` and the response echoes it.
* **Audit:** every write call appends to `audit.log`.
* **Secrets:** no API key, token, or model credential may appear in any response. Secrets are
  loaded server-side from environment only.
* **Tracing:** OpenTelemetry-compatible span IDs are added to `data.trace_id` for observability.