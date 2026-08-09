# Program L — Backend `src/` Root Module Ownership & Placement Audit

**Date:** 2026-08-08
**Scope:** `backend/src/` root-level production modules
**Mode:** AUDIT-ONLY (no source files moved, renamed, deleted, or modified)
**Baseline commit:** `0c8410c3` (HEAD)

---

## 1. Executive Conclusion

The current root-level structure of `backend/src/` is **architecturally valid and
intentional**. After reading every root module and mapping all consumers, the evidence
shows that the root placement of these modules is justified by one of three well-defined
roles:

1. **Application composition root** (`api.py`) — the FastAPI app factory imported by
   deployment (`start.sh`), test fixtures, contract tests, and dev tooling.
2. **Cross-cutting infrastructure** (`config.py`, `logger.py`, `errors.py`, `health.py`,
   `startup.py`) — domain-wide concerns consumed by nearly every package under `src/`.
3. **Compatibility / legacy surface** (`db.py` and its wrapper `common/database.py`) —
   explicitly retained backward-compatible facades over `src.core.db`.

`ingest.py` is a **standalone CLI ingestion pipeline** (PDF → DB). It overlaps in name
and intent with the HTTP import path (`import_router.py` + `import_service.py`), but it
is a *separate, complete implementation* with a distinct consumer surface (only e2e
import-presence tests), not duplicated orchestration of the same code. Its root placement
as a CLI entrypoint is architecturally consistent with `api.py` and `startup.py`.

No root module is a clear "misplaced canonical package member" (classification D) with a
safe, evidence-backed relocation target. The only files bearing a future-action flag are
`db.py` / `common/database.py` (future retirement of the compatibility facade), which the
audit explicitly does **not** perform.

**Conclusion:** The absence of a containing folder is NOT evidence of architectural
failure for these modules. The tree is sound.

---

## 2. Root Module Classification

| Module | Classification | Production consumers | Test consumers | Current placement justified? | Candidate destination | Risk |
| ------ | -------------- | -------------------: | -------------: | ---------------------------- | --------------------- | ---- |
| `api.py` | A — Legitimate application root | 5 (start.sh, 2 tools, client fixture, 2 contract tests) | 5 | Yes (proven) | — | n/a (retain) |
| `config.py` | B — Cross-cutting infrastructure | 7 (errors, startup, logger, health, api, core/db/config, fixtures) | 1 | Yes | — | n/a (retain) |
| `errors.py` | B — Cross-cutting infrastructure | 8 (api, 4 routers, behaviour_service) | 2 | Yes | — | n/a (retain) |
| `logger.py` | B — Cross-cutting infrastructure | 4 (errors, startup, health, behaviour_service) | 0 | Yes | — | n/a (retain) |
| `health.py` | B — Cross-cutting infrastructure | 2 (api, routers/health re-export) | 0 | Yes | — | n/a (retain) |
| `startup.py` | A/B — Application bootstrap (CLI) | 0 (standalone CLI) | 0 | Yes | — | n/a (retain) |
| `ingest.py` | A — Standalone CLI ingestion entrypoint | 0 (standalone CLI) | 2 (e2e import-presence) | Yes (proven distinct) | — | n/a (retain) |
| `db.py` | C — Compatibility infrastructure | 2 (common/database.py, tools/generators) | 0 fixture (migrated in K) | Yes (retained intentionally) | — | future retirement |
| `__init__.py` | A — Package marker | n/a | n/a | Yes | — | n/a (retain) |

### Classification legend
- **A** — Legitimate application root / entrypoint
- **B** — Cross-cutting infrastructure
- **C** — Compatibility infrastructure (retained)
- **D** — Canonical package member misplaced at root (none found)
- **E** — Legacy candidate, must not be deleted (n/a here)
- **F** — Ambiguous (none required)

---

## 3. Dependency Evidence

Direction of imports (root module → dependency):

```
api.py            → config, errors, health, routers.*            (composition root)
startup.py        → config, core.db.connection, logger          (bootstrap)
config.py         → core.db.config (lazy)                       (delegates path resolution)
errors.py         → logger, config (lazy)                       (handler fmt)
logger.py         → config (lazy, ImportError-tolerant)         (log level/format)
health.py         → config, core.db.connection, logger          (health endpoints)
ingest.py         → extraction.*, repositories.*                (CLI pipeline)
db.py             → core.db.config/connection/schema, common.calculations  (facade)
common/database.py→ core.db.config, db (TYPE_CHECKING + lazy)   (facade)
```

Key observations:

- **No circular dependency at import time.** The `config.py` ↔ `core.db.config.py`
  relationship is one-directional (config lazily imports `core.db.config`, and
  `core.db.config` lazily imports `config` only inside the function body to read
  `_database_path_override`). Both sides use lazy/function-scope imports, so the
  dependency is intentional and safe.
- **Root modules sit *above* packages**: `api`, `startup`, `ingest` (entrypoints) and
  `config`/`logger`/`errors`/`health` (cross-cutting) depend *downward* into
  `core`, `routers`, `extraction`, `repositories`. This is the correct layering
  direction — entrypoints and infrastructure at the root depend on sub-packages, not
  vice versa.
- **`db.py` and `common/database.py` are the only modules that point "sideways" into a
  compatibility role** — both wrap `src.core.db` and are explicitly marked deprecated in
  their own docstrings. They are the canonical-compatibility layer, not misplaced members
  of `core/db`.

---

## 4. Compatibility Evidence (root import paths that MUST be preserved)

These `src.<module>` import paths are part of an established public/compatibility surface
and must not be broken by relocation:

| Import path | Preserved because | Consumers |
| ----------- | ----------------- | --------- |
| `src.api:app` | `uvicorn src.api:app` in `start.sh` (deployment); test client fixture; contract-test generators; `coVF_discover.py`, `generate_contract_tests.py` tooling | 5 |
| `src.db.FinanceDB` | `common/database.py` re-export (`src.common.get_db`); `tools/generators/generate_synthetic_data.py` uses `from db import FinanceDB` | 2 active |
| `src.config.settings` | Pervasive; read by `core.db.config`, `runtime` scope classifier, and ~7 src modules | ubiquitous |
| `src.errors.{AppError,NotFoundError,...}` | Imported by 4 routers + `behaviour_service`; error contract | 8 |
| `src.logger.{logger,log_error,...}` | Imported by errors/startup/health/behaviour_service | 4 |
| `src.health.register_health_routes` | Re-exported by `routers/health.py`; registered by `api.py` | 2 |

`runtime/foundation/verification/models/scope.py` hardcodes `"backend/src/api": ["api"]`
as a verification scope entry — relocating `api.py` would require updating this scope map
(verification impact, see §11).

---

## 5. Duplicate / Overlap Findings

### `health.py` vs `routers/health.py`
**NOT a duplicate.** `routers/health.py` is a 6-line re-export:
```python
from src.health import register_health_routes, router
```
It exists only to surface the root health logic under the `routers` namespace for import
consistency. No behavioral duplication; `routers/health.py` contains zero logic of its own.

### `ingest.py` vs `import_service.py` / `import_router.py` (dedicated analysis)
These implement the **same conceptual workflow** (extract → categorize → store → validate)
but are **distinct implementations with different entry contracts**:

| Aspect | `ingest.py` (root CLI) | `import_service.py` + `import_router.py` (HTTP path) |
| ------ | ---------------------- | ---------------------------------------------------- |
| Trigger | `python ingest.py <pdf>` CLI | `POST /api/upload` HTTP |
| DB path | hardcoded `data/finance.db` (CWD-relative) | `db_path=None` → `get_db_path()` canonical |
| Categorization | `categorize(desc, amount_float)` (float) | `categorize(desc, amount_float)` (from paise) |
| Validation | 4-strategy heuristic on `total_due` | single net-vs-total paise comparison |
| Post-upload | none | `StatementProcessingOrchestrator.process_after_upload` + behavior cache invalidation |
| Consumers | 2 e2e import-presence tests only | routers, frontend, full upload pipeline |

**Finding:** `ingest.py` is NOT a facade over `import_service.py` and shares no code with
it. It is a parallel/legacy CLI ingestion path. There is genuine *functional overlap* (two
ways to ingest a PDF), but no *code* duplication that relocation would resolve. Merging
them would be a behavior change (different validation, no post-upload pipeline), which is
out of scope for this audit. Classification: **A (standalone CLI entrypoint)**, with a
note that it is a **legacy/parallel ingestion path** relative to the HTTP import service.

### Other overlap checks
- `config.py` vs `core/db/config.py`: complementary, not overlapping. `config.py` owns
  application env settings; `core/db/config.py` owns canonical DB path resolution. `config`
  delegates DB path to `core.db.config`. No duplication.
- `logger.py` vs `common/`: `common/` contains `calculations`, `enrichment`, `formatting`,
  `parsing`, `database` — none provide logging. No duplication.
- `errors.py` vs any `core/errors`: no error package exists under `core/`. `errors.py` is
  the sole exception owner. No duplication.

---

## 6. Relocation Candidates

### Strong candidates
**None.** No root module meets the bar of "clearly misplaced AND safe to migrate with a
strong evidence-based justification." Each has either a proven entrypoint/infra role, an
active compatibility contract, or active consumers that would be broken by relocation.

### Conditional candidates
**None require a conditional flag.** The overlap findings in §5 are real but do not imply
misplacement at root; they imply *parallel implementations* (ingest) or *compatibility
facades* (db), which are intentionally rooted.

### Retain (root placement justified)
- `api.py` — composition root (deployment + tests + tooling)
- `config.py` — application-wide configuration
- `errors.py` — domain-wide exception + handler registry
- `logger.py` — cross-cutting logging infrastructure
- `health.py` — application health endpoints
- `startup.py` — bootstrap CLI
- `ingest.py` — standalone ingestion CLI entrypoint
- `__init__.py` — package marker

### Future retirement (legacy/compatibility, retain for now)
- `db.py` — backward-compatible `FinanceDB` facade over `src.core.db`. Marked
  `.. deprecated::` in its own docstring. Program K migrated all fixture consumers; current
  active consumers: `common/database.py` (compatibility re-export) and
  `tools/generators/generate_synthetic_data.py`. **Retirement requires a separate
  evidence-driven program.** Do NOT delete here.
- `common/database.py` — deprecated `get_db()` shim, explicitly documented as having
  "zero production consumers." Retained alongside `db.py`.

---

## 7. Recommended Next Program

**No relocation is warranted** by this audit. The root modules are correctly placed as
application entrypoints (A) and cross-cutting infrastructure (B), and the only
compatibility surfaces (`db.py`, `common/database.py`) are intentionally retained and
already documented as future-retirement candidates.

Therefore a **Program M — Controlled Backend Root Module Relocation** is NOT recommended at
this time. Should future work target the `db.py` / `common/database.py` compatibility
facade, the appropriate future program is:

> **Program M — Controlled Retirement of `db.py` / `common/database.py` Compatibility Facade**
> (distinct from relocation; scope = eliminate the deprecated `FinanceDB`/`get_db` surface
> after migrating `tools/generators/generate_synthetic_data.py` and the
> `src.common.get_db` re-export to `src.core.db`).

This is recorded as a recommended future program only for the compatibility facade. No
files were moved, renamed, deleted, or modified during Program L.

---

## Appendix A — Phase L1 Baseline

- **Working tree:** clean except pre-existing user work (`.gitignore`, frontend, fixtures,
  runtime generated, `backend/src/data/__init__.py` rename from Program K).
- **Tracked `backend/src` change:** `R backend/src/data/finance.db -> backend/src/data/__init__.py`
  (Program K, pre-existing at audit start — not introduced by this program).
- **Root files:** `api.py`, `config.py`, `db.py`, `errors.py`, `health.py`, `ingest.py`,
  `logger.py`, `startup.py`, `__init__.py` + package dirs (`common`, `core`, `data`,
  `engines`, `extraction`, `models`, `orchestration`, `repositories`, `routers`,
  `services`, `structural`, `utils`).
- **Generated artifacts ignored:** `__pycache__`, `.mypy_cache` (excluded from audit).

## Appendix B — Phase L12 No-Change Validation

- All 8 root modules import successfully (`python3 -c "import src.api, ..."` → OK).
- `git status --short backend/src` shows ONLY the pre-existing Program K rename; **no
  audit-induced production change**.
- Quick verification (`runtime/verify.py quick`) reflects a pre-existing cached plan
  failure (`run_fast_checks.sh`) keyed to commit `0c8410c3` from earlier in the session,
  unrelated to this audit (zero source changes made). `tests/unit/test_errors.py` confirmed
  passing (26 passed) as a spot check of root-module test health.
- No runtime verification rules, provider registry entries, architecture tests, or test
  strictness were modified.

## Appendix C — Consumer Counts (evidence)

| Module | Production | Tests | Tooling | Notes |
| ------ | ---------- | ----- | ------- | ----- |
| `api.py` | 1 (start.sh uvicorn) | 3 (client, schema_providers, schema_validators) | 2 (coVF_discover, generate_contract_tests) | composition root |
| `config.py` | 7 | 1 (fixtures/database) | — | pervasive |
| `errors.py` | 8 (api + 4 routers + service) | 2 (test_errors, test_behaviour_service) | — | |
| `logger.py` | 4 | 0 | — | |
| `health.py` | 2 (api, routers/health) | 0 | — | |
| `startup.py` | 0 | 0 | 0 | standalone CLI, not invoked by start.sh |
| `ingest.py` | 0 | 2 (e2e import-presence) | 0 | standalone CLI |
| `db.py` | 2 (common/database, tools/generators) | 0 fixture (migrated in K) | — | compatibility facade |
