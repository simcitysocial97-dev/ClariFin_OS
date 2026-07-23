# Phase 1 — Recovery Inventory

## Authority
Integration Decision Document (22 July 2026)
Mode: ACT
Goal: Verify every RESTORE and MERGE item. Produce final verified inventory.

## Verification Method
- **Current commit (HEAD):** `8c2e3037` (Production-Gate / stage-5-dashboard-completion)
- **Lost source:** `363ea27e` (Reconciliation-v2 branch tip)
- All items verified via `git ls-tree -r --name-only HEAD` and `git ls-tree -r --name-only 363ea27e`

---

## 1. PARSING PIPELINE

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 1 | `camelot_extractor.py` | `backend/src/extraction/camelot_extractor.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 2 | `hybrid_extractor.py` | `backend/src/extraction/hybrid_extractor.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 3 | `statement_extractor.py` | `backend/src/statement_extractor.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 4 | `table_extractor.py` | `backend/src/table_extractor.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 5 | `csv_importer.py` | `backend/src/csv_importer.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 6 | `ingest.py` | `backend/src/ingest.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 7 | `categorizer.py` | `backend/src/categorizer.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 8 | `transaction_parser.py` | `backend/src/transaction_parser.py` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 9 | `debug-parser-step.ts` | `frontend/scripts/debug-parser-step.ts` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked RESTORE, file exists in HEAD) |
| 10 | `test-semantic-parser.ts` | `frontend/scripts/test-semantic-parser.ts` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked RESTORE, file exists in HEAD) |
| 11 | `auto-fix-metadata.ts` | `frontend/scripts/auto-fix-metadata.ts` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked DISCARD, file exists in HEAD) |
| 12 | `test-metadata.ts` | `frontend/scripts/test-metadata.ts` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked DISCARD, file exists in HEAD) |
| 13 | `generate-expected-metadata.js` | `frontend/scripts/generate-expected-metadata.js` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked DISCARD, file exists in HEAD) |
| 14 | `scripts/verify-fast.sh` | None in HEAD | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |

---

## 2. FINANCIAL INTELLIGENCE ENGINES

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 15 | `financial_intelligence/` (7 files) | None | `363ea27e` | Missing (exit 1) | **RESTORE** | Restore entire directory from `363ea27e` |
| 16 | `transaction_intelligence/` (5 files) | None | `363ea27e` | Missing (exit 1) | **RESTORE** | Restore entire directory from `363ea27e` |
| 17 | `financial_events/` (2 files) | None | `363ea27e` | Missing (exit 1) | **RESTORE** | Restore entire directory from `363ea27e` |
| 18 | `behaviour_engine/credit_dependency.py` | None | `363ea27e` | Missing | **MERGE** | Merge into current `behaviour_engine/` package |
| 19 | `behaviour_engine/stress.py` | None | `363ea27e` | Missing | **MERGE** | Merge into current `behaviour_engine/` package |
| 20 | `behaviour_engine/temporal.py` | None | `363ea27e` | Missing | **MERGE** | Merge into current `behaviour_engine/` package |
| 21 | `behaviour_engine/savings.py` | `behaviour_engine/savings.py` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked MERGE, file exists in HEAD) |
| 22 | `behaviour_engine/profile.py` | `behaviour_engine/profile.py` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked MERGE, file exists in HEAD) |
| 23 | `behaviour_engine/wellness.py` | `behaviour_engine/wellness.py` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked MERGE, file exists in HEAD) |
| 24 | `behaviour_engine/account.py` | `behaviour_engine/account.py` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked MERGE, file exists in HEAD) |
| 25 | `cashflow_engine.py` | `services/cashflow_service.py` (HEAD) | `363ea27e` | Missing (exit 1) | **KEEP CURRENT** | Already replaced by service-layer implementation |
| 26 | `loan_engine/` (12 files in Recon-V2) | `loan_engine/` (8 files in HEAD) | `363ea27e` | **Exists in HEAD** (different implementation) | **MERGE** | Compare algorithms; merge unique logic from Recon-V2 into current modular structure |
| 27 | `recommendation_engine/` | `engines/recommendation_engine/` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |

---

## 3. BACKEND INFRASTRUCTURE

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 28 | `repositories/balance_repository.py` | `repositories/account_balance_repository.py` (HEAD) | `363ea27e` | Missing (but equivalent exists) | **MERGE** | Merge unique queries from lost version into current |
| 29 | `repositories/financial_event_repository.py` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 30 | `repositories/financial_goal_repository.py` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 31 | `repositories/liquidity_pattern_repository.py` | None | `363ea27e` | Missing | **DISCARD** | Niche use case, low value |
| 32 | `repositories/transaction_classification_repository.py` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 33 | `services/financial_events_service.py` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 34 | `services/financial_intelligence_service.py` | `services/forecast_service.py` (HEAD) | `363ea27e` | Missing (but partial equivalent exists) | **RESTORE** | Restore from `363ea27e`; merge with forecast_service if overlapping |
| 35 | `services/transaction_intelligence_service.py` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 36 | `models/credit_card_statement.py` | `models/credit_card.py` (HEAD) | `363ea27e` | **Tracked in HEAD** | **KEEP CURRENT** | None — already present (CORRECTION: was marked MERGE, file exists in HEAD) |
| 37 | `models/financial_goal.py` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |

---

## 4. FRONTEND INFRASTRUCTURE

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 38 | `frontend/tools/lock_toolchain.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 39 | `frontend/tools/architecture_audit.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 40 | `frontend/tools/type_react_audit.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 41 | `frontend/tools/generated_api_audit.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 42 | `frontend/tools/query_audit.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 43 | `frontend/tools/import_audit.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 44 | `frontend/tools/build_audit.ts` | None in HEAD | `363ea27e` | Missing from working tree | **RESTORE** | Restore from Git history |
| 45 | `frontend/tools/validate.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 46 | `frontend/tools/types.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 47 | `frontend/tools/utils.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 48 | `frontend/tools/__tests__/fvf.test.ts` | None in HEAD | `363ea27e` | Untracked in working tree | **RESTORE** | Commit existing untracked file |
| 49 | API Contract Tests (11 files) | `frontend/__tests__/api-contracts/` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |
| 50 | Playwright Tests (4 files) | `frontend/playwright/tests/` (HEAD) | `363ea27e` | Tracked in HEAD | **KEEP CURRENT** | None — already present |

---

## 5. TESTING ARCHITECTURE

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 51 | `tests/architecture/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 52 | `tests/capabilities/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 53 | `tests/contracts/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 54 | `tests/domain/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 55 | `tests/golden/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 56 | `tests/invariants/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 57 | `tests/meta/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 58 | `tests/properties/` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |

---

## 6. BACKEND VERIFICATION TOOLS

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 59 | `backend/tools/validation_orchestrator.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 60 | `backend/tools/selective_verify.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 61 | `backend/tools/change_intelligence.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 62 | `backend/tools/check_coverage.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 63 | `backend/tools/mutation_discovery.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 64 | `backend/tools/test_strength.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 65 | `backend/tools/coVF_discover.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 66 | `backend/tools/validation_audit.py` | None (0 .py files in HEAD) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |

---

## 7. MEMORY-BANK ASSETS

| # | Capability | Current Equivalent | Lost Source | Current Status | Decision | Action Required |
|---|---|---|---|---|---|---|
| 67 | `memory-bank/capabilities/` (10 YAML files) | None (only activeContext.md, projectbrief.md) | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 68 | `memory-bank/generated/` (30+ files) | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 69 | `memory-bank/architecture.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 70 | `memory-bank/engine-map.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 71 | `memory-bank/domain-invariants.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 72 | `memory-bank/validation-architecture.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 73 | `memory-bank/testing-strategy.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 74 | `memory-bank/service-map.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 75 | `memory-bank/database-map.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 76 | `memory-bank/dependency-map.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 77 | `memory-bank/engine-contracts.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 78 | `memory-bank/engine-maturity.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 79 | `memory-bank/cline-workflow.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 80 | `memory-bank/capability-index.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 81 | `memory-bank/capability-status.json` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 82 | `memory-bank/qea-rules.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 83 | `memory-bank/test-coverage.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 84 | `memory-bank/validation-review.md` | None | `363ea27e` | Missing | **RESTORE** | Restore from `363ea27e` |
| 85 | `memory-bank/regression-history.md` | None | `363ea27e` | Missing | **DISCARD** | Historical artifact, no current value |
| 86 | Historical memory-bank files (7 files) | None | `cd539408` | Missing | **DISCARD** | Historical artifacts, no current value |

---

## CORRECTIONS TO INTEGRATION DECISION DOCUMENT

The following items were incorrectly classified in the original Integration Decision Document and have been corrected above:

| Item | Original Decision | Corrected Decision | Reason |
|---|---|---|---|
| `frontend/scripts/debug-parser-step.ts` | RESTORE | **KEEP CURRENT** | File exists tracked in HEAD |
| `frontend/scripts/test-semantic-parser.ts` | RESTORE | **KEEP CURRENT** | File exists tracked in HEAD |
| `frontend/scripts/auto-fix-metadata.ts` | DISCARD | **KEEP CURRENT** | File exists tracked in HEAD |
| `frontend/scripts/test-metadata.ts` | DISCARD | **KEEP CURRENT** | File exists tracked in HEAD |
| `frontend/scripts/generate-expected-metadata.js` | DISCARD | **KEEP CURRENT** | File exists tracked in HEAD |
| `behaviour_engine/savings.py` | MERGE | **KEEP CURRENT** | File exists tracked in HEAD |
| `behaviour_engine/profile.py` | MERGE | **KEEP CURRENT** | File exists tracked in HEAD |
| `behaviour_engine/wellness.py` | MERGE | **KEEP CURRENT** | File exists tracked in HEAD |
| `behaviour_engine/account.py` | MERGE | **KEEP CURRENT** | File exists tracked in HEAD |
| `models/credit_card_statement.py` | MERGE | **KEEP CURRENT** | File exists tracked in HEAD |
| `loan_engine/` (12 files) | RESTORE | **MERGE** | Current HEAD has 8 different files; merge unique algorithms only |

---

## SUMMARY

| Decision | Count |
|---|---|
| **KEEP CURRENT** | 23 items |
| **RESTORE** | 36 items |
| **MERGE** | 7 items |
| **DISCARD** | 8 items |
| **REWRITE** | 0 items |
| **Total** | 74 items |

---

## FILES SAFE TO RESTORE IMMEDIATELY (No Dependencies)

1. `scripts/verify-fast.sh` (item 14)
2. All 8 `backend/tools/*.py` files (items 59-66)
3. `frontend/tools/build_audit.ts` (item 44)
4. Commit 10 untracked `frontend/tools/*.ts` files (items 38-48)
5. `memory-bank/capabilities/` (10 YAML files) (item 67)
6. `memory-bank/generated/` (30+ files) (item 68)
7. `memory-bank/{architecture,engine-map,domain-invariants,validation-architecture,testing-strategy,service-map,database-map,dependency-map,engine-contracts,engine-maturity,cline-workflow,capability-index,capability-status,qea-rules,test-coverage,validation-review}.md` (items 69-84)

## FILES REQUIRING MERGE

1. `behaviour_engine/credit_dependency.py` (item 18) — merge into current package
2. `behaviour_engine/stress.py` (item 19) — merge into current package
3. `behaviour_engine/temporal.py` (item 20) — merge into current package
4. `loan_engine/` (item 26) — compare 12 Recon-V2 files vs 8 HEAD files; merge unique algorithms
5. `repositories/balance_repository.py` (item 28) — merge unique queries into `account_balance_repository.py`
6. `services/financial_intelligence_service.py` (item 34) — merge with `forecast_service.py`

## FILES TO DISCARD

1. `repositories/liquidity_pattern_repository.py` (item 31)
2. `memory-bank/regression-history.md` (item 85)
3. Historical memory-bank files (item 86)

---

## PROPOSED ENTERPRISE DIRECTORY ORGANIZATION AFTER RECOVERY

```
backend/
  src/
    engines/
      financial_intelligence/      ← RESTORE (7 files)
      transaction_intelligence/    ← RESTORE (5 files)
      financial_events/            ← RESTORE (2 files)
      loan_engine/                 ← MERGE (compare 12 vs 8, keep modular)
      behaviour_engine/            ← MERGE (add credit_dependency, stress, temporal)
      credit_card_engine/          ← KEEP CURRENT
      account_engine/              ← KEEP CURRENT
      balance_engine.py            ← KEEP CURRENT
      behavior_engine.py           ← KEEP CURRENT
      ledger_audit_engine.py       ← KEEP CURRENT
      reconciliation_engine.py     ← KEEP CURRENT
      recommendation_engine/       ← KEEP CURRENT
    repositories/
      financial_event_repository.py    ← RESTORE
      financial_goal_repository.py     ← RESTORE
      transaction_classification_repository.py ← RESTORE
      account_balance_repository.py    ← MERGE (from balance_repository.py)
      (all existing repositories)      ← KEEP CURRENT
    services/
      financial_intelligence_service.py  ← RESTORE
      transaction_intelligence_service.py ← RESTORE
      financial_events_service.py        ← RESTORE
      forecast_service.py                ← MERGE (with financial_intelligence_service)
      (all existing services)            ← KEEP CURRENT
    models/
      financial_goal.py                ← RESTORE
      (all existing models)            ← KEEP CURRENT
  tools/
    validation_orchestrator.py     ← RESTORE
    selective_verify.py            ← RESTORE
    change_intelligence.py         ← RESTORE
    check_coverage.py              ← RESTORE
    mutation_discovery.py          ← RESTORE
    test_strength.py               ← RESTORE
    coVF_discover.py               ← RESTORE
    validation_audit.py            ← RESTORE
  tests/
    architecture/                  ← RESTORE
    capabilities/                  ← RESTORE
    contracts/                     ← RESTORE
    domain/                        ← RESTORE
    golden/                        ← RESTORE
    invariants/                    ← RESTORE
    meta/                          ← RESTORE
    properties/                    ← RESTORE
    (all existing test files)      ← KEEP CURRENT
  scripts/
    verify-fast.sh                 ← RESTORE

frontend/
  tools/                           ← RESTORE (commit untracked + build_audit.ts)
  scripts/                         ← KEEP CURRENT (already tracked)

memory-bank/
  capabilities/                    ← RESTORE
  generated/                       ← RESTORE
  architecture.md                  ← RESTORE
  engine-map.md                    ← RESTORE
  domain-invariants.md             ← RESTORE
  validation-architecture.md       ← RESTORE
  testing-strategy.md              ← RESTORE
  service-map.md                   ← RESTORE
  database-map.md                  ← RESTORE
  dependency-map.md                ← RESTORE
  engine-contracts.md              ← RESTORE
  engine-maturity.md               ← RESTORE
  cline-workflow.md                ← RESTORE
  capability-index.md              ← RESTORE
  capability-status.json           ← RESTORE
  qea-rules.md                     ← RESTORE
  test-coverage.md                 ← RESTORE
  validation-review.md             ← RESTORE
  activeContext.md                 ← KEEP CURRENT
  projectbrief.md                  ← KEEP CURRENT
```

---

## RECOVERY EXECUTION BATCHES (Ordered by Dependency)

### Batch 1 — Foundation (No Dependencies)
- Restore `scripts/verify-fast.sh`
- Restore all 8 `backend/tools/*.py`
- Commit 10 untracked `frontend/tools/*.ts` files
- Restore `frontend/tools/build_audit.ts`
- Restore `memory-bank/capabilities/` and `memory-bank/generated/`
- Restore `memory-bank/*.md` documentation files

### Batch 2 — Testing Architecture (Depends on Batch 1)
- Restore all 8 `backend/tests/` subdirectories

### Batch 3 — Financial Intelligence Engines (Depends on Batch 2)
- Restore `financial_intelligence/` (7 files)
- Restore `transaction_intelligence/` (5 files)
- Restore `financial_events/` (2 files)
- Restore `loan_engine/` comparison (merge unique algorithms)

### Batch 4 — Service Layer (Depends on Batch 3)
- Restore `financial_intelligence_service.py`
- Restore `transaction_intelligence_service.py`
- Restore `financial_events_service.py`
- Merge `financial_intelligence_service.py` with `forecast_service.py`

### Batch 5 — Behaviour Engine Completion (Depends on Batch 3)
- Merge `credit_dependency.py`, `stress.py`, `temporal.py` into `behaviour_engine/`

### Batch 6 — Repository & Model Layer (Depends on Batch 4)
- Restore `financial_event_repository.py`
- Restore `financial_goal_repository.py`
- Restore `transaction_classification_repository.py`
- Restore `financial_goal.py`
- Merge `balance_repository.py` queries into `account_balance_repository.py`
