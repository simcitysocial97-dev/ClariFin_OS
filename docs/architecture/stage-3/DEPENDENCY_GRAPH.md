# Stage 3 — Dependency Graph

## Execution Order

The following dependency graph defines the execution order for Stage 3. Each layer must be completed before the next layer can begin.

```
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
│  (API endpoints, services, and data models)                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTION VIEWMODEL                        │
│  S3-TVM-001 through S3-TVM-020                               │
│  - Type definitions                                             │
│  - Field documentation                                          │
│  - Validation                                                   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       MAPPER LAYER                              │
│  S3-MAP-001 through S3-MAP-020                                 │
│  - DTO to ViewModel mapping                                     │
│  - Formatting utilities                                         │
│  - Error handling                                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    CAPABILITY LAYER                             │
│  S3-CAP-001 through S3-CAP-020                                 │
│  - React context and hooks                                      │
│  - State management                                             │
│  - React Query integration                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FILTERING ENGINE                            │
│  S3-FIL-001 through S3-FIL-020                                 │
│  - Filter types                                                 │
│  - Filter components                                             │
│  - Filter state management                                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SEARCH ENGINE                              │
│  S3-SEA-001 through S3-SEA-020                                 │
│  - Search input component                                         │
│  - Search state and actions                                       │
│  - Backend search endpoint                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        GROUPING                                 │
│  S3-GRP-001 through S3-GRP-020                                 │
│  - Group types                                                    │
│  - Group actions                                                  │
│  - Group UI components                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         SORTING                                 │
│  S3-SRT-001 through S3-SRT-020                                 │
│  - Sort types                                                   │
│  - Sort actions                                                 │
│  - Sort UI components                                             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SELECTION MODEL                             │
│  S3-SEL-001 through S3-SEL-020                                 │
│  - Selection types                                                │
│  - Selection actions                                              │
│  - Selection UI components                                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      EVIDENCE SYSTEM                            │
│  S3-EVD-001 through S3-EVD-020                                 │
│  - Evidence types                                                 │
│  - Evidence drawer                                                │
│  - Evidence for all sources                                       │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     WORKSPACE LAYOUT                            │
│  S3-WS-001 through S3-WS-020                                   │
│  - Page composition                                             │
│  - Region integration                                           │
│  - State management                                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TOOLBAR                                 │
│  S3-TBR-001 through S3-TBR-020                                 │
│  - Toolbar component                                              │
│  - Action buttons                                                 │
│  - State indicators                                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    TRANSACTION TABLE                            │
│  S3-TBL-001 through S3-TBL-020                                 │
│  - Table component                                                │
│  - Row and cell components                                        │
│  - Pagination and virtualization                                  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       NAVIGATION                                │
│  S3-NAV-001 through S3-NAV-020                                 │
│  - Cross-navigation links                                         │
│  - Breadcrumb and back button                                     │
│  - State persistence                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LOADING/ERROR STATES                         │
│  S3-LOD-001 through S3-LOD-020                                 │
│  - Loading spinner                                                │
│  - Error message                                                  │
│  - Empty state                                                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         TESTING                                 │
│  S3-TST-001 through S3-TST-020                                 │
│  - Contract tests                                                 │
│  - Explainability tests                                           │
│  - User behavior tests                                            │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                        VALIDATION                                 │
│  S3-VAL-001 through S3-VAL-020                                 │
│  - TypeScript check                                               │
│  - ESLint check                                                   │
│  - Architecture validation                                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       PERFORMANCE                                 │
│  S3-PER-001 through S3-PER-020                                 │
│  - Performance optimization                                       │
│  - Performance tests                                              │
│  - Monitoring                                                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOCUMENTATION                              │
│  S3-DOC-001 through S3-DOC-020                                 │
│  - All documentation files                                        │
│  - User guides                                                    │
│  - API documentation                                              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    BENCHMARK COMPLETION                           │
│  All benchmarks from STAGE_3_BENCHMARK.md must pass             │
└─────────────────────────────────────────────────────────────────┘
```

## Parallel Execution Opportunities

The following TODOs can be executed in parallel within their capability groups:

### Transaction ViewModel
- S3-TVM-002 through S3-TVM-016 can be done in parallel after S3-TVM-001

### Mapper Layer
- S3-MAP-004 through S3-MAP-012 can be done in parallel after S3-MAP-002

### Filtering Engine
- S3-FIL-002 through S3-FIL-006 can be done in parallel after S3-FIL-001

### Search Engine
- S3-SEA-002 through S3-SEA-009 can be done in parallel after S3-SEA-001
- S3-SEA-010 through S3-SEA-020 can be done in parallel

### Grouping
- S3-GRP-002 through S3-GRP-005 can be done in parallel after S3-GRP-001
- S3-GRP-008 through S3-GRP-013 can be done in parallel

### Sorting
- S3-SRT-004 through S3-SRT-008 can be done in parallel after S3-SRT-003
- S3-SRT-009 through S3-SRT-020 can be done in parallel

### Selection Model
- S3-SEL-003 through S3-SEL-006 can be done in parallel after S3-SEL-002
- S3-SEL-007 through S3-SEL-013 can be done in parallel

### Evidence System
- S3-EVD-003 through S3-EVD-008 can be done in parallel after S3-EVD-002
- S3-EVD-010 through S3-EVD-014 can be done in parallel

### Loading/Error States
- S3-LOD-001 through S3-LOD-004 can be done in parallel
- S3-LOD-005 through S3-LOD-009 can be done in parallel

## Critical Path

The critical path (longest dependency chain) is:

S3-TVM-001 → S3-MAP-001 → S3-CAP-001 → S3-WS-001 → S3-TST-001 → S3-VAL-001 → S3-PER-001 → S3-DOC-001

This path determines the minimum time to complete the stage.

## Next Executable TODOs

After all documentation is created, the first executable TODOs are:

1. S3-TVM-001: Create TransactionViewModel type definition
2. S3-LOD-001: Create loading spinner component (no dependencies)
3. S3-LOD-002: Create skeleton row component (no dependencies)
4. S3-LOD-003: Create error message component (no dependencies)
5. S3-LOD-004: Create empty state component (no dependencies)