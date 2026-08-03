import { z } from 'zod'

// Dashboard Metrics Schema
export const DashboardMetricsSchema = z.object({
  // Canonical paise fields
  net_cash_flow_paise: z.number().int(),
  total_income_paise: z.number().int(),
  total_expenses_paise: z.number().int(),
  emi_paise: z.number().int(),
  // Other fields
  savings_rate: z.number().min(0).max(1),
  emi_ratio: z.number().min(0).max(1),
  buffer_days: z.number().int(),
  financial_health_score: z.number().min(0).max(100),
  recent_transactions: z.array(z.any()).optional(),
  // Deprecated rupees field (for backward compatibility)
  net_cash_flow_rupees: z.number().optional(),
})

export type DashboardMetrics = z.infer<typeof DashboardMetricsSchema>