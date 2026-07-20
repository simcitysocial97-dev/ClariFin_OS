/**
 * Evidence Module - Stage 3 Transaction Intelligence Workspace
 *
 * Public API exports for the evidence system.
 */

export { useEvidence } from './use-evidence';
export {
  createCategorizationEvidence,
  createImportEvidence,
  createAdjustmentEvidence,
  createBalanceEvidence,
  createReconciliationEvidence,
} from './factories';
export type {
  EvidenceType,
  EvidenceSource,
  EvidenceItem,
  EvidenceState,
  EvidenceAction,
  EvidenceActionType,
  EvidenceSummary,
} from './types';

// ===== Stage 7.5 Runtime Consolidation =====
export { EvidenceRuntime, evidenceRuntime } from './evidence-runtime';