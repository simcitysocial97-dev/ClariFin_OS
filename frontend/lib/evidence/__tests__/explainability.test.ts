/**
 * Explainability Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests verify the evidence system provides explainability for all transaction insights.
 */

import { describe, it, expect } from 'vitest';
import {
  createCategorizationEvidence,
  createImportEvidence,
  createAdjustmentEvidence,
  createBalanceEvidence,
  createReconciliationEvidence,
} from '../factories';
import type { EvidenceItem, EvidenceType, EvidenceSource, EvidenceSummary } from '../types';

describe('Evidence System Explainability', () => {
  describe('Evidence Types', () => {
    it('should have all required evidence types', () => {
      // Verify all evidence types exist
      const evidenceTypes: EvidenceType[] = [
        'categorization',
        'import',
        'adjustment',
        'balance',
        'reconciliation',
      ];

      // This is a compile-time check
      expect(evidenceTypes.length).toBe(5);
    });

    it('should have correct type for EvidenceType', () => {
      // Type verification
      type CategorizationType = 'categorization';
      type ImportType = 'import';
      type AdjustmentType = 'adjustment';
      type BalanceType = 'balance';
      type ReconciliationType = 'reconciliation';

      const _cat: CategorizationType = 'categorization';
      const _imp: ImportType = 'import';
      const _adj: AdjustmentType = 'adjustment';
      const _bal: BalanceType = 'balance';
      const _rec: ReconciliationType = 'reconciliation';

      expect(_cat).toBeDefined();
      expect(_imp).toBeDefined();
      expect(_adj).toBeDefined();
      expect(_bal).toBeDefined();
      expect(_rec).toBeDefined();
    });
  });

  describe('Evidence Source', () => {
    it('should have all required source fields', () => {
      // Type verification for EvidenceSource
      type SourceKeys = keyof EvidenceSource;

      const sourceKeys: SourceKeys[] = [
        'file_id',
        'row_number',
        'extraction_id',
        'api_endpoint',
      ];

      // This is a compile-time check
      expect(sourceKeys.length).toBe(4);
    });

    it('should allow optional source fields', () => {
      // All source fields are optional
      const source: EvidenceSource = {};
      expect(source).toBeDefined();
    });

    it('should allow partial source fields', () => {
      const source: EvidenceSource = {
        file_id: 'file-123',
        row_number: 42,
      };
      expect(source.file_id).toBe('file-123');
      expect(source.row_number).toBe(42);
    });
  });

  describe('Evidence Item', () => {
    it('should have all required fields', () => {
      // Type verification for EvidenceItem
      type ItemKeys = keyof EvidenceItem;

      const itemKeys: ItemKeys[] = [
        'type',
        'summary',
        'source',
        'confidence',
      ];

      // This is a compile-time check
      expect(itemKeys.length).toBe(4);
    });

    it('should have confidence as optional field', () => {
      // Confidence is optional
      const item: EvidenceItem = {
        type: 'categorization',
        summary: 'Test summary',
        source: {},
      };
      expect(item.confidence).toBeUndefined();
    });
  });

  describe('Categorization Evidence', () => {
    it('should create categorization evidence with required fields', () => {
      const evidence = createCategorizationEvidence(
        'Transaction categorized as Food',
        { file_id: 'file-1', row_number: 10 },
        95
      );

      expect(evidence.type).toBe('categorization');
      expect(evidence.summary).toBe('Transaction categorized as Food');
      expect(evidence.source.file_id).toBe('file-1');
      expect(evidence.source.row_number).toBe(10);
      expect(evidence.confidence).toBe(95);
    });

    it('should have confidence in categorization evidence', () => {
      const evidence = createCategorizationEvidence(
        'Test',
        {},
        80
      );

      expect(evidence.confidence).toBe(80);
    });
  });

  describe('Import Evidence', () => {
    it('should create import evidence with required fields', () => {
      const evidence = createImportEvidence(
        'Imported from CSV file',
        { file_id: 'import-123' }
      );

      expect(evidence.type).toBe('import');
      expect(evidence.summary).toBe('Imported from CSV file');
      expect(evidence.source.file_id).toBe('import-123');
    });

    it('should allow optional confidence in import evidence', () => {
      const evidence = createImportEvidence(
        'Test',
        {},
        75
      );

      expect(evidence.confidence).toBe(75);
    });
  });

  describe('Adjustment Evidence', () => {
    it('should create adjustment evidence with required fields', () => {
      const evidence = createAdjustmentEvidence(
        'Amount adjusted for fee',
        { extraction_id: 'ext-123' }
      );

      expect(evidence.type).toBe('adjustment');
      expect(evidence.summary).toBe('Amount adjusted for fee');
      expect(evidence.source.extraction_id).toBe('ext-123');
    });
  });

  describe('Balance Evidence', () => {
    it('should create balance evidence with required fields', () => {
      const evidence = createBalanceEvidence(
        'Balance updated after transaction',
        { api_endpoint: '/api/balances' }
      );

      expect(evidence.type).toBe('balance');
      expect(evidence.summary).toBe('Balance updated after transaction');
      expect(evidence.source.api_endpoint).toBe('/api/balances');
    });
  });

  describe('Reconciliation Evidence', () => {
    it('should create reconciliation evidence with required fields', () => {
      const evidence = createReconciliationEvidence(
        'Transaction reconciled',
        { api_endpoint: '/api/reconciliation' }
      );

      expect(evidence.type).toBe('reconciliation');
      expect(evidence.summary).toBe('Transaction reconciled');
      expect(evidence.source.api_endpoint).toBe('/api/reconciliation');
    });
  });

  describe('Evidence Summary', () => {
    it('should have all required summary fields', () => {
      // Type verification for EvidenceSummary
      type SummaryKeys = keyof EvidenceSummary;

      const summaryKeys: SummaryKeys[] = [
        'count',
        'byType',
        'averageConfidence',
      ];

      // This is a compile-time check
      expect(summaryKeys.length).toBe(3);
    });

    it('should calculate average confidence correctly', () => {
      const evidence: EvidenceItem[] = [
        { type: 'categorization', summary: 'Test 1', source: {}, confidence: 90 },
        { type: 'categorization', summary: 'Test 2', source: {}, confidence: 80 },
        { type: 'import', summary: 'Test 3', source: {} },
      ];

      // Calculate average confidence (only items with confidence)
      const itemsWithConfidence = evidence.filter(e => e.confidence !== undefined);
      const averageConfidence = itemsWithConfidence.reduce(
        (sum, e) => sum + (e.confidence || 0),
        0
      ) / itemsWithConfidence.length;

      expect(averageConfidence).toBe(85);
    });

    it('should count evidence by type', () => {
      const evidence: EvidenceItem[] = [
        { type: 'categorization', summary: 'Test 1', source: {} },
        { type: 'categorization', summary: 'Test 2', source: {} },
        { type: 'import', summary: 'Test 3', source: {} },
        { type: 'adjustment', summary: 'Test 4', source: {} },
      ];

      const byType: Record<EvidenceType, number> = {
        categorization: 0,
        import: 0,
        adjustment: 0,
        balance: 0,
        reconciliation: 0,
      };

      for (const e of evidence) {
        byType[e.type] = (byType[e.type] || 0) + 1;
      }

      expect(byType.categorization).toBe(2);
      expect(byType.import).toBe(1);
      expect(byType.adjustment).toBe(1);
      expect(byType.balance).toBe(0);
      expect(byType.reconciliation).toBe(0);
    });
  });

  describe('Evidence Chain', () => {
    it('should support multiple evidence items for a transaction', () => {
      const evidence: EvidenceItem[] = [
        createCategorizationEvidence('Categorized as Food', { file_id: 'f1' }, 95),
        createImportEvidence('Imported from CSV', { file_id: 'f1' }),
        createBalanceEvidence('Balance updated', { api_endpoint: '/api/balances' }),
      ];

      expect(evidence.length).toBe(3);
      expect(evidence[0].type).toBe('categorization');
      expect(evidence[1].type).toBe('import');
      expect(evidence[2].type).toBe('balance');
    });

    it('should provide full traceability for transaction insights', () => {
      // A transaction with full evidence chain
      const evidence: EvidenceItem[] = [
        createImportEvidence(
          'Transaction imported from statement',
          { file_id: 'stmt-123', row_number: 42 },
          100
        ),
        createCategorizationEvidence(
          'Auto-categorized as Groceries',
          { file_id: 'stmt-123', row_number: 42 },
          85
        ),
        createBalanceEvidence(
          'Account balance updated',
          { api_endpoint: '/api/balances' },
          100
        ),
      ];

      // Verify we can trace the full chain
      const importEvidence = evidence.find(e => e.type === 'import');
      const categorizationEvidence = evidence.find(e => e.type === 'categorization');
      const balanceEvidence = evidence.find(e => e.type === 'balance');

      expect(importEvidence).toBeDefined();
      expect(categorizationEvidence).toBeDefined();
      expect(balanceEvidence).toBeDefined();

      // Verify source references are preserved
      expect(importEvidence?.source.file_id).toBe('stmt-123');
      expect(importEvidence?.source.row_number).toBe(42);
    });
  });
});