import { z } from 'zod'

// Behavior Score Schema
export const BehaviorScoreSchema = z.object({
  score: z.number().min(0).max(100),
  financial_health_score: z.number().min(0).max(100).optional(),
  band: z.enum(["Excellent", "Healthy", "Developing", "Risk", "Critical"]),
  components: z.record(z.string(), z.number().min(0).max(100)),
  risk_flags: z.record(z.string(), z.boolean()).optional(),
  summary: z.string().optional(),
  snapshot_date: z.string(),
  version: z.number().int(),
})

export type BehaviorScore = z.infer<typeof BehaviorScoreSchema>