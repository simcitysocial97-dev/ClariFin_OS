/**
 * Context Panel Tests - Stage 9 Context Panel Experience
 *
 * Tests for the ContextPanel component — the OS inspector.
 * Verifies entity-specific context views, empty states,
 * insight filtering, and section rendering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ContextPanel } from '../context-panel';
import { selectionRuntime } from '@/lib/runtime/selection-runtime';
import { passiveInsightRuntime } from '@/lib/intelligence/passive-runtime';
import type { SelectionEntity } from '@/lib/runtime/runtime-types';

// ===== Mock Runtimes =====
vi.mock('@/lib/runtime/selection-runtime', () => ({
  selectionRuntime: {
    state: { active: null, multi: new Set(), history: [] },
  },
}));

vi.mock('@/lib/intelligence/passive-runtime', () => ({
  passiveInsightRuntime: {
    getInsights: () => [],
  },
}));

vi.mock('@/lib/intelligence/investigative-runtime', () => ({
  investigativeInsightRuntime: {
    getInsights: () => [],
  },
}));

// ===== Mock Capabilities =====
vi.mock('@/lib/capabilities/use-transaction-capability', () => ({
  useTransactionCapability: () => ({
    transactions: [],
    loading: false,
    error: null,
  }),
}));

vi.mock('@/lib/capabilities/use-accounts-capability', () => ({
  useAccountsCapability: () => ({
    accounts: null,
    loading: false,
    error: null,
  }),
}));

vi.mock('@/lib/capabilities/use-loans-capability', () => ({
  useLoansCapability: () => ({
    loans: null,
    loading: false,
    error: null,
  }),
}));

vi.mock('@/lib/capabilities/use-credit-cards-capability', () => ({
  useCreditCardsCapability: () => ({
    creditCards: null,
    loading: false,
    error: null,
  }),
}));

vi.mock('@/lib/capabilities/use-investments-capability', () => ({
  useInvestmentsCapability: () => ({
    investments: null,
    loading: false,
    error: null,
  }),
}));

vi.mock('@/lib/capabilities/use-reconciliation-capability', () => ({
  useReconciliationCapability: () => ({
    reconciliation: null,
    loading: false,
    error: null,
  }),
}));

// ===== Helper: Create Selection Entity =====
function createSelection(type: SelectionEntity['type'], id: string | number): SelectionEntity {
  if (type === 'reconciliation') {
    return { type: 'reconciliation', id: id as number };
  }
  return { type, id: id as string };
}

// ===== Test Wrapper =====
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        {children}
      </QueryClientProvider>
    );
  };
}

// ===== Test Setup =====
describe('ContextPanel — Milestone 4', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(selectionRuntime).state = {
      active: null,
      multi: new Set(),
      history: [],
    };
  });

  describe('Empty State (no selection)', () => {
    it('renders empty state message when no entity is selected', () => {
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText('Select an entity to view context')).toBeInTheDocument();
    });

    it('renders hint text in empty state', () => {
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Click any row or card/)).toBeInTheDocument();
    });
  });

  describe('Transaction Context', () => {
    it('shows not-found message when transaction data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-abc'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Transaction not found in current view/)).toBeInTheDocument();
    });

    it('displays not-found message when transaction data is missing', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-abc'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Transaction not found in current view/)).toBeInTheDocument();
    });
  });

  describe('Account Context', () => {
    it('shows not-found message when account data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('account', 'acc-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Account not found in current view/)).toBeInTheDocument();
    });
  });

  describe('Loan Context', () => {
    it('shows not-found message when loan data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('loan', 'loan-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Loan not found in current view/)).toBeInTheDocument();
    });
  });

  describe('Card Context', () => {
    it('shows not-found message when card data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('card', 'card-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Card not found in current view/)).toBeInTheDocument();
    });
  });

  describe('Investment Context', () => {
    it('shows not-found message when investment data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('investment', 'inv-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Investment not found in current view/)).toBeInTheDocument();
    });
  });

  describe('Reconciliation Context', () => {
    it('shows not-found message when reconciliation data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('reconciliation', 1),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Reconciliation not found in current view/)).toBeInTheDocument();
    });
  });

  describe('Actions Section', () => {
    it('always renders Actions section when entity is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders action buttons in Actions section', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText('View full evidence trail')).toBeInTheDocument();
      expect(screen.getByText('Run what-if analysis')).toBeInTheDocument();
      expect(screen.getByText('Compare with similar entities')).toBeInTheDocument();
    });
  });

  describe('No Navigation Violation', () => {
    it('does not contain any navigation links', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      const { container } = render(<ContextPanel />, { wrapper: createWrapper() });
      const links = container.querySelectorAll('a[href]');
      expect(links.length).toBe(0);
    });
  });

  describe('Section Rendering', () => {
    it('renders not-found message when entity data is not loaded', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText(/Transaction not found in current view/)).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders Insight section only when matching insights exist', () => {
      const originalGetInsights = passiveInsightRuntime.getInsights;
      (passiveInsightRuntime as unknown as Record<string, unknown>).getInsights = () => [
        {
          id: 'insight-1',
          category: 'spending',
          title: 'Spending anomaly',
          summary: 'Unusual spending detected',
          severity: 'warning',
          confidence: 0.85,
          relatedEntityId: 'tx-001',
          relatedEntityType: 'transaction',
          dismissible: true,
          relevanceScore: 0.7,
          createdAt: Date.now(),
        } as never,
      ];

      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />, { wrapper: createWrapper() });
      expect(screen.getByText('Insights')).toBeInTheDocument();
      expect(screen.getByText('Spending anomaly')).toBeInTheDocument();

      (passiveInsightRuntime as unknown as Record<string, unknown>).getInsights = originalGetInsights;
    });
  });

  describe('Context Panel Structure', () => {
    it('renders within a scrollable region', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      const { container } = render(<ContextPanel />, { wrapper: createWrapper() });
      expect(container.querySelector('[class*="overflow-y-auto"]')).toBeInTheDocument();
    });

    it('renders header with entity type and id', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      const { container } = render(<ContextPanel />, { wrapper: createWrapper() });
      expect(container.innerHTML).toContain('Transaction');
      expect(container.innerHTML).toContain('tx-001');
    });
  });
});
