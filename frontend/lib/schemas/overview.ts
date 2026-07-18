import { z } from 'zod'

// Overview Schema
const BehavioralInsightSchema = z.object({
  title: z.string(),
  description: z.string(),
  severity: z.enum(['warning', 'positive', 'neutral']),
  icon: z.string(),
})

const MonthlyChartPointSchema = z.object({
  month: z.string(),
  amount: z.number().int(), // In paise (canonical)
})

const CategoryChartPointSchema = z.object({
  name: z.string(),
  value: z.number().int(), // In paise (canonical)
})

export const OverviewSchema = z.object({
  total_spend: z.number().int(),
  total_spend_display: z.string(),
  this_month: z.number().int(),
  this_month_display: z.string(),
  last_month: z.number().int(),
  last_month_display: z.string(),
  month_change: z.string(),
  transaction_count: z.number().int(),
  card_count: z.number().int(),
  months_of_data: z.number().int(),
  monthly_average: z.number().int(),
  monthly_average_display: z.string(),
  above_below_avg: z.string(),
  above_avg_is_bad: z.boolean(),
  monthly_chart: z.array(MonthlyChartPointSchema),
  category_chart: z.array(CategoryChartPointSchema),
  behavioral_insights: z.array(BehavioralInsightSchema),
})

export type Overview = z.infer<typeof OverviewSchema>