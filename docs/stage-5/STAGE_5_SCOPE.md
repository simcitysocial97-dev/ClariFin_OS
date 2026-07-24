# Stage 5 — Command Center Platform

## Objective

Build the Financial Operating System home screen.

The Command Center is a composition layer built on top of the Financial Graph Runtime.

It must not duplicate workspace logic.

It must not perform financial calculations.

It consumes only Runtime APIs.

---

## Architecture

Backend

↓

DTO

↓

Mapper

↓

ViewModel

↓

Capability

↓

Workspace

↓

Financial Graph Runtime

↓

Command Center Runtime

↓

Command Center UI

---

## Responsibilities

The Command Center provides:

- Money Graph visualization
- Financial timeline
- Workspace previews
- Context panels
- Insight feed
- Global search
- Cross-workspace navigation
- Layout management

---

## Out of Scope

Do not modify:

- Backend
- DTOs
- Mappers
- ViewModels
- Workspace capabilities
- Financial calculations

Do not introduce duplicate business logic.

---

## Exit Criteria

The Command Center becomes the single entry point into ClariFin_OS.

Every workspace is reachable through the graph.

Every insight is explainable.

Every navigation path is deterministic.

The Money Graph is the primary interaction model.
