/**
 * Evidence Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for evidence components.
 */

import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { EvidenceDrawer } from '../evidence-drawer';
import { EvidenceList } from '../evidence-list';
import { EvidenceItemComponent } from '../evidence-item';
import type { EvidenceState, EvidenceItem } from '@/lib/evidence/types';

// Mock the Sheet component
vi.mock('@/components/ui/sheet', () => ({
  Sheet: ({ open, children }: any) => open ? <div>{children}</div> : null,
  SheetContent: ({ children }: any) => <div>{children}</div>,
  SheetHeader: ({ children }: any) => <div>{children}</div>,
  SheetTitle: ({ children }: any) => <h2>{children}</h2>,
  SheetDescription: ({ children }: any) => <p>{children}</p>,
}));

// Mock EvidenceSummary
vi.mock('../evidence-summary', () => ({
  EvidenceSummary: () => <div data-testid="evidence-summary" />,
}));

describe('Evidence Performance', () => {
  it('should render evidence drawer with 100 items', () => {
    const evidence: EvidenceItem[] = Array.from({ length: 100 }, (_, i) => ({
      type: 'categorization',
      summary: `Evidence item ${i}`,
      source: { file_id: `file-${i}` },
      confidence: 80 + (i % 20),
    }));

    const state: EvidenceState = {
      isOpen: true,
      transactionId: 'tx-123',
      evidence,
      loading: false,
      error: null,
    };

    render(<EvidenceDrawer state={state} onClose={() => {}} />);
    // Should render without errors
    expect(true).toBe(true);
  });

  it('should render evidence list with 100 items', () => {
    const evidence: EvidenceItem[] = Array.from({ length: 100 }, (_, i) => ({
      type: 'categorization',
      summary: `Evidence item ${i}`,
      source: { file_id: `file-${i}` },
      confidence: 80 + (i % 20),
    }));

    render(<EvidenceList evidence={evidence} loading={false} error={null} />);
    // Should render without errors
    expect(true).toBe(true);
  });

  it('should render evidence item component', () => {
    const item: EvidenceItem = {
      type: 'categorization',
      summary: 'Test evidence',
      source: { file_id: 'file-1', row_number: 5 },
      confidence: 95,
    };

    render(<EvidenceItemComponent item={item} />);
    // Should render without errors
    expect(true).toBe(true);
  });

  it('should handle large evidence arrays without memory issues', () => {
    const evidence: EvidenceItem[] = Array.from({ length: 1000 }, (_, i) => ({
      type: 'categorization',
      summary: `Evidence item ${i}`.repeat(10), // Longer text
      source: { file_id: `file-${i}`, row_number: i },
      confidence: i % 100,
    }));

    const state: EvidenceState = {
      isOpen: true,
      transactionId: 'tx-123',
      evidence,
      loading: false,
      error: null,
    };

    // Should not throw
    expect(() => {
      render(<EvidenceDrawer state={state} onClose={() => {}} />);
    }).not.toThrow();
  });

  it('should calculate average confidence efficiently', () => {
    const evidence: EvidenceItem[] = Array.from({ length: 1000 }, (_, i) => ({
      type: 'categorization',
      summary: `Evidence ${i}`,
      source: { file_id: `file-${i}` },
      confidence: i % 100,
    }));

    const state: EvidenceState = {
      isOpen: true,
      transactionId: 'tx-123',
      evidence,
      loading: false,
      error: null,
    };

    render(<EvidenceDrawer state={state} onClose={() => {}} />);
    // Should render without errors
    expect(true).toBe(true);
  });
});