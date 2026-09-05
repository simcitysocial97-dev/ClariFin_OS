# CLARIFIN CONSOLE INFORMATION ARCHITECTURE

**Document ID:** M9-C57 / CONSOLE_INFORMATION_ARCHITECTURE
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** PLATFORM_API_DESIGN.md

---

## 1. Purpose

Define the GUI information architecture for the **ClariFin Platform Console** — the
standalone route group `/platform/*` inside the existing Next.js application.

The Platform Console is **NOT** the financial product UI. It is the **engineering / platform
operations interface** that answers:

> "What is the current state of ClariFin_OS, what is healthy, what is broken, what changed,
> what has been verified, what remains unverified, what can I run, what happened previously,
> and what should I do next?"

It is operable without AI.

---

## 2. Decision: GUI Technology (Section 41)

**DECISION:** **Option A — Existing Next.js frontend + new `/platform` route group.**

Rationale:

* The repo already contains a fully wired Next.js 14+ app with command-center, evidence,
  and workspace UI (`frontend/components/command-center/`, `frontend/components/evidence/`).
* The platform console shares **design system** but is **not** part of the financial UI.
* No new build toolchain, no new test runner, no new deploy pipeline.
* Faster delivery; aligns with Section 67 ("speed of delivery").

A separate top-level layout is used so the platform console is visually and structurally
distinct from the financial UI (Section 42).

---

## 3. Route Map

```
/platform                              → Dashboard
/platform/verification                  → Verification Center
/platform/verification/run/:capability  → Live execution view
/platform/verification/history/:runId   → Past run detail
/platform/diagnostics                  → Diagnostics
/platform/diagnostics/change           → Change Intelligence
/platform/history                      → Historical runs
/platform/history/compare              → Comparison view
/platform/errors                       → Error Observatory
/platform/architecture                 → Architecture Safety Center
/platform/capabilities                  → Capability Explorer
/platform/capabilities/:capabilityId    → Capability detail
/platform/ai                           → AI Workspace
/platform/ai/runs                      → AI Observability
/platform/ai/runs/:runId               → AI Run trace
/platform/settings                     → Model routing, secrets, authorization
```

---

## 4. Dashboard (`/platform`)

**Goal:** A single screen showing whether ClariFin_OS is operable, and the dimensions
underlying the answer.

### Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  ClariFin Platform Console                                         │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──── System ────┐  ┌──── Quick Actions ────┐  ┌──── Diagnostics ─┐│
│  │ HEALTHY        │  │ [Diagnose]            │  │ 1 NON-CRITICAL ││
│  │ 5 dimensions   │  │ [Verify]              │  │ 0 CRITICAL     ││
│  │ degraded       │  │ [History]             │  │ last: ...      ││
│  └────────────────┘  │ [Errors]              │  └────────────────┘│
│                      │ [AI]                  │                     │
│                      └───────────────────────┘                     │
│                                                                      │
│  ┌──── Readiness Scoreboard ──────────────────────────────────────┐ │
│  │ Domain                Status    Last Check   Source             │ │
│  │ Environment           HEALTHY   ...          /platform/v1/...  │ │
│  │ Repository            HEALTHY   ...          ...                │ │
│  │ Backend               HEALTHY   ...          /health            │ │
│  │ Frontend              HEALTHY   ...          ...                │ │
│  │ ...                                                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌──── Recent Activity (last 24h) ────────────────────────────────┐│
│  │ verification.failed   recon.contract   03:55                   ││
│  │ evidence.invalidated  sha256:abc...    03:55                   ││
│  │ task.created          obl-...          03:54                   ││
│  └────────────────────────────────────────────────────────────────┘│
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### Data sources

* `/platform/v1/health` — single snapshot.
* `/platform/v1/events?since=24h` — recent activity.
* `/platform/v1/errors/recent` — current error count.

### Performance budget

* Initial render < 300ms on Lenovo IdeaPad S145.
* No repository scan, no full verification run, no LLM call.

---

## 5. Verification Center (`/platform/verification`)

### 5.1 Verification list view

```
┌──────────────────────────────────────────────────────────────────────┐
│ Verification Center                                                  │
├──────────────────────────────────────────────────────────────────────┤
│ Filters: [Capability] [Profile] [Status] [Last Run]                 │
│                                                                      │
│ ┌─ Capability ───────────────── Status  Last Run  Tests  ─────────┐│
│ │ discover.blast-radius         HEALTHY  03:55    -     [Run]    ││
│ │ execute.unit-tests.backend    HEALTHY  03:50    240   [Run]    ││
│ │ execute.contract.api          DEGRAD  03:55    12    [Run]    ││
│ │ execute.mutation              HEALTHY  02:10    -     [Run]    ││
│ │ ...                                                            ││
│ └────────────────────────────────────────────────────────────────┘│
│                                                                      │
│ [Run Selected] [Run Affected] [Run Full Suite] [Cancel All]         │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 Capability detail

```
┌──────────────────────────────────────────────────────────────────────┐
│ execute.contract.api                                                 │
├──────────────────────────────────────────────────────────────────────┤
│ Status: DEGRADED   Last Run: 03:55   Duration: 12s                  │
│ Command: ...                                                         │
│ Produces: contract_evidence                                          │
│                                                                      │
│ Recent results:                                                       │
│   2026-09-05 03:55  FAILED  evidence=sha256:...                    │
│   2026-09-04 03:00  PASSED  evidence=sha256:...                    │
│   2026-09-03 03:00  PASSED  evidence=sha256:...                    │
│                                                                      │
│ Affected capabilities: [...]                                         │
│ Cache: HIT / MISS (last 7 days)                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.3 Live execution view (`/platform/verification/run/:capability`)

```
RUNNING — execute.contract.api
────────────────────────────────────────────────────────────
Task:       obl-abc
Execution:  exec-xyz
Started:    03:55:12
Elapsed:    00:00:08

Phases:
  ✓ capability.resolved
  ✓ obligation.created
  ▶ execution.started
  · evidence.generated
  · reconciliation
  · decision

Subprocess:
  pytest -q backend/tests/contracts/...  (running)
  stdout: ...
  stderr: ...

[Cancel]
```

Implemented via SSE on `/platform/v1/executions/{id}/stream`. No fake progress bars.

---

## 6. Diagnostics (`/platform/diagnostics`)

### 6.1 Diagnostics landing

The lowest-cost sufficient diagnostic first (Section 14):

```
L0 — historical evidence (cheapest)
L1 — metadata / health inspection
L2 — targeted diagnostics
L3 — affected verification
L4 — broader verification
L5 — full repository verification (most expensive)
```

UI flow: enter symptom → AI diagnostic assistant OR deterministic diagnostic engine →
recommended next step (always lowest-cost first).

### 6.2 Change Intelligence (`/platform/diagnostics/change`)

```
Repository changes since last known-good state
──────────────────────────────────────────────
Files changed: 3
Capabilities affected: 2

backend/src/engines/reconciliation/foo.py
  → recon.engine.contract    stale evidence: sha256:abc
  → recon.engine.unit        stale evidence: sha256:def

frontend/components/recon/recon-panel.tsx
  → recon.frontend.snapshot  no test change

Suggested verification:
  L3 — execute.contract.api (3 contract tests)
```

Data source: `/platform/v1/change/intelligence`.

---

## 7. History (`/platform/history`)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Run History                                                          │
├──────────────────────────────────────────────────────────────────────┤
│ Filters: [Environment] [Intent] [Status] [Capability] [Date]        │
│                                                                      │
│ ┌─ Run ─────────── Started ─── Status ── Tests ── Duration ─┐      │
│ │ run-latest      03:55       FAILED    240      449s      │      │
│ │ run-2026-09-04  03:00       PASSED    240      410s      │      │
│ │ ...                                                       │      │
│ └────────────────────────────────────────────────────────────┘      │
│                                                                      │
│ Compare: [vs Last Run] [vs Last Pass] [vs Known Good] [vs Baseline]│
└──────────────────────────────────────────────────────────────────────┘
```

### Comparison view (`/platform/history/compare`)

Shows:

* Repository changes.
* Test diff (added / removed / new failures / resolved).
* Duration delta.
* Coverage delta (where relevant).
* Evidence invalidated / preserved.
* Capability state changes.

---

## 8. Error Observatory (`/platform/errors`)

### Tabs

* **Current** — last hour, sorted by recency.
* **Recent** — last 24h.
* **Recurring** — grouped by signature.
* **Frequency** — histogram.
* **By layer** — backend, verification, AI, application.

### Per-error detail

```
Error sha256:abc123
  First seen:  2026-09-04 18:00
  Last seen:   2026-09-05 03:55
  Frequency:   4 occurrences / 24h
  Layer:       verification
  Capability:  recon.engine.contract
  Root cause:  UNKNOWN  (run diagnose →)
  Resolution:  PENDING
  Affected workflows: reconciliation, daily ledger
  Evidence:    sha256:def
  Execution:   exec-456
```

---

## 9. Architecture Safety Center (`/platform/architecture`)

### Authorities grid

| Authority | Status | Source |
|-----------|--------|--------|
| Canonical control plane | HEALTHY | `runtime/foundation/verification/canonical_control_plane.py` |
| Capability authority | HEALTHY | `capability_authority.py` |
| Task authority | HEALTHY | `obligation.py` |
| Execution authority | HEALTHY | `executor.py` |
| Evidence authority | HEALTHY | `evidence_contract.py` |
| Decision authority | HEALTHY | `control_plane_efficiency.py` |
| Cache authority | HEALTHY | `cache.py` |
| Verification authority | HEALTHY | `verification.yaml` |

### Other panels

* Bypass attempts (last 30 days).
* Duplicate authorities.
* Deprecated calls still in use.
* Unmapped capabilities.
* Invalid transitions.

---

## 10. Capability Explorer (`/platform/capabilities`)

Tree view (left) + detail panel (right).

### Capability detail

```
recon.engine.contract
─────────────────────
Owner:        @engineering
Runtime:      backend
API:          POST /api/recon/run
Frontend:     recon-panel, recon-drawer
Dependencies: ledger_engine, transaction_engine
Tests:        backend/tests/contracts/recon/...
Verification: execute.contract.api
Evidence:     sha256:abc...
Recent failures: 2 / 30 days
Recent changes:  4 / 30 days
Health:        DEGRADED
```

Clicking any link opens the corresponding platform page.

---

## 11. AI Workspace (`/platform/ai`)

### 11.1 Chat

```
You: Why did reconciliation fail in the last run?

AI (qwen2.5-3b-instruct, 1.2s):
  Found 1 capability with new failure: recon.engine.contract
  Evidence: sha256:abc
  Previous result: PASSED
  Change: backend/src/engines/reconciliation/foo.py
  Hypothesis: state-shape mismatch after the recent ledger serializer change.
  Recommendation: run targeted reconciliation contract verification.

  [Run]  [Inspect capability]  [Explain]
```

### 11.2 AI observability (`/platform/ai/runs`)

List of AI runs with filters: model, tool, duration, outcome, cost.

Per-run trace (`/platform/ai/runs/:runId`):

* Request, model, context sources, plan, tool calls, evidence, decisions, final response,
  outcome, token usage, latency.
* **Operational summaries only** — no chain-of-thought.

### 11.3 Settings (`/platform/settings`)

* Model providers (Local Ollama, OpenRouter, future).
* Default per-task routing rules.
* Authorization scopes.
* Secret handling (read from env only, never echoed).

---

## 12. Visual / UX Principles

1. **One navigation rail** (left): Dashboard / Verification / Diagnostics / History / Errors /
   Architecture / Capabilities / AI / Settings.
2. **One global status bar** (top): overall platform health + AI readiness.
3. **Dark / light themes** supported (reuse existing design tokens).
4. **No fake animations.** Live state uses real data; static sections are static.
5. **Density-first.** Engineer / operator audience — maximize signal per pixel.
6. **Keyboard-first.** `g d` → dashboard, `g v` → verification, `g h` → history, etc.
7. **Offline-ready.** All pages render against cached snapshots. SSE shows "disconnected"
   banner when stream is unavailable.

---

## 13. Layout Isolation from Financial UI

The Platform Console uses:

* `frontend/app/platform/layout.tsx` (new).
* `frontend/app/platform/globals.css` (new).
* `frontend/components/platform/*` (new directory).
* Does NOT import from `frontend/components/command-center/` or `frontend/components/evidence/`
  unless wrapped in a platform-specific adapter.

The financial UI (`/accounts`, `/transactions`, etc.) **does NOT** import from the platform
directory. One-directional dependency.

---

## 14. Accessibility

* WCAG 2.1 AA target.
* Color is not the sole signal (status badges include text + icon).
* All interactive elements keyboard-reachable.
* All AI responses provide evidence links (Section 43).

---

## 15. Acceptance Criteria (Console MVP)

1. User can open `/platform` without an IDE.
2. Dashboard renders in < 300ms using cached snapshot.
3. User can run a single verification, a group, or the full suite.
4. User can inspect history with comparison.
5. User can inspect errors with frequency analysis.
6. User can inspect architecture safety and capability tree.
7. **No LLM call is required for any page to load or operate.**
8. AI workspace is fully optional and can be disabled by configuration.