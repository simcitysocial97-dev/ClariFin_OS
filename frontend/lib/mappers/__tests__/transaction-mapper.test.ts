/**
 * Transaction Mapper Unit Tests
 *
 * Tests verify mapper transformations work correctly.
 */

import { describe, it, expect } from 'vitest';
import { TransactionMapper } from '../transaction-mapper';
import type { Transaction } from '../../../types/transaction';

describe('TransactionMapper', () => {
  const mapper = new TransactionMapper();

  describe('mapTransaction', () => {
    it('should map a basic transaction to ViewModel', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Amazon Purchase',
        type: 'debit',
        category: 'Shopping',
        bank: 'HDFC Bank',
        amount_paise: -150000,
        amount_rupees: -1500.0,
      };

      const result = mapper.mapTransaction(dto);

      expect(result.id).toBe('txn_123');
      expect(result.date).toBe('2026-07-05');
      expect(result.description).toBe('Amazon Purchase');
      expect(result.amount.paise).toBe(-150000);
      expect(result.amount.rupees).toBe(-1500.0);
      expect(result.category_name).toBe('Shopping');
      expect(result.bank).toBe('HDFC Bank');
      expect(result.transaction_type).toBe('debit');
    });

    it('should map date components correctly', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        type: 'debit',
        category: 'Shopping',
        bank: 'HDFC',
      };

      const result = mapper.mapTransaction(dto);

      expect(result.year).toBe(2026);
      expect(result.month).toBe(7);
      expect(result.day).toBe(5);
      expect(result.month_key).toBe('2026-07');
    });

    it('should format date for display', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        type: 'debit',
        category: 'Shopping',
        bank: 'HDFC',
      };

      const result = mapper.mapTransaction(dto);

      expect(result.date_formatted).toBeDefined();
      expect(result.date_formatted).toContain('2026');
    });

    it('should map with Money object', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        type: 'credit',
        category: 'Income',
        bank: 'ICICI',
        amount: { paise: 500000, rupees: 5000.0 },
      };

      const result = mapper.mapTransaction(dto);

      expect(result.amount.paise).toBe(500000);
      expect(result.amount.rupees).toBe(5000.0);
    });

    it('should build evidence for categorized transactions', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        type: 'debit',
        category: 'Shopping',
        bank: 'HDFC',
        statement_file: 'statement_001.pdf',
      };

      const result = mapper.mapTransaction(dto);

      expect(result.evidence).toBeDefined();
      expect(result.evidence).toHaveLength(2);
      expect(result.evidence?.[0].type).toBe('categorization');
      expect(result.evidence?.[1].type).toBe('import');
    });

    it('should build import lineage when statement file present', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        type: 'debit',
        category: 'Shopping',
        bank: 'HDFC',
        statement_file: 'statement_001.pdf',
        statement_period_from: '2026-06-01',
        statement_period_to: '2026-06-30',
      };

      const result = mapper.mapTransaction(dto);

      expect(result.import_lineage).toBeDefined();
      expect(result.import_lineage?.file_id).toBe('statement_001.pdf');
      expect(result.import_lineage?.source_type).toBe('pdf');
    });

    it('should set default selection state', () => {
      const dto: Transaction = {
        id: 'txn_123',
        date: '2026-07-05',
        description: 'Test',
        type: 'debit',
        category: 'Shopping',
        bank: 'HDFC',
      };

      const result = mapper.mapTransaction(dto);

      expect(result.selected).toBe(false);
      expect(result.selectable).toBe(true);
    });
  });

  describe('mapTransactions', () => {
    it('should map empty array to empty array', () => {
      const result = mapper.mapTransactions([]);
      expect(result).toEqual([]);
    });

    it('should map null/undefined to empty array', () => {
      const result = mapper.mapTransactions(null as unknown as Transaction[]);
      expect(result).toEqual([]);
    });

    it('should map multiple transactions', () => {
      const dtos: Transaction[] = [
        { id: '1', date: '2026-07-01', description: 'A', type: 'debit', category: 'Food', bank: 'HDFC' },
        { id: '2', date: '2026-07-02', description: 'B', type: 'credit', category: 'Income', bank: 'ICICI' },
      ];

      const result = mapper.mapTransactions(dtos);

      expect(result).toHaveLength(2);
      expect(result[0].id).toBe('1');
      expect(result[1].id).toBe('2');
    });
  });
});