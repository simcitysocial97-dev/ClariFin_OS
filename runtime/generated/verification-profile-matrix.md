# Verification Profile Matrix

| Profile | Scope | Tasks | Commands | Key Tools |
|---------|-------|-------|----------|-----------|
| quick | quick | 3 | 3 | ruff, mypy, pytest |
| backend | backend | 6 | 6 | ruff, mypy, pytest, schemathesis |
| frontend | frontend | 5 | 5 | eslint, tsc, vitest, npm |
| contracts | contracts | 3 | 3 | schemathesis, pytest |
| graph | repository | 3 | 3 | graph_service, cross-layer map |
| full | full | 11 | 11 | All tools combined |

## Profile Details

### VERIFY_QUICK
- Ruff lint check
- MyPy type check
- Quick unit tests

### VERIFY_BACKEND
- Ruff lint check
- MyPy type check
- Backend unit tests
- Backend integration tests
- Schemathesis contract tests
- Aggregate evidence

### VERIFY_FRONTEND
- Frontend lint check
- Frontend type check
- Frontend unit tests
- Frontend build
- Aggregate evidence

### VERIFY_CONTRACTS
- Schemathesis contract validation
- Backend unit tests for contracts
- Aggregate contract evidence

### VERIFY_GRAPH
- Graph integrity check
- Cross-layer map validation
- Aggregate graph evidence

### VERIFY_FULL
- All backend tasks (ruff, mypy, unit, integration, schemathesis)
- All frontend tasks (lint, typecheck, unit, build)
- Graph integrity check
- Aggregate evidence

## Immutability Guarantee

All profiles are defined as frozen dataclasses (`frozen=True, slots=True`).
No profile may be modified at runtime.
No profile may contain duplicated commands.
