import { z } from 'zod'

// Behavior Score Schema — aligned with WellnessScoreResponse DTO
// Note: Backend serialises Decimal fields as strings; we coerce to numbers.
// The score is expressed in basis points (0-10000 == 0-100%), matching the
// canonical contract documented in types/behaviour-view-model.ts.
export const BehaviorScoreSchema = z.object({
  score: z.coerce.number().min(0).max(10000),
  financial_health_score: z.coerce.number().min(0).max(100).optional(),
  band: z.enum(['Excellent', 'Healthy', 'Developing', 'Risk', 'Critical']),
  components: z.record(z.string(), z.coerce.number().min(0).max(100)),
  risk_flags: z.record(z.string(), z.boolean()).optional(),
  summary: z.string().optional(),
  snapshot_date: z.string(),
  version: z.number().int(),
})

export type BehaviorScore = z.infer<typeof BehaviorScoreSchema>