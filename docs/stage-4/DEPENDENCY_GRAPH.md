# Stage 4 — Dependency Graph & Execution Levels

## Overview
This document classifies every capability across all 9 workspaces into execution levels. Capabilities in the same level have no architectural dependency on one another and can be executed in parallel.

---

## Level 0 — Foundation (Backend DTOs)

All Level 0 capabilities are **Parallel** — no cross-workspace dependency.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L0-01 | Net Worth | Backend DTO (Cap 18) | Parallel | None |
| L0-02 | Cashflow | Backend DTO (Cap 18) | Parallel | None |
| L0-03 | Accounts | Backend DTO (Cap 18) | Parallel | None |
| L0-04 | Loans | Backend DTO (Cap 18) | Parallel | None |
| L0-05 | Credit Cards | Backend DTO (Cap 18) | Parallel | None |
| L0-06 | Investments | Backend DTO (Cap 18) | Parallel | None |
| L0-07 | Reconciliation | Backend DTO (Cap 18) | Parallel | None |
| L0-08 | Behaviour | Backend DTO (Cap 18) | Parallel | None |
| L0-09 | Forecast | Backend DTO (Cap 18) | Parallel | None |

---

## Level 1 — ViewModel Types

All Level 1 capabilities are **Parallel** — each ViewModel is independent.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L1-01 | Net Worth | ViewModel (Cap 1) | Parallel | None |
| L1-02 | Cashflow | ViewModel (Cap 1) | Parallel | None |
| L1-03 | Accounts | ViewModel (Cap 1) | Parallel | None |
| L1-04 | Loans | ViewModel (Cap 1) | Parallel | None |
| L1-05 | Credit Cards | ViewModel (Cap 1) | Parallel | None |
| L1-06 | Investments | ViewModel (Cap 1) | Parallel | None |
| L1-07 | Reconciliation | ViewModel (Cap 1) | Parallel | None |
| L1-08 | Behaviour | ViewModel (Cap 1) | Parallel | None |
| L1-09 | Forecast | ViewModel (Cap 1) | Parallel | None |

---

## Level 2 — Mappers

All Level 2 capabilities are **Parallel** — each mapper depends only on its own ViewModel.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L2-01 | Net Worth | Mapper (Cap 2) | Parallel | L1-01 |
| L2-02 | Cashflow | Mapper (Cap 2) | Parallel | L1-02 |
| L2-03 | Accounts | Mapper (Cap 2) | Parallel | L1-03 |
| L2-04 | Loans | Mapper (Cap 2) | Parallel | L1-04 |
| L2-05 | Credit Cards | Mapper (Cap 2) | Parallel | L1-05 |
| L2-06 | Investments | Mapper (Cap 2) | Parallel | L1-06 |
| L2-07 | Reconciliation | Mapper (Cap 2) | Parallel | L1-07 |
| L2-08 | Behaviour | Mapper (Cap 2) | Parallel | L1-08 |
| L2-09 | Forecast | Mapper (Cap 2) | Parallel | L1-09 |

---

## Level 3 — Backend Services

All Level 3 capabilities are **Parallel** — each service depends only on its own DTO.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L3-01 | Net Worth | Backend Service (Cap 20) | Parallel | L0-01 |
| L3-02 | Cashflow | Backend Service (Cap 20) | Parallel | L0-02 |
| L3-03 | Accounts | Backend Service (Cap 20) | Parallel | L0-03 |
| L3-04 | Loans | Backend Service (Cap 20) | Parallel | L0-04 |
| L3-05 | Credit Cards | Backend Service (Cap 20) | Parallel | L0-05 |
| L3-06 | Investments | Backend Service (Cap 20) | Parallel | L0-06 |
| L3-07 | Reconciliation | Backend Service (Cap 20) | Parallel | L0-07 |
| L3-08 | Behaviour | Backend Service (Cap 20) | Parallel | L0-08 |
| L3-09 | Forecast | Backend Service (Cap 20) | Parallel | L0-09 |

---

## Level 4 — Backend Routers

All Level 4 capabilities are **Parallel** — each router depends only on its own Service and DTO.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L4-01 | Net Worth | Backend Router (Cap 19) | Parallel | L0-01, L3-01 |
| L4-02 | Cashflow | Backend Router (Cap 19) | Parallel | L0-02, L3-02 |
| L4-03 | Accounts | Backend Router (Cap 19) | Parallel | L0-03, L3-03 |
| L4-04 | Loans | Backend Router (Cap 19) | Parallel | L0-04, L3-04 |
| L4-05 | Credit Cards | Backend Router (Cap 19) | Parallel | L0-05, L3-05 |
| L4-06 | Investments | Backend Router (Cap 19) | Parallel | L0-06, L3-06 |
| L4-07 | Reconciliation | Backend Router (Cap 19) | Parallel | L0-07, L3-07 |
| L4-08 | Behaviour | Backend Router (Cap 19) | Parallel | L0-08, L3-08 |
| L4-09 | Forecast | Backend Router (Cap 19) | Parallel | L0-09, L3-09 |

---

## Level 5 — Capability Hooks

All Level 5 capabilities are **Parallel** — each hook depends only on its own ViewModel and Mapper.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L5-01 | Net Worth | Capability Hook (Cap 3) | Parallel | L1-01, L2-01 |
| L5-02 | Cashflow | Capability Hook (Cap 3) | Parallel | L1-02, L2-02 |
| L5-03 | Accounts | Capability Hook (Cap 3) | Parallel | L1-03, L2-03 |
| L5-04 | Loans | Capability Hook (Cap 3) | Parallel | L1-04, L2-04 |
| L5-05 | Credit Cards | Capability Hook (Cap 3) | Parallel | L1-05, L2-05 |
| L5-06 | Investments | Capability Hook (Cap 3) | Parallel | L1-06, L2-06 |
| L5-07 | Reconciliation | Capability Hook (Cap 3) | Parallel | L1-07, L2-07 |
| L5-08 | Behaviour | Capability Hook (Cap 3) | Parallel | L1-08, L2-08 |
| L5-09 | Forecast | Capability Hook (Cap 3) | Parallel | L1-09, L2-09 |

---

## Level 6 — UI Components (Summary Cards, Charts, Tables)

All Level 6 capabilities are **Parallel** — each component depends only on its own Capability Hook.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L6-01 | Net Worth | Summary Card (Cap 4) | Parallel | L5-01 |
| L6-02 | Net Worth | Composition Chart (Cap 5) | Parallel | L5-01 |
| L6-03 | Net Worth | Trend Chart (Cap 6) | Parallel | L5-01 |
| L6-04 | Net Worth | Account Breakdown (Cap 7) | Parallel | L5-01 |
| L6-05 | Cashflow | Summary Card (Cap 4) | Parallel | L5-02 |
| L6-06 | Cashflow | Monthly Trend (Cap 5) | Parallel | L5-02 |
| L6-07 | Cashflow | Category Breakdown (Cap 6) | Parallel | L5-02 |
| L6-08 | Cashflow | Transaction List (Cap 7) | Parallel | L5-02 |
| L6-09 | Accounts | Summary Card (Cap 4) | Parallel | L5-03 |
| L6-10 | Accounts | Balance Trend (Cap 5) | Parallel | L5-03 |
| L6-11 | Accounts | Type Breakdown (Cap 6) | Parallel | L5-03 |
| L6-12 | Accounts | Transaction List (Cap 7) | Parallel | L5-03 |
| L6-13 | Loans | Summary Card (Cap 4) | Parallel | L5-04 |
| L6-14 | Loans | Amortization Schedule (Cap 5) | Parallel | L5-04 |
| L6-15 | Loans | Payment Progress (Cap 6) | Parallel | L5-04 |
| L6-16 | Loans | Interest Analysis (Cap 7) | Parallel | L5-04 |
| L6-17 | Credit Cards | Summary Card (Cap 4) | Parallel | L5-05 |
| L6-18 | Credit Cards | Statement History (Cap 5) | Parallel | L5-05 |
| L6-19 | Credit Cards | Utilization Chart (Cap 6) | Parallel | L5-05 |
| L6-20 | Credit Cards | Spending by Category (Cap 7) | Parallel | L5-05 |
| L6-21 | Investments | Summary Card (Cap 4) | Parallel | L5-06 |
| L6-22 | Investments | Performance Chart (Cap 5) | Parallel | L5-06 |
| L6-23 | Investments | Asset Allocation (Cap 6) | Parallel | L5-06 |
| L6-24 | Investments | Holdings Table (Cap 7) | Parallel | L5-06 |
| L6-25 | Reconciliation | Summary Card (Cap 4) | Parallel | L5-07 |
| L6-26 | Reconciliation | Status Overview (Cap 5) | Parallel | L5-07 |
| L6-27 | Reconciliation | Discrepancy List (Cap 6) | Parallel | L5-07 |
| L6-28 | Reconciliation | Audit Trail (Cap 7) | Parallel | L5-07 |
| L6-29 | Behaviour | Score Card (Cap 4) | Parallel | L5-08 |
| L6-30 | Behaviour | Spending Patterns (Cap 5) | Parallel | L5-08 |
| L6-31 | Behaviour | Savings Rate (Cap 6) | Parallel | L5-08 |
| L6-32 | Behaviour | Debt Health (Cap 7) | Parallel | L5-08 |
| L6-33 | Behaviour | Wellness Radar (Cap 8) | Parallel | L5-08 |
| L6-34 | Forecast | Summary Card (Cap 4) | Parallel | L5-09 |
| L6-35 | Forecast | Net Worth Projection (Cap 5) | Parallel | L5-09 |
| L6-36 | Forecast | Cashflow Projection (Cap 6) | Parallel | L5-09 |
| L6-37 | Forecast | Scenario Comparison (Cap 7) | Parallel | L5-09 |

---

## Level 7 — UI Infrastructure (Filters, Search, Evidence, Insights, Toolbar)

All Level 7 capabilities are **Parallel** — each depends only on its own Capability Hook.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L7-01 | Net Worth | Filters (Cap 8) | Parallel | L5-01 |
| L7-02 | Net Worth | Search (Cap 9) | Parallel | L5-01 |
| L7-03 | Net Worth | Evidence Drawer (Cap 10) | Parallel | L5-01 |
| L7-04 | Net Worth | Insights Panel (Cap 11) | Parallel | L5-01 |
| L7-05 | Net Worth | Toolbar (Cap 12) | Parallel | L5-01 |
| L7-06 | Cashflow | Filters (Cap 8) | Parallel | L5-02 |
| L7-07 | Cashflow | Search (Cap 9) | Parallel | L5-02 |
| L7-08 | Cashflow | Evidence Drawer (Cap 10) | Parallel | L5-02 |
| L7-09 | Cashflow | Insights Panel (Cap 11) | Parallel | L5-02 |
| L7-10 | Cashflow | Toolbar (Cap 12) | Parallel | L5-02 |
| L7-11 | Accounts | Filters (Cap 8) | Parallel | L5-03 |
| L7-12 | Accounts | Search (Cap 9) | Parallel | L5-03 |
| L7-13 | Accounts | Evidence Drawer (Cap 10) | Parallel | L5-03 |
| L7-14 | Accounts | Insights Panel (Cap 11) | Parallel | L5-03 |
| L7-15 | Accounts | Toolbar (Cap 12) | Parallel | L5-03 |
| L7-16 | Loans | Filters (Cap 8) | Parallel | L5-04 |
| L7-17 | Loans | Search (Cap 9) | Parallel | L5-04 |
| L7-18 | Loans | Evidence Drawer (Cap 10) | Parallel | L5-04 |
| L7-19 | Loans | Insights Panel (Cap 11) | Parallel | L5-04 |
| L7-20 | Loans | Toolbar (Cap 12) | Parallel | L5-04 |
| L7-21 | Credit Cards | Filters (Cap 8) | Parallel | L5-05 |
| L7-22 | Credit Cards | Search (Cap 9) | Parallel | L5-05 |
| L7-23 | Credit Cards | Evidence Drawer (Cap 10) | Parallel | L5-05 |
| L7-24 | Credit Cards | Insights Panel (Cap 11) | Parallel | L5-05 |
| L7-25 | Credit Cards | Toolbar (Cap 12) | Parallel | L5-05 |
| L7-26 | Investments | Filters (Cap 8) | Parallel | L5-06 |
| L7-27 | Investments | Search (Cap 9) | Parallel | L5-06 |
| L7-28 | Investments | Evidence Drawer (Cap 10) | Parallel | L5-06 |
| L7-29 | Investments | Insights Panel (Cap 11) | Parallel | L5-06 |
| L7-30 | Investments | Toolbar (Cap 12) | Parallel | L5-06 |
| L7-31 | Reconciliation | Filters (Cap 8) | Parallel | L5-07 |
| L7-32 | Reconciliation | Search (Cap 9) | Parallel | L5-07 |
| L7-33 | Reconciliation | Evidence Drawer (Cap 10) | Parallel | L5-07 |
| L7-34 | Reconciliation | Insights Panel (Cap 11) | Parallel | L5-07 |
| L7-35 | Reconciliation | Toolbar (Cap 12) | Parallel | L5-07 |
| L7-36 | Behaviour | Filters (Cap 9) | Parallel | L5-08 |
| L7-37 | Behaviour | Search (Cap 10) | Parallel | L5-08 |
| L7-38 | Behaviour | Evidence Drawer (Cap 11) | Parallel | L5-08 |
| L7-39 | Behaviour | Insights Panel (Cap 12) | Parallel | L5-08 |
| L7-40 | Behaviour | Toolbar (Cap 13) | Parallel | L5-08 |
| L7-41 | Forecast | Filters (Cap 8) | Parallel | L5-09 |
| L7-42 | Forecast | Search (Cap 9) | Parallel | L5-09 |
| L7-43 | Forecast | Evidence Drawer (Cap 10) | Parallel | L5-09 |
| L7-44 | Forecast | Insights Panel (Cap 11) | Parallel | L5-09 |
| L7-45 | Forecast | Toolbar (Cap 12) | Parallel | L5-09 |

---

## Level 8 — UX Infrastructure (Loading, Error, Empty States)

All Level 8 capabilities are **Parallel** — each depends only on its own Capability Hook.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L8-01 | Net Worth | Loading States (Cap 14) | Parallel | L5-01 |
| L8-02 | Net Worth | Error States (Cap 15) | Parallel | L5-01 |
| L8-03 | Net Worth | Empty States (Cap 16) | Parallel | L5-01 |
| L8-04 | Cashflow | Loading States (Cap 14) | Parallel | L5-02 |
| L8-05 | Cashflow | Error States (Cap 15) | Parallel | L5-02 |
| L8-06 | Cashflow | Empty States (Cap 16) | Parallel | L5-02 |
| L8-07 | Accounts | Loading States (Cap 14) | Parallel | L5-03 |
| L8-08 | Accounts | Error States (Cap 15) | Parallel | L5-03 |
| L8-09 | Accounts | Empty States (Cap 16) | Parallel | L5-03 |
| L8-10 | Loans | Loading States (Cap 14) | Parallel | L5-04 |
| L8-11 | Loans | Error States (Cap 15) | Parallel | L5-04 |
| L8-12 | Loans | Empty States (Cap 16) | Parallel | L5-04 |
| L8-13 | Credit Cards | Loading States (Cap 14) | Parallel | L5-05 |
| L8-14 | Credit Cards | Error States (Cap 15) | Parallel | L5-05 |
| L8-15 | Credit Cards | Empty States (Cap 16) | Parallel | L5-05 |
| L8-16 | Investments | Loading States (Cap 14) | Parallel | L5-06 |
| L8-17 | Investments | Error States (Cap 15) | Parallel | L5-06 |
| L8-18 | Investments | Empty States (Cap 16) | Parallel | L5-06 |
| L8-19 | Reconciliation | Loading States (Cap 14) | Parallel | L5-07 |
| L8-20 | Reconciliation | Error States (Cap 15) | Parallel | L5-07 |
| L8-21 | Reconciliation | Empty States (Cap 16) | Parallel | L5-07 |
| L8-22 | Behaviour | Loading States (Cap 14) | Parallel | L5-08 |
| L8-23 | Behaviour | Error States (Cap 15) | Parallel | L5-08 |
| L8-24 | Behaviour | Empty States (Cap 16) | Parallel | L5-08 |
| L8-25 | Forecast | Loading States (Cap 14) | Parallel | L5-09 |
| L8-26 | Forecast | Error States (Cap 15) | Parallel | L5-09 |
| L8-27 | Forecast | Empty States (Cap 16) | Parallel | L5-09 |

---

## Level 9 — Cross-Navigation

All Level 9 capabilities are **Parallel** — each depends only on its own Capability Hook.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L9-01 | Net Worth | Cross-Navigation (Cap 17) | Parallel | L5-01 |
| L9-02 | Cashflow | Cross-Navigation (Cap 17) | Parallel | L5-02 |
| L9-03 | Accounts | Cross-Navigation (Cap 17) | Parallel | L5-03 |
| L9-04 | Loans | Cross-Navigation (Cap 17) | Parallel | L5-04 |
| L9-05 | Credit Cards | Cross-Navigation (Cap 17) | Parallel | L5-05 |
| L9-06 | Investments | Cross-Navigation (Cap 17) | Parallel | L5-06 |
| L9-07 | Reconciliation | Cross-Navigation (Cap 17) | Parallel | L5-07 |
| L9-08 | Behaviour | Cross-Navigation (Cap 17) | Parallel | L5-08 |
| L9-09 | Forecast | Cross-Navigation (Cap 17) | Parallel | L5-09 |

---

## Level 10 — Workspace Pages (Composition)

All Level 10 capabilities are **Sequential** within each workspace — each page depends on all prior capabilities in its workspace. Pages across workspaces are **Parallel**.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L10-01 | Net Worth | Workspace Page (Cap 13) | Sequential | L5-01, L6-01..04, L7-01..05, L8-01..03, L9-01 |
| L10-02 | Cashflow | Workspace Page (Cap 13) | Sequential | L5-02, L6-05..08, L7-06..10, L8-04..06, L9-02 |
| L10-03 | Accounts | Workspace Page (Cap 13) | Sequential | L5-03, L6-09..12, L7-11..15, L8-07..09, L9-03 |
| L10-04 | Loans | Workspace Page (Cap 13) | Sequential | L5-04, L6-13..16, L7-16..20, L8-10..12, L9-04 |
| L10-05 | Credit Cards | Workspace Page (Cap 13) | Sequential | L5-05, L6-17..20, L7-21..25, L8-13..15, L9-05 |
| L10-06 | Investments | Workspace Page (Cap 13) | Sequential | L5-06, L6-21..24, L7-26..30, L8-16..18, L9-06 |
| L10-07 | Reconciliation | Workspace Page (Cap 13) | Sequential | L5-07, L6-25..28, L7-31..35, L8-19..21, L9-07 |
| L10-08 | Behaviour | Workspace Page (Cap 13) | Sequential | L5-08, L6-29..33, L7-36..40, L8-22..24, L9-08 |
| L10-09 | Forecast | Workspace Page (Cap 13) | Sequential | L5-09, L6-34..37, L7-41..45, L8-25..27, L9-09 |

---

## Level 11 — Benchmark Validation

All Level 11 capabilities are **Sequential** — each depends on its own completed workspace.

| ID | Workspace | Capability | Type | Dependencies |
|----|-----------|------------|------|--------------|
| L11-01 | Net Worth | Benchmark Validation (Cap 21) | Sequential | L10-01 |
| L11-02 | Cashflow | Benchmark Validation (Cap 21) | Sequential | L10-02 |
| L11-03 | Accounts | Benchmark Validation (Cap 21) | Sequential | L10-03 |
| L11-04 | Loans | Benchmark Validation (Cap 21) | Sequential | L10-04 |
| L11-05 | Credit Cards | Benchmark Validation (Cap 21) | Sequential | L10-05 |
| L11-06 | Investments | Benchmark Validation (Cap 21) | Sequential | L10-06 |
| L11-07 | Reconciliation | Benchmark Validation (Cap 21) | Sequential | L10-07 |
| L11-08 | Behaviour | Benchmark Validation (Cap 21) | Sequential | L10-08 |
| L11-09 | Forecast | Benchmark Validation (Cap 21) | Sequential | L10-09 |

---

## Execution Level Summary

| Level | Count | Parallelism | Description |
|-------|-------|-------------|-------------|
| L0 | 9 | Full Parallel | Backend DTOs |
| L1 | 9 | Full Parallel | ViewModel Types |
| L2 | 9 | Full Parallel | Mappers |
| L3 | 9 | Full Parallel | Backend Services |
| L4 | 9 | Full Parallel | Backend Routers |
| L5 | 9 | Full Parallel | Capability Hooks |
| L6 | 37 | Full Parallel | UI Components |
| L7 | 45 | Full Parallel | UI Infrastructure |
| L8 | 27 | Full Parallel | UX States |
| L9 | 9 | Full Parallel | Cross-Navigation |
| L10 | 9 | Per-Workspace Sequential | Workspace Pages |
| L11 | 9 | Per-Workspace Sequential | Benchmark Validation |

**Total capabilities: 189** (21 per workspace × 9 workspaces)

**Maximum parallel batch: 45** (Level 7)

**Minimum sequential steps: 12** (Levels 0→1→2→3→4→5→6→7→8→9→10→11)