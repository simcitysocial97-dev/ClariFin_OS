/**
 * Virtualized Table Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for virtualized table component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { VirtualizedTable } from '../virtualized-table';
import type { TransactionViewModel } from '@/types/transaction-view-model';

const mockTransactions: TransactionViewModel[] = [
  {
    id: '1',
    date: '2024-01-15',
    date_formatted: 'Jan 15, 2024',
    description: 'Test transaction 1',
    amount: { paise: 10000, rupees: 100 },
    transaction_type: 'debit',
    category_id: 'cat1',
    category_name: 'Food',
    merchant_id: 'merch1',
    merchant_name: 'Test Merchant',
    evidence: [],
    import_lineage: { file_id: '1', filename: 'test.pdf', import_date: '2024-01-15', source_type: 'pdf', bank: 'Test Bank' },
  },
  {
    id: '2',
    date: '2024-01-16',
    date_formatted: 'Jan 16, 2024',
    description: 'Test transaction 2',
    amount: { paise: 25000, rupees: 250 },
    transaction_type: 'credit',
    category_id: 'cat2',
    category_name: 'Income',
    merchant_id: 'merch2',
    merchant_name: 'Test Merchant 2',
    evidence: [],
    import_lineage: { file_id: '1', filename: 'test.pdf', import_date: '2024-01-15', source_type: 'pdf', bank: 'Test Bank' },
  },
];

describe('VirtualizedTable', () => {
  it('renders all transactions', () => {
    render(<VirtualizedTable transactions={mockTransactions} />);
    expect(screen.getByText('Test transaction 1')).toBeInTheDocument();
    expect(screen.getByText('Test transaction 2')).toBeInTheDocument();
  });

  it('displays transaction dates', () => {
    render(<VirtualizedTable transactions={mockTransactions} />);
    expect(screen.getByText('Jan 15, 2024')).toBeInTheDocument();
    expect(screen.getByText('Jan 16, 2024')).toBeInTheDocument();
  });

  it('displays transaction amounts', () => {
    render(<VirtualizedTable transactions={mockTransactions} />);
    expect(screen.getByText('₹100.00')).toBeInTheDocument();
    expect(screen.getByText('₹250.00')).toBeInTheDocument();
  });

  it('displays category badges', () => {
    render(<VirtualizedTable transactions={mockTransactions} />);
    expect(screen.getByText('Food')).toBeInTheDocument();
    expect(screen.getByText('Income')).toBeInTheDocument();
  });

  it('shows loading state with skeleton rows', () => {
    render(<VirtualizedTable transactions={[]} loading={true} />);
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('shows error state', () => {
    render(<VirtualizedTable transactions={[]} error={new Error('Failed to load')} />);
    expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
  });

  it('shows empty state when no transactions', () => {
    render(<VirtualizedTable transactions={[]} />);
    expect(screen.getByText(/No transactions found/)).toBeInTheDocument();
  });

  it('has table role and aria-label', () => {
    render(<VirtualizedTable transactions={mockTransactions} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('has fixed height container for virtualization', () => {
    const { container } = render(<VirtualizedTable transactions={mockTransactions} />);
    const scrollContainer = container.querySelector('.h-\\[400px\\]');
    expect(scrollContainer).toBeInTheDocument();
  });
});