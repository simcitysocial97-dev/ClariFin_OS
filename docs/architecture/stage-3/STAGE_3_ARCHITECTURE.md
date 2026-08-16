# Stage 3 — Architecture

## Canonical Runtime Flow

Backend

↓

API

↓

Generated DTO

↓

Mapper

↓

Transaction ViewModel

↓

Capability Layer

↓

Workspace Components

↓

Page

This flow is mandatory.

No layer may be skipped.

---

# Ownership

Backend

- calculations
- financial rules
- reconciliation
- aggregation

Mapper

- DTO → ViewModel

Capability

- orchestration
- filtering
- composition
- commands

Workspace

- layout
- interaction
- routing

Components

- presentation only

---

# Workspace Layout

+------------------------------------------------------+

Toolbar

--------------------------------------------------------

Filter Panel

--------------------------------------------------------

Transaction Grid / Table

--------------------------------------------------------

Selection Summary

--------------------------------------------------------

Insight Panel

--------------------------------------------------------

Evidence Drawer

--------------------------------------------------------

Action Drawer

+------------------------------------------------------+

This layout is canonical.

Future capabilities may reuse these regions.

---

# Explainability

Every insight must expose

Summary

↓

Evidence

↓

Calculation

↓

Source

Progressive disclosure is mandatory.

Nothing beyond Summary is visible by default.

---

# Component Rules

Components

Must

- render
- format
- emit events

Must NOT

- fetch
- calculate
- map DTOs
- mutate business state

---

# Capability Rules

Capability layer owns

- filtering
- sorting
- searching
- orchestration
- selection state
- commands

Pages never implement capability logic.

---

# Data Ownership

React Query

↓

Capability

↓

Workspace

↓

Presentation

Never bypass this hierarchy.

---

# Testing Boundary

Tests verify

- capability contracts
- explainability
- invariants
- user behaviour

Tests never verify

- CSS
- HTML structure
- component implementation

---

# Reuse Policy

Before creating

Component

Hook

Mapper

ViewModel

Capability

AI must first search for an existing implementation.

Duplicate implementations are prohibited.
