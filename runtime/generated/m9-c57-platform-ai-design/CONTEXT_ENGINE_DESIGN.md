# CLARIFIN CONTEXT ENGINE DESIGN

**Document ID:** M9-C57 / CONTEXT_ENGINE_DESIGN
**Date:** 2026-09-05
**Status:** DESIGN ONLY
**Companion to:** AI_CONTROL_LAYER_DESIGN.md, MODEL_ROUTING_DESIGN.md

---

## 1. Purpose

The Context Engine assembles the **smallest sufficient context** for an AI task. It must
prevent the AI from ingesting the entire repository or relying on long chat memory alone.

The directive (Section 22) is explicit:

> The AI should receive the smallest context sufficient to solve the task.

The Context Engine produces a **Context Pack** — a deterministic, content-addressed bundle
of evidence, code, history, architecture, and policy references that an AI run can consume
without re-reading the repository.

---

## 2. Context Pack Structure

```json
{
  "kind": "platform.context_pack",
  "version": "1.0.0",
  "id": "sha256:<hex>",
  "generated_at": "...",
  "components": {
    "repository": { ... },
    "capability": { ... },
    "runtime": { ... },
    "financial": { ... },
    "task": { ... },
    "failure": { ... },
    "evidence": [ ... ],
    "historical": { ... },
    "architecture": { ... },
    "policy": { ... }
  },
  "total_tokens_estimate": 2400,
  "token_budget": 8000,
  "sources": [
    "knowledge:KnowledgeEntry(capability.recon.engine.contract)",
    "history:EngineeringRun(run-latest)",
    "evidence:VerificationEvidence(sha256:abc)",
    "repository:RepoFile(backend/src/engines/reconciliation/foo.py)",
    "policy:Tool(diagnose_failure)"
  ]
}
```

Each source is content-addressed. The pack is reproducible: given the same inputs, the
same context pack id is produced.

---

## 3. Context Sources (REUSE-first)

| Source | Owner module | Format |
|--------|--------------|--------|
| Repository | `runtime/foundation/repository/query/query.py` | file/symbol references |
| Knowledge | `runtime/foundation/knowledge/catalog.py` | KnowledgeEntry, CapabilityEntry, EndpointEntry, ComponentEntry |
| History | `runtime/generated/engineering-history.json` | run records |
| Evidence | `runtime/system/evidence/models/evidence.py` | VerificationEvidence, ContractEvidence |
| Events | `runtime/system/observability/event_store.py` | EngineeringEvent list |
| Errors | NEW `runtime/platform/errors/store.py` | error records |
| Architecture | `runtime/foundation/architecture/` | authority health |
| Policy | NEW `runtime/platform/ai/policy.py` | tool risk + scope |
| Memory | NEW `runtime/platform/ai/memory/*.py` | episodic, operational |

**No new index database is introduced.** The Context Engine reads existing structures.

---

## 4. Retrieval Strategy

### 4.1 Deterministic retrieval (default)

```
intent → seed components
  → expand via dependency graph (capability → owner → tests → evidence)
  → expand via history (recent runs affecting those capabilities)
  → expand via evidence (linked evidence_ids)
  → expand via policy (allowed tools + risk)
  → token-budget trim (drop lowest priority)
  → SHA-256 of canonical serialization
```

### 4.2 Relevance ranking

Each candidate component has a priority score:

| Source | Priority weight |
|--------|-----------------|
| Direct evidence (failing test, failing contract) | 100 |
| Recent change affecting capability | 80 |
| Capability itself | 70 |
| Recent run for capability | 60 |
| Knowledge entry for capability | 50 |
| Adjacent capability (1 hop) | 30 |
| Architecture boundary | 20 |
| Documentation | 10 |
| Repository file (selected symbol) | variable, capped 100 |

The pack is filled top-down until the token budget is reached.

### 4.3 Dependency expansion

Each capability has dependencies (`runtime/foundation/verification/capability_graph.py`).
The engine expands 1 hop by default. Recursion is bounded.

### 4.4 Historical comparison

If the request mentions "compare" or "diff", the engine includes the `current vs baseline`
delta (Section 13 of directive) as a structured component.

---

## 5. Token Budget Management

| Profile | Budget | Notes |
|---------|--------|-------|
| Local small model | 2k–4k | Lenovo IdeaPad S145 |
| Local larger model | 8k–16k | Gaming PC |
| External model | 16k–32k | OpenRouter default |

The Context Engine honors the budget and **never** silently truncates. If the budget is
insufficient, it produces a pack with `status=incomplete` and a list of omitted components.
The orchestrator decides whether to drop the request or escalate.

---

## 6. Provenance

Every component in the pack carries a `source` field with:

* `kind`: knowledge | history | evidence | event | error | architecture | policy | memory | repository
* `id`: stable identifier (KnowledgeEntry id, run id, evidence id, etc.)
* `path` (if file)
* `symbol` (if symbol)
* `line_range` (if symbol)

The Context Engine never invents content. Every byte of the pack traces back to a known
source.

---

## 7. Context Pack Assembly Pipeline

```
PlanStep:
  intent = "diagnose"
  capability_id = "recon.engine.contract"
  run_id = "run-latest"

  ↓

ContextBuilder.build(intent, plan_step):
  capability = knowledge.get(capability_id)
  recent_runs = history.recent(capability_id, limit=5)
  failed_runs = history.failed(capability_id, limit=3)
  failing_evidence = evidence.by_run(run_id, status="failed")
  affected_files = repo.files_changed_since(last_known_good)
  test_files = repo.tests_for_capability(capability_id)
  adjacent_capabilities = capability_graph.neighbors(capability_id, depth=1)
  policy = policy.tools_for_capability(capability_id)
  episodic = memory.recent_runs(summar, limit=3)

  ↓

Rank + assemble + budget trim.

  ↓

ContextPack(id=sha256(...), components=..., sources=..., total_tokens=...)
```

---

## 8. Small Local Model Compensation (Section 24)

The directive requires the platform to compensate for small-model limitations through
structured context. The Context Engine does this by:

1. **Constraining output schema.** Tools return JSON. The model never generates free-form
   arguments.
2. **Providing ranked candidates.** The model is told "given these 5 candidates, choose
   one" rather than "find the right one in the entire repo".
4. **Pre-computed evidence.** The model does not run tools mid-response. It picks from a
   pre-computed menu.
5. **No multi-turn planning.** The orchestrator plans once, executes sequentially, and
   stops. No recursive tool chaining in one LLM call.
6. **Decision templates.** Each diagnostic intent has a template response with placeholders
   the model fills.

This makes a small model effective without requiring intelligence about everything.

---

## 9. Context Engine Subsystems

| Subsystem | Module | Responsibility |
|-----------|--------|----------------|
| Builder | `runtime/platform/ai/context/builder.py` | Assemble the pack. |
| Ranker | `runtime/platform/ai/context/ranker.py` | Priority scoring. |
| Trimmer | `runtime/platform/ai/context/trimmer.py` | Token budget enforcement. |
| Provenance | `runtime/platform/ai/context/provenance.py` | Track every byte. |
| Serializer | `runtime/platform/ai/context/serializer.py` | Canonical JSON for hashing. |
| Cache | `runtime/platform/ai/context/cache.py` | Reuse identical packs by id. |

---

## 10. Cache Behavior

Context packs are content-addressed. If two plan steps produce the same logical request, the
same pack id is generated and reused. Cache TTL: until any source component changes.

Invalidation sources:

* `git status` change → repository source invalidated.
* New run recorded → history source invalidated.
* New evidence → evidence source invalidated.
* Capability catalog change → capability source invalidated.

---

## 11. Test Plan

* Unit tests for builder, ranker, trimmer, serializer, provenance.
* Property tests for content-addressing.
* Integration tests using a fixed fixture repository.
* Token-budget tests asserting `total_tokens_estimate ≤ budget`.
* Provenance tests asserting every byte is traceable.

---

## 12. Acceptance Criteria

* A Context Pack is reproducible: same inputs → same id.
* A Context Pack never exceeds its budget (or surfaces `status=incomplete`).
* Every component in the pack traces to a known source.
* The small local model can answer a "diagnose" intent using only the pack.
* Cache hit rate improves over time as the platform runs more requests.