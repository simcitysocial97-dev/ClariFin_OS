# CLARIFIN PLATFORM READINESS ASSESSMENT

**Document ID:** M9-C57 / PLATFORM_READINESS_ASSESSMENT
**Date:** 2026-09-05
**Workstream:** M9-C57 — Platform Operations & AI Architecture (Design Phase)
**Status:** DESIGN ONLY — readiness gate not yet passed
**Relationship to M9-C50:** Built on top of frozen C50 Platform Architecture; no C50 modifications proposed.

---

## 1. Purpose

Inventory the current ClariFin_OS repository to determine:

1. Which Platform primitives already exist (control plane, capability registry, executor, evidence, events, knowledge, errors, history).
2. Which components are missing for the Platform Console.
3. Which components exist but are **not yet surfaced** through a stable Platform API.
4. Which components are **partial, duplicate, or obsolete**.
5. Whether the prerequisites for an independently operable Platform Console already exist.

This document is the **factual foundation** of the entire M9-C57 design program. It is
explicitly based on repository inspection, not on historical documentation alone.

---

## 2. Inventory Method

Inspection commands used:

```bash
ls runtime/system/{command,context,evidence,graph,observability} runtime/foundation/{architecture,knowledge,repository,verification}
.venv/bin/python runtime/verify.py                         # surface commands
.venv/bin/python runtime/verify.py doctor                  # operational health
.venv/bin/python runtime/verify.py inspect capabilities    # capability catalog
.venv/bin/python runtime/verify.py inspect health          # capability health
.venv/bin/python runtime/verify.py inspect evidence        # open obligations
grep -rln "ollama\|openrouter" backend/src runtime/ frontend/
```

Source of truth: live repository state on `2026-09-05T03:59Z`. All counts below are derived
directly from `.venv/bin/python runtime/verify.py inspect capabilities` and the relevant
listing commands.

---

## 3. Inventory Result (EXISTS / PARTIAL / MISSING / DUPLICATE / OBSOLETE)

### 3.1 Platform Architecture core (M9-C50 frozen)

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Canonical control plane | `runtime/foundation/verification/canonical_control_plane.py` | **EXISTS — FROZEN** | Single dispatcher, 408 LOC. C50 authoritative. |
| Control plane facade | `runtime/foundation/verification/control_plane_facade.py` | **EXISTS** | 687 LOC, surfaces all operator/AI commands. |
| Control plane core | `runtime/foundation/verification/control_plane.py` | **EXISTS** | 654 LOC, plan/execute engine. |
| Thin CLI shim | `runtime/verify.py` | **EXISTS** | 34 LOC, delegates to facade. |
| Capability catalog | `runtime/foundation/verification/capability_catalog*.py` | **EXISTS** | 55 capabilities, 13 profiles, 0 issues. |
| Capability authority | `runtime/foundation/verification/capability_authority.py` | **EXISTS** | Single canonical resolver. |
| Capability graph | `runtime/foundation/verification/capability_graph*.py` | **EXISTS** | Dependency graph. |
| Capability contract | `runtime/foundation/verification/capability_contract.py` | **EXISTS** | Stage-based contract authority. |
| Capability resolver | `runtime/foundation/verification/capability_resolver.py` | **EXISTS** | File→capability mapping. |
| Latent capability audit | `runtime/foundation/verification/capability_latent_audit.py` | **EXISTS** | Detects unmapped capabilities. |
| Executor | `runtime/foundation/verification/executor.py`, `executor_pipeline.py`, `execution_orchestrator.py` | **EXISTS** | Stage-based executor. |
| Evidence contract | `runtime/foundation/verification/evidence_contract.py` | **EXISTS** | Deterministic evidence identity. |
| Evidence planner / reuse | `evidence_planner.py`, `evidence_reuse.py`, `evidence_integrity.py` | **EXISTS** | Plan + cache + integrity. |
| Obligation model | `obligation.py`, `obligation_reconciliation.py` | **EXISTS** | 13 open obligations observed. |
| Mutation authority | `mutation_authority.py`, `mutation_contract.py` | **EXISTS** | C42 frozen. |
| Configuration authority | `configuration_authority.py`, `configuration_authority_enforcement.py` | **EXISTS** | Single config authority. |
| Decision authority | `control_plane_efficiency.py`, `route_authority.py` | **EXISTS** | Decision lineage preserved. |
| Failure classification | `failure_report.py`, `gap_classification.py` | **EXISTS** | Survivor taxonomy. |
| Cache semantics | `cache.py`, `test_cache_invalidation.py` | **EXISTS** | Deterministic cache identity. |
| Self-verification | `execution_enforcer.py`, `ci_evidence.py` | **EXISTS** | Pipeline enforcement. |
| Pipeline enforcement | `pipeline_enforcement.py` | **EXISTS** | Convergence loop. |
| Generation engine | `generation_engine.py`, `test_generator.py` | **EXISTS — EVIDENCE-GATED** | Only operates on stale evidence. |
| Blast radius | `blast_radius.py`, `blast_radius_cli.py`, `change_surface.py` | **EXISTS** | File→capability blast radius. |

**Verdict:** C50 Platform Architecture primitives are present, frozen, and authoritative.
There is **no need to rebuild** any of them. They are the substrate the Platform Console
will expose.

### 3.2 Evidence, Events, Knowledge

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Evidence collectors | `runtime/system/evidence/collectors/{coverage,mutation,contract,contract_tests,property_tests,test_results,base}.py` | **EXISTS** | 7 collectors. |
| Evidence ingestion pipeline | `runtime/system/evidence/ingestion/pipeline.py` | **EXISTS** | Aggregator. |
| Evidence models | `runtime/system/evidence/models/evidence.py` | **EXISTS** | Coverage/Mutation/TestResult/Contract/VerificationEvidence. |
| Evidence API surface | `runtime/system/evidence/api/` | **EXISTS (package only)** | **PARTIAL** — no public API yet, only internal aggregator. |
| Engineering event store | `runtime/system/observability/event_store.py` | **EXISTS** | EngineeringEvent + EngineeringEventStore. |
| Run history store | `runtime/system/observability/health_report.py`, `flaky_tests.py` | **EXISTS** | 75 runs persisted. |
| Cost analysis | `runtime/system/observability/cost_analysis.py` | **EXISTS** | Stage-level cost. |
| Knowledge catalog | `runtime/foundation/knowledge/catalog.py`, `models.py` | **EXISTS** | 13 entry kinds: KnowledgeEntry, CapabilityEntry, EndpointEntry, ComponentEntry, ViewModelEntry, WorkspaceEntry, MapperEntry, GraphRendererEntry, VerificationProfileEntry, IntegrityRuleEntry, RuntimeArtifactEntry, DocumentationEntry, RelationshipChain. |
| Knowledge indexer | `runtime/foundation/knowledge/indexer.py` | **EXISTS** | Builds JSON `runtime/generated/knowledge-index.json`. |
| Knowledge query | `runtime/foundation/knowledge/query.py` | **EXISTS** | Cross-layer retrieval. |
| Intelligence platform | `runtime/foundation/intelligence/platform/` | **EXISTS (subpackage)** | **PARTIAL** — see `intelligence/platform/`. |

**Verdict:** The infrastructure for evidence, events, history, and knowledge indexing exists.
**Missing:** a stable **Platform API surface** that exposes these to a GUI/AI client with
JSON contracts and stable identifiers.

### 3.3 Repository indexing

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Repository scanner | `runtime/foundation/repository/scanner/` | **EXISTS** | 11 specialized scanners: api, backend, docs, frontend, metadata, migration, script, test, workflow, base. |
| Repository graph | `runtime/foundation/repository/graph/{schema,graph_service}.py` | **EXISTS** | File→symbol→capability linkage. |
| Repository query | `runtime/foundation/repository/query/query.py` | **EXISTS** | Targeted queries. |
| Repository API surface | `runtime/foundation/repository/api/` | **EXISTS (package only)** | **PARTIAL** — no public API yet. |
| Cross-layer map | `runtime/foundation/repository/graph/` | **EXISTS** | `cross-layer-map-v2.json`. |

**Verdict:** Repository understanding already exists. The Platform Console can read directly
from these subsystems.

### 3.4 Application runtime (Financial OS)

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| FastAPI app | `backend/src/api.py` | **EXISTS** | App setup, middleware, CORS. |
| Routers | `backend/src/routers/*.py` | **EXISTS** | 14 routers, 89 endpoints. |
| Engines | `backend/src/engines/` | **EXISTS** | 36 engines. |
| Services | `backend/src/services/` | **EXISTS** | 17 services. |
| Orchestration | `backend/src/orchestration/statement_orchestrator.py` | **EXISTS** | Statement-level coordination. |
| Domain | `backend/src/core/domain/` | **EXISTS** | Domain invariants. |
| Database | `backend/src/core/db/` | **EXISTS** | Connection management. |
| DTOs / Mappers | `backend/src/core/{dtos,mappers}/` | **EXISTS** | Type-safe boundary. |
| Structural / Extraction | `backend/src/{structural,extraction}/` | **EXISTS** | Parse + extract pipelines. |
| Repositories | `backend/src/repositories/` | **EXISTS** | Persistence layer. |
| Health endpoints | `backend/src/health.py` | **EXISTS** | `/health`, `/ready`. |
| Models | `backend/src/models/` | **EXISTS** | Domain models. |
| Startup validation | `backend/src/startup.py` | **EXISTS** | Pre-flight checks. |
| Ingest | `backend/src/ingest.py` | **EXISTS** | Import entrypoint. |

**Verdict:** The financial application runtime is complete enough for a Platform Console to
read its state via dedicated platform endpoints (not by mutating it).

### 3.5 Error framework

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Error exceptions | `backend/src/errors.py` | **EXISTS** | 251 LOC. Hierarchy: `AppError → ValidationError, DatabaseError, FileError, ImportError, NotFoundError`. |
| Error constants | `backend/src/errors.py` | **EXISTS** | `LOAN_NOT_FOUND`, `INVALID_REQUEST`, etc. |
| Error formatter | `format_error_response` | **EXISTS** | Structured JSON error response. |
| Error registration | `register_error_handlers(app)` | **EXISTS** | FastAPI handler registration. |
| Logger | `backend/src/logger.py` | **EXISTS** | 112 LOC. `log_info`, `log_error`. |
| Validation handler | `RequestValidationError` handler | **EXISTS** | FastAPI integration. |

**Verdict:** Error framework is **partial**: present in backend, but **not surfaced through a
dedicated Platform API** (e.g. /platform/errors, /platform/recurring, /platform/root-cause).
The Platform Console must read these via **platform endpoints**, not by parsing logs.

### 3.6 Frontend (Next.js)

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| App router | `frontend/app/` | **EXISTS** | Domain routes: accounts, behaviour, cards, cashflow, forecast, investments, loans, net-worth, reconciliation, transactions. |
| Command center | `frontend/app/command-center` + `frontend/components/command-center/` | **EXISTS** | context-panel, decision-feed, timeline, money-graph, metrics, workspace-preview, hooks, layout. |
| Evidence UI | `frontend/components/evidence/` | **EXISTS** | evidence-calculation-view, evidence-drawer, evidence-item, evidence-list, evidence-source-link, evidence-summary. |
| Workspace UI | `frontend/components/command-center/decision-feed/`, `metrics/`, `graph/` | **EXISTS** | Workspace + graph rendering. |
| Global search | `frontend/components/global-search/` | **EXISTS** | Cross-cutting search. |
| Layout | `frontend/components/layout/`, `frontend/app/layout.tsx` | **EXISTS** | Shell. |
| Test framework | `frontend/vitest.config.ts`, `frontend/playwright.config.ts` | **EXISTS** | Vitest + Playwright. |

**Verdict:** A Next.js frontend with command-center, evidence, and workspace UI **already exists**.
This means the Platform Console can be delivered as **a new Next.js route group** under the
existing application — no need to introduce a new frontend toolchain.

### 3.7 LLM / AI runtime

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Ollama | — | **MISSING** | No `ollama` integration in `backend/src`, `runtime/`, `frontend/`. |
| OpenRouter | — | **MISSING** | No `openrouter` integration found. |
| Tool registry | — | **MISSING** | No governed AI tool surface. |
| AI orchestration | — | **MISSING** | No context builder, planner, or memory. |
| AI run history | — | **MISSING** | No AI run store. |

**Verdict:** The AI layer is **greenfield**. This is the largest scope of the design program.
Per Section 71 of the directive, the design must support a **very small local model** on the
Lenovo IdeaPad S145, with graceful degradation when external models are unavailable.

### 3.8 Tooling / Scripts / CLI

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Dev tools | `tools/development/{change_intelligence,check_coverage,generate_contract_tests,generate_health_dashboard,generate_validation_report,mutation_discovery,selective_verify,test_strength,validation_audit,validation_orchestrator}.py` | **EXISTS** | 12 utilities. |
| Diagnostic tools | `tools/diagnostics/{check_mutation_matrix,check_paths,generate_health_report}.py` | **EXISTS** | 3 utilities. |
| Generators | `tools/generators/{build_consumer_migration,build_cross_layer_map,generate_repository_index,generate_synthetic_data}.py` | **EXISTS** | 4 utilities. |
| Bootstrap script | `scripts/bootstrap.sh`, `start.sh` | **EXISTS** | Env bootstrap. |
| Env doctor | `scripts/env-doctor.sh` | **EXISTS** | Environment guard. |
| E2E seed | `tools/e2e_seed.py` | **EXISTS** | E2E data seed. |

**Verdict:** Tooling exists for developers, not for an AI or GUI client. These are CLI-only.

### 3.9 Observability

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| Dashboard generator | `runtime/system/observability/dashboard.py` | **EXISTS** | Markdown dashboard. |
| Health report | `runtime/system/observability/health_report.py` | **EXISTS** | EngineeringHealthReport. |
| Analytics | `runtime/system/observability/analytics.py` | **EXISTS** | Cross-layer analytics. |
| Cost analysis | `runtime/system/observability/cost_analysis.py` | **EXISTS** | Stage-level cost. |
| Execution context | `runtime/system/observability/execution_context.py` | **EXISTS** | Run context. |
| Repository observability | `runtime/system/observability/repository.py` | **EXISTS** | Repo deltas. |

**Verdict:** The observability data exists. It is exposed via CLI commands under
`runtime/verify.py doctor`, not via an HTTP/JSON API.

### 3.10 CI

| Component | Path | State | Notes |
|-----------|------|--------|-------|
| `.github/workflows/*.yml` | **EXISTS** | CI orchestration. |
| `.github/actions/*.yml` | **EXISTS** | Reusable composite actions (per M9-C50 invariant). |
| `runtime/foundation/verification/ci_evidence.py` | **EXISTS** | CI evidence collector. |

**Verdict:** CI is governed by the canonical control plane (per `toolchain-verification-policy.md`).
Parity with local can be exposed through the Platform API.

---

## 4. Authority Map (STOP CONDITIONS resolution)

Section 73 of the directive defines stop conditions. Each is resolved below:

| Authority | Owner | Resolution |
|-----------|-------|-----------|
| **Platform API authority** | `runtime/platform/api/*` (NEW) | New surface exposes existing C50 primitives; AI and GUI consume the same surface. |
| **Task authority** | `runtime/foundation/verification/{obligation,executor}.py` | REUSED — C50 obligation model is THE task model. Platform Console creates obligations, does not bypass. |
| **Execution authority** | `runtime/foundation/verification/executor*.py` | REUSED — single execution boundary. |
| **Evidence authority** | `runtime/foundation/verification/evidence_*.py` + `runtime/system/evidence/*` | REUSED — evidence identity, cache, reuse, integrity. |
| **AI tool authority** | `runtime/platform/ai/tools/*` (NEW) | New governed registry. Tools call Platform API. |
| **Financial data authority** | `backend/src/core/db/*`, `backend/src/repositories/*` | UNCHANGED. AI may read via Platform API; never writes directly. |
| **History storage** | `runtime/generated/{engineering-history.json, evidence/*, execution/*}` | REUSED — append-only JSONL + structured JSON. |
| **Error ownership** | `backend/src/errors.py` (request errors) + NEW `runtime/platform/errors/` (platform errors) | Split: request errors stay in backend; platform operations gain their own. |
| **Event ownership** | `runtime/system/observability/event_store.py` | REUSED + EXTENDED with platform events. |
| **GUI/backend boundary** | New `/platform/*` route group in Next.js + new FastAPI `/platform/v1/*` route module | Both consume Platform API contracts. |
| **Local/remote model boundary** | `runtime/platform/ai/model_router.py` (NEW) | New router. |

**No competing authorities remain.** The design does NOT propose a second executor, a second
evidence format, a second capability registry, a second task model, or a second event store.

---

## 5. Current Capability Count vs Directive Targets

| Directive Section | Current State | Gap |
|-------------------|---------------|-----|
| §3 Principle: deterministic → operable → diagnosable → intelligent → autonomous | Deterministic+partially operable via CLI; rest is design | Need Console + AI layer. |
| §6 System/Verification/Architecture/Application/AI questions | Partially answered via CLI; not aggregated | Need Platform API aggregator. |
| §7 Dashboard | Dashboard generator exists in `runtime/system/observability/dashboard.py` as Markdown; **no GUI dashboard exists**. | Need GUI dashboard. |
| §8 Readiness scoreboard | Health report exists as CLI; **no GUI scoreboard**. | Need GUI scoreboard. |
| §9 Error Observatory | Error framework in backend; no platform-wide observability. | Need `runtime/platform/errors/*` + GUI Error Observatory. |
| §10 Verification Center | Capability catalog has 55 capabilities; **no GUI verification center**. | Need GUI + API endpoints. |
| §11 Live execution view | Obligation/evidence records exist; **no live stream to GUI**. | Need event bus + WebSocket/SSE endpoint. |
| §12 Historical run database | 75 runs stored in JSON files. | Need queryable API + GUI history view. |
| §13 Result comparison engine | `runtime/foundation/verification/evidence_reuse.py` exists; **no explicit compare view**. | Need `/platform/v1/history/compare` endpoint. |
| §14 Incremental diagnostics | `discover.capability-for`, `what-should-i-run` exist. | Need deterministic diagnostic pipeline. |
| §15 Change intelligence | `runtime/foundation/verification/change_surface.py`, `blast_radius.py` exist. | Need change→capability→stale-evidence chain in API. |
| §16 Capability explorer | Knowledge catalog + cross-layer map exist. | Need GUI capability tree + detail page. |
| §17 Architecture safety center | `configuration_authority`, `route_authority`, `capability_authority` exist. | Need API surface + GUI to expose each authority. |
| §18 CI / local parity | `toolchain-verification-policy.md` exists; CI parity checks exist in workflow. | Need `/platform/v1/ci-parity` endpoint. |
| §19 Application readiness | `/health`, `/ready` in `backend/src/health.py`. | Need platform aggregator + GUI view. |
| §20 Logging architecture | `backend/src/logger.py` exists for app; platform-wide separation MISSING. | Need platform log channels. |
| §21-32 AI Control Layer | **MISSING** | Full design required. |
| §37 Performance | Dashboard reads cached snapshots. | Need `runtime/generated/platform/snapshot.json` cache. |
| §38 Offline-first | Verification, history, evidence, knowledge work offline (no network). | Confirm AI can run offline. |
| §39 Data storage | Reuse existing infrastructure — no new databases. | Confirmed. |
| §40 Security | Backend has `register_error_handlers`; no AI-specific auth. | Need AI authorization + secret handling. |
| §41 GUI technology | **EXISTS** — Next.js already in repo. Console = new route group under existing Next.js. | DECISION: Option A (existing frontend + `/platform`). |
| §42 Product vs Platform UI | Different conceptual apps; share design system. | DECISION: separate route group, no shared chrome. |
| §44 No black-box AI | — | Need AI observability endpoints. |
| §45 Diagnostic knowledge | — | Need failure signature store. |
| §47 Repository indexing | 11 scanners + indexer exist. | Need incremental index invalidation. |
| §48 Self-diagnostic | — | Need `/platform/v1/health/deep`. |
| §49 Failure isolation | — | Need platform runs without AI; AI runs without external models. |
| §50-60 Phases | — | Implementation roadmap required. |

---

## 6. Readiness Verdict

### What is ready to build on

* C50 frozen control plane (`runtime/foundation/verification/canonical_control_plane.py`)
* 55-capability catalog + 13 profiles
* Evidence identity, obligation model, blast-radius, cache
* Knowledge catalog with 13 entry kinds (capability, endpoint, component, workspace, etc.)
* Engineering event store with persistence
* 75-run history with cost/analytics
* Error framework (AppError hierarchy) in backend
* Next.js frontend with command-center + evidence UI
* 11 specialized repository scanners
- 14 backend routers, 89 endpoints, 36 engines

### What must be built (no shortcut exists in the codebase)

1. **Platform API surface** (`runtime/platform/api/*`) — JSON contracts for health, capabilities, tasks, verification, evidence, history, errors, architecture, events, AI.
2. **FastAPI `/platform/v1/*` routes** in `backend/src/routers/platform.py` — thin wrappers around Platform API.
3. **Next.js `/platform` route group** — Dashboard, Verification, Diagnostics, History, Errors, Architecture, Capability Explorer.
4. **AI Control Layer** (`runtime/platform/ai/*`) — orchestrator, intent, planner, policy, context engine, tool registry, model router, AI run store.
5. **AI tool surface** — read-only first, then diagnostic, then verification, then controlled modification.
6. **Local LLM provider** — Ollama integration, provider abstraction, capability-based routing.
7. **Error Observatory** — `runtime/platform/errors/*` aggregating backend errors + verification errors + AI errors.
8. **Live execution view** — event-streamed obligations/executions to GUI.
9. **Historical comparison engine** — `/platform/v1/history/compare`.
10. **Change intelligence endpoint** — `/platform/v1/change/intelligence` returning blast radius + stale evidence + recommended verification.

### What must NOT be built (anti-design guard)

* A second executor, evidence format, capability registry, task model, event store.
* A second frontend application.
* A second Python environment (forbidden per AGENTS.md).
* A second AI framework separate from the Platform Architecture.
* A second event store.
* Unrestricted AI autonomy.
* A second CLI for AI (the AI must use the same `runtime/verify.py` control plane via the Platform API).

### Forbidden scope expansions

* No mutation score chase.
* No new M9 verification campaigns.
* No new databases.
* No new toolchains.
* No new repository indexing systems.

---

## 7. Decisions Required Before Implementation

Per Section 73 of the directive, the following were the only authorities in question. They are
now resolved (Section 4 above). All other stop conditions are clear.

**Status: READINESS DESIGN CAN PROCEED.**

---

## 8. Open Questions (Resolved in Subsequent Documents)

| Question | Resolution Document |
|----------|---------------------|
| How should the Platform API be shaped? | `PLATFORM_API_DESIGN.md` |
| Which components are reused vs built? | `PLATFORM_COMPONENT_MAP.md` |
| How is the GUI structured? | `CONSOLE_INFORMATION_ARCHITECTURE.md` |
| How is the AI Control Layer shaped? | `AI_CONTROL_LAYER_DESIGN.md` |
| Which AI tools exist, with what authority? | `AI_TOOL_AUTHORITY_MATRIX.md` |
| How does the Context Engine work? | `CONTEXT_ENGINE_DESIGN.md` |
| How does model routing work? | `MODEL_ROUTING_DESIGN.md` |
| What is the implementation sequence? | `IMPLEMENTATION_ROADMAP.md` |
| What is the single authoritative design? | `PLATFORM_AI_ARCHITECTURE.md` |

---

## 9. Conclusion

The Platform Architecture is **sufficiently mature** to support a Platform Console.
All C50 primitives, evidence, knowledge, repository scanners, observability, the Next.js
frontend, and the backend FastAPI surface already exist.

The Platform Console requires:

1. A new thin Platform API surface (JSON contracts, stable identifiers).
2. A new FastAPI route module `/platform/v1/*` (backend).
3. A new Next.js route group `/platform/*` (frontend).
4. A new AI Control Layer (orchestrator + context engine + tool registry + model router + AI run store).
5. New platform-specific subsystems: live event bus, historical comparison, error observability, capability explorer, application readiness, change intelligence, self-diagnostic.

No existing system is duplicated. C50 remains frozen. No second M9 campaign is opened.