/**
 * Transaction Table Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for transaction table component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { TransactionTable } from '../transaction-table';
import type { TransactionViewModel } from '@/types/transaction-view-model';

const createMockTransactions = (count: number): TransactionViewModel[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `tx-${i}`,
    date: '2024-01-15',
    date_formatted: 'Jan 15, 2024',
    description: `Test transaction ${i}`,
    amount: { paise: 10000 * (i + 1), display: `₹${(i + 1) * 100}.00` },
    transaction_type: 'debit',
    category_id: 'cat1',
    category_name: 'Food',
    merchant_id: 'merch1',
    merchant_name: 'Test Merchant',
    confidence_score: 0.95,
    evidence: [],
    import_lineage: { source: 'test', file_id: '1' },
    adjustment: null,
    relationship: { related_ids: [] },
    navigation: { category: '/category/cat1', merchant: '/merchant/merch1' },
    selection: { selected: false, selectable: true },
  }));

describe('TransactionTable Performance', () => {
  it('renders 100 transactions under 700ms', () => {
    const transactions = createMockTransactions(100);
    const start = performance.now();
    render(<TransactionTable transactions={transactions} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(700);
  });

  it('renders 500 transactions under 2000ms', () => {
    const transactions = createMockTransactions(500);
    const start = performance.now();
    render(<TransactionTable transactions={transactions} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(2000);
  });

  it('renders loading state under 50ms', () => {
    const start = performance.now();
    render(<TransactionTable transactions={[]} loading={true} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(50);
  });

  it('renders error state under 50ms', () => {
    const start = performance.now();
    render(<TransactionTable transactions={[]} error={new Error('Test error')} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(50);
  });
});