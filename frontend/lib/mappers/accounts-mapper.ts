/**
 * Accounts Mapper - Stage 4 Accounts Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Accounts Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type {
  AccountsViewModel,
  AccountDetailViewModel,
  BalanceHistoryViewModel,
  AccountTransactionViewModel,
  AccountTypeBreakdownViewModel,
  AccountInsightViewModel,
  AccountEvidenceChainViewModel,
  AccountFiltersViewModel,
  AccountNavigationViewModel,
} from '../../types/accounts-view-model';

// ===== DTO Types (from backend) =====

type AccountType = 'savings' | 'current' | 'credit_card' | 'investment' | 'loan' | 'other';
type AccountStatus = 'active' | 'inactive' | 'closed';

interface AccountDetailDTO {
  id: string;
  name: string;
  type: AccountType;
  institution: string;
  balance_paise: number;
  currency: string;
  status: AccountStatus;
  account_number_last4?: string;
  opened_date?: string;
  closed_date?: string;
}

interface BalanceHistoryDTO {
  date: string;
  balance_paise: number;
  account_id: string;
}

interface AccountTransactionDTO {
  id: string;
  date: string;
  description: string;
  amount_paise: number;
  category: string;
  merchant?: string;
}

interface AccountTypeBreakdownDTO {
  type: AccountType;
  count: number;
  total_balance_paise: number;
  percentage: number;
}

type AccountInsightType = 'positive' | 'warning' | 'info' | 'alert';
type AccountInsightSeverity = 'low' | 'medium' | 'high';

interface AccountInsightDTO {
  type: AccountInsightType;
  severity: AccountInsightSeverity;
  message: string;
  action_url?: string;
}

interface AccountEvidenceItemDTO {
  type: string;
  summary: string;
  source: string;
  confidence?: number;
}

interface AccountCalculationStepDTO {
  name: string;
  description: string;
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
}

interface AccountEvidenceChainDTO {
  summary: string;
  evidence: AccountEvidenceItemDTO[];
  calculation_steps: AccountCalculationStepDTO[];
  source_references: string[];
  confidence_score: number;
}

interface AccountsDTO {
  accounts: AccountDetailDTO[];
  total_balance_paise: number;
  account_count: number;
  type_breakdown: AccountTypeBreakdownDTO[];
  insights: AccountInsightDTO[];
  evidence_chain?: AccountEvidenceChainDTO;
}

/**
 * Accounts Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface IAccountsMapper {
  /**
   * Map a single Accounts DTO to ViewModel
   */
  mapAccountsDTO(dto: AccountsDTO): AccountsViewModel;

  /**
   * Map account details DTOs to ViewModels
   */
  mapAccountDetails(dtos: AccountDetailDTO[]): AccountDetailViewModel[];

  /**
   * Map balance history DTOs to ViewModels
   */
  mapBalanceHistory(dtos: BalanceHistoryDTO[]): BalanceHistoryViewModel[];

  /**
   * Map transactions DTOs to ViewModels
   */
  mapTransactions(dtos: AccountTransactionDTO[]): AccountTransactionViewModel[];

  /**
   * Map type breakdown DTOs to ViewModels
   */
  mapTypeBreakdown(dtos: AccountTypeBreakdownDTO[]): AccountTypeBreakdownViewModel[];

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: AccountInsightDTO[]): AccountInsightViewModel[];

  /**
   * Map evidence chain DTO to ViewModel
   */
  mapEvidenceChain(
    dto: AccountEvidenceChainDTO | null | undefined
  ): AccountEvidenceChainViewModel | undefined;
}

/**
 * Accounts Mapper Implementation
 * Transforms backend accounts data to ViewModels
 */
export class AccountsMapper implements IAccountsMapper {
  /**
   * Map a single Accounts DTO to ViewModel
   * @param dto - Accounts data from API
   * @returns AccountsViewModel for presentation
   */
  mapAccountsDTO(dto: AccountsDTO): AccountsViewModel {
    return {
      accounts: this.mapAccountDetails(dto.accounts),
      total_balance_paise: dto.total_balance_paise,
      account_count: dto.account_count,
      type_breakdown: this.mapTypeBreakdown(dto.type_breakdown),
      balance_history: [],
      transactions: [],
      insights: this.mapInsights(dto.insights),
      evidence_chain: this.mapEvidenceChain(dto.evidence_chain),
      filters: this.createDefaultFilters(),
      navigation: this.createDefaultNavigation(),
    };
  }

  /**
   * Map account details DTOs to ViewModels
   */
  mapAccountDetails(dtos: AccountDetailDTO[]): AccountDetailViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      id: dto.id,
      name: dto.name,
      type: dto.type,
      institution: dto.institution,
      balance_paise: dto.balance_paise,
      currency: dto.currency,
      status: dto.status,
      account_number_last4: dto.account_number_last4,
      opened_date: dto.opened_date,
      closed_date: dto.closed_date,
    }));
  }

  /**
   * Map balance history DTOs to ViewModels
   */
  mapBalanceHistory(dtos: BalanceHistoryDTO[]): BalanceHistoryViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      date: dto.date,
      balance_paise: dto.balance_paise,
      account_id: dto.account_id,
    }));
  }

  /**
   * Map transactions DTOs to ViewModels
   */
  mapTransactions(dtos: AccountTransactionDTO[]): AccountTransactionViewModel[] {
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
   * Map type breakdown DTOs to ViewModels
   */
  mapTypeBreakdown(dtos: AccountTypeBreakdownDTO[]): AccountTypeBreakdownViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map((dto) => ({
      type: dto.type,
      count: dto.count,
      total_balance_paise: dto.total_balance_paise,
      percentage: dto.percentage,
    }));
  }

  /**
   * Map insights DTOs to ViewModels
   */
  mapInsights(dtos: AccountInsightDTO[]): AccountInsightViewModel[] {
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
    dto: AccountEvidenceChainDTO | null | undefined
  ): AccountEvidenceChainViewModel | undefined {
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
  private createDefaultFilters(): AccountFiltersViewModel {
    return {
      account_types: undefined,
      institutions: undefined,
      statuses: undefined,
      date_range: undefined,
      balance_range: undefined,
    };
  }

  /**
   * Create default navigation
   */
  private createDefaultNavigation(): AccountNavigationViewModel {
    return {
      deep_link: '/accounts',
      cross_references: {
        net_worth: '/net-worth',
        transactions: '/transactions',
      },
    };
  }
}

// Export singleton instance
export const accountsMapper = new AccountsMapper();