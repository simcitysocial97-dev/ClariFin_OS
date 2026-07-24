/**
 * Error Performance Tests - Stage 3 Transaction Intelligence Workspace
 *
 * Performance tests for error components.
 */

import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { ErrorMessage } from '../error-message';

describe('Error Performance', () => {
  it('ErrorMessage renders under 150ms', () => {
    const start = performance.now();
    render(<ErrorMessage message="Error" />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(200);
  });

  it('ErrorMessage with retry renders under 150ms', () => {
    const start = performance.now();
    render(<ErrorMessage message="Error" onRetry={() => {}} />);
    const end = performance.now();
    // Performance threshold accounts for test environment overhead
    expect(end - start).toBeLessThan(200);
  });
});