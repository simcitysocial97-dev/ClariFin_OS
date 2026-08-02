# Active Context

## Current Focus
Program 6.0 — Repository Architecture Convergence Audit (Final) — COMPLETE

## Recent Changes
- **Program 6.0 Audit (2026-08-02)**
  - Produced READ-ONLY audit at `docs/ARCHITECTURE_CONVERGENCE_AUDIT.md` (936 lines, 70 KB)
  - Section 1 (Repository Tree): Backend (27 dirs), Frontend (13 app pages + 30+ component dirs), runtime/, servers/, docs/, memory-bank/
  - Section 2 (Folder Responsibility Matrix): 30+ directories classified (canonical/partial/empty/deprecated)
  - Section 3 (Module Pipeline): PDF ingest pipeline mapped with 11 orphan candidates
  - Section 4 (Runtime Pipeline): 8 runtime pipelines (dashboard, behaviour, cashflow, forecast, loan, recon, graph, command)
  - Section 5 (Folder Placement): 25 files checked; 15 misplaced or orphaned
  - Section 6 (Duplicate Concept Matrix): 14 duplicate concepts (behavior/behaviour, account/accounts, db.py/core/db, etc.)
  - Section 7 (Layer Verification): 3 routers use src.models (P1); 3 standalone engines bypass repos with sqlite3; 2 routers unregistered
  - Section 8 (Engine Architecture): 22 engines catalogued (8 pure packages, 7 standalone, 1 .bak, 6 cross-dep)
  - Section 9 (Extraction Pipeline): extraction/ package disconnected; root-level files (statement_extractor, validator, etc.) misplaced
  - Section 10 (Database Pipeline): 35 tables, 24 idx, 2 triggers in core/db/schema; db.py + common/database.py deprecated
  - Section 11 (DTO Pipeline): 9 of 14 DTOs lack mappers; models/ (19 files) active-legacy vs core/domain/ (1 file)
  - Section 12 (API Contract): 115 endpoints, 26 registered routers, 110/115 untyped; 2 routers unregistered; dual type source (api.ts vs api-generated.ts)
  - Section 13 (Workspace): 7/8 workspaces dual-router; forecast/behaviour lack page.tsx
  - Section 14 (Intelligence): financial_intelligence unregistered; 4 orphan engines (recommendation, nudge, insight, goal_planner)
  - Section 15 (Connectivity): 20 modules mapped (reachability/duplicate/incomplete)
  - Section 16 (Compatibility): 11 bridges/shims classified
  - Section 17 (Feature Coverage): 24 features classified
  - Section 18 (Scorecard): Overall C (converging toward canonical core/)
  - Section 19 (Action Queue): P0=0, P1=6, P2=11, P3=3, P4=7, P5=0
  - Section 20 (Blueprint): Final ASCII architecture schematic

## Next Immediate Steps
- Address P1 items: register financial_intelligence.py + accounts_router.py, migrate routers from models→DTOs, route standalone engines through repositories
- Address P2 items: consolidate duplicate concepts (behavior/behaviour, account/accounts, db.py vs core/db)
- Address P3 items: remove get_db() export, complete behaviour_engine migration
- Address P4 items: populate or remove empty core/{models,repositories,services}, clean extraction/ fragmentation

</parameter>
<task_progress>
- [x] Phase A: Full discovery complete (backend, frontend, runtime, servers, tests, docs)
- [x] Phase B: Compile ARCHITECTURE_CONVERGENCE_AUDIT.md with all 20 sections
- [x] Phase C: Validate output file (70K, 936 lines, git untracked new file)
</task_progress>
</write_to_file>