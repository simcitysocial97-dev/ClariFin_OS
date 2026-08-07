# Program C — Repository Freeze Baseline

**Status:** FROZEN
**Date:** 2026-08-07
**Purpose:** Establish the immutable repository baseline for Program C — Product Completion & Production Readiness.

---

## 1. Frozen Architecture

| Component | Status | Note |
|-----------|--------|------|
| Financial OS Shell Architecture | FROZEN | `docs/FINANCIAL_OS_SHELL_ARCHITECTURE.md` v1.0.0 |
| Engineering Constitution | FROZEN | `docs/ENGINEERING_CONSTITUTION.md` |
| GitHub Actions Constitution | FROZEN | `docs/GITHUB_ACTIONS_CONSTITUTION.md` |
| Platform Foundation (Milestones 1-10) | FROZEN | All layers complete |
| Capability → Mapper → ViewModel pipeline | FROZEN | Canonical data flow |
| Runtime Ownership | FROZEN | Singleton instances, no duplicate state |
| EventBus | FROZEN | Inter-runtime communication |
| Integrity Rules (ARCH-001 through ARCH-028) | FROZEN | 28 rules, all verified |
| Repository Structure | FROZEN | No further restructuring |

---

## 2. Frozen Runtime

| Runtime | Path | Status |
|---------|------|--------|
| Selection Runtime | `frontend/lib/runtime/selection-runtime.ts` | FROZEN |
| Timeline Runtime | `frontend/lib/runtime/timeline-runtime.ts` | FROZEN |
| Navigation Runtime | `frontend/lib/runtime/navigation-runtime.ts` | FROZEN |
| Intelligence Runtime | `frontend/lib/intelligence/passive-runtime.ts` | FROZEN |
| Workspace Runtime | `frontend/lib/workspace/` | FROZEN |
| Command Center Runtime | `frontend/lib/command-center/` | FROZEN |
| Financial Graph Runtime | `backend/src/engines/` | FROZEN |

---

## 3. Frozen Canonical Ownership

| Domain | Canonical Owner | Status |
|-------|-----------------|--------|
| Accounts | `AccountService` / `AccountMapper` | FROZEN |
| Credit Cards | `CreditCardService` / `CreditCardMapper` | FROZEN |
| Loans | `LoanService` / `LoanMapper` | FROZEN |
| Investments | `InvestmentService` / `InvestmentMapper` | FROZEN |
| Reconciliation | `ReconciliationService` / `ReconciliationMapper` | FROZEN |
| Behaviour | `BehaviourService` / `behaviour_engine/` | FROZEN |
| Forecast | `ForecastService` / `ForecastMapper` | FROZEN |
| Cashflow | `CashflowService` / `CashflowMapper` | FROZEN |
| Net Worth | `NetWorthService` / `NetWorthMapper` | FROZEN |
| Dashboard | `DashboardService` / `DashboardMapper` | FROZEN |
| Audit/Verification | `AuditService` / ledger_audit_engine | FROZEN |

---

## 4. Frozen Repository Structure

```
ClariFin_OS/
├── backend/
│   ├── src/
│   │   ├── api.py                    # FastAPI entrypoint
│   │   ├── routers/                  # 28 routers (CANONICAL)
│   │   ├── services/                 # 33 services (CANONICAL)
│   │   ├── repositories/             # 27 repositories (CANONICAL)
│   │   ├── engines/                  # Computation engines (CANONICAL)
│   │   ├── core/                     # DB, DTOs, Mappers, Domain (CANONICAL)
│   │   ├── models/                   # Domain models (CANONICAL)
│   │   ├── extraction/               # PDF/CSV extraction (CANONICAL)
│   │   ├── orchestration/            # Post-upload pipeline (CANONICAL)
│   │   └── structural/               # Layout analysis (CANONICAL)
│   └── tests/                        # Backend test suite
├── frontend/
│   ├── app/                          # Next.js App Router workspaces
│   ├── components/                   # UI components (CANONICAL)
│   ├── lib/                          # Capabilities, runtimes, mappers (CANONICAL)
│   ├── styles/                       # Financial OS design system
│   └── tests/                        # Frontend test suite
├── runtime/                          # Engineering runtime (FROZEN)
├── docs/                             # Architecture & execution docs
└── .github/                          # CI workflows & actions
```

---

## 5. Baseline Guarantees

- All 28 integrity rules pass with 0 violations
- TypeScript compiles with 0 errors
- CI workflows valid YAML
- Artifact generation deterministic
- No placeholder workspaces
- No router restructuring
- No duplicate discovery
- No God files

---

## 6. Known Pre-existing Issues

These issues existed before Program C and are NOT product defects. They are tracked for future cleanup only if required by feature implementation.

| Issue | Severity | Status |
|-------|----------|--------|
| ESLint config: `react-hooks` plugin not installed | Low | Pre-existing |
| Backend: `tests/migrations/test_migration_confidence_bps.py` missing module | Low | Pre-existing |
| ContextPanel: entity data is synthetic/mock | **Product Gap** | See Program C Gap Inventory |
| Command Center: forecast mapped to cashflowData | **Product Defect** | See Program C Backlog |
| ResizableLayout: passthrough implementation | **Product Gap** | See Program C Gap Inventory |

---

## 7. Freeze Statement

**The repository structure, runtime, architecture, and canonical ownership are frozen.**

Future work must build on this baseline. No architectural restructuring. No router merging. No duplicate discovery. No placeholder workspaces.

Program C focuses exclusively on:
- Completing user-facing financial workflows
- Wiring real data into UI components
- Closing product capability gaps
- Production hardening via CI
