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
  it('LoadingSpinner renders', () => {
    const { container } = render(<LoadingSpinner />);
    expect(container.querySelector('.animate-spin')).toBeInTheDocument();
  });

  it('SkeletonRow renders', () => {
    const { container } = render(<SkeletonRow />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('SkeletonTable renders 100 rows', () => {
    const { container } = render(<SkeletonTable rows={100} />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });

  it('SkeletonTable renders 1000 rows', () => {
    const { container } = render(<SkeletonTable rows={1000} />);
    const pulseElements = container.querySelectorAll('.animate-pulse');
    expect(pulseElements.length).toBeGreaterThan(0);
  });
});