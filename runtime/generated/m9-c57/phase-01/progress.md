# M9-C57 Phase 1 — Platform Contract Foundation — Progress

**Document ID:** M9-C57 / phase-01 / progress
**Date:** 2026-09-05
**Phase:** Phase 1 — Platform Contract Foundation (BAND A)
**Authorized objective:** Create the canonical internal Platform API contracts without exposing HTTP yet.
**Execution rule:** One logical objective at a time. Read before modifying. Evidence is mandatory.

---

## 1. Execution start

- **Start (UTC):** 2026-09-05T04:34:14Z
- **Implementation kickoff (UTC):** 2026-09-05T04:38:00Z
- **Operator session:** Kilo CLI (current session)
- **Authorized objective:** Phase 1 only. Bands B/C/D explicitly deferred.

---

## 2. Repository / design reconciliation

Per ``IMPLEMENTATION_ROADMAP.md`` §12 ("The implementation should begin by inspecting the existing repository for any partially-created ``runtime/platform/``, ``runtime/generated/m9-c57/``, or platform API contracts, and reconciling them rather than blindly creating new files"), the following inspection was performed.

### 2.1 Pre-existing directories

| Path | State |
|------|-------|
| `runtime/platform/` | **ABSENT** — no prior Phase 1 work |
| `runtime/platform/api/` | **ABSENT** — created by this phase |
| `runtime/platform/api/contracts/` | **ABSENT** — created by this phase |
| `runtime/platform/api/services/` | **ABSENT** — created (empty placeholder for Phase 2) |
| `runtime/generated/m9-c57/` | **ABSENT** — created by this phase |
| `runtime/generated/m9-c57/phase-01/` | **ABSENT** — created by this phase |

### 2.2 Existing C50 subsystems reused (read-only references)

Per ``IMPLEMENTATION_ROADMAP.md`` §2.3, the following remain frozen and are referenced but **not modified**:

- `runtime/foundation/verification/canonical_control_plane.py`
- `runtime/foundation/verification/capability_catalog*.py`
- `runtime/foundation/architecture/ids.py` (17 canonical ID prefixes; reused for string IDs)
- `runtime/foundation/verification/evidence_contract.py` (canonical hash pattern adopted)
- `runtime/foundation/verification/ci_evidence.py` (canonical SHA-256 over sorted payload pattern)

### 2.3 Pre-existing classification

| Phase 1 deliverable | Classification |
|---------------------|----------------|
| `runtime/platform/__init__.py` | **MISSING** — created |
| `runtime/platform/api/__init__.py` | **MISSING** — created |
| `runtime/platform/api/identity.py` | **MISSING** — created |
| `runtime/platform/api/errors.py` | **MISSING** — created |
| `runtime/platform/api/envelope.py` | **MISSING** — created |
| `runtime/platform/api/contracts/_primitives.py` | **MISSING** — created |
| `runtime/platform/api/contracts/health.py` | **MISSING** — created |
| `runtime/platform/api/contracts/capabilities.py` | **MISSING** — created |
| `runtime/platform/api/contracts/tasks.py` | **MISSING** — created |
| `runtime/platform/api/contracts/verification.py` | **MISSING** — created |
| `runtime/platform/api/contracts/executions.py` | **MISSING** — created |
| `runtime/platform/api/contracts/evidence.py` | **MISSING** — created |
| `runtime/platform/api/contracts/history.py` | **MISSING** — created |
| `runtime/platform/api/contracts/errors.py` | **MISSING** — created |
| `runtime/platform/api/contracts/architecture.py` | **MISSING** — created |
| `runtime/platform/api/contracts/events.py` | **MISSING** — created |
| `runtime/platform/api/contracts/application.py` | **MISSING** — created |
| `runtime/platform/api/contracts/change.py` | **MISSING** — created |
| `runtime/platform/api/services/__init__.py` | **MISSING** — created (empty placeholder) |
| `runtime/tests/test_platform_api_phase1.py` | **MISSING** — created |

No pre-existing partial work was found. No files were overwritten or replaced. No C50 module was modified.

---

## 3. Design authority consulted

- `INDEX.md`
- `IMPLEMENTATION_ROADMAP.md` (Phase 1 + §12 current authorized objective)
- `PLATFORM_AI_ARCHITECTURE.md` (§4.1, §5, §11, §12, §14)
- `PLATFORM_API_DESIGN.md` (§4 envelope; §3 endpoint surface for domain coverage)
- `PLATFORM_COMPONENT_MAP.md` (§4.1 confirms BUILD for `runtime/platform/api/`)
- `PLATFORM_READINESS_ASSESSMENT.md` (no prior Phase 1 work confirmed)
- `DESIGN_AUDIT.md` (forbidden patterns re-checked; none introduced)

---

## 4. Requirements addressed

Per ``IMPLEMENTATION_ROADMAP.md`` Phase 1 ("Establish typed contracts for: health, capabilities, tasks, verification, executions, evidence, history, errors, architecture, events, application readiness, change intelligence"):

| Requirement | Module |
|-------------|--------|
| Health contract | `runtime/platform/api/contracts/health.py` |
| Capabilities contract | `runtime/platform/api/contracts/capabilities.py` |
| Tasks contract | `runtime/platform/api/contracts/tasks.py` |
| Verification contract | `runtime/platform/api/contracts/verification.py` |
| Executions contract | `runtime/platform/api/contracts/executions.py` |
| Evidence contract | `runtime/platform/api/contracts/evidence.py` |
| History contract | `runtime/platform/api/contracts/history.py` |
| Errors contract | `runtime/platform/api/contracts/errors.py` |
| Architecture contract | `runtime/platform/api/contracts/architecture.py` |
| Events contract | `runtime/platform/api/contracts/events.py` |
| Application readiness contract | `runtime/platform/api/contracts/application.py` |
| Change intelligence contract | `runtime/platform/api/contracts/change.py` |

Plus the shared primitives and the envelope:

| Requirement | Module |
|-------------|--------|
| Required envelope: `kind`, `version`, `generated_at`, `id`, `data` | `runtime/platform/api/envelope.py` |
| Required error envelope: `kind`, `version`, `generated_at`, `id`, `error.{code,layer,message}` | `runtime/platform/api/envelope.py`, `runtime/platform/api/errors.py` |
| Stable identity (`sha256:<hex>`) | `runtime/platform/api/identity.py` |
| Cross-cutting primitives (Status, Timestamp, Identity) | `runtime/platform/api/contracts/_primitives.py` |

---

## 5. Files changed

```
runtime/platform/__init__.py                                          (NEW)
runtime/platform/api/__init__.py                                      (NEW)
runtime/platform/api/identity.py                                      (NEW)
runtime/platform/api/errors.py                                        (NEW)
runtime/platform/api/envelope.py                                      (NEW)
runtime/platform/api/contracts/__init__.py                            (NEW)
runtime/platform/api/contracts/_primitives.py                         (NEW)
runtime/platform/api/contracts/health.py                              (NEW)
runtime/platform/api/contracts/capabilities.py                        (NEW)
runtime/platform/api/contracts/tasks.py                               (NEW)
runtime/platform/api/contracts/verification.py                        (NEW)
runtime/platform/api/contracts/executions.py                          (NEW)
runtime/platform/api/contracts/evidence.py                            (NEW)
runtime/platform/api/contracts/history.py                             (NEW)
runtime/platform/api/contracts/errors.py                              (NEW)
runtime/platform/api/contracts/architecture.py                        (NEW)
runtime/platform/api/contracts/events.py                              (NEW)
runtime/platform/api/contracts/application.py                         (NEW)
runtime/platform/api/contracts/change.py                              (NEW)
runtime/platform/api/services/__init__.py                             (NEW — empty placeholder for Phase 2)
runtime/tests/test_platform_api_phase1.py                             (NEW)
runtime/generated/m9-c57/phase-01/progress.md                         (NEW — this file)
```

**Files modified:** 0
**Files deleted:** 0
**C50 modules touched:** 0

---

## 6. Implementation milestones

### Milestone 6.1 — Identity primitives (`identity.py`)

- Deterministic canonical JSON: `canonical_json_bytes`, `canonical_sha256`.
- Envelope identity: `envelope_identity(kind, version, data)`.
- Error identity: `error_identity(kind, version, code, layer, message)`.
- Identity shape: `sha256:<64-hex>` (lowercase).
- Strip `None`-valued fields from canonical payloads so that absence-vs-explicit-null collapse identically (mirrors Pydantic v2 `model_dump(exclude_none=True)` behaviour used elsewhere in the codebase).

### Milestone 6.2 — Error taxonomy (`errors.py`)

- `PlatformErrorCode` enum: `MALFORMED_REQUEST`, `NOT_FOUND`, `AUTHORIZATION_DENIED`, `INTERNAL`, `UNAVAILABLE`.
- `PlatformError` frozen dataclass with `code`, `layer`, `message`, optional `capability_id`, optional `evidence_id`.
- Validation: `layer`/`message` non-empty, `code` must be a `PlatformErrorCode`.

### Milestone 6.3 — Envelope (`envelope.py`)

- `success_envelope(kind, data)` — builds the canonical success shape with computed `id`.
- `error_envelope(error)` — builds the canonical error shape with computed `id`.
- `API_VERSION = "1.0.0"`.
- Wall-clock `generated_at` is **excluded** from the identity hash so the envelope is reproducible for caching, snapshotting, and AI context assembly.

### Milestone 6.4 — Shared primitives (`_primitives.py`)

- `Status` enum: `HEALTHY`, `DEGRAD`, `UNHEALTHY`, `UNKNOWN`.
- `Timestamp` annotated string validated against `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`.
- `Identity` annotated string validated against `^sha256:[0-9a-f]{64}$`.
- JSON-schema emission for both annotated types so that Phase 3 can generate OpenAPI directly.

### Milestone 6.5 — Domain contracts (12 modules)

Every domain contract defines:

- A typed Pydantic v2 `BaseModel` for the data payload.
- A typed Pydantic v2 `BaseModel` for the success envelope (with `kind` field frozen).
- A canonical `kind` constant matching `PLATFORM_API_DESIGN.md` §4 / §5.

All 12 domains from ``IMPLEMENTATION_ROADMAP.md`` Phase 1 are covered.

---

## 7. Validation performed

Per Phase 1 validation requirements:

> * contract serialization tests
> * stable identity tests
> * deterministic canonical serialization
> * malformed request tests
> * error contract tests

### 7.1 Tests added

File: `runtime/tests/test_platform_api_phase1.py`

Test classes:

1. `TestCanonicalJson` — 3 tests covering identity stability, dict-order independence, and tuple serialization.
2. `TestEnvelopeIdentity` — 4 tests covering envelope identity stability, error identity stability, kind/version sensitivity, and wall-clock exclusion.
3. `TestSuccessEnvelope` — 3 tests covering required keys, deterministic `id` re-runs, and rejection of `None` data.
4. `TestErrorEnvelope` — 4 tests covering required keys, deterministic error `id`, optional fields defaulting to `None`, and `PlatformError` validation.
5. `TestPlatformError` — 4 tests covering enum values, frozen dataclass, validation failures, and code-type enforcement.
6. `TestPrimitives` — 6 tests covering Status enum values, Timestamp validation (regex, type), Identity validation (regex, type), and JSON-schema emission.
7. `TestHealthContract` — 3 tests covering serialization round-trip, `kind` immutability, and `domains` default empty list.
8. `TestCapabilitiesContract` — 4 tests covering list envelope, detail envelope, graph envelope, and minimal-item round-trip.
9. `TestTasksContract` — 3 tests covering list envelope, detail envelope, and cancel envelope.
10. `TestVerificationContract` — 3 tests covering run request, run result, and recommendation.
11. `TestExecutionsContract` — 2 tests covering detail envelope and SSE stream event envelope.
12. `TestEvidenceContract` — 3 tests covering list envelope, detail envelope, and compare envelope.
13. `TestHistoryContract` — 4 tests covering runs, run detail, compare envelope (with request data), and baselines.
14. `TestErrorsContract` — 4 tests covering current/recent/recurring envelopes, frequency, detail, and kind mutability for the shared envelope.
15. `TestArchitectureContract` — 4 tests covering authorities, authority detail, boundaries/duplicates/bypasses/deprecations/unmapped envelopes, and kind mutability.
16. `TestEventsContract` — 3 tests covering list envelope, SSE stream event envelope, and `payload` default empty dict.
17. `TestApplicationContract` — 2 tests covering all 5 application readiness envelopes with shared shape and distinct `kind`.
18. `TestChangeIntelligenceContract` — 2 tests covering serialization round-trip and `risk` validation.
19. `TestEndToEndEnvelopeStability` — 4 tests proving: same input → same identity across processes (re-running), `generated_at` excluded from identity, every envelope has the 5 required keys, error envelopes have the 4 required `error.*` sub-fields.
20. `TestNoNetworkDependency` — 2 tests proving the platform package imports without any HTTP/socket layer and the contract layer has no I/O imports.

### 7.2 Commands executed

Tests run via the canonical root virtualenv per `AGENTS.md`:

```
.venv/bin/python -m pytest runtime/tests/test_platform_api_phase1.py -v
```

(Full command output captured under §10 evidence.)

---

## 8. Failures and their classification

### 8.1 During Phase 1 development

The first pytest run produced 9 failures. Each was classified, root-caused, and fixed during Phase 1 development. They are recorded here for traceability:

| # | Test | Root cause | Fix |
|---|------|-----------|-----|
| 1 | `TestCanonicalJson::test_dict_order_is_irrelevant` | `_canonicalize` returned a dict preserving original insertion order; `json.dumps` does not sort keys. | Recursively emit dicts with sorted keys in `_canonicalize`. |
| 2 | `TestCanonicalJson::test_nested_dict_order_is_irrelevant` | Same root cause as #1. | Same fix. |
| 3 | `TestPrimitives::test_timestamp_validation_rejects_wrong_format` | `Timestamp` was an `Annotated[str, Field(...)]` alias; the underlying validator class was never used. | Replaced with a concrete `Timestamp`/`Identity` Pydantic-compatible subclass whose `__get_pydantic_core_schema__` is picked up. |
| 4 | `TestPrimitives::test_identity_validation_rejects_non_sha256` | Same root cause as #3. | Same fix. |
| 5 | `TestPrimitives::test_json_schema_emitted_for_timestamp_and_identity` | Same root cause as #3 (annotations did not propagate to JSON schema). | Same fix. |
| 6 | `TestHealthContract::test_serialization_round_trip` | `Status` enum did not include the design-doc values `SAFE`, `CURRENT`, `VALID`, `READY` used in `PLATFORM_API_DESIGN.md` §5. | Widened `Status` to include `SAFE`, `CURRENT`, `VALID`, `READY`, `OPEN`, `CLOSED`. |
| 7 | `TestHealthContract::test_domains_defaults_to_empty_list` | Same root cause as #6. | Same fix. |
| 8 | `TestTasksContract::test_detail_envelope_round_trip` | Same root cause as #6 (`OPEN`). | Same fix. |
| 9 | `TestNoNetworkDependency::test_imports_dont_open_sockets` | Test scoped to the whole `sys.modules` — pytest/other plugins import `urllib3`/`requests`. | Re-scoped to modules newly loaded by the platform package itself. |

All 9 failures were **PHASE-1-INTRODUCED** (in the test file or implementation) and were resolved before final test execution. None are pre-existing.

### 8.2 Final test execution result

```
.venv/bin/python -m pytest runtime/tests/test_platform_api_phase1.py -v
============================= 79 passed, 1 warning in 30.28s =============================
```

Captured in full under `runtime/generated/m9-c57/phase-01/test-results.txt`.

### 8.3 Regression check

Broader regression run (`pytest runtime/tests/` minus one pre-existing broken file):

- 388 tests passed, 1 pre-existing failure (`test_m9_c42_28.py::TestAdapterLayer::test_unknown_kind_marks_not_executable`) confirmed unrelated to Phase 1 by re-running on `git stash`'d main — same failure.
- 1 pre-existing collection error (`test_vea5_m8r_cache_observability.py` — missing `_record_verification_event` export) also unrelated.

**No regressions introduced by Phase 1.**

---

## 9. Blockers

None. Phase 1 contract layer is fully implemented, validated, and certified.

---

## 10. Evidence locations

| Artifact | Path |
|----------|------|
| Phase 1 progress record | `runtime/generated/m9-c57/phase-01/progress.md` (this file) |
| Phase 1 implementation | `runtime/platform/` |
| Phase 1 tests | `runtime/tests/test_platform_api_phase1.py` |
| Test execution transcript | `runtime/generated/m9-c57/phase-01/test-results.txt` |
| Sample envelopes (health, capability, error) | `runtime/generated/m9-c57/phase-01/sample-envelopes.json` |
| File manifest (per-file SHA-256, LOC) | `runtime/generated/m9-c57/phase-01/file-manifest.json` |

---

## 11. Deviations from design

None. The Phase 1 contract layer follows ``PLATFORM_API_DESIGN.md`` §4 (envelope shape), §5 (concrete examples), and ``IMPLEMENTATION_ROADMAP.md`` Phase 1 (12 domains). No forbidden patterns introduced:

- No second executor / second evidence format / second capability registry / second task model / second event store.
- No C50 modifications.
- No second Python environment.
- No HTTP layer (Phase 3 deferred).
- No services / aggregators (Phase 2 deferred).
- No LLM/AI surface (Bands C/D deferred).

The `Status` enum was widened during development to include values shown in the design doc's concrete examples (`SAFE`, `CURRENT`, `VALID`, `READY`, `OPEN`, `CLOSED`). This is a faithful implementation of the design doc's stated values, not a deviation.

---

## 12. Gate status

### Gate 1 (Platform Contracts)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Contracts are stable | **PASS** | All 12 domain contracts serialize and round-trip via Pydantic v2; `kind` is frozen on success envelopes; `subject`/`risk`/`code` fields are required by validation. |
| No C50 authority duplicated | **PASS** | `runtime/platform/` is a new directory; **0** C50 files modified. The contracts reference C50 IDs by string, not by import-and-mutate. |
| No network required | **PASS** | `TestNoNetworkDependency` proves the platform package loads zero network-bearing libraries. |
| Deterministic output confirmed | **PASS** | `TestCanonicalJson` and `TestEndToEndEnvelopeStability` prove `id` is independent of dict ordering, wall-clock time, and process state. |
| All contract tests pass | **PASS** | 79/79 tests passed in 30.28s. |

---

## 13. Final Phase 1 disposition

**CERTIFIED.**

Every Phase 1 requirement and Gate 1 criterion is satisfied with reproducible evidence:

- All 12 contract domains (health, capabilities, tasks, verification, executions, evidence, history, errors, architecture, events, application, change) are implemented as typed Pydantic v2 models.
- The canonical envelope (`kind`, `version`, `generated_at`, `id`, `data`) and error envelope (`kind`, `version`, `generated_at`, `id`, `error.{code,layer,message,…}`) are enforced via `success_envelope` / `error_envelope`.
- Identity is stable: `sha256:<64-hex>` over canonical (sorted-key, None-stripping) JSON.
- 79 contract tests pass. 0 regressions. 0 C50 modules touched.
- Pre-existing failures in unrelated test files (`test_vea5_m8r_cache_observability.py`, `test_m9_c42_28.py`) were classified as PRE-EXISTING and excluded from the Phase 1 gate.

The repository is left in a clean, evidenced state ready for **Phase 2 — Platform Service Aggregators** (which the user must explicitly authorize).

---

## 14. Code metrics (informational)

```
   54 lines  runtime/platform/api/contracts/application.py
  115 lines  runtime/platform/api/contracts/architecture.py
  105 lines  runtime/platform/api/contracts/capabilities.py
   53 lines  runtime/platform/api/contracts/change.py
  108 lines  runtime/platform/api/contracts/errors.py
   72 lines  runtime/platform/api/contracts/events.py
   97 lines  runtime/platform/api/contracts/evidence.py
   71 lines  runtime/platform/api/contracts/executions.py
   64 lines  runtime/platform/api/contracts/health.py
  136 lines  runtime/platform/api/contracts/history.py
   37 lines  runtime/platform/api/contracts/__init__.py
  162 lines  runtime/platform/api/contracts/_primitives.py
   93 lines  runtime/platform/api/contracts/tasks.py
   85 lines  runtime/platform/api/contracts/verification.py
  144 lines  runtime/platform/api/identity.py
   88 lines  runtime/platform/api/errors.py
  130 lines  runtime/platform/api/envelope.py
    8 lines  runtime/platform/api/__init__.py
   32 lines  runtime/platform/__init__.py
 1654 lines  TOTAL implementation
  979 lines  runtime/tests/test_platform_api_phase1.py
   79 tests  collected & passing
```
