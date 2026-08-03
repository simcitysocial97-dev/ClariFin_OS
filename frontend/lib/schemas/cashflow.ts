import { z } from 'zod'

export const CashflowMonthSchema = z.object({
  month_key: z.string().regex(/^\d{4}-\d{2}$/),
  month_label: z.string(),
  income_paise: z.number().int().nonnegative(),
  expense_paise: z.number().int().nonnegative(),
  net_paise: z.number().int(),
  transaction_count: z.number().int().nonnegative(),
})

export const CashflowResponseSchema = z.object({
  months: z.array(CashflowMonthSchema),
  period_months: z.number().int(),
  total_income_paise: z.number().int(),
  total_expense_paise: z.number().int(),
  total_net_paise: z.number().int(),
  transaction_count: z.number().int(),
})

export type CashflowMonth = z.infer<typeof CashflowMonthSchema>
export type CashflowResponse = z.infer<typeof CashflowResponseSchema>
