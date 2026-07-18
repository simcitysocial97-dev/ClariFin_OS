/**
 * Reconciliation Mapper - Pure transformation from DTO to Model
 *
 * This mapper transforms raw API responses to domain-friendly models.
 * It is deterministic, side-effect free, and fully typed.
 */

import type { ReconciliationDto, ReconciliationMatchDto } from '../contracts/api/reconciliation'
import type { ReconciliationModel, ReconciliationMatchModel } from '../models/reconciliation'

/**
 * Map ReconciliationMatch DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 */
export function mapReconciliationMatchToModel(dto: ReconciliationMatchDto): ReconciliationMatchModel {
  return {
    id: dto.id,
    debitTxnId: dto.debit_txn_id,
    creditTxnId: dto.credit_txn_id,
    debitAccountId: dto.debit_account_id,
    creditAccountId: dto.credit_account_id,
    amountPaise: dto.amount_paise,
    dateDiffDays: dto.date_diff_days,
    matchConfidence: dto.match_confidence,
    matchType: dto.match_type,
    status: dto.status,
    createdAt: dto.created_at,
    confirmedAt: dto.confirmed_at,
    // Transaction details
    debitDate: dto.debit_date,
    debitDateIso: dto.debit_date_iso,
    debitDescription: dto.debit_description,
    debitAmountPaise: dto.debit_amount_paise,
    debitBank: dto.debit_bank,
    creditDate: dto.credit_date,
    creditDateIso: dto.credit_date_iso,
    creditDescription: dto.credit_description,
    creditAmountPaise: dto.credit_amount_paise,
    creditBank: dto.credit_bank,
  }
}

/**
 * Map Reconciliation DTO to Model
 *
 * Transformation rules:
 * - Rename fields to camelCase for consistency
 * - Preserve explanation unchanged
 */
export function mapReconciliationToModel(dto: ReconciliationDto): ReconciliationModel {
  return {
    matches: dto.matches.map(mapReconciliationMatchToModel),
    count: dto.count,
    isPartial: dto.is_partial,
    partialReason: dto.partial_reason,
    lastUpdated: dto.last_updated,
    explanation: dto.explanation ?? null,
  }
}

// Re-export types for convenience
export type { ReconciliationModel, ReconciliationMatchModel }