# Programs I–K — Final Integrated Validation

**Date:** 2026-08-08
**Programs:** I (hygiene/gitignore), J (registry regeneration), K (fixture migration)
**Result:** All three program gates PASSED. Final gates 1–4, 6, 7 PASS; gate 5 fails only on PRE-EXISTING property-test failures.

---

## Gate Results

| Gate | Check | Result |
|---|---|---|
| **1** | Repository integrity (`git status`, `diff --check`, `ls-files`) | **PASS** |
| **2** | Backend imports (243 `src.*` modules) + FastAPI composition | **PASS** — 243/243, 119 routes |
| **3** | `tests/architecture` + `tests/meta` | **PASS** — 111 passed |
| **4** | Database/fixture/repository/service/invariant/contract/capability | **PASS** — 318 passed |
| **5** | `runtime/verify.py backend` | **FAIL — PRE-EXISTING** (see below) |
| **6** | `runtime/verify.py quick` | **PASS** |
| **7** | Clean-checkout simulation | **PASS** — 244 files, 243 imports, 108 tests pass |

---

## Gate 5 — Root Cause Analysis (execution rule followed)

The first Gate 5 run reported **6 failures**, worse than the Program H baseline of 1. Per the execution rule I stopped and isolated each cause rather than proceeding.

### Failure 1 — `run_fast_checks.sh` — CAUSED BY PROGRAM K → FIXED

```
UP037 Remove quotes from type annotation
 --> tests/fixtures/database.py:70:28
     def __enter__(self) -> "TestDatabase":
```

A ruff violation I introduced in the new `TestDatabase` handle. Because the module already has `from __future__ import annotations`, the quoted forward reference is unnecessary.

**Fix applied:** `-> "TestDatabase"` → `-> TestDatabase`.

**Verified after fix:**
```
ruff check .   -> All checks passed!        (whole backend)
black --check . -> 460 files unchanged      (whole backend)
run_fast_checks.sh -> passed
```

This was the only defect Programs I–K introduced, and it is resolved.

### Failures 2–6 — `run_backend_verification.sh` — PRE-EXISTING

The script runs 4 suites. Isolating them individually:

| Suite | Result |
|---|---|
| `tests/contract` | **161 passed** |
| `tests/invariants` | **26 passed** |
| `tests/unit/engines` | **468 passed** |
| `tests/properties` | **7 failed**, 199 passed |

All 7 failures are Hypothesis property tests:

- `financial_events/test_lineage_properties.py::test_lineage_no_duplicate_events`
- `loan_engine/test_floating_rate_properties.py::test_apply_floating_rate_change_math_accuracy`
- `loan_engine/test_floating_rate_properties.py::test_simulate_floating_rate_schedule_rate_application`
- `loan_engine/test_foreclosure_properties.py::test_compute_foreclosure_amount_math_accuracy`
- `loan_engine/test_metrics_properties.py::test_calculate_tenure_saved_invariants`
- `loan_engine/test_metrics_properties.py::test_get_interest_component_invariants`
- `loan_engine/test_prepayment_properties.py::test_apply_prepayment_at_month_reduce_tenure_mode`

**Proof they are PRE-EXISTING** — stash-and-rerun:

```bash
git stash push backend/tests/fixtures/database.py backend/tests/fixtures/benchmark_fixtures.py
pytest tests/properties   # -> 7 failed, 199 passed   (IDENTICAL set)
git stash pop
```

Supporting evidence:
1. These tests use **no database fixtures** (verified by grep) — Program K cannot affect them.
2. `backend/src/engines/` and `backend/tests/properties/` are **untouched** — `git status` on both paths is empty.
3. Program H documented 3 such failures; the count grew to 7 because Hypothesis maintains a **19,949-file example database** (`.hypothesis/examples/`) that accumulates newly discovered counterexamples across the many test runs in this session. The fuzzer finding additional counterexamples in unchanged code is expected behaviour, not a regression.

Per the mission ("Finding D… These failures are NOT part of this program"), the loan-engine production logic and tests were **not modified and not weakened**.

---

## Final State

### Files changed (9 source/config + 7 regenerated artifacts)

| File | Program | Change |
|---|---|---|
| `.gitignore` | I | +3 lines — negation for `backend/src/data/` |
| `backend/.gitignore` | I | anchored `/data/`, `/uploads/` |
| `backend/src/data/finance.db` | I | **untracked** (retained on disk) |
| `backend/src/data/__init__.py` | I | **now tracked** |
| `runtime/analyze_architecture.py` | J | corrected engine declaration constants |
| `runtime/analyze_engine_topology.py` | J | corrected engine declaration constants |
| `runtime/analyze_engine_normalization.py` | J | emptied phantom `PARKED`; guarded duplicate finding |
| `runtime/analyze_execution.py` | J | corrected narrative note |
| `runtime/analyze_ownership.py` | J | corrected narrative note |
| `backend/tests/fixtures/database.py` | K | migrated to `core.db`; added `TestDatabase` |
| `backend/tests/fixtures/benchmark_fixtures.py` | K | migrated to `core.db.schema` |

**Regenerated (7):** `architecture-inventory.json`, `architecture-inventory-summary.json`, `architecture-provider.json`, `engine-normalization.json`, `engine-topology.json`, `execution-graph.json`, `ownership-graph.json`

### Files added
`docs/audits/backend-src/` — 5 Program H documents + 3 program validation artifacts

### Files deleted — **NONE**
Explicitly preserved: `backend/src/db.py`, `backend/src/common/database.py`, `backend/src/engines/cashflow_engine.py`, `backend/src/data/`.

### Production source behavior changes — **NONE**
No `.py` file under `backend/src` was modified. `git status --porcelain backend/src` shows only the `data/` tracking change (0-byte files).

### Verification-rule changes — **NONE**
`runtime/verify.py`, `runtime/foundation/`, and all architecture/meta tests are unmodified. The canonical provider implementation (`provider.py`) was not touched — only its generator inputs.

---

## Clean-Checkout Result (Gate 7)

Extracted the full tree from the git index into a scratch directory:

```
clean tree backend/src .py files : 244   (was 243 before Program I)
backend/src/data/                : __init__.py present, finance.db absent
cache/db artifacts leaked        : 0
imports in clean checkout        : OK=243 FAILURES=0
tests in clean checkout          : 108 passed (repositories + architecture)
```

The clean checkout no longer depends on ignored developer-local files, and the migrated fixtures work there.

---

## Remaining Pre-Existing Failures (not addressed, by instruction)

| Failure set | Count | Status |
|---|---|---|
| `tests/properties` Hypothesis math/invariant failures (6 loan_engine + 1 financial_events) | 7 | **PRE-EXISTING** — proven by stash-rerun |
| `tests/integration/e2e/test_upload_pipeline.py` — imports `src.column_mapper` (module actually at `src.extraction.column_mapper`) | 13 | **PRE-EXISTING** — proven by stash-rerun |

---

## Follow-up Candidates (separate from completed work)

1. **Loan-engine property failures** — interest-accrual tolerance breaches found by Hypothesis in unchanged engine code. Needs a dedicated numerical-correctness program to decide whether the engine or the property bound is wrong.
2. **`test_upload_pipeline.py` stale import paths** — 13 tests import `src.column_mapper`/`src.statement_extractor` instead of the `src.extraction.*` locations. A test-path correction program.
3. **Stale sqlite3 whitelist** — `tests/architecture/test_layer_boundaries.py` whitelists 4 engine files as "known sqlite3 violations", but no engine imports `sqlite3`. Removing it would *strengthen* verification (Program H finding; still not actioned).
4. **`backend/.gitignore` lines 1/10/17** (`Python`, `Database`, `Environment`) are active patterns, not comments. They match nothing today.
5. **Root `data/` ignore rule** still masks new files under `data/`, `backend/data/`, `backend/tests/data/`. The 14 tracked golden statement fixtures survive only because tracked files bypass ignore rules.
6. **`db.py` / `common/database.py` retirement** — now at **zero production and zero fixture consumers**. Retirement remains a separate evidence-driven program (explicitly out of scope here).
