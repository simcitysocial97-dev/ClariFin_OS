import { z } from 'zod'

// Behavior Score Schema — aligned with WellnessScoreResponse DTO
// Note: Backend serialises Decimal fields as strings; we coerce to numbers.
//
// SCALE — M10-A3. This field required three separate rounds of evidence, and
// the two positions the frontend had held were both wrong.
//
// What the documentation says:
//   * `WellnessScoreResponse.score` is documented "Wellness score between 0 and
//     100" (backend/src/models/behaviour.py:31)
//   * `compute_wellness_score` returns `wellness_score * 100` clamped to
//     `[0, 100]` (backend/src/engines/behaviour_engine/wellness.py:88-89)
//
// What the API actually returns:
//   * with no transaction data (the auto-compute fallback,
//     behaviour_service.py:276-289): `{"score": "100", "band": "Excellent"}`
//   * with real data: `{"score": "7561.45", ...}`
//
// Why: `compute_financial_profile` stores
// `wellness_score_bps = int(wellness_score * 10000)`
// (backend/src/services/behaviour_service.py:217) — multiplying an ALREADY
// 0-100 value by 10000 again — and `get_wellness_score` reads that column
// straight into the response without dividing (behaviour_service.py:328-333,
// 548). The response is therefore double-scaled, and
// `classify_wellness_band` (which thresholds at 90/75/50/25) consequently
// returns "Excellent" for any value at or above 90, including 7561.45.
//
// This is a BACKEND defect, not a frontend contract. The frontend's two prior
// beliefs were each a symptom: the schema claimed basis points
// (`0-10000 == 0-100%`, `.max(10000)`) and `behaviour-score.tsx` divided by 100
// against 800/600 thresholds, which is how one payload rendered as "1.0%" on
// /behaviour and as a bare number on /dashboard.
//
// The validator accepts the authority's real output. It does NOT rescale: the
// console must not invent a corrected value, so `behaviour-score.tsx` renders
// the score as stated and flags it when it falls outside the documented 0-100
// range. Upper-bound enforcement belongs to the backend fix.
//
// `components` and `financial_health_score` ARE genuinely 0-100
// (behaviour_service.py:292 documents the components as "already in 0-100
// range"), so their bounds are retained and are not affected by the double
// scaling.
export const BehaviorScoreSchema = z.object({
  /**
   * The wellness score as the authority states it.
   *
   * No upper bound: the authority is observed emitting 7561.45, and a bound
   * here would reject a valid HTTP 200 and blank the whole /behaviour
   * workspace. `WELLNESS_SCORE_DOCUMENTED_MAX` below is the documented range,
   * used by the UI to flag an out-of-contract value rather than to reject it.
   */
  score: z.coerce.number().min(0),
  /** Documented upper bound of `WellnessScoreResponse.score`. */
  financial_health_score: z.coerce.number().min(0).max(100).optional(),
  band: z.enum(['Excellent', 'Healthy', 'Developing', 'Risk', 'Critical']),
  components: z.record(z.string(), z.coerce.number().min(0).max(100)),
  risk_flags: z.record(z.string(), z.boolean()).optional(),
  summary: z.string().optional(),
  snapshot_date: z.string(),
  version: z.number().int(),
})

/**
 * The upper bound `WellnessScoreResponse.score` is documented to respect.
 *
 * Exported so the UI can distinguish "the authority reported a score" from
 * "the authority reported a score outside its own contract" without
 * duplicating the number or re-deriving a corrected one.
 */
export const WELLNESS_SCORE_DOCUMENTED_MAX = 100

export type BehaviorScore = z.infer<typeof BehaviorScoreSchema>
