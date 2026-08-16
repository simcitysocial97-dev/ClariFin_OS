# Stage 5 Technical Specification

## Runtime

Create a new runtime layer:

CommandCenterRuntime

Responsibilities:

- workspace registration
- panel routing
- graph synchronization
- node focus
- workspace preview
- layout persistence
- event propagation

---

## Money Graph

Primary visualization.

Supports:

- zoom
- pan
- fit
- search
- trace
- expand
- collapse
- highlight
- path traversal
- selection

Consumes only FinancialGraphRuntime.

---

## Timeline

Chronological financial activity.

Examples:

Salary

↓

Transfer

↓

Expense

↓

Investment

↓

Loan payment

↓

Forecast

Timeline is graph-backed.

---

## Workspace Preview

Selecting any graph node loads:

- summary
- key metrics
- evidence
- navigation
- actions

without opening the workspace.

---

## Context Panel

Displays:

Summary

Evidence

Calculation

Confidence

Sources

Relationships

Navigation

No hidden calculations.

---

## Insight Feed

Runtime-generated.

Not static widgets.

Examples:

- spending anomalies
- large transfers
- loan milestones
- investment changes
- forecast alerts

Every insight links back to graph nodes.

---

## Global Search

Searches:

- transactions
- merchants
- categories
- accounts
- cards
- loans
- investments
- forecasts
- behaviors

Returns graph nodes.

---

## Layout Runtime

Supports:

- docking
- resize
- collapse
- favorites
- saved layouts

No business logic.

---

## Runtime Rules

Everything consumes:

FinancialGraphRuntime

Nothing bypasses Runtime.

No duplicate calculations.

No direct API calls from UI.

No duplicated workspace logic.
