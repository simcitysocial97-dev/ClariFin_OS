# Architectural Decision Log — ClariFin_OS

> Tracking key architectural decisions and rationale. Each entry is concise (<60 lines).

---

## Template

```markdown
### [ID] Decision Title

**Status:** Accepted | Proposed | Superseded  
**Date:** YYYY-MM-DD  
**Deciders:** [Team/Stakeholders]

**Context:** What problem necessitated this decision?

**Decision:** What was decided?

**Consequences:** What becomes easier/harder?

**Alternatives Considered:** What else was evaluated?
```

---

## Decisions

### [AD-001] Dashboard Built Last

**Status:** Accepted  
**Date:** 2024-07  
**Deciders:** Lead Engineer, Product Team

**Context:** Frontend development requires stable backend contracts. Early dashboard attempts failed due to API instability.

**Decision:** Build dashboard components only after backend contracts are stable and verified. Start with API layer, then services, then UI.

**Consequences:** Easier: API contract stability, type consistency. Harder: Longer initial feedback loop.

**Alternatives Considered:** Parallel frontend/backend development (led to integration churn).

---

### [AD-002] Invariant Testing Over Snapshot Testing

**Context:** Snapshot tests drift with legitimate changes; financial correctness requires verification against mathematical identities.

**Decision:** Use property/invariant tests (Hypothesis) for all financial logic, supplemented by golden master tests for known formulas.

**Consequences:** Easier: Mathematical correctness verification, edge case discovery. Harder: Test setup complexity for property testing.

**Alternatives Considered:** Jest snapshots (rejected), pytest fixtures only (insufficient coverage).

---

### [AD-003] Backend-first Architecture

**Status:** Accepted  
**Date:** 2024-07  
**Deciders:** Lead Engineer, Architecture Review

**Context:** Financial systems require data integrity. Frontend-first led to speculative API contracts.

**Decision:** SQLite/FastAPI backend is the single source of truth. Frontend consumes OpenAPI types. All state mutations go through API.

**Consequences:** Easier: Data consistency, audit trail, offline capability. Harder: Slower UI iteration.

**Alternatives Considered:** Full-stack TypeScript (prisma, next.js), Firebase backend (rejected for privacy-first requirement).

---

### [AD-004] Explainability-first Philosophy

**Context:** Financial AI must be auditable. Black-box models create trust issues.

**Decision:** Every financial metric MUST have an explainable derivation. LLM explanations derive from deterministic data. Cache explanations to prevent drift.

**Consequences:** Easier: User trust, regulatory compliance, debugging. Harder: More complex output structures.

**Alternatives Considered:** Opaque scoring (rejected), score-only display (insufficient for finance).

---

### [AD-005] Paise-integer Monetary Convention

**Status:** Accepted  
**Date:** 2024-07  
**Deciders:** Lead Engineer

**Context:** Float precision errors cause silent financial miscalculations. Rupee floats display inconsistently (₹1.00 vs 1.0).

**Decision:** Store all monetary values as integers representing paise (₹1 = 100 paise). Use `decimal.Decimal` for division.

**Consequences:** Easier: Exact arithmetic, consistent display, audit verification. Harder: Conversion overhead, UI formatting.

**Alternatives Considered:** Float rupees (precision risk), string storage (comparisons hard), Decimal objects (SQLite lacks native support).

---

### [AD-006] Pure Engine Architecture

**Status:** Accepted (exception: audit tools)  
**Date:** 2024-07  
**Deciders:** Lead Engineer

**Context:** Testing impure engines requires database fixtures. Financial logic should be deterministic and testable.

**Decision:** Engines accept data via parameters (list[dict]), NOT db_path. Repositories handle SQL. Exception: audit engines (balance_engine, ledger_audit_engine).

**Consequences:** Easier: Unit testing, determinism, parallelization. Harder: Refactoring legacy impure engines.

**Alternatives Considered:** Impure engines (rejected), ORM abstraction (rejected for simplicity).

---

### [AD-007] Capability-based Testing

**Status:** Accepted  
**Date:** 2024-07  
**Deciders:** QA Lead, Lead Engineer

**Context:** Monolithic test suites grow slowly with unclear coverage. Need domain-focused validation.

**Decision:** Organize tests by business capability. Each capability has smoke, property, and golden tests. Map to architectural layers.

**Consequences:** Easier: Selective verification, coverage mapping, impact analysis. Harder: Initial setup overhead.

**Alternatives Considered:** File-based test organization (rejected), feature-based only (insufficient granularity).

---

### [AD-008] Repository Boundary Rule

**Status:** Accepted (enforce)  
**Date:** 2024-07  
**Deciders:** Lead Engineer

**Context:** Cross-layer database access creates coupling and testing complexity. Engines should be pure.

**Decision:** ONLY files under `src/repositories/` may import FinanceDB. Violation triggers immediate refactoring.

**Consequences:** Easier: Layer separation, testability. Harder: Refactoring existing boundary violations.

**Alternatives Considered:** Dependency injection (more complex), service-layer DB access (still violates).

---

*Version: 1.0 (Stage 0)*  
*Last updated: July 16, 2026*