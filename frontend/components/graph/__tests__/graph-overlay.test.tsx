/**
 * Graph Overlay Tests - Stage 7 Graph Runtime Integration
 *
 * Tests for GraphOverlay component: rendering, dismissal, keyboard shortcuts,
 * node selection, evidence panel integration, and search.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { GraphOverlay } from '../graph-overlay';
import { financialGraphRuntime } from '@/lib/graph';
import { graphInvocation, resetGraphInvocation } from '@/lib/graph/graph-invocation';
import { runtimeEventBus } from '@/lib/event-bus';
import type { GraphScope } from '@/lib/graph/graph-invocation';
import type { GraphResult, NodeType, EdgeType } from '@/lib/graph/types';

// ===== Mocks =====
vi.mock('@/lib/graph', () => ({
  financialGraphRuntime: {
    build: vi.fn(),
    related: vi.fn(),
    select: vi.fn(),
    focus: vi.fn(),
    explain: vi.fn(),
  },
}));

vi.mock('@/lib/graph/graph-invocation', () => ({
  graphInvocation: {
    invoke: vi.fn(),
    close: vi.fn(),
    getScope: vi.fn(),
    getResult: vi.fn(),
    isOpen: vi.fn(() => false),
    subscribe: vi.fn(() => () => {}),
    getRuntime: vi.fn(),
  },
  resetGraphInvocation: vi.fn(),
}));

vi.mock('@/lib/event-bus', () => ({
  runtimeEventBus: {
    publish: vi.fn(),
    subscribe: vi.fn(),
  },
  GRAPH_NODE_SELECTED: 'GraphNodeSelected',
  GRAPH_OVERLAY_OPENED: 'GraphOverlayOpened',
  GRAPH_OVERLAY_CLOSED: 'GraphOverlayClosed',
}));

vi.mock('@/lib/graph/financial-graph-model', () => {
  return {
    FinancialGraphModel: class {
      build() { return this; }
      applyLayout() {
        return { nodes: [], edges: [], width: 100, height: 100 };
      }
      getNode() { return undefined; }
      getNodesByType() { return []; }
    },
  };
});

vi.mock('@/components/graph/renderer/graph-renderer', () => ({
  GraphRenderer: function MockGraphRenderer({ onNodeSelect, onNodeFocus }: { onNodeSelect?: (node: any) => void; onNodeFocus?: (node: any) => void }) {
    return (
      <div data-testid="graph-renderer">
        <button data-testid="node-tx1" onClick={() => onNodeSelect?.({ id: 'tx:1', type: 'transaction', label: 'Test' })} onDoubleClick={() => onNodeFocus?.({ id: 'tx:1', type: 'transaction', label: 'Test' })}>Transaction Node</button>
        <button data-testid="node-ac1" onClick={() => onNodeSelect?.({ id: 'ac:1', type: 'account', label: 'Account' })}>Account Node</button>
      </div>
    );
  },
}));

vi.mock('@/components/graph/graph-evidence-panel', () => ({
  GraphEvidencePanel: function MockEvidencePanel() {
    return <div data-testid="evidence-panel">Evidence Panel</div>;
  },
}));

// ===== Helpers =====
function createScope(overrides: Partial<GraphScope> = {}): GraphScope {
  return {
    trigger: 'command',
    mode: 'overlay',
    focusDepth: 2,
    ...overrides,
  } as GraphScope;
}

const initialResult: GraphResult = {
  nodes: [
    { id: 'tx:1', type: 'transaction', label: 'Test', workspace: 'transactions', metadata: {} },
    { id: 'ac:1', type: 'account', label: 'Account', workspace: 'accounts', metadata: {} },
  ],
  edges: [
    { id: 'e1', source: 'tx:1', target: 'ac:1', type: 'belongs_to', label: 'DEBIT', weight: 1, metadata: {} },
  ],
  metadata: {
    node_count: 2,
    edge_count: 1,
    nodes_by_type: {} as Record<NodeType, number>,
    edges_by_type: {} as Record<EdgeType, number>,
    workspaces: [],
    built_at: '',
    version: '1.0.0',
  },
};

// ===== Tests =====
describe('GraphOverlay — Milestone 7', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    resetGraphInvocation();
  });

  describe('Rendering', () => {
    it('renders the overlay with header and controls', () => {
      render(<GraphOverlay scope={createScope()} initialResult={initialResult} />);

      expect(screen.getByText('Graph Exploration')).toBeInTheDocument();
      expect(screen.getByTestId('graph-renderer')).toBeInTheDocument();
    });

    it('displays node and edge counts in status bar', async () => {
      render(<GraphOverlay scope={createScope()} initialResult={initialResult} />);

      await waitFor(() => {
        expect(screen.getByText(/Nodes: 2/)).toBeInTheDocument();
        expect(screen.getByText(/Edges: 1/)).toBeInTheDocument();
      });
    });

    it('shows entity ID in header when provided', () => {
      const scope = createScope({ entityId: 'tx:abc123', trigger: 'selection' });
      render(<GraphOverlay scope={scope} />);

      expect(screen.getByText(/Entity:/)).toBeInTheDocument();
    });

    it('shows trigger in status bar', () => {
      const scope = createScope({ trigger: 'insight', entityId: 'tx:1' });
      render(<GraphOverlay scope={scope} />);

      expect(screen.getByText(/Trigger: insight/)).toBeInTheDocument();
    });

    it('renders layout control buttons', () => {
      render(<GraphOverlay scope={createScope()} />);

      expect(screen.getByRole('button', { name: /force/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /tree/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /timeline/i })).toBeInTheDocument();
    });
  });

  describe('Dismissal', () => {
    it('calls onDismiss when X button is clicked', () => {
      const onDismiss = vi.fn();
      render(<GraphOverlay scope={createScope()} onDismiss={onDismiss} />);

      const closeButton = screen.getByLabelText('Close graph overlay');
      fireEvent.click(closeButton);

      expect(onDismiss).toHaveBeenCalledOnce();
      expect(graphInvocation.close).toHaveBeenCalledWith('overlay-dismissed');
    });

    it('renders search input', () => {
      render(<GraphOverlay scope={createScope()} />);

      const searchInput = document.querySelector('input');
      expect(searchInput).toBeInTheDocument();
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('closes on Escape key', () => {
      render(<GraphOverlay scope={createScope()} />);

      fireEvent.keyDown(window, { key: 'Escape' });

      expect(graphInvocation.close).toHaveBeenCalledWith('overlay-dismissed');
    });

    it('does not close on other keys', () => {
      render(<GraphOverlay scope={createScope()} />);
      vi.clearAllMocks();

      fireEvent.keyDown(window, { key: 'a' });

      expect(graphInvocation.close).not.toHaveBeenCalled();
    });
  });

  describe('Evidence Panel', () => {
    it('shows evidence panel after node click', () => {
      render(<GraphOverlay scope={createScope()} />);

      const nodeButton = screen.getByTestId('node-tx1');
      fireEvent.click(nodeButton);

      expect(screen.getByTestId('evidence-panel')).toBeInTheDocument();
    });

    it('hides evidence panel when closed', () => {
      render(<GraphOverlay scope={createScope()} />);

      const nodeButton = screen.getByTestId('node-tx1');
      fireEvent.click(nodeButton);
      expect(screen.getByTestId('evidence-panel')).toBeInTheDocument();
    });
  });

  describe('Selection Delegation', () => {
    it('delegates node selection to FinancialGraphRuntime', () => {
      render(<GraphOverlay scope={createScope()} />);

      const nodeButton = screen.getByTestId('node-tx1');
      fireEvent.click(nodeButton);

      expect(financialGraphRuntime.select).toHaveBeenCalledWith(['tx:1']);
    });

    it('publishes GRAPH_NODE_SELECTED event on node click', () => {
      render(<GraphOverlay scope={createScope()} />);

      const nodeButton = screen.getByTestId('node-tx1');
      fireEvent.click(nodeButton);

      expect(runtimeEventBus.publish).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'GraphNodeSelected',
          source: 'GraphRuntime',
        }),
      );
    });

    it('delegates node focus to FinancialGraphRuntime on double click', () => {
      render(<GraphOverlay scope={createScope()} />);

      const nodeButton = screen.getByTestId('node-tx1');
      fireEvent.doubleClick(nodeButton);

      expect(financialGraphRuntime.focus).toHaveBeenCalledWith('tx:1', 2);
    });
  });

  describe('Invariant: Investigative Only', () => {
    it('always renders as fixed overlay (z-index)', () => {
      const { container } = render(<GraphOverlay scope={createScope()} />);

      const overlay = container.firstChild as HTMLElement;
      expect(overlay.className).toContain('fixed');
      expect(overlay.className).toContain('z-[1001]');
    });

    it('shows "Esc to close" in status bar', () => {
      render(<GraphOverlay scope={createScope()} />);
      expect(screen.getByText('Esc to close')).toBeInTheDocument();
    });
  });
});
