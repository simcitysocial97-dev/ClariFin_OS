/**
 * Transaction Table Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Tests for transaction table component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TransactionTable } from '../transaction-table';
import type { TransactionViewModel } from '@/types/transaction-view-model';

const mockTransactions: TransactionViewModel[] = [
  {
    id: '1',
    date: '2024-01-15',
    date_formatted: 'Jan 15, 2024',
    description: 'Test transaction 1',
    amount: { paise: 10000, display: '₹100.00' },
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
  },
  {
    id: '2',
    date: '2024-01-16',
    date_formatted: 'Jan 16, 2024',
    description: 'Test transaction 2',
    amount: { paise: 25000, display: '₹250.00' },
    transaction_type: 'credit',
    category_id: 'cat2',
    category_name: 'Income',
    merchant_id: 'merch2',
    merchant_name: 'Test Merchant 2',
    confidence_score: 0.85,
    evidence: [],
    import_lineage: { source: 'test', file_id: '1' },
    adjustment: null,
    relationship: { related_ids: [] },
    navigation: { category: '/category/cat2', merchant: '/merchant/merch2' },
    selection: { selected: false, selectable: true },
  },
];

describe('TransactionTable', () => {
  it('renders all transactions', () => {
    render(<TransactionTable transactions={mockTransactions} />);
    expect(screen.getByText('Test transaction 1')).toBeInTheDocument();
    expect(screen.getByText('Test transaction 2')).toBeInTheDocument();
  });

  it('displays transaction dates', () => {
    render(<TransactionTable transactions={mockTransactions} />);
    expect(screen.getByText('Jan 15, 2024')).toBeInTheDocument();
    expect(screen.getByText('Jan 16, 2024')).toBeInTheDocument();
  });

  it('displays transaction amounts', () => {
    render(<TransactionTable transactions={mockTransactions} />);
    expect(screen.getByText('₹100.00')).toBeInTheDocument();
    expect(screen.getByText('₹250.00')).toBeInTheDocument();
  });

  it('displays category badges', () => {
    render(<TransactionTable transactions={mockTransactions} />);
    expect(screen.getByText('Food')).toBeInTheDocument();
    expect(screen.getByText('Income')).toBeInTheDocument();
  });

  it('shows loading state with skeleton rows', () => {
    render(<TransactionTable transactions={[]} loading={true} />);
    // Check for skeleton elements (animate-pulse class)
    const skeletonElements = document.querySelectorAll('.animate-pulse');
    expect(skeletonElements.length).toBeGreaterThan(0);
  });

  it('shows error state', () => {
    render(<TransactionTable transactions={[]} error={new Error('Failed to load')} />);
    expect(screen.getByText(/Failed to load/)).toBeInTheDocument();
  });

  it('shows empty state when no transactions', () => {
    render(<TransactionTable transactions={[]} />);
    expect(screen.getByText(/No transactions found/)).toBeInTheDocument();
  });

  it('has table role and aria-label', () => {
    render(<TransactionTable transactions={mockTransactions} />);
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('calls onRowClick when row is clicked', () => {
    const onRowClick = vi.fn();
    render(<TransactionTable transactions={mockTransactions} onRowClick={onRowClick} />);
    const rows = screen.getAllByRole('row');
    rows[1].click(); // Skip header row
    expect(onRowClick).toHaveBeenCalled();
  });

  it('calls onSelectionChange when checkbox is clicked', () => {
    const onSelectionChange = vi.fn();
    render(<TransactionTable transactions={mockTransactions} onSelectionChange={onSelectionChange} />);
    const checkboxes = screen.getAllByRole('checkbox');
    checkboxes[0].click();
    expect(onSelectionChange).toHaveBeenCalledWith('1', true);
  });

  it('shows selected state for selected rows', () => {
    render(<TransactionTable transactions={mockTransactions} selectedIds={new Set(['1'])} />);
    const rows = screen.getAllByRole('row');
    expect(rows[1]).toHaveAttribute('aria-selected', 'true');
  });
});