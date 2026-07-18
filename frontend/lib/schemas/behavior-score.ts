import { z } from 'zod'

// Behavior Score Schema
const BehaviorComponentsSchema = z.object({
  savings_discipline: z.number().int().min(0).max(100),
  habit_stability: z.number().int().min(0).max(100),
  impulsivity: z.number().int().min(0).max(100),
  financial_stress: z.number().int().min(0).max(100),
  loss_aversion: z.number().int().min(0).max(100),
})

const IndiaRiskFlagsSchema = z.object({
  upi_micro_spend_flag: z.boolean(),
  gambling_flag: z.boolean(),
  loan_app_pattern_flag: z.boolean(),
  loan_credit_count: z.number().int(),
  emi_ratio: z.number(),
  monthly_emi_total: z.number().int(),
})

const RiskFlagsSchema = z.object({
  india_specific: IndiaRiskFlagsSchema,
  high_impulsivity: z.boolean(),
  high_stress: z.boolean(),
  low_savings: z.boolean(),
})

export const BehaviorScoreSchema = z.object({
  financial_health_score: z.number().int().min(0).max(100),
  confidence: z.number().int().min(0).max(100),
  components: BehaviorComponentsSchema,
  risk_flags: RiskFlagsSchema,
  summary: z.string(),
})

export type BehaviorScore = z.infer<typeof BehaviorScoreSchema>