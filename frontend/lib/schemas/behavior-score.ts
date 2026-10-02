import { z } from 'zod'

// Behavior Score Schema — aligned with WellnessScoreResponse DTO
// Note: Backend serialises Decimal fields as strings; we coerce to numbers.
//
// SCALE — M10-A3 follow-up. A3 tightened this to `.max(100)` on the reasoning
// that the authority is a 0-100 magnitude, and that reasoning is CORRECT:
// `WellnessScoreResponse.score` is documented "between 0 and 100"
// (backend/src/models/behaviour.py:31), `wellness.py:83-86` clamps to [0,100],
// and `classify_wellness_band` classifies on 0-100.
//
// It was reverted because the backend does not currently honour that contract.
// `BehaviourService.get_winless_score` returns the RAW stored value
// (`snapshot["wellness_score"]`) with no normalisation, and the live response is
//
//     {"score": "7561.45", "band": "Excellent", ...}
//
// 7561.45 / 100 = 75.61, i.e. the stored snapshot is double-scaled. Rejecting it
// here did not fix the scale, it just turned the whole /behaviour page into an
// error state.
//
// The scale defect belongs to the backend, which owns the number. Normalising
// in the frontend would be frontend money arithmetic and is forbidden. Until
// the backend is corrected the permissive range is restored so the page renders
// real data; the defect is filed as a MAJOR backlog item with this evidence.
export const BehaviorScoreSchema = z.object({
  score: z.coerce.number().min(0).max(10000),
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