# Active Context

## Current Focus
Program 6.0 — Repository Architecture Convergence Audit (Complete)
Program C — Financial OS Shell Architecture (Complete)

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

- **Financial OS Shell Architecture Spec (2026-03-08)**
  - Created `docs/FINANCIAL_OS_SHELL_ARCHITECTURE.md` — permanent specification (12 parts, ~1700 lines)
  - Part 1: Shell regions (Global Header, Command HUD, Left Nav Rail, Workspace Host, Right Context Panel, Bottom Intelligence Shelf, Overlay Layer, Modal Layer) with ownership, runtime deps, lifecycle, resize, responsive rules
  - Parts 2-11: Workspace Host lifecycle, Context Runtime interface, Intelligence tiers (Passive/Investigative/Executive), Graph Runtime (investigative-only), Command Runtime, Renderer Architecture (7 modes), Design System, Runtime Event Bus (25+ events), Future Runtime Roadmap (6 runtimes), 12 Anti-Patterns
  - Part 12: 10-milestone implementation plan with validation checklists and exit criteria
  - Aligned with existing `financial-os.css` tokens, AppShell layout, and existing runtime patterns
  - No frozen platform APIs modified

## Next Immediate Steps
- Implement milestones sequentially per Part 12 (no frozen API modifications)
- Milestone 1: Shell skeleton with all 8 regions, region contracts frozen
- Milestone 2: Workspace Host lifecycle, LRU caching (max 5), state persistence/restoration
- Track progress via verify-fast.sh validation gates at each milestone

</task_progress>

- [x] Phase A: Full discovery complete (backend, frontend, runtime, servers, tests, docs)
- [x] Phase B: Compile ARCHITECTURE_CONVERGENCE_AUDIT.md with all 20 sections
- [x] Phase C: Validate output file (70K, 936 lines, git untracked new file)
- [x] Write `docs/FINANCIAL_OS_SHELL_ARCHITECTURE.md` (12 parts, permanent specification)
- [x] Update memory-bank/activeContext.md with changes summary
- [ ] Git commit
</task_progress>
