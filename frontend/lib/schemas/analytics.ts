import { z } from 'zod'

// Analytics Schema
//
// M10-A3: every field below is validated as a *rupee* amount unless its name
// makes it a count. The monetary ones were declared `z.number().int()`, but a
// rupee average is fractional by construction: `GET /api/v1/analytics` returns
// `"avg_monthly": 9974.17` and a per-month `"average": 9974.17`, so safeParse
// failed with 7 issues (1 + one per trend point) and the dashboard analytics
// band rendered "Unable to load data / Try again" against a 200 response.
//
// The counts keep `.int()` — a fractional transaction count is meaningless, so
// that constraint is still doing its job. Only the false constraints on
// monetary magnitudes are removed; the fields stay required and typed.

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
  amount: z.number(),
  count: z.number().int(),
})

const SpendingTrendPointSchema = z.object({
  month: z.string(),
  amount: z.number(),
  average: z.number(),
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
  amount: z.number(),
  date: z.string(),
  bank: z.string(),
})

export const AnalyticsSchema = z.object({
  highest_month: z.string(),
  highest_month_amount: z.string(),
  avg_monthly: z.number(),
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