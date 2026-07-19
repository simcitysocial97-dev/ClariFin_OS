/**
 * Credit Cards Mapper - Stage 4 Credit Cards Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Credit Cards Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  CreditCardsViewModel,
  CreditCardSummaryViewModel,
  StatementHistoryViewModel,
  UtilizationViewModel,
  SpendingByCategoryViewModel,
  CreditCardInsightViewModel,
  CreditCardEvidenceChainViewModel,
  CreditCardFiltersViewModel,
  CreditCardNavigationViewModel,
} from '../../types/credit-cards-view-model';

// ===== DTO Types (from backend) =====

type CreditCardStatus = 'active' | 'inactive' | 'closed';

interface StatementHistoryDTO {
  id: number;
  card_id: string;
  period_from: string;
  period_to: string;
  total_due_paise: number;
  min_due_paise: number;
  total_payment_paise: number;
  payment_date?: string;
  status: string;
}

interface UtilizationDTO {
  card_id: string;
  credit_limit_paise: number;
  current_balance_paise: number;
  utilization_percentage: number;
  available_paise: number;
}

interface SpendingByCategoryDTO {
  card_id: string;
  category: string;
  amount_paise: number;
  percentage: number;
  transaction_count: number;
}

interface CreditCardSummaryDTO {
  id: string;
  name: string;
  bank: string;
  card_number_last4: string;
  credit_limit_paise: number;
  current_balance_paise: number;
  available_paise: number;
  min_due_paise: number;
  total_due_paise: number;
  due_date: string;
  status: CreditCardStatus;
  reward_points: number;
}

type CreditCardInsightType = 'positive' | 'warning' | 'info' | 'alert';
type CreditCardInsightSeverity = 'low' | 'medium' | 'high';

interface CreditCardInsightDTO {
  type: CreditCardInsightType;
  severity: CreditCardInsightSeverity;
  message: string;
  action_url?: string;
}

interface CreditCardEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface CreditCardCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface CreditCardEvidenceChainDTO {
  summary: string;
  evidence: CreditCardEvidenceItemDTO[];
  calculation_steps: CreditCardCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface CreditCardsDTO {
  cards: CreditCardSummaryDTO[];
  total_balance_paise: number;
  total_due_paise: number;
  total_available_paise: number;
  card_count: number;
  insights: CreditCardInsightDTO[];
  evidence_chain?: CreditCardEvidenceChainDTO;
}

/**
 * Credit Cards Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface ICreditCardsMapper {
  /**
   * Map a single Credit Cards DTO to ViewModel
   */
  mapCreditCardsDTO(dto: CreditCardsDTO): CreditCardsViewModel;

  /**
   * Map card summaries DTOs to ViewModels
   */
  mapCardSummaries(dtos: CreditCardSummaryDTO[]): CreditCardSummaryViewModel[];

  /**
   * Map statement history DTOs to ViewModels
   */
  mapStatementHistory(dtos: StatementHistoryDTO[]): StatementHistoryViewModel[];

  /**
   * Map utilization DTOs to ViewModels
   */
  mapUtilization(dtos: UtilizationDTO[]): UtilizationViewModel[];

  /**
   * Map spending by category DTOs to ViewModels
   */
  mapSpendingByCategory(dtos: SpendingByCategoryDTO[]): SpendingByCategoryViewModel[];

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: CreditCardInsightDTO[]): CreditCardInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: CreditCardEvidenceChainDTO | null | undefined
  ): CreditCardEvidenceChainViewModel | undefined;
}

/**
 * Credit Cards Mapper Implementation
 * Transforms backend credit cards data to ViewModels
 */
export class CreditCardsMapper implements ICreditCardsMapper {
  /**
   * Map a single Credit Cards DTO to ViewModel
   * @param dto - Credit Cards data from API
   * @returns CreditCardsViewModel for presentation
   */
  mapCreditCardsDTO(dto: CreditCardsDTO): CreditCardsViewModel {
    return {
      cards: this.mapCardSummaries(dto.cards),
      total_balance_paise: dto.total_balance_paise,
      total_due_paise: dto.total_due_paise,
      total_available_paise: dto.total_available_paise,
      card_count: dto.card_count,
      statements: [],
      utilization: [],
      spending: [],
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map card summaries DTOs to ViewModels
   */
  mapCardSummaries(dtos: CreditCardSummaryDTO[]): CreditCardSummaryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      name: dto.name,
      bank: dto.bank,
      card_number_last4: dto.card_number_last4,
      credit_limit_paise: dto.credit_limit_paise,
      current_balance_paise: dto.current_balance_paise,
      available_paise: dto.available_paise,
      min_due_paise: dto.min_due_paise,
      total_due_paise: dto.total_due_paise,
      due_date: dto.due_date,
      status: dto.status,
      reward_points: dto.reward_points,
    }));
  }

  /**
   * Map statement history DTOs to ViewModels
   */
  mapStatementHistory(dtos: StatementHistoryDTO[]): StatementHistoryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      card_id: dto.card_id,
      period_from: dto.period_from,
      period_to: dto.period_to,
      total_due_paise: dto.total_due_paise,
      min_due_paise: dto.min_due_paise,
      total_payment_paise: dto.total_payment_paise,
      payment_date: dto.payment_date,
      status: dto.status,
    }));
  }

  /**
   * Map utilization DTOs to ViewModels
   */
  mapUtilization(dtos: UtilizationDTO[]): UtilizationViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      card_id: dto.card_id,
      credit_limit_paise: dto.credit_limit_paise,
      current_balance_paise: dto.current_balance_paise,
      utilization_percentage: dto.utilization_percentage,
      available_paise: dto.available_paise,
    }));
  }

  /**
   * Map spending by category DTOs to ViewModels
   */
  mapSpendingByCategory(dtos: SpendingByCategoryDTO[]): SpendingByCategoryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      card_id: dto.card_id,
      category: dto.category,
      amount_paise: dto.amount_paise,
      percentage: dto.percentage,
      transaction_count: dto.transaction_count,
    }));
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: CreditCardInsightDTO[]): CreditCardInsightViewModel[] {
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
    dto: CreditCardEvidenceChainDTO | null | undefined
  ): CreditCardEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): CreditCardFiltersViewModel {
    return {
      statuses: undefined,
      banks: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): CreditCardNavigationViewModel {
    return {
      deep_link: '/credit-cards',
      cross_references: {
        net_worth: '/net-worth',
        accounts: '/accounts',
      },
    };
  }
}

// Export singleton instance
export const creditCardsMapper = new CreditCardsMapper();