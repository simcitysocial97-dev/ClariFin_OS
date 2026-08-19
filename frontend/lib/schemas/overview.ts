import { z } from 'zod'

// Overview Schema
const BehavioralInsightSchema = z.object({
  title: z.string(),
  description: z.string(),
  severity: z.enum(['warning', 'positive', 'neutral', 'info']),
  icon: z.string(),
})

const MonthlyChartPointSchema = z.object({
  month: z.string(),
  amount: z.number(), // Can be float from API, represents paise
})

const CategoryChartPointSchema = z.object({
  name: z.string(),
  value: z.number(), // Can be float from API, represents paise
})

const BankChartPointSchema = z.object({
  bank: z.string(),
  amount: z.number(),
})

const RecentTransactionSchema = z.object({
  id: z.union([z.number(), z.string()]),
  sequence_num: z.number().optional(),
  date: z.string(),
  description: z.string(),
  amount_paise: z.number().optional(),
  debit: z.number().optional(),
  credit: z.number().optional(),
  type: z.string(),
  category: z.string(),
  subcategory: z.string().nullable().optional(),
  raw_description: z.string().nullable().optional(),
  member: z.string(),
  bank: z.string(),
  statement_file: z.string().optional(),
  statement_period_from: z.string().optional(),
  statement_period_to: z.string().optional(),
  parsed_date: z.string().optional(),
  date_display: z.string().optional(),
  month_key: z.string().optional(),
  weekday: z.string().optional(),
  amount_display: z.string().optional(),
  amount: z.number().optional(),
  description_display: z.string().optional(),
  is_large: z.boolean().optional(),
})

export const OverviewSchema = z.object({
  total_spend: z.number(),
  total_spend_display: z.string(),
  this_month: z.number(),
  this_month_display: z.string(),
  last_month: z.number(),
  last_month_display: z.string(),
  month_change: z.string(),
  transaction_count: z.number(),
  card_count: z.number(),
  months_of_data: z.number(),
  monthly_average: z.number(),
  monthly_average_display: z.string(),
  above_below_avg: z.string(),
  above_avg_is_bad: z.boolean(),
  monthly_chart: z.array(MonthlyChartPointSchema),
  category_chart: z.array(CategoryChartPointSchema),
  bank_chart: z.array(BankChartPointSchema).optional(),
  recent_transactions: z.array(RecentTransactionSchema).optional(),
  behavioral_insights: z.array(BehavioralInsightSchema),
})

export type Overview = z.infer<typeof OverviewSchema>