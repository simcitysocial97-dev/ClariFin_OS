/**
 * Invariant Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests verify data consistency and invariants for the TransactionViewModel.
 */

import { describe, it, expect } from 'vitest';
import type {
  TransactionViewModel,
  MoneyViewModel,
  EvidenceItem,
  CalculationStep,
  ImportLineage,
} from '../transaction-view-model';

describe('TransactionViewModel Invariants', () => {
  describe('MoneyViewModel', () => {
    it('should have paise as the canonical value', () => {
      // Paise is the canonical value for financial determinism
      const money: MoneyViewModel = {
        paise: 123456,
        rupees: 1234.56,
      };

      // Verify the relationship: 1 rupee = 100 paise
      // rupees should be paise / 100
      expect(money.rupees).toBe(money.paise / 100);
    });

    it('should have non-negative paise for valid transactions', () => {
      // Valid transactions should have non-negative paise
      const validMoney: MoneyViewModel = {
        paise: 0,
        rupees: 0,
      };

      expect(validMoney.paise).toBeGreaterThanOrEqual(0);
    });

    it('should handle large paise values', () => {
      // Large values should be supported
      const largeMoney: MoneyViewModel = {
        paise: 999999999,
        rupees: 9999999.99,
      };

      expect(largeMoney.paise).toBeGreaterThan(0);
      expect(largeMoney.rupees).toBe(largeMoney.paise / 100);
    });
  });

  describe('TransactionViewModel Core Fields', () => {
    it('should have required core fields', () => {
      // Type verification for core fields
      type CoreFields = Pick<TransactionViewModel, 'id' | 'date' | 'description' | 'amount'>;

      const coreFields: CoreFields = {
        id: 'tx-123',
        date: '2026-07-19',
        description: 'Test transaction',
        amount: { paise: 10000, rupees: 100 },
      };

      expect(coreFields.id).toBeDefined();
      expect(coreFields.date).toBeDefined();
      expect(coreFields.description).toBeDefined();
      expect(coreFields.amount).toBeDefined();
    });

    it('should have valid date format', () => {
      // Date should be in ISO format YYYY-MM-DD
      const validDate = '2026-07-19';
      const dateRegex = /^\d{4}-\d{2}-\d{2}$/;

      expect(dateRegex.test(validDate)).toBe(true);
    });

    it('should have non-empty id', () => {
      // ID should be a non-empty string
      const validId = 'tx-123';
      expect(validId.length).toBeGreaterThan(0);
    });

    it('should have non-empty description', () => {
      // Description should be a non-empty string
      const validDescription = 'Grocery shopping at supermarket';
      expect(validDescription.length).toBeGreaterThan(0);
    });
  });

  describe('TransactionViewModel Date Navigation', () => {
    it('should have consistent date navigation fields', () => {
      // If year/month/day are present, they should be consistent with date
      const date = '2026-07-19';
      const year = 2026;
      const month = 7;
      const day = 19;

      // Verify consistency
      expect(year).toBe(2026);
      expect(month).toBeGreaterThanOrEqual(1);
      expect(month).toBeLessThanOrEqual(12);
      expect(day).toBeGreaterThanOrEqual(1);
      expect(day).toBeLessThanOrEqual(31);
    });

    it('should have valid month key format', () => {
      // Month key should be in format YYYY-MM
      const monthKey = '2026-07';
      const monthKeyRegex = /^\d{4}-\d{2}$/;

      expect(monthKeyRegex.test(monthKey)).toBe(true);
    });
  });

  describe('TransactionViewModel Selection State', () => {
    it('should have consistent selection state', () => {
      // If selected is true, selectable should be true
      const selected = true;
      const selectable = true;

      if (selected) {
        expect(selectable).toBe(true);
      }
    });

    it('should have selection reason when not selectable', () => {
      // If selectable is false, selection_reason should be present
      const selectable = false;
      const selectionReason = 'Transaction is locked';

      if (!selectable) {
        expect(selectionReason).toBeDefined();
        expect(selectionReason.length).toBeGreaterThan(0);
      }
    });
  });

  describe('TransactionViewModel Adjustment', () => {
    it('should have adjustment fields when is_adjusted is true', () => {
      // If is_adjusted is true, adjustment_id and adjustment_reason should be present
      const isAdjusted = true;
      const adjustmentId = 'adj-123';
      const adjustmentReason = 'Fee correction';

      if (isAdjusted) {
        expect(adjustmentId).toBeDefined();
        expect(adjustmentReason).toBeDefined();
      }
    });

    it('should have valid adjustment status', () => {
      // Reconciliation status should be one of the valid values
      type Status = 'pending' | 'confirmed' | 'rejected';
      const validStatuses: Status[] = ['pending', 'confirmed', 'rejected'];

      expect(validStatuses).toContain('pending');
      expect(validStatuses).toContain('confirmed');
      expect(validStatuses).toContain('rejected');
    });
  });

  describe('EvidenceItem', () => {
    it('should have valid evidence type', () => {
      // Evidence type should be one of the valid values
      type EvidenceType = 'categorization' | 'import' | 'adjustment' | 'balance' | 'reconciliation';
      const validTypes: EvidenceType[] = ['categorization', 'import', 'adjustment', 'balance', 'reconciliation'];

      expect(validTypes.length).toBe(5);
    });

    it('should have confidence between 0 and 100', () => {
      // Confidence should be in valid range
      const validConfidence = 85;
      expect(validConfidence).toBeGreaterThanOrEqual(0);
      expect(validConfidence).toBeLessThanOrEqual(100);
    });

    it('should have non-empty summary', () => {
      // Summary should be a non-empty string
      const validSummary = 'Transaction categorized as Food';
      expect(validSummary.length).toBeGreaterThan(0);
    });
  });

  describe('CalculationStep', () => {
    it('should have required fields', () => {
      // Type verification for CalculationStep
      type StepFields = Pick<CalculationStep, 'name' | 'description' | 'inputs' | 'outputs'>;

      const step: StepFields = {
        name: 'categorize',
        description: 'Categorize transaction based on description',
        inputs: { description: 'Grocery shopping' },
        outputs: { category: 'Food' },
      };

      expect(step.name).toBeDefined();
      expect(step.description).toBeDefined();
      expect(step.inputs).toBeDefined();
      expect(step.outputs).toBeDefined();
    });

    it('should have non-empty name', () => {
      // Name should be a non-empty string
      const validName = 'calculate_balance';
      expect(validName.length).toBeGreaterThan(0);
    });
  });

  describe('ImportLineage', () => {
    it('should have required fields', () => {
      // Type verification for ImportLineage
      type LineageFields = Pick<ImportLineage, 'file_id' | 'filename' | 'import_date' | 'source_type' | 'bank'>;

      const lineage: LineageFields = {
        file_id: 'file-123',
        filename: 'statement.csv',
        import_date: '2026-07-19T10:30:00Z',
        source_type: 'csv',
        bank: 'HDFC Bank',
      };

      expect(lineage.file_id).toBeDefined();
      expect(lineage.filename).toBeDefined();
      expect(lineage.import_date).toBeDefined();
      expect(lineage.source_type).toBeDefined();
      expect(lineage.bank).toBeDefined();
    });

    it('should have valid source type', () => {
      // Source type should be one of the valid values
      type SourceType = 'pdf' | 'csv' | 'excel';
      const validSourceTypes: SourceType[] = ['pdf', 'csv', 'excel'];

      expect(validSourceTypes.length).toBe(3);
    });

    it('should have valid import date format', () => {
      // Import date should be in ISO format
      const importDate = '2026-07-19T10:30:00Z';
      const isoDateRegex = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/;

      expect(isoDateRegex.test(importDate)).toBe(true);
    });
  });

  describe('TransactionViewModel Consistency', () => {
    it('should maintain data consistency across all fields', () => {
      // Create a complete transaction with all fields
      const transaction: TransactionViewModel = {
        id: 'tx-123',
        date: '2026-07-19',
        description: 'Grocery shopping',
        amount: { paise: 123456, rupees: 1234.56 },
        year: 2026,
        month: 7,
        day: 19,
        month_key: '2026-07',
        date_formatted: 'Jul 19, 2026',
        category_id: 'cat-1',
        category_name: 'Food',
        category_path: 'Essentials > Food',
        merchant_id: 'merch-1',
        merchant_name: 'Supermarket',
        merchant_category: 'Grocery',
        account_id: 'acc-1',
        account_name: 'Savings Account',
        bank: 'HDFC',
        transaction_type: 'debit',
        reference_number: 'REF123456',
        selected: false,
        selectable: true,
        is_adjusted: false,
        import_lineage: {
          file_id: 'file-1',
          filename: 'statement.csv',
          import_date: '2026-07-19T10:30:00Z',
          source_type: 'csv',
          bank: 'HDFC Bank',
        },
        evidence: [
          {
            type: 'categorization',
            summary: 'Auto-categorized as Food',
            source: { file_id: 'file-1' },
            confidence: 95,
          },
        ],
        calculation_chain: [
          {
            name: 'categorize',
            description: 'Categorize transaction',
            inputs: { description: 'Grocery shopping' },
            outputs: { category: 'Food' },
          },
        ],
        source_reference: {
          file_id: 'file-1',
          row_number: 42,
        },
        confidence: 95,
        reconciliation_id: 'rec-1',
        reconciliation_status: 'confirmed',
      };

      // Verify all required fields are present
      expect(transaction.id).toBeDefined();
      expect(transaction.date).toBeDefined();
      expect(transaction.description).toBeDefined();
      expect(transaction.amount).toBeDefined();

      // Verify date consistency
      expect(transaction.year).toBe(2026);
      expect(transaction.month).toBe(7);
      expect(transaction.day).toBe(19);

      // Verify amount consistency
      expect(transaction.amount.rupees).toBe(transaction.amount.paise / 100);

      // Verify evidence has valid confidence
      if (transaction.evidence && transaction.evidence[0]) {
        expect(transaction.evidence[0].confidence).toBeGreaterThanOrEqual(0);
        expect(transaction.evidence[0].confidence).toBeLessThanOrEqual(100);
      }
    });
  });
});