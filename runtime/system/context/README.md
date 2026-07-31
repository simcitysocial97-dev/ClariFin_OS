# Context Runtime

The **Context Runtime** is the global state engine of ClariFin_OS. It provides a deterministic, framework-independent runtime for managing contexts, workspaces, and user interactions.

## Design Principles

- **Time-first architecture**: Every state change is recorded with timestamps.
- **Immutable state**: All updates create new snapshots.
- **Serializable**: Full state can be serialized and restored.
- **Deterministic**: Same operations always produce the same results.
- **Event-driven**: All changes are recorded as events.
- **Workspace isolation**: No shared mutable state between workspaces.

## Core Components

| Component | Responsibility |
|-----------|----------------|
| `ContextRuntime` | Core singleton runtime |
| `ContextManager` | High-level API for context operations |
| `ContextRegistry` | Context registration and discovery |
| `ContextSession` | Session management |
| `ContextSerializer` | Serialization/deserialization |
| `ContextRestorer` | State restoration from snapshots |
| `ContextHistory` | Event history and auditing |
| `ContextSelection` | Object selection management |
| `ContextNavigation` | Navigation state management |
| `ContextFilter` | Filter application and management |
| `ContextFocus` | Focus management |
| `ContextComparison` | Context comparison operations |
| `ContextWorkspace` | Workspace management |
| `ContextValidator` | Validation utilities |

## Public API

```typescript
import ContextRuntime from '@clari-fin/context-runtime';

// Core operations
ContextRuntime.create(name, type, owner, workspace)
ContextRuntime.destroy(contextId)
ContextRuntime.activate(contextId)
ContextRuntime.snapshot(contextId)
ContextRuntime.restore(snapshotId)

// State accessors
ContextRuntime.history(contextId)
ContextRuntime.workspace(workspaceId)
ContextRuntime.selection(contextId)
ContextRuntime.focus(contextId)
ContextRuntime.navigation(contextId)
ContextRuntime.filters(contextId)
ContextRuntime.compare(contextId)

// Serialization
ContextRuntime.serialize(contextId)
ContextRuntime.deserialize(serializedContext)
ContextRuntime.validate(context)
```

## Supported Context Types

- `Dashboard`
- `Account`
- `Transaction`
- `Loan`
- `Investment`
- `Goal`
- `Budget`
- `CashFlow`
- `NetWorth`
- `Forecast`
- `Investigation`
- `Comparison`
- `Simulation`
- `Search`
- `Command`
- `Workspace`

## Architecture Diagram

```
Applications
    │
    ▼
Context Runtime
    │
┌───┴───────────┐
│               │
▼               ▼
History     Selection
│               │
▼               ▼
Snapshots    Navigation
│               │
▼               ▼
Filters     Comparison
    │               │
    └───────┬───────┘
            │
            ▼
    Future Time Runtime
```

## Testing

Run tests with:

```bash
npm test
```

## Building

```bash
npm run build
```

## Key Features

1. **Immutable State**: All updates create new snapshots
2. **Full History**: Every change is recorded as an event
3. **Workspace Isolation**: No shared state between workspaces
4. **Serialization**: Full state can be serialized to JSON
5. **Deterministic**: Same operations always produce same results
6. **Framework Independent**: Pure TypeScript with no UI dependencies