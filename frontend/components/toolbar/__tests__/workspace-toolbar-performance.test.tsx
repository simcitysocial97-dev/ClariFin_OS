/**
 * Workspace Toolbar Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for toolbar component.
 */

import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import { WorkspaceToolbar } from '../workspace-toolbar';

describe('WorkspaceToolbar Performance', () => {
  const mockProps = {
    onSearchClick: vi.fn(),
    onFilterToggle: vi.fn(),
    onGroupToggle: vi.fn(),
    onSortToggle: vi.fn(),
    onExport: vi.fn(),
    onRefresh: vi.fn(),
    onSettings: vi.fn(),
    transactionCount: 0,
    activeFilterCount: 0,
  };

  it('renders under 100ms', () => {
    const start = performance.now();
    render(<WorkspaceToolbar {...mockProps} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(100);
  });

  it('renders with high transaction count under 100ms', () => {
    const start = performance.now();
    render(<WorkspaceToolbar {...mockProps} transactionCount={10000} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(100);
  });

  it('renders with active filters under 100ms', () => {
    const start = performance.now();
    render(<WorkspaceToolbar {...mockProps} activeFilterCount={10} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(100);
  });

  it('renders loading state under 100ms', () => {
    const start = performance.now();
    render(<WorkspaceToolbar {...mockProps} loading={true} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(100);
  });
});