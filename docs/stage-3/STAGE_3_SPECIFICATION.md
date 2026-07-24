# Stage 3 — Transaction Intelligence Workspace

## Stage Objective

Build the Transaction Intelligence Workspace.

This stage establishes the canonical workspace for exploring, understanding,
verifying and acting upon financial transactions.

The workspace becomes the foundation for every future capability including:

- Cashflow
- Behaviour
- Reconciliation
- Money Graph
- Dashboard
- AI Insights

This stage does NOT implement those capabilities.
It only exposes the transaction intelligence they will consume.

---

# Core Principles

The workspace must satisfy the global project constraints.

- Backend is the source of truth.
- No financial calculations inside the frontend.
- No duplicated business logic.
- Every displayed insight must be explainable.
- Components remain presentation-only.
- Capabilities own business orchestration.
- Workspace owns composition only.

---

# Scope

Included

- Transaction exploration
- Search
- Filtering
- Sorting
- Grouping
- Category navigation
- Merchant navigation
- Date navigation
- Selection model
- Bulk actions
- Evidence drilldown
- Import lineage
- Adjustment visibility
- Transaction relationships
- Explainability
- Navigation to dependent workspaces

Excluded

- Dashboard
- Behaviour workspace
- Cashflow workspace
- Reconciliation workspace
- Money Graph
- Forecasting
- Scenario simulation
- AI recommendations

---

# Deliverables

The stage produces

- Transaction Intelligence Capability
- Transaction Workspace
- Shared reusable components
- Shared ViewModels
- Shared mappers
- Shared evidence model
- Tests
- Documentation

No speculative components may be created.

---

# Success Definition

A user should be able to answer every question about any transaction without
leaving this workspace.

Examples

Where did this come from?

Why was it categorized here?

Which import created it?

What calculations depend on it?

Which balance includes it?

Which reconciliation references it?

What evidence supports this classification?

How was this amount derived?

If those questions cannot be answered, the stage is incomplete.
