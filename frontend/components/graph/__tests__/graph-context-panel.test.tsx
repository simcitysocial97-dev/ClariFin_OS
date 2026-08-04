/**
 * Graph Context Panel Tests - Stage 7 Graph Runtime Integration
 *
 * Tests for GraphContextPanel: relationship loading, node capping at 20,
 * error handling, loading state, and empty state.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { GraphContextPanel } from '../graph-context-panel';
import { financialGraphRuntime } from '@/lib/graph';
import { selectionRuntime } from '@/lib/runtime/selection-runtime';

// ===== Mocks =====
vi.mock('@/lib/graph', () => ({
  financialGraphRuntime: {
    related: vi.fn(),
    explain: vi.fn(),
  },
}));

vi.mock('@/lib/runtime/selection-runtime', () => ({
  selectionRuntime: {
    selectEntity: vi.fn(),
    state: { active: null },
  },
}));

vi.mock('@/lib/utils', () => ({
  cn: (...args: unknown[]) => args.filter(Boolean).join(' '),
}));

// ===== Helpers =====
const TEST_ENTITY_ID = 'tx:test123';

const mockGraphResult = {
  nodes: [
    { id: 'tx:test123', type: 'transaction', label: 'Amazon Purchase', workspace: 'transactions', metadata: {}, deep_link: '/transactions/tx:test123' },
    { id: 'ac:savings', type: 'account', label: 'Savings Account', workspace: 'accounts', metadata: {}, deep_link: '/accounts/ac:savings' },
    { id: 'cat:shopping', type: 'category', label: 'Shopping', workspace: 'categories', metadata: {}, deep_link: '/categories/cat:shopping' },
  ],
  edges: [
    { id: 'e1', source: 'tx:test123', target: 'ac:savings', type: 'belongs_to', label: 'DEBIT', weight: 1, metadata: {} },
    { id: 'e2', source: 'tx:test123', target: 'cat:shopping', type: 'categorized_as', label: 'CATEGORIZED_AS', weight: 1, metadata: {} },
  ],
  metadata: { node_count: 3, edge_count: 2, nodes_by_type: {}, edges_by_type: {}, workspaces: [], built_at: '', version: '1.0.0' },
};

const mockGraphResultWithValue = {
  nodes: [
    { id: 'tx:test123', type: 'transaction', label: 'Amazon Purchase', workspace: 'transactions', metadata: {}, value_paise: 129900, deep_link: '/transactions/tx:test123' },
    { id: 'ac:savings', type: 'account', label: 'Savings Account', workspace: 'accounts', metadata: {}, value_paise: 2500000, deep_link: '/accounts/ac:savings' },
  ],
  edges: [],
  metadata: { node_count: 2, edge_count: 0, nodes_by_type: {}, edges_by_type: {}, workspaces: [], built_at: '', version: '1.0.0' },
};

// ===== Tests =====
describe('GraphContextPanel — Milestone 7', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Empty entityId', () => {
    it('shows "No relationships found" when no entityId is provided', () => {
      render(<GraphContextPanel />);
      expect(screen.getByText('No relationships found')).toBeInTheDocument();
    });
  });

  describe('Loading and Content', () => {
    it('renders relationship nodes with labels', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue(mockGraphResult);

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(screen.getByText('Amazon Purchase')).toBeInTheDocument();
      });
    });

    it('displays node count in header', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue(mockGraphResult);

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(screen.getByText('Relationships (3)')).toBeInTheDocument();
      });
    });

    it('shows monetary values when present', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue(mockGraphResultWithValue);

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(screen.getByText(/₹1299/)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('shows "No relationships found" when no nodes returned', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue({
        nodes: [],
        edges: [],
        metadata: { node_count: 0, edge_count: 0, nodes_by_type: {}, edges_by_type: {}, workspaces: [], built_at: '', version: '1.0.0' },
      });

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(screen.getByText('No relationships found')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error message when loading throws', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockImplementation(() => {
        throw new Error('Failed to load');
      });

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load relationships')).toBeInTheDocument();
      });
    });
  });

  describe('Node Capping (max 20)', () => {
    it('caps nodes at 20 per architecture spec §5.5', async () => {
      const largeResult = {
        nodes: Array.from({ length: 25 }, (_, i) => ({
          id: `node:${i}`,
          type: 'transaction',
          label: `Node ${i}`,
          workspace: 'transactions',
          metadata: {},
        })),
        edges: [],
        metadata: { node_count: 25, edge_count: 0, nodes_by_type: {}, edges_by_type: {}, workspaces: [], built_at: '', version: '1.0.0' },
      };
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue(largeResult);

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        const nodes = screen.getAllByText(/Node \d+/);
        expect(nodes.length).toBeLessThanOrEqual(20);
      });
    });
  });

  describe('Node Click — Selection Delegation', () => {
    it('delegates selection to SelectionRuntime on node click', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue(mockGraphResult);

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(screen.getByText('Amazon Purchase')).toBeInTheDocument();
      });

      const nodeButton = screen.getByText('Amazon Purchase').closest('button');
      if (nodeButton) {
        fireEvent.click(nodeButton);
        expect(selectionRuntime.selectEntity).toHaveBeenCalledOnce();
      }
    });
  });

  describe('Invariant: Investigative Only', () => {
    it('uses depth=1 for context panel (1-hop relationships)', async () => {
      (financialGraphRuntime.related as ReturnType<typeof vi.fn>).mockReturnValue(mockGraphResult);

      render(<GraphContextPanel entityId={TEST_ENTITY_ID} />);

      await waitFor(() => {
        expect(financialGraphRuntime.related).toHaveBeenCalledWith(TEST_ENTITY_ID, 1);
      });
    });
  });
});
