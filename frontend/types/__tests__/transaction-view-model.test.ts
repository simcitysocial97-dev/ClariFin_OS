/**
 * TransactionViewModel Unit Tests
 *
 * Tests verify all required fields exist and have correct types.
 */

import { describe, it, expect } from 'vitest';
import type {
  TransactionViewModel,
  MoneyViewModel,
  EvidenceItem,
  ImportLineage,
  TransactionSummary,
} from '../transaction-view-model';

describe('TransactionViewModel', () => {
  describe('Core Fields', () => {
    it('should have required core fields', () => {
      const viewModel: TransactionViewModel = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Amazon Purchase',
        amount: { paise: -150000, rupees: -1500.0 },
      };

      expect(viewModel.id).toBe('txn_123');
      expect(viewModel.date).toBe('2026-07-05');
      expect(viewModel.description).toBe('Amazon Purchase');
      expect(viewModel.amount.paise).toBe(-150000);
      expect(viewModel.amount.rupees).toBe(-1500.0);
    });

    it('should support optional extended fields', () => {
      const viewModel: TransactionViewModel = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Amazon Purchase',
        amount: { paise: -150000, rupees: -1500.0 },
        balance: { paise: 850000, rupees: 8500.0 },
        category_id: 'cat_shopping',
        category_name: 'Shopping',
        category_path: 'Shopping > E-commerce',
        merchant_id: 'mer_001',
        merchant_name: 'Amazon',
        year: 2026,
        month: 7,
        day: 5,
        account_id: 'acc_001',
        transaction_type: 'debit',
      };

      expect(viewModel.balance).toBeDefined();
      expect(viewModel.category_id).toBe('cat_shopping');
      expect(viewModel.merchant_name).toBe('Amazon');
      expect(viewModel.year).toBe(2026);
      expect(viewModel.month).toBe(7);
      expect(viewModel.day).toBe(5);
    });
  });

  describe('MoneyViewModel', () => {
    it('should represent paise as canonical unit', () => {
      const money: MoneyViewModel = { paise: 123456, rupees: 1234.56 };
      expect(money.paise).toBe(123456);
      expect(money.rupees).toBe(1234.56);
    });

    it('should handle negative amounts for debits', () => {
      const money: MoneyViewModel = { paise: -150000, rupees: -1500.0 };
      expect(money.paise).toBe(-150000);
    });
  });

  describe('EvidenceItem', () => {
    it('should have required evidence fields', () => {
      const evidence: EvidenceItem = {
        type: 'categorization',
        summary: 'Categorized as Shopping based on merchant',
        source: {
          file_id: 'file_001',
          row_number: 5,
        },
      };

      expect(evidence.type).toBe('categorization');
      expect(evidence.summary).toBe('Categorized as Shopping based on merchant');
      expect(evidence.source.file_id).toBe('file_001');
    });

    it('should support optional confidence score', () => {
      const evidence: EvidenceItem = {
        type: 'categorization',
        summary: 'Test',
        source: {},
        confidence: 95,
      };

      expect(evidence.confidence).toBe(95);
    });
  });

  describe('ImportLineage', () => {
    it('should have required import lineage fields', () => {
      const lineage: ImportLineage = {
        file_id: 'file_001',
        filename: 'statement.pdf',
        import_date: '2026-07-05T10:30:00Z',
        source_type: 'pdf',
        bank: 'HDFC Bank',
      };

      expect(lineage.file_id).toBe('file_001');
      expect(lineage.filename).toBe('statement.pdf');
      expect(lineage.source_type).toBe('pdf');
    });

    it('should support optional statement period', () => {
      const lineage: ImportLineage = {
        file_id: 'file_001',
        filename: 'statement.pdf',
        import_date: '2026-07-05T10:30:00Z',
        source_type: 'pdf',
        bank: 'HDFC Bank',
        period_from: '2026-06-01',
        period_to: '2026-06-30',
      };

      expect(lineage.period_from).toBe('2026-06-01');
      expect(lineage.period_to).toBe('2026-06-30');
    });
  });

  describe('Selection State', () => {
    it('should support selection state fields', () => {
      const viewModel: TransactionViewModel = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        amount: { paise: 10000, rupees: 100.0 },
        selected: true,
        selectable: true,
      };

      expect(viewModel.selected).toBe(true);
      expect(viewModel.selectable).toBe(true);
    });

    it('should support selection reason for non-selectable items', () => {
      const viewModel: TransactionViewModel = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        amount: { paise: 10000, rupees: 100.0 },
        selected: false,
        selectable: false,
        selection_reason: 'Already reconciled',
      };

      expect(viewModel.selection_reason).toBe('Already reconciled');
    });
  });

  describe('Adjustment Visibility', () => {
    it('should support adjustment fields', () => {
      const viewModel: TransactionViewModel = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        amount: { paise: 10000, rupees: 100.0 },
        is_adjusted: true,
        adjustment_id: 'adj_001',
        adjustment_reason: 'Correction for duplicate entry',
      };

      expect(viewModel.is_adjusted).toBe(true);
      expect(viewModel.adjustment_id).toBe('adj_001');
    });
  });

  describe('Reconciliation Reference', () => {
    it('should support reconciliation fields', () => {
      const viewModel: TransactionViewModel = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        amount: { paise: 10000, rupees: 100.0 },
        reconciliation_id: 'rec_001',
        reconciliation_status: 'pending',
      };

      expect(viewModel.reconciliation_id).toBe('rec_001');
      expect(viewModel.reconciliation_status).toBe('pending');
    });
  });

  describe('TransactionSummary', () => {
    it('should have required summary fields', () => {
      const summary: TransactionSummary = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Amazon Purchase',
        amount: '₹1,500.00',
        category: 'Shopping',
      };

      expect(summary.id).toBe('txn_123');
      expect(summary.amount).toBe('₹1,500.00');
    });
  });
});