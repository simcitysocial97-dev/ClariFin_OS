# CLARIFIN AI CONTROL LAYER DESIGN

**Document ID:** M9-C57 / AI_CONTROL_LAYER_DESIGN
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** AI_TOOL_AUTHORITY_MATRIX.md, CONTEXT_ENGINE_DESIGN.md, MODEL_ROUTING_DESIGN.md

---

## 1. Purpose

Design the AI Control Layer as a **governed client** of the ClariFin Platform Architecture.

The AI Control Layer is **not** the platform. It does not own execution, evidence, or
authority. It uses Platform APIs and tools to inspect, diagnose, propose, and — only with
authorization — execute governed tasks.

This is the foundational architectural rule:

> The AI is a governed client/operator of the Platform Architecture.
> Replace the model, the provider, or the agent implementation without replacing the system.

---

## 2. Architectural Position

```
                    USER
                      │
              ┌───────┴────────┐
              ▼                ▼
        PLATFORM GUI     AI WORKSPACE (in same Next.js)
              │                │
              └───────┬────────┘
                      ▼
            PLATFORM API  (/platform/v1/*)
                      │
                      ▼
        CANONICAL CONTROL PLANE  (C50, frozen)
                      │
                      ▼
       CAPABILITY / OBLIGATION GRAPH + EXECUTOR
                      │
                      ▼
              EVIDENCE + HISTORY
                      ▲
                      │
                      │
              AI CONTROL LAYER (NEW)
              ┌───────┴────────┐
              │                │
        ORCHESTRATOR      MODEL ROUTER
              │                │
              ├── Context Engine
              ├── Planner
              ├── Policy Engine
              ├── Tool Registry
              ├── Run Store
              └── Memory
```

The AI Control Layer lives **above** the Platform API and **below** the AI Workspace GUI.
It has **no** direct path to the executor, DB, or filesystem.

---

## 3. Components

### 3.1 Orchestrator (`runtime/platform/ai/orchestrator.py`)

Top-level loop. One orchestrator instance per AI request.

Responsibilities:

1. Receive user input.
2. Resolve intent.
4. Build context pack.
5. Produce plan.
6. Authorize plan via policy engine.
7. Execute plan tool-by-tool.
8. Observe each tool result.
9. Decide next step (continue, ask user, finalize).
10. Persist AI run record.
11. Return response.

Deterministic lifecycle (matches Section 28):

```
REQUEST → UNDERSTAND → INSPECT → PLAN → AUTHORIZE → EXECUTE → OBSERVE → RECONCILE → DECIDE → LEARN
```

### 3.2 Intent Resolver (`runtime/platform/ai/intent.py`)

Maps user request to a high-level intent:

| Intent | Examples |
|--------|----------|
| `diagnose` | "Why did X fail?" |
| `verify` | "Run the contract tests." |
| `inspect` | "Show me the dependency graph for X." |
| `plan` | "What should I run next?" |
| `compare` | "What's different from last run?" |
| `patch` | "Fix the failure." (Level 2+) |
| `workflow` | "Run reconciliation." (Level 3+) |

Uses the small local model by default. Falls back to deterministic intent catalog when the
model is unavailable.

### 3.3 Context Engine (`runtime/platform/ai/context/`)

See `CONTEXT_ENGINE_DESIGN.md`. Builds minimal context packs.

### 3.4 Planner (`runtime/platform/ai/planner.py`)

Produces a deterministic plan:

```
Plan(
  steps=[
    Step(tool="inspect_capability", args={"id": "recon.engine.contract"}),
    Step(tool="compare_runs", args={"current": "run-latest", "baseline": "LAST_PASS"}),
    Step(tool="diagnose_failure", args={"signature": "recon.contract"}),
  ],
  estimated_tokens=800,
  estimated_cost_usd=0.0,
)
```

The planner can be:

* **Deterministic** (rule-based) — preferred for known request patterns.
* **Model-assisted** — uses small local model for novel patterns.

### 3.5 Policy Engine (`runtime/platform/ai/policy.py`)

Authorizes every step. See `AI_TOOL_AUTHORITY_MATRIX.md`.

### 3.6 Tool Registry (`runtime/platform/ai/tools/`)

Governed tools. Each tool declares:

```python
class Tool:
    name: str
    description: str
    schema: dict[str, Any]      # JSON schema for args
    authorization: AuthorizationLevel
    risk: RiskLevel
    preconditions: list[Precondition]
    output_contract: dict[str, Any]
    evidence_behavior: Literal["creates", "consumes", "links"]
    cost_estimate: Literal["low", "medium", "high"]
```

Tools may not bypass the Platform API. They must call into the canonical control plane or
Platform API.

### 3.7 Model Router (`runtime/platform/ai/model_router.py`)

See `MODEL_ROUTING_DESIGN.md`. Routes requests to the appropriate provider.

### 3.8 AI Run Store (`runtime/platform/ai/runs/store.py`)

Persistent record of every AI run:

```
runtime/generated/platform/ai/runs/{run_id}.json
```

Same `EngineeringEvent` envelope, `kind=ai_run`.

### 3.9 Memory

| Class | Owner | Scope |
|-------|-------|-------|
| User memory | `runtime/platform/ai/memory/user.py` | Local. Stable user prefs. |
| Operational memory | `runtime/platform/ai/memory/operational.py` | Recent platform activity. |
| Engineering memory | `runtime/platform/ai/memory/engineering.py` | Known defects, decisions. |
| Episodic memory | `runtime/platform/ai/memory/episodic.py` | Recent AI runs. |
| Knowledge memory | **REUSE** `runtime/foundation/knowledge/` | Repository knowledge. |
| Financial state | **NEVER** stored in LLM memory. | Deterministic DB only. |

Memory writes are append-only and subject to the same audit log as Platform API writes.

### 3.10 Engineering Agent (`runtime/platform/ai/agents/engineering.py`)

Specialized prompt + tool subset for engineering tasks. Same orchestrator underneath.

Capabilities (Section 28):

* inspect
* diagnose
* plan
* modify (with authorization)
* test
* verify
* compare
* repair

Mandatory lifecycle: REQUEST → UNDERSTAND → INSPECT → PLAN → AUTHORIZE → EXECUTE →
OBSERVE → VERIFY → RECONCILE → DECIDE → LEARN.

The agent **never** reports success because a patch was generated. Success requires actual
evidence (an evidence_id).

### 3.11 Financial AI Agent (`runtime/platform/ai/agents/financial.py`)

Specialized agent for financial analysis. Read-only by default.

Capabilities (Section 29):

* financial analysis
* cashflow interpretation
* forecast interpretation
* anomaly explanation
* recommendation generation
* budget assistance
* reconciliation assistance
* scenario analysis

**Rule:** the Financial AI is **never** the authoritative financial calculator. All numbers
must trace back to the deterministic data model.

---

## 4. Authority Levels (Section 27)

| Level | AI may | Default tools | Required authorization |
|-------|--------|----------------|------------------------|
| 0 — Observe | inspect, summarize, diagnose, recommend | read-only tools | none |
| 1 — Analyze | run diagnostics, run tests, compare evidence, inspect failures | diagnostic + verification tools | none |
| 2 — Development | modify code, create tests, execute verification | modification tools | human confirmation |
| 3 — Controlled operations | state-changing application operations | workflow tools | human approval per task |
| 4 — High-risk | destructive migrations, bulk financial mutations, data deletion, production deployment | — | explicit human confirmation + audit trail |

The model **cannot elevate its own authority**. Elevation requires a config change.

---

## 5. AI Modes (Section 33)

| Mode | Description |
|------|-------------|
| **Manual** | AI disabled. User operates Console directly. |
| **Assisted** | AI recommends; user executes. Default mode. |
| **Autonomous** | AI executes permitted tasks within policy. Off by default. |

Mode is configured per-session via `/platform/settings`. The AI never silently changes mode.

---

## 6. AI Observability (Section 31)

Every AI run emits:

```
AI Run
  ├── request
  ├── model (provider + version)
  ├── context pack id + sources
  ├── plan
  ├── tool calls (one per step)
  ├── tool results (one per step)
  ├── executions (undertaken via /platform/v1/tasks)
  ├── evidence (linked evidence_ids)
  ├── decisions (plan outcomes)
  ├── final response
  ├── outcome
  ├── duration
  ├── token usage
  ├── cost
  └── audit trail
```

The `/platform/ai/runs/:runId` GUI page renders exactly this. No chain-of-thought is exposed
— only operational summaries and evidence lineage.

---

## 7. AI Diagnostic Experience (Section 32)

```
User: "Diagnose this system."
  ↓
AI:
  inspect_health()         → /platform/v1/health
  inspect_recent_changes() → /platform/v1/change/intelligence
  inspect_history_failures() → /platform/v1/history/runs?status=failed
  identify_affected_capabilities() → knowledge catalog
  inspect_evidence() → /platform/v1/evidence/by-execution/{id}
  construct_hypothesis() (model-assisted)
  recommend_diagnostic() → /platform/v1/ai/diagnose
  ↓
Response:
  FACT         — observed facts with evidence_ids
  EVIDENCE     — supporting evidence
  INFERENCE    — model-based reasoning (clearly labeled)
  HYPOTHESIS   — proposed root cause
  RECOMMENDATION — suggested action (with risk label)
```

The response always distinguishes FACT / EVIDENCE / INFERENCE / HYPOTHESIS / RECOMMENDATION.
LLM speculation is **never** presented as system truth.

---

## 8. AI + Human Cooperative Mode (Section 33)

Implemented as a `CooperativeSession` in the AI Workspace:

| Mode | UI behavior |
|------|-------------|
| Manual | AI Workspace hidden. |
| Assisted | AI shows recommended action; user clicks Run. |
| Autonomous | AI executes permitted tasks; user sees live execution + evidence. |

Per-mode behavior is enforced server-side, not client-side.

---

## 9. Failure Isolation (Section 49)

The AI Control Layer **must** degrade gracefully:

| Failure | Behavior |
|---------|----------|
| Local LLM unavailable | Fallback to deterministic intent / planner / canned responses. |
| External LLM unavailable | Same. |
| Tool call fails | Orchestrator logs error, marks step failed, decides retry vs surface to user. |
| Evidence invalidation detected | AI run pauses; user prompted. |
| Verification command fails | AI run aborts with diagnostic; no fabricated success. |
| AI run exceeds token budget | Abort with reason; do not silently truncate. |

---

## 10. Anti-Patterns (Forbidden)

* AI writing to DB directly — must use `/platform/v1/tasks` or platform tool.
* AI reading raw files outside context engine — must use `inspect_file` tool.
* AI proposing a patch without evidence — agent must produce evidence_id.
* AI calling external network without explicit tool allow-list.
* AI exposing chain-of-thought — only operational summaries.
* AI elevating its own authority — config-only.
* AI running the same tool call twice in parallel — at most one call per capability per plan step.
* AI caching secrets in memory — secrets read once per process.

---

## 11. Lifecycles (deterministic)

```
AI Run lifecycle:   REQUESTED → RUNNING → (PAUSED | COMPLETED | FAILED | ABORTED)
Tool call lifecycle: PLANNED → AUTHORIZED → RUNNING → (OK | FAILED) → RECORDED
Task lifecycle:      inherits from C50 obligation model
Evidence lifecycle:  inherits from C50 evidence model
```

The AI must NOT invent lifecycle states. If a state is missing, it is a defect.

---

## 12. Security

* All AI tool calls are logged in `audit.log` (separate from `application.log`).
* Local LLM endpoint never reaches the public internet.
* OpenRouter / external provider keys are loaded from environment only.
* Response payloads never include provider keys or local model paths.
* AI memory is local-only; no automatic upload.

---

## 13. Acceptance Criteria

* AI Control Layer is reachable only via `/platform/v1/ai/*`.
* AI never executes without a recorded AI Run id.
* AI Run trace includes model, context sources, plan, tool calls, evidence, decision.
* AI cannot fabricate evidence or execution.
* AI diagnostic responses distinguish FACT / EVIDENCE / INFERENCE / HYPOTHESIS / RECOMMENDATION.
* AI failure does not affect verification availability.
* Local Ollama is the default provider; absence does not block platform operation.
* Memory writes are auditable.