/**
 * Evidence Types - Stage 3 Transaction Intelligence Workspace
 *
 * Type definitions for transaction evidence system.
 * Evidence provides explainability and traceability for transaction data.
 */

// Evidence type enumeration
export type EvidenceType = 'categorization' | 'import' | 'adjustment' | 'balance' | 'reconciliation';

// Evidence source reference
export interface EvidenceSource {
  /** File ID for import evidence */
  file_id?: string;
  /** Row number in source file */
  row_number?: number;
  /** Extraction ID for PDF parsing */
  extraction_id?: string;
  /** API endpoint that provided this evidence */
  api_endpoint?: string;
}

// Evidence item (re-exported from transaction-view-model for convenience)
export interface EvidenceItem {
  /** Type of evidence */
  type: EvidenceType;
  /** Human-readable summary of the evidence */
  summary: string;
  /** Source reference for the evidence */
  source: EvidenceSource;
  /** Confidence score (0-100) if applicable */
  confidence?: number;
}

// Evidence drawer state
export interface EvidenceState {
  /** Whether the evidence drawer is open */
  isOpen: boolean;
  /** Currently selected transaction ID for evidence view */
  transactionId: string | null;
  /** Evidence items for the selected transaction */
  evidence: EvidenceItem[];
  /** Loading state for evidence data */
  loading: boolean;
  /** Error state for evidence data */
  error: string | null;
}

// Evidence action types
export type EvidenceActionType = 'toggle' | 'open' | 'close' | 'select';

// Evidence action
export interface EvidenceAction {
  type: EvidenceActionType;
  transactionId?: string;
  evidence?: EvidenceItem[];
}

// Evidence summary
export interface EvidenceSummary {
  /** Total count of evidence items */
  count: number;
  /** Count by evidence type */
  byType: Record<EvidenceType, number>;
  /** Average confidence score */
  averageConfidence: number;
}