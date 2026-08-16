# Architecture Documentation

## Overview

Stage 3 follows a strict layered architecture with clear ownership boundaries.

## Canonical Runtime Flow

```
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
```

## Ownership

### Backend
- Calculations
- Financial rules
- Reconciliation
- Aggregation

### Mapper
- DTO → ViewModel transformation
- Date formatting
- Amount formatting
- Evidence mapping

### Capability
- Orchestration
- Filtering
- Sorting
- Searching
- Grouping
- Selection state
- Commands

### Workspace
- Layout
- Interaction
- Routing

### Components
- Presentation only
- No fetching
- No calculations
- No DTO mapping
- No business state mutation

## Component Rules

Components MUST:
- Render
- Format
- Emit events

Components MUST NOT:
- Fetch
- Calculate
- Map DTOs
- Mutate business state

## Capability Rules

Capability layer owns:
- Filtering
- Sorting
- Searching
- Orchestration
- Selection state
- Commands

Pages never implement capability logic.

## Data Ownership

```
React Query
  ↓
Capability
  ↓
Workspace
  ↓
Presentation
```

Never bypass this hierarchy.

## Testing Boundary

Tests verify:
- Capability contracts
- Explainability
- Invariants
- User behaviour

Tests never verify:
- CSS
- HTML structure
- Component implementation

## Reuse Policy

Before creating:
- Component
- Hook
- Mapper
- ViewModel
- Capability

Search for existing implementation. Duplicate implementations are prohibited.