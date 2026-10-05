import { z } from 'zod'

// Behavior Score Schema — aligned with WellnessScoreResponse DTO
// Note: Backend serialises Decimal fields as strings; we coerce to numbers.
//
// SCALE — the canonical unit is 0-100, and it is now enforced end to end.
//
// What the documentation says:
//   * `WellnessScoreResponse.score` is "between 0 and 100"
//     (backend/src/models/behaviour.py:31)
//   * `compute_wellness_score` returns `wellness_score * 100` clamped to
//     `[0, 100]` (backend/src/engines/behaviour_engine/wellness.py:88-89)
//   * `classify_wellness_band` thresholds at 90/75/50/25
//   * `tests/invariants/behaviour.py::assert_behaviour_score_valid` asserts
//     `[0, 100]`
//   * the no-data fallback returns `Decimal("100")` / "Excellent"
//   * every reader of `snapshot["wellness_score"]` is 0-100, including
//     `_generate_alerts` (thresholds 25/50)
//
// What the API used to return: with real data, `{"score": "7561.45", ...}`.
// The write layer stored `wellness_score_bps = int(wellness_score * 10000)`
// on a value that is ALREADY 0-100, so the basis-point column held
// 0-1,000,000 instead of 0-10,000; the repository read model then multiplied
// by 100 again, so a real 87.5449 was served as 8754.4900 and its band read
// "Excellent" for every household.
//
// M11 fixed that at the authoritative layer (the write), because the read
// model was already correct: `behaviour_service.py` now stores
// `int(wellness_score * 100)` and `run_migrations` rescales persisted rows
// above 10000. Every sibling column written in the same snapshot
// (`cashflow_stability_score_bps` = 8230, `resilience_index_bps` = 9860)
// was already a true basis-point value in 0-10,000 — only wellness was scaled
// twice.
//
// Because the authority now honours its own documented range, the bound is
// enforced here rather than left open. M10 deliberately did NOT enforce it:
// at the time the backend emitted 7561.45, and a bound would have rejected a
// valid HTTP 200 and blanked the whole /behaviour workspace. That reasoning is
// no longer true, so this schema is restored to the documented contract.
//
// `components` and `financial_health_score` were always genuinely 0-100 and are
// unchanged.

/**
 * The upper bound `WellnessScoreResponse.score` is documented to respect.
 *
 * Exported so the UI can distinguish "the authority reported a score" from
 * "the authority reported a score outside its own contract" without
 * duplicating the number or re-deriving a corrected one. The backend no longer
 * violates it, so the out-of-range branch should never be reached; it is kept
 * because a display layer that silently clamps a bad number would hide a
 * recurrence of the defect this bound exists to catch.
 */
export const WELLNESS_SCORE_DOCUMENTED_MAX = 100

export const BehaviorScoreSchema = z.object({
  /**
   * The wellness score as the authority states it: 0-100.
   */
  score: z.coerce.number().min(0).max(WELLNESS_SCORE_DOCUMENTED_MAX),
  /** Documented upper bound of `WellnessScoreResponse.score`. */
  financial_health_score: z.coerce.number().min(0).max(100).optional(),
  band: z.enum(['Excellent', 'Healthy', 'Developing', 'Risk', 'Critical']),
  components: z.record(z.string(), z.coerce.number().min(0).max(100)),
  risk_flags: z.record(z.string(), z.boolean()).optional(),
  summary: z.string().optional(),
  snapshot_date: z.string(),
  version: z.number().int(),
})

export type BehaviorScore = z.infer<typeof BehaviorScoreSchema>
