/**
 * Transaction Mapper - Stage 3 Transaction Intelligence Workspace
 *
 * Transforms backend DTOs to ViewModels for the Transaction Intelligence Workspace.
 * This is the ONLY location where DTO to ViewModel mapping occurs.
 *
 * Architecture Flow: Backend → API → DTO → Mapper → ViewModel
 */

import type { TransactionViewModel, MoneyViewModel, ImportLineage, EvidenceItem } from '../../types/transaction-view-model';
import type { Transaction } from '../../types/transaction';

/**
 * Transaction Mapper Interface
 * Defines the contract for DTO to ViewModel mapping
 */
export interface ITransactionMapper {
  /**
   * Map a single transaction DTO to ViewModel
   */
  mapTransaction(dto: Transaction): TransactionViewModel;

  /**
   * Map an array of transaction DTOs to ViewModels
   */
  mapTransactions(dtos: Transaction[]): TransactionViewModel[];
}

/**
 * Transaction Mapper Implementation
 * Transforms backend transaction data to ViewModels
 */
export class TransactionMapper implements ITransactionMapper {
  /**
   * Map a single transaction DTO to ViewModel
   * @param dto - Transaction data from API
   * @returns TransactionViewModel for presentation
   */
  mapTransaction(dto: Transaction): TransactionViewModel {
    // Extract date components for navigation
    const dateParts = this.parseDate(dto.date);

    // Build the ViewModel
    const viewModel: TransactionViewModel = {
      // Core fields
      id: String(dto.id),
      date: dto.date,
      description: dto.description,
      amount: this.mapMoney(dto),

      // Extended fields
      balance: undefined,
      category_id: dto.category ? `cat_${dto.category.toLowerCase()}` : undefined,
      category_name: dto.category,
      category_path: dto.subcategory ? `${dto.category} > ${dto.subcategory}` : dto.category,
      subcategory: dto.subcategory,
      merchant_id: undefined,
      merchant_name: undefined,
      merchant_category: undefined,
      year: dateParts.year,
      month: dateParts.month,
      day: dateParts.day,
      date_formatted: this.formatDate(dto.date),
      month_key: dateParts.monthKey,
      account_id: dto.cardId,
      account_name: dto.bank,
      bank: dto.bank,
      transaction_type: dto.type,
      reference_number: undefined,

      // Selection state (default values)
      selected: false,
      selectable: true,

      // Adjustment visibility
      is_adjusted: false,
      adjustment_id: undefined,
      adjustment_reason: undefined,

      // Import lineage
      import_lineage: dto.statement_file ? this.mapImportLineage(dto) : undefined,

      // Evidence
      evidence: this.buildEvidence(dto),

      // Source reference
      source_reference: dto.statement_file ? {
        file_id: dto.statement_file,
        row_number: dto.sequence_num,
      } : undefined,

      // Confidence score
      confidence: undefined,

      // Reconciliation reference
      reconciliation_id: undefined,
      reconciliation_status: undefined,
    };

    return viewModel;
  }

  /**
   * Map an array of transaction DTOs to ViewModels
   * @param dtos - Array of transaction data from API
   * @returns Array of TransactionViewModels
   */
  mapTransactions(dtos: Transaction[]): TransactionViewModel[] {
    if (!dtos || dtos.length === 0) {
      return [];
    }
    return dtos.map(dto => this.mapTransaction(dto));
  }

  // ===== Private Helper Methods =====

  /**
   * Map MoneyDTO to MoneyViewModel
   */
  private mapMoney(dto: Transaction): MoneyViewModel {
    // Use the amount field if available (canonical), otherwise use amount_paise
    if (dto.amount && typeof dto.amount === 'object' && 'paise' in dto.amount) {
      return {
        paise: dto.amount.paise,
        rupees: dto.amount.rupees,
      };
    }
    // Fallback to amount_paise
    return {
      paise: dto.amount_paise ?? 0,
      rupees: dto.amount_rupees ?? this.paiseToRupees(dto.amount_paise ?? 0),
    };
  }


  /**
   * Convert paise to rupees
   */
  private paiseToRupees(paise: number): number {
    return paise / 100;
  }

  /**
   * Parse date string into components
   */
  private parseDate(dateString: string): { year: number; month: number; day: number; monthKey: string } {
    const date = new Date(dateString);
    return {
      year: date.getFullYear(),
      month: date.getMonth() + 1,
      day: date.getDate(),
      monthKey: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`,
    };
  }

  /**
   * Format date for display
   */
  private formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  }

  /**
   * Build import lineage from DTO
   */
  private mapImportLineage(dto: Transaction): ImportLineage {
    return {
      file_id: dto.statement_file ?? '',
      filename: dto.statement_file ?? 'unknown',
      import_date: new Date().toISOString(),
      source_type: 'pdf',
      bank: dto.bank,
      period_from: dto.statement_period_from ?? undefined,
      period_to: dto.statement_period_to ?? undefined,
    };
  }

  /**
   * Build evidence array from DTO
   */
  private buildEvidence(dto: Transaction): EvidenceItem[] | undefined {
    const evidence: EvidenceItem[] = [];

    // Categorization evidence
    if (dto.category) {
      evidence.push({
        type: 'categorization',
        summary: `Categorized as ${dto.category}${dto.subcategory ? ` > ${dto.subcategory}` : ''}`,
        source: {
          file_id: dto.statement_file,
          row_number: dto.sequence_num,
        },
      });
    }

    // Import evidence
    if (dto.statement_file) {
      evidence.push({
        type: 'import',
        summary: `Imported from ${dto.statement_file}`,
        source: {
          file_id: dto.statement_file,
          row_number: dto.sequence_num,
        },
      });
    }

    return evidence.length > 0 ? evidence : undefined;
  }
}

// Export singleton instance
export const transactionMapper = new TransactionMapper();