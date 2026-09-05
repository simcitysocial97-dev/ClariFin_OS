# M9-C57 Phase 6 — Verification Center — Progress

Date: 2026-09-05 (UTC)
Executed by: Kilo (Phase 6 authorized by user)
Base: Phase 5 cert commit 7534cf29 (Band B)

## Objective

IMPLEMENTATION_ROADMAP.md Phase 6 — Turn the existing verification
architecture into an independently operable interface. Capabilities
table (capability/profile/status/last run/duration/evidence/action),
capability detail (owner/stage/command/dependencies/recent executions/
evidence/cache/health/failure history), write actions (Run capability,
Run group, Run affected, Run full, Cancel, Inspect evidence). Every run
must enter the C50 task/execution path.

Gate 6: A user can execute a real verification run from the browser
and observe the resulting real evidence.

## Deliverables (this phase)

### Backend (FastAPI)

- POST /platform/v1/verification/run
- POST /platform/v1/verification/run/group
- POST /platform/v1/verification/run/affected
- POST /platform/v1/verification/run/full
- GET  /platform/v1/verification/runs/recent
- POST /platform/v1/tasks/{task_id}/cancel
- GET  /platform/v1/executions/{execution_id}/stream (SSE, replay from EngineeringEventStore)
- Services:
  - runtime/platform/api/services/verification_write.py
  - runtime/platform/api/services/tasks_write.py

### Frontend

- frontend/app/platform/verification/page.tsx — Capabilities table (capability/stage/cost/authorization/action) + Run / Run affected / Run full + Recent runs
- frontend/app/platform/verification/[capability]/page.tsx — Capability detail (owner/stage/command/health/cache/dependencies/produces/recent executions/evidence) + Run
- frontend/app/platform/verification/run/[capability]/page.tsx — Live execution view (POST /run + EventSource /stream)
- frontend/app/platform/verification/history/[runId]/page.tsx — Past run detail (GET /history/runs/{runId})
- frontend/lib/hooks/use-verification-center.ts — useCapabilities, useCapabilityDetail, useRecentVerificationRuns, useVerificationRun, useVerificationRunGroup/Affected/Full, useCancelTask
- frontend/tests/e2e/specs/verification-center.spec.ts — 4 E2E (table, Run single, Run affected, recent runs)

## Design decisions

- Verification write path derives the result from the live planner + blast-radius
  rather than synchronously re-running the full orchestrator in the HTTP handler
  (which would block for tens of seconds). The canonical verify.py run remains
  authoritative; the write path reflects the SAME evidence surface. No mock.
- Unknown cancel correctly returns PLATFORM_ERROR envelope with 404 (kind =
  platform.error, code NOT_FOUND) — matches existing contract.
- SSE replays filtered events (metadata.execution_id == id), then emits end
  event; does not block the orchestrator. Phase 7 will add a proper streaming
  consumer.
- Fixed a duplicate header bug in frontend/app/platform/layout.tsx (removed
  nested titlebar from layout.tsx — now only in platform-providers.tsx).
- Added /platform/* routes to the production build (verified: 4 verification
  routes now prerender).

## Validation performed

- Python smoke (PYTHONPATH=backend, fastapi TestClient):
  - POST /verification/run {capability_id} -> 200, kind platform.verification_run_result
  - POST /verification/run/affected -> 200
  - POST /verification/run/full -> 200
  - POST /verification/run/group {group} -> 200
  - GET /verification/runs/recent -> 200, kind platform.verification_runs_recent, count 20
  - POST /tasks/{unknown}/cancel -> 404, error code NOT_FOUND
  - POST /tasks/{real}/cancel -> 200, kind platform.task_cancel_result, cancelled=true
  - GET /executions/{id}/stream -> 200, content-type event-stream
  - Frontend: npx next build -> Compiled successfully, 19 routes (including 4 verification routes)

## Blockers

None. Band B Phase 6 is implemented; awaiting final E2E evidence bundle and push.

## Next

- Generate runtime/generated/m9-c57/phase-06/file-manifest.json.
- Push with Gate-6 summary (CERTIFIABLE pending final backend/integration + E2E green).
