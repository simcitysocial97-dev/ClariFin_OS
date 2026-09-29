# CLARIFIN MODEL ROUTING DESIGN

**Document ID:** M9-C57 / MODEL_ROUTING_DESIGN
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** AI_CONTROL_LAYER_DESIGN.md, CONTEXT_ENGINE_DESIGN.md

---

## 1. Purpose

Define how AI requests are routed across model providers, with explicit support for the
Lenovo IdeaPad S145 (low memory, small local model) and a future gaming PC (larger local
model + larger context).

The directive (Sections 25, 38, 70, 71) requires:

* Provider abstraction.
* Routing by task complexity, context size, privacy, latency, cost, availability, reasoning.
* Offline-first: the platform remains operational when external models are unavailable.
* Migration between hardware profiles via configuration, not architectural changes.

---

## 2. Providers

| Provider | Type | Default model | Hardware |
|----------|------|----------------|----------|
| `local-small` | Ollama | `qwen2.5:3b-instruct` (default) | Laptop |
| `local-large` | Ollama | `qwen2.5-coder:14b` or equivalent | Gaming PC |
| `openrouter` | External HTTP | user-configured | Any |

The provider catalog is open-ended. New providers implement the `ModelProvider` protocol:

```python
class ModelProvider(Protocol):
    name: str
    kind: Literal["local", "external"]
    models: list[ModelDescriptor]

    def complete(
        self,
        *,
        model: str,
        messages: list[Message],
        tools: list[ToolSpec],
        tool_choice: Literal["auto", "none"] | str,
        max_tokens: int,
        temperature: float,
    ) -> CompletionResult: ...

    def health(self) -> ProviderHealth: ...
```

---

## 3. Routing Policy

Each request carries a routing profile:

```python
@dataclass(frozen=True)
class RoutingProfile:
    task_kind: str            # "diagnose", "summarize", "classify", "plan", "explain"
    context_size: int         # tokens in the context pack
    privacy: Literal["local", "external_ok"]
    latency_budget_ms: int
    cost_budget_usd: float
    required_capability: CapabilityRequirement
    availability_required: bool
```

The router evaluates providers in order of preference:

1. **Local providers** first (privacy + offline).
2. Filter by `task_kind` capability (see Section 5).
3. Filter by `context_size ≤ model.context_window`.
4. Filter by `privacy` (external rejected if `local`).
5. Filter by `availability` (health check).
6. Filter by `latency_budget_ms` (estimated).
7. Filter by `cost_budget_usd`.
8. Pick the **best-scoring** provider (capability weight + latency weight + cost weight).

If no provider satisfies, fall back:

* For observability/diagnostic tasks → deterministic intent catalog.
* For modification tasks → require human.

---

## 4. Routing Configuration (`runtime/platform/ai/routing.yaml`)

```yaml
defaults:
  provider: local-small
  model: qwen2.5:3b-instruct
  temperature: 0.1

providers:
  local-small:
    kind: local
    endpoint: http://localhost:11434
    health_check_interval_s: 30
    fallback: deterministic

  local-large:
    kind: local
    endpoint: http://localhost:11434
    health_check_interval_s: 30
    fallback: local-small

  openrouter:
    kind: external
    endpoint: https://openrouter.ai/api/v1
    api_key_env: OPENROUTER_API_KEY
    health_check_interval_s: 60
    fallback: local-small
    disabled: true   # default off; opt-in via settings

task_profiles:
  classify:
    preferred_providers: [local-small]
    deterministic_fallback: true
  summarize:
    preferred_providers: [local-small]
  diagnose:
    preferred_providers: [local-small, local-large]
    escalate_if_uncertain: true
  plan:
    preferred_providers: [local-small, local-large]
    deterministic_fallback: true
  patch:
    preferred_providers: [local-large, openrouter]
    human_required: true
    disabled_by_default: true

routing_weights:
  capability: 0.5
  latency: 0.2
  cost: 0.2
  privacy: 0.1
```

---

## 5. Model Capabilities

Each model descriptor declares:

```yaml
- name: qwen2.5:3b-instruct
  context_window: 4096
  capabilities:
    - classify
    - summarize
    - route
    - tool_select
    - simple_plan
    - short_explain
  cost_per_1k_tokens: 0.0   # local
  latency_p50_ms: 600

- name: qwen2.5-coder:14b
  context_window: 16384
  capabilities:
    - classify
    - summarize
    - route
    - tool_select
    - plan
    - explain
    - patch
    - test_generation
  cost_per_1k_tokens: 0.0
  latency_p50_ms: 2400

- name: openrouter:anthropic/claude-3.5-sonnet
  context_window: 200000
  capabilities:
    - classify
    - summarize
    - route
    - tool_select
    - plan
    - explain
    - patch
    - test_generation
    - long_context_analysis
  cost_per_1k_tokens: 0.003
  latency_p50_ms: 1500
  privacy: external_ok
```

Capabilities are derived from model descriptions and runtime evaluation, not invented.

---

## 6. Provider Health

The router maintains a per-provider health snapshot:

```python
@dataclass(frozen=True)
class ProviderHealth:
    provider: str
    reachable: bool
    last_check: datetime
    last_success: datetime | None
    last_failure: datetime | None
    failure_streak: int
    p50_latency_ms: int
    notes: str
```

Updated every `health_check_interval_s`. Health checks are **non-blocking**; the orchestrator
never awaits them on the critical path. Stale health snapshots may be used with a warning.

If `reachable=false` and `failure_streak ≥ 3`, the provider is **marked down** and
re-evaluation is delayed.

---

## 7. Deterministic Fallback (Section 38, 49)

When all providers are unavailable, the orchestrator must still respond. The deterministic
fallback layer provides:

* **Intent catalog** — map user input to closest matching intent.
* **Tool-only execution** — execute the plan using only platform tools, no model reasoning.
* **Canned summaries** — for known failure signatures, return the stored diagnosis.

The fallback **never** fabricates evidence or pretends the model was used. The AI Run record
clearly marks `mode=deterministic_fallback`.

---

## 8. Hardware Profile Migration (Section 70, 71)

Migration from laptop → gaming PC is configuration-only:

```yaml
# laptop profile
defaults:
  provider: local-small
  model: qwen2.5:3b-instruct

# gaming-pc profile
defaults:
  provider: local-large
  model: qwen2.5-coder:14b
```

No code changes required. The router selects providers based on configuration and health.

A single CLI command switches the profile:

```bash
.venv/bin/python runtime/verify.py platform profile set gaming-pc
```

---

## 9. Privacy Boundary (Section 40)

* `privacy: local` requests MUST NOT reach external providers, even on fallback.
* The router rejects external providers for `privacy=local` and surfaces the rejection in
  the AI Run trace.
* Provider credentials are read from environment only; never logged.
* The Context Engine may redact certain components before sending them to external
  providers (e.g. private memory entries). Redaction is recorded in the trace.

---

## 10. Cost Awareness

* Token usage is recorded in the AI Run record.
* A session-level budget is enforced (default: $0.10 per session; configurable).
* External providers are **off by default** (per Section 38 + 67).
* The router never silently switches providers mid-run.

---

## 11. Observability

The router exposes `/platform/v1/ai/providers`:

```json
{
  "kind": "platform.ai_providers",
  "data": {
    "providers": [
      {
        "name": "local-small",
        "kind": "local",
        "models": ["qwen2.5:3b-instruct"],
        "health": { "reachable": true, "p50_latency_ms": 600, "failure_streak": 0 }
      },
      {
        "name": "local-large",
        "kind": "local",
        "models": ["qwen2.5-coder:14b"],
        "health": { "reachable": false, "last_failure": "...", "failure_streak": 5 }
      },
      {
        "name": "openrouter",
        "kind": "external",
        "models": ["anthropic/claude-3.5-sonnet"],
        "health": { "reachable": false, "reason": "disabled_by_default" }
      }
    ]
  }
}
```

---

## 12. Acceptance Criteria

* Provider abstraction exists; no platform code references a provider name directly.
* Local provider is the default; external providers are opt-in.
* Offline operation is supported (deterministic fallback).
* Cost and latency budgets are enforced.
* Hardware migration is configuration-only.
* Provider health is observable.
* Privacy boundary is enforced server-side.