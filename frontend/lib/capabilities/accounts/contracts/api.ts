/**
 * Accounts API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 */

import { z } from 'zod'

/**
 * Account schema - matches backend /api/accounts/manage response
 */
export const AccountSchema = z.object({
  id: z.string(),
  name: z.string(),
  bank: z.string(),
  account_type: z.string(),
  balance_paise: z.number().int(),
  account_number_last4: z.string().nullable(),
  is_active: z.number(),
  notes: z.string().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
})

/**
 * Accounts response schema - matches backend /api/accounts/manage
 */
export const AccountsResponseSchema = z.object({
  accounts: z.array(AccountSchema),
  total: z.number().int(),
})

export type AccountDto = z.infer<typeof AccountSchema>
export type AccountsResponseDto = z.infer<typeof AccountsResponseSchema>