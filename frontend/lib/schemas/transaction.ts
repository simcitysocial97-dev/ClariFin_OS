import { z } from 'zod'

// ===== Money Schema (matches backend MoneyDTO) =====
export const MoneySchema = z.object({
  paise: z.number().int(),
  rupees: z.number(),
})

export const TransactionSchema = z.object({
  id: z.union([z.string(), z.number()]),
  date: z.string(),
  description: z.string(),
  amount: MoneySchema.optional(),
  type: z.enum(['debit', 'credit']),
  category: z.string(),
  subcategory: z.string().nullable().optional(),
  bank: z.string(),
  member: z.string().nullable().optional(),
  statement_file: z.string().nullable().optional(),
  // Deprecated fields for backward compatibility
  amount_paise: z.number().int().optional(),
  amount_rupees: z.number().optional(),
})

export const TransactionsResponseSchema = z.object({
  transactions: z.array(TransactionSchema),
  total: z.number().int(),
  limit: z.number().int().optional(),
  offset: z.number().int().optional(),
})

export type Transaction = z.infer<typeof TransactionSchema>
export type TransactionsResponse = z.infer<typeof TransactionsResponseSchema>
export type Money = z.infer<typeof MoneySchema>