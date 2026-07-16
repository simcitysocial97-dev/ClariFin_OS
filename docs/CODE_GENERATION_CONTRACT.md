# Code Generation Contract — ClariFin_OS

> **Mandatory Execution Rules for AI Agents**  
> Every code modification MUST follow this contract.

---

## 1. Pre-flight Checklist

Before modifying ANY source code:

- [ ] Read `docs/ARCHITECTURE_CONSTRAINTS.md` (immutable rulebook)
- [ ] Run CGC `find_code("SymbolName")` for schema discovery
- [ ] Analyze call chain with `analyze_code_relationships` if needed
- [ ] Read memory bank: `projectbrief.md`, `activeContext.md`
- [ ] Check existing implementation patterns in target layer
- [ ] Verify no TypeScript escape hatches in modified files
- [ ] Verify no FinanceDB imports outside repositories/
- [ ] Verify no float usage in currency paths

---

## 2. Required Project Reading Order

```
CGC (find_code)
  ↓
Memory Bank (projectbrief.md, activeContext.md)
  ↓
Existing implementation (target layer files)
  ↓
vgrep/rg for patterns (token-efficient discovery)
  ↓
File reads (only if CGC insufficient)
```

**Rationale**: CGC returns complete source with `INDEX_SOURCE=true`. Use `rg` for quick pattern extraction before full file reads.

---

## 3. Reuse Requirements

### Existing Patterns
- Match existing code style (PEP 8, type hints, naming conventions)
- Reuse `BaseRepository` for all database operations
- Extend existing engine patterns (pure functions, dict inputs)
- Follow component layer responsibilities strictly

### No Reinvention
- NEVER create new validation functions — use invariants in `tests/domain/invariants/`
- NEVER add new state management — use Zustand/React Query patterns
- NEVER create new error types — use `AppError` tree in `errors.py`
- NEVER modify database schema — use `ADD COLUMN IF NOT EXISTS`

---

## 4. Stop Conditions

STOP immediately if:

| Condition | Action |
|-----------|--------|
| `as any` found in TypeScript | Fix type error properly |
| FinanceDB import outside repositories/ | Refactor boundary violation |
| Float used for currency | Use integer paise |
| Engine calls sqlite3 directly | Move to repository |
| Router contains business logic | Move to service |
| Test coverage drops below threshold | Add missing tests |
| Validation fails (ruff/mypy/type-check) | Must fix before commit |

---

## 5. Forbidden Behaviors

### Absolute Prohibitions
- ❌ Never use `as any`, `@ts-ignore`, `@ts-nocheck` in TypeScript
- ❌ Never drop database tables or columns
- ❌ Never use `float` for currency values
- ❌ Never use `sqlite3` to query FalkorDB
- ❌ Never call `DELETE FROM table` in migrations
- ❌ Never add tables without ARCHITECTURE.md update

### Layer Violations
- ❌ Routers MUST NOT import `FinanceDB`
- ❌ Engines MUST NOT import `FinanceDB`
- ❌ Engines MUST NOT call `sqlite3.connect()`
- ❌ Models MUST NOT contain computation logic
- ❌ Services MUST NOT access DB directly

---

## 6. Required Outputs

After ANY file modification:

### Verification
```bash
# Frontend (from frontend/)
npm run type-check && npm run lint && npm test -- --run && npm run build

# Backend (from backend/)
./venv/bin/python3 -m ruff check . && ./venv/bin/python3 -m mypy .
```

### Commit Protocol
1. `git add -A`
2. `git commit -m "[type]: [description]"` (semantic style)
3. `git push origin [current-branch]`

---

## 7. Change Summary Template

Every commit MUST include a summary following this pattern:

```markdown
## Changes Made

- [Layer]: Brief description of change
- [Layer]: Modified file path for specific purpose
- [Layer]: Added/deleted/replaced logic

## Verification

- Frontend: type-check ✓/✗, lint ✓/✗, tests ✓/✗, build ✓/✗
- Backend: ruff ✓/✗, mypy ✓/✗

## Constraints Checked

- Financial Truth: [paise integers, bps range]
- Data Flow: [pure engine, repository boundary]
- Type System: [no any, correct types]

## No Source Code Modified

Only documentation updated in this change.
```

---

## 8. Human Verification Checklist

Before sign-off:

- [ ] All monetary values use integer paise
- [ ] All confidence values in 0-10000 bps range
- [ ] Repository boundary rule not violated
- [ ] No TypeScript escape hatches introduced
- [ ] Tests pass (unit + integration)
- [ ] Frontend builds successfully
- [ ] No regression in existing functionality
- [ ] ARCHITECTURE.md updated if layer changed

---

## 9. Execution Phases

### Phase A: Schema Discovery
Use CGC `find_code("SymbolName")` to locate and retrieve schemas. The `source` field contains COMPLETE type definitions.

### Phase B: Delta-Only Generation
Execute code modifications matching Phase A schemas. Enforce financial guardrails.

### Phase C: Autonomous Verification Gate
Run validation suites. Self-correct errors iteratively until clean.

---

## 10. Token Efficiency Rules

- Use `rg "class ClassName" --type py` before reading files
- Count lines with `wc -l` before reading
- Use CGC with targeted queries (avoid broad patterns)
- Index code chunks via ctx_index for large outputs
- Never read files >200 lines without targeted extraction

---

*Version: 1.0 (Stage 0)*  
*This contract supersedes any conflicting instructions.*