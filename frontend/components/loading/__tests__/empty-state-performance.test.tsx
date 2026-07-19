/**
 * Empty State Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for empty state components.
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { EmptyState } from '../empty-state';

describe('Empty State Performance', () => {
  it('EmptyState renders under 150ms', () => {
    const start = performance.now();
    render(<EmptyState />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(150);
  });

  it('EmptyState with action renders under 150ms', () => {
    const start = performance.now();
    render(<EmptyState onAction={() => {}} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(150);
  });
});
