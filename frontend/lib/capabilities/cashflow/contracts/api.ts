/**
 * Cashflow API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 */

import { z } from 'zod'

/**
 * Cashflow month schema - matches backend response
 */
export const CashflowMonthSchema = z.object({
  month_key: z.string().regex(/^\d{4}-\d{2}$/),
  month_label: z.string(),
  income_paise: z.number().int().nonnegative(),
  expense_paise: z.number().int().nonnegative(),
  net_paise: z.number().int(),
  transaction_count: z.number().int().nonnegative(),
})

/**
 * Cashflow response schema - matches backend /api/cashflow/monthly
 */
export const CashflowResponseSchema = z.object({
  months: z.array(CashflowMonthSchema),
  period_months: z.number().int(),
  total_income_paise: z.number().int(),
  total_expense_paise: z.number().int(),
  total_net_paise: z.number().int(),
})

export type CashflowMonthDto = z.infer<typeof CashflowMonthSchema>
export type CashflowResponseDto = z.infer<typeof CashflowResponseSchema>