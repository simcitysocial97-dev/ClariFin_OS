/**
 * Reconciliation Mapper - Stage 4 Reconciliation Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Reconciliation Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  ReconciliationViewModel,
  DiscrepancyViewModel,
  StatusOverviewViewModel,
  AuditTrailEntryViewModel,
  ReconciliationSummaryViewModel,
  ReconciliationInsightViewModel,
  ReconciliationEvidenceChainViewModel,
  ReconciliationFiltersViewModel,
  ReconciliationNavigationViewModel,
} from '../../types/reconciliation-view-model';

// ===== DTO Types (from backend) =====

type ReconciliationStatus = 'pending' | 'confirmed' | 'rejected' | 'disputed';

interface DiscrepancyDTO {
  id: number;
  transaction_id: number;
  statement_id: number;
  type: string;
  expected_paise: number;
  actual_paise: number;
  difference_paise: number;
  status: ReconciliationStatus;
  notes?: string;
}

interface StatusOverviewDTO {
  total_transactions: number;
  reconciled: number;
  pending: number;
  discrepancies: number;
  match_rate: number;
}

interface AuditTrailEntryDTO {
  id: number;
  transaction_id: number;
  action: string;
  user: string;
  timestamp: string;
  notes?: string;
}

interface ReconciliationSummaryDTO {
  statement_id: number;
  bank: string;
  period_from: string;
  period_to: string;
  total_debit_paise: number;
  total_credit_paise: number;
  transaction_count: number;
  reconciled_count: number;
  status: ReconciliationStatus;
}

type ReconciliationInsightType = 'positive' | 'warning' | 'info' | 'alert';
type ReconciliationInsightSeverity = 'low' | 'medium' | 'high';

interface ReconciliationInsightDTO {
  type: ReconciliationInsightType;
  severity: ReconciliationInsightSeverity;
  message: string;
  action_url?: string;
}

interface ReconciliationEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface ReconciliationCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface ReconciliationEvidenceChainDTO {
  summary: string;
  evidence: ReconciliationEvidenceItemDTO[];
  calculation_steps: ReconciliationCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface ReconciliationDTO {
  statements: ReconciliationSummaryDTO[];
  discrepancies: DiscrepancyDTO[];
  status_overview: StatusOverviewDTO;
  audit_trail: AuditTrailEntryDTO[];
  insights: ReconciliationInsightDTO[];
  evidence_chain?: ReconciliationEvidenceChainDTO;
}

/**
 * Reconciliation Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface IReconciliationMapper {
  /**
   * Map a single Reconciliation DTO to ViewModel
   */
  mapReconciliationDTO(dto: ReconciliationDTO): ReconciliationViewModel;

  /**
   * Map discrepancy DTOs to ViewModels
   */
  mapDiscrepancies(dtos: DiscrepancyDTO[]): DiscrepancyViewModel[];

  /**
   * Map status overview DTO to ViewModel
   */
  mapStatusOverview(dto: StatusOverviewDTO): StatusOverviewViewModel;

  /**
   * Map audit trail DTOs to ViewModels
   */
  mapAuditTrail(dtos: AuditTrailEntryDTO[]): AuditTrailEntryViewModel[];

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: ReconciliationInsightDTO[]): ReconciliationInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: ReconciliationEvidenceChainDTO | null | undefined
  ): ReconciliationEvidenceChainViewModel | undefined;
}

/**
 * Reconciliation Mapper Implementation
 * Transforms backend reconciliation data to ViewModels
 */
export class ReconciliationMapper implements IReconciliationMapper {
  /**
   * Map a single Reconciliation DTO to ViewModel
   * @param dto - Reconciliation data from API
   * @returns ReconciliationViewModel for presentation
   */
  mapReconciliationDTO(dto: ReconciliationDTO): ReconciliationViewModel {
    return {
      statements: this.mapStatements(dto.statements),
      discrepancies: this.mapDiscrepancies(dto.discrepancies),
      status_overview: this.mapStatusOverview(dto.status_overview),
      audit_trail: this.mapAuditTrail(dto.audit_trail),
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map statement DTOs to ViewModels
   */
  private mapStatements(dtos: ReconciliationSummaryDTO[]): ReconciliationSummaryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      statement_id: dto.statement_id,
      bank: dto.bank,
      period_from: dto.period_from,
      period_to: dto.period_to,
      total_debit_paise: dto.total_debit_paise,
      total_credit_paise: dto.total_credit_paise,
      transaction_count: dto.transaction_count,
      reconciled_count: dto.reconciled_count,
      status: dto.status,
    }));
  }

  /**
   * Map discrepancy DTOs to ViewModels
   */
  mapDiscrepancies(dtos: DiscrepancyDTO[]): DiscrepancyViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      transaction_id: dto.transaction_id,
      statement_id: dto.statement_id,
      type: dto.type,
      expected_paise: dto.expected_paise,
      actual_paise: dto.actual_paise,
      difference_paise: dto.difference_paise,
      status: dto.status,
      notes: dto.notes,
    }));
  }

  /**
   * Map status overview DTO to ViewModel
   */
  mapStatusOverview(dto: StatusOverviewDTO): StatusOverviewViewModel {
    return {
      total_transactions: dto.total_transactions,
      reconciled: dto.reconciled,
      pending: dto.pending,
      discrepancies: dto.discrepancies,
      match_rate: dto.match_rate,
    };
  }

  /**
   * Map audit trail DTOs to ViewModels
   */
  mapAuditTrail(dtos: AuditTrailEntryDTO[]): AuditTrailEntryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      transaction_id: dto.transaction_id,
      action: dto.action,
      user: dto.user,
      timestamp: dto.timestamp,
      notes: dto.notes,
    }));
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: ReconciliationInsightDTO[]): ReconciliationInsightViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      type: dto.type,
      severity: dto.severity,
      message: dto.message,
      action_url: dto.action_url,
    }));
  }

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: ReconciliationEvidenceChainDTO | null | undefined
  ): ReconciliationEvidenceChainViewModel | undefined {
    if (!dto) {
      return undefined;
    }
    return {
      summary: dto.summary,
      evidence: dto.evidence.map((item) => ({
        type: item.type,
        summary: item.summary,
        source: item.source,
        confidence: item.confidence,
      })),
      calculation_steps: dto.calculation_steps.map((step) => ({
        name: step.name,
        description: step.description,
        inputs: step.inputs,
        outputs: step.outputs,
      })),
      source_references: dto.source_references,
      confidence_score: dto.confidence_score,
    };
  }

  /**
   * Create default filters
   */
  private createDefaultFilters(): ReconciliationFiltersViewModel {
    return {
      status: undefined,
      banks: undefined,
      date_range: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): ReconciliationNavigationViewModel {
    return {
      deep_link: '/reconciliation',
      cross_references: {
        accounts: '/accounts',
        transactions: '/transactions',
      },
    };
  }
}

// Export singleton instance
export const reconciliationMapper = new ReconciliationMapper();