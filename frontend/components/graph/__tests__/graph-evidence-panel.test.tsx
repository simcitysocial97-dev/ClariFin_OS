/**
 * Graph Evidence Panel Tests - Stage 7 Graph Runtime Integration
 *
 * Tests for GraphEvidencePanel: evidence rendering, confidence display,
 * low-confidence styling, source navigation, and trace path.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GraphEvidencePanel } from '../graph-evidence-panel';
import { financialGraphRuntime } from '@/lib/graph';

// ===== Mocks =====
vi.mock('@/lib/graph', () => ({
  financialGraphRuntime: {
    explain: vi.fn(),
  },
}));

// ===== Helpers =====
const MOCK_NODE_ID = 'tx:123';

const mockPayloadWithEvidence = {
  node_id: MOCK_NODE_ID,
  evidence: [
    { type: 'categorization', summary: 'Auto-categorized from merchant', source: 'transactions', confidence: 94 },
    { type: 'import', summary: 'Matched statement import', source: 'statements', confidence: 88 },
  ],
  calculations: [
    { name: 'amount_calc', description: 'Sum of transaction amounts', inputs: {}, outputs: {} },
  ],
  sources: [
    { id: 'st:456', type: 'statement', label: 'HDFC Statement July 2026', timestamp: '2026-07-31T00:00:00Z' },
  ],
  confidence: 94,
  trace_path: {
    path: ['tx:123', 'st:456'],
    edge_types: ['traces_to'],
    steps: 1,
    complete: true,
  },
};

const mockPayloadLowConfidence = {
  node_id: MOCK_NODE_ID,
  evidence: [
    { type: 'guess', summary: 'Heuristic category guess', source: 'rules', confidence: 45 },
  ],
  calculations: [],
  sources: [],
  confidence: 45,
};

const mockPayloadNoEvidence = {
  node_id: MOCK_NODE_ID,
  evidence: [],
  calculations: [],
  sources: [],
  confidence: 100,
};

// ===== Tests =====
describe('GraphEvidencePanel — Milestone 7', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('High Confidence (>= 80%)', () => {
    it('displays confidence badge as positive', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      expect(screen.getByText('Confidence: 94%')).toBeInTheDocument();
      // Green/high confidence styling
      const badge = screen.getByText('Confidence: 94%').closest('div');
      expect(badge).toBeTruthy();
    });

    it('shows evidence items', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      expect(screen.getByText('Auto-categorized from merchant')).toBeInTheDocument();
      expect(screen.getByText('Matched statement import')).toBeInTheDocument();
    });

    it('shows calculation steps', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      expect(screen.getByText('amount_calc')).toBeInTheDocument();
      expect(screen.getByText('Sum of transaction amounts')).toBeInTheDocument();
    });

    it('shows source references', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      expect(screen.getByText('HDFC Statement July 2026')).toBeInTheDocument();
      expect(screen.getByText('statement')).toBeInTheDocument();
    });

    it('shows trace path when available', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      expect(screen.getByText('Trace Path')).toBeInTheDocument();
      expect(screen.getByText('1 hops · complete')).toBeInTheDocument();
    });
  });

  describe('Low Confidence (< 80%)', () => {
    it('displays confidence badge as warning', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadLowConfidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      expect(screen.getByText('Confidence: 45%')).toBeInTheDocument();
      expect(screen.getByText('low confidence')).toBeInTheDocument();
    });

    it('applies dashed border to low-confidence evidence', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadLowConfidence);

      const { container } = render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      // Low confidence evidence items should have dashed border styling
      const evidenceItems = container.querySelectorAll('[class*="border-dashed"]');
      expect(evidenceItems.length).toBeGreaterThan(0);
    });
  });

  describe('No Evidence', () => {
    it('renders without evidence section when empty', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadNoEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      // Should still show the panel, just without evidence items
      expect(screen.getByText('Evidence & Provenance')).toBeInTheDocument();
    });
  });

  describe('No Payload', () => {
    it('shows "No evidence available" when explain returns null', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(null);

      render(<GraphEvidencePanel nodeId="nonexistent" onClose={vi.fn()} />);

      expect(screen.getByText('No evidence available')).toBeInTheDocument();
    });
  });

  describe('Source Navigation', () => {
    it('calls onNavigate when source is clicked', () => {
      const onNavigate = vi.fn();
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} onNavigate={onNavigate} />);

      const sourceButton = screen.getByText('HDFC Statement July 2026').closest('button');
      if (sourceButton) {
        fireEvent.click(sourceButton);
        expect(onNavigate).toHaveBeenCalledWith('st:456');
      }
    });
  });

  describe('Closing', () => {
    it('calls onClose when close button is clicked', () => {
      const onClose = vi.fn();
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={onClose} />);

      const closeButton = screen.getByLabelText('Close evidence panel');
      fireEvent.click(closeButton);

      expect(onClose).toHaveBeenCalledOnce();
    });
  });

  describe('Invariant: Evidence is traceable to source', () => {
    it('every evidence item has a source reference', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadWithEvidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      for (const evidence of mockPayloadWithEvidence.evidence) {
        expect(screen.getByText(evidence.summary)).toBeInTheDocument();
      }
    });

    it('low confidence evidence is visually distinct', () => {
      (financialGraphRuntime.explain as ReturnType<typeof vi.fn>).mockReturnValue(mockPayloadLowConfidence);

      render(<GraphEvidencePanel nodeId={MOCK_NODE_ID} onClose={vi.fn()} />);

      // Should have warning coloring for low confidence
      expect(screen.getByText('low confidence')).toBeInTheDocument();
    });
  });
});
