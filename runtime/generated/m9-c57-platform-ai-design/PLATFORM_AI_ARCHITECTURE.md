# CLARIFIN PLATFORM OPERATIONS & AI ARCHITECTURE

**Document ID:** M9-C57 / PLATFORM_AI_ARCHITECTURE (authoritative)
**Date:** 2026-09-05
**Status:** DESIGN ONLY — readiness gate pending user approval
**Workstream:** M9-C57 — Platform Operations & AI Architecture
**Relationship to M9-C50:** Builds ON TOP OF frozen C50 Platform Architecture. No C50
modifications proposed without an explicit production defect ticket.

---

## 1. Objective

Define the smallest, strongest, fastest path to:

1. A standalone **Platform Operations Console** that operates, diagnoses, verifies, and
   inspects ClariFin_OS without an IDE.
2. A governed **AI Control Layer** that lets a small local LLM (and external models,
   optionally) inspect, diagnose, and propose changes — without bypassing the Platform
   Architecture.

The final system lets the user answer, in one place:

> "What is the current state of ClariFin_OS, what is healthy, what is broken, what changed,
> what has been verified, what remains unverified, what can I run, what happened previously,
> and what should I do next?"

The design respects Section 3 of the directive:

```
DETERMINISTIC → OBSERVABLE → OPERABLE → DIAGNOSTIC → INTELLIGENT → AUTONOMOUS
```

---

## 2. Companion Documents (M9-C57 design set)

| Document | Purpose |
|----------|---------|
| `PLATFORM_AI_ARCHITECTURE.md` (this) | Authoritative overview. |
| `PLATFORM_READINESS_ASSESSMENT.md` | Repository inventory, gap analysis, authority resolution. |
| `PLATFORM_COMPONENT_MAP.md` | REUSE / ADAPT / BUILD / FORBIDDEN per component. |
| `PLATFORM_API_DESIGN.md` | `/platform/v1/*` JSON contracts. |
| `CONSOLE_INFORMATION_ARCHITECTURE.md` | Next.js `/platform` route group + screens. |
| `AI_CONTROL_LAYER_DESIGN.md` | AI orchestrator, planner, agents, observability. |
| `AI_TOOL_AUTHORITY_MATRIX.md` | Tool registry, authority levels, policy. |
| `CONTEXT_ENGINE_DESIGN.md` | Minimal context packs. |
| `MODEL_ROUTING_DESIGN.md` | Provider abstraction + routing. |
| `IMPLEMENTATION_ROADMAP.md` | Phased delivery + acceptance criteria. |

---

## 3. Repository Reality (current)

### 4.1 What exists (frozen, REUSE)

* `runtime/foundation/verification/canonical_control_plane.py` — single C50 dispatcher.
* `runtime/foundation/verification/control_plane_facade.py` — operator/AI command surface.
* `runtime/foundation/verification/control_plane.py` — plan/execute engine.
* `runtime/foundation/verification/capability_catalog*.py` — **55 capabilities, 13 profiles, 0 issues**.
* `runtime/foundation/verification/{obligation, executor, evidence_*, blast_radius, change_surface, cache, capability_authority, configuration_authority, route_authority, control_plane_efficiency}.py` — single authorities.
* `runtime/foundation/architecture/{ids, models, provider, sources, cross_layer, discovery}.py` — identity + architecture.
* `runtime/foundation/knowledge/{catalog, indexer, models, query}.py` — knowledge index (13 entry kinds).
* `runtime/foundation/repository/{scanner, graph, query, scanner/api_scanner, backend_scanner, docs_scanner, frontend_scanner, metadata_scanner, migration_scanner, script_scanner, test_scanner, workflow_scanner}.py` — repository indexing (11 scanners).
* `runtime/system/evidence/{aggregator, collectors/{coverage, mutation, contract, contract_tests, property_tests, test_results, base}, ingestion/pipeline, models/evidence}.py` — evidence collection.
* `runtime/system/observability/{event_store, health_report, dashboard, analytics, cost_analysis, execution_context, repository, flaky_tests, dependency_growth}.py` — observability.
* `backend/src/errors.py` — `AppError` hierarchy (ValidationError, DatabaseError, FileError, ImportError, NotFoundError).
* `backend/src/logger.py` — `log_info`, `log_error`.
* `backend/src/health.py` — `/health`, `/ready`.
* `backend/src/api.py` + 14 routers + 89 endpoints — application API.
* `backend/src/{engines, services, orchestration, core/domain, core/db, core/dtos, core/mappers, repositories, structural, extraction, models, startup, ingest}/` — financial application runtime (36 engines, 17 services).
* `frontend/app/{accounts, behaviour, cards, cashflow, command-center, dashboard, forecast, investments, loans, net-worth, reconciliation, settings, transactions}/` — financial UI.
* `frontend/components/{command-center, evidence, global-search, layout}/` — existing reusable UI.
* `runtime/verify.py` — thin CLI shim.

### 4.2 What is missing (BUILD)

* A stable Platform API surface (`/platform/v1/*` JSON contracts).
* FastAPI mount for the Platform API in `backend/src/routers/platform.py`.
* Next.js `/platform` route group.
* AI Control Layer (`runtime/platform/ai/*`).
* AI tool registry, policy engine, audit.
* Context Engine.
* Model router + providers.
* Error Observatory platform aggregator.
* Live execution event stream to GUI.
* Historical comparison engine endpoint.
* Change intelligence endpoint.
* Application readiness aggregator.
* Self-diagnostic pipeline.
* Local Ollama integration.

### 4.3 What must NOT be built (FORBIDDEN)

* A second executor, evidence format, capability registry, task model, event store.
* A second frontend application.
* A second Python environment (forbidden per AGENTS.md).
* A second CLI for AI.
* A second mutation framework.
* A second database.
* Unrestricted AI autonomy.

---

## 5. Authority Resolution (Section 73 STOP conditions)

| Authority | Owner |
|-----------|-------|
| Platform API | `runtime/platform/api/*` (NEW) |
| Task | `runtime/foundation/verification/obligation.py` (REUSED, C50 frozen) |
| Execution | `runtime/foundation/verification/executor*.py` (REUSED, C50 frozen) |
| Evidence | `runtime/foundation/verification/evidence_*.py` + `runtime/system/evidence/*` (REUSED, C50 frozen) |
| AI tools | `runtime/platform/ai/tools/*` (NEW) |
| Financial data | `backend/src/core/db/*` + `backend/src/repositories/*` (UNCHANGED) |
| History | `runtime/generated/{engineering-history.json, evidence/*, execution/*}` (REUSED + extended) |
| Errors (request) | `backend/src/errors.py` (REUSED) |
| Errors (platform) | `runtime/platform/errors/*` (NEW) |
| Events | `runtime/system/observability/event_store.py` (REUSED + extended) |
| GUI/backend boundary | `/platform/v1/*` FastAPI + `/platform/*` Next.js |
| Local/remote model | `runtime/platform/ai/model_router.py` (NEW) |

**No competing authorities remain.**

---

## 6. Architectural Model

```
                         USER
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       PLATFORM GUI             AI WORKSPACE
       (Next.js /platform)      (Next.js /platform/ai)
              │                       │
              └───────────┬───────────┘
                          ▼
                  PLATFORM API  (/platform/v1/*)
                          │
                          ▼
             CANONICAL CONTROL PLANE  (C50, frozen)
                          │
                          ▼
        CAPABILITY / OBLIGATION GRAPH + EXECUTOR
                          │
                          ▼
                  EVIDENCE + HISTORY
                          ▲
                          │
                          │
                 AI CONTROL LAYER (NEW)
        ┌──────────┬──────────┬──────────┬──────────┐
        │Orchestr. │ Context  │ Planner  │ Policy   │
        │          │ Engine   │          │ Engine   │
        ├──────────┴──────────┴──────────┴──────────┤
        │ Tool Registry   Model Router              │
        │ Memory          Run Store                │
        └──────────────────────────────────────────┘
                          │
                          ▼
                  PLATFORM API  (consumes itself for evidence/permissions)
```

Rule: the AI **never** bypasses the Platform API. Every action is a governed tool call.

---

## 7. Platform Primitives (single source of truth)

| Primitive | Owner | AI representation | GUI representation |
|-----------|-------|--------------------|---------------------|
| Capability | `capability_catalog.py` | tool schema | capability card |
| Obligation | `obligation.py` | task descriptor | run lifecycle view |
| Task | same | run request | task list |
| Execution | `executor*.py` | execution trace | live execution view |
| Evidence | `evidence_*.py` + `runtime/system/evidence/*` | evidence reference | evidence drawer |
| Decision | `control_plane_efficiency.py` | decision explanation | decision feed |
| Event | `event_store.py` | event subscription | timeline |
| Identity | `runtime/foundation/architecture/ids.py` | content hash | identity badge |
| Policy | `authorization_boundary.py` | tool risk + scope | approval dialog |
| Health | `health_report.py` + new aggregator | health snapshot | dashboard tile |
| History | `engineering-history.json` + new aggregator | run record | history page |
| Context | `runtime/platform/ai/context/` (NEW) | context pack | debug-only view |
| Tool | `runtime/platform/ai/tools/` (NEW) | tool registry | (AI-only) |
| AI Run | `runtime/platform/ai/runs/` (NEW) | run trace | AI observability page |

---

## 8. AI Authority Levels (Section 27)

| Level | Description | Default |
|-------|-------------|---------|
| 0 Observe | inspect / summarize / diagnose / recommend | enabled |
| 1 Analyze | run diagnostics / tests / compare evidence | enabled |
| 2 Development | modify code / create tests / execute verification | disabled |
| 3 Controlled operations | state-changing app operations | disabled |
| 4 High-risk | destructive migrations / bulk financial mutations / data deletion / production deployment | disabled |

Elevation requires a configuration change. The AI cannot self-elevate.

---

## 9. Design Authority vs Execution Authority

This design set establishes the **design authority** for M9-C57. The **execution
authority** is `IMPLEMENTATION_ROADMAP.md`, which the prepared implementation plan
supersedes with a finer-grained 4-band / 21-phase sequence.

| Concern | Authority document |
|---------|---------------------|
| Architecture, primitives, authority model, invariants | This document + companion design set |
| Phase sequence, gates, evidence structure, execution rule, current authorized objective | `IMPLEMENTATION_ROADMAP.md` |
| Per-phase evidence, files changed, gate results | `runtime/generated/m9-c57/progress.md` (created during implementation) |

These authorities must not be confused. The design set defines **what** must be built
and **why**. The implementation roadmap defines **when**, **in what order**, and **how
completion is proven**. The progress file records **what actually happened**.

---

## 10. Implementation Bands and Phases (summary)

Full detail in `IMPLEMENTATION_ROADMAP.md`. Summary:

```
BAND A — PLATFORM FOUNDATION
  1  Platform Contract Foundation
  2  Platform Service Aggregators
  3  FastAPI Platform Mount
  4  Platform Snapshot & Read-Path Performance

BAND B — OPERATIONAL CONSOLE
  5  Console Shell + Dashboard
  6  Verification Center
  7  Execution, Evidence, Live State (SSE)
  8  History + Evidence + Comparison
  9  Error Observatory + Architecture + Capability Explorer

BAND C — DIAGNOSTIC PLATFORM
  10 Deterministic Change Intelligence
  11 Deterministic Self-Diagnostic Engine
  12 Application Readiness + Platform Self-Diagnostics

BAND D — AI CONTROL LAYER
  13 AI Control Layer Foundation  (governance WITHOUT model)
  14 Context Engine
  15 Model Router + Local Provider
  16 Level 0–1 Governed AI Tools
  17 AI Diagnostic Assistant
  18 Engineering Agent / Development Authority
  19 Financial AI
  20 Controlled Workflow Automation
  21 High-Risk Authority
```

Program-level gates A–H are defined in `IMPLEMENTATION_ROADMAP.md` §7.

---

## 11. Execution Discipline (from IMPLEMENTATION_ROADMAP.md §11)

The coding agent must execute one logical objective at a time:

```
READ AUTHORITATIVE PLAN
   ↓
SELECT NEXT UNGATED OBJECTIVE
   ↓
INSPECT CURRENT REPOSITORY
   ↓
IMPLEMENT ONLY THAT OBJECTIVE
   ↓
RUN TARGETED VALIDATION
   ↓
UPDATE progress.md
   ↓
REPORT GATE
```

Anti-patterns explicitly forbidden during execution:

* Redesigning settled architecture.
* Reopening C50.
* Creating parallel authorities.
* Skipping evidence.
* Batching unrelated objectives for convenience.
* Declaring completion from compilation alone.
* Introducing speculative infrastructure.

---

## 12. Current Authorized Objective

M9-C57 design work is complete. The next implementation objective is:

> **Phase 1 — Platform Contract Foundation.**

Implementation should begin by inspecting the existing repository for any partially
created `runtime/platform/`, `runtime/generated/m9-c57/`, or platform API contracts,
and **reconciling** them rather than blindly creating new files.

No implementation has begun. This document is the **design gate**, not the
implementation start signal.

---

## 13. Critical Constraint — Speed of Delivery (Section 67)

Mapped to the 4-band model:

### MUST HAVE NOW (Bands A + B, Phases 1–9)

Platform contracts, services, FastAPI mount, snapshot, Console shell, verification
center, live execution, history/evidence/comparison, errors/architecture/capabilities.

**No AI is required for these phases.** After Phase 9 the Console is already operationally
useful.

### SHOULD HAVE SOON (Band C, Phases 10–12)

Deterministic change intelligence, diagnostic engine, application readiness,
platform self-diagnostics. These make the platform intelligent about its own state
**without** an LLM.

### FUTURE (Band D, Phases 13–21)

AI governance first, then context engine, model router, governed tools, AI diagnostic
assistant, engineering agent, financial AI, controlled autonomy, high-risk authority.

The platform MUST become useful **before** all AI capabilities are built. Band D phases
may proceed in parallel with ClariFin_OS product development.

---

## 14. Architectural Invariants (do not violate)

1. **GUI → Platform API → Canonical Control Plane.** No bypass.
2. **AI → Platform API / governed tools.** No direct DB / filesystem / shell.
3. **One executor, one evidence format, one capability registry, one task model, one event store.**
4. **C50 is frozen.** No modification without an explicit production defect ticket.
5. **No second Python environment** (per AGENTS.md).
6. **All tool calls are audited.**
7. **External model providers are disabled by default.**
8. **Dashboard renders from cached snapshot.**
9. **AI diagnostics distinguish FACT / EVIDENCE / INFERENCE / HYPOTHESIS / RECOMMENDATION.**
10. **Financial truth remains deterministic.**

---

## 15. End-State User Experience (Section 66)

You open `/platform`.

Immediately:

```
SYSTEM HEALTHY
ARCHITECTURE SAFE
VERIFICATION CURRENT
NO CRITICAL ERRORS
3 NON-CRITICAL ISSUES
LAST VERIFIED: ...
CHANGES SINCE LAST PASS: ...
```

You click **Diagnose**. The platform performs low-cost deterministic analysis first.
Then the AI (if enabled) interprets the result and recommends the targeted verification.
You click **Run**. The task is created via the canonical control plane. Evidence appears.
You click **Inspect**. The full evidence trail is visible. You click **AI**. The AI proposes a
patch (Level 2 — requires human approval). You approve. The patch is applied. The platform
verifies it. The final record becomes:

```
REQUEST → DIAGNOSIS → PLAN → CHANGE → EXECUTION → EVIDENCE → VERIFICATION → DECISION
```

Everything visible. Everything auditable. Everything traceable.

---

## 16. Acceptance (Section 72)

### Architecture

* One Platform control plane. PASS.
* One capability authority. PASS.
* One task model. PASS.
* One execution boundary. PASS.
* One evidence model. PASS.
* One history model. PASS.
* One AI tool registry. PASS.

### GUI

* Independently operable. PASS (no AI required).
* Useful without AI. PASS.
* Exposes health / verification / errors / architecture / history / evidence / diagnostics. PASS.

### AI

* Optional. PASS.
* Replaceable. PASS (router).
* Locally executable. PASS (Ollama default).
* Governed. PASS (policy + audit).
* Observable. PASS (per-run trace).
* Evidence-aware. PASS.
* Context-efficient. PASS.
* Incapable of bypassing platform controls. PASS.

### Performance

* Dashboard does not require full repository scan. PASS (cached snapshot).
* Routine diagnosis does not require full-suite execution. PASS (diagnostic engine).
* Historical results are reusable. PASS.
* Context is incremental. PASS.
* Small model remains practical. PASS.

### Safety

* Financial truth remains deterministic. PASS.
* AI cannot directly mutate the database. PASS.
* High-risk actions require authorization. PASS.
* Failures cannot become successes. PASS.
* AI cannot fabricate evidence. PASS.
* AI cannot fabricate execution. PASS.
* Every executed operation is traceable. PASS.

**All acceptance criteria PASS by design. Implementation will verify empirically.**

---

## 17. STOP Conditions (Section 73)

Implementation MUST STOP and resolve if:

* A second control plane, executor, evidence format, capability registry, task model, or
  event store is introduced.
* C50 architecture is modified without an explicit production defect ticket.
* AI gains authority without a configuration change.
* An AI tool bypasses the policy engine.
* The dashboard requires a full repository scan to render.
* External providers are enabled by default.
* A second Python environment is introduced.
* A new M9 verification campaign is opened.

---

## 18. Final Statement

The Platform Console + AI Control Layer can be built entirely on top of the existing C50
Platform Architecture. No second anything is needed. The design prefers:

```
one reusable task system
one evidence model
one capability graph
one execution boundary
one audit log
one AI tool registry
```

over any duplication.

The goal is **maximum leverage with minimum new architecture.** The design achieves
this.

**Authorities:**

| Concern | Document |
|---------|----------|
| Architecture / primitives / invariants | This document (PLATFORM_AI_ARCHITECTURE.md) |
| Phase sequence / gates / evidence structure | `IMPLEMENTATION_ROADMAP.md` |
| Per-phase execution record | `runtime/generated/m9-c57/progress.md` (to be created at Phase 1) |

**Status: design complete. Awaiting user approval to begin Phase 1.**