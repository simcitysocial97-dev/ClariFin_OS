/**
 * Cashflow Mapper - Stage 4 Cashflow Truth Workspace
 *
 * Transforms backend DTOs to ViewModels for the Cashflow Truth Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  CashflowViewModel,
  CashflowTrendViewModel,
  CashflowMonthlyViewModel,
  CashflowCategoryViewModel,
  CashflowTransactionViewModel,
  CashflowInsightViewModel,
  CashflowEvidenceChainViewModel,
  CashflowFiltersViewModel,
  CashflowNavigationViewModel,
} from '../../types/cashflow-view-model';

// ===== DTO Types (from backend) =====

type CashflowTrendDirection = 'up' | 'down' | 'flat';

interface CashflowTrendDTO {
  direction: CashflowTrendDirection;
  percentage_change: number;
  period: string;
  volatility_score: number;
}

interface CashflowMonthlyDTO {
  month: string;
  income_paise: number;
  expenses_paise: number;
  net_paise: number;
  transaction_count: number;
}

interface CashflowCategoryDTO {
  category_id: string;
  category_name: string;
  amount_paise: number;
  percentage: number;
  transaction_count: number;
}

interface CashflowTransactionDTO {
  id: string;
  date: string;
  description: string;
  amount_paise: number;
  category: string;
  merchant?: string;
}

type CashflowInsightType = 'positive' | 'warning' | 'info' | 'alert';
type CashflowInsightSeverity = 'low' | 'medium' | 'high';

interface CashflowInsightDTO {
  type: CashflowInsightType;
  severity: CashflowInsightSeverity;
  message: string;
  action_url?: string;
}

interface CashflowEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface CashflowCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface CashflowEvidenceChainDTO {
  summary: string;
  evidence: CashflowEvidenceItemDTO[];
  calculation_steps: CashflowCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface CashflowSummaryDTO {
  total_income_paise: number;
  total_expenses_paise: number;
  net_cashflow_paise: number;
  transaction_count: number;
  trend?: CashflowTrendDTO;
  insights: CashflowInsightDTO[];
  evidence_chain?: CashflowEvidenceChainDTO;
}

/**
 * Cashflow Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface ICashflowMapper {
  /**
   * Map a single Cashflow DTO to ViewModel
   */
  mapCashflowDTO(dto: CashflowSummaryDTO): CashflowViewModel;

  /**
   * Map monthly summaries DTOs to ViewModels
   */
  mapMonthlySummaries(dtos: CashflowMonthlyDTO[]): CashflowMonthlyViewModel[];

  /**
   * Map category breakdowns DTOs to ViewModels
   */
  mapCategoryBreakdowns(dtos: CashflowCategoryDTO[]): CashflowCategoryViewModel[];

  /**
   * Map transactions DTOs to ViewModels
   */
  mapTransactions(dtos: CashflowTransactionDTO[]): CashflowTransactionViewModel[];

  /**
   * Map trend DTO to ViewModel
   */
  mapTrendDTO(dto: CashflowTrendDTO | null | undefined): CashflowTrendViewModel | undefined;

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: CashflowInsightDTO[]): CashflowInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: CashflowEvidenceChainDTO | null | undefined
  ): CashflowEvidenceChainViewModel | undefined;
}

/**
 * Cashflow Mapper Implementation
 * Transforms backend cashflow data to ViewModels
 */
export class CashflowMapper implements ICashflowMapper {
  /**
   * Map a single Cashflow DTO to ViewModel
   * @param dto - Cashflow data from API
   * @returns CashflowViewModel for presentation
   */
  mapCashflowDTO(dto: CashflowSummaryDTO): CashflowViewModel {
    return {
      total_income_paise: dto.total_income_paise,
      total_expenses_paise: dto.total_expenses_paise,
      net_cashflow_paise: dto.net_cashflow_paise,
      transaction_count: dto.transaction_count,
      trend: this.mapTrendDTO(dto.trend),
      monthly: [],
      categories: [],
      transactions: [],
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map monthly summaries DTOs to ViewModels
   */
  mapMonthlySummaries(dtos: CashflowMonthlyDTO[]): CashflowMonthlyViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      month: dto.month,
      income_paise: dto.income_paise,
      expenses_paise: dto.expenses_paise,
      net_paise: dto.net_paise,
      transaction_count: dto.transaction_count,
    }));
  }

  /**
   * Map category breakdowns DTOs to ViewModels
   */
  mapCategoryBreakdowns(dtos: CashflowCategoryDTO[]): CashflowCategoryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      category_id: dto.category_id,
      category_name: dto.category_name,
      amount_paise: dto.amount_paise,
      percentage: dto.percentage,
      transaction_count: dto.transaction_count,
    }));
  }

  /**
   * Map transactions DTOs to ViewModels
   */
  mapTransactions(dtos: CashflowTransactionDTO[]): CashflowTransactionViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      date: dto.date,
      description: dto.description,
      amount_paise: dto.amount_paise,
      category: dto.category,
      merchant: dto.merchant,
    }));
  }

  /**
   * Map trend DTO to ViewModel
   */
  mapTrendDTO(
    dto: CashflowTrendDTO | null | undefined
  ): CashflowTrendViewModel | undefined {
    if (!dto) {
      return undefined;
    }
    return {
      direction: dto.direction,
      percentage_change: dto.percentage_change,
      period: dto.period,
      volatility_score: dto.volatility_score,
    };
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: CashflowInsightDTO[]): CashflowInsightViewModel[] {
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
    dto: CashflowEvidenceChainDTO | null | undefined
  ): CashflowEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): CashflowFiltersViewModel {
    return {
      date_range: undefined,
      categories: undefined,
      merchants: undefined,
      amount_range: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): CashflowNavigationViewModel {
    return {
      deep_link: '/cashflow',
      cross_references: {
        accounts: '/accounts',
        transactions: '/transactions',
      },
    };
  }
}

// Export singleton instance
export const cashflowMapper = new CashflowMapper();