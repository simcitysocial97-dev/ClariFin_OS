import { z } from 'zod'

// Analytics Schema
const TopMerchantSchema = z.object({
  merchant: z.string(),
  amount_display: z.string(),
  count: z.number().int(),
})

const RecurringChargeSchema = z.object({
  description: z.string(),
  frequency: z.number().int(),
  avg_display: z.string(),
  annual_display: z.string(),
})

const DayOfWeekPointSchema = z.object({
  day: z.string(),
  amount: z.number().int(),
  count: z.number().int(),
})

const SpendingTrendPointSchema = z.object({
  month: z.string(),
  amount: z.number().int(),
  average: z.number().int(),
})

const LargestTransactionSchema = z.object({
  rank: z.number().int(),
  date_display: z.string(),
  description: z.string(),
  amount_display: z.string(),
  bank: z.string(),
})

const BiggestTransactionSchema = z.object({
  description: z.string(),
  amount: z.number().int(),
  date: z.string(),
  bank: z.string(),
})

export const AnalyticsSchema = z.object({
  highest_month: z.string(),
  highest_month_amount: z.string(),
  avg_monthly: z.number().int(),
  avg_monthly_display: z.string(),
  biggest_transaction: BiggestTransactionSchema.nullable(),
  unique_merchants: z.number().int(),
  spending_trend: z.array(SpendingTrendPointSchema),
  day_of_week: z.array(DayOfWeekPointSchema),
  top_merchants: z.array(TopMerchantSchema),
  recurring_charges: z.array(RecurringChargeSchema),
  largest_transactions: z.array(LargestTransactionSchema),
})

export type Analytics = z.infer<typeof AnalyticsSchema>