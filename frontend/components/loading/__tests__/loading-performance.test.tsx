/**
 * Loading Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for loading components.
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { LoadingSpinner } from '../loading-spinner';
import { SkeletonRow, SkeletonTable } from '../skeleton-row';

describe('Loading Performance', () => {
  it('LoadingSpinner renders under 100ms', () => {
    const start = performance.now();
    render(<LoadingSpinner />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(100);
  });

  it('SkeletonRow renders under 50ms', () => {
    const start = performance.now();
    render(<SkeletonRow />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(50);
  });

  it('SkeletonTable renders 100 rows under 1000ms', () => {
    const start = performance.now();
    render(<SkeletonTable rows={100} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(1000);
  });

  it('SkeletonTable renders 1000 rows under 3000ms', () => {
    const start = performance.now();
    render(<SkeletonTable rows={1000} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(3000);
  });
});
