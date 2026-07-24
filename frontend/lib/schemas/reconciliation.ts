import { z } from 'zod'

// Reconciliation Schema
export const TransactionDetailSchema = z.object({
  id: z.number().int(),
  date: z.string(),
  date_iso: z.string(),
  description: z.string(),
  amount_paise: z.number().int(),
  type: z.enum(['debit', 'credit']),
  bank: z.string(),
})

export const ReconciliationMatchSchema = z.object({
  id: z.number().int(),
  debit_txn_id: z.number().int(),
  credit_txn_id: z.number().int(),
  debit_account_id: z.string(),
  credit_account_id: z.string(),
  amount_paise: z.number().int(), // In paise (canonical)
  date_diff_days: z.number().int(),
  match_confidence_bps: z.number().int().min(0).max(10000), // In basis points (0-10000)
  match_type: z.enum(['exact', 'window', 'fuzzy', 'manual']),
  status: z.enum(['pending', 'confirmed', 'rejected']),
  created_at: z.string(),
  confirmed_at: z.string().nullable(),
  // Transaction details from join
  debit_date: z.string(),
  debit_date_iso: z.string(),
  debit_description: z.string(),
  debit_amount_paise: z.number().int(),
  debit_bank: z.string(),
  credit_date: z.string(),
  credit_date_iso: z.string(),
  credit_description: z.string(),
  credit_amount_paise: z.number().int(),
  credit_bank: z.string(),
})

export const ReconciliationsDataSchema = z.object({
  reconciliations: z.array(ReconciliationMatchSchema),
})

export type TransactionDetail = z.infer<typeof TransactionDetailSchema>
export type ReconciliationMatch = z.infer<typeof ReconciliationMatchSchema>
export type ReconciliationsData = z.infer<typeof ReconciliationsDataSchema>