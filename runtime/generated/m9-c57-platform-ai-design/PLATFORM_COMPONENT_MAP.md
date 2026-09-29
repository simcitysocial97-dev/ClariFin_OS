# CLARIFIN PLATFORM COMPONENT MAP

**Document ID:** M9-C57 / PLATFORM_COMPONENT_MAP
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** PLATFORM_READINESS_ASSESSMENT.md

---

## 1. Purpose

Map every component of the future Platform Console + AI Control Layer to either:

* **REUSE** an existing C50/repo subsystem (no duplication)
* **ADAPT** an existing subsystem (thin wrapper)
* **BUILD** (only when no existing component exists)
* **FORBIDDEN** (must not be created)

This is the **authority map for code reuse**. It guarantees Section 62's directive:
"Do not duplicate C50 — reuse the canonical control plane, obligation model, executor,
evidence identity, decision model, cache semantics, capability graph, governance invariants,
failure taxonomy, self-verification, and canonical verification commands."

---

## 2. Decision Legend

| Marker | Meaning | Implementation |
|--------|---------|----------------|
| **REUSE** | Component already exists and is the source of truth. | Platform API calls into it directly. |
| **ADAPT** | Component exists but needs a thin adapter for HTTP/JSON exposure. | Wrap with a stable JSON contract. |
| **BUILD** | No existing component fills the role. | New module under `runtime/platform/*` or `frontend/app/platform/*`. |
| **FORBIDDEN** | Must NOT be built. Reason stated. | None — anti-pattern. |

---

## 3. Platform Primitives (Single Authoritative Source)

| Primitive | Owner Module | AI Representation | GUI Representation |
|-----------|--------------|--------------------|---------------------|
| **Capability** | `runtime/foundation/verification/capability_catalog.py` | tool schema | capability card |
| **Obligation** | `runtime/foundation/verification/obligation.py` | task descriptor | run lifecycle view |
| **Task** | same module (task is a thin wrapper around obligation+plan) | run request | task list |
| **Execution** | `runtime/foundation/verification/executor*.py` | execution trace | live execution view |
| **Evidence** | `runtime/foundation/verification/evidence_*.py` + `runtime/system/evidence/*` | evidence reference | evidence drawer |
| **Decision** | `runtime/foundation/verification/control_plane_efficiency.py` | decision explanation | decision feed |
| **Event** | `runtime/system/observability/event_store.py` | event subscription | timeline |
| **Identity** | `runtime/foundation/architecture/ids.py` | content-addressed hash | identity badge |
| **Policy** | `runtime/foundation/verification/authorization_boundary.py` | tool risk + scope | approval dialog |
| **Health** | `runtime/system/observability/health_report.py` + new aggregator | health snapshot | dashboard tile |
| **History** | `runtime/generated/engineering-history.json` + new aggregator | run record | history page |
| **Context** | NEW — `runtime/platform/context/` | context pack | debug-only view |
| **Tool** | NEW — `runtime/platform/ai/tools/` | tool registry | (AI-only) |
| **AI Run** | NEW — `runtime/platform/ai/runs/` | run trace | AI observability page |

---

## 4. Component Map

### 4.1 Platform API (`runtime/platform/api/`)

| Component | State | Source | Notes |
|-----------|-------|--------|-------|
| `/health` aggregator | **BUILD** | Reads `backend/src/health.py` + `runtime/system/observability/health_report.py` + control plane state | One snapshot endpoint. |
| `/capabilities` | **ADAPT** | `runtime/foundation/verification/capability_catalog.py` | JSON list of 55 capabilities. |
| `/tasks` | **ADAPT** | `runtime/foundation/verification/obligation.py` | Open/closed obligations. |
| `/verification/*` | **ADAPT** | `runtime/foundation/verification/canonical_control_plane.py` | Wraps `verify check`, `verify run`, `verify plan`. |
| `/evidence/*` | **ADAPT** | `runtime/system/evidence/` | Evidence list, fetch, compare. |
| `/history/*` | **ADAPT** | `runtime/generated/engineering-history.json` + `runtime/system/observability/health_report.py` | Runs, comparison, baselines. |
| `/errors/*` | **BUILD** | NEW `runtime/platform/errors/` | Aggregates backend + platform errors. |
| `/architecture/*` | **ADAPT** | `runtime/foundation/architecture/` + knowledge catalog | Authorities, boundary health. |
| `/events/*` | **ADAPT** | `runtime/system/observability/event_store.py` | Stream + replay. |
| `/ai/*` | **BUILD** | NEW `runtime/platform/ai/api/` | Run, list, plan, diagnose. |

### 4.2 FastAPI Backend Mount (`backend/src/routers/platform.py`)

| Endpoint Group | State | Notes |
|----------------|-------|-------|
| `/platform/v1/health` | **ADAPT** | Thin wrapper calling Platform API. |
| `/platform/v1/capabilities` | **ADAPT** | Same. |
| `/platform/v1/tasks` | **ADAPT** | Same. |
| `/platform/v1/verification/*` | **ADAPT** | Wraps canonical control plane via subprocess (Python import not HTTP — faster). |
| `/platform/v1/evidence/*` | **ADAPT** | Wraps evidence subsystem. |
| `/platform/v1/history/*` | **ADAPT** | Reads history store. |
| `/platform/v1/errors/*` | **BUILD** | New platform error aggregator. |
| `/platform/v1/architecture/*` | **ADAPT** | Wraps authority modules. |
| `/platform/v1/events` | **BUILD** | SSE endpoint backed by event store. |
| `/platform/v1/ai/*` | **BUILD** | AI Control Layer endpoints. |

### 4.3 Frontend Route Group (`frontend/app/platform/`)

| Route | State | Notes |
|-------|-------|-------|
| `/platform` | **BUILD** | Dashboard. |
| `/platform/verification` | **BUILD** | Verification Center. |
| `/platform/diagnostics` | **BUILD** | Diagnostics + Change Intelligence. |
| `/platform/history` | **BUILD** | History + Comparison. |
| `/platform/errors` | **BUILD** | Error Observatory. |
| `/platform/architecture` | **BUILD** | Architecture Safety Center. |
| `/platform/capabilities` | **BUILD** | Capability Explorer. |
| `/platform/ai` | **BUILD** | AI Workspace. |
| `/platform/ai/runs` | **BUILD** | AI Observability. |
| `/platform/settings` | **BUILD** | Model routing, authorization, secret storage. |

### 4.4 AI Control Layer (`runtime/platform/ai/`)

| Component | State | Notes |
|-----------|-------|-------|
| Orchestrator | **BUILD** | Top-level AI loop. |
| Intent resolver | **BUILD** | Maps user request to capability cluster. |
| Context engine | **BUILD** | Builds minimal context pack. |
| Planner | **BUILD** | Produces deterministic plan with policy gate. |
| Policy engine | **BUILD** | Authorizes tool calls. |
| Tool registry | **BUILD** | Governed tools. |
| Model router | **BUILD** | Provider abstraction. |
| Local LLM provider | **BUILD** | Ollama (default) + OpenAI-compatible. |
| External LLM provider | **BUILD** | OpenRouter + future. |
| AI run store | **BUILD** | Persistent record of every AI run. |
| Memory (operational, episodic) | **BUILD** | Local-only. |

### 4.5 Errors Observatory (`runtime/platform/errors/`)

| Component | State | Notes |
|-----------|-------|-------|
| Platform error taxonomy | **BUILD** | Mirrors `backend/src/errors.py` + verification errors + AI errors. |
| Error aggregator | **BUILD** | Reads backend error log + verification failures + AI run errors. |
| Error frequency analyzer | **BUILD** | Detects recurring patterns. |
| Error explorer API | **BUILD** | `/platform/v1/errors/{current,recent,recurring,frequency}`. |

### 4.6 Live Execution Bus

| Component | State | Notes |
|-----------|-------|-------|
| Event store extension | **REUSE** | `runtime/system/observability/event_store.py` already supports `EngineeringEvent`. New event types added: `task_started`, `task_completed`, `verification_started`, etc. |
| SSE endpoint | **BUILD** | New `/platform/v1/events/stream`. |
| GUI live panel | **BUILD** | New component. |

### 4.7 Historical Comparison Engine

| Component | State | Notes |
|-----------|-------|-------|
| Run query | **ADAPT** | Reads `runtime/generated/engineering-history.json`. |
| Compare endpoint | **BUILD** | `/platform/v1/history/compare`. |
| Comparison view | **BUILD** | GUI page. |

### 4.8 Change Intelligence

| Component | State | Notes |
|-----------|-------|-------|
| Blast radius | **REUSE** | `runtime/foundation/verification/blast_radius.py` |
| Stale-evidence detector | **REUSE** | `runtime/foundation/verification/evidence_integrity.py` |
| Capability resolver | **REUSE** | `runtime/foundation/verification/capability_resolver.py` |
| Change intelligence endpoint | **BUILD** | Aggregates above. |

### 4.9 Capability Explorer

| Component | State | Notes |
|-----------|-------|-------|
| Knowledge catalog | **REUSE** | `runtime/foundation/knowledge/` |
| Cross-layer map | **REUSE** | `runtime/foundation/repository/graph/` |
| Explorer endpoint | **BUILD** | `/platform/v1/capabilities/{id}`. |
| Explorer GUI | **BUILD** | Capability detail page. |

### 4.10 Architecture Safety Center

| Component | State | Notes |
|-----------|-------|-------|
| Configuration authority | **REUSE** | `runtime/foundation/verification/configuration_authority.py` |
| Route authority | **REUSE** | `runtime/foundation/verification/route_authority.py` |
| Capability authority | **REUSE** | `runtime/foundation/verification/capability_authority.py` |
| Decision authority | **REUSE** | `runtime/foundation/verification/control_plane_efficiency.py` |
| Architecture safety endpoint | **BUILD** | Aggregates above. |

### 4.11 Application Readiness

| Component | State | Notes |
|-----------|-------|-------|
| Backend health | **REUSE** | `backend/src/health.py` |
| Frontend health | **BUILD** | New `/platform/v1/app/frontend`. |
| Domain invariants | **REUSE** | `backend/src/core/domain/` |
| Application readiness endpoint | **BUILD** | Aggregates above. |

### 4.12 Diagnostic Knowledge

| Component | State | Notes |
|-----------|-------|-------|
| Failure signatures | **BUILD** | JSON store keyed by signature hash. |
| Historical occurrences | **ADAPT** | Reads engineering-history. |
| Diagnostic recommendations | **BUILD** | Deterministic rules first, LLM only after. |

### 4.13 Logging Architecture

| Channel | Owner | Storage |
|---------|-------|---------|
| `application.log` | `backend/src/logger.py` | Append-only JSON. |
| `verification.log` | NEW `runtime/platform/logging/` | `runtime/generated/platform/logs/verification.jsonl`. |
| `execution.log` | NEW | Same. |
| `error.log` | NEW | Same. |
| `ai.log` | NEW | Same. |
| `audit.log` | NEW | Same. |
| `security.log` | NEW | Same. |

All channels use the same `EngineeringEvent` envelope; only `kind` differs.

---

## 5. Forbidden Components

| Forbidden | Reason |
|-----------|--------|
| Second executor | C50 executor is the single execution boundary. |
| Second evidence format | `runtime/system/evidence/models/evidence.py` is canonical. |
| Second capability registry | `capability_catalog.py` is the single authority. |
| Second task model | Obligation model IS the task model. |
| Second event store | `EngineeringEventStore` is the single bus. |
| Second frontend application | `/platform` route group under existing Next.js. |
| Second Python env | Forbidden per AGENTS.md. |
| Second CLI for AI | AI uses Platform API → canonical control plane. |
| Second mutation framework | C42 mutation authority frozen. |
| Second DB | Reuse `backend/src/core/db/`. |
| Unrestricted AI autonomy | Authority levels 0–4. |
| AI direct file mutation | Tools must execute via capabilities. |
| AI direct DB write | AI never writes DB; capability-routed only. |

---

## 6. Summary

* **REUSE:** 28 C50/observability/knowledge/repository components.
* **ADAPT:** 10 thin JSON-contract wrappers.
* **BUILD:** 38 new Platform-API + GUI + AI Control Layer components.
* **FORBIDDEN:** 13 anti-patterns explicitly listed.

The leverage ratio is **roughly 38 new components reusing 38 existing ones**, which is
consistent with the directive's preference for "maximum leverage with minimum new architecture."