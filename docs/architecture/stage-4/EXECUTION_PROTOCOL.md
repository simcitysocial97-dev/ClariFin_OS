# Stage 4 — Execution Protocol

## Purpose
This document defines the deterministic execution protocol for Stage 4. Future execution must be able to continue from these documents alone without scanning the entire repository.

---

## 1. Reading Order

When beginning a Stage 4 execution session, read these files in order:

1. `docs/stage-4/STAGE_4_SCOPE.md` — Understand what is in/out of scope
2. `docs/stage-4/STAGE_4_SPECIFICATION.md` — Understand the workspace specification
3. `docs/stage-4/STAGE_4_ARCHITECTURE.md` — Understand the architecture constraints
4. `docs/stage-4/STAGE_4_BENCHMARK.md` — Understand the completion criteria
5. `docs/stage-4/DEPENDENCY_GRAPH.md` — Understand execution levels and parallelism
6. `docs/stage-4/WORKSPACE_PROGRESS.md` — Understand current state
7. `docs/stage-4/EXECUTION_PROTOCOL.md` — Understand this protocol
8. `docs/stage-4/todo/{WORKSPACE_ID}.md` — Read the specific workspace TODO document

**Do NOT read** any Stage 3 documentation unless explicitly referenced by a TODO. Stage 3 is complete and its patterns are already encoded in the Stage 4 TODO documents.

---

## 2. Validation Policy

### 2.1 Per-Capability Validation
Every capability must pass these checks before being marked DONE:

1. **TypeScript Check**: `cd frontend && npx tsc --noEmit` — zero errors
2. **Lint Check**: `cd frontend && npx eslint .` — zero errors
3. **Backend Ruff**: `cd backend && ./venv/bin/python3 -m ruff check .` — zero errors
4. **Backend Mypy**: `cd backend && ./venv/bin/python3 -m mypy .` — zero errors
5. **Unit Tests**: All capability-specific tests pass
6. **Architecture Check**: No DTO in components, no calculations in components, no business logic in pages
7. **Financial Values**: All monetary values use paise (integer), no loose floats

### 2.2 Per-Workspace Validation (Cap 21 — Benchmark)
Before marking a workspace DONE, run the full benchmark checklist from the workspace TODO document (Cap 21). Every item must pass.

### 2.3 Validation Order
- Run validation **immediately** after each capability is implemented
- Do NOT batch validations — fix issues while context is fresh
- If validation fails, fix and re-validate before moving to next capability

---

## 3. Batch Size

### 3.1 Maximum Batch Size
- **Level 0-5**: Execute all 9 capabilities in parallel (one per workspace)
- **Level 6**: Execute all 37 capabilities in parallel
- **Level 7**: Execute all 45 capabilities in parallel
- **Level 8**: Execute all 27 capabilities in parallel
- **Level 9**: Execute all 9 capabilities in parallel
- **Level 10**: Execute 1 capability per workspace (9 total, parallel across workspaces)
- **Level 11**: Execute 1 capability per workspace (9 total, parallel across workspaces)

### 3.2 Recommended Batch Size (Context Management)
Given context window constraints, the recommended batch size per session is:

| Level | Recommended Batch | Rationale |
|-------|------------------|-----------|
| L0 | 3 DTOs per session | Small files, low complexity |
| L1 | 3 ViewModels per session | Type definitions, moderate complexity |
| L2 | 3 Mappers per session | Moderate complexity |
| L3 | 2 Services per session | High complexity, business logic |
| L4 | 3 Routers per session | Moderate complexity |
| L5 | 2 Capability Hooks per session | High complexity, state management |
| L6 | 4 Components per session | Low complexity per component |
| L7 | 4 Components per session | Low complexity per component |
| L8 | 6 Components per session | Very low complexity |
| L9 | 3 Navigation files per session | Low complexity |
| L10 | 1 Workspace Page per session | High complexity, composition |
| L11 | 1 Benchmark per session | Verification only |

### 3.3 Session Limit
- Maximum 10 tool calls per capability before escalating
- If a capability requires more than 10 tool calls, stop and assess:
  1. Is the scope too large? Split into sub-capabilities.
  2. Is there an unexpected dependency? Update DEPENDENCY_GRAPH.md.
  3. Is the specification unclear? Update the TODO document.

---

## 4. Context Management

### 4.1 Session Boundaries
Each execution session must:
1. Start by reading the 8 files listed in Section 1 (Reading Order)
2. End by updating `docs/stage-4/WORKSPACE_PROGRESS.md` with current status
3. End by updating `memory-bank/activeContext.md` with 2-3 bullet summary

### 4.2 Context Preservation
To avoid losing context between sessions:
- **WORKSPACE_PROGRESS.md** is the single source of truth for status
- **DEPENDENCY_GRAPH.md** is the single source of truth for dependencies
- **TODO documents** are the single source of truth for capability details
- Do NOT rely on memory or conversation history for status

### 4.3 Context Recovery
If resuming after a break:
1. Read WORKSPACE_PROGRESS.md to find the last completed capability
2. Read the relevant TODO document for the next capability
3. Read the DEPENDENCY_GRAPH.md to confirm dependencies are met
4. Begin execution

---

## 5. Documentation Update Policy

### 5.1 When to Update
Update documentation in these cases:

| Event | Document to Update | Timing |
|-------|-------------------|--------|
| Capability started | WORKSPACE_PROGRESS.md | Immediately |
| Capability completed | WORKSPACE_PROGRESS.md | Immediately |
| Capability blocked | WORKSPACE_PROGRESS.md | Immediately |
| New dependency discovered | DEPENDENCY_GRAPH.md | Immediately |
| Scope change | STAGE_4_SCOPE.md | Before implementation |
| Architecture change | STAGE_4_ARCHITECTURE.md | Before implementation |
| Session end | WORKSPACE_PROGRESS.md, memory-bank/activeContext.md | End of session |

### 5.2 What to Update
- **WORKSPACE_PROGRESS.md**: Change status field, add notes
- **DEPENDENCY_GRAPH.md**: Add/remove dependencies, update levels
- **TODO documents**: Mark TODOs as complete, add new TODOs if scope expands
- **memory-bank/activeContext.md**: 2-3 bullet summary of changes + next steps

### 5.3 What NOT to Update
- Do NOT update STAGE_4_SPECIFICATION.md — it is the authoritative spec
- Do NOT update STAGE_4_BENCHMARK.md — it is the completion criteria
- Do NOT update Stage 3 documentation — it is frozen

---

## 6. Stop Conditions

### 6.1 Normal Stop
Stage 4 is complete when:
- All 189 capabilities across all 9 workspaces are marked DONE
- All 9 workspaces pass their benchmark validation (Cap 21)
- WORKSPACE_PROGRESS.md shows 189/189 DONE
- No BLOCKED capabilities remain

### 6.2 Emergency Stop
Stop immediately and escalate if:
1. **Architecture violation**: A component imports a DTO directly
2. **Financial violation**: A monetary value uses float instead of paise
3. **Data loss**: Any operation could delete or corrupt financial data
4. **Infinite loop**: Same capability fails validation 3+ times
5. **Context exhaustion**: Context window exceeds 80% capacity

### 6.3 Pause Conditions
Pause execution and update documentation if:
1. **Missing dependency**: A capability's dependency is not yet implemented
2. **Scope ambiguity**: A TODO is unclear or incomplete
3. **Test failure**: Existing tests break due to changes
4. **Performance regression**: Operations exceed performance budgets

---

## 7. Recovery Procedure

### 7.1 Failed Capability Recovery
If a capability fails validation:
1. Read the error output completely
2. Identify the root cause (type error, logic error, architecture violation)
3. Fix the issue
4. Re-run validation
5. If validation fails again, check if the TODO needs clarification
6. If validation fails 3 times, escalate (stop condition)

### 7.2 Blocked Capability Recovery
If a capability is blocked:
1. Identify the blocking dependency from DEPENDENCY_GRAPH.md
2. Check if the dependency is marked DONE in WORKSPACE_PROGRESS.md
3. If the dependency is DONE but the capability is still blocked, update DEPENDENCY_GRAPH.md
4. If the dependency is NOT DONE, implement the dependency first
5. Update WORKSPACE_PROGRESS.md with BLOCKED status and reason

### 7.3 Context Loss Recovery
If context is lost (session timeout, crash, etc.):
1. Read WORKSPACE_PROGRESS.md to find the last completed capability
2. Read the TODO document for the in-progress capability
3. Re-read the capability's required files
4. Continue from the last uncompleted TODO item
5. Do NOT re-implement completed work

### 7.4 Rollback Procedure
If a capability needs to be rolled back:
1. Follow the Rollback Strategy specified in the capability's TODO
2. Update WORKSPACE_PROGRESS.md to NOT_STARTED
3. Remove any created files
4. Revert any modified files
5. Run validation to confirm clean state

---

## 8. Continuation Protocol

### 8.1 Session Start
Each session must begin with:
```
1. Read WORKSPACE_PROGRESS.md → identify next capability
2. Read DEPENDENCY_GRAPH.md → confirm dependencies met
3. Read relevant TODO document → understand capability details
4. Read required files listed in TODO → understand existing code
5. Begin implementation
```

### 8.2 Session End
Each session must end with:
```
1. Update WORKSPACE_PROGRESS.md with current status
2. Update memory-bank/activeContext.md with 2-3 bullet summary
3. Commit changes with semantic commit message
4. Push to remote
```

### 8.3 Handoff Protocol
When handing off to another executor:
1. Ensure WORKSPACE_PROGRESS.md is up to date
2. Ensure memory-bank/activeContext.md has clear next steps
3. Leave a clear note on what was completed and what's next
4. The receiving executor follows the Reading Order in Section 1

### 8.4 Parallel Execution
When executing capabilities in parallel:
1. Each capability is independent (confirmed by DEPENDENCY_GRAPH.md)
2. Use separate sessions/contexts for each capability
3. Do NOT share state between parallel capabilities
4. Update WORKSPACE_PROGRESS.md after each capability completes
5. Wait for all capabilities in a level to complete before advancing to next level

---

## 9. Execution Order (Recommended)

Follow this exact order for maximum parallelism:

### Phase 1: Foundation (Levels 0-1)
```
Batch 1: L0-01 through L0-09 (9 Backend DTOs — parallel)
Batch 2: L1-01 through L1-09 (9 ViewModels — parallel)
```

### Phase 2: Transformation (Levels 2-3)
```
Batch 3: L2-01 through L2-09 (9 Mappers — parallel)
Batch 4: L3-01 through L3-09 (9 Backend Services — parallel)
```

### Phase 3: API & State (Levels 4-5)
```
Batch 5: L4-01 through L4-09 (9 Backend Routers — parallel)
Batch 6: L5-01 through L5-09 (9 Capability Hooks — parallel)
```

### Phase 4: UI Components (Levels 6-7)
```
Batch 7: L6-01 through L6-37 (37 UI Components — parallel)
Batch 8: L7-01 through L7-45 (45 UI Infrastructure — parallel)
```

### Phase 5: UX & Navigation (Levels 8-9)
```
Batch 9: L8-01 through L8-27 (27 UX States — parallel)
Batch 10: L9-01 through L9-09 (9 Cross-Navigation — parallel)
```

### Phase 6: Composition (Levels 10-11)
```
Batch 11: L10-01 through L10-09 (9 Workspace Pages — parallel across workspaces)
Batch 12: L11-01 through L11-09 (9 Benchmark Validations — parallel across workspaces)
```

### Total: 12 batches minimum
### Maximum parallelism: 45 capabilities (Batch 8)

---

## 10. Quality Gates

### Gate 1: Per-Capability
- [ ] TypeScript compiles
- [ ] Backend ruff passes
- [ ] Backend mypy passes
- [ ] Unit tests pass
- [ ] No DTO in components
- [ ] No calculations in components
- [ ] No business logic in pages
- [ ] All monetary values in paise

### Gate 2: Per-Workspace
- [ ] All 21 capabilities pass Gate 1
- [ ] Workspace page renders all regions
- [ ] All states (loading, empty, error) work
- [ ] Search, filter, sort, group, pagination work
- [ ] Evidence drawer shows summary, evidence, calculation, source, confidence
- [ ] Keyboard navigation works
- [ ] Responsive layout works
- [ ] Dark mode works
- [ ] Accessibility (ARIA labels) works
- [ ] Benchmark checklist (Cap 21) passes

### Gate 3: Per-Stage
- [ ] All 9 workspaces pass Gate 2
- [ ] No cross-workspace violations
- [ ] No duplicated code across workspaces
- [ ] No TODO/FIXME comments in code
- [ ] Build passes
- [ ] All tests pass
- [ ] Dashboard implementation not started (out of scope)
- [ ] Money Graph not started (out of scope)

---

## 11. File Naming Convention

### Frontend
| Layer | Convention | Example |
|-------|-----------|---------|
| ViewModel | `frontend/types/{workspace}-view-model.ts` | `net-worth-view-model.ts` |
| Mapper | `frontend/lib/mappers/{workspace}-mapper.ts` | `net-worth-mapper.ts` |
| Capability Hook | `frontend/lib/capabilities/use-{workspace}-capability.ts` | `use-net-worth-capability.ts` |
| Capability Context | `frontend/lib/capabilities/{workspace}-context.tsx` | `net-worth-context.tsx` |
| Component | `frontend/components/{workspace}/{component-name}.tsx` | `net-worth-summary.tsx` |
| Navigation | `frontend/lib/navigation/{workspace}-navigation.ts` | `net-worth-navigation.ts` |
| Workspace Page | `frontend/app/{workspace}/page.tsx` | `frontend/app/net-worth/page.tsx` |

### Backend
| Layer | Convention | Example |
|-------|-----------|---------|
| DTO | `backend/src/core/dtos/{workspace}_dto.py` | `net_worth_dto.py` |
| Router | `backend/src/routers/{workspace}_router.py` | `net_worth_router.py` |
| Service | `backend/src/services/{workspace}_service.py` | `net_worth_service.py` |

### Documentation
| Type | Convention | Example |
|------|-----------|---------|
| TODO | `docs/stage-4/todo/{NN}_{WORKSPACE}.md` | `01_NET_WORTH.md` |
| Benchmark | `docs/stage-4/benchmarks/{workspace}-benchmark.md` | `net-worth-benchmark.md` |

---

## 12. Git Commit Convention

### Format
```
[workspace-id]: [action] [capability]

[optional body with details]
```

### Examples
```
net-worth: add ViewModel type with evidence chain support
cashflow: implement mapper with DTO to ViewModel transformation
loans: create backend service for amortization calculation
```

### Workspace IDs
| Workspace | ID |
|-----------|-----|
| Net Worth | `net-worth` |
| Cashflow | `cashflow` |
| Accounts | `accounts` |
| Loans | `loans` |
| Credit Cards | `credit-cards` |
| Investments | `investments` |
| Reconciliation | `reconciliation` |
| Behaviour | `behaviour` |
| Forecast | `forecast` |
| Cross-cutting | `stage-4` |

### Commit Frequency
- Commit after each capability completes and passes validation
- Do NOT batch multiple capabilities into one commit
- Exception: Level 6-8 UI components can be batched per workspace per level

---

## 13. Escalation Path

If any of these conditions are met, stop and escalate:

| Condition | Escalate To |
|-----------|-------------|
| Architecture violation | Update STAGE_4_ARCHITECTURE.md |
| Scope violation | Update STAGE_4_SCOPE.md |
| Missing dependency in graph | Update DEPENDENCY_GRAPH.md |
| Unclear TODO | Update the TODO document |
| Test framework issue | Check test configuration |
| Build system issue | Check build configuration |
| Performance regression | Check performance budget |

---

## 14. Protocol Version

- **Version**: 1.0
- **Date**: 2026-07-19
- **Author**: Cline (Autonomous Core Agent)
- **Status**: Active

This protocol is self-referential. Any changes to the execution process must be reflected in this document before implementation begins.