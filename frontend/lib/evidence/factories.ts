/**
 * Evidence Factories - Stage 3 Transaction Intelligence Workspace
 *
 * Factory functions for creating evidence items of specific types.
 */

import type { EvidenceItem, EvidenceSource } from './types';

/**
 * Create evidence for categorization
 */
export function createCategorizationEvidence(
  summary: string,
  source: EvidenceSource,
  confidence: number
): EvidenceItem {
  return {
    type: 'categorization',
    summary,
    source,
    confidence,
  };
}

/**
 * Create evidence for import
 */
export function createImportEvidence(
  summary: string,
  source: EvidenceSource,
  confidence?: number
): EvidenceItem {
  return {
    type: 'import',
    summary,
    source,
    confidence,
  };
}

/**
 * Create evidence for adjustment
 */
export function createAdjustmentEvidence(
  summary: string,
  source: EvidenceSource,
  confidence?: number
): EvidenceItem {
  return {
    type: 'adjustment',
    summary,
    source,
    confidence,
  };
}

/**
 * Create evidence for balance
 */
export function createBalanceEvidence(
  summary: string,
  source: EvidenceSource,
  confidence?: number
): EvidenceItem {
  return {
    type: 'balance',
    summary,
    source,
    confidence,
  };
}

/**
 * Create evidence for reconciliation
 */
export function createReconciliationEvidence(
  summary: string,
  source: EvidenceSource,
  confidence?: number
): EvidenceItem {
  return {
    type: 'reconciliation',
    summary,
    source,
    confidence,
  };
}