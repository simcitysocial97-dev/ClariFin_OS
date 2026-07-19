/**
 * Loans Mapper - Stage 4 Loans Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Loans Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  LoansViewModel,
  LoanSummaryViewModel,
  AmortizationEntryViewModel,
  PaymentProgressViewModel,
  InterestAnalysisViewModel,
  LoanInsightViewModel,
  LoanEvidenceChainViewModel,
  LoanFiltersViewModel,
  LoanNavigationViewModel,
} from '../../types/loans-view-model';

// ===== DTO Types (from backend) =====

type LoanType = 'personal' | 'home' | 'car' | 'education' | 'other';
type LoanStatus = 'active' | 'closed' | 'defaulted';

interface AmortizationEntryDTO {
  payment_number: number;
  date: string;
  principal_paise: number;
  interest_paise: number;
  emi_paise: number;
  balance_paise: number;
}

interface LoanSummaryDTO {
  id: string;
  name: string;
  type: LoanType;
  lender: string;
  original_amount_paise: number;
  outstanding_paise: number;
  interest_rate_bps: number;
  tenure_months: number;
  remaining_months: number;
  emi_paise: number;
  status: LoanStatus;
  start_date: string;
  end_date?: string;
}

interface PaymentProgressDTO {
  loan_id: string;
  total_payments: number;
  total_principal_paise: number;
  total_interest_paise: number;
  principal_percentage: number;
  interest_percentage: number;
}

interface InterestAnalysisDTO {
  loan_id: string;
  total_interest_paise: number;
  paid_interest_paise: number;
  remaining_interest_paise: number;
  interest_ratio: number;
}

type LoanInsightType = 'positive' | 'warning' | 'info' | 'alert';
type LoanInsightSeverity = 'low' | 'medium' | 'high';

interface LoanInsightDTO {
  type: LoanInsightType;
  severity: LoanInsightSeverity;
  message: string;
  action_url?: string;
}

interface LoanEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface LoanCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface LoanEvidenceChainDTO {
  summary: string;
  evidence: LoanEvidenceItemDTO[];
  calculation_steps: LoanCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface LoansDTO {
  loans: LoanSummaryDTO[];
  total_outstanding_paise: number;
  total_emi_paise: number;
  loan_count: number;
  insights: LoanInsightDTO[];
  evidence_chain?: LoanEvidenceChainDTO;
}

/**
 * Loans Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface ILoansMapper {
  /**
   * Map a single Loans DTO to ViewModel
   */
  mapLoansDTO(dto: LoansDTO): LoansViewModel;

  /**
   * Map loan summaries DTOs to ViewModels
   */
  mapLoanSummaries(dtos: LoanSummaryDTO[]): LoanSummaryViewModel[];

  /**
   * Map amortization entries DTOs to ViewModels
   */
  mapAmortization(dtos: AmortizationEntryDTO[]): AmortizationEntryViewModel[];

  /**
   * Map payment progress DTOs to ViewModels
   */
  mapPaymentProgress(dtos: PaymentProgressDTO[]): PaymentProgressViewModel[];

  /**
   * Map interest analysis DTOs to ViewModels
   */
  mapInterestAnalysis(dtos: InterestAnalysisDTO[]): InterestAnalysisViewModel[];

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: LoanInsightDTO[]): LoanInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: LoanEvidenceChainDTO | null | undefined
  ): LoanEvidenceChainViewModel | undefined;
}

/**
 * Loans Mapper Implementation
 * Transforms backend loans data to ViewModels
 */
export class LoansMapper implements ILoansMapper {
  /**
   * Map a single Loans DTO to ViewModel
   * @param dto - Loans data from API
   * @returns LoansViewModel for presentation
   */
  mapLoansDTO(dto: LoansDTO): LoansViewModel {
    return {
      loans: this.mapLoanSummaries(dto.loans),
      total_outstanding_paise: dto.total_outstanding_paise,
      total_emi_paise: dto.total_emi_paise,
      loan_count: dto.loan_count,
      amortization: [],
      payment_progress: [],
      interest_analysis: [],
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map loan summaries DTOs to ViewModels
   */
  mapLoanSummaries(dtos: LoanSummaryDTO[]): LoanSummaryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      name: dto.name,
      type: dto.type,
      lender: dto.lender,
      original_amount_paise: dto.original_amount_paise,
      outstanding_paise: dto.outstanding_paise,
      interest_rate_bps: dto.interest_rate_bps,
      tenure_months: dto.tenure_months,
      remaining_months: dto.remaining_months,
      emi_paise: dto.emi_paise,
      status: dto.status,
      start_date: dto.start_date,
      end_date: dto.end_date,
    }));
  }

  /**
   * Map amortization entries DTOs to ViewModels
   */
  mapAmortization(dtos: AmortizationEntryDTO[]): AmortizationEntryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      payment_number: dto.payment_number,
      date: dto.date,
      principal_paise: dto.principal_paise,
      interest_paise: dto.interest_paise,
      emi_paise: dto.emi_paise,
      balance_paise: dto.balance_paise,
    }));
  }

  /**
   * Map payment progress DTOs to ViewModels
   */
  mapPaymentProgress(dtos: PaymentProgressDTO[]): PaymentProgressViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      loan_id: dto.loan_id,
      total_payments: dto.total_payments,
      total_principal_paise: dto.total_principal_paise,
      total_interest_paise: dto.total_interest_paise,
      principal_percentage: dto.principal_percentage,
      interest_percentage: dto.interest_percentage,
    }));
  }

  /**
   * Map interest analysis DTOs to ViewModels
   */
  mapInterestAnalysis(dtos: InterestAnalysisDTO[]): InterestAnalysisViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      loan_id: dto.loan_id,
      total_interest_paise: dto.total_interest_paise,
      paid_interest_paise: dto.paid_interest_paise,
      remaining_interest_paise: dto.remaining_interest_paise,
      interest_ratio: dto.interest_ratio,
    }));
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: LoanInsightDTO[]): LoanInsightViewModel[] {
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
    dto: LoanEvidenceChainDTO | null | undefined
  ): LoanEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): LoanFiltersViewModel {
    return {
      loan_types: undefined,
      lenders: undefined,
      statuses: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): LoanNavigationViewModel {
    return {
      deep_link: '/loans',
      cross_references: {
        net_worth: '/net-worth',
        accounts: '/accounts',
      },
    };
  }
}

// Export singleton instance
export const loansMapper = new LoansMapper();