# M9-C57 Phase 2 — Platform Service Aggregators — Progress

**Document ID:** M9-C57 / phase-02 / progress
**Date:** 2026-09-05
**Phase:** Phase 2 — Platform Service Aggregators (BAND A)
**Authorized objective:** Implement deterministic service adapters that aggregate existing platform subsystems.
**Execution rule:** One logical objective at a time. Read before modifying. Evidence is mandatory.

---

## 1. Execution start

- **Start (UTC):** 2026-09-05T09:05:31Z (immediately after user authorization "Proceed to Phase-2")
- **Operator session:** Kilo CLI (current session)
- **Authorized objective:** Phase 2 only. Bands B/C/D explicitly deferred.

---

## 2. Repository / design reconciliation

Per ``IMPLEMENTATION_ROADMAP.md`` Phase 2 ("These services must use existing authorities … Do not introduce a new persistent model for any of those domains"), the following C50 authorities were inspected before implementation:

| Authority | Module | Used by Phase 2 service |
|-----------|--------|-------------------------|
| Capability catalog | `runtime/foundation/verification/capability_catalog.py` | `capabilities.py`, `verification.py` |
| Planner + obligation set | `runtime/foundation/verification/control_plane_facade.py` + `obligation.py` | `tasks.py`, `verification.py`, `evidence.py`, `application.py`, `errors.py` |
| Blast-radius contract | `runtime/foundation/verification/blast_radius.py` | `change.py` |
| Change surface | `runtime/foundation/verification/change_surface.py` | `change.py` |
| Evidence integrity | `runtime/foundation/verification/evidence_integrity.py` | `errors.py` |
| Engineering event store | `runtime/system/observability/event_store.py` | `executions.py`, `events.py`, `history.py` |
| Analytics engine | `runtime/system/observability/analytics.py` | `health.py`, `history.py` |
| Health report | `runtime/system/observability/health_report.py` | `health.py` |
| Configuration authority | `runtime/foundation/verification/configuration_authority.py` | `architecture.py` |
| Route authority | `runtime/foundation/verification/route_authority.py` | `architecture.py` |
| Capability authority | `runtime/foundation/verification/capability_authority.py` | `architecture.py` |
| Control-plane efficiency | `runtime/foundation/verification/control_plane_efficiency.py` | `architecture.py` |

No C50 module was modified. No new persistent model was introduced.

### Pre-existing classification

| Phase 2 deliverable | Classification |
|---------------------|----------------|
| `runtime/platform/api/services/_helpers.py` | **MISSING** — created |
| `runtime/platform/api/services/capabilities.py` | **MISSING** — created |
| `runtime/platform/api/services/tasks.py` | **MISSING** — created |
| `runtime/platform/api/services/health.py` | **MISSING** — created |
| `runtime/platform/api/services/verification.py` | **MISSING** — created |
| `runtime/platform/api/services/executions.py` | **MISSING** — created |
| `runtime/platform/api/services/evidence.py` | **MISSING** — created |
| `runtime/platform/api/services/history.py` | **MISSING** — created |
| `runtime/platform/api/services/architecture.py` | **MISSING** — created |
| `runtime/platform/api/services/events.py` | **MISSING** — created |
| `runtime/platform/api/services/application.py` | **MISSING** — created |
| `runtime/platform/api/services/change.py` | **MISSING** — created |
| `runtime/platform/api/services/errors.py` | **MISSING** — created |
| `runtime/tests/test_platform_api_phase2.py` | **MISSING** — created |
| `runtime/platform/api/contracts/_primitives.py` | **MODIFIED** — relaxed `Timestamp` regex to accept fractional seconds (per ISO-8601). Phase 1 tests re-verified, no regressions. |

---

## 3. Design authority consulted

- `IMPLEMENTATION_ROADMAP.md` Phase 2 + Gate 2
- `PLATFORM_AI_ARCHITECTURE.md` §4.1 (REUSE/ADAPT/BUILD per component)
- `PLATFORM_API_DESIGN.md` §3 endpoint surface
- `PLATFORM_COMPONENT_MAP.md` §4.1 (component-by-component decision)
- `PLATFORM_READINESS_ASSESSMENT.md` §3.1–3.4 (authority inventory)
- `DESIGN_AUDIT.md` (forbidden-pattern check)

---

## 4. Requirements addressed

Per Phase 2 ("Establish deterministic service adapters that aggregate existing platform subsystems"):

| Service | Authority aggregated |
|---------|----------------------|
| `capabilities.build_capability_list` | `get_capability_catalog()` |
| `capabilities.build_capability_detail` | `get_capability_catalog().get(id)` |
| `capabilities.build_capability_graph` | `producers_of` / `consumers_of` |
| `tasks.build_task_list` | `ControlPlane()._plan_to_obligations()` |
| `tasks.build_task_detail` | live `ObligationSet` |
| `health.build_health_snapshot` | `EngineeringEventStore` + `AnalyticsEngine` + `EngineeringHealthReport` |
| `verification.build_verification_recommendation` | live `CapabilityResolution` |
| `verification.build_verification_run_request/result` | (typed projection; run execution is Phase 3) |
| `executions.build_execution_detail` | `EngineeringEventStore.iter_events` |
| `executions.build_execution_stream_event` | (typed projection for SSE) |
| `evidence.build_evidence_list/detail/compare` | live `ObligationSet.evidence` |
| `history.build_history_runs/run/baselines` | `engineering-history.json` artifact + `AnalyticsEngine` |
| `architecture.build_architecture_authorities` | `configuration_authority`, `route_authority`, `capability_authority`, `control_plane_efficiency` |
| `architecture.build_architecture_authority/boundaries/...` | projections from above |
| `events.build_events_list/stream_event` | `EngineeringEventStore.iter_events` |
| `application.build_app_*` | live `ObligationSet` open/closed counts |
| `change.build_change_intelligence` | `compute_blast_radius()` + `discover_working_tree_changes()` + planner |
| `errors.build_errors_*` | `build_evidence_integrity_report()` + live obligations |

---

## 5. Files changed

```
runtime/platform/api/services/__init__.py        (was empty placeholder; docstring added)
runtime/platform/api/services/_helpers.py        (NEW — 35 LOC)
runtime/platform/api/services/capabilities.py    (NEW — 145 LOC)
runtime/platform/api/services/tasks.py           (NEW — 122 LOC)
runtime/platform/api/services/health.py          (NEW — 109 LOC)
runtime/platform/api/services/verification.py    (NEW — 89 LOC)
runtime/platform/api/services/executions.py      (NEW — 99 LOC)
runtime/platform/api/services/evidence.py        (NEW — 138 LOC)
runtime/platform/api/services/history.py         (NEW — 169 LOC)
runtime/platform/api/services/architecture.py    (NEW — 184 LOC)
runtime/platform/api/services/events.py          (NEW — 78 LOC)
runtime/platform/api/services/application.py     (NEW — 113 LOC)
runtime/platform/api/services/change.py          (NEW — 109 LOC)
runtime/platform/api/services/errors.py          (NEW — 156 LOC)
runtime/platform/api/contracts/_primitives.py    (MODIFIED — Timestamp regex relaxed for fractional seconds)
runtime/tests/test_platform_api_phase2.py        (NEW — 410 LOC)
runtime/generated/m9-c57/phase-02/progress.md     (NEW — this file)
```

C50 modules touched: **0**

---

## 6. Implementation milestones

### Milestone 6.1 — Shared helpers (`_helpers.py`)

- `now_iso()` — UTC ISO-8601 ``Z``-suffix timestamp that satisfies the Phase 1 `Timestamp` contract primitive.
- `envelope()` — convenience wrapper around `success_envelope()` so service modules have one stable import.

### Milestone 6.2 — Capabilities service

- `build_capability_list` reads `get_capability_catalog()`, projects 55 entries to `CapabilityListItem`.
- `build_capability_detail` returns one `CapabilityDetailEnvelope` or `None`.
- `build_capability_graph` derives upstream/downstream from `producers_of`/`consumers_of`.

### Milestone 6.3 — Tasks service

- `build_task_list` projects the live `ObligationSet` (13 open obligations observed).
- `build_task_detail` returns one envelope or `None`.
- Cancel is intentionally **not** implemented in Phase 2 (writes go through canonical control plane in Phase 3).

### Milestone 6.4 — Health service

- `build_health_snapshot` reads event store + analytics engine + health report.
- Top-level `platform` status is derived from `success_rate` thresholds (HEALTHY ≥95%, DEGRAD ≥80%, UNHEALTHY <80%).

### Milestone 6.5 — Verification service

- `build_verification_recommendation` derives recommended capabilities from the live planner's `directly_affected_capabilities` + `transitively_affected_capabilities`.
- Run request/result envelopes are projected (actual run execution is delegated to the canonical control plane in Phase 3).

### Milestone 6.6 — Executions service

- `build_execution_detail` joins events sharing one `execution_id` from the live event store.
- `build_execution_stream_event` projects one event for SSE.

### Milestone 6.7 — Evidence service

- Walks the live obligation set's evidence references.
- Compare is a **structural** projection (Phase 8 will add semantic comparison).

### Milestone 6.8 — History service

- Prefers `engineering-history.json` artifact; falls back to `EngineeringEventStore` derivation.
- Baselines are derived from analytics engine counts.

### Milestone 6.9 — Architecture service

- Aggregates `configuration_authority`, `route_authority`, `capability_authority`, `control_plane_efficiency`.
- Five findings envelopes (boundaries, duplicates, bypasses, deprecations, unmapped) all return `ArchitectureFindingsEnvelope` with the shared shape.

### Milestone 6.10 — Events service

- `build_events_list` reads the live event store.
- `build_events_stream_event` projects one event for SSE.

### Milestone 6.11 — Application service

- Five endpoints (`/app/backend`, `/app/frontend`, `/app/domain`, `/app/financial`, `/app/workflows`).
- Backend/frontend/workflows derive from live obligation counts.

### Milestone 6.12 — Change intelligence service

- Uses `compute_blast_radius()` + `discover_working_tree_changes()` + planner.
- Risk is computed from `is_fail_closed` + escalation conditions + affected capability counts.

### Milestone 6.13 — Errors service

- `EvidenceIntegrityReport` failures + open obligations become error items.
- Frequency is bucketed by `(code, layer)`.
- Recurring items are those with `counter[code] > 1`.

---

## 7. Validation performed

### 7.1 Tests added

File: `runtime/tests/test_platform_api_phase2.py`

13 test classes, 39 tests:

1. `TestCapabilitiesService` (6) — list, list-items, detail-known, detail-unknown, graph-known, graph-unknown.
2. `TestTasksService` (3) — list real obligations, detail-known, detail-unknown.
3. `TestHealthService` (1) — snapshot reads real event store.
4. `TestVerificationService` (3) — recommendation uses real planner, run request, run result.
5. `TestExecutionsService` (1) — stream event round-trip.
6. `TestEvidenceService` (3) — list, detail-unknown, compare-unknown.
7. `TestHistoryService` (3) — runs, run-detail-unknown, baselines.
8. `TestArchitectureService` (4) — authorities, authority detail known/unknown, all five findings endpoints.
9. `TestEventsService` (2) — list round-trip, stream event round-trip.
10. `TestApplicationService` (5, parametrized) — all five `/app/*` endpoints.
11. `TestChangeIntelligenceService` (1) — risk reflects blast-radius signals.
12. `TestErrorsService` (4) — current/recent listings, recurring, frequency, detail-unknown.
13. `TestGate2EndToEnd` (3) — capability count matches catalog, task count matches obligations, change risk matches blast-radius signals.

### 7.2 Commands executed

```
.venv/bin/python -m pytest runtime/tests/test_platform_api_phase1.py runtime/tests/test_platform_api_phase2.py -v
```

Full transcript: `runtime/generated/m9-c57/phase-02/test-results.txt`

---

## 8. Failures and their classification

### 8.1 During Phase 2 development

| # | Test | Root cause | Fix |
|---|------|-----------|-----|
| 1 | Tasks list/detail (`Requirement.description`) | C50 `Requirement` dataclass uses `.rationale`, not `.description`. | Use `.rationale` in `_obligation_to_task_item` and `build_task_detail`. |
| 2 | Tasks list (`created_at` is a string) | C50 `Obligation.created_at` is already a pre-formatted ISO string in this codebase; my `_iso()` assumed a `datetime`. | Accept strings in `_iso()`; normalize trailing `+00:00` to `Z`. |
| 3 | Errors service (same `Requirement.description` bug) | Same root cause as #1. | Same fix. |
| 4 | Phase 1+2 round-trip (`Timestamp` regex) | Real C50 data carries fractional seconds in `created_at`/`timestamp` (e.g. `2026-09-05T09:30:22.779879Z`); the Phase 1 regex required `HH:MM:SS` exactly. | Relaxed `ISO8601_UTC_PATTERN` in `_primitives.py` to `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$`. Phase 1 re-run: 79/79 still pass. This is a faithful ISO-8601 implementation, not a regression. |
| 5 | Execution/Events stream tests (`EngineeringEvent` ctor) | `EngineeringEvent.__init__` requires `execution_context` keyword arg. | Pass `execution_context={"environment": "local"}` in tests. |

All 5 failures were **PHASE-2-INTRODUCED** and resolved before final test execution. Failure #4 is a Phase 1 contract correction (the original regex was overly strict).

### 8.2 Final test execution result

```
.venv/bin/python -m pytest runtime/tests/test_platform_api_phase1.py runtime/tests/test_platform_api_phase2.py -v
========================= 118 passed, 1 warning in 37.28s ========================
```

- Phase 1: 79/79 pass
- Phase 2: 39/39 pass
- Combined: 118/118 pass

Captured in full under `runtime/generated/m9-c57/phase-02/test-results.txt`.

### 8.3 Live data verification

The Phase 2 services emit real repository state. The samples captured in `runtime/generated/m9-c57/phase-02/live-envelope-samples.json` confirm:

```
capability_list         count=55  (matches the live M9-C51 catalog)
task_list               open=13 closed=0  (matches live obligation set)
health_snapshot         platform=UNHEALTHY  (success_rate=33.3% from analytics)
history_runs            total=75  (matches EngineeringEventStore.count())
change_intelligence     risk=HIGH  (working-tree dirty, escalations present)
architecture_authorities count=4  (the four C50 authorities)
errors_current          count=13  (open obligations surfaced as errors)
```

The `platform: UNHEALTHY` reading is **not a bug** — it is the honest projection of the live `success_rate=0.3333` from the analytics engine. The platform correctly reports its own state.

---

## 9. Blockers

None.

---

## 10. Evidence locations

| Artifact | Path |
|----------|------|
| Phase 2 progress record | `runtime/generated/m9-c57/phase-02/progress.md` (this file) |
| Phase 2 implementation | `runtime/platform/api/services/` |
| Phase 2 tests | `runtime/tests/test_platform_api_phase2.py` |
| Test execution transcript | `runtime/generated/m9-c57/phase-02/test-results.txt` |
| Live envelope samples | `runtime/generated/m9-c57/phase-02/live-envelope-samples.json` |
| File manifest (per-file SHA-256 + LOC) | `runtime/generated/m9-c57/phase-02/file-manifest.json` |

---

## 11. Deviations from design

### 11.1 Phase 1 contract correction: `Timestamp` regex

The Phase 1 `_primitives.py` regex was overly strict (`HH:MM:SS` exact). Phase 2 integration exposed that real C50 data carries fractional seconds. The regex was relaxed to:

```
^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{1,6})?Z$
```

This is faithful ISO-8601 with UTC `Z` suffix. Phase 1 tests still pass (they use no-fractional-seconds values).

### 11.2 Evidence compare projection

Per Phase 2 scope ("Do not introduce a new persistent model"), `evidence.compare` is a **structural** projection (diffs the two list rows). Semantic comparison (test failures, durations, recovered failures, …) is explicitly Phase 8 per `IMPLEMENTATION_ROADMAP.md`.

### 11.3 Cancel-task not implemented

Phase 2 is read-only. The `tasks.cancel` endpoint is documented in the contract (Phase 1) but **not** wired to a service. Writes go through the canonical control plane in Phase 3.

### 11.4 Architecture findings envelopes may be empty

The five architecture-findings endpoints (boundaries, duplicates, bypasses, deprecations, unmapped) currently return zero-issue lists when the live authorities report no problems. This is correct behavior — the contract is empty by default and only surfaces real findings.

### 11.5 Forbidden-pattern check

- No second executor / second evidence format / second capability registry / second task model / second event store.
- No C50 modifications.
- No second Python environment.
- No HTTP layer (Phase 3 deferred).
- No new persistent models.
- No mock platform state for production paths.
- No LLM/AI surface (Bands C/D deferred).

---

## 12. Gate status

### Gate 2 (Platform API)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Health / capabilities / tasks / verification / executions / evidence / history / architecture / events / application / change services accessible | **PASS** | All 11 services implemented; 37 `build_*` functions exposed; 39 Phase 2 tests pass. |
| Services use existing authorities | **PASS** | Each service module imports from a frozen C50 module (no duplication, no shadow authority). |
| No new persistent model introduced | **PASS** | All state is read from existing event store / catalog / obligation set / artifact. |
| Real repository state | **PASS** | Live samples confirm: 55 capabilities, 13 open obligations, 75 runs, UNHEALTHY verification success rate. |
| No mock platform state for production paths | **PASS** | No mock objects anywhere in `runtime/platform/api/services/`. |
| All service tests pass | **PASS** | 39/39 Phase 2 tests + 79/79 Phase 1 tests = 118/118. |
| Envelopes satisfy Phase 1 contract | **PASS** | `TestGate2EndToEnd` and every per-service test round-trip through the Phase 1 Pydantic models. |

---

## 13. Final Phase 2 disposition

**CERTIFIED.**

Every Phase 2 requirement and Gate 2 criterion is satisfied with reproducible evidence:

- All 11 service adapters implemented as deterministic, real-authority aggregators.
- Each service emits a Phase 1 contract payload wrapped in the canonical envelope.
- No C50 modules touched; no new persistent models; no mock state.
- 39 Phase 2 tests + 79 Phase 1 tests = 118 tests passing.
- Live envelope samples prove real repository state flows through (55 capabilities, 13 obligations, 75 history runs, honest UNHEALTHY verification status, HIGH change-intelligence risk from a dirty working tree).

The repository is left in a clean, evidenced state ready for **Phase 3 — FastAPI Platform Mount** (which the user must explicitly authorize).

---

## 14. Code metrics (informational)

```
   35 lines  runtime/platform/api/services/_helpers.py
  145 lines  runtime/platform/api/services/capabilities.py
  122 lines  runtime/platform/api/services/tasks.py
  109 lines  runtime/platform/api/services/health.py
   89 lines  runtime/platform/api/services/verification.py
   99 lines  runtime/platform/api/services/executions.py
  138 lines  runtime/platform/api/services/evidence.py
  169 lines  runtime/platform/api/services/history.py
  184 lines  runtime/platform/api/services/architecture.py
   78 lines  runtime/platform/api/services/events.py
  113 lines  runtime/platform/api/services/application.py
  109 lines  runtime/platform/api/services/change.py
  156 lines  runtime/platform/api/services/errors.py
 1546 lines  TOTAL Phase 2 implementation (13 files)
  410 lines  runtime/tests/test_platform_api_phase2.py
   39 tests  collected & passing (Phase 2)
  +118       total Phase 1 + Phase 2 tests passing
```
