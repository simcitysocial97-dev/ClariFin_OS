/**
 * Behaviour Mapper - Stage 4 Behaviour Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Behaviour Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  BehaviourViewModel,
  BehaviourScoreViewModel,
  SpendingPatternViewModel,
  SavingsRateViewModel,
  DebtHealthViewModel,
  WellnessRadarViewModel,
  BehaviourInsightViewModel,
  BehaviourEvidenceChainViewModel,
  BehaviourFiltersViewModel,
  BehaviourNavigationViewModel,
} from '../../types/behaviour-view-model';
import type { BehaviorScore } from '../../lib/schemas/behavior-score';

// ===== DTO Types (from backend) =====

interface BehaviourScoreDTO {
  score: number;
  label: string;
  factors: string[];
}

interface SpendingPatternDTO {
  category: string;
  amount_paise: number;
  percentage: number;
  trend: string;
  month_over_month_change: number;
}

interface SavingsRateDTO {
  savings_rate_bps: number;
  income_paise: number;
  savings_paise: number;
  period: string;
}

interface DebtHealthDTO {
  debt_to_income_bps: number;
  total_debt_paise: number;
  total_income_paise: number;
  health_score: number;
}

interface WellnessRadarDTO {
  dimension: string;
  score: number;
  max_score: number;
}

type BehaviourInsightType = 'positive' | 'warning' | 'info' | 'alert';
type BehaviourInsightSeverity = 'low' | 'medium' | 'high';

interface BehaviourInsightDTO {
  type: BehaviourInsightType;
  severity: BehaviourInsightSeverity;
  message: string;
  action_url?: string;
}

interface BehaviourEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface BehaviourCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface BehaviourEvidenceChainDTO {
  summary: string;
  evidence: BehaviourEvidenceItemDTO[];
  calculation_steps: BehaviourCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface BehaviourDTO {
  wellness_score: BehaviourScoreDTO;
  spending_patterns: SpendingPatternDTO[];
  savings_rate?: SavingsRateDTO;
  debt_health?: DebtHealthDTO;
  wellness_radar: WellnessRadarDTO[];
  insights: BehaviourInsightDTO[];
  evidence_chain?: BehaviourEvidenceChainDTO;
}

/**
 * Behaviour Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface IBehaviourMapper {
  /**
   * Map a single Behaviour DTO to ViewModel
   */
  mapBehaviourDTO(dto: BehaviourDTO): BehaviourViewModel;

  /**
   * Map the canonical wellness-score response (BehavioralScore) returned by
   * /api/v1/behaviour/wellness-score to a BehaviourViewModel. The backend only
   * exposes the wellness score, so the richer BehaviourDTO fields are left empty
   * (the corresponding UI surfaces render empty states).
   */
  mapBehavioralScoreToViewModel(dto: BehaviorScore): BehaviourViewModel;

  /**
   * Map wellness score DTO to ViewModel
   */
  mapWellnessScore(dto: BehaviourScoreDTO): BehaviourScoreViewModel;

  /**
   * Map spending patterns DTOs to ViewModels
   */
  mapSpendingPatterns(dtos: SpendingPatternDTO[]): SpendingPatternViewModel[];

  /**
   * Map savings rate DTO to ViewModel
   */
  mapSavingsRate(dto: SavingsRateDTO | null | undefined): SavingsRateViewModel | undefined;

  /**
   * Map debt health DTO to ViewModel
   */
  mapDebtHealth(dto: DebtHealthDTO | null | undefined): DebtHealthViewModel | undefined;

  /**
   * Map wellness radar DTOs to ViewModels
   */
  mapWellnessRadar(dtos: WellnessRadarDTO[]): WellnessRadarViewModel[];

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: BehaviourInsightDTO[]): BehaviourInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: BehaviourEvidenceChainDTO | null | undefined
  ): BehaviourEvidenceChainViewModel | undefined;
}

/**
 * Behaviour Mapper Implementation
 * Transforms backend behaviour data to ViewModels
 */
export class BehaviourMapper implements IBehaviourMapper {
  /**
   * Map a single Behaviour DTO to ViewModel
   * @param dto - Behaviour data from API
   * @returns BehaviourViewModel for presentation
   */
  mapBehaviourDTO(dto: BehaviourDTO): BehaviourViewModel {
    return {
      wellness_score: this.mapWellnessScore(dto.wellness_score),
      spending_patterns: this.mapSpendingPatterns(dto.spending_patterns),
      savings_rate: this.mapSavingsRate(dto.savings_rate),
      debt_health: this.mapDebtHealth(dto.debt_health),
      wellness_radar: this.mapWellnessRadar(dto.wellness_radar),
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map the canonical wellness-score response to a BehaviourViewModel.
   *
   * The backend exposes only /api/v1/behaviour/wellness-score, which returns a
   * BehavioralScore (score in basis points, band, component health map). This
   * mapper maps that onto the BehaviourViewModel contract, deriving the wellness
   * radar and score factors from the component health map. Surfaces that depend
   * on data the backend does not currently expose (spending patterns, savings
   * rate, debt health, insights) receive empty values so their UI renders
   * empty states rather than crashing.
   */
  mapBehavioralScoreToViewModel(dto: BehaviorScore): BehaviourViewModel {
    const components = dto.components ?? {};
    const componentEntries = Object.entries(components).map(([dimension, rawScore]) => ({
      dimension,
      score: Number(rawScore),
      max_score: 100,
    }));

    return {
      wellness_score: {
        score: dto.score / 100, // canonical score is in basis points (0-10000)
        label: dto.band,
        factors: Object.keys(components),
      },
      spending_patterns: [],
      savings_rate: undefined,
      debt_health: undefined,
      wellness_radar: componentEntries,
      insights: [],
      evidence_chain: undefined,
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map wellness score DTO to ViewModel
   */
  mapWellnessScore(dto: BehaviourScoreDTO): BehaviourScoreViewModel {
    return {
      score: dto.score,
      label: dto.label,
      factors: dto.factors,
    };
  }

  /**
   * Map spending patterns DTOs to ViewModels
   */
  mapSpendingPatterns(dtos: SpendingPatternDTO[]): SpendingPatternViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      category: dto.category,
      amount_paise: dto.amount_paise,
      percentage: dto.percentage,
      trend: dto.trend,
      month_over_month_change: dto.month_over_month_change,
    }));
  }

  /**
   * Map savings rate DTO to ViewModel
   */
  mapSavingsRate(dto: SavingsRateDTO | null | undefined): SavingsRateViewModel | undefined {
    if (!dto) {
      return undefined;
    }
    return {
      savings_rate_bps: dto.savings_rate_bps,
      income_paise: dto.income_paise,
      savings_paise: dto.savings_paise,
      period: dto.period,
    };
  }

  /**
   * Map debt health DTO to ViewModel
   */
  mapDebtHealth(dto: DebtHealthDTO | null | undefined): DebtHealthViewModel | undefined {
    if (!dto) {
      return undefined;
    }
    return {
      debt_to_income_bps: dto.debt_to_income_bps,
      total_debt_paise: dto.total_debt_paise,
      total_income_paise: dto.total_income_paise,
      health_score: dto.health_score,
    };
  }

  /**
   * Map wellness radar DTOs to ViewModels
   */
  mapWellnessRadar(dtos: WellnessRadarDTO[]): WellnessRadarViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      dimension: dto.dimension,
      score: dto.score,
      max_score: dto.max_score,
    }));
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: BehaviourInsightDTO[]): BehaviourInsightViewModel[] {
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
    dto: BehaviourEvidenceChainDTO | null | undefined
  ): BehaviourEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): BehaviourFiltersViewModel {
    return {
      period: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): BehaviourNavigationViewModel {
    return {
      deep_link: '/behaviour',
      cross_references: {
        cashflow: '/cashflow',
        net_worth: '/net-worth',
      },
    };
  }
}

// Export singleton instance
export const behaviourMapper = new BehaviourMapper();