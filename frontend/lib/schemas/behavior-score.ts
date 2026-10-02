import { z } from 'zod'

// Behavior Score Schema — aligned with WellnessScoreResponse DTO
// Note: Backend serialises Decimal fields as strings; we coerce to numbers.
//
// SCALE — M10-A3: this file previously claimed the score is "in basis points
// (0-10000 == 0-100%)" and validated `score` against `.max(10000)`. The
// authority uses a plain 0-100 magnitude:
//   * `WellnessScoreResponse.score` is documented "Wellness score between 0 and
//     100" (backend/src/models/behaviour.py:31)
//   * it is produced by `wellness_score * 100` clamped to `[0, 100]`
//     (backend/src/engines/behaviour_engine/wellness.py:83-85)
//   * `classify_wellness_band` then classifies that same 0-100 value, which is
//     why a score of 100 comes back as band "Excellent"
// A live response is `{"score": "100", "band": "Excellent", ...}`. Validating
// 0-100 is the authoritative range and is tighter than the 0-10000 that was
// there before, so this is a correction of a wrong assumption rather than a
// relaxed check. `components/behaviour/behaviour-score.tsx` and
// `components/dashboard/behavior-score-card.tsx` had each compensated for the
// wrong assumption in their own way, which is how the same payload rendered as
// "1.0%" on /behaviour and "76" on /dashboard.
export const BehaviorScoreSchema = z.object({
  score: z.coerce.number().min(0).max(100),
  // `financial_health_score` is a separate 0-100 field from the dashboard
  // summary, not a basis-point restatement of `score`.
  financial_health_score: z.coerce.number().min(0).max(100).optional(),
  band: z.enum(['Excellent', 'Healthy', 'Developing', 'Risk', 'Critical']),
  components: z.record(z.string(), z.coerce.number().min(0).max(100)),
  risk_flags: z.record(z.string(), z.boolean()).optional(),
  summary: z.string().optional(),
  snapshot_date: z.string(),
  version: z.number().int(),
})

export type BehaviorScore = z.infer<typeof BehaviorScoreSchema>