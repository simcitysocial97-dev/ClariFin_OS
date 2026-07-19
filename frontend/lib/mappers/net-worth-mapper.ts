/**
 * Net Worth Mapper - Stage 4 Net Worth Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Net Worth Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  NetWorthViewModel,
  NetWorthCompositionViewModel,
  NetWorthBreakdownItemViewModel,
  NetWorthHistoricalSnapshotViewModel,
  NetWorthTrendViewModel,
  NetWorthInsightViewModel,
  NetWorthEvidenceChainViewModel,
  NetWorthFiltersViewModel,
  NetWorthNavigationViewModel,
} from '../../types/net-worth-view-model';

// ===== DTO Types (from backend) =====

interface NetWorthBreakdownItemDTO {
  id: string;
  name: string;
  type: string;
  balance_paise: number;
  percentage: number;
  contribution_paise: number;
}

interface NetWorthCompositionDTO {
  total_assets_paise: number;
  total_liabilities_paise: number;
  asset_breakdown: NetWorthBreakdownItemDTO[];
  liability_breakdown: NetWorthBreakdownItemDTO[];
}

interface NetWorthHistoricalSnapshotDTO {
  date: string;
  net_worth_paise: number;
  assets_paise: number;
  liabilities_paise: number;
}

type NetWorthTrendDirection = 'up' | 'down' | 'flat';

interface NetWorthTrendDTO {
  direction: NetWorthTrendDirection;
  percentage_change: number;
  period: string;
}

type NetWorthInsightType = 'positive' | 'warning' | 'info' | 'alert';
type NetWorthInsightSeverity = 'low' | 'medium' | 'high';

interface NetWorthInsightDTO {
  type: NetWorthInsightType;
  severity: NetWorthInsightSeverity;
  message: string;
  action_url?: string;
}

interface NetWorthEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface NetWorthCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface NetWorthEvidenceChainDTO {
  summary: string;
  evidence: NetWorthEvidenceItemDTO[];
  calculation_steps: NetWorthCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface NetWorthDTO {
  total_net_worth_paise: number;
  total_assets_paise: number;
  total_liabilities_paise: number;
  composition: NetWorthCompositionDTO;
  trend?: NetWorthTrendDTO;
  insights: NetWorthInsightDTO[];
  evidence_chain?: NetWorthEvidenceChainDTO;
}

/**
 * Net Worth Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface INetWorthMapper {
  /**
   * Map a single Net Worth DTO to ViewModel
   */
  mapNetWorthDTO(dto: NetWorthDTO): NetWorthViewModel;

  /**
   * Map composition DTO to ViewModel
   */
  mapCompositionDTO(dto: NetWorthCompositionDTO): NetWorthCompositionViewModel;

  /**
   * Map historical snapshots DTOs to ViewModels
   */
  mapHistoricalSnapshots(
    dtos: NetWorthHistoricalSnapshotDTO[]
  ): NetWorthHistoricalSnapshotViewModel[];

  /**
   * Map trend DTO to ViewModel
   */
  mapTrendDTO(dto: NetWorthTrendDTO | null | undefined): NetWorthTrendViewModel | undefined;

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: NetWorthInsightDTO[]): NetWorthInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: NetWorthEvidenceChainDTO | null | undefined
  ): NetWorthEvidenceChainViewModel | undefined;
}

/**
 * Net Worth Mapper Implementation
 * Transforms backend net worth data to ViewModels
 */
export class NetWorthMapper implements INetWorthMapper {
  /**
   * Map a single Net Worth DTO to ViewModel
   * @param dto - Net Worth data from API
   * @returns NetWorthViewModel for presentation
   */
  mapNetWorthDTO(dto: NetWorthDTO): NetWorthViewModel {
    return {
      total_net_worth_paise: dto.total_net_worth_paise,
      total_assets_paise: dto.total_assets_paise,
      total_liabilities_paise: dto.total_liabilities_paise,
      composition: this.mapCompositionDTO(dto.composition),
      trend: this.mapTrendDTO(dto.trend),
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map composition DTO to ViewModel
   */
  mapCompositionDTO(dto: NetWorthCompositionDTO): NetWorthCompositionViewModel {
    return {
      total_assets_paise: dto.total_assets_paise,
      total_liabilities_paise: dto.total_liabilities_paise,
      asset_breakdown: dto.asset_breakdown.map((item) => this.mapBreakdownItem(item)),
      liability_breakdown: dto.liability_breakdown.map((item) =>
        this.mapBreakdownItem(item)
      ),
    };
  }

  /**
   * Map a single breakdown item DTO to ViewModel
   */
  private mapBreakdownItem(dto: NetWorthBreakdownItemDTO): NetWorthBreakdownItemViewModel {
    return {
      id: dto.id,
      name: dto.name,
      type: dto.type,
      balance_paise: dto.balance_paise,
      percentage: dto.percentage,
      contribution_paise: dto.contribution_paise,
    };
  }

  /**
   * Map historical snapshots DTOs to ViewModels
   */
  mapHistoricalSnapshots(
    dtos: NetWorthHistoricalSnapshotDTO[]
  ): NetWorthHistoricalSnapshotViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      date: dto.date,
      net_worth_paise: dto.net_worth_paise,
      assets_paise: dto.assets_paise,
      liabilities_paise: dto.liabilities_paise,
    }));
  }

  /**
   * Map trend DTO to ViewModel
   */
  mapTrendDTO(
    dto: NetWorthTrendDTO | null | undefined
  ): NetWorthTrendViewModel | undefined {
    if (!dto) {
      return undefined;
    }
    return {
      direction: dto.direction,
      percentage_change: dto.percentage_change,
      period: dto.period,
    };
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: NetWorthInsightDTO[]): NetWorthInsightViewModel[] {
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
    dto: NetWorthEvidenceChainDTO | null | undefined
  ): NetWorthEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): NetWorthFiltersViewModel {
    return {
      date_range: undefined,
      account_types: undefined,
      period: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): NetWorthNavigationViewModel {
    return {
      deep_link: '/net-worth',
      cross_references: {
        accounts: '/accounts',
        investments: '/investments',
        loans: '/loans',
        credit_cards: '/credit-cards',
      },
    };
  }
}

// Export singleton instance
export const netWorthMapper = new NetWorthMapper();