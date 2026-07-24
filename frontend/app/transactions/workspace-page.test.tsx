/**
 * Transaction Workspace Page Tests - Stage 3
 *
 * Tests for workspace page keyboard navigation, accessibility, and state management.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TransactionWorkspacePage } from './workspace-page';

// Mock the hooks
const mockUseTransactionCapability = vi.fn();
const mockUseEvidence = vi.fn();

vi.mock('@/lib/capabilities/use-transaction-capability', () => ({
  useTransactionCapability: () => mockUseTransactionCapability(),
}));

vi.mock('@/lib/evidence/use-evidence', () => ({
  useEvidence: () => mockUseEvidence(),
}));

vi.mock('@/components/filters/filter-panel', () => ({
  FilterPanel: () => <div data-testid="filter-panel">Filter Panel</div>,
}));

vi.mock('@/components/loading/loading-spinner', () => ({
  LoadingSpinner: ({ size }: { size: string }) => (
    <div data-testid="loading-spinner" className={`spinner-${size}`}>
      Loading...
    </div>
  ),
}));

vi.mock('@/components/loading/error-message', () => ({
  ErrorMessage: ({ message, onRetry }: { message: string; onRetry: () => void }) => (
    <div data-testid="error-message">
      {message}
      <button onClick={onRetry}>Retry</button>
    </div>
  ),
}));

vi.mock('@/components/loading/empty-state', () => ({
  EmptyState: ({ onAction }: { onAction: () => void }) => (
    <div data-testid="empty-state">
      No transactions
      <button onClick={onAction}>Clear filters</button>
    </div>
  ),
}));

vi.mock('@/components/evidence/evidence-drawer', () => ({
  EvidenceDrawer: () => <div data-testid="evidence-drawer">Evidence Drawer</div>,
}));

vi.mock('@/components/toolbar/workspace-toolbar', () => ({
  WorkspaceToolbar: ({ transactionCount, activeFilterCount }: { transactionCount: number; activeFilterCount: number }) => (
    <div data-testid="workspace-toolbar" data-transaction-count={transactionCount} data-filter-count={activeFilterCount}>
      Toolbar
    </div>
  ),
}));

vi.mock('@/components/selection/selection-summary', () => ({
  SelectionSummary: () => <div data-testid="selection-summary">Selection Summary</div>,
}));

vi.mock('@/components/workspace/insight-panel', () => ({
  InsightPanel: () => <div data-testid="insight-panel">Insight Panel</div>,
}));

vi.mock('@/components/workspace/action-drawer', () => ({
  ActionDrawer: () => <div data-testid="action-drawer">Action Drawer</div>,
}));

vi.mock('@/components/transaction-table/transaction-table', () => ({
  TransactionTable: () => <div data-testid="transaction-table">Transaction Table</div>,
}));

const defaultMockCapability = {
  loading: false,
  loadingTimeout: false,
  loadingTimeoutMessage: '',
  error: null,
  transactions: [
    {
      id: 'tx-1',
      date: '2026-07-15',
      description: 'Test transaction',
      amount: { paise: 10000, rupees: 100 },
      category_name: 'Food',
      merchant_name: 'Test Merchant',
      transaction_type: 'debit',
      evidence: [],
    },
  ],
  total: 1,
  searchQuery: '',
  dateFilter: null,
  categoryFilter: [],
  merchantFilter: [],
  amountFilter: null,
  statusFilter: [],
  selectedIds: new Set(),
  setSearchQuery: vi.fn(),
  setDateFilter: vi.fn(),
  setCategoryFilter: vi.fn(),
  setMerchantFilter: vi.fn(),
  setAmountFilter: vi.fn(),
  setStatusFilter: vi.fn(),
  toggleSelection: vi.fn(),
  selectAllVisible: vi.fn(),
  clearSelection: vi.fn(),
  clearFilters: vi.fn(),
  refresh: vi.fn(),
  toggleGroup: vi.fn(),
};

const defaultMockEvidence = {
  isOpen: false,
  openEvidence: vi.fn(),
  closeEvidence: vi.fn(),
};

describe('TransactionWorkspacePage', () => {
  beforeEach(() => {
    mockUseTransactionCapability.mockReturnValue(defaultMockCapability);
    mockUseEvidence.mockReturnValue(defaultMockEvidence);
  });

  it('renders the workspace with all regions', () => {
    render(<TransactionWorkspacePage />);

    expect(screen.getByTestId('workspace-toolbar')).toBeInTheDocument();
    expect(screen.getByTestId('filter-panel')).toBeInTheDocument();
    expect(screen.getByTestId('transaction-table')).toBeInTheDocument();
    expect(screen.getByTestId('insight-panel')).toBeInTheDocument();
    expect(screen.getByTestId('evidence-drawer')).toBeInTheDocument();
  });

  it('has proper accessibility attributes', () => {
    render(<TransactionWorkspacePage />);

    const main = screen.getByRole('main');
    expect(main).toHaveAttribute('aria-label', 'Transaction Intelligence Workspace');
    expect(main).toHaveAttribute('tabIndex', '0');
  });

  it('displays transaction count in toolbar', () => {
    render(<TransactionWorkspacePage />);

    const toolbar = screen.getByTestId('workspace-toolbar');
    expect(toolbar).toHaveAttribute('data-transaction-count', '1');
  });

  it('displays active filter count in toolbar', () => {
    render(<TransactionWorkspacePage />);

    const toolbar = screen.getByTestId('workspace-toolbar');
    expect(toolbar).toHaveAttribute('data-filter-count', '0');
  });
});

describe('TransactionWorkspacePage - Loading Timeout', () => {
  beforeEach(() => {
    mockUseEvidence.mockReturnValue(defaultMockEvidence);
  });

  it('shows loading spinner when loading is true', () => {
    mockUseTransactionCapability.mockReturnValue({
      ...defaultMockCapability,
      loading: true,
      transactions: [],
      total: 0,
    });

    render(<TransactionWorkspacePage />);

    expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('shows loading timeout message when loadingTimeout is true', () => {
    mockUseTransactionCapability.mockReturnValue({
      ...defaultMockCapability,
      loading: true,
      loadingTimeout: true,
      loadingTimeoutMessage: 'Loading is taking longer than expected. Please wait...',
      transactions: [],
      total: 0,
    });

    render(<TransactionWorkspacePage />);

    expect(screen.getByRole('status')).toHaveTextContent('Loading is taking longer than expected. Please wait...');
  });

  it('does not show loading timeout message when loadingTimeout is false', () => {
    mockUseTransactionCapability.mockReturnValue({
      ...defaultMockCapability,
      loading: true,
      loadingTimeout: false,
      loadingTimeoutMessage: '',
      transactions: [],
      total: 0,
    });

    render(<TransactionWorkspacePage />);

    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
});