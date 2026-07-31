# ClariFin_OS — Integration Decision Document & Roadmap

## EXECUTIVE SUMMARY

The `Reconciliation-v2` branch (commit `363ea27e`) was developed in parallel to `main` for 40+ commits but was **never merged**. When the developer switched branches, all `Reconciliation-v2`-exclusive files were left behind. The current `stage-5`/`Production-Gate` branch rebuilt many capabilities from scratch but lost the entire verification infrastructure, testing architecture, and several backend engine modules.

This document identifies every lost capability, classifies it as KEEP_CURRENT / RESTORE / MERGE / REWRITE / DISCARD, and produces an ordered integration roadmap that avoids duplication and preserves the current architecture.

---

## DECISION KEY

- **KEEP CURRENT**: Current implementation is sufficient. Do not restore.
- **RESTORE**: Lost version has no current equivalent. Restore from Git as-is.
- **MERGE**: Both versions have value. Integrate lost functionality into current implementation.
- **REWRITE**: Lost functionality should be reimplemented from scratch to fit current architecture.
- **DISCARD**: No longer needed. Do not restore.

---

## 1. PARSING PIPELINE

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| Statement extraction (`camelot_extractor.py`, `hybrid_extractor.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present in current branch |
| Statement extractor (`statement_extractor.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present |
| Table extractor (`table_extractor.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present |
| CSV importer (`csv_importer.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present |
| Ingestion (`ingest.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present |
| Categorization (`categorizer.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present |
| Transaction parser (`transaction_parser.py`) | Tracked, exists | Same files | **KEEP CURRENT** | Already present |
| Parser debug tool (`debug-parser-step.ts`) | Lost | In `363ea27e` | **RESTORE** | Valuable developer tooling for debugging PDF parsing |
| Parser validation (`test-semantic-parser.ts`) | Lost | In `363ea27e` | **RESTORE** | Validates parser accuracy across all bank PDFs |
| Metadata auto-fix (`auto-fix-metadata.ts`) | Lost | In `363ea27e` | **DISCARD** | Niche tool, low ongoing value |
| Metadata test (`test-metadata.ts`) | Lost | In `363ea27e` | **DISCARD** | Niche tool, low ongoing value |
| Expected metadata generator (`generate-expected-metadata.js`) | Lost | In `363ea27e` | **DISCARD** | Test fixture generator, low ongoing value |

---

## 2. FINANCIAL INTELLIGENCE

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| Financial Intelligence Engine (`financial_intelligence/`) | Missing entirely | 7 files in `363ea27e` | **RESTORE** | No current equivalent. Forecasting, goal planning, optimization, scenario simulation all missing |
| Transaction Intelligence (`transaction_intelligence/`) | Missing entirely | 5 files in `363ea27e` | **RESTORE** | No current equivalent. Cash conversion, CC payment, EMI detection all missing |
| Financial Events (`financial_events/`) | Missing entirely | 2 files in `363ea27e` | **RESTORE** | No current equivalent. Event lineage tracking for audit trail |
| Behaviour Engine — `credit_dependency.py` | Missing (8/15 files) | In `363ea27e` | **MERGE** | Integrate into current `behaviour_engine/` package |
| Behaviour Engine — `stress.py` | Missing | In `363ea27e` | **MERGE** | Integrate into current `behaviour_engine/` package |
| Behaviour Engine — `temporal.py` | Missing | In `363ea27e` | **MERGE** | Integrate into current `behaviour_engine/` package |
| Behaviour Engine — `savings.py` | Missing | In `363ea27e` | **MERGE** | Integrate into current `behaviour_engine/` package |
| Behaviour Engine — `profile.py` | Missing | In `363ea27e` | **MERGE** | Integrate into current `behaviour_engine/` package |
| Behaviour Engine — `wellness.py` | Missing | In `363ea27e` | **MERGE** | Partial replacement exists in `behaviour_service.py`; merge unique logic |
| Behaviour Engine — `account.py` | Missing | In `363ea27e` | **MERGE** | Integrate into current `behaviour_engine/` package |
| Cashflow Engine (`cashflow_engine.py`) | Replaced by `cashflow_service.py` | In `363ea27e` | **KEEP CURRENT** | Already replaced by service-layer implementation |
| Loan Engine (`loan_engine/`) | Missing entirely | 12 files in `363ea27e` | **RESTORE** | No current equivalent. Credit card engine exists but loan engine is missing |
| Recommendation Engine | Tracked, exists | Same files | **KEEP CURRENT** | Already present |

---

## 3. BACKEND INFRASTRUCTURE

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| Balance Repository | `account_balance_repository.py` exists | `balance_repository.py` in `363ea27e` | **MERGE** | Merge unique queries from lost version into current |
| Financial Event Repository | Missing | In `363ea27e` | **RESTORE** | No current equivalent |
| Financial Goal Repository | Missing | In `363ea27e` | **RESTORE** | No current equivalent |
| Liquidity Pattern Repository | Missing | In `363ea27e` | **DISCARD** | Niche use case, low value |
| Transaction Classification Repository | Missing | In `363ea27e` | **RESTORE** | No current equivalent |
| Financial Events Service | Missing | In `363ea27e` | **RESTORE** | No current equivalent |
| Financial Intelligence Service | Missing | In `363ea27e` | **RESTORE** | No current equivalent. Critical for FI engine orchestration |
| Transaction Intelligence Service | Missing | In `363ea27e` | **RESTORE** | No current equivalent |
| Credit Card Statement Model | `credit_card.py` exists | `credit_card_statement.py` in `363ea27e` | **MERGE** | Merge statement-specific fields into current model |
| Financial Goal Model | Missing | In `363ea27e` | **RESTORE** | No current equivalent |

---

## 4. FRONTEND INFRASTRUCTURE

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| FVF — lock_toolchain.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — architecture_audit.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — type_react_audit.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — generated_api_audit.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — query_audit.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — import_audit.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — build_audit.ts | Missing from working tree | In `363ea27e` | **RESTORE** | Restore from Git history |
| FVF — validate.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — types.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — utils.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| FVF — fvf.test.ts | Untracked in working tree | In `363ea27e` | **RESTORE** | Commit existing untracked file |
| API Contract Tests (11 files) | Tracked, exists | Same files | **KEEP CURRENT** | Already present and tracked |
| Playwright Tests (4 files) | Tracked, exists | Same files | **KEEP CURRENT** | Already present and tracked |

---

## 5. TESTING ARCHITECTURE

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| Architecture boundary tests | Only pycache | In `363ea27e` | **RESTORE** | Enforces clean architecture — prevents future drift |
| Capability tests (11 files) | Only pycache | In `363ea27e` | **RESTORE** | Validates each financial capability end-to-end |
| Contract tests (8 files) | Only pycache | In `363ea27e` | **RESTORE** | API contract validation — prevents breaking changes |
| Domain tests (20+ files) | Only pycache | In `363ea27e` | **RESTORE** | Domain invariant tests — ensures financial correctness |
| Golden dataset tests (20+ files) | Only pycache | In `363ea27e` | **RESTORE** | Regression tests for financial calculations |
| Invariant tests (4 files) | Only pycache | In `363ea27e` | **RESTORE** | Financial invariant tests |
| Meta tests (6 files) | Only pycache | In `363ea27e` | **RESTORE** | Validates test infrastructure itself |
| Property tests (10+ files) | Only pycache | In `363ea27e` | **RESTORE** | Property-based testing for edge cases |

---

## 6. BACKEND VERIFICATION TOOLS

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| Validation Orchestrator (`validation_orchestrator.py`) | Missing | In `363ea27e` | **RESTORE** | Central validation framework — no current equivalent |
| Selective Verify (`selective_verify.py`) | Missing | In `363ea27e` | **RESTORE** | SVF — speeds up CI dramatically |
| Change Intelligence (`change_intelligence.py`) | Missing | In `363ea27e` | **RESTORE** | CIF — feeds SVF with change impact analysis |
| Check Coverage (`check_coverage.py`) | Missing | In `363ea27e` | **RESTORE** | Coverage integrity checker |
| Mutation Discovery (`mutation_discovery.py`) | Missing | In `363ea27e` | **RESTORE** | Mutation testing framework |
| Test Strength (`test_strength.py`) | Missing | In `363ea27e` | **RESTORE** | Test strength assessment |
| CoVF Discover (`coVF_discover.py`) | Missing | In `363ea27e` | **RESTORE** | Contract validation discovery |
| Validation Audit (`validation_audit.py`) | Missing | In `363ea27e` | **RESTORE** | Validation audit reporting |

---

## 7. SCRIPTS & DEVELOPER TOOLING

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| `scripts/verify-fast.sh` | Missing | In `363ea27e` | **RESTORE** | Fast verification script — critical for CI |

---

## 8. MEMORY-BANK ASSETS

| Capability | Current State | Lost Version | Decision | Rationale |
|---|---|---|---|---|
| `memory-bank/capabilities/` (10 YAML files) | Missing | In `363ea27e` | **RESTORE** | Source of truth for capability-based testing |
| `memory-bank/generated/` (30+ files) | Missing | In `363ea27e` | **RESTORE** | Generated artifacts for verification pipeline |
| `memory-bank/architecture.md` | Missing | In `363ea27e` | **RESTORE** | System architecture documentation |
| `memory-bank/engine-map.md` | Missing | In `363ea27e` | **RESTORE** | Engine relationship map |
| `memory-bank/domain-invariants.md` | Missing | In `363ea27e` | **RESTORE** | Financial invariant definitions |
| `memory-bank/validation-architecture.md` | Missing | In `363ea27e` | **RESTORE** | Validation pipeline documentation |
| `memory-bank/testing-strategy.md` | Missing | In `363ea27e` | **RESTORE** | Testing approach documentation |
| `memory-bank/service-map.md` | Missing | In `363ea27e` | **RESTORE** | Service dependency map |
| `memory-bank/database-map.md` | Missing | In `363ea27e` | **RESTORE** | Database schema map |
| `memory-bank/dependency-map.md` | Missing | In `363ea27e` | **RESTORE** | Module dependency map |
| `memory-bank/engine-contracts.md` | Missing | In `363ea27e` | **RESTORE** | Engine interface contracts |
| `memory-bank/engine-maturity.md` | Missing | In `363ea27e` | **RESTORE** | Engine maturity tracking |
| `memory-bank/cline-workflow.md` | Missing | In `363ea27e` | **RESTORE** | Development workflow documentation |
| `memory-bank/capability-index.md` | Missing | In `363ea27e` | **RESTORE** | Capability navigation index |
| `memory-bank/capability-status.json` | Missing | In `363ea27e` | **RESTORE** | Capability completion status |
| `memory-bank/qea-rules.md` | Missing | In `363ea27e` | **RESTORE** | Quality/Edge/Architecture rules |
| `memory-bank/test-coverage.md` | Missing | In `363ea27e` | **RESTORE** | Test coverage documentation |
| `memory-bank/validation-review.md` | Missing | In `363ea27e` | **RESTORE** | Validation status tracking |
| `memory-bank/regression-history.md` | Missing | In `363ea27e` | **DISCARD** | Historical artifact, no current value |
| Historical memory-bank files (7 files) | Missing | In `cd539408` | **DISCARD** | Historical artifacts, no current value |

---

## INTEGRATION ROADMAP

### Phase 1 — Foundation (Critical, No Dependencies)

**Goal:** Restore the verification and testing infrastructure that has no current equivalent and is required for all other work.

| Order | Action | Source | Effort | Risk |
|---|---|---|---|---|
| 1 | Restore `scripts/verify-fast.sh` | `363ea27e` | Low | Low |
| 2 | Restore all 8 backend tools (`backend/tools/*.py`) | `363ea27e` | Medium | Medium |
| 3 | Restore `memory-bank/capabilities/` (10 YAML files) | `363ea27e` | Low | Low |
| 4 | Restore `memory-bank/generated/` (30+ files) | `363ea27e` | Low | Low |
| 5 | Commit untracked FVF tools (10 files from working tree) | Working tree | Low | Low |
| 6 | Restore `frontend/tools/build_audit.ts` from Git | `363ea27e` | Low | Low |
| 7 | Restore `frontend/scripts/debug-parser-step.ts` and `test-semantic-parser.ts` | `363ea27e` | Low | Low |

### Phase 2 — Testing Architecture (High Priority)

**Goal:** Restore the layered testing architecture that validates financial correctness.

| Order | Action | Source | Effort | Risk |
|---|---|---|---|---|
| 8 | Restore `backend/tests/architecture/test_layer_boundaries.py` | `363ea27e` | Low | Low |
| 9 | Restore `backend/tests/contracts/` (8 files) | `363ea27e` | High | High |
| 10 | Restore `backend/tests/domain/` (20+ files) | `363ea27e` | High | High |
| 11 | Restore `backend/tests/golden/` (20+ files) | `363ea27e` | High | High |
| 12 | Restore `backend/tests/invariants/` (4 files) | `363ea27e` | Medium | Medium |
| 13 | Restore `backend/tests/meta/` (6 files) | `363ea27e` | Medium | Medium |
| 14 | Restore `backend/tests/properties/` (10+ files) | `363ea27e` | High | High |
| 15 | Restore `backend/tests/capabilities/` (11 files) | `363ea27e` | High | High |

### Phase 3 — Financial Intelligence Engines (High Priority)

**Goal:** Restore the missing financial intelligence engines that have no current equivalent.

| Order | Action | Source | Effort | Risk |
|---|---|---|---|---|
| 16 | Restore `backend/src/engines/financial_intelligence/` (7 files) | `363ea27e` | High | High |
| 17 | Restore `backend/src/engines/transaction_intelligence/` (5 files) | `363ea27e` | High | High |
| 18 | Restore `backend/src/engines/financial_events/` (2 files) | `363ea27e` | Medium | Medium |
| 19 | Restore `backend/src/engines/loan_engine/` (12 files) | `363ea27e` | High | High |
| 20 | Restore `backend/src/services/financial_intelligence_service.py` | `363ea27e` | High | High |
| 21 | Restore `backend/src/services/transaction_intelligence_service.py` | `363ea27e` | High | High |
| 22 | Restore `backend/src/services/financial_events_service.py` | `363ea27e` | Medium | Medium |

### Phase 4 — Behaviour Engine Completion (Medium Priority)

**Goal:** Complete the behaviour engine by merging missing modules into the current package.

| Order | Action | Source | Effort | Risk |
|---|---|---|---|---|
| 23 | Merge `credit_dependency.py` into `behaviour_engine/` | `363ea27e` | Medium | Medium |
| 24 | Merge `stress.py` into `behaviour_engine/` | `363ea27e` | Medium | Medium |
| 25 | Merge `temporal.py` into `behaviour_engine/` | `363ea27e` | Medium | Medium |
| 26 | Merge `savings.py` into `behaviour_engine/` | `363ea27e` | Low | Low |
| 27 | Merge `profile.py` into `behaviour_engine/` | `363ea27e` | Medium | Medium |
| 28 | Merge `wellness.py` into `behaviour_engine/` | `363ea27e` | Medium | Medium |
| 29 | Merge `account.py` into `behaviour_engine/` | `363ea27e` | Medium | Medium |

### Phase 5 — Backend Infrastructure Completion (Medium Priority)

**Goal:** Complete the repository and model layers.

| Order | Action | Source | Effort | Risk |
|---|---|---|---|---|
| 30 | Restore `backend/src/repositories/financial_event_repository.py` | `363ea27e` | Medium | Medium |
| 31 | Restore `backend/src/repositories/financial_goal_repository.py` | `363ea27e` | Medium | Medium |
| 32 | Restore `backend/src/repositories/transaction_classification_repository.py` | `363ea27e` | Medium | Medium |
| 33 | Merge `balance_repository.py` queries into `account_balance_repository.py` | `363ea27e` | Low | Low |
| 34 | Restore `backend/src/models/financial_goal.py` | `363ea27e` | Low | Low |
| 35 | Merge `credit_card_statement.py` fields into `credit_card.py` | `363ea27e` | Low | Low |

### Phase 6 — Memory Bank Documentation (Low Priority)

**Goal:** Restore development context documentation.

| Order | Action | Source | Effort | Risk |
|---|---|---|---|---|
| 36 | Restore remaining memory-bank docs | `363ea27e` | Low | Low |

### Phase 7 — Discard (No Action Required)

| Capability | Reason |
|---|---|
| `liquidity_pattern_repository.py` | Niche use case, low value |
| `auto-fix-metadata.ts`, `test-metadata.ts`, `generate-expected-metadata.js` | Niche parser debugging tools |
| Historical memory-bank files (7 files) | Historical artifacts |
| `cashflow_engine.py` | Already replaced by `cashflow_service.py` |

---

## DUPLICATION AVOIDANCE RULES

1. **Before restoring any file, check if a current equivalent exists.** Use `git ls-tree HEAD -- <path>` to verify.
2. **For MERGE operations, always diff the lost version against the current version first.** Use `git diff <current_commit> <recon_v2_commit> -- <path>` to identify unique content.
3. **For engines, restore the entire directory at once** to preserve internal imports.
4. **For tests, restore the entire directory structure** to preserve conftest.py and __init__.py files.
5. **For memory-bank, restore all files at once** to preserve cross-references.
6. **Do not restore files that are already tracked in the current commit.** Verify with `git ls-tree HEAD -- <path>` before each restore.

---

## ROOT CAUSE SUMMARY

The loss was caused by **branch divergence without merge**: `Reconciliation-v2` was developed for 40+ commits in parallel to `main`/`stage-5` but was never integrated. When the developer switched branches, all `Reconciliation-v2`-exclusive files were left behind. The `stage-5` branch rebuilt many capabilities but lost the entire verification infrastructure, testing architecture, and several backend engine modules that existed only on `Reconciliation-v2`.

**Source commit for all restorations:** `363ea27e` (Reconciliation-v2 branch tip)
