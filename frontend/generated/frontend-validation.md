# Frontend Validation Framework (FVF)

## Overview

The FVF is a lightweight, deterministic validation system for the ClariFin frontend. It prevents AI-generated TypeScript, React, Next.js, and architecture errors by running 8 independent audit stages.

## Validation Flow

```
npm run fvf
│
└─ npx tsx tools/validate.ts
   │
   ├─ [1] Toolchain Lock          ~1s  — package.json, tsconfig, versions
   ├─ [2] Architecture Audit      ~2s  — Server/Client Component boundaries
   ├─ [3] Type & React Audit      ~2s  — Type chain + React 19 compat
   ├─ [4] Generated API Audit     ~1s  — Backend contract integration
   ├─ [5] React Query Audit       ~2s  — Query keys, mutations, cache
   ├─ [6] Import Graph Audit      ~3s  — Cycles, depth, layer violations
   ├─ [7] Build Validation        ~5-20s — tsc → eslint → next build
   │
   └─ Output: validation-report.md + validation-manifest.json
              Total: ~<30s (--fast: ~10s)
```

## Stage Responsibilities

| Stage | What it checks | Exit on fail? |
|-------|---------------|---------------|
| Toolchain Lock | Package versions, floating ranges, deprecated deps, tsconfig strict | No (warning) |
| Architecture Audit | Server Components using hooks, Client Components using server APIs, unnecessary 'use client' | Yes |
| Type & React Audit | Direct DTO imports in components, `any` return types, React 19 deprecated patterns | Yes |
| Generated API Audit | Generated types exist, hooks use generated types, components don't import DTOs directly | Yes |
| React Query Audit | Duplicate query keys, missing invalidations, staleTime > gcTime, query in event handlers | Yes |
| Import Graph Audit | Circular dependencies, deep chains (>5), layer violations | Yes |
| Build Validation | tsc --noEmit, eslint, next build (each independent) | Yes |

## Commands

```bash
# Full validation (all 7 stages)
npm run fvf

# Fast validation (toolchain + build only)
npm run fvf:fast

# Individual stages
npx tsx tools/validate.ts --architecture
npx tsx tools/validate.ts --types
npx tsx tools/validate.ts --api
npx tsx tools/validate.ts --query
npx tsx tools/validate.ts --imports
npx tsx tools/validate.ts --build
```

## Output Files

All generated under `frontend/generated/`:

| File | Description |
|------|-------------|
| `toolchain-lock.json` | Snapshot of all tool versions and detected issues |
| `validation-report.md` | Human-readable report with all findings |
| `validation-manifest.json` | Machine-readable manifest (like backend) |
| `validation-history.json` | Last 100 runs (for error loop detection) |
| `build-report.json` | Build step results with timings |

## AI Error Loop Detection

The FVF automatically detects when the same stage fails for 3+ consecutive runs. When detected, it prints:

```
⚠️  AI ERROR LOOP DETECTED
  Repeated: Architecture Audit, Type & React Audit
  Suggestion: Consider reverting recent changes instead of continuing incremental fixes.
```

This prevents AI agents from spending hours making superficial edits while the underlying architectural issue remains.

## Change Intelligence

The orchestrator automatically selects relevant stages based on which files changed:

| Changed files | Stages run |
|---------------|------------|
| `components/*` | Architecture + Types + API + Build |
| `lib/hooks/*` | Types + API + Query + Build |
| `types/*` | API + Types + Build |
| `app/*` | Architecture + Types + Build |
| Config files | Toolchain + Build |
| Other | Build only |

## Troubleshooting

### "Generated types not found"
Run `npm run gen:types` while the backend is running.

### "TypeScript compilation failed"
Run `npx tsc --noEmit` locally to see detailed errors.

### "ESLint failed"
Run `npm run lint` locally to see detailed errors.

### "Build failed"
Check the build output in `generated/build-report.json` for specific error messages.

## Developer Workflow

1. Make changes to frontend code
2. Run `npm run fvf:fast` for quick feedback
3. If fast passes, run `npm run fvf` for full validation
4. Fix any errors reported
5. If the same error persists for 3+ runs, consider reverting and taking a different approach

## CI Integration

```yaml
# .github/workflows/frontend-validate.yml
name: Frontend Validation
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm ci
      - run: npm run fvf
```

## Architecture

```
frontend/
├── tools/
│   ├── types.ts                    # Shared types
│   ├── utils.ts                    # Shared utilities
│   ├── validate.ts                 # Orchestrator (entry point)
│   ├── lock_toolchain.ts           # Phase 1
│   ├── architecture_audit.ts       # Phase 2
│   ├── type_react_audit.ts         # Phase 3
│   ├── generated_api_audit.ts      # Phase 4
│   ├── query_audit.ts              # Phase 5
│   ├── import_audit.ts             # Phase 6
│   ├── build_audit.ts              # Phase 7
│   └── __tests__/
│       └── fvf.test.ts             # Meta tests
└── generated/
    ├── toolchain-lock.json
    ├── validation-report.md
    ├── validation-manifest.json
    ├── validation-history.json
    ├── build-report.json
    └── frontend-validation.md      # This file