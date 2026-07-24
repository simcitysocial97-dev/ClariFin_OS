/**
 * Transaction Table Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for transaction table component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TransactionTable } from '../transaction-table';
import type { TransactionViewModel } from '@/types/transaction-view-model';

const createMockTransactions = (count: number): TransactionViewModel[] =>
  Array.from({ length: count }, (_, i) => ({
    id: `tx-${i}`,
    date: '2024-01-15',
    date_formatted: 'Jan 15, 2024',
    description: `Test transaction ${i}`,
    amount: { paise: 10000 * (i + 1), rupees: 100 * (i + 1) },
    transaction_type: 'debit',
    category_id: 'cat1',
    category_name: 'Food',
    merchant_id: 'merch1',
    merchant_name: 'Test Merchant',
    evidence: [],
    import_lineage: { file_id: '1', filename: 'test.pdf', import_date: '2024-01-15', source_type: 'pdf', bank: 'Test Bank' },
  }));

describe('TransactionTable Performance', () => {
  it('renders 100 transactions', () => {
    const transactions = createMockTransactions(100);
    render(<TransactionTable transactions={transactions} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders 500 transactions', () => {
    const transactions = createMockTransactions(500);
    render(<TransactionTable transactions={transactions} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('renders loading state', () => {
    render(<TransactionTable transactions={[]} loading={true} />);
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('renders error state', () => {
    render(<TransactionTable transactions={[]} error={new Error('Test error')} />);
    expect(screen.getByText(/Test error/)).toBeInTheDocument();
  });
});