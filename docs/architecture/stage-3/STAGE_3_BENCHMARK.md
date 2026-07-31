# Stage 3 — Acceptance Benchmark

The stage is complete only when every benchmark passes.

---

# A. Functional

- Loads real backend data
- No mock financial data
- Search functional
- Multi-filter functional
- Sorting functional
- Grouping functional
- Merchant navigation functional
- Category navigation functional
- Date navigation functional
- Bulk selection functional
- Bulk actions functional
- Pagination or virtualization if required
- Import lineage visible
- Adjustment visibility present
- Cross-navigation working

---

# B. Explainability

Every transaction exposes

- Summary
- Evidence
- Calculation
- Source

Evidence drawer functional.

Calculation chain readable.

Source references navigable.

Confidence shown where applicable.

No hidden calculations.

---

# C. Architecture

No DTO reaches components.

Mapper layer used everywhere.

ViewModels consumed everywhere.

No duplicated mappers.

No duplicated hooks.

No duplicated capabilities.

No duplicated components.

No business logic inside page.

No calculations inside components.

---

# D. Runtime

Loading state

Empty state

Error state

Success state

Refresh state

Recoverable failures

No hydration issues

No runtime warnings

---

# E. Validation

TypeScript clean

ESLint clean

FVF Fast clean

Architecture validation clean

React Query validation clean

Generated type validation clean

Build successful

No console errors

---

# F. UX

Keyboard navigation

Responsive

Dark mode

Accessible

Consistent spacing

Predictable navigation

No dead ends

No placeholder UI

---

# G. Performance

Filtering responsive

Searching responsive

No unnecessary re-renders

Stable query cache

No duplicated requests

Lazy loading where appropriate

---

# H. Maintainability

No TODO comments

No FIXME comments

No temporary code

No hardcoded financial values

No speculative abstractions

Shared primitives reused

Shared formatter reused

Shared error handling reused

Shared loading reused

Shared empty states reused

---

# Stage Closure Checklist

The stage closes only when

✓ All benchmarks pass

✓ Human review completed

✓ Architecture unchanged

✓ FVF clean

✓ Tests green

✓ Documentation updated

✓ Decision log updated (if required)

After closure this stage is considered locked.

Future stages consume its capabilities but do not modify its architecture unless a genuine defect is discovered.
