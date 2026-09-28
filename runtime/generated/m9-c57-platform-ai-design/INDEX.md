# M9-C57 Platform & AI Architecture — Design Set Index

**Document ID:** M9-C57 / INDEX
**Date:** 2026-09-05
**Status:** Design gate complete. Awaiting user approval.

This directory contains the **complete readiness design** for the ClariFin Platform
Operations Console and AI Control Layer. The design is built on top of the frozen M9-C50
Platform Architecture. No C50 module is modified.

---

## 1. Authority Split

| Authority | Document | Role |
|-----------|----------|------|
| **Design** | All docs in this directory | Defines architecture, primitives, invariants, contracts. |
| **Execution** | `IMPLEMENTATION_ROADMAP.md` | Defines phase sequence, gates, evidence structure. |
| **Execution record** | `runtime/generated/m9-c57/progress.md` (to be created at Phase 1) | Records what actually happened during implementation. |

These three must not be confused. The design set does **not** contain the execution
sequence by itself; the implementation roadmap does. The progress file is the
execution log, not a checklist.

---

## 2. Documents in This Set

| # | File | Purpose |
|---|------|---------|
| 1 | `PLATFORM_AI_ARCHITECTURE.md` | **Authoritative overview** — architecture, primitives, invariants, current authorized objective. |
| 2 | `PLATFORM_READINESS_ASSESSMENT.md` | Repository inventory + Section 73 STOP-condition resolution. |
| 3 | `PLATFORM_COMPONENT_MAP.md` | REUSE / ADAPT / BUILD / FORBIDDEN per component. |
| 4 | `PLATFORM_API_DESIGN.md` | `/platform/v1/*` JSON contracts. |
| 5 | `CONSOLE_INFORMATION_ARCHITECTURE.md` | Next.js `/platform` route group + screens. |
| 6 | `AI_CONTROL_LAYER_DESIGN.md` | Orchestrator, agents, observability. |
| 7 | `AI_TOOL_AUTHORITY_MATRIX.md` | Governed tools + Levels 0–4. |
| 8 | `CONTEXT_ENGINE_DESIGN.md` | Minimal context packs. |
| 9 | `MODEL_ROUTING_DESIGN.md` | Provider abstraction + routing. |
| 10 | `IMPLEMENTATION_ROADMAP.md` | **Execution authority** — 4-band / 21-phase plan + gates A–H. |
| 11 | `DESIGN_AUDIT.md` | Section 73 + Section 77 closure. |

---

## 3. Reading Order for Reviewers

1. `PLATFORM_AI_ARCHITECTURE.md` — overview, decisions, current state.
2. `PLATFORM_READINESS_ASSESSMENT.md` — repository reality + authority resolution.
3. `PLATFORM_COMPONENT_MAP.md` — what to reuse vs build.
4. `PLATFORM_API_DESIGN.md` + `CONSOLE_INFORMATION_ARCHITECTURE.md` — external surfaces.
5. `AI_CONTROL_LAYER_DESIGN.md` + `AI_TOOL_AUTHORITY_MATRIX.md` + `CONTEXT_ENGINE_DESIGN.md` + `MODEL_ROUTING_DESIGN.md` — AI Control Layer.
6. `IMPLEMENTATION_ROADMAP.md` — execution plan.
7. `DESIGN_AUDIT.md` — audit closure.

---

## 4. Reading Order for the Coding Agent (post-approval)

When implementation begins:

1. Read `IMPLEMENTATION_ROADMAP.md` **first** (this is the execution authority).
2. Read `PLATFORM_AI_ARCHITECTURE.md` §11 (Execution Discipline) and §12 (Current
   Authorized Objective).
3. Read the relevant design document(s) for the phase currently being implemented.
4. Read `DESIGN_AUDIT.md` to know which forbidden patterns to avoid.
5. Inspect the repository for any partial pre-existing work in `runtime/platform/`,
   `runtime/generated/m9-c57/`, or platform API contracts, and **reconcile** before
   creating new files (IMPLEMENTATION_ROADMAP.md §12).

---

## 5. Non-Negotiable Invariants

* **Single authorities** — one control plane, one executor, one evidence format, one
  capability registry, one task model, one event store.
* **C50 is frozen** — listed modules may not be modified without an explicit
  production-defect decision.
* **No second Python environment** (per `AGENTS.md`).
* **External model providers disabled by default.**
* **AI never bypasses the Platform API** — every AI call is a governed tool.
* **One objective at a time** — no batching of unrelated objectives.

---

## 6. Reconciliation Note for Phase 1

Phase 1 (`IMPLEMENTATION_ROADMAP.md` §12) requires the coding agent to first inspect for
partial pre-existing work in:

```
runtime/platform/
runtime/generated/m9-c57/
platform API contracts
```

If any partial implementation exists, it must be **reconciled**, not duplicated. The
design set above is the target state; the repository is the source of truth for what
already exists.

---

## 7. Status

* **Design gate:** PASS (DESIGN_AUDIT.md).
* **Implementation:** NOT STARTED. Awaiting user approval.
* **Current authorized objective** (per IMPLEMENTATION_ROADMAP.md §12):
  **Phase 1 — Platform Contract Foundation.**