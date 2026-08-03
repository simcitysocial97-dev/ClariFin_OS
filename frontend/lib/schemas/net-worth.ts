import { z } from 'zod'

// Net Worth Breakdown Item Schema
const NetWorthBreakdownItemSchema = z.object({
  id: z.string(),
  name: z.string(),
  type: z.string(),
  balance_paise: z.number().int(),
  percentage: z.number(),
  contribution_paise: z.number().int(),
})

// Net Worth Composition Schema
const NetWorthCompositionSchema = z.object({
  total_assets_paise: z.number().int(),
  total_liabilities_paise: z.number().int(),
  asset_breakdown: z.array(NetWorthBreakdownItemSchema),
  liability_breakdown: z.array(NetWorthBreakdownItemSchema),
})

// Net Worth Trend Schema
const NetWorthTrendSchema = z.object({
  direction: z.enum(['up', 'down', 'flat']),
  percentage_change: z.number(),
  period: z.string(),
})

// Net Worth Insight Schema
const NetWorthInsightSchema = z.object({
  type: z.enum(['positive', 'warning', 'info', 'alert']),
  severity: z.enum(['low', 'medium', 'high']),
  message: z.string(),
  action_url: z.string().optional(),
})

// Net Worth Evidence Chain Schema (simplified)
const NetWorthEvidenceChainSchema = z.object({
  summary: z.string(),
  confidence_score: z.number().min(0).max(100),
}).optional()

// Net Worth Schema
export const NetWorthSchema = z.object({
  total_net_worth_paise: z.number().int(),
  total_assets_paise: z.number().int(),
  total_liabilities_paise: z.number().int(),
  composition: NetWorthCompositionSchema,
  trend: NetWorthTrendSchema.optional(),
  insights: z.array(NetWorthInsightSchema),
  evidence_chain: NetWorthEvidenceChainSchema,
})

// Types
export type NetWorth = z.infer<typeof NetWorthSchema>
export type NetWorthBreakdownItem = z.infer<typeof NetWorthBreakdownItemSchema>
export type NetWorthComposition = z.infer<typeof NetWorthCompositionSchema>
export type NetWorthTrend = z.infer<typeof NetWorthTrendSchema>
export type NetWorthInsight = z.infer<typeof NetWorthInsightSchema>