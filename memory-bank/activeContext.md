# Active Context

## Current Focus
Program 7A — Cross-Layer Intelligence Foundation (Complete)
Program 6.0 — Repository Architecture Convergence Audit (Complete)
Program C — Financial OS Shell Architecture (Complete)

## Recent Changes
- **M10 — Unified Reproducible Dev Environment & Dependency Modernization (2026-08-14)**
  - Created single repository Python venv (`./.venv`) via `scripts/bootstrap.sh`; root `pyproject.toml` now the SINGLE Python dependency authority (removed obsolete `backend/requirements*.txt`)
  - Added repo-owned wrappers `scripts/verify.sh`, `scripts/env-doctor.sh`, `scripts/freeze-env.sh`; CI `setup-python-runtime` now consumes `pip install -e ".[all]"` (no inline tool installs)
  - Removed backend `[tool.ruff]`/`[tool.black]` duplicates → canonical Black/Ruff at root; `requirements.lock` generated (77 pinned pkgs)
  - Safe upgrades validated locally: fastapi 0.139.2, pydantic 2.13.4, pytest 9.1.1 (ruff + mypy + 760 unit tests green via controlled interpreter)
  - Decision record: `docs/decisions/M10_ENVIRONMENT_DEPENDENCIES.md`
- **Program 7A: Cross-Layer Intelligence Foundation (2026-08-04)**
  - Created `tools/generators/build_cross_layer_map.py` for deterministic dependency graph generation
  - Generated `runtime/generated/cross-layer-map.json` with 57 engine entries (57 files)
  - Added `CrossLayerImpactPlanner` and `ImpactReport` to `runtime/foundation/verification/planner/planner.py`
  - Enriched evidence aggregation in `runtime/system/evidence/aggregator.py` with dependency chains
  - Updated `__init__.py` exports for planner (CrossLayerImpactPlanner, ImpactReport)
  - Updated `.github/workflows/backend-verify.yml` and `.github/workflows/frontend.yml` with cross-layer map generation
  - Created `docs/CROSS_LAYER_INTELLIGENCE.md` with full documentation
  - No business logic, frontend, backend, DTO, or runtime redesign changes
  - All validation passes: ruff clean, JSON valid, planner works, aggregator imports
  - Verified minimal blast radius - loan engine change only affects loan workspace, not dashboard/cashflow/forecast

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
  - Parts 13-19 (Execution Rules, Never Skip, Startup/End-of-Run Validation, State Machine, Milestone Template, Rollback Support) — AI Operating Manual for autonomous execution
  - Milestones updated to 4-section format (State/Objective/Implementation/Validation/Freeze Decision) per template in Part 18
  - Created `docs/EXECUTION_STATE.md` — single mutable source of truth for AI progress (Current Milestone, Completed, Current Task, Validation Status, Known Tech Debt, Deferred, Next Action, Rollback file records)
  - Architecture doc is immutable; execution state lives only in EXECUTION_STATE.md
  - Aligned with existing `financial-os.css` tokens, AppShell layout, and existing runtime patterns
  - No frozen platform APIs modified

## Next Immediate Steps
- Begin Milestone 1: Shell Skeleton and Region Contracts per EXECUTION_STATE.md
- Read FINANCIAL_OS_SHELL_ARCHITECTURE.md and EXECUTION_STATE.md on every session start
- Follow Part 14 (Never Skip) checklist before writing any code
- Track progress exclusively in docs/EXECUTION_STATE.md (not in architecture doc)
- Milestone state machine: NOT_STARTED → IN_PROGRESS → VALIDATED → COMPLETE → FROZEN

</task_progress>

- [x] Phase A: Full discovery complete (backend, frontend, runtime, servers, tests, docs)
- [x] Phase B: Compile ARCHITECTURE_CONVERGENCE_AUDIT.md with all 20 sections
- [x] Phase C: Validate output file (70K, 936 lines, git untracked new file)
- [x] Write `docs/FINANCIAL_OS_SHELL_ARCHITECTURE.md` (12 parts, permanent specification)
- [x] Update memory-bank/activeContext.md with changes summary
- [ ] Git commit
</task_progress>

---

## M9-C8 — Merge-Gate Policy Separation (2026-08-16)

- **Changed:** GitHub repository ruleset `protect-main-branch` (ID 20127383) — expanded `required_status_checks` from 1 to 6 contexts: `Quality Gate`, `Backend Verification`, `Frontend Verification`, `Runtime Verification`, `Plan / Execute / Reconcile`, `Analyze`
- **Excluded from required:** All 6 Playwright E2E checks (`E2E Tests (*)`), `M9 Forensic Evidence Collection`, and dynamic `CodeQL` check — all remain non-required
- **Preserved:** deletion, non_fast_forward, pull_request (1 review), strict=false, bypass_actors=[]
- **No file changes** to workflows, Playwright config, application code, or verification framework — only `progress.md` appended
- **Validation:** All 6 required checks pass on PR #5; Playwright/M9 fail but non-blocking; Playwright workflow remains `active`; PR mergeability blocked solely by the existing 1-approving-review requirement
- **Next step:** Human reviewer approves PR #5 → mergeable. Playwright reliability remains a separate future task.
