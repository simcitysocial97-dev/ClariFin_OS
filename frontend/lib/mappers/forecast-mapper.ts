/**
 * Forecast Mapper - Stage 4 Forecast Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Forecast Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  ForecastViewModel,
  NetWorthProjectionViewModel,
  CashflowProjectionViewModel,
  ForecastScenarioViewModel,
  ConfidenceIntervalViewModel,
  ForecastSummaryViewModel,
  ForecastInsightViewModel,
  ForecastEvidenceChainViewModel,
  ForecastFiltersViewModel,
  ForecastNavigationViewModel,
} from '../../types/forecast-view-model';

// ===== DTO Types (from backend) =====

interface NetWorthProjectionDTO {
  date: string;
  projected_paise: number;
  lower_bound_paise: number;
  upper_bound_paise: number;
}

interface CashflowProjectionDTO {
  month: string;
  income_paise: number;
  expenses_paise: number;
  net_paise: number;
}

interface ForecastScenarioDTO {
  name: string;
  description: string;
  probability_bps: number;
  net_worth_projections: NetWorthProjectionDTO[];
  cashflow_projections: CashflowProjectionDTO[];
}

type ConfidenceLevel = 90 | 95 | 99;

interface ConfidenceIntervalDTO {
  level: ConfidenceLevel;
  lower_paise: number;
  upper_paise: number;
}

interface ForecastSummaryDTO {
  horizon_months: number;
  current_net_worth_paise: number;
  projected_net_worth_paise: number;
  projected_growth_paise: number;
  projected_growth_percentage: number;
}

type ForecastInsightType = 'positive' | 'warning' | 'info' | 'alert';
type ForecastInsightSeverity = 'low' | 'medium' | 'high';

interface ForecastInsightDTO {
  type: ForecastInsightType;
  severity: ForecastInsightSeverity;
  message: string;
  action_url?: string;
}

interface ForecastEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface ForecastCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface ForecastEvidenceChainDTO {
  summary: string;
  evidence: ForecastEvidenceItemDTO[];
  calculation_steps: ForecastCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface ForecastDTO {
  summary: ForecastSummaryDTO;
  net_worth_projections: NetWorthProjectionDTO[];
  cashflow_projections: CashflowProjectionDTO[];
  scenarios: ForecastScenarioDTO[];
  confidence_intervals: ConfidenceIntervalDTO[];
  insights: ForecastInsightDTO[];
  evidence_chain?: ForecastEvidenceChainDTO;
}

/**
 * Forecast Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface IForecastMapper {
  /**
   * Map a single Forecast DTO to ViewModel
   */
  mapForecastDTO(dto: ForecastDTO): ForecastViewModel;

  /**
   * Map net worth projections DTOs to ViewModels
   */
  mapNetWorthProjections(dtos: NetWorthProjectionDTO[]): NetWorthProjectionViewModel[];

  /**
   * Map cashflow projections DTOs to ViewModels
   */
  mapCashflowProjections(dtos: CashflowProjectionDTO[]): CashflowProjectionViewModel[];

  /**
   * Map forecast scenarios DTOs to ViewModels
   */
  mapScenarios(dtos: ForecastScenarioDTO[]): ForecastScenarioViewModel[];

  /**
   * Map confidence intervals DTOs to ViewModels
   */
  mapConfidenceIntervals(dtos: ConfidenceIntervalDTO[]): ConfidenceIntervalViewModel[];

  /**
   * Map summary DTO to ViewModel
   */
  mapSummary(dto: ForecastSummaryDTO): ForecastSummaryViewModel;

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: ForecastInsightDTO[]): ForecastInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: ForecastEvidenceChainDTO | null | undefined
  ): ForecastEvidenceChainViewModel | undefined;
}

/**
 * Forecast Mapper Implementation
 * Transforms backend forecast data to ViewModels
 */
export class ForecastMapper implements IForecastMapper {
  /**
   * Map a single Forecast DTO to ViewModel
   * @param dto - Forecast data from API
   * @returns ForecastViewModel for presentation
   */
  mapForecastDTO(dto: ForecastDTO): ForecastViewModel {
    return {
      summary: this.mapSummary(dto.summary),
      net_worth_projections: this.mapNetWorthProjections(dto.net_worth_projections),
      cashflow_projections: this.mapCashflowProjections(dto.cashflow_projections),
      scenarios: this.mapScenarios(dto.scenarios),
      confidence_intervals: this.mapConfidenceIntervals(dto.confidence_intervals),
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map net worth projections DTOs to ViewModels
   */
  mapNetWorthProjections(dtos: NetWorthProjectionDTO[]): NetWorthProjectionViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      date: dto.date,
      projected_paise: dto.projected_paise,
      lower_bound_paise: dto.lower_bound_paise,
      upper_bound_paise: dto.upper_bound_paise,
    }));
  }

  /**
   * Map cashflow projections DTOs to ViewModels
   */
  mapCashflowProjections(dtos: CashflowProjectionDTO[]): CashflowProjectionViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      month: dto.month,
      income_paise: dto.income_paise,
      expenses_paise: dto.expenses_paise,
      net_paise: dto.net_paise,
    }));
  }

  /**
   * Map forecast scenarios DTOs to ViewModels
   */
  mapScenarios(dtos: ForecastScenarioDTO[]): ForecastScenarioViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      name: dto.name,
      description: dto.description,
      probability_bps: dto.probability_bps,
      net_worth_projections: this.mapNetWorthProjections(dto.net_worth_projections),
      cashflow_projections: this.mapCashflowProjections(dto.cashflow_projections),
    }));
  }

  /**
   * Map confidence intervals DTOs to ViewModels
   */
  mapConfidenceIntervals(dtos: ConfidenceIntervalDTO[]): ConfidenceIntervalViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      level: dto.level,
      lower_paise: dto.lower_paise,
      upper_paise: dto.upper_paise,
    }));
  }

  /**
   * Map summary DTO to ViewModel
   */
  mapSummary(dto: ForecastSummaryDTO): ForecastSummaryViewModel {
    return {
      horizon_months: dto.horizon_months,
      current_net_worth_paise: dto.current_net_worth_paise,
      projected_net_worth_paise: dto.projected_net_worth_paise,
      projected_growth_paise: dto.projected_growth_paise,
      projected_growth_percentage: dto.projected_growth_percentage,
    };
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: ForecastInsightDTO[]): ForecastInsightViewModel[] {
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
    dto: ForecastEvidenceChainDTO | null | undefined
  ): ForecastEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): ForecastFiltersViewModel {
    return {
      horizon: undefined,
      scenarios: undefined,
      metric_types: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): ForecastNavigationViewModel {
    return {
      deep_link: '/forecast',
      cross_references: {
        net_worth: '/net-worth',
        cashflow: '/cashflow',
      },
    };
  }
}

// Export singleton instance
export const forecastMapper = new ForecastMapper();