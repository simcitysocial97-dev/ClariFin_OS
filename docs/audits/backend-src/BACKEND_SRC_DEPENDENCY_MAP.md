# Backend `src/` Dependency Map — Program H

Derived by AST analysis of all 244 Python files under `backend/src` (imports resolved per-module, `__pycache__` excluded), cross-checked with grep evidence.

---

## 1. Layer Edge Table (complete, weighted)

Counts are import statements between layers.

| Source layer | → | Target layer | Count | Direction |
|---|---|---|---|---|
| services | → | repositories | 54 | correct |
| routers | → | services | 28 | correct |
| services | → | engines | 23 | correct |
| repositories | → | toplevel | 19 | see §4 |
| core.mappers | → | core.dtos | 13 | correct |
| routers | → | models | 12 | **DTO bypass** |
| core.dtos | → | toplevel | 12 | see §4 |
| extraction | → | toplevel | 10 | see §4 |
| routers | → | core.dtos | 8 | correct |
| repositories | → | models | 8 | correct |
| services | → | models | 7 | correct |
| orchestration | → | services | 7 | correct |
| routers | → | toplevel | 6 | correct (errors/config) |
| common | → | toplevel | 5 | see §4 |
| services | → | core.dtos | 5 | correct |
| toplevel | → | extraction | 4 | `ingest.py` |
| services | → | extraction | 4 | `import_service.py` |
| db.py(shim) | → | core.db | 3 | **compatibility** |
| toplevel | → | core.db | 3 | correct |
| engines | → | core.db | 3 | **purity violation** |
| core.mappers | → | core.domain | 3 | correct |
| core.mappers | → | toplevel | 3 | see §4 |
| toplevel | → | repositories | 2 | `ingest.py` |
| routers | → | core.mappers | 2 | correct |
| repositories | → | core.db | 2 | correct |
| services | → | core.db | 2 | correct |
| services | → | common | 2 | correct |
| services | → | core.mappers | 2 | correct |
| services | → | toplevel | 2 | correct |
| toplevel | → | routers | 1 | `api.py` (composition root) |
| db.py(shim) | → | common | 1 | compatibility |
| common | → | core.db | 1 | correct |
| common | → | db.py(shim) | 1 | **compatibility** |
| routers | → | common | 1 | correct |
| **models** | → | **engines** | **1** | **REVERSE-LAYER** |
| engines | → | toplevel | 1 | see §4 |
| core.db | → | toplevel | 1 | lazy `config` (guarded) |
| core.domain | → | toplevel | 1 | see §4 |
| services | → | orchestration | 1 | correct |
| extraction | → | structural | 1 | correct |

---

## 2. Canonical Layer Flow (verified)

```text
                    api.py  (composition root, 28 routers → 119 routes)
                       │
                       ▼
   ┌──────────────  routers (29)  ──────────────┐
   │ 28→services   8→core.dtos   2→core.mappers │
   │ 12→models  ⚠ DTO bypass                    │
   └───────────────────┬────────────────────────┘
                       ▼
   ┌──────────────  services (32)  ─────────────┐
   │ 54→repositories  23→engines  5→core.dtos   │
   │ 4→extraction  1→orchestration              │
   └───────────────────┬────────────────────────┘
                       ▼
   ┌────────────  repositories (27)  ───────────┐
   │ 8→models  2→core.db  19→toplevel(errors)   │
   └───────────────────┬────────────────────────┘
                       ▼
              core/db/  ← CANONICAL DATABASE AUTHORITY
```

**No circular imports.** Proven empirically: all 243 `src.*` modules import successfully in isolation (`pkgutil.walk_packages` sweep, 0 failures).

---

## 3. Database Dependency Graph (Phase H3)

```text
                    ┌──────────────────────────┐
                    │   src/core/db/           │  ◀── CANONICAL
                    │   config · connection    │
                    │   schema · transaction   │
                    │   health                 │
                    └───────────▲──────────────┘
                                │ (43 import statements, 16 modules)
        ┌────────────┬──────────┼───────────┬─────────────┐
        │            │          │           │             │
   startup.py    health.py   config.py  repositories/  services/
                                          base.py       base.py
                                                        financial_
                                                        intelligence_
                                                        service.py
        │            │
   engines/balance_engine.py ────┐
   engines/ledger_audit_engine.py│ ⚠ function-local imports
   engines/reconciliation_engine.py┘  (purity violation, 8 sites)

   ── COMPATIBILITY (no production consumers) ──
   src/db.py ──3──▶ core.db          [FinanceDB]
        ▲
        │ imported ONLY by:
        ├── src/common/database.py  (itself deprecated, 0 consumers)
        └── tests/fixtures/database.py
            tests/fixtures/client.py
            tests/fixtures/seed.py
            tests/fixtures/benchmark_fixtures.py
```

### Database implementation classification

| Implementation | Class | Prod consumers | Test consumers |
|---|---|---|---|
| `core/db/**` | **CANONICAL** | 16 modules / 43 imports | 3 files |
| `db.py` (`FinanceDB`) | **COMPATIBILITY** | **0** | **4 fixtures** |
| `common/database.py` (`get_db`) | **COMPATIBILITY (dormant)** | **0** | 0 |

**Consolidation blocker:** `db.py` cannot be retired until the 4 test fixtures migrate to `core.db`. This is why it is Class **C/D**, not **E**.

---

## 4. `toplevel` Edge Explanation

The `toplevel` target in the edge table is **not** a layering smell. It resolves almost entirely to legitimate cross-cutting infrastructure:

| Consumer layer | Target module | Purpose |
|---|---|---|
| repositories (19) | `src.errors` | domain exception raising |
| core.dtos (12) | `src.errors` / `src.config` | contract validation |
| extraction (10) | `src.errors`, `src.logger` | error + logging |
| common (5), routers (6), mappers (3) | `src.errors`, `src.config`, `src.logger` | cross-cutting |
| core.db (1) | `src.config` | **lazy, ImportError-guarded** to avoid a cycle |

`core/db/config.py` deliberately wraps its `src.config` import in `try/except ImportError` with the comment *"lazy import to avoid circular dependency"* — an intentional, documented cycle-breaker.

---

## 5. Engine Consumer Matrix

| Engine | src consumers | test files | Consuming services |
|---|---|---|---|
| `loan_engine` | 8 | 9 | loan, loan_analysis, loan_simulation, loans_workspace |
| `behaviour_engine` | 3 | 8 | behaviour_service, behaviour_workspace |
| `recommendation_engine` | 2 | 2 | recommendation_service |
| `account_engine` | 1 | 2 | account_service |
| `credit_card_engine` | 1 | 6 | credit_card_service |
| `financial_events` | 1 | 5 | financial_events_service |
| `financial_intelligence` | 1 | 1 | financial_intelligence_service |
| `transaction_intelligence` | 1 | 1 | transaction_intelligence_service |
| `balance_engine` | 1 | 1 | via `engines/__init__` facade |
| `ledger_audit_engine` | 1 | 1 | audit_service |
| `reconciliation_engine` | 1 | 4 | reconciliation_service |
| `cashflow_engine` | **0** | 2 + 4 meta | **none** — capability/test-referenced only |

---

## 6. Extraction / Ingestion Graph

```text
              ┌─────────────────────────────────┐
              │      extraction/ (11 modules)   │
              │  hybrid_extractor ─┐            │
              │  camelot_extractor │            │
              │  table_extractor   ├─ statement_extractor (1556 LOC)
              │  metadata_extractor│            │
              │  csv_importer      │            │
              │  transaction_parser│            │
              │  column_mapper     │            │
              │  categorizer       │            │
              │  validator         │            │
              └────────┬───────────┴────────────┘
                       │ 1 edge
                       ▼
              structural/layout_analyzer.py   (sole consumer: hybrid_extractor)

   TWO PARALLEL COMPOSITIONS of the same extraction modules:

   (CLI)  ingest.py ──4──▶ extraction ──2──▶ repositories
                                │
   (API)  services/import_service.py ──▶ extraction
                                     ──▶ services{statement,transaction,behaviour}
                                     ──▶ orchestration/statement_orchestrator (lazy, line 119)
                                              │ 7 edges
                                              ▼
                          services{behaviour, cashflow, dashboard,
                                   financial_intelligence, loan,
                                   transaction_intelligence}
```

Shared parsing logic is **single-sourced** in `extraction/`; only the wiring is duplicated.

---

## 7. Reverse / Anomalous Edges (full inventory)

| # | Edge | Site | Risk |
|---|---|---|---|
| 1 | `models → engines` | `models/loan_simulation.py:12` → `engines.loan_engine.models.PrepaymentMode` | Low — shared enum |
| 2 | `engines → core.db` | `balance_engine.py:96,175,234,284` | Medium — engine purity |
| 3 | `engines → core.db` | `ledger_audit_engine.py:35,156` | Medium |
| 4 | `engines → core.db` | `reconciliation_engine.py:281,335` | Medium |
| 5 | `routers → models` | `routers/{loans,credit_cards,behaviour,accounts}.py` | Low — DTO adoption gap |
| 6 | `common → db.py(shim)` | `common/database.py:30` | Low — compatibility, dormant |

All 8 sites in rows 2–4 are **function-local (lazy) imports**, not module-level — a deliberate cycle-avoidance technique. They still constitute engine-purity violations.

---

## 8. Test Reference Summary (secondary evidence scope)

| Target | Test-file references |
|---|---|
| `FinanceDB` / `src.db` | 4 fixture modules |
| `core.db` | 3 files |
| `cashflow_engine` | 2 functional + 4 meta/tooling |
| `ingest.py` | 1 (`integration/e2e/test_upload_pipeline.py`) |
| `behaviour_engine` | 8 |
| `loan_engine` | 9 |
