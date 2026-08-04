/**
 * Context Panel Tests - Stage 9 Context Panel Experience
 *
 * Tests for the ContextPanel component — the OS inspector.
 * Verifies entity-specific context views, empty states,
 * insight filtering, and section rendering.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
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

// ===== Helper: Create Selection Entity =====
function createSelection(type: SelectionEntity['type'], id: string | number): SelectionEntity {
  if (type === 'reconciliation') {
    return { type: 'reconciliation', id: id as number };
  }
  return { type, id: id as string };
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
      render(<ContextPanel />);
      expect(screen.getByText('Select an entity to view context')).toBeInTheDocument();
    });

    it('renders hint text in empty state', () => {
      render(<ContextPanel />);
      expect(screen.getByText(/Click any row or card/)).toBeInTheDocument();
    });
  });

  describe('Transaction Context', () => {
    it('renders transaction context when transaction is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-abc'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Amount')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
      expect(screen.getByText('Category')).toBeInTheDocument();
      expect(screen.getByText('Merchant')).toBeInTheDocument();
      expect(screen.getByText('Date')).toBeInTheDocument();
      expect(screen.getByText('Confidence')).toBeInTheDocument();
    });

    it('displays evidence section for transactions', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-abc'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText(/Matched source record #1/)).toBeInTheDocument();
      expect(screen.getByText(/Matched source record #2/)).toBeInTheDocument();
      expect(screen.getByText(/Matched source record #3/)).toBeInTheDocument();
    });

    it('displays explanation section for transactions', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-abc'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText(/UPI transaction matched/)).toBeInTheDocument();
    });
  });

  describe('Account Context', () => {
    it('renders account context when account is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('account', 'acc-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Status')).toBeInTheDocument();
      expect(screen.getByText('Balance')).toBeInTheDocument();
      expect(screen.getByText('Institution')).toBeInTheDocument();
      expect(screen.getByText('Opened')).toBeInTheDocument();
      expect(screen.getByText('Transactions')).toBeInTheDocument();
    });

    it('displays account status badge', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('account', 'acc-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('active')).toBeInTheDocument();
    });

    it('shows explanation section for accounts', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('account', 'acc-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText(/Savings account with consistent deposit pattern/)).toBeInTheDocument();
    });
  });

  describe('Loan Context', () => {
    it('renders loan context when loan is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('loan', 'loan-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Outstanding')).toBeInTheDocument();
      expect(screen.getByText('Monthly EMI')).toBeInTheDocument();
      expect(screen.getByText('Interest Rate')).toBeInTheDocument();
      expect(screen.getByText('Remaining')).toBeInTheDocument();
      expect(screen.getByText('Lender')).toBeInTheDocument();
    });

    it('shows forecast section for loans', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('loan', 'loan-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Forecast')).toBeInTheDocument();
      expect(screen.getByText(/Projected completion/)).toBeInTheDocument();
    });

    it('shows explanation section for loans', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('loan', 'loan-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText(/Home loan with consistent EMI payments/)).toBeInTheDocument();
    });
  });

  describe('Card Context', () => {
    it('renders card context when card is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('card', 'card-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Last 4')).toBeInTheDocument();
      expect(screen.getByText('Current Usage')).toBeInTheDocument();
      expect(screen.getByText('Credit Limit')).toBeInTheDocument();
      expect(screen.getByText('Utilization')).toBeInTheDocument();
      expect(screen.getByText('Due Date')).toBeInTheDocument();
    });

    it('shows explanation section for cards', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('card', 'card-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText(/Credit utilization/)).toBeInTheDocument();
    });
  });

  describe('Investment Context', () => {
    it('renders investment context when investment is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('investment', 'inv-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Scheme')).toBeInTheDocument();
      expect(screen.getByText('Type')).toBeInTheDocument();
      expect(screen.getByText('Units')).toBeInTheDocument();
      expect(screen.getByText('NAV')).toBeInTheDocument();
      expect(screen.getByText('Invested')).toBeInTheDocument();
      expect(screen.getByText('Current Value')).toBeInTheDocument();
      expect(screen.getByText('Gain')).toBeInTheDocument();
    });

    it('shows forecast section for investments', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('investment', 'inv-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Forecast')).toBeInTheDocument();
    });

    it('shows explanation section for investments', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('investment', 'inv-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText(/Equity-linked savings fund/)).toBeInTheDocument();
    });
  });

  describe('Reconciliation Context', () => {
    it('renders reconciliation context when reconciliation is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('reconciliation', 1),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Period')).toBeInTheDocument();
      expect(screen.getByText('Matched')).toBeInTheDocument();
      expect(screen.getByText('Unmatched')).toBeInTheDocument();
      expect(screen.getByText('Discrepancy')).toBeInTheDocument();
    });
  });

  describe('Actions Section', () => {
    it('always renders Actions section when entity is selected', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders action buttons in Actions section', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
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
      const { container } = render(<ContextPanel />);
      const links = container.querySelectorAll('a[href]');
      expect(links.length).toBe(0);
    });
  });

  describe('Section Rendering', () => {
    it('renders expected sections for a transaction', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      render(<ContextPanel />);
      expect(screen.getByText('Evidence')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
      expect(screen.getAllByText('Explanation').length).toBeGreaterThanOrEqual(1);
    });

    it('renders Insight section only when matching insights exist', () => {
      // Override the mock for this specific test
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
      render(<ContextPanel />);
      expect(screen.getByText('Insights')).toBeInTheDocument();
      expect(screen.getByText('Spending anomaly')).toBeInTheDocument();

      // Restore
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
      const { container } = render(<ContextPanel />);
      expect(container.querySelector('[class*="overflow-y-auto"]')).toBeInTheDocument();
    });

    it('renders header with entity type and id', () => {
      vi.mocked(selectionRuntime).state = {
        active: createSelection('transaction', 'tx-001'),
        multi: new Set(),
        history: [],
      };
      const { container } = render(<ContextPanel />);
      // Header contains entity type label and id
      expect(container.innerHTML).toContain('Transaction');
      expect(container.innerHTML).toContain('tx-001');
    });
  });
});
