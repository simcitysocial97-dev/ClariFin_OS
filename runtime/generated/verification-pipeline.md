# Execution Pipeline Diagram

```
collect_changed_files()
        │
        ▼
┌─────────────────────────┐
│  Git diff --name-only   │
│  HEAD                   │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  CrossLayerImpactPlanner│◄── Program 7A (single source of truth)
│  .analyze()             │    for dependency analysis
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  VerificationPlanner    │◄── Reused from Program 5/7A,
│  .plan()                │    NOT duplicated
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  VerificationOrchestrator│
│  .execute()             │
│  ├─ Executor.execute()  │
│  ├─ Python commands     │
│  ├─ npm commands        │
│  ├─ pytest              │
│  ├─ vitest              │
│  ├─ playwright          │
│  └─ schemathesis        │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  EvidenceAggregator     │◄── Program 7A evidence aggregation
│  .aggregate()           │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  VerificationReport     │
│  .to_markdown()         │
│  .save_markdown()       │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  runtime/generated/     │
│  verification-report.md │
│  verification-cache.json│
└─────────────────────────┘
```

## Data Flow

1. **Input**: Changed files (from git diff)
2. **Dependency Analysis**: CrossLayerImpactPlanner (Program 7A)
3. **Planning**: VerificationPlanner (reused, not duplicated)
4. **Execution**: Executor runs commands, returns ExecutionResult
5. **Evidence**: EvidenceAggregator collects artifacts
6. **Output**: VerificationReport (markdown + cache)

## Key Design Decisions

- The orchestrator NEVER performs dependency analysis itself
- Dependency analysis comes exclusively from CrossLayerImpactPlanner (Program 7A)
- VerificationPlanner is reused, not duplicated
- All execution results use typed dataclasses (ExecutionResult), not raw dictionaries
- Profiles are immutable (frozen dataclasses)
- The runtime is the source of truth for CI verification steps
