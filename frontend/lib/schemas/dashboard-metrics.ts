import { z } from 'zod'

// Dashboard Metrics Schema
export const DashboardMetricsSchema = z.object({
  // Canonical paise fields
  net_cash_flow_paise: z.number().int(),
  total_income_paise: z.number().int(),
  total_expenses_paise: z.number().int(),
  emi_paise: z.number().int(),
  // Rates as ratios (0-1) per backend DTO spec
  savings_rate: z.number().min(0),
  emi_ratio: z.number().min(0),
  buffer_days: z.number().int(),
  // Health score from behaviour analysis (0-100), nullable as per DTO
  financial_health_score: z.number().min(0).max(100).nullable().optional(),
  recent_transactions: z.array(z.any()).optional(),
  // Deprecated nullable field (backend returns null, kept for contract parity)
  net_cash_flow_rupees: z.number().nullable().optional(),
})

export type DashboardMetrics = z.infer<typeof DashboardMetricsSchema>