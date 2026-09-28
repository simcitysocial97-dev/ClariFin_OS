import { z } from 'zod'

// Cashflow Monthly DTO - matches backend CashflowMonthlyDTO
export const CashflowMonthSchema = z.object({
  month: z.string(),
  income_paise: z.number().int().nonnegative(),
  expenses_paise: z.number().int().nonnegative(),
  net_paise: z.number().int(),
  transaction_count: z.number().int().nonnegative(),
})

// Cashflow Monthly Response - matches backend CashflowMonthlyResponse
export const CashflowResponseSchema = z.object({
  months: z.array(CashflowMonthSchema),
  total_count: z.number().int().nonnegative(),
})

export type CashflowMonth = z.infer<typeof CashflowMonthSchema>
export type CashflowResponse = z.infer<typeof CashflowResponseSchema>
