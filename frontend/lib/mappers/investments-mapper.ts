/**
 * Investments Mapper - Stage 4 Investments Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Investments Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  InvestmentsViewModel,
  InvestmentSummaryViewModel,
  PerformanceViewModel,
  AssetAllocationViewModel,
  HoldingViewModel,
  InvestmentInsightViewModel,
  InvestmentEvidenceChainViewModel,
  InvestmentFiltersViewModel,
  InvestmentNavigationViewModel,
} from '../../types/investments-view-model';

// ===== DTO Types (from backend) =====

type InvestmentType = 'stocks' | 'mutual_funds' | 'bonds' | 'fd' | 'ppf' | 'gold' | 'other';
type InvestmentStatus = 'active' | 'closed' | 'matured';

interface PerformanceDTO {
  date: string;
  value_paise: number;
  returns_bps: number;
  day_change_bps: number;
}

interface AssetAllocationDTO {
  type: InvestmentType;
  value_paise: number;
  percentage: number;
  count: number;
}

interface HoldingDTO {
  id: string;
  name: string;
  type: InvestmentType;
  symbol?: string;
  quantity: number;
  purchase_price_paise: number;
  current_price_paise: number;
  current_value_paise: number;
  invested_paise: number;
  returns_paise: number;
  returns_percentage: number;
  last_updated: string;
}

interface InvestmentSummaryDTO {
  id: string;
  name: string;
  type: InvestmentType;
  institution: string;
  current_value_paise: number;
  invested_paise: number;
  returns_paise: number;
  returns_percentage: number;
  returns_ytd_bps: number;
  status: InvestmentStatus;
}

type InvestmentInsightType = 'positive' | 'warning' | 'info' | 'alert';
type InvestmentInsightSeverity = 'low' | 'medium' | 'high';

interface InvestmentInsightDTO {
  type: InvestmentInsightType;
  severity: InvestmentInsightSeverity;
  message: string;
  action_url?: string;
}

interface InvestmentEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface InvestmentCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface InvestmentEvidenceChainDTO {
  summary: string;
  evidence: InvestmentEvidenceItemDTO[];
  calculation_steps: InvestmentCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface InvestmentsDTO {
  investments: InvestmentSummaryDTO[];
  total_value_paise: number;
  total_invested_paise: number;
  total_returns_paise: number;
  investment_count: number;
  insights: InvestmentInsightDTO[];
  evidence_chain?: InvestmentEvidenceChainDTO;
}

/**
 * Investments Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface IInvestmentsMapper {
  /**
   * Map a single Investments DTO to ViewModel
   */
  mapInvestmentsDTO(dto: InvestmentsDTO): InvestmentsViewModel;

  /**
   * Map investment summaries DTOs to ViewModels
   */
  mapInvestmentSummaries(dtos: InvestmentSummaryDTO[]): InvestmentSummaryViewModel[];

  /**
   * Map performance DTOs to ViewModels
   */
  mapPerformance(dtos: PerformanceDTO[]): PerformanceViewModel[];

  /**
   * Map asset allocation DTOs to ViewModels
   */
  mapAssetAllocation(dtos: AssetAllocationDTO[]): AssetAllocationViewModel[];

  /**
   * Map holdings DTOs to ViewModels
   */
  mapHoldings(dtos: HoldingDTO[]): HoldingViewModel[];

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: InvestmentInsightDTO[]): InvestmentInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: InvestmentEvidenceChainDTO | null | undefined
  ): InvestmentEvidenceChainViewModel | undefined;
}

/**
 * Investments Mapper Implementation
 * Transforms backend investments data to ViewModels
 */
export class InvestmentsMapper implements IInvestmentsMapper {
  /**
   * Map a single Investments DTO to ViewModel
   * @param dto - Investments data from API
   * @returns InvestmentsViewModel for presentation
   */
  mapInvestmentsDTO(dto: InvestmentsDTO): InvestmentsViewModel {
    return {
      investments: this.mapInvestmentSummaries(dto.investments),
      total_value_paise: dto.total_value_paise,
      total_invested_paise: dto.total_invested_paise,
      total_returns_paise: dto.total_returns_paise,
      investment_count: dto.investment_count,
      performance: [],
      allocation: [],
      holdings: [],
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map investment summaries DTOs to ViewModels
   */
  mapInvestmentSummaries(dtos: InvestmentSummaryDTO[]): InvestmentSummaryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      name: dto.name,
      type: dto.type,
      institution: dto.institution,
      current_value_paise: dto.current_value_paise,
      invested_paise: dto.invested_paise,
      returns_paise: dto.returns_paise,
      returns_percentage: dto.returns_percentage,
      returns_ytd_bps: dto.returns_ytd_bps,
      status: dto.status,
    }));
  }

  /**
   * Map performance DTOs to ViewModels
   */
  mapPerformance(dtos: PerformanceDTO[]): PerformanceViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      date: dto.date,
      value_paise: dto.value_paise,
      returns_bps: dto.returns_bps,
      day_change_bps: dto.day_change_bps,
    }));
  }

  /**
   * Map asset allocation DTOs to ViewModels
   */
  mapAssetAllocation(dtos: AssetAllocationDTO[]): AssetAllocationViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      type: dto.type,
      value_paise: dto.value_paise,
      percentage: dto.percentage,
      count: dto.count,
    }));
  }

  /**
   * Map holdings DTOs to ViewModels
   */
  mapHoldings(dtos: HoldingDTO[]): HoldingViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      name: dto.name,
      type: dto.type,
      symbol: dto.symbol,
      quantity: dto.quantity,
      purchase_price_paise: dto.purchase_price_paise,
      current_price_paise: dto.current_price_paise,
      current_value_paise: dto.current_value_paise,
      invested_paise: dto.invested_paise,
      returns_paise: dto.returns_paise,
      returns_percentage: dto.returns_percentage,
      last_updated: dto.last_updated,
    }));
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: InvestmentInsightDTO[]): InvestmentInsightViewModel[] {
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
    dto: InvestmentEvidenceChainDTO | null | undefined
  ): InvestmentEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): InvestmentFiltersViewModel {
    return {
      investment_types: undefined,
      institutions: undefined,
      statuses: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): InvestmentNavigationViewModel {
    return {
      deep_link: '/investments',
      cross_references: {
        net_worth: '/net-worth',
        accounts: '/accounts',
      },
    };
  }
}

// Export singleton instance
export const investmentsMapper = new InvestmentsMapper();