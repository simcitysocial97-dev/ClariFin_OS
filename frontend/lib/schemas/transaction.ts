import { z } from 'zod'

export const TransactionSchema = z.object({
  id: z.union([z.string(), z.number()]),
  date: z.string(),
  description: z.string(),
  amount_paise: z.number().int(),
  type: z.enum(['debit', 'credit']),
  category: z.string(),
  bank: z.string(),
  member: z.string().nullable().optional(),
})

export const TransactionsResponseSchema = z.object({
  transactions: z.array(TransactionSchema),
  total: z.number().int(),
})

export type Transaction = z.infer<typeof TransactionSchema>
export type TransactionsResponse = z.infer<typeof TransactionsResponseSchema>
