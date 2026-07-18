import { z } from 'zod'

// Dashboard Metrics Schema
export const DashboardMetricsSchema = z.object({
  // Canonical paise fields
  net_cash_flow_paise: z.number().int(),
  total_income_paise: z.number().int(),
  total_expenses_paise: z.number().int(),
  // Deprecated rupees field (for backward compatibility)
  net_cash_flow_rupees: z.number().optional(),
  // Other fields
  savings_rate: z.number().min(0).max(1),
  emi_paise: z.number().int(),
  emi_ratio: z.number().min(0).max(1),
  buffer_days: z.number().int(),
  financial_health_score: z.number().int().min(0).max(100),
  seven_day_trend: z.number(),
  category_drift_alert: z.string().nullable(),
  recent_transactions: z.array(z.any()),
})

export type DashboardMetrics = z.infer<typeof DashboardMetricsSchema>