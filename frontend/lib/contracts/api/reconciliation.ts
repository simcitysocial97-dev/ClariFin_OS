/**
 * Reconciliation API Contract - Zod schemas for DTO validation
 *
 * These schemas validate raw API responses before mapping to ViewModels.
 * SourceReference schema mirrors backend model exactly.
 */

import { z } from 'zod'
import {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
} from '@/lib/explainability/contracts/explainability.zod'

// Re-export shared schemas from explainability (they are canonical)
export {
  SourceReferenceSchema,
  EvidenceSchema,
  CalculationStepSchema,
  ConfidenceSchema,
  ExplanationSchema,
}

// Reconciliation match schema
const ReconciliationMatchSchema = z.object({
  id: z.number().int().nullable(),
  debit_txn_id: z.number().int(),
  credit_txn_id: z.number().int(),
  debit_account_id: z.string(),
  credit_account_id: z.string(),
  amount_paise: z.number().int(),
  date_diff_days: z.number().int(),
  match_confidence: z.number(),
  match_type: z.string(),
  status: z.string().nullable(),
  created_at: z.string().nullable(),
  confirmed_at: z.string().nullable(),
  // Transaction details
  debit_date: z.string().nullable(),
  debit_date_iso: z.string().nullable(),
  debit_description: z.string().nullable(),
  debit_amount_paise: z.number().int().nullable(),
  debit_bank: z.string().nullable(),
  credit_date: z.string().nullable(),
  credit_date_iso: z.string().nullable(),
  credit_description: z.string().nullable(),
  credit_amount_paise: z.number().int().nullable(),
  credit_bank: z.string().nullable(),
})

/**
 * Reconciliation response from /api/reconciliations/scan
 */
export const ReconciliationResponseSchema = z.object({
  matches: z.array(ReconciliationMatchSchema),
  count: z.number().int(),
  is_partial: z.boolean(),
  partial_reason: z.string().nullable(),
  last_updated: z.string().nullable(),
  explanation: ExplanationSchema.optional(),
})

export type ReconciliationMatchDto = z.infer<typeof ReconciliationMatchSchema>
export type ReconciliationDto = z.infer<typeof ReconciliationResponseSchema>