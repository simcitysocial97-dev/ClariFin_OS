# Engineering Knowledge Base (Program 11)

## Purpose

The Engineering Knowledge Base (EKB) is a deterministic, read-only system that indexes, correlates, and exposes engineering knowledge already produced by the runtime.

It **never** generates new engineering facts, performs AI reasoning, or duplicates runtime calculations.

## Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Knowledge Base                      │
│                                                          │
│  ┌────────────┐  ┌─────────────┐  ┌─────────┐            │
│  │  Catalog   │  │  Indexer    │  │  Query  │            │
│  │            │  │             │  │  Engine │            │
│  └────────────┘  └─────────────┘  └─────────┘            │
│       │               │                │                 │
│       └───────────────┴────────────────┘                 │
│                    │                                     │
│           ┌────────▼────────┐                            │
│           │  References     │                            │
│           │  Engine         │                            │
│           └────────────────┘                            │
│                    │                                     │
│           ┌────────▼────────┐                            │
│           │  Formatter      │                            │
│           │  (Terminal)     │                            │
│           └────────────────┘                            │
└────────────────────────────────────────────────────────┘
```

## Components

### Catalog (`catalog.py`)

Immutable catalog entries for all engineering entity types:

- **Endpoints** - API endpoint paths and methods
- **Capabilities** - Frontend capabilities
- **Mappers** - Data transformation layers
- **ViewModels** - UI state containers
- **Workspaces** - Feature modules
- **Components** - UI components
- **Graph Renderers** - Visualization layers
- **Verification Profiles** - Test verification configurations
- **Integrity Rules** - Constitutional rules
- **Runtime Artifacts** - Generated files
- **Documentation** - Engineering documents

### Indexer (`indexer.py`)

Builds deterministic indexes from runtime artifacts:

- `runtime/generated/cross-layer-map.json` - Endpoint/Capability/Component relationships
- `runtime/generated/dashboard.json` - Verification metrics
- `runtime/generated/engineering-history.json` - Run history
- `runtime/generated/engineering-health.md` - Health status
- `runtime/generated/engineering-analytics.json` - Performance analytics
- `runtime/generated/verification-report.md` - Verification results
- `runtime/generated/dependency-growth.json` - Dependency metrics
- `runtime/generated/flaky-tests.json` - Test stability data
- `runtime/generated/cost-analysis.json` - Execution costs
- Constitutional rules registry
- Verification profiles registry
- Documentation under `docs/`

Output: `runtime/generated/knowledge-index.json`

### Query Engine (`query.py`)

Deterministic lookups supporting:

- `python runtime/verify.py knowledge endpoint /api/v1/loans`
- `python runtime/verify.py knowledge capability useLoansCapability`
- `python runtime/verify.py knowledge workspace loans`
- `python runtime/verify.py knowledge rule ARCH-002`
- `python runtime/verify.py knowledge component AmortizationTable`

### Reference Engine (`references.py`)

Resolves relationships following the chain:

```
Endpoint → Capability → Mapper → ViewModel → Workspace → Component → Tests
   → Verification Profile → Integrity Rules → Documentation
```

### Formatter (`formatter.py`)

Professional terminal rendering with:

- Adaptive Unicode/ASCII support
- Readable hierarchy
- No JSON dumps

## Query Model

Each query returns:

| Field | Description |
|-------|-------------|
| Ownership | Layer and owner attribution |
| Dependencies | Related entities |
| Verification Profile | Applicable profile |
| Integrity Rules | Relevant rules |
| Documentation References | Linked docs |
| Related Runtime Artifacts | Source artifacts |

## Relationship with Programs 7–10

| Program | Contribution | Knowledge Base Consumption |
|---------|-------------|---------------------------|
| Program 7A | Cross-layer dependency intelligence | `cross-layer-map.json` |
| Program 7B | Verification orchestration | `verification-cache.json`, `verification-report.md` |
| Program 8 | Diagnostics, repair, risk analysis | `engineering-history.json`, `engineering-health.md`, `engineering-analytics.json` |
| Program 9 | Engineering Workspace | All generated artifacts |
| Program 10 | Architectural Integrity Engine | `integrity` package, constitutional rules |

## Acceptance Criteria

✓ No backend modifications  
✓ No frontend modifications  
✓ No runtime planner modifications  
✓ No observability modifications  
✓ No integrity modifications  
✓ No workspace modifications  
✓ Uses only existing runtime artifacts  
✓ Read-only architecture  
✓ Immutable models  
✓ Deterministic indexing  
✓ Terminal-first interface  

## CLI Usage

```bash
# Display knowledge index summary
python runtime/verify.py knowledge

# Query by endpoint path
python runtime/verify.py knowledge endpoint /api/v1/loans

# Query by capability name
python runtime/verify.py knowledge capability useLoansCapability

# Query by workspace name
python runtime/verify.py knowledge workspace loans

# Query by integrity rule ID
python runtime/verify.py knowledge rule ARCH-002

# Query by component name
python runtime/verify.py knowledge component AmortizationTable
```

## Design Principles

1. **Read-only**: Never modifies any artifacts
2. **Deterministic**: Same input always produces same output
3. **Immutable**: All dataclasses use `frozen=True, slots=True`
4. **Index-only**: Only references, no duplicated metadata
5. **Terminal-first**: Optimized for CLI interaction